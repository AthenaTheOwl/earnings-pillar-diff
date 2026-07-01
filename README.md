# earnings-pillar-diff

MSFT spent 44,477M on property and equipment one year and 64,551M the next — a 45%
jump — while its purchase obligations fell 14.5%. Two numbers in a 10-Q, four
quarters apart, that decide whether a thesis pillar holds. This repo finds them and
writes down what to do about it.

## What it does

Five hyperscaler prints a quarter — MSFT, GOOG, AMZN, META, ORCL — and each one
buries the interesting line items in a structured 10-Q: capex, purchase obligations,
lease commitments, off-balance-sheet financing. The disclosure is public the moment
it files. The work is diffing it against last quarter before the move is priced in,
and saying which conviction it confirms or breaks.

earnings-pillar-diff runs a fixed pipeline within 24 hours of a print. Pull the new
10-Q from EDGAR, diff the structured line items against the prior quarter, map each
material delta onto a named pillar in [thesis-pillar-tracker](https://github.com/AthenaTheOwl/thesis-pillar-tracker),
and emit `earnings_diff/<ticker>-<quarter>.md` with the deltas, the pillar tags, an
action, and a revert threshold that says exactly what number flips it.

The memo is read once, acted on, and never edited. The recommendation is committed;
the outcome gets captured 90 days later as its own entry. A call you can't grade
later isn't a call.

## Try it

One command, no setup. It reads the committed report and ranks the deltas:

```bash
uv run epd show
# earnings-pillar-diff - MSFT 2025Q4 10-Q line-item deltas
# 2 delta(s) vs prior quarter, ranked by absolute change. action: HOLD ...
```

```
earnings-pillar-diff - MSFT 2025Q4 10-Q line-item deltas
2 delta(s) vs prior quarter, ranked by absolute change. action: HOLD  |  pillars: chip-cowos-2027

line item                                               prior        current          delta      pct
----------------------------------------------------------------------------------------------------
PaymentsToAcquirePropertyPlantAndEquipment        USD 44,477M    USD 64,551M   +USD 20,074M   +45.1%
UnrecordedUnconditionalPurchaseObligationBalan   USD 108,400M    USD 92,700M   -USD 15,700M   -14.5%

biggest move: PaymentsToAcquirePropertyPlantAndEquipment USD 44,477M -> USD 64,551M (+USD 20,074M, +45.1%). action on MSFT 2025Q4: HOLD.
revert threshold: If next-quarter purchase obligations fall below USD 85,000M, change action to TRIM.
```

Ranked by absolute change, biggest move first. The threshold line is the whole
point: capex climbing while obligations stay above 85,000M confirms the chip pillar,
and the moment obligations drop under it the action becomes TRIM.

## Live demo

A root `streamlit_app.py` renders the same result as a page — the ranked delta
table, the pillar effects, the action and its revert threshold. It reads the
committed `reports/*.jsonl` directly. No network, no secrets.

```bash
uv run --with streamlit streamlit run streamlit_app.py
```

Deploy on Streamlit Community Cloud -> New app -> repo
`AthenaTheOwl/earnings-pillar-diff`, branch `main`, main file `streamlit_app.py`.

<!-- live-url: https://share.streamlit.io/... (fill in after first deploy) -->

## How it connects

The event-driven companion to [thesis-pillar-tracker](https://github.com/AthenaTheOwl/thesis-pillar-tracker).
That repo holds the standing pillars; this one watches the five prints that can move
them and writes the status-change memo when one does. Every delta here points back
at a pillar by name, so a confirmed thesis and the filing line that confirmed it sit
one link apart.

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

## Status

v0.1 data-report repo: schema validation, voice linting, pillar-reference checks, a
Python CLI, tests, product docs, and one checked-in MSFT report. The sample under
`earnings_diff/MSFT-2025Q4.md` and `reports/MSFT-2025Q4.jsonl` is hand-entered — it
exercises the schema, voice, and pillar gates before parser-produced deltas land.

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
