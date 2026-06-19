# Design — 0001 Foundation

## Architecture sketch

Three-stage pipeline. Each stage is a separate CLI subcommand and can be
re-run independently. Intermediate artifacts are cached on disk.

```
EDGAR --fetch--> data/filings/MSFT-2026Q4.xbrl
              \
               +-diff-> data/deltas/MSFT-2026Q4.json
                       \
                        +-memo-> earnings_diff/MSFT-2026Q4.md
```

## Stages

### fetch

Pulls the 10-Q XBRL document for a given ticker and quarter from EDGAR's
JSON API. Caches under `data/filings/<TICKER>-<QUARTER>.xbrl`. Records
the filing URL and filing timestamp in `data/filings/<TICKER>-<QUARTER>.meta.json`.

### diff

Reads the current quarter's XBRL plus the prior quarter's cached XBRL.
Computes per-tag deltas for a fixed list of tags:

- `us-gaap:PurchaseObligation`
- `us-gaap:PaymentsToAcquirePropertyPlantAndEquipment`
- `us-gaap:LesseeOperatingLeaseLiabilityPaymentsDue`
- `msft:OffBalanceSheetCommitments` (issuer-specific)

Writes `data/deltas/<TICKER>-<QUARTER>.json` with the absolute and
relative delta for each tag plus the EDGAR anchor.

### memo

Reads the delta JSON. Filters to material deltas per R-EPD-004. Asks
the human reviewer (interactively in v0; potentially an LLM with
human-gate later) to map each material delta to affected pillar IDs.
Renders the memo Markdown.

## Pillar reference validation

`scripts/check_pillar_references.py --pillar-repo ../thesis-pillar-tracker`
parses every memo, extracts pillar IDs from frontmatter, and confirms
each is present as an `active` pillar in the linked repo. The path is a
configurable CLI flag, not a hardcoded sibling assumption.

## Memo template

```markdown
---
ticker: MSFT
quarter: 2026Q4
filing_url: https://www.sec.gov/cgi-bin/browse-edgar?...
filing_date: 2026-07-29T20:05:00Z
pillars_affected: [chip-cowos-2027, ai-capex-elasticity]
action: TRIM
revert_threshold: "If next-quarter purchase obligations grow >15% QoQ, revert to HOLD"
---

## Line-item deltas
| Tag | Prior | Current | Delta | Anchor |
|---|---|---|---|---|
| PurchaseObligation | 178B | 192B | +14B (+7.9%) | [10-Q p.34](url) |

## Pillar effects
- **chip-cowos-2027** CONFIRMS — purchase obligations grew above prior trend
- **ai-capex-elasticity** WEAKENS — capex grew faster than guided

## Action
TRIM positions exposed to the WEAKENS pillar by 50bps.

## Revert threshold
If next-quarter purchase obligations grow >15% QoQ, revert to HOLD.
```
