.PHONY: setup clean test tree lint

.DEFAULT_GOAL := setup

setup:
	@echo "Setting up the project..."
	@uv sync;

	@if [ ! -d ".git" ]; then \
		echo "Setting up git..."; \
		git init -b main > /dev/null; \
	fi

	@echo "Setting up pre-commit..."
	@uv run pre-commit install --hook-type pre-commit --hook-type commit-msg

	@echo "Setup completed successfully!"

clean:
	@echo "Uninstalling local packages..."
	@rm -rf uv.lock
	@uv sync

	@echo -e "Cleaning up project artifacts..."
	@find . \( \
		-name ".pytest_cache" -o \
		-name ".ruff_cache" -o \
		-name "dist" -o \
		-name "__pycache__" -o \
		-name ".ipynb_checkpoints" \) \
		-type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name ".coverage" -type f -delete 2>/dev/null || true

	@echo "Cleanup completed."
	@reset

test:
	@echo "Running tests..."
	@uv build
	@uv sync
	@uv run pytest -v tests --cov=src --cov-report=term

tree:
	@echo "Generating project tree..."
	@tree -I '.venv|__pycache__|archive|scratch|.databricks|.ruff_cache|.mypy_cache|.pytest_cache|.git|htmlcov|site|dist|.DS_Store|fixtures' -a

lint:
	@echo "Linting the project..."
	@uv sync
	@echo "Building the project..."
	@uv build >/dev/null 2>&1
	@echo "Running ruff..."
	-@uv run ruff check --output-format=concise .
	@echo "Running ty..."
	-@uv run ty check .
	@echo "Running pydoclint..."
	-@uv run pydoclint .
	@echo "Linting completed!"

dashboard:
	@echo "Building dashboard locally..."
	@uv run streamlit run src/scifi/dashboard.py
