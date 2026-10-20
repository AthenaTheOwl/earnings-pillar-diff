"""Lease-axis facts are lease commitments, and lease classes are summed.

The fixtures under tests/fixtures/filings/ are verbatim excerpts of four
Microsoft filings: the ix:nonFraction facts for
us-gaap:UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount and
us-gaap:PaymentsToAcquirePropertyPlantAndEquipment, and the contexts they
reference.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from earnings_pillar_diff.cli import main, read_report
from earnings_pillar_diff.model import build_delta_rows, normalize_line_items
from earnings_pillar_diff.xbrl import (
    LEASE_COMMITMENT_LABEL,
    extract_facts,
    line_item_label,
    line_items_for_period,
)

ROOT = Path(__file__).resolve().parents[1]
FILINGS = ROOT / "tests" / "fixtures" / "filings"
OBLIGATION = "us-gaap:UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount"
CAPEX = "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment"
LEASE_AXIS = "us-gaap:LeaseContractualTermAxis"


def filing_items(stem: str, period_end: str, months: int = 12) -> list[dict]:
    text = (FILINGS / f"{stem}.excerpt.htm").read_text(encoding="utf-8")
    return line_items_for_period(extract_facts(text), period_end, months)


def obligation_row(prior: list[dict], current: list[dict]):
    rows = build_delta_rows(normalize_line_items(prior), normalize_line_items(current))
    matches = [row for row in rows if row.tag == OBLIGATION]
    assert len(matches) == 1, matches
    return matches[0]


def test_extractor_reads_the_lease_axis_and_labels_a_lease_commitment() -> None:
    text = (FILINGS / "msft-20240630.excerpt.htm").read_text(encoding="utf-8")
    facts = {(f.concept, f.context.dimensions): f for f in extract_facts(text)}

    operating = facts[(OBLIGATION, ((LEASE_AXIS, "msft:OperatingLeaseMember"),))]
    finance = facts[(OBLIGATION, ((LEASE_AXIS, "msft:FinanceLeaseMember"),))]
    assert (operating.value, finance.value) == (8600.0, 108400.0)
    # the tag says purchase obligation; the axis says lease
    assert operating.label == finance.label == LEASE_COMMITMENT_LABEL
    assert "PurchaseObligation" not in operating.label

    capex = facts[(CAPEX, ())]
    assert capex.value == 44477.0
    assert capex.label == "PaymentsToAcquirePropertyPlantAndEquipment"


def test_label_depends_on_the_axis_not_the_tag_alone() -> None:
    assert line_item_label(OBLIGATION, LEASE_AXIS) == LEASE_COMMITMENT_LABEL
    # with no lease axis the same tag is what it says it is
    assert line_item_label(OBLIGATION) == "UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount"
    # other concepts on a lease axis are not called commitments
    assert (
        line_item_label("us-gaap:PropertyPlantAndEquipmentGross", LEASE_AXIS)
        == "PropertyPlantAndEquipmentGross (lease classes)"
    )


def test_fy2025_delta_sums_lease_classes_like_for_like() -> None:
    prior = filing_items("msft-20240630", "2024-06-30")
    current = filing_items("msft-20250630", "2025-06-30")
    row = obligation_row(prior, current)

    # FY2024 operating 8.6B + finance 108.4B against FY2025 combined 92.7B
    assert row.prior == 117000.0
    assert row.current == 92700.0
    assert row.delta == -24300.0
    assert round(row.percent_delta * 100, 1) == -20.8
    assert row.label == LEASE_COMMITMENT_LABEL
    assert row.prior_members == ("msft:OperatingLeaseMember", "msft:FinanceLeaseMember")
    assert row.current_members == ("msft:OperatingLeaseMember",)

    capex = next(r for r in build_delta_rows(normalize_line_items(prior), normalize_line_items(current)) if r.tag == CAPEX)
    assert (capex.prior, capex.current) == (44477.0, 64551.0)


def test_member_flip_between_filings_stays_one_line_item() -> None:
    # the combined figure moves from the operating member (FY2025 10-K) to
    # the finance member (Q1 FY2026 10-Q); the sum still lines up
    prior = filing_items("msft-20250630", "2025-06-30")
    current = filing_items("msft-20250930", "2025-09-30", months=3)
    row = obligation_row(prior, current)
    assert row.prior_members == ("msft:OperatingLeaseMember",)
    assert row.current_members == ("msft:FinanceLeaseMember",)
    assert (row.prior, row.current) == (92700.0, 106200.0)


def test_duplicate_rows_are_an_error_not_last_one_wins() -> None:
    with pytest.raises(ValueError, match="listed twice"):
        normalize_line_items([{"tag": CAPEX, "value": 1}, {"tag": CAPEX, "value": 2}])
    with pytest.raises(ValueError, match="listed twice"):
        normalize_line_items(
            [
                {"tag": OBLIGATION, "value": 1, "axis": LEASE_AXIS, "member": "msft:FinanceLeaseMember"},
                {"tag": OBLIGATION, "value": 2, "axis": LEASE_AXIS, "member": "msft:FinanceLeaseMember"},
            ]
        )


def test_nil_fact_does_not_swallow_the_next_fact() -> None:
    text = (
        '<xbrli:context id="c1"><xbrli:entity></xbrli:entity><xbrli:period>'
        "<xbrli:instant>2025-06-30</xbrli:instant></xbrli:period></xbrli:context>"
        '<ix:nonFraction name="us-gaap:Liabilities" contextRef="c1" unitRef="U_USD" xsi:nil="true"/>'
        '<ix:nonFraction name="us-gaap:Assets" contextRef="c1" unitRef="U_USD" scale="6">1,234</ix:nonFraction>'
    )
    facts = extract_facts(text)
    assert [(f.concept, f.value) for f in facts] == [("us-gaap:Assets", 1234.0)]


def load_memo_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_memo_schema", ROOT / "scripts" / "validate_memo_schema.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_extract_diff_memo_names_the_lease_commitment(tmp_path) -> None:
    files = {
        "prior": ("msft-20240630", "2024-06-30"),
        "current": ("msft-20250630", "2025-06-30"),
    }
    for side, (stem, period_end) in files.items():
        assert (
            main(
                [
                    "extract",
                    "--filing",
                    str(FILINGS / f"{stem}.excerpt.htm"),
                    "--period-end",
                    period_end,
                    "--anchor",
                    f"https://www.sec.gov/Archives/edgar/data/789019/{stem}.htm",
                    "--output",
                    str(tmp_path / f"{side}.json"),
                ]
            )
            == 0
        )
    delta = tmp_path / "delta.json"
    assert (
        main(
            [
                "diff",
                "--ticker",
                "MSFT",
                "--quarter",
                "2025Q4",
                "--prior-file",
                str(tmp_path / "prior.json"),
                "--current-file",
                str(tmp_path / "current.json"),
                "--output",
                str(delta),
            ]
        )
        == 0
    )
    memo = tmp_path / "MSFT-2025Q4.md"
    assert (
        main(
            [
                "memo",
                "--ticker",
                "MSFT",
                "--quarter",
                "2025Q4",
                "--delta-file",
                str(delta),
                "--pillars",
                "chip-cowos-2027",
                "--action",
                "HOLD",
                "--revert-threshold",
                "If next-quarter leases not yet commenced fall below USD 85,000M, change action to TRIM.",
                "--filing-url",
                "https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm",
                "--filing-date",
                "2025-07-30",
                "--output",
                str(memo),
            ]
        )
        == 0
    )
    text = memo.read_text(encoding="utf-8")
    lease_line = next(line for line in text.splitlines() if OBLIGATION in line and "|" in line)
    assert f"{OBLIGATION} on {LEASE_AXIS}" in lease_line
    assert LEASE_COMMITMENT_LABEL in lease_line
    assert "msft:OperatingLeaseMember + msft:FinanceLeaseMember" in lease_line
    assert "| 117,000 | 92,700 | -24,300 (-20.8%) |" in lease_line
    assert "-14.5%" not in text
    # the template still passes the memo gate
    validator = load_memo_validator()
    assert validator.validate_memo(memo) == []


def test_committed_report_lease_row_matches_the_filings() -> None:
    header, deltas = read_report(ROOT / "reports" / "MSFT-2025Q4.jsonl")
    row = next(d for d in deltas if d["tag"] == OBLIGATION)
    computed = obligation_row(
        filing_items("msft-20240630", "2024-06-30"), filing_items("msft-20250630", "2025-06-30")
    )
    assert row["axis"] == LEASE_AXIS
    assert row["prior"] == f"USD {computed.prior:,.0f}M"
    assert row["current"] == f"USD {computed.current:,.0f}M"
    assert row["delta"] == f"-USD {abs(computed.delta):,.0f}M"
    assert row["percent_delta"] == f"{computed.percent_delta * 100:+.1f}%"
    assert row["prior_members"] == list(computed.prior_members)
    assert row["current_members"] == list(computed.current_members)
    # the first-reported figures are kept beside the correction
    assert row["as_first_reported"]["percent_delta"] == "-14.5%"
    # the recorded call is left as written
    assert header["action"] == "HOLD"
    assert header["revert_threshold"].startswith("If next-quarter purchase obligations fall below USD 85,000M")


def test_show_names_the_lease_row_a_lease_commitment(capsys) -> None:
    assert main(["show"]) == 0
    out = capsys.readouterr().out
    table = [line for line in out.splitlines() if line.startswith(LEASE_COMMITMENT_LABEL)]
    assert table and "-20.8%" in table[0] and "USD 117,000M" in table[0]
    assert "reported as a lease commitment, not a purchase obligation" in out
    assert "first reported as USD 108,400M -> USD 92,700M (-USD 15,700M, -14.5%)" in out
    assert "correction: 2026-10-20, corrections/MSFT-2025Q4.md" in out


def test_show_derives_the_label_from_the_axis(tmp_path, capsys) -> None:
    report = tmp_path / "MSFT-2026Q4.jsonl"
    rows = [
        {"type": "report", "ticker": "MSFT", "quarter": "2026Q4", "action": "HOLD"},
        {
            "type": "delta",
            "tag": OBLIGATION,
            "label": "purchase obligations",
            "axis": LEASE_AXIS,
            "prior_members": ["msft:OperatingLeaseMember"],
            "current_members": ["msft:OperatingLeaseMember"],
            "prior": "USD 92,700M",
            "current": "USD 329,100M",
            "delta": "+USD 236,400M",
            "percent_delta": "+255.0%",
        },
    ]
    report.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    assert main(["show", "--report", str(report)]) == 0
    out = capsys.readouterr().out
    assert f"biggest move: {LEASE_COMMITMENT_LABEL} USD 92,700M" in out
    assert "purchase obligations" not in out
