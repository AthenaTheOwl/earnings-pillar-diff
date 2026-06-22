# Acceptance

## Required Files

- `PRODUCT_BRIEF.md`
- `SYSTEM_MAP.md`
- `STATUS.md`
- `specs/0002-design/requirements.md`
- `specs/0002-design/design.md`
- `specs/0002-design/tasks.md`
- `specs/0002-design/acceptance.md`
- `specs/0002-design/ledger.md`
- `earnings_pillar_diff/cli.py`
- `earnings_pillar_diff/model.py`
- `earnings_pillar_diff/scoring.py`
- `reports/MSFT-2025Q4.jsonl`

## Gates

```bash
uv run pytest
python scripts/voice_lint.py earnings_diff/
python scripts/validate_memo_schema.py
python scripts/check_pillar_references.py --pillar-repo ../thesis-pillar-tracker
```

## Manual Check

Run `ls -la` on the root, `specs/0002-design`, `earnings_pillar_diff`, and
`reports` directories and confirm the required files exist.
