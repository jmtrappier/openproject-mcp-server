# Repository Guidelines

## Project Structure & Module Organization
- `src/` — core Python package: `mcp_server.py`, `openproject_client.py`, `config.py`, plus `handlers/` and `utils/`.
- `scripts/` — ops and entrypoints: `run_server.py`, `deploy.sh`, test helpers.
- `tests/` — pytest suite (`test_*.py`, `conftest.py`, `run_tests.py`).
- Deployment: `Dockerfile`, `docker-compose*.yml`.
- Configuration: `.env` (local), `env.example` (template). Data/logs persist in `data/`, `logs/`.

## Build, Test, and Development Commands
- Environment setup:
  - `python3 -m venv venv && source venv/bin/activate`
  - `pip install -r requirements.txt` (runtime) or `pip install -r requirements-test.txt` (dev/test).
- Run locally: `python3 scripts/run_server.py`.
- Tests:
  - Quick: `python3 tests/run_tests.py`
  - Full: `pytest -v --tb=short --cov=src tests/`.
- Lint/format/type-check: `black src tests && isort src tests && flake8 src tests && mypy src`.
- Docker: `./scripts/deploy.sh deploy 39127` or `docker build -t openproject-mcp-server .`.

## Coding Style & Naming Conventions
- Python 3.8+; 4-space indentation; type hints required for public APIs.
- Use `black` (default line length), `isort` (profiles=black), `flake8` for lint.
- Naming: `snake_case` for modules/functions, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- Docstrings: triple-quoted, concise purpose + args/returns where non-trivial.
- Logging: use `utils.logging.get_logger`; avoid `print()` in library code.

## Testing Guidelines
- Framework: `pytest` + `pytest-asyncio`, coverage via `pytest-cov`.
- Location/naming: put tests in `tests/`, files named `test_*.py`; use fixtures in `tests/conftest.py`.
- Aim for meaningful coverage of new/changed code; prefer async tests where applicable.

## Commit & Pull Request Guidelines
- Commits: short imperative subject (≤72 chars), optional body for context. Reference issues (e.g., `Fixes #123`).
- Before PR: ensure `pytest` passes, code is formatted/linted, and relevant docs updated (README, scripts, env examples).
- PR description: scope, rationale, test evidence (commands/output), and any config or deployment impacts.

## Security & Configuration Tips
- Never commit secrets. Copy `env.example` to `.env` and edit locally. `.env` is read by `python-dotenv` in `src/config.py`.
- Required vars: `OPENPROJECT_URL`, `OPENPROJECT_API_KEY`; validate via `python3 scripts/test_mvp.py`.
- When using Docker, map `logs/` and `data/`; avoid printing sensitive tokens in logs.

## Agent-Specific Notes
- Keep changes minimal and aligned with existing patterns. Update tests alongside behavior changes.
- If adding new tools/resources/endpoints, document commands in README and include examples.
