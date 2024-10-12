.PHONY: install setup clean test tree docs

install:
	@echo "Verifying if Homebrew is installed..."
	@which brew > /dev/null || (echo "Homebrew is not installed. Installing Homebrew..." && /bin/bash -c "$$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)")

	@for tool in git uv; do \
		if ! command -v $$tool >/dev/null 2>&1; then \
			echo "Installing $$tool..."; \
			brew install $$tool; \
		else \
			echo "$$tool is already installed. Skipping."; \
		fi; \
	done

	@echo "Setting up Python version $$PYTHON_VERSION"; \
	uv python install;

	@echo "All tools installed successfully."

setup:
	@echo "Setting up the project..."
	uv sync;

	@if [ ! -d ".git" ]; then \
		echo "Setting up git..."; \
		git init -b main > /dev/null; \
	fi

	@echo "Setting up pre-commit..."
	. .venv/bin/activate;
	.venv/bin/pre-commit install --hook-type pre-commit --hook-type commit-msg;

clean:
	@echo "Cleaning up..."
	rm -rf .venv uv.lock
	find . -type d \
		\( -name ".pytest_cache" \
		-o -name ".mypy_cache" \
		-o -name ".ruff_cache" \
		-o -name "dist" \) \
		-exec rm -rf {} +
	@echo "Cleanup completed. Resetting terminal..."
	@reset

test:
	@echo "Running tests..."
	.venv/bin/pre-commit run --all-files
	uv sync;
	uv run pytest tests --cov=src --cov-report term;

tree:
	@echo "Generating project tree..."
	@tree -I '.venv|__pycache__|archive|scratch|.databricks|.ruff_cache|.mypy_cache|.pytest_cache|.git|htmlcov|site|dist|.DS_Store|fixtures' -a

docs:
	@echo "Running tests and generating badges..."
	@uv run pytest -v tests --cov=src --cov-report html:docs/tests/coverage --junitxml=docs/tests/coverage/pytest_coverage.xml
	@uv run coverage xml -o docs/tests/coverage/coverage.xml
	@uv run genbadge coverage -i docs/tests/coverage/coverage.xml -o docs/assets/badge-coverage.svg
	@uv run genbadge tests -i docs/tests/coverage/pytest_coverage.xml -o docs/assets/badge-tests.svg
	@rm -rf docs/tests/coverage/.gitignore
	@echo "Generating HTML documentation..."
	@uv run pdoc --html src/scifi -o docs/api --force
	@uv run pdoc --html tests -o docs/api --force
	# @uv run mkdocs build
	@uv run mkdocs serve
