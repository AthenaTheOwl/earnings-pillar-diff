# Status

v0.1 is a data-report repo.

## Current state

- Product brief, system map, and spec 0002 design ledger shipped.
- Python CLI exposed as `epd` (entry: `python -m earnings_pillar_diff validate`).
- Memo schema, voice, and pillar-reference validation scripts.
- 4 tests pass on a fresh `uv sync` (CLI + validation scripts).
- One real MSFT memo under `earnings_diff/MSFT-2025Q4.md`.
- One real MSFT JSONL report artifact at `reports/MSFT-2025Q4.jsonl` with actual EDGAR-tag deltas.

## Known limits

- Hand-entered sample values rather than parser-produced deltas from raw 10-Q XBRL.
- Only one issuer (MSFT) wired; no GOOG / AMZN / META / ORCL tag maps yet.
- No outcome entries yet — the 90-day review window for the MSFT memo hasn't elapsed.
- No CI workflow; gates run locally only.

## Next feature queue

1. Replace the hand-entered sample values with parser-produced deltas from the actual 10-Q XBRL.
2. Add issuer tag maps for GOOG, AMZN, META, and ORCL.
3. Add outcome entries after the 90-day review window.
4. Wire a GitHub Action that runs the validate command on every PR.
