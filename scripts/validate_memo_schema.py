#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ACTIONS = {"HOLD", "TRIM", "ADD", "HEDGE"}
TICKERS = {"MSFT", "GOOG", "AMZN", "META", "ORCL"}


def configure_streams() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
        except (AttributeError, ValueError):
            pass


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(part.strip()) for part in inner.split(",")]
    return value


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing YAML frontmatter")
    try:
        end = next(idx for idx in range(1, len(lines)) if lines[idx].strip() == "---")
    except StopIteration as exc:
        raise ValueError("unterminated YAML frontmatter") from exc

    data: dict[str, Any] = {}
    current_key: str | None = None
    for raw_line in lines[1:end]:
        if not raw_line.strip():
            continue
        if raw_line.startswith("  - "):
            if current_key is None:
                raise ValueError("list item without key")
            data.setdefault(current_key, []).append(parse_scalar(raw_line[4:]))
            continue
        if ":" not in raw_line:
            raise ValueError(f"invalid frontmatter line: {raw_line}")
        key, raw_value = raw_line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        current_key = key
        data[key] = [] if raw_value == "" else parse_scalar(raw_value)
    body = "\n".join(lines[end + 1 :])
    return data, body


def line_item_rows(body: str) -> list[str]:
    lines = body.splitlines()
    in_section = False
    rows: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            in_section = stripped.lower() == "## line-item deltas"
            continue
        if in_section and stripped.startswith("|"):
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if len(cells) < 5:
                continue
            if set(cells[0]) <= {"-", ":"}:
                continue
            if cells[0].lower() in {"xbrl tag", "tag"}:
                continue
            rows.append(stripped)
    return rows


def validate_frontmatter(path: Path, data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {
        "ticker",
        "quarter",
        "filing_url",
        "filing_date",
        "pillars_affected",
        "action",
        "revert_threshold",
    }
    missing = sorted(required - set(data))
    if missing:
        errors.append(f"missing required fields: {', '.join(missing)}")
        return errors

    if data["ticker"] not in TICKERS:
        errors.append("ticker must be one of MSFT, GOOG, AMZN, META, ORCL")
    if not re.fullmatch(r"\d{4}Q[1-4]", str(data["quarter"])):
        errors.append("quarter must match YYYYQn")
    if not str(data["filing_url"]).startswith("https://www.sec.gov/"):
        errors.append("filing_url must be an EDGAR URL")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}Z)?", str(data["filing_date"])):
        errors.append("filing_date must be YYYY-MM-DD or UTC timestamp")
    pillars = data["pillars_affected"]
    if not isinstance(pillars, list) or not pillars:
        errors.append("pillars_affected must be a non-empty list")
    elif len(set(pillars)) != len(pillars):
        errors.append("pillars_affected must not contain duplicates")
    elif any(not re.fullmatch(r"[a-z0-9][a-z0-9-]*[a-z0-9]", str(pillar)) for pillar in pillars):
        errors.append("pillar IDs must use lowercase slug format")
    if data["action"] not in ACTIONS:
        errors.append("action must be one of HOLD, TRIM, ADD, HEDGE")
    threshold = str(data["revert_threshold"])
    if len(threshold) < 12 or not re.search(r"\d", threshold):
        errors.append("revert_threshold must be measurable")
    if path.name != f"{data['ticker']}-{data['quarter']}.md":
        errors.append("memo filename must be <TICKER>-<YYYYQn>.md")
    return errors


def validate_memo(path: Path) -> list[str]:
    try:
        data, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        return [str(exc)]

    errors = validate_frontmatter(path, data)
    rows = line_item_rows(body)
    if not rows:
        errors.append("Line-item deltas section must contain at least one data row")
    for idx, row in enumerate(rows, start=1):
        if "https://www.sec.gov/" not in row:
            errors.append(f"delta row {idx} missing EDGAR URL")
        if not re.search(r"\b[a-zA-Z0-9]+:[A-Za-z0-9]+", row):
            errors.append(f"delta row {idx} missing XBRL tag")
    return errors


def iter_memos(root: Path) -> list[Path]:
    memo_dir = root / "earnings_diff"
    if not memo_dir.exists():
        return []
    return sorted(path for path in memo_dir.glob("*.md") if path.is_file())


def main(argv: list[str] | None = None) -> int:
    configure_streams()
    parser = argparse.ArgumentParser(description="validate earnings memo schema")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)

    root = args.root.resolve()
    memos = iter_memos(root)
    if not memos:
        print("ERROR: no memos found under earnings_diff/", file=sys.stderr)
        return 1

    failures = 0
    for memo in memos:
        errors = validate_memo(memo)
        for error in errors:
            print(f"{memo.relative_to(root).as_posix()}: ERROR: {error}")
        failures += len(errors)

    if failures:
        print(f"memo-schema: {failures} error(s) across {len(memos)} memo(s).", file=sys.stderr)
        return 1
    print(f"OK: {len(memos)} memo validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
