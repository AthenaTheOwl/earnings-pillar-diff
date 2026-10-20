from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from epd.cli import main
from epd.cli import parse_usd

ROOT = Path(__file__).resolve().parents[1]


def test_parse_usd_handles_signed_million_strings() -> None:
    assert parse_usd("-USD 15,700M") == -15700.0
    assert parse_usd("+USD 20,074M") == 20074.0
    assert parse_usd(1234) == 1234.0
    assert parse_usd("") == 0.0


def test_show_prints_ranked_committed_report(capsys) -> None:
    code = main(["show"])
    assert code == 0
    out = capsys.readouterr().out
    # header line names the ticker/quarter of the committed report
    assert "MSFT 2025Q4" in out
    # fiscal Q4 is the annual 10-K, so the deltas are against the prior fiscal
    # year, not a prior quarter
    assert "MSFT 2025Q4 10-K line-item deltas" in out
    assert "2 delta(s) vs prior fiscal year" in out
    assert "10-Q" not in out
    assert "vs prior quarter" not in out
    # capex (+20,074M) is the biggest absolute move, so it leads the headline
    assert "biggest move: PaymentsToAcquirePropertyPlantAndEquipment" in out
    # the ranked table lists both delta rows
    assert "UnrecordedUnconditionalPurchaseObligation"[:30] in out
    assert "action on MSFT 2025Q4: HOLD." in out


def test_show_labels_interim_report_as_10q_vs_prior_quarter(tmp_path, capsys) -> None:
    report = tmp_path / "MSFT-2026Q1.jsonl"
    report.write_text(
        "\n".join(
            json.dumps(row)
            for row in [
                {"type": "report", "ticker": "MSFT", "quarter": "2026Q1", "action": "HOLD"},
                {
                    "type": "delta",
                    "tag": "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment",
                    "prior": "USD 100M",
                    "current": "USD 125M",
                    "delta": "+USD 25M",
                    "percent_delta": "+25.0%",
                },
            ]
        ),
        encoding="utf-8",
    )
    assert main(["show", "--report", str(report)]) == 0
    out = capsys.readouterr().out
    assert "MSFT 2026Q1 10-Q line-item deltas" in out
    assert "1 delta(s) vs prior quarter" in out


def test_diff_writes_material_delta() -> None:
    with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
        temp_path = Path(temp_dir)
        prior = temp_path / "prior.json"
        current = temp_path / "current.json"
        output = temp_path / "delta.json"
        prior.write_text(
            json.dumps(
                {
                    "line_items": [
                        {
                            "tag": "us-gaap:PurchaseObligation",
                            "value": 1000,
                            "anchor": "https://www.sec.gov/example-prior",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        current.write_text(
            json.dumps(
                {
                    "line_items": [
                        {
                            "tag": "us-gaap:PurchaseObligation",
                            "value": 1125,
                            "anchor": "https://www.sec.gov/example-current",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        code = main(
            [
                "diff",
                "--ticker",
                "MSFT",
                "--quarter",
                "2025Q4",
                "--prior-file",
                str(prior),
                "--current-file",
                str(current),
                "--output",
                str(output),
            ]
        )

        assert code == 0
        payload = json.loads(output.read_text(encoding="utf-8"))
        assert payload["material_deltas"][0]["delta"] == 125
        assert payload["material_deltas"][0]["tag"] == "us-gaap:PurchaseObligation"
        # pin the percent_delta sign/formula through the diff path (1000 -> 1125)
        assert payload["material_deltas"][0]["percent_delta"] == 0.125


def test_fetch_picks_the_filing_for_the_requested_fiscal_period(tmp_path, monkeypatch) -> None:
    import earnings_pillar_diff.cli as cli

    submissions = {
        "fiscalYearEnd": "0630",
        "filings": {
            "recent": {
                "form": ["10-Q", "10-K", "10-Q", "10-K"],
                "accessionNumber": [
                    "0001193125-26-400000",
                    "0001193125-26-323660",
                    "0000950170-25-150000",
                    "0000950170-25-100235",
                ],
                "primaryDocument": [
                    "msft-20260930.htm",
                    "msft-20260630.htm",
                    "msft-20250930.htm",
                    "msft-20250630.htm",
                ],
                "reportDate": ["2026-09-30", "2026-06-30", "2025-09-30", "2025-06-30"],
            }
        },
    }

    def fake_request_text(url: str, user_agent: str) -> str:
        if "submissions" in url:
            return json.dumps(submissions)
        return f"<html>{url}</html>"

    monkeypatch.setattr(cli, "request_text", fake_request_text)

    # the newest 10-K is FY2026; FY2025Q4 must still resolve to the FY2025 10-K
    args = ["fetch", "--ticker", "MSFT", "--output-dir", str(tmp_path)]
    assert cli.main([*args, "--quarter", "2025Q4"]) == 0
    meta = json.loads((tmp_path / "MSFT-2025Q4.meta.json").read_text(encoding="utf-8"))
    assert meta["filing_url"].endswith("/000095017025100235/msft-20250630.htm")

    # no FY2024 10-K in the list: fail instead of caching the FY2026 10-K as 2024Q4
    with pytest.raises(SystemExit, match="no 10-K filing for MSFT 2024Q4"):
        cli.main([*args, "--quarter", "2024Q4"])
    assert not (tmp_path / "MSFT-2024Q4.htm").exists()
