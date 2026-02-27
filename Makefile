.PHONY: install test run api lint clean

install:
	pip install -r requirements.txt

test:
	python -m pytest wisdom/tests/ -v

run:
	streamlit run wisdom/body/app.py

api:
	uvicorn wisdom.body.api:app --reload --port 8000

lint:
	ruff check wisdom/
	ruff format --check wisdom/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ htmlcov/ .coverage
