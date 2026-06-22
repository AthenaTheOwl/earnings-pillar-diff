from __future__ import annotations

import json
import tempfile
from pathlib import Path

from epd.cli import main

ROOT = Path(__file__).resolve().parents[1]


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
