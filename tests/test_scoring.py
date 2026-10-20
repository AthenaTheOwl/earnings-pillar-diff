from __future__ import annotations

import datetime as dt

from earnings_pillar_diff.scoring import (
    comparison_basis,
    filing_form,
    fiscal_period_end,
    material_delta,
    percent_delta,
)


def test_percent_delta_sign_and_zero_prior() -> None:
    # +12.5% move, and the zero-prior branch that must return None (no ratio).
    assert percent_delta(1000, 1125) == 0.125
    assert percent_delta(1000, 875) == -0.125
    assert percent_delta(0, 5) is None


def test_material_delta_delta_branch_includes() -> None:
    # 125 absolute change clears threshold min(1000*0.05, 500) = 50.
    assert material_delta(1000, 1125) is True


def test_material_delta_pct_branch_includes() -> None:
    # Small absolute change (1.0) below the 500 cap, but 5% pct clears 0.05.
    assert material_delta(20, 21) is True


def test_material_delta_below_threshold_excludes() -> None:
    # 2% move: 20 < threshold 50 and 0.02 < 0.05, so neither branch fires.
    assert material_delta(1000, 1020) is False


def test_filing_form_and_comparison_basis_follow_fiscal_quarter() -> None:
    # fiscal Q4 is the annual 10-K, measured against the prior fiscal year.
    assert filing_form("2025Q4") == "10-K"
    assert comparison_basis("10-K") == "prior fiscal year"
    # interim quarters are 10-Qs, measured against the prior quarter.
    assert filing_form("2026Q1") == "10-Q"
    assert comparison_basis("10-Q") == "prior quarter"


def test_fiscal_period_end_names_fiscal_year_by_its_end() -> None:
    # MSFT: fiscal year ends June 30
    assert fiscal_period_end("2025Q4", "0630") == dt.date(2025, 6, 30)
    assert fiscal_period_end("2025Q1", "0630") == dt.date(2024, 9, 30)
    assert fiscal_period_end("2025Q2", "0630") == dt.date(2024, 12, 31)
    # calendar fiscal year
    assert fiscal_period_end("2025Q1", "1231") == dt.date(2025, 3, 31)
