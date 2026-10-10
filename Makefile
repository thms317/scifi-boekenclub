.PHONY: setup lint test dashboard clean
.DEFAULT_GOAL := setup

setup:
	@echo "Setting up the project..."
	@uv sync
	@echo "Setting up pre-commit hooks (with prek)..."
	@uv run prek install --hook-type pre-commit --hook-type commit-msg --hook-type pre-push
	@echo "Setup completed successfully!"

lint:
	@echo "Running ruff format check..."
	@uv run ruff format --check .
	@echo "Running ruff..."
	@uv run ruff check --output-format=concise .
	@echo "Running ty..."
	@uv run ty check .
	@echo "Running pydoclint..."
	@uv run pydoclint .
	@echo "Linting completed!"

test:
	@echo "Running tests..."
	@uv run pytest -v tests --cov=src --cov-report=term

dashboard:
	@echo "Building dashboard locally..."
	@uv run streamlit run app.py

clean:
	@echo "Cleaning up project artifacts..."
	@rm -rf .pytest_cache .ruff_cache dist src/*.egg-info .coverage
	@find . -path ./.venv -prune -o \( -name __pycache__ -o -name .ipynb_checkpoints \) -type d -exec rm -rf {} +
	@echo "Cleanup completed."
