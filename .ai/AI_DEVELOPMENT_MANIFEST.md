# AI Development Manifest

Version: 1.0

---

## Objective

This repository is designed to be developed collaboratively by humans and AI assistants.

Every AI agent contributing to this repository must follow these rules.

---

# First Rule

Never start writing code immediately.

Always understand the project first.

Read the following documents in order:

1. PROJECT_CHARTER.md
2. AGENTS.md
3. ARCHITECTURE.md
4. ROADMAP.md
5. .ai/context/current_state.md

Only after reading them should implementation begin.

---

# Scope

Implement exactly what has been requested.

Do not introduce additional features.

Do not refactor unrelated code.

Do not rename concepts.

Do not redesign the architecture.

---

# Architecture

Architecture is considered stable.

Structural changes require an Architecture Decision Record (ADR).

Never introduce architectural changes inside a feature PR.

---

# Pull Requests

Every Pull Request must have:

- One objective
- Small scope
- Passing tests
- Updated documentation if required

---

# Code Quality

Prefer readability over cleverness.

Avoid unnecessary abstractions.

Avoid premature optimization.

Write deterministic code.

Keep functions small.

---

# Testing

Every important business rule requires tests.

Every bug fix requires a regression test.

---

# Documentation

Documentation is part of the implementation.

When behavior changes, documentation must be updated.

---

# Communication

If implementation requires assumptions:

- Explain them.
- Keep them explicit.
- Never hide them inside the code.

---

# Philosophy

The objective is not producing code.

The objective is producing software that can evolve safely for years.