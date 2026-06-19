# First PR after the scaffold

Narrow scope: schema, voice gate, pillar-reference checker, one
hand-written sample memo. No EDGAR fetcher yet.

## Title

`feat: memo schema, validators, sample MSFT memo`

## Files changed

- `schemas/memo.schema.json` (new) — JSON Schema for the memo
  frontmatter. Required fields per R-EPD-002. Action enum per R-EPD-003.
- `scripts/validate_memo_schema.py` (new) — walks `earnings_diff/`,
  parses frontmatter, validates against the schema, asserts every
  material delta has an anchor.
- `scripts/voice_lint.py` (new) — copied from sports-prediction-os.
- `scripts/check_pillar_references.py` (new) — argparse-driven; takes
  `--pillar-repo` path; emits a non-zero exit code if any referenced
  pillar is absent or not `active`.
- `earnings_diff/MSFT-2025Q4.md` (new) — hand-written sample memo with
  a placeholder pillar set referenced via README disclaimer.
- `Makefile` (new) — `make validate` chains the three scripts.
- `README.md` already exists in the scaffold; add a "Sample memo"
  pointer to the new file.

## Why a hand-written sample memo

The schema and voice gate need a real test fixture before the parser
exists. Hand-writing one quarter forces the schema to match how the
output actually reads. Once PR 2 ships the parser, the sample memo
becomes a regression target.

## Verification

```bash
make validate
```

Expected output: `OK: 1 memo validated.` Zero exit code.

A reviewer should read the sample memo and confirm: (a) every delta
cited has an EDGAR URL, (b) the action is in the enum, (c) the
revert-threshold reads as a measurable condition rather than a vibe.

## What this PR does NOT do

- No EDGAR fetcher; that is PR 2.
- No automated delta computation; PR 2 too.
- No memo CLI; PR 3.
- No CI workflow.
