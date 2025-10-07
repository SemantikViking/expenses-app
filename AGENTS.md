# Repository Guidelines

## Project Structure & Module Organization
The Python package lives in `src/receipt_processor`, organized by capability: AI integrations in `ai_providers/`, workflow coordinators such as `payment_workflow.py`, and CLI entry points in `cli.py` and `email_cli.py`. Configuration helpers sit in `config_loader.py`, templates in `templates/`, and long-running orchestration in `daemon.py`. Tests mirror the package inside `tests/`, with `test_unit_*.py` and `test_integration_*.py` suites plus end-to-end coverage in `test_e2e_processing.py`. Automation helpers live in `scripts/`, with task docs in `tasks/`.

## Build, Test, and Development Commands
Run `make setup` for a full dev install plus hooks. Use `make test` for the complete pytest suite, or `make test-unit`, `make test-integration`, and `make test-e2e` when iterating on a layer. `make lint` executes flake8, black, isort, and mypy checks; `make format` applies black and isort. `make security` runs bandit and safety. When packaging, `make build` produces distribution artifacts, and `make docker-build` creates the container image.

## Coding Style & Naming Conventions
Python 3.8+ code uses four-space indentation and type hints; mypy settings disallow untyped defs, so annotate new functions. Black enforces an 88-character line length, and imports should be grouped using isort's black profile. Favor descriptive module names such as `payment_storage.py`, and note that pytest discovers functions named `test_*`. CLI commands should expose verbs (`process`, `monitor`) to match the existing pattern.

## Testing Guidelines
Pytest is configured via `pytest.ini` with strict markers and a minimum 80% coverage threshold. Add unit tests under `tests/`, using `Test*` classes or module-level functions. Mark slow or external-service tests with the provided markers (`@pytest.mark.ai_service`, etc.) so they can be filtered. After larger changes, run `make test-coverage` to refresh HTML reports in `htmlcov/` and ensure `test-results.xml` stays green.

## Commit & Pull Request Guidelines
Commits in `git log` favor imperative summaries ('Complete Phase 8...') and occasionally conventional prefixes (`feat:`). Follow that tone, optionally prefixing with a type when it clarifies scope, and keep messages scoped to one change. Before opening a PR, run `make lint`, `make type-check`, `make test`, and `make security`; include results plus any screenshots or logs in the template's Testing section. Reference linked issues, describe functional impacts, and call out breaking changes explicitly.

## Configuration & Secrets
Duplicate `env.example` into `.env` for local credentials and keep secrets out of source control. Reusable JSON logs land in `logs/` and `receipt_processing_log.json`; avoid committing personal data. Use `config/` for shared YAML or JSON configurations and `docs/` when user-visible behavior changes.
