# Changelog

All notable changes to this project will be documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- `linkedin_games/config.py` — centralised envvar-based configuration for CDP URL, delays, and timeouts.
- `linkedin_games/py.typed` — PEP 561 marker for IDE type-stub support.
- `tests/` — unit test suite (57 tests) covering solver algorithms for all three games.
- `.github/workflows/ci.yml` — CI pipeline: lint, typecheck, tests on Python 3.10–3.12, docs build.
- `Makefile` — convenience targets for install, lint, format, typecheck, test, docs, and run.
- `.pre-commit-config.yaml` — ruff + mypy hooks enforced at commit time.
- `CONTRIBUTING.md` — contributor guide including the pattern for adding new games.
- `docs/` — MkDocs Material site covering getting started, per-game algorithms, architecture, and API reference.
- `pyproject.toml` — `[project.optional-dependencies]` for `dev` and `docs` extras; tool configs for ruff, mypy, pytest, and coverage.

## [0.1.0] — 2026-04-19

### Added
- Initial release with solvers for Mini Sudoku, Tango, and Patches.
- Backtracking + MRV solver for 6×6 Sudoku.
- Constraint propagation + backtracking solver for Tango.
- CSP + forward-checking + MRV solver for Patches (Shikaku variant).
- Playwright-based DOM extraction and input automation for all three games.
- CLI entry points: `sudoku`, `tango`, `patches`.
