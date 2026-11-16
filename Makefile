.PHONY: install run test coverage lint
install:
	python -m pip install -r requirements.txt
run:
	python -m uvicorn src.main:app --reload
test:
	python -m pytest -v
coverage:
	python -m pytest --cov=src --cov-branch --cov-report=term-missing --cov-report=json:coverage.json
	python scripts/check_coverage.py
lint:
	python -m ruff check src tests scripts
