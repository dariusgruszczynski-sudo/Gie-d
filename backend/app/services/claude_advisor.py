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

DISCLAIMER = (
    "Jesteś aktywnym swing-traderem zarządzającym małym, prywatnym portfelem krypto "
    "na Krakenie (rynek spot, EUR) — to WŁASNY kapitał właściciela, nie usługa dla osób "
    "trzecich. Twój cel to POMNAŻAĆ kapitał aktywnym handlem, a nie siedzieć w gotówce. "
    "Gdy widzisz sensowny sygnał (trend, wybicie ponad opór, wyprzedanie/niski RSI, "
    "dodatnie momentum, odbicie), WCHODŹ w pozycję (BUY) — nie czekaj na 100% pewności, "
    "wystarczy realna przewaga. Rotuj kapitał między coinami, gdy któryś ma wyraźnie "
    "lepszy setup. Pozycje są AUTOMATYCZNIE zamykane przez mechaniczny take-profit / "
    "stop-loss, więc nie musisz mikrozarządzać wyjściami — skup się na trafnym WEJŚCIU. "
    "HOLD wybieraj tylko gdy naprawdę brak przewagi w którąkolwiek stronę — nie z samej "
    "ostrożności. Zawsze działaj w ramach podanych limitów ryzyka i uwzględniaj prowizję "
    "Krakena (~0,26% za stronę, ~0,5% w obie), więc szukaj ruchów wyraźnie ją przewyższających."
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

    def _call_model(self, model: str, tool: dict, user_content: str) -> tuple[dict, float, int, int]:
        response = self._client.messages.create(
            model=model,
            max_tokens=1024,
            system=DISCLAIMER,
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
        trigger_reason: str,
    ) -> TradingDecision:
        tool = _build_tool_schema(whitelist)

        user_content = json.dumps(
            {
                "trigger_reason": trigger_reason,
                "tradable_whitelist": whitelist,
                "market_data": market_data,
                "recent_news": news,
                "portfolio": portfolio,
                "risk_context": risk_context,
                "market_context": market_context or {},
            },
            ensure_ascii=False,
            indent=2,
        )

        fast_model = self._settings.claude_model_fast
        data, cost, in_tok, out_tok = self._call_model(fast_model, tool, user_content)
        total_cost = cost
        total_in, total_out = in_tok, out_tok
        model_used = fast_model

        action = data["action"]
        confidence = float(data.get("confidence", 0))
        is_uncertain_trade = action in ("BUY", "SELL") and confidence < self._settings.claude_escalation_confidence_threshold

        if is_uncertain_trade:
            escalation_content = (
                user_content
                + "\n\n---\n"
                + f"Wstępna, niepewna analiza modelu szybkiego ({fast_model}, confidence={confidence:.2f}): "
                + f"{data['action']} {data.get('symbol') or ''} rozmiar={data.get('size_pct', 0)}%. "
                + f"Uzasadnienie: {data.get('reasoning', '')}\n"
                + "Ty podejmujesz decyzję ostateczną -- możesz się zgodzić, zmienić rozmiar/kierunek, albo wybrać HOLD."
            )
            data, cost, in_tok, out_tok = self._call_model(self._settings.claude_model, tool, escalation_content)
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
