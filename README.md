# Earnings Call Pillar Diff

Within 24 hours of MSFT / GOOG / AMZN / META / ORCL prints, diffs 10-Q
purchase-obligations and capex disclosures versus prior quarter, maps the
deltas onto thesis pillars, and ships a one-page status-change memo with
explicit action recommendations.

## What this is

An event-driven companion to `thesis-pillar-tracker`. Five hyperscaler
prints per quarter trigger a fixed pipeline:

1. Pull the new 10-Q from EDGAR.
2. Diff the structured line items (capex, purchase obligations, lease
   commitments, off-balance-sheet financing) versus the prior quarter.
3. Map each material delta onto one or more named pillars in the linked
   thesis-pillar-tracker repo.
4. Emit `earnings_diff/<ticker>-<quarter>.md` with line-item deltas,
   pillar tags, an action recommendation, and a revert / trim threshold.

The output is read once, acted on, and never edited. The recommendation
is committed; the outcome is captured 90 days later as a separate entry.

## Status

v0.1 data-report repo. It includes schema validation, voice linting,
pillar-reference checks, a Python CLI, tests, product docs, and one
checked-in MSFT report artifact.

## How to run

```bash
uv sync
uv run epd --help
uv run epd validate --pillar-repo ../thesis-pillar-tracker
uv run pytest
```

The CLI also exposes filing cache, JSON diff, and memo-render commands:

```bash
uv run epd fetch --ticker MSFT --quarter 2025Q4 --filing-url <edgar-url>
uv run epd diff --ticker MSFT --quarter 2025Q4 --prior-file prior.json --current-file current.json
uv run epd memo --ticker MSFT --quarter 2025Q4 --delta-file data/deltas/MSFT-2025Q4.json --pillars chip-cowos-2027 --action HOLD --revert-threshold "If next-quarter purchase obligations fall below USD 85,000M, change action to TRIM." --filing-url <edgar-url> --filing-date 2025-07-30 --output earnings_diff/MSFT-2025Q4.md
```

## live demo

A no-arg `show` verb prints a readable, ranked view of the committed report:

```bash
uv run epd show
# earnings-pillar-diff - MSFT 2025Q4 10-Q line-item deltas
# 2 delta(s) vs prior quarter, ranked by absolute change. action: HOLD ...
```

A root `streamlit_app.py` renders the same result as an interactive page,
reading the committed `reports/*.jsonl` directly (no network, no secrets):

```bash
uv run --with streamlit streamlit run streamlit_app.py
```

Deploy on Streamlit Community Cloud -> New app -> repo
`AthenaTheOwl/earnings-pillar-diff`, branch `main`, main file `streamlit_app.py`.

<!-- live-url: https://share.streamlit.io/... (fill in after first deploy) -->

## Sample Memo

See `earnings_diff/MSFT-2025Q4.md` and `reports/MSFT-2025Q4.jsonl`. The sample
is a hand-entered report artifact used to exercise the schema, voice, and
pillar-reference gates before parser-produced deltas land.

## Layout

```
earnings-pillar-diff/
  earnings_diff/                # YYYY-QN memos, write-once
  reports/                      # JSONL report artifacts
  earnings_pillar_diff/         # CLI, data model, and scoring
  data/
    filings/                    # cached 10-Q XBRL (.gitignored)
    deltas/                     # parsed per-quarter line items
  src/epd/                      # compatibility wrapper
  specs/0001-foundation/
  specs/0002-design/
  schemas/
  scripts/
  tests/
  PRODUCT_BRIEF.md
  SYSTEM_MAP.md
  STATUS.md
  docs/first-pr.md
  docs/product-brief.md
  docs/system-map.md
  AGENTS.md
  LICENSE
  README.md
```

## License

MIT. See LICENSE.
