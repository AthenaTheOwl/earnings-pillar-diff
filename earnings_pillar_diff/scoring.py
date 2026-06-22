from __future__ import annotations

TICKERS = {
    "MSFT": "0000789019",
    "GOOG": "0001652044",
    "AMZN": "0001018724",
    "META": "0001326801",
    "ORCL": "0001341439",
}

ACTIONS = {"HOLD", "TRIM", "ADD", "HEDGE"}
DEFAULT_USER_AGENT = "earnings-pillar-diff/0.1 data-report contact@example.com"


def percent_delta(prior: float, current: float) -> float | None:
    if prior == 0:
        return None
    return (current - prior) / abs(prior)


def material_delta(prior: float, current: float) -> bool:
    delta = abs(current - prior)
    pct = delta / abs(prior) if prior else 1.0
    threshold = min(abs(prior) * 0.05, 500.0) if prior else 500.0
    return delta >= threshold or pct >= 0.05


def require_action(action: str) -> str:
    normalized = action.upper()
    if normalized not in ACTIONS:
        raise ValueError(f"unsupported action: {action}")
    return normalized


def require_ticker(ticker: str) -> str:
    normalized = ticker.upper()
    if normalized not in TICKERS:
        raise ValueError(f"unsupported ticker: {ticker}")
    return normalized

