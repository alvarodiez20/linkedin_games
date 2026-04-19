.PHONY: install install-dev install-docs lint format typecheck test test-cov docs-serve docs-build sudoku tango patches

install:
	uv sync

install-dev:
	uv sync --extra dev

install-docs:
	uv sync --extra docs

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy linkedin_games/

test:
	uv run pytest

test-cov:
	uv run pytest --cov=linkedin_games --cov-report=term-missing

docs-serve:
	uv run mkdocs serve

docs-build:
	uv run mkdocs build

sudoku:
	uv run python -m linkedin_games.sudoku

tango:
	uv run python -m linkedin_games.tango

patches:
	uv run python -m linkedin_games.patches
