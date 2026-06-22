#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parents[1]


class Rule(NamedTuple):
    severity: str
    label: str
    pattern: re.Pattern[str]


def configure_streams() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
        except (AttributeError, ValueError):
            pass


def phrase_rule(severity: str, label: str, phrase: str) -> Rule:
    return Rule(severity, label, re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE))


BANNED_FAIL = [
    "leverage",
    "synergy",
    "best-in-class",
    "seamless",
    "seamlessly",
    "cutting-edge",
    "state-of-the-art",
    "production-grade",
    "portfolio-grade",
    "industry-leading",
    "world-class",
    "next-generation",
    "transformative",
    "game-changing",
    "revolutionary",
    "significant",
    "substantial",
    "innovative",
    "utilize",
    "delve",
    "tapestry",
    "testament to",
    "myriad",
    "in the realm of",
    "it is worth noting",
    "it is important to note",
    "it goes without saying",
    "in conclusion",
    "in summary",
    "at the end of the day",
    "shed light",
    "pivotal",
    "embark",
    "facilitate",
    "showcase",
    "crucial role",
]

BANNED_WARN = [
    "clearly",
    "obviously",
    "basically",
    "actually",
    "literally",
    "very",
    "quite",
    "somewhat",
    "rather",
    "seemingly",
    "moreover",
    "furthermore",
]

STRUCTURAL = [
    Rule("FAIL", "not-just-but", re.compile(r"\bnot\s+(?:just|only|merely|simply)\b[^.!?\n]{1,80}\bbut\b", re.IGNORECASE)),
    Rule("FAIL", "more-than-just", re.compile(r"\bmore\s+than\s+just\b", re.IGNORECASE)),
    Rule("FAIL", "the-point-is", re.compile(r"\bthe\s+point\s+(?:is|is\s+not|isn't)\b", re.IGNORECASE)),
    Rule("FAIL", "not-because-because", re.compile(r"\bnot\s+because\s+[^.!?\n]{1,100}[.!?]\s+because\s+", re.IGNORECASE)),
]

ALLOWLIST_RE = re.compile(r"voice_lint:allow\s+([A-Za-z0-9\-_ ]+)")
DEFAULT_TARGETS = ["README.md", "docs/**/*.md", "specs/**/*.md", "earnings_diff/**/*.md"]
SKIP_DIRS = {".git", ".venv", "data", "node_modules", "dist"}


def line_allowlist(line: str) -> set[str]:
    match = ALLOWLIST_RE.search(line)
    if not match:
        return set()
    return {label.strip() for label in match.group(1).split() if label.strip()}


def rules() -> list[Rule]:
    out = [phrase_rule("FAIL", f"banned-{phrase}", phrase) for phrase in BANNED_FAIL]
    out.extend(phrase_rule("WARN", f"weak-{phrase}", phrase) for phrase in BANNED_WARN)
    out.extend(STRUCTURAL)
    return out


def iter_files(root: Path, targets: list[str]) -> list[Path]:
    files: set[Path] = set()
    for target in targets:
        candidate = (root / target).resolve() if not Path(target).is_absolute() else Path(target)
        if candidate.exists():
            if candidate.is_file():
                files.add(candidate)
            else:
                for path in candidate.rglob("*.md"):
                    if not any(part in SKIP_DIRS for part in path.parts):
                        files.add(path)
            continue
        for path in root.glob(target):
            if path.is_file() and not any(part in SKIP_DIRS for part in path.parts):
                files.add(path)
    return sorted(files)


def scan(path: Path, active_rules: list[Rule]) -> list[tuple[str, int, str, str]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []
    offenses: list[tuple[str, int, str, str]] = []
    for line_no, line in enumerate(lines, start=1):
        allowed = line_allowlist(line)
        if "all" in allowed:
            continue
        for severity, label, pattern in active_rules:
            if label in allowed:
                continue
            if pattern.search(line):
                offenses.append((severity, line_no, label, line.strip()))
    return offenses


def main(argv: list[str] | None = None) -> int:
    configure_streams()
    parser = argparse.ArgumentParser(description="lint memo and repo prose")
    parser.add_argument("targets", nargs="*", help="files, directories, or globs to scan")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--warn-only", action="store_true")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    targets = args.targets or DEFAULT_TARGETS
    files = iter_files(root, targets)
    total = 0
    fail_total = 0
    warn_total = 0
    for file_path in files:
        for severity, line_no, label, line_text in scan(file_path, rules()):
            rel = file_path.relative_to(root).as_posix()
            snippet = line_text if len(line_text) <= 200 else line_text[:200] + "..."
            print(f"{rel}:{line_no}: {severity}: {label} -> {snippet}")
            total += 1
            if severity == "FAIL":
                fail_total += 1
            else:
                warn_total += 1
    if total:
        print(f"voice-lint: {fail_total} FAIL, {warn_total} WARN across {len(files)} file(s).", file=sys.stderr)
        return 0 if args.warn_only or fail_total == 0 else 1
    print(f"voice-lint: clean. {len(files)} file(s) scanned.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
