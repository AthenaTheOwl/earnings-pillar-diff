.PHONY: validate test

PYTHON ?= python
PILLAR_REPO ?= ../thesis-pillar-tracker

validate:
	$(PYTHON) scripts/voice_lint.py earnings_diff/
	$(PYTHON) scripts/validate_memo_schema.py
	$(PYTHON) scripts/check_pillar_references.py --pillar-repo $(PILLAR_REPO)

test:
	$(PYTHON) -m pytest
