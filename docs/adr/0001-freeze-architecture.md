# ADR-0001 — Freeze Architecture

## Status

Accepted

## Context

During the initial development of Aegis, several architectural alternatives were explored.

Frequent structural changes made it difficult to maintain consistency across the codebase and slowed down feature development.

## Decision

The architecture is frozen during Sprint 0.

Until Sprint 1 begins:

- No folder restructuring.
- No renaming of existing concepts.
- No pattern changes.
- No refactoring unless required to fix a bug.

The only allowed work is preparing the repository and development workflow.

## Consequences

Development becomes predictable.

Future PRs focus on delivering functionality instead of redesigning the system.