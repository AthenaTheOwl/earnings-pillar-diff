# System Map

## Artifact Flow

```text
EDGAR filing URL
  -> data/filings/<TICKER>-<QUARTER>.htm
  -> JSON line-item inputs (epd extract)
  -> data/deltas/<TICKER>-<QUARTER>.json
  -> earnings_diff/<TICKER>-<QUARTER>.md
  -> reports/<TICKER>-<QUARTER>.jsonl
```

## Components

- `epd fetch` caches an EDGAR filing document and writes filing metadata.
- `epd extract` reads USD facts and their contexts out of a cached inline XBRL
  filing (`earnings_pillar_diff.xbrl`).
- `epd diff` compares prior and current JSON line-item inputs, summing
  lease-axis members of one tag per period.
- `epd memo` renders a write-once Markdown report from material deltas.
- `earnings_pillar_diff.model` holds typed line-item and delta records.
- `earnings_pillar_diff.scoring` holds materiality and action rules.
- `scripts/validate_memo_schema.py` checks memo frontmatter and delta rows.
- `scripts/voice_lint.py` blocks banned memo phrasing.
- `scripts/check_pillar_references.py` checks pillar IDs against the linked
  pillar repo.

## Data Contracts

- Line-item JSON values are expressed in USD millions unless the `unit` field
  says otherwise.
- A delta is material when absolute change is at least 5% or USD 500M,
  whichever is smaller.
- Memo action is exactly one of `HOLD`, `TRIM`, `ADD`, or `HEDGE`.
- Each delta row must carry an EDGAR URL.
- A line item may carry `axis` and `member`. A purchase-obligation tag on
  `us-gaap:LeaseContractualTermAxis` is a lease commitment, and its members
  are summed before the delta. A tag listed twice without an axis is an error.
- Corrections to a write-once memo are appended, dated, under `corrections/`.
