# earnings-pillar-diff

MSFT spent 44,477M on property and equipment in fiscal 2024 and 64,551M in fiscal
2025, a 45% jump, while its leases not yet commenced, primarily for datacenters,
fell 20.8%, from 117,000M to 92,700M. Two numbers in a 10-K, each against the prior
fiscal year, that decide whether a thesis pillar holds. This repo finds them and
writes down what to do about it.

The first memo called the second number purchase obligations and put it at
-14.5%. Both were wrong: the tag says purchase obligation, but the fact sits on a
lease axis, and -14.5% compared one lease class with all of them. The memo stays
as written; the correction is in [corrections/MSFT-2025Q4.md](corrections/MSFT-2025Q4.md).

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
# earnings-pillar-diff - MSFT 2025Q4 10-K line-item deltas
# 2 delta(s) vs prior fiscal year, ranked by absolute change. action: HOLD ...
```

```
earnings-pillar-diff - MSFT 2025Q4 10-K line-item deltas
2 delta(s) vs prior fiscal year, ranked by absolute change. action: HOLD  |  pillars: chip-cowos-2027

line item                                               prior        current          delta      pct
----------------------------------------------------------------------------------------------------
lease commitments not yet commenced              USD 117,000M    USD 92,700M   -USD 24,300M   -20.8%
PaymentsToAcquirePropertyPlantAndEquipment        USD 44,477M    USD 64,551M   +USD 20,074M   +45.1%

lease commitments not yet commenced: us-gaap:UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount on us-gaap:LeaseContractualTermAxis, reported as a lease commitment, not a purchase obligation. members summed: prior msft:OperatingLeaseMember + msft:FinanceLeaseMember; current msft:OperatingLeaseMember.
corrected 2026-10-20: first reported as USD 108,400M -> USD 92,700M (-USD 15,700M, -14.5%), FY2024 finance leases only (msft:FinanceLeaseMember) against FY2025 all leases.

biggest move: lease commitments not yet commenced USD 117,000M -> USD 92,700M (-USD 24,300M, -20.8%). action on MSFT 2025Q4: HOLD.
revert threshold: If next-quarter purchase obligations fall below USD 85,000M, change action to TRIM.
correction: 2026-10-20, corrections/MSFT-2025Q4.md: the figure the revert threshold calls purchase obligations is Microsoft's leases not yet commenced; the call and threshold stand as recorded.
```

Ranked by absolute change, biggest move first. The threshold line is the whole
point: capex climbing while leases not yet commenced stay above 85,000M confirms
the chip pillar, and the moment they drop under it the action becomes TRIM. The
threshold keeps the words it was recorded with ("purchase obligations"); the
correction line says which figure they name.

## Reading a tag in its context

A tag name does not say what a number is. Microsoft files its leases not yet
commenced under `us-gaap:UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount`,
on `us-gaap:LeaseContractualTermAxis` with its own members
(`msft:OperatingLeaseMember`, `msft:FinanceLeaseMember`). So:

- `epd extract` keeps each fact's context: period and dimension members.
- A purchase-obligation tag on a lease axis is labelled a lease commitment in
  `diff`, `memo` and `show`, whatever the tag is called.
- Lease-axis members of one tag are summed per period before the delta. The
  FY2024 10-K splits the figure by lease class (8.6B operating, 108.4B finance);
  the FY2025 10-K reports one combined 92.7B under the operating member, and the
  Q1 FY2026 10-Q moves the combined figure to the finance member. Only the sum
  compares like with like.
- A tag listed twice in one period, or one member listed twice, is an input
  error instead of last-one-wins.

The tests pin this to verbatim excerpts of the four filings in
`tests/fixtures/filings/`.

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

The CLI also exposes filing cache, fact extraction, JSON diff, and memo-render
commands:

```bash
uv run epd fetch --ticker MSFT --quarter 2025Q4 --filing-url <edgar-url>
uv run epd extract --filing data/filings/MSFT-2024Q4.htm --period-end 2024-06-30 --output prior.json
uv run epd extract --filing data/filings/MSFT-2025Q4.htm --period-end 2025-06-30 --output current.json
uv run epd diff --ticker MSFT --quarter 2025Q4 --prior-file prior.json --current-file current.json
uv run epd memo --ticker MSFT --quarter 2025Q4 --delta-file data/deltas/MSFT-2025Q4.json --pillars chip-cowos-2027 --action HOLD --revert-threshold "If next-quarter leases not yet commenced fall below USD 85,000M, change action to TRIM." --filing-url <edgar-url> --filing-date 2025-07-30 --output earnings_diff/MSFT-2025Q4.md
```

`extract` keeps duration facts of `--duration-months` (12 for a 10-K year, 3 for
a quarter) and instant facts at `--period-end`. Facts on axes other than the
lease axis are left out.

## Status

v0.1 data-report repo: schema validation, voice linting, pillar-reference checks, a
Python CLI, tests, product docs, and one checked-in MSFT report. The sample under
`earnings_diff/MSFT-2025Q4.md` and `reports/MSFT-2025Q4.jsonl` is hand-entered — it
exercises the schema, voice, and pillar gates. Its lease row was corrected on
2026-10-20 and is now checked against `epd extract` output on the filing excerpts.
Its 90-day outcome is graded in `outcome/MSFT-2025Q4.md`: the HOLD held.

## Layout

```
earnings-pillar-diff/
  earnings_diff/                # YYYY-QN memos, write-once
  corrections/                  # dated corrections to a memo, appended, never edited in place
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
    fixtures/filings/           # verbatim excerpts of the MSFT filings the tests read
  PRODUCT_BRIEF.md
  SYSTEM_MAP.md
  STATUS.md
  docs/comparable-filing-contexts.md
  docs/first-pr.md
  docs/product-brief.md
  docs/system-map.md
  AGENTS.md
  LICENSE
  README.md
```

## Method update

[October method update: A filing delta needs a comparable period and context](docs/comparable-filing-contexts.md).

## License

MIT. See LICENSE.
