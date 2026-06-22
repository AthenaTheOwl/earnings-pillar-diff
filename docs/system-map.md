# System Map

## Artifact Flow

```text
EDGAR filing URL
  -> data/filings/<TICKER>-<QUARTER>.htm
  -> JSON line-item inputs
  -> data/deltas/<TICKER>-<QUARTER>.json
  -> earnings_diff/<TICKER>-<QUARTER>.md
  -> reports/<TICKER>-<QUARTER>.jsonl
```

## Components

- `epd fetch` caches an EDGAR filing document and writes a metadata file.
- `epd diff` compares prior and current JSON line-item inputs.
- `epd memo` renders a write-once Markdown report from material deltas.
- `earnings_pillar_diff.model` holds typed line-item and delta records.
- `earnings_pillar_diff.scoring` holds materiality and action rules.
- `scripts/validate_memo_schema.py` checks memo frontmatter and delta rows.
- `scripts/voice_lint.py` blocks banned memo phrasing.
- `scripts/check_pillar_references.py` checks pillar IDs against the linked
  pillar repo.

## Data Contracts

- Line-item JSON values are expressed in USD millions unless the `unit`
  field says otherwise.
- Materiality follows the repo rule: absolute change of at least 5% or
  USD 500M, whichever is smaller.
- Memo action is exactly one of `HOLD`, `TRIM`, `ADD`, or `HEDGE`.
