# Spec 0002 Design Ledger

Status: implemented in v0.1.

## Decisions

- Package name is `earnings-pillar-diff`; import package is `earnings_pillar_diff`.
- `uv` installs the project package by default through `[tool.uv] package = true`.
- Dev dependencies live under `[dependency-groups]`.
- The CLI has four subcommands: `fetch`, `diff`, `memo`, and `validate`.
- Validators are plain Python scripts so the repo can run gates without a
  service or database.
- The first memo artifact is `earnings_diff/MSFT-2025Q4.md`.
- The first JSONL report artifact is `reports/MSFT-2025Q4.jsonl`.

## Interfaces

```bash
epd fetch --ticker MSFT --quarter 2025Q4 --filing-url URL
epd diff --ticker MSFT --quarter 2025Q4 --prior-file prior.json --current-file current.json
epd memo --ticker MSFT --quarter 2025Q4 --delta-file data/deltas/MSFT-2025Q4.json --pillars chip-cowos-2027 --action HOLD --revert-threshold "If next-quarter purchase obligations fall below USD 85,000M, change action to TRIM." --filing-url URL --filing-date 2025-07-30 --output earnings_diff/MSFT-2025Q4.md
epd validate --pillar-repo ../thesis-pillar-tracker
```

## Open Items

- Replace hand-entered sample values with parser-produced MSFT deltas.
- Add issuer-specific tag maps for GOOG, AMZN, META, and ORCL.
- Move pillar mapping from command flags to a human-reviewed prompt.
