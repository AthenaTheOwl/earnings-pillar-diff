# Requirements

## Functional

- The repo shall expose a Python CLI named `epd`.
- The CLI shall support `fetch`, `diff`, `memo`, and `validate` commands.
- The package import path shall be `earnings_pillar_diff`.
- Each memo shall include ticker, quarter, EDGAR filing URL, filing date,
  affected pillar IDs, action, and revert threshold.
- Each material delta shall include an XBRL tag, prior value, current value,
  delta, and EDGAR URL.
- The repo shall include at least one checked-in JSONL report artifact under
  `reports/`.

## Validation

- `uv run pytest` shall pass.
- `python scripts/voice_lint.py earnings_diff/` shall pass.
- `python scripts/validate_memo_schema.py` shall pass.
- `python scripts/check_pillar_references.py --pillar-repo ../thesis-pillar-tracker`
  shall pass when the linked pillar repo is present.

## Packaging

- Dev dependencies shall live under `[dependency-groups]`.
- `[tool.uv] package = true` shall be present.
- The build backend shall install `earnings_pillar_diff` as the project package.
