# Tasks — 0001 Foundation

## PR 1 — Schema + voice gate

- [ ] Add `schemas/memo.schema.json` for the YAML frontmatter
- [ ] Add `scripts/validate_memo_schema.py`
- [ ] Add `scripts/voice_lint.py` copied from sports-prediction-os
- [ ] Add `scripts/check_pillar_references.py`
- [ ] Add `Makefile` with `validate` target
- [ ] Add one hand-written sample memo at `earnings_diff/MSFT-2025Q4.md`
- [ ] Confirm `make validate` passes

## PR 2 — MSFT fetch + diff

- [ ] Add `pyproject.toml` with `epd` console script
- [ ] Implement `epd fetch --ticker MSFT --quarter QUARTER`
- [ ] Implement `epd diff --ticker MSFT --quarter QUARTER`
- [ ] Add fixtures for the 2026Q1 and 2026Q2 MSFT 10-Qs
- [ ] Add pytest cases asserting expected line-item deltas
- [ ] Wire `make test` to run pytest + validate

## PR 3 — memo subcommand

- [ ] Implement `epd memo` with interactive pillar-mapping prompt
- [ ] Render the memo template per design.md
- [ ] Add a smoke test asserting the rendered memo passes
  `validate_memo_schema.py` and `voice_lint.py`
- [ ] Document the 24-hour SLA in README

## Out of scope for foundation

- [ ] ORCL, AMZN, META, GOOG parsers (spec 0003)
- [ ] LLM-assisted pillar mapping (spec 0004)
- [ ] 90-day outcome capture (spec 0005)
