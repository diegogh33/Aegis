# ADR-0002 — Configuration First

## Status

Accepted

## Context

Investment strategies evolve over time.

Hardcoded parameters make maintenance difficult and require code changes for simple adjustments.

## Decision

Investment parameters must live outside the source code.

Configuration files are the single source of truth for:

- Delta ranges
- DTE ranges
- Liquidity thresholds
- Earnings windows
- Risk parameters
- Strategy settings

## Consequences

Strategies can evolve without modifying business logic.

The engine remains generic and reusable.