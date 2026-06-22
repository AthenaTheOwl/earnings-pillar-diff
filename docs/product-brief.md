# Product Brief

## Problem

Hyperscaler filings move the AI-infra thesis through balance-sheet facts.
The decision owner needs one report per print, with the filing delta,
the affected thesis pillar, the action, and the numeric tripwire for
changing that action later.

## Reader

The primary reader is the thesis owner who already knows the pillar set.
They need a short memo that can be committed once and audited later.

## v0.1 Scope

- Validate checked-in memo frontmatter.
- Require an EDGAR URL and XBRL tag for each line-item delta.
- Check memo pillar IDs against the linked `thesis-pillar-tracker` repo.
- Provide a Python CLI for filing cache, JSON delta computation, memo
  rendering, and local validation.
- Commit one sample MSFT memo artifact and one JSONL report artifact.

## Out Of Scope

- Intraday market calls.
- Price targets.
- Filers outside MSFT, GOOG, AMZN, META, and ORCL.
- Automated pillar mapping.
