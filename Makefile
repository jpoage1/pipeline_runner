.PHONY: format format-check lint typecheck test check install-hooks

format:
	black src tests

format-check:
	black --check src tests

lint:
	./scripts/strict-checking.sh
	ruff check src tests

typecheck:
	./scripts/strict-checking.sh
	pyright src tests

test:
	pytest --cov=pipeline_runner --cov-report=term-missing --cov-fail-under=100

check: format-check lint typecheck test

install-hooks:
	scripts/install-hooks.sh
