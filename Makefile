.PHONY: setup clean test tree lint dashboard update-pre-commit update-venv validate-update update

.DEFAULT_GOAL := setup

setup:
	@echo "Setting up the project..."
	@uv sync;

	@if [ ! -d ".git" ]; then \
		echo "Setting up git..."; \
		git init -b main > /dev/null; \
	fi

	@echo "Setting up pre-commit hooks (with prek)..."
	@uv run prek install --hook-type pre-commit --hook-type commit-msg --hook-type pre-push
	@uv run prek autoupdate


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

# Update pre-commit hooks to latest versions
update-pre-commit:
	@echo "Updating pre-commit hooks..."
	@uv run pre-commit autoupdate

# Update virtual environment dependencies to latest versions
update-venv:
	@echo "Updating virtual environment dependencies..."
	@uv sync --upgrade

# Validate synchronization between venv and pre-commit hook versions
validate-update:
	@for tool in ruff ty pydoclint; do \
		pc_ver=$$(grep -v '^\s*#' .pre-commit-config.yaml | grep -A1 "$$tool" | grep rev | sed 's/.*v//' | tr -d ' ' | sed 's/://'); \
		uv_ver=$$(awk '/\[\[package\]\]/{p=0} /name = "'"$$tool"'"/{p=1} p && /version = /{print $$NF; exit}' uv.lock | tr -d '"'); \
		[ -n "$$pc_ver" ] && [ -n "$$uv_ver" ] && \
		[ "$$(echo $$pc_ver | cut -d. -f1-2)" != "$$(echo $$uv_ver | cut -d. -f1-2)" ] && \
		echo "❌ $$tool: $$pc_ver vs $$uv_ver"; \
	done; true

# Update both pre-commit hooks and virtual environment dependencies
update: update-pre-commit update-venv validate-update
	@echo "All dependencies updated and synced"
