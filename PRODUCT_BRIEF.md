# Product Brief

## Problem

Hyperscaler filings change the AI-infra thesis through filed balance-sheet
facts. The decision owner needs one report per print with the filing delta,
the affected pillar, the action, and the numeric tripwire for changing that
action later.

## Reader

The reader is the thesis owner who already knows the pillar set. They need a
short memo that can be committed once and audited later.

## v0.1 Scope

- Validate checked-in memo frontmatter.
- Require an EDGAR URL and XBRL tag for each line-item delta.
- Check memo pillar IDs against the linked `thesis-pillar-tracker` repo.
- Provide a Python CLI for filing cache, JSON delta computation, memo
  rendering, and local validation.
- Commit one MSFT report artifact and one matching JSONL report record.

## Out Of Scope

- Intraday market calls.
- Price targets.
- Filers outside MSFT, GOOG, AMZN, META, and ORCL.
- Automated pillar mapping.
