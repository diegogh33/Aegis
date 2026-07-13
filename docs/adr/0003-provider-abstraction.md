# ADR-0003 — Provider Abstraction

## Status

Accepted

## Context

Market data may come from multiple providers.

Examples:

- Alpha Vantage
- Interactive Brokers
- Polygon
- Tradier

## Decision

The domain layer must never depend on a specific provider.

Every provider must expose the same interface and convert external data into domain models.

## Consequences

Providers become interchangeable.

Replacing one provider should not affect business logic.