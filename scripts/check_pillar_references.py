#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_memo_schema import parse_frontmatter  # noqa: E402


def configure_streams() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
        except (AttributeError, ValueError):
            pass


def frontmatter_from_file(path: Path) -> dict[str, Any] | None:
    try:
        data, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return None
    return data


def collect_active_pillars(pillar_repo: Path) -> set[str]:
    active: set[str] = set()
    for pattern in ("thesis/*.md", "pillars/*.md", "thesis/**/*.md"):
        for path in pillar_repo.glob(pattern):
            data = frontmatter_from_file(path)
            if not data:
                continue
            if str(data.get("status", "")).lower() == "active" and data.get("id"):
                active.add(str(data["id"]))

    if active:
        return active

    # Scaffold bridge: before thesis-pillar-tracker has real thesis files,
    # its spec docs carry the same frontmatter shape inside fenced examples.
    for path in sorted((pillar_repo / "specs").glob("**/*.md")):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for block in re.findall(r"```(?:yaml)?\n(.*?)\n```", text, flags=re.DOTALL):
            pillar_id_match = re.search(r"^id:\s*([a-z0-9][a-z0-9-]*[a-z0-9])\s*$", block, flags=re.MULTILINE)
            status_match = re.search(r"^status:\s*active\s*$", block, flags=re.MULTILINE)
            if pillar_id_match and status_match:
                active.add(pillar_id_match.group(1))
    return active


def memo_pillars(root: Path) -> list[tuple[Path, list[str]]]:
    rows: list[tuple[Path, list[str]]] = []
    for path in sorted((root / "earnings_diff").glob("*.md")):
        data = frontmatter_from_file(path)
        if not data:
            rows.append((path, []))
            continue
        raw = data.get("pillars_affected", [])
        rows.append((path, [str(item) for item in raw] if isinstance(raw, list) else []))
    return rows


def main(argv: list[str] | None = None) -> int:
    configure_streams()
    parser = argparse.ArgumentParser(description="check memo pillar references")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--pillar-repo", type=Path, required=True)
    args = parser.parse_args(argv)

    root = args.root.resolve()
    pillar_repo = (root / args.pillar_repo).resolve() if not args.pillar_repo.is_absolute() else args.pillar_repo.resolve()
    if not pillar_repo.exists():
        print(f"ERROR: pillar repo not found: {pillar_repo}", file=sys.stderr)
        return 1

    active = collect_active_pillars(pillar_repo)
    if not active:
        print(f"ERROR: no active pillars found in {pillar_repo}", file=sys.stderr)
        return 1

    failures = 0
    checked = 0
    for path, pillars in memo_pillars(root):
        rel = path.relative_to(root).as_posix()
        if not pillars:
            print(f"{rel}: ERROR: no pillars_affected entries")
            failures += 1
            continue
        for pillar in pillars:
            checked += 1
            if pillar not in active:
                print(f"{rel}: ERROR: inactive or missing pillar: {pillar}")
                failures += 1
    if failures:
        print(f"pillar-check: {failures} error(s) across {checked} reference(s).", file=sys.stderr)
        return 1
    print(f"OK: {checked} pillar reference checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
