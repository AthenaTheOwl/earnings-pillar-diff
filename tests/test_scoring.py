from __future__ import annotations

from earnings_pillar_diff.scoring import material_delta, percent_delta


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
