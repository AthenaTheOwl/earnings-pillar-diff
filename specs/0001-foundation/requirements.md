# Requirements — 0001 Foundation

## Functional requirements

- **R-EPD-001** The repo SHALL emit one memo file per (ticker, quarter)
  pair, named `earnings_diff/<TICKER>-<YYYYQN>.md`.
- **R-EPD-002** Each memo SHALL include a YAML frontmatter block with
  fields: `ticker`, `quarter`, `filing_url`, `filing_date`,
  `pillars_affected`, `action`, `revert_threshold`.
- **R-EPD-003** The `action` field SHALL be one of {HOLD, TRIM, ADD,
  HEDGE}.
- **R-EPD-004** Each memo SHALL contain a "Line-item deltas" section
  listing material deltas; "material" means absolute change of at least
  5% or USD 500M, whichever is smaller.
- **R-EPD-005** Each line in the deltas section SHALL anchor an EDGAR
  URL plus the XBRL tag for the cited figure.
- **R-EPD-006** The first supported ticker SHALL be MSFT; ORCL, AMZN,
  META, GOOG land in spec 0003.
- **R-EPD-007** The CLI SHALL expose `fetch`, `diff`, `memo`
  subcommands (implementation in spec 0002).
- **R-EPD-008** Every pillar ID referenced in a memo SHALL exist as an
  active pillar in the linked `thesis-pillar-tracker` repo at the time
  of commit.

## Non-functional requirements

- **R-EPD-009** All memo prose SHALL pass `scripts/voice_lint.py`.
- **R-EPD-010** The full pipeline (fetch + diff + memo) SHALL complete
  in under five minutes on a cached filing.
- **R-EPD-011** Memo files SHALL be write-once: once committed, the file
  is not modified; outcomes are captured as separate `outcome/` entries.
- **R-EPD-012** The 24-hour SLA SHALL be measured from the filing
  timestamp on EDGAR, not from market open.
