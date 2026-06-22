from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_sample_memo_schema_validates() -> None:
    result = run_script("scripts/validate_memo_schema.py")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK: 1 memo validated." in result.stdout


def test_voice_lint_accepts_sample_memo() -> None:
    result = run_script("scripts/voice_lint.py", "earnings_diff/")
    assert result.returncode == 0, result.stdout + result.stderr


def test_pillar_checker_accepts_active_fixture_pillar() -> None:
    result = run_script(
        "scripts/check_pillar_references.py",
        "--pillar-repo",
        "tests/fixtures/pillar_repo",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK: 1 pillar reference checked." in result.stdout
