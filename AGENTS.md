# AGENTS.md — earnings-pillar-diff

Operating contract for AI agents working in this repo.

## What this repo is

An event-driven memo pipeline. Five hyperscaler prints per quarter. Each
print produces one memo file. The memo includes a line-item delta, the
affected pillars, an action, and a revert threshold. The memo is written
once and committed; outcomes land later as new entries.

The repo is downstream of `thesis-pillar-tracker`. Pillar IDs in memos
SHALL match active pillars in that repo.

## Roles you may see in tasks

| Role | What they do |
|---|---|
| `filing-fetcher` | Pulls the new 10-Q from EDGAR, caches XBRL |
| `delta-parser` | Computes the line-item delta vs the prior quarter |
| `pillar-mapper` | Tags each material delta with affected pillar IDs |
| `memo-writer` | Emits the one-page memo with action and revert threshold |

Not all roles are implemented in v0.

## Voice constraints

- No marketing words. No "leverage", "synergy", "best-in-class",
  "seamless", "cutting-edge".
- No antithetical reversals as a structural device.
- Plain numeric assertions. Cite the EDGAR URL for every delta.
- Action recommendation is one of {HOLD, TRIM, ADD, HEDGE}; no hedging
  the recommendation in prose.

## Gates (will land in spec 0002)

```bash
uv run pytest
python scripts/voice_lint.py earnings_diff/
python scripts/validate_memo_schema.py
python scripts/check_pillar_references.py --pillar-repo ../thesis-pillar-tracker
```

A memo without an EDGAR anchor for every delta, or with a pillar ID not
present in the linked thesis-pillar-tracker repo, fails the gate.

## Out of scope

- Intraday reactions. The 24-hour window is the SLA, not a real-time
  feed.
- Tickers beyond the five named hyperscalers. Other filers belong in a
  separate repo if ever.
- Price targets. The memo names actions and revert thresholds, not
  targets.
