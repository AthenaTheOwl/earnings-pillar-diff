from __future__ import annotations

import calendar
import datetime as dt
import re

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


def filing_form(quarter: str) -> str:
    """Fiscal Q4 is reported in the annual 10-K; Q1-Q3 in a 10-Q."""
    return "10-K" if quarter.endswith("Q4") else "10-Q"


def fiscal_period_end(quarter: str, fiscal_year_end: str) -> dt.date:
    """Nominal end date of fiscal `quarter` (e.g. 2025Q4) given the issuer's
    fiscal year end as EDGAR's MMDD string (e.g. "0630").

    A fiscal year is named for the calendar year it ends in, so MSFT 2025Q4
    ends 2025-06-30 and 2025Q1 ends 2024-09-30.
    """
    match = re.fullmatch(r"(\d{4})Q([1-4])", quarter)
    if not match:
        raise ValueError(f"quarter must look like 2025Q4, got {quarter!r}")
    if not re.fullmatch(r"\d{4}", fiscal_year_end or ""):
        raise ValueError(f"fiscal year end must be MMDD, got {fiscal_year_end!r}")
    year, fiscal_quarter = int(match.group(1)), int(match.group(2))
    fy_month, fy_day = int(fiscal_year_end[:2]), int(fiscal_year_end[2:])
    month_index = year * 12 + (fy_month - 1) - 3 * (4 - fiscal_quarter)
    end_year, end_month = divmod(month_index, 12)
    end_month += 1
    last_day = calendar.monthrange(end_year, end_month)[1]
    fy_month_last_day = calendar.monthrange(year, fy_month)[1]
    day = last_day if fy_day >= fy_month_last_day else min(fy_day, last_day)
    return dt.date(end_year, end_month, day)


def comparison_basis(form: str) -> str:
    """The comparable period a delta from this form is measured against."""
    return "prior fiscal year" if form == "10-K" else "prior quarter"


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

