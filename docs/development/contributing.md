# Contributing

See `CONTRIBUTING.md` at the repo root for the full guide.

## Quick reference

```bash
# Setup
uv sync --extra dev && uv run pre-commit install

# Before committing
make lint && make typecheck && make test
```

Commit style: `feat:`, `fix:`, `docs:`, `test:`, `chore:`.

All CI checks (lint, typecheck, tests on Python 3.10–3.12, docs build) must pass before merge.
