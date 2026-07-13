# Aegis Project Charter

Version: 1.0

Status: Active

---

# Mission

Aegis is an investment decision engine.

Its purpose is to help evaluate investment opportunities using transparent, configurable and reproducible rules.

Aegis is **not** an automated trading bot.

It never executes trades.

It only analyzes opportunities and provides recommendations.

---

# Vision

The long-term objective is to codify a professional investment process into software.

Every recommendation produced by Aegis must be:

- Explainable
- Reproducible
- Testable
- Configurable

The engine must always be able to explain *why* a recommendation was produced.

---

# Product Principles

The following principles are immutable.

## Transparency

Every score must be explainable.

No black-box algorithms.

No hidden weights.

---

## Configuration First

Investment criteria must live in configuration files.

Business rules must never depend on hardcoded parameters.

---

## Separation of Responsibilities

Each component has one responsibility.

Providers retrieve data.

Mappers transform data.

Strategies orchestrate.

Rules evaluate.

Formatters render.

---

## Domain Independence

Business logic must never depend on:

- HTTP
- Alpha Vantage
- Interactive Brokers
- Claude
- MCP

External services are implementation details.

---

## Deterministic Behaviour

Given the same input and configuration, Aegis must always produce the same result.

---

## Testability

Every important component must be independently testable.

Every business rule requires unit tests.

---

# Development Rules

## Architecture

The architecture is frozen until Sprint 0 finishes.

No structural changes are allowed without creating a new ADR.

---

## Pull Requests

Every Pull Request must:

- Have one objective.
- Leave the project working.
- Include tests when applicable.
- Update documentation when necessary.

---

## Commits

Commits should remain focused.

Do not mix unrelated changes.

---

# Coding Standards

- Python 3.13
- Type hints everywhere
- Small functions
- Explicit code
- Prefer composition
- Avoid unnecessary inheritance

---

# Documentation

Documentation is part of the product.

Every architectural decision must be documented.

---

# Artificial Intelligence

AI assistants are first-class contributors.

Before generating code they should read:

1. PROJECT_CHARTER.md
2. AGENTS.md
3. ARCHITECTURE.md
4. ROADMAP.md

Only after understanding those documents should implementation begin.

---

# Long-Term Goal

The final version of Aegis should be capable of:

- Downloading market data.
- Evaluating businesses.
- Selecting option contracts.
- Applying configurable investment strategies.
- Producing professional investment reports.
- Integrating with LLMs through MCP.

The investment methodology must remain independent from any specific provider or language model.