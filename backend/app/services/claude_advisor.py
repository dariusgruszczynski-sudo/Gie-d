"""Wraps the Anthropic API call that produces a trading decision.

Claude Opus is forced to respond via a single tool call with a fixed schema,
so downstream code never has to parse free-form text.
"""

import json
from dataclasses import dataclass, field

import anthropic

from app.config import Settings

TOOL_NAME = "trading_decision"

DISCLAIMER = (
    "Jesteś silnikiem decyzyjnym prywatnego, eksperymentalnego bota tradingowego "
    "działającego na WŁASNYM kapitale właściciela — to nie jest usługa doradztwa "
    "inwestycyjnego dla osób trzecich. Twoje decyzje bezpośrednio wpływają na realne "
    "środki, więc bądź konserwatywny: gdy dane są niejednoznaczne, wybieraj HOLD."
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
                        "Dla BUY: % dostępnego wolnego kapitału USDT do zaangażowania. "
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

    def decide(
        self,
        *,
        whitelist: list[str],
        market_data: dict,
        news: list[dict],
        portfolio: dict,
        risk_context: dict,
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
            },
            ensure_ascii=False,
            indent=2,
        )

        response = self._client.messages.create(
            model=self._settings.claude_model,
            max_tokens=1024,
            system=DISCLAIMER,
            tools=[tool],
            tool_choice={"type": "tool", "name": TOOL_NAME},
            messages=[{"role": "user", "content": user_content}],
        )

        for block in response.content:
            if block.type == "tool_use" and block.name == TOOL_NAME:
                data = block.input
                return TradingDecision(
                    action=data["action"],
                    symbol=data.get("symbol"),
                    size_pct=float(data.get("size_pct", 0)),
                    confidence=float(data.get("confidence", 0)),
                    reasoning=data.get("reasoning", ""),
                    raw_input=data,
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                )

        raise RuntimeError("Claude response did not contain the expected tool_use block")
