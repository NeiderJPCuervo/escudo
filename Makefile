.PHONY: install lint format typecheck test baseline ci

install:  ## Crea .venv con el workspace y las herramientas de desarrollo
	uv sync

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff check . --fix
	uv run ruff format .

typecheck:
	uv run mypy

test:
	uv run pytest --cov

baseline:  ## Tabla de línea base sobre el simulador con semilla
	uv run escudo-baseline --seed 2

ci: lint typecheck test baseline  ## Lo mismo que corre GitHub Actions
