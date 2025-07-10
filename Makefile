.PHONY: test lint

unittests: ; pytest tests/unit -q --cov

lint: ; ruff check . && mypy src tests