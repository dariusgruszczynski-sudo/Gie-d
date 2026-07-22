"""Wraps the Anthropic API calls that produce a trading decision.

Every cycle is analyzed first by the fast/cheap model (Sonnet). Its decision
is trusted directly for HOLD or a confident BUY/SELL; a BUY/SELL where the
fast model itself reports low confidence -- genuine doubt -- is escalated to
the slower/pricier model (Opus) for a second opinion, which is what actually
gets recorded and executed. Claude is forced to respond via a single tool
call with a fixed schema, so downstream code never has to parse free-form
text.
"""

import json
import logging
from dataclasses import dataclass, field

import anthropic

from app.config import Settings
from app.services import budget_tracker

logger = logging.getLogger(__name__)

TOOL_NAME = "trading_decision"
# Portfolio-manager tool: Claude returns a SET of actions across the WHOLE
# whitelist in one call, not a single pick -- this is the "AI tool, not a
# calculator" model (see decide_portfolio / run_cycle).
TOOL_NAME_PORTFOLIO = "portfolio_decisions"

# Wspólny „regulamin mechaniki" doklejany do obu person (mózgów) -- reguły
# wyjść, uczenia się z własnej historii i uczciwej pewności są identyczne dla
# akcji i krypto; różni się tylko charakter/agresja rynku (intro wyżej).
_SHARED_TAIL = (
    "Podawaj UCZCIWĄ pewność (confidence) — automat odrzuca BUY poniżej progu z "
    "risk_context.min_buy_confidence, więc zawyżanie pewności tylko marnuje cykl. "
    "Pozycje są AUTOMATYCZNIE zamykane przez mechaniczny take-profit / CZĘŚCIOWĄ realizację / "
    "trailing-stop / stop-loss — nie mikrozarządzaj wyjściami, skup się na trafnym WEJŚCIU. "
    "FILOZOFIA 'PO TROCHU DO CELU' dotyczy WEJŚĆ i WYJŚĆ: nie czekaj na idealny szczyt ani na "
    "idealny, podręcznikowy setup — na małym koncie SERIA drobnych, wysoko-prawdopodobnych "
    "zysków (nawet po kilka dolarów) jest WARTOŚCIOWA i to jest cel, nie efekt uboczny. Jeśli "
    "widzisz solidny, choć skromny ruch z jednym wyraźnym sygnałem — wejdź, nie czekaj na "
    "konfluencję wszystkiego naraz. Jeśli pozycja jest na plusie a setup się psuje, śmiało "
    "proponuj CZĘŚCIOWY SELL (mniejszy % pozycji) zamiast trzymać wszystko do końca; lepszy "
    "zrealizowany mniejszy zysk niż oddany zysk papierowy. "
    "'your_performance.playbook' to STAŁA baza zasad destylowana z praktyki doświadczonych traderów i "
    "botów — traktuj ją jako fundament, na którym budujesz własne, świeższe lekcje; łam ją tylko z "
    "wyraźnego powodu popartego dzisiejszymi danymi. "
    "UCZ SIĘ z pola 'your_performance': otwarte pozycje z ceną wejścia i bieżącym P&L oraz "
    "ostatnie transakcje z uzasadnieniami. Dokładaj do tego, co działa, nie powtarzaj setupów, "
    "które wielokrotnie kończyły się stratą; pozycji świeżo zamkniętej stop-lossem nie odkupuj bez "
    "wyraźnie nowego, mocniejszego sygnału. 'your_performance.lessons_learned' to Twoje wnioski z "
    "cotygodniowych przeglądów — stosuj je, chyba że dzisiejsze dane im przeczą. "
    "'your_performance.per_symbol_stats' to twardy bilans per ticker (zamknięte, W/L, trafność, "
    "P&L) — preferuj tickery z dodatnią historią, unikaj powtarzalnych strat. "
    "BUY przechodzi przez LEKKI mechaniczny filtr: wystarczy JEDEN wyraźny sygnał z trzech "
    "(SMA50>SMA200, MACD byczy, RSI w zdrowej/momentum strefie LUB świeże wyprzedanie z odbiciem) "
    "— nie potrzebujesz wszystkich naraz, więc NIE rezygnuj z kandydata tylko dlatego, że nie ma "
    "podręcznikowej konfluencji wszystkiego. Odrzucone jest tylko wejście z zerowym wsparciem "
    "technicznym (0 z 3). Nagłówki z flagą 'just_published': true to newsy, które WYWOŁAŁY ten cykl — "
    "potraktuj je priorytetowo. Rozmiar pozycji jest automatycznie skalowany w dół dla bardziej "
    "zmiennych tickerów (technical.volatility_pct_1h), więc podawaj % śmiało — system i tak zetnie "
    "rozmiar dzikiej nazwy. Uwzględniaj risk_context.market_regime: w risk_off bądź defensywny."
)

# MÓZG 1 — AKCJE US (średnio agresywnie).
EQUITIES_PERSONA = (
    "Jesteś aktywnym swing-traderem zarządzającym małym, prywatnym portfelem akcji/ETF-ów na "
    "Alpaca (rynek US, USD, zlecenia bez prowizji) — to WŁASNY kapitał właściciela. Tryb: "
    "ASYMETRYCZNY — OSTROŻNY W DÓŁ, ODWAŻNY W GÓRĘ. Gdy rynek jest w wyraźnym trendzie spadkowym / "
    "risk_off (SPY pod średnimi, MACD bearish, tech-rout, rosnący VIX): CHROŃ kapitał — nie łap "
    "spadających noży, nie dokładaj do stratnych pozycji, siedź w GOTÓWCE lub kup defensywę "
    "(SH/GLD/TLT). ALE gdy pojawia się REALNA okazja z przewagą (potwierdzony trend wzrostowy, "
    "wybicie ponad opór z wolumenem, wyprzedanie z wyraźnym odbiciem, mocny katalizator/news, "
    "konfluencja kilku sygnałów) — NIE bądź zachowawczy: wchodź ZDECYDOWANIE i MOCNO, użyj GÓRNEGO "
    "zakresu dozwolonego rozmiaru (nie symbolicznego skrawka), bo timid sizing zostawia zysk na "
    "stole. Nie obniżaj jakości setupu, obniż wahanie: dobry setup zasługuje na pełny rozmiar. "
    "Jedna mocna, dobrze wybrana transakcja bije pięć przeciętnych; bezczynność w DOBRYM secie też "
    "kosztuje. Jeśli nie ma ani spadku do ochrony, ani czystej okazji — GOTÓWKA to pełnoprawna "
    "pozycja i HOLD jest OK. "
    "Rynek działa tylko w godzinach sesji US — poza sesją po prostu HOLD. "
    "Whitelist jest CELOWO skupiona (SPY/QQQ + mega-capy tech AAPL/MSFT/NVDA/AMZN/GOOGL/META + "
    "wysokobetowa TSLA), plus defensywa: złoto (GLD), obligacje (TLT) i ETF ODWROTNY SH (inverse "
    "S&P). W wyraźnym trendzie spadkowym rynku KUP SH zamiast siedzieć w gotówce — to normalna "
    "długa pozycja, nie ryzykowny short. W 'your_performance.scorecard' masz wynik vs "
    "bierne trzymanie SPY: jeśli alpha ujemna, bądź bardziej selektywny. " + _SHARED_TAIL
)

# MÓZG 2 — POZA SESJĄ (extended hours, tanie ETF-y, ostrożnie).
EXTENDED_PERSONA = (
    "Jesteś ostrożnym traderem prowadzącym drugą nogę tego samego, małego prywatnego konta na "
    "Alpaca: handel akcjami/ETF-ami US POZA sesją regularną (pre-market 4:00–9:30 i after-hours "
    "16:00–20:00 ET) — WŁASNY kapitał właściciela. Uniwersum to WĄSKA lista TANICH, płynnych ETF-ów "
    "(całe sztuki muszą zmieścić się w budżecie). Poza sesją płynność jest CIEŃSZA, a spready "
    "SZERSZE niż w dzień, więc bądź BARDZIEJ selektywny niż silnik sesji regularnej: wyższy próg "
    "pewności, wchodź tylko na wyraźnym sygnale (momentum/wybicie/mocny news), a nie na szumie. "
    "ALE gdy sygnał jest CZYSTY i mocny — nie bądź przesadnie zachowawczy: wejdź z przekonaniem, w "
    "górnym rozmiarze dozwolonym dla tej nogi. Ostrożność dotyczy szumu, cienkiej płynności i "
    "spreadów — NIE realnych okazji z przewagą. Zlecenia to LIMIT na całe akcje — fill nie jest "
    "gwarantowany, i to jest OK: "
    "lepiej nie wejść niż przepłacić spread. Rynek US to jeden reżim: w risk_off (SPY w trendzie "
    "spadkowym, wysoki VIX) jedyną defensywą jest GOTÓWKA — wtedy HOLD/redukuj, nie 'łap spadających "
    "noży'. " + _SHARED_TAIL
)


# Doklejane WYŁĄCZNIE w trybie zarządzania portfelem (decide_portfolio). Zmienia
# rolę Claude z "wybierz jedną pozycję" na "prowadź cały portfel": to jest
# realizacja intencji właściciela — narzędzie AI, nie kalkulator, który tylko
# zatwierdza przesiane pozycje.
_PORTFOLIO_ADDENDUM = (
    "\n\nTRYB: ZARZĄDZASZ CAŁYM PORTFELEM. Zwróć ZESTAW akcji (pole 'actions', 0..N pozycji) na CAŁEJ "
    "whiteliście naraz — możesz w jednym przejściu otworzyć kilka pozycji, dokupić do istniejącej, "
    "przyciąć/zrotować słabnącą i zamknąć wybraną. Pusta lista = świadomie nic nie robię (trzymam "
    "wszystko). Rozmiary BUY liczą się PO KOLEI od AKTUALNEJ wolnej gotówki w momencie wykonania, więc "
    "trzy BUY po 40% nie przepalą konta — każdy bierze % z tego, co zostało (system dodatkowo ogranicza "
    "przydziałem kapitału i zmiennością). "
    "GRAJ AKTYWNIE I W MIARĘ AGRESYWNIE: na małym koncie SERIA drobnych, wysoko-prawdopodobnych zysków "
    "składa się w wynik — nie siedź w gotówce, gdy widzisz realną przewagę; ale nie handluj dla samego "
    "handlu bez przewagi. "
    "MECHANICZNE SITO WEJŚCIA JEST TERAZ TYLKO DORADCZE: masz je w market_data[symbol].technical jako "
    "jeden z inputów — NIE jest twardym wetem. TY decydujesz. Wystarczy jeden wyraźny sygnał + "
    "katalizator z newsów/sentymentu, żeby wejść; nie czekaj na podręcznikową konfluencję wszystkiego. "
    "TWOJA PRZEWAGA nad czystą mechaniką to CZYTANIE KONTEKSTU: recent_news (z flagą just_published), "
    "sentiment_label/sentiment_score i market_context — używaj ich, bo tego kalkulator nie policzy. "
    "Wyjścia (stop/trailing/take-profit/częściowa) dalej chodzą mechanicznie co poll i CHRONIĄ kapitał "
    "— skup się na trafnych WEJŚCIACH i ROTACJI, nie mikrozarządzaj każdym stopem. "
    "W 'portfolio_thesis' podaj krótką (2-4 zdania) tezę całościową: jak widzisz rynek i portfel teraz."
)


@dataclass
class TradingDecision:
    action: str  # BUY / SELL / HOLD
    symbol: str | None
    size_pct: float
    confidence: float
    reasoning: str
    raw_input: dict = field(default_factory=dict)
    input_tokens: int = 0
    output_tokens: int = 0
    # Real $ cost of every API call this decision required (fast pass, plus
    # the escalation pass when one happened) -- priced per-model, since Sonnet
    # and Opus have different rates.
    cost_usd: float = 0.0
    model_used: str = ""


def _build_tool_schema(whitelist: list[str]) -> dict:
    return {
        "name": TOOL_NAME,
        "description": "Zwraca jedną decyzję inwestycyjną dla bieżącego cyklu analizy.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["BUY", "SELL", "HOLD"],
                },
                "symbol": {
                    "type": ["string", "null"],
                    "enum": whitelist + [None],
                    "description": "Wymagane dla BUY/SELL, null dla HOLD.",
                },
                "size_pct": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100,
                    "description": (
                        "Dla BUY: % dostępnego wolnego kapitału do zaangażowania. "
                        "Dla SELL: % aktualnie posiadanej pozycji w danym symbolu do sprzedania. "
                        "Dla HOLD: 0."
                    ),
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                },
                "reasoning": {
                    "type": "string",
                    "description": "Krótkie uzasadnienie decyzji (2-5 zdań) po polsku.",
                },
            },
            "required": ["action", "symbol", "size_pct", "confidence", "reasoning"],
        },
    }


def _parse_portfolio_actions(data: dict, model: str) -> list[TradingDecision]:
    """Turns a portfolio_decisions tool payload into a non-empty list of
    TradingDecision. Only actionable (BUY/SELL with a symbol) actions are kept;
    if Claude sent nothing actionable, collapse to a single HOLD (so we still
    record a decision and fire the 'czeka' notification). Cost/tokens are set by
    the caller on the first element."""
    thesis = (data.get("portfolio_thesis") or "").strip()
    raw_actions = data.get("actions") or []
    decisions: list[TradingDecision] = []
    for a in raw_actions:
        action = (a.get("action") or "HOLD").upper()
        if action not in ("BUY", "SELL", "HOLD"):
            logger.warning("decide_portfolio: nieznana akcja %r, pomijam", action)
            continue
        reasoning = (a.get("reasoning") or "").strip()
        if thesis and decisions == []:
            reasoning = f"{reasoning} [Teza: {thesis}]".strip()
        decisions.append(
            TradingDecision(
                action=action,
                symbol=a.get("symbol"),
                size_pct=float(a.get("size_pct", 0) or 0),
                confidence=float(a.get("confidence", 0) or 0),
                reasoning=reasoning,
                raw_input=a,
                model_used=model,
            )
        )

    actionable = [d for d in decisions if d.action in ("BUY", "SELL") and d.symbol]
    if not actionable:
        actionable = [
            TradingDecision(
                action="HOLD",
                symbol=None,
                size_pct=0.0,
                confidence=float(raw_actions[0].get("confidence", 0)) if raw_actions else 0.0,
                reasoning=(thesis or "Trzymam cały portfel — brak wyraźnej przewagi w tym cyklu."),
                raw_input=data,
                model_used=model,
            )
        ]
    return actionable


def _build_portfolio_tool_schema(whitelist: list[str]) -> dict:
    return {
        "name": TOOL_NAME_PORTFOLIO,
        "description": "Zwraca ZESTAW decyzji inwestycyjnych dla całego portfela w bieżącym cyklu.",
        "input_schema": {
            "type": "object",
            "properties": {
                "actions": {
                    "type": "array",
                    "description": (
                        "Lista akcji do wykonania TERAZ, w kolejności. Pusta lista = nic nie robię "
                        "(trzymam cały portfel). Możesz zwrócić kilka BUY/SELL naraz."
                    ),
                    "items": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["BUY", "SELL", "HOLD"]},
                            "symbol": {
                                "type": ["string", "null"],
                                "enum": whitelist + [None],
                                "description": "Wymagane dla BUY/SELL, null dla HOLD.",
                            },
                            "size_pct": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 100,
                                "description": (
                                    "Dla BUY: % AKTUALNEJ wolnej gotówki (liczone po kolei). "
                                    "Dla SELL: % posiadanej pozycji w tym symbolu. Dla HOLD: 0."
                                ),
                            },
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            "reasoning": {
                                "type": "string",
                                "description": "Krótkie uzasadnienie tej akcji (1-3 zdania) po polsku.",
                            },
                        },
                        "required": ["action", "symbol", "size_pct", "confidence", "reasoning"],
                    },
                },
                "portfolio_thesis": {
                    "type": "string",
                    "description": "Krótka teza całościowa (2-4 zdania) po polsku: jak widzisz rynek i portfel.",
                },
            },
            "required": ["actions"],
        },
    }


class ClaudeAdvisor:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def _call_model(
        self, model: str, tool: dict, user_content: str, system: str, max_tokens: int = 1024
    ) -> tuple[dict, float, int, int]:
        tool_name = tool["name"]
        response = self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            tools=[tool],
            tool_choice={"type": "tool", "name": tool_name},
            messages=[{"role": "user", "content": user_content}],
        )
        for block in response.content:
            if block.type == "tool_use" and block.name == tool_name:
                cost = budget_tracker.estimate_cost_usd(
                    model, response.usage.input_tokens, response.usage.output_tokens
                )
                return block.input, cost, response.usage.input_tokens, response.usage.output_tokens
        raise RuntimeError("Claude response did not contain the expected tool_use block")

    def decide(
        self,
        *,
        whitelist: list[str],
        market_data: dict,
        news: list[dict],
        portfolio: dict,
        risk_context: dict,
        market_context: dict | None = None,
        performance_context: dict | None = None,
        trigger_reason: str,
        venue: str = "alpaca",
    ) -> TradingDecision:
        # Two brains: the extended venue gets the aggressive 24/7 extended persona,
        # everything else the medium-aggressive equities persona.
        system = EXTENDED_PERSONA if venue == "extended" else EQUITIES_PERSONA
        tool = _build_tool_schema(whitelist)

        user_content = json.dumps(
            {
                "trigger_reason": trigger_reason,
                "tradable_whitelist": whitelist,
                "market_data": market_data,
                "recent_news": news,
                "portfolio": portfolio,
                # Your own track record: open positions with their entry price
                # and current unrealized P&L, plus your most recent executed
                # trades and why. USE IT to improve -- add to what's working,
                # don't repeat what keeps losing, and know whether a position
                # is a winner (let it run) or a loser (already stop-loss'd
                # mechanically, so don't average down blindly).
                "your_performance": performance_context or {},
                "risk_context": risk_context,
                "market_context": market_context or {},
            },
            ensure_ascii=False,
            indent=2,
        )

        fast_model = self._settings.claude_model_fast
        data, cost, in_tok, out_tok = self._call_model(fast_model, tool, user_content, system)
        total_cost = cost
        total_in, total_out = in_tok, out_tok
        model_used = fast_model

        action = data["action"]
        confidence = float(data.get("confidence", 0))
        # LEAN-AI: escalation to the pricier model only happens when explicitly
        # enabled. On a small account the extra Opus call per uncertain trade is
        # a cost the edge can't justify -- one cheap fast-model call per cycle.
        is_uncertain_trade = (
            self._settings.claude_escalation_enabled
            and action in ("BUY", "SELL")
            and confidence < self._settings.claude_escalation_confidence_threshold
        )

        if is_uncertain_trade:
            escalation_content = (
                user_content
                + "\n\n---\n"
                + f"Wstępna, niepewna analiza modelu szybkiego ({fast_model}, confidence={confidence:.2f}): "
                + f"{data['action']} {data.get('symbol') or ''} rozmiar={data.get('size_pct', 0)}%. "
                + f"Uzasadnienie: {data.get('reasoning', '')}\n"
                + "Ty podejmujesz decyzję ostateczną -- możesz się zgodzić, zmienić rozmiar/kierunek, albo wybrać HOLD."
            )
            data, cost, in_tok, out_tok = self._call_model(self._settings.claude_model, tool, escalation_content, system)
            total_cost += cost
            total_in += in_tok
            total_out += out_tok
            model_used = self._settings.claude_model

        return TradingDecision(
            action=data["action"],
            symbol=data.get("symbol"),
            size_pct=float(data.get("size_pct", 0)),
            confidence=float(data.get("confidence", 0)),
            reasoning=data.get("reasoning", ""),
            raw_input=data,
            input_tokens=total_in,
            output_tokens=total_out,
            cost_usd=total_cost,
            model_used=model_used,
        )

    def decide_portfolio(
        self,
        *,
        whitelist: list[str],
        market_data: dict,
        news: list[dict],
        portfolio: dict,
        risk_context: dict,
        market_context: dict | None = None,
        performance_context: dict | None = None,
        trigger_reason: str,
        venue: str = "alpaca",
    ) -> list[TradingDecision]:
        """Portfolio-manager mode: ONE cheap fast-model call returns a SET of
        actions across the whole whitelist (0..N), not a single pick. Reuses the
        same context payload as decide(); the full month's-budget guard and the
        per-action risk gates still run downstream in run_cycle. No escalation
        (LEAN-AI: one fast-model call per cycle keeps 5-min cadence affordable).

        ALWAYS returns a non-empty list: an empty 'actions' (Claude chose to sit
        tight) becomes a single HOLD decision carrying the call's full cost, so
        cost accounting and the 'czeka' notification both have a row to hang on.
        The total call cost/token counts ride on the FIRST element only (the API
        call is one, regardless of how many actions come back)."""
        system = (EXTENDED_PERSONA if venue == "extended" else EQUITIES_PERSONA) + _PORTFOLIO_ADDENDUM
        tool = _build_portfolio_tool_schema(whitelist)
        user_content = json.dumps(
            {
                "trigger_reason": trigger_reason,
                "tradable_whitelist": whitelist,
                "market_data": market_data,
                "recent_news": news,
                "portfolio": portfolio,
                "your_performance": performance_context or {},
                "risk_context": risk_context,
                "market_context": market_context or {},
            },
            ensure_ascii=False,
            indent=2,
        )

        fast_model = self._settings.claude_model_fast
        data, cost, in_tok, out_tok = self._call_model(fast_model, tool, user_content, system, max_tokens=2048)
        actionable = _parse_portfolio_actions(data, fast_model)
        total_cost, total_in, total_out = cost, in_tok, out_tok

        # Kaganiec zdjęty: gdy escalation ON i którakolwiek AKTYWNA akcja jest
        # niepewna, Claude może sięgnąć po mocniejszy model (Opus) i przemyśleć
        # CAŁY portfel jeszcze raz -- to jego wynik wygrywa. Koszt obu wywołań
        # sumowany (właściciel dosypuje tokeny, świadoma decyzja "jak chce").
        uncertain = any(
            d.action in ("BUY", "SELL") and d.confidence < self._settings.claude_escalation_confidence_threshold
            for d in actionable
        )
        if self._settings.claude_escalation_enabled and uncertain:
            data2, cost2, in2, out2 = self._call_model(
                self._settings.claude_model, tool, user_content, system, max_tokens=2048
            )
            actionable = _parse_portfolio_actions(data2, self._settings.claude_model)
            total_cost += cost2
            total_in += in2
            total_out += out2

        # The call(s)' cost/tokens ride on the first element only.
        actionable[0].cost_usd = total_cost
        actionable[0].input_tokens = total_in
        actionable[0].output_tokens = total_out
        return actionable
