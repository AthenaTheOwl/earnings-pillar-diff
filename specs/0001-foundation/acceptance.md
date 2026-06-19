# Acceptance — 0001 Foundation

## What v0 done means

- `make validate` passes on a clean clone with the one hand-written
  sample memo committed.
- `uv run epd fetch --ticker MSFT --quarter 2026Q2` pulls and caches an
  EDGAR XBRL document.
- `uv run epd diff --ticker MSFT --quarter 2026Q2` produces a delta
  JSON whose values match a hand-computed reference.
- `uv run epd memo --ticker MSFT --quarter 2026Q2 --pillar-repo PATH`
  produces a memo file that passes voice_lint and schema validation.

## Commands to run

```bash
git clone <repo>
cd earnings-pillar-diff
uv sync
make validate
uv run epd fetch --ticker MSFT --quarter 2026Q2
uv run epd diff --ticker MSFT --quarter 2026Q2
```

Expected: zero exit codes; cached XBRL and delta JSON appear under
`data/`.

## Gates to pass

- `python scripts/voice_lint.py earnings_diff/` — no banned terms.
- `python scripts/validate_memo_schema.py` — every memo file's
  frontmatter validates.
- `python scripts/check_pillar_references.py --pillar-repo PATH` — every
  pillar ID referenced exists as active.
- `uv run pytest` — fetch and diff cases pass.

## Out of scope for acceptance

- Memo CLI is PR 3, not the acceptance target.
- Additional tickers are spec 0003.
