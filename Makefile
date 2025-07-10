.PHONY: test lint


unittests: ; pytest tests/unit -q --cov

# Run all integration tests
integrationtests: ; pytest tests/integration -q

# Individual integration test targets
dir := tests/integration
integration_test_google_stt: ; pytest $(dir)/test_google_stt.py -q

# Add more integration test targets below as needed

lint: ; ruff check . && mypy src tests