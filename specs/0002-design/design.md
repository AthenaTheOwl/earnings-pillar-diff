# Design

## Package Layout

```text
earnings_pillar_diff/
  __init__.py
  cli.py
  model.py
  scoring.py
```

`earnings_pillar_diff.cli` owns command parsing and file IO. The `model` module
normalizes JSON line-item input into typed records. The `scoring` module owns
materiality, ticker, and action rules.

## CLI Flow

`epd fetch` writes cached filing text plus metadata. `epd diff` reads two JSON
line-item files, normalizes rows by XBRL tag, computes all deltas, and writes
material deltas to JSON. `epd memo` renders a Markdown memo from a delta JSON
file. `epd validate` runs the local validation scripts.

## Report Artifact

`reports/<TICKER>-<QUARTER>.jsonl` stores machine-readable report rows. The
first row is report metadata. Later rows are delta records with the EDGAR URL
used by the memo.

## Compatibility

The legacy `epd` module remains as a wrapper so existing tests and local imports
continue to work while the contract import path moves to `earnings_pillar_diff`.
