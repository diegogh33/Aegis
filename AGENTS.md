# AGENTS.md

This document defines the development rules for every AI agent contributing to Aegis.

## Objective

Every contribution must improve the project without degrading its architecture.

Correctness is more important than speed.

Readability is more important than cleverness.

## Golden Rules

1. Never hardcode investment parameters.
2. Business rules must remain pure.
3. Configuration belongs in YAML.
4. Domain models must never know HTTP.
5. Domain models must never know Alpha Vantage.
6. Every new rule must include tests.
7. Every Pull Request must leave the project in a working state.
8. Never refactor unrelated code inside a feature PR.
9. Preserve backwards compatibility unless explicitly approved.
10. Keep functions small and focused.

## Architecture

The architecture is frozen during Sprint 0.

No structural changes are allowed until Sprint 1 begins.

## Code Style

- Python 3.13
- Type hints everywhere
- Docstrings for public classes
- No commented code
- No dead code
- Prefer composition over inheritance
- Prefer explicit code over magic

## Testing

Every feature must include:

- Unit tests
- Edge cases
- Failure cases

All tests must pass before a PR is considered complete.

## Pull Requests

Every PR must include:

- Objective
- Files changed
- Tests
- Validation steps
- Commit message

## Scope

Implement only the requested feature.

Do not introduce unrelated improvements.