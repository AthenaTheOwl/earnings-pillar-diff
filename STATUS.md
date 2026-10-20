# Status

v0.1 is a data-report repo.

## Current state

- Product brief, system map, and spec 0002 design ledger shipped.
- Python CLI exposed as `epd` (entry: `python -m earnings_pillar_diff validate`).
- Memo schema, voice, and pillar-reference validation scripts.
- 24 tests pass on a fresh `uv sync` (CLI, extraction, validation scripts); CI runs them in `.github/workflows/ci.yml`.
- `epd extract` reads USD facts from a cached inline XBRL filing with their contexts; a purchase-obligation tag on a lease axis is reported as a lease commitment, and lease-axis members are summed per period.
- One real MSFT memo under `earnings_diff/MSFT-2025Q4.md`, write-once. A dated correction (2026-10-20) is in `corrections/MSFT-2025Q4.md`: its watched figure is leases not yet commenced, and like for like it moved 117,000M to 92,700M (-20.8%), not -14.5%.
- One real MSFT JSONL report artifact at `reports/MSFT-2025Q4.jsonl` with EDGAR-tag deltas; its lease row carries the correction and the first-reported values.

## Known limits

- The committed sample report is hand-entered; its lease row is checked against `epd extract` on verbatim filing excerpts, and the capex row matches them.
- Only one issuer (MSFT) wired; no GOOG / AMZN / META / ORCL tag maps yet.
- `extract` leaves out facts on axes other than the lease axis.
- No outcome entries yet. The 90-day review window for the MSFT 2025Q4 memo (filed 2025-07-30) closed on 2025-10-28, and the outcome entry is still to be written by the owner. The next-quarter filing is the Q1 FY2026 10-Q (accession 0001193125-25-256321, filed 2025-10-29); per the correction, its threshold figure is the sum of lease classes, which that filing tags `msft:FinanceLeaseMember`.

## Next feature queue

1. Replace the hand-entered sample values with parser-produced deltas from the actual filing XBRL.
2. Add issuer tag maps for GOOG, AMZN, META, and ORCL.
3. Write the MSFT 2025Q4 outcome entry (window closed 2025-10-28; owner to write).
4. Run the `validate` command (pillar references) in CI on every PR; CI runs the tests, memo schema, voice and data-conformance gates today.
