"""Klasyfikator LLM katalizatorów — „czy to zagraża monecie, którą handluję, i jak mocno".

Tu LLM zarabia na tokeny (analiza 2026-11-21): surowy feed daje nagłówki, ale dopiero
rozumienie treści mówi, czy news realnie dotyka naszej pozycji i jak jest poważny.
Fallback keyword (crypto_events.classify_severity) jest zgrubny; LLM robi to rzetelnie.

Oszczędnie: klasyfikator dostaje BATCH nagłówków w JEDNYM wywołaniu, i tylko tych,
które przeszły tani prefiltr. `call_model` jest WSTRZYKIWANY (= ClaudeAdvisor._call_model
albo fake w testach), więc logika prompt/parse jest w pełni testowalna bez API.
Config-gated: crypto_event_llm_enabled domyślnie False -> zero kosztu, dopóki OFF.
"""

from __future__ import annotations

from collections.abc import Callable

CLASSIFY_TOOL = {
    "name": "classify_crypto_events",
    "description": "Oceń listę nagłówków krypto: czy dotyczą tradeowalnej monety i jak są poważne.",
    "input_schema": {
        "type": "object",
        "properties": {
            "events": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "idx": {"type": "integer", "description": "indeks nagłówka z wejścia"},
                        "symbol": {"type": "string", "description": "baza monety z uniwersum, której dotyczy (np. 'ETH'), albo '' gdy żadnej"},
                        "kind": {"type": "string", "description": "hack|exploit|depeg|delisting|unlock|listing|regulatory|other"},
                        "severity": {"type": "number", "description": "0..1, jak mocno uderza w cenę/holdera (1=katastrofa)"},
                    },
                    "required": ["idx", "symbol", "kind", "severity"],
                },
            }
        },
        "required": ["events"],
    },
}

_SYSTEM = (
    "Jesteś analitykiem ryzyka krypto. Dostajesz nagłówki i listę monet, które bot handluje. "
    "Dla KAŻDEGO nagłówka zwróć: której monety z uniwersum dotyczy (symbol bazowy albo '' gdy "
    "żadnej/całorynkowy), typ zdarzenia, i powagę 0..1 (jak mocno uderza w cenę posiadacza). "
    "Bądź konserwatywny: gdy niepewne, niższa powaga. Nie wymyślaj monet spoza uniwersum."
)


def build_user_content(headlines: list[str], universe: list[str]) -> str:
    uni = ", ".join(sorted({u.split("/")[0].upper() for u in universe}))
    lines = "\n".join(f"[{i}] {h}" for i, h in enumerate(headlines))
    return f"Uniwersum (tradeowalne): {uni}\n\nNagłówki:\n{lines}"


def parse_classification(tool_input: dict, n: int) -> list[dict]:
    """tool_input z LLM -> lista {idx, symbol, kind, severity} znormalizowana i przycięta
    do zakresu. Braki/śmieci pomijane; severity clamped 0..1; idx w zakresie."""
    out = []
    for e in (tool_input or {}).get("events", []) or []:
        try:
            idx = int(e.get("idx"))
        except (TypeError, ValueError):
            continue
        if not (0 <= idx < n):
            continue
        sev = e.get("severity")
        try:
            sev = max(0.0, min(1.0, float(sev)))
        except (TypeError, ValueError):
            sev = 0.0
        out.append({
            "idx": idx,
            "symbol": (str(e.get("symbol") or "").upper().split("/")[0] or None),
            "kind": str(e.get("kind") or "other").lower(),
            "severity": sev,
        })
    return out


def classify_headlines(
    headlines: list[str],
    universe: list[str],
    call_model: Callable[..., tuple],
    *,
    model: str = "",
    max_tokens: int = 1024,
) -> list[dict]:
    """Klasyfikuje batch nagłówków. `call_model` ma sygnaturę ClaudeAdvisor._call_model
    (model, tool, user_content, system, max_tokens) -> (input_dict, cost, in_tok, out_tok).
    Zwraca listę {idx, symbol, kind, severity}. Błąd LLM -> [] (best-effort, nigdy nie wywala)."""
    if not headlines:
        return []
    try:
        result = call_model(model, CLASSIFY_TOOL, build_user_content(headlines, universe), _SYSTEM, max_tokens)
        tool_input = result[0] if isinstance(result, (tuple, list)) else result
    except Exception:  # noqa: BLE001
        return []
    return parse_classification(tool_input, len(headlines))
