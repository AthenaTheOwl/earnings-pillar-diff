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

v0 scaffold; no implementation yet. Spec 0002 will implement the MSFT
parser. Spec 0003 will generalize to the other four filers.

## How to run

Will land in spec 0002. The expected shape:

```bash
uv sync
uv run epd fetch --ticker MSFT --quarter 2026Q4
uv run epd diff --ticker MSFT --quarter 2026Q4
uv run epd memo --ticker MSFT --quarter 2026Q4 --pillar-repo ../thesis-pillar-tracker
```

For v0 the only working command is `uv run epd --help`.

## Layout

```
earnings-pillar-diff/
  earnings_diff/                # YYYY-QN memos, write-once
  data/
    filings/                    # cached 10-Q XBRL (.gitignored)
    deltas/                     # parsed per-quarter line items
  src/epd/                      # CLI + parser (lands in spec 0002)
  specs/0001-foundation/
  docs/first-pr.md
  AGENTS.md
  LICENSE
  README.md
```

## License

MIT. See LICENSE.
