.PHONY: test test-cover test-e2e lint ci

# UT: unit tests only, full mock, no external deps, < 60s
test:
	uv run pytest tests/unit/ -q

# test-cover: UT + coverage report, output to test-result/
test-cover:
	@mkdir -p test-result
	uv run pytest tests/unit/ \
		--cov=src/kweaver \
		--cov-report=term-missing \
		--cov-report=xml:test-result/coverage.xml \
		-q

# test-e2e: full e2e suite (requires live KWeaver + DB env vars in ~/.env.secrets)
test-e2e:
	uv run pytest tests/e2e/ -v --run-destructive

# lint: static type check
lint:
	uv run python -m py_compile $$(find src/kweaver -name "*.py" | tr '\n' ' ')

# ci: lint + test-cover
ci: lint test-cover
