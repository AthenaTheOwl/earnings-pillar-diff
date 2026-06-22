from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any

from earnings_pillar_diff.model import build_delta_rows, normalize_line_items
from earnings_pillar_diff.scoring import DEFAULT_USER_AGENT, TICKERS, require_action, require_ticker

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def request_text(url: str, user_agent: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
        return response.read().decode("utf-8", errors="replace")


def command_fetch(args: argparse.Namespace) -> int:
    try:
        ticker = require_ticker(args.ticker)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    user_agent = args.user_agent or DEFAULT_USER_AGENT

    if args.filing_url:
        filing_url = args.filing_url
        filing_text = request_text(filing_url, user_agent)
    else:
        cik = TICKERS[ticker]
        submissions_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        submissions = json.loads(request_text(submissions_url, user_agent))
        recent = submissions["filings"]["recent"]
        desired_form = "10-K" if args.quarter.endswith("Q4") else "10-Q"
        selected_index = next(
            (
                idx
                for idx, form in enumerate(recent["form"])
                if form == desired_form and recent["primaryDocument"][idx]
            ),
            None,
        )
        if selected_index is None:
            raise SystemExit(f"no {desired_form} filing found for {ticker}")
        accession = recent["accessionNumber"][selected_index]
        primary = recent["primaryDocument"][selected_index]
        cik_int = str(int(cik))
        accession_path = accession.replace("-", "")
        filing_url = (
            "https://www.sec.gov/Archives/edgar/data/"
            f"{cik_int}/{accession_path}/{primary}"
        )
        filing_text = request_text(filing_url, user_agent)

    suffix = ".htm" if "<html" in filing_text.lower() else ".txt"
    filing_path = output_dir / f"{ticker}-{args.quarter}{suffix}"
    filing_path.write_text(filing_text, encoding="utf-8")
    write_json(
        output_dir / f"{ticker}-{args.quarter}.meta.json",
        {
            "ticker": ticker,
            "quarter": args.quarter,
            "filing_url": filing_url,
            "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "path": filing_path.as_posix(),
        },
    )
    print(f"wrote {filing_path}")
    return 0


def command_diff(args: argparse.Namespace) -> int:
    ticker = args.ticker.upper()
    prior_items = normalize_line_items(load_json(Path(args.prior_file)))
    current_items = normalize_line_items(load_json(Path(args.current_file)))
    rows = build_delta_rows(prior_items, current_items, args.anchor)
    row_dicts = [row.to_dict() for row in rows]

    output = Path(args.output)
    write_json(
        output,
        {
            "ticker": ticker,
            "quarter": args.quarter,
            "basis": "USD millions unless noted",
            "material_deltas": [row for row in row_dicts if row["material"]],
            "all_deltas": row_dicts,
        },
    )
    print(f"wrote {output}")
    return 0


def fmt_number(value: float) -> str:
    if value.is_integer():
        return f"{int(value):,}"
    return f"{value:,.1f}"


def fmt_pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:+.1f}%"


def command_memo(args: argparse.Namespace) -> int:
    try:
        action = require_action(args.action)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    payload = load_json(Path(args.delta_file))
    deltas = payload.get("material_deltas", [])
    if not deltas:
        raise SystemExit("delta file has no material_deltas")

    pillars = [item.strip() for item in args.pillars.split(",") if item.strip()]
    if not pillars:
        raise SystemExit("--pillars must name at least one pillar")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "---",
        f"ticker: {args.ticker.upper()}",
        f"quarter: {args.quarter}",
        f"filing_url: {args.filing_url}",
        f"filing_date: {args.filing_date}",
        "pillars_affected:",
    ]
    lines.extend(f"  - {pillar}" for pillar in pillars)
    lines.extend(
        [
            f"action: {action}",
            f'revert_threshold: "{args.revert_threshold}"',
            "---",
            "",
            "## Line-item deltas",
            "| XBRL tag | Prior | Current | Delta | EDGAR anchor |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for row in deltas:
        delta_text = f"{fmt_number(float(row['delta']))} ({fmt_pct(row.get('percent_delta'))})"
        lines.append(
            "| "
            f"{row['tag']} | {fmt_number(float(row['prior']))} | "
            f"{fmt_number(float(row['current']))} | {delta_text} | "
            f"[{row['tag']}]({row.get('anchor') or args.filing_url}) |"
        )
    lines.extend(
        [
            "",
            "## Pillar effects",
            *(f"- {pillar} CONFIRMS: material filing deltas changed the tracked input." for pillar in pillars),
            "",
            "## Action",
            f"{action}.",
            "",
            "## Revert threshold",
            args.revert_threshold,
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {output}")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    repo_root = Path(args.root)
    commands = [
        [sys.executable, "scripts/voice_lint.py", "earnings_diff/"],
        [sys.executable, "scripts/validate_memo_schema.py"],
        [
            sys.executable,
            "scripts/check_pillar_references.py",
            "--pillar-repo",
            args.pillar_repo,
        ],
    ]
    for command in commands:
        completed = subprocess.run(command, cwd=repo_root)  # noqa: S603
        if completed.returncode:
            return completed.returncode
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="epd")
    parser.add_argument("--version", action="version", version="epd 0.1.0")
    sub = parser.add_subparsers(dest="command", required=True)

    fetch = sub.add_parser("fetch", help="cache an EDGAR filing document")
    fetch.add_argument("--ticker", required=True)
    fetch.add_argument("--quarter", required=True)
    fetch.add_argument("--filing-url", default=None)
    fetch.add_argument("--output-dir", default="data/filings")
    fetch.add_argument("--user-agent", default=None)
    fetch.set_defaults(func=command_fetch)

    diff = sub.add_parser("diff", help="compute line-item deltas from JSON files")
    diff.add_argument("--ticker", required=True)
    diff.add_argument("--quarter", required=True)
    diff.add_argument("--prior-file", required=True)
    diff.add_argument("--current-file", required=True)
    diff.add_argument("--output", default=None)
    diff.add_argument("--anchor", default="")
    diff.set_defaults(func=command_diff)

    memo = sub.add_parser("memo", help="render a memo from a delta JSON file")
    memo.add_argument("--ticker", required=True)
    memo.add_argument("--quarter", required=True)
    memo.add_argument("--delta-file", required=True)
    memo.add_argument("--pillars", required=True)
    memo.add_argument("--action", required=True)
    memo.add_argument("--revert-threshold", required=True)
    memo.add_argument("--filing-url", required=True)
    memo.add_argument("--filing-date", required=True)
    memo.add_argument("--output", required=True)
    memo.set_defaults(func=command_memo)

    validate = sub.add_parser("validate", help="run repository validation gates")
    validate.add_argument("--root", default=ROOT.as_posix())
    validate.add_argument("--pillar-repo", default="../thesis-pillar-tracker")
    validate.set_defaults(func=command_validate)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "diff" and args.output is None:
        args.output = f"data/deltas/{args.ticker.upper()}-{args.quarter}.json"
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
