.PHONY: format format-check lint typecheck test check pre-check fix install-hooks

RUFF := $(shell command -v ruff 2>/dev/null)
PYRIGHT := $(shell command -v pyright 2>/dev/null)
BLACK := $(shell command -v black 2>/dev/null)
PYTEST := .venv/bin/pytest

pre-check:
	@scripts/strict-checking.sh

format:
ifndef BLACK
	$(error "black not found in PATH")
endif
	$(BLACK) src tests

format-check:
ifndef BLACK
	$(error "black not found in PATH")
endif
	$(BLACK) --check src tests

lint: pre-check
ifndef RUFF
	$(error "ruff not found in PATH")
endif
	$(RUFF) check src tests

typecheck: pre-check
ifndef PYRIGHT
	$(error "pyright not found in PATH")
endif
	$(PYRIGHT) --pythonpath .venv/bin/python src tests

fix:
ifndef RUFF
	$(error "ruff not found in PATH")
endif
	$(RUFF) check --fix src tests

test:
	$(PYTEST) --cov=pipeline_runner --cov-report=term-missing --cov-fail-under=100 2>/dev/null || $(PYTEST)

check: format-check lint typecheck test

install-hooks:
	scripts/install-hooks.sh
