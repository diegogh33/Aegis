# Architecture

This document describes the high-level architecture of Aegis.

## Philosophy

Aegis follows a layered architecture with clear responsibilities.

Every component has one purpose.

## Main Flow

User

↓

CLI

↓

Strategy

↓

Provider

↓

Mapper

↓

Domain Models

↓

Metrics Engine

↓

Selector

↓

Rule Engine

↓

Evaluation Report

↓

Formatter

↓

Output

## Principles

- Business logic lives in the domain.
- Providers only retrieve data.
- Mappers transform external data.
- Rules evaluate.
- Strategies orchestrate.
- Formatters render output.

## Configuration

All investment parameters must live in configuration files.

Business logic must never depend on magic numbers.

## Testing

Every important component must be independently testable.