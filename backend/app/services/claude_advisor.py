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
from dataclasses import dataclass, field

import anthropic

from app.config import Settings
from app.services import budget_tracker

TOOL_NAME = "trading_decision"

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


class ClaudeAdvisor:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def _call_model(self, model: str, tool: dict, user_content: str, system: str) -> tuple[dict, float, int, int]:
        response = self._client.messages.create(
            model=model,
            max_tokens=1024,
            system=system,
            tools=[tool],
            tool_choice={"type": "tool", "name": TOOL_NAME},
            messages=[{"role": "user", "content": user_content}],
        )
        for block in response.content:
            if block.type == "tool_use" and block.name == TOOL_NAME:
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
