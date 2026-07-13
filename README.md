# Aegis

> Intelligent investment analysis engine focused on systematic decision-making for Cash Secured PUT strategies.

## Vision

Aegis is not a trading bot.

It is a decision-support system designed to evaluate investment opportunities using a transparent, configurable and reproducible methodology.

The goal is to codify a long-term investment process into software.

## Current Status

🚧 Early development (Sprint 0)

The current objective is to build a robust architecture before implementing business functionality.

## Main Features (Planned)

- Market data providers
- Option chain analysis
- Automatic contract selection
- Rule engine
- Strategy engine
- Rich terminal reports
- Claude MCP integration
- Historical analysis
- Watchlists
- Portfolio management

## Technology

- Python 3.13
- uv
- Typer
- Rich
- Pytest
- Ruff
- MyPy
- Pydantic
- YAML configuration

## Development

Install dependencies

```bash
uv sync
```

Run tests

```bash
pytest
```

Run lint

```bash
ruff check .
```

Run type checking

```bash
mypy app
```

Run Aegis

```bash
uv run aegis
```