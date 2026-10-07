# Python Standard

General engineering guidance for Python code in data engineering work.
Used by the [Data Engineer agent](../agents/data-engineer.agent.md) and
checked during [`code-review`](../skills/code-review/SKILL.md).

## Type hints

Use type hints where they add clarity or catch real mistakes —
function signatures, public module boundaries, data structures passed
between components. Do not chase 100% type-hint coverage for its own
sake if it adds noise without value.

## Module boundaries

Keep clear boundaries: ingestion, transformation, and
loading/orchestration logic should be separable and independently
testable. Avoid one module that does all three with no internal
structure.

## Configuration

- Configuration (connection targets, paths, thresholds, feature flags) is
  explicit and externalized — never hard-coded inline, never
  environment-specific values baked into shared code.
- No secrets in configuration files committed to the repository. See
  [`security.md`](security.md).

## Logging

- Use structured logging (consistent fields: component, operation,
  identifiers, outcome) rather than ad-hoc print statements.
- Log enough to diagnose a production failure without re-running the job
  with extra instrumentation first.
- Do not log secrets, full PII payloads, or connection strings.

## Exceptions

- Raise/propagate specific exceptions rather than swallowing errors
  silently.
- Catch only what can actually be handled meaningfully at that point;
  do not catch broad exceptions just to continue execution silently.
- Fail loudly and visibly for conditions that compromise data
  correctness (e.g., an unexpected schema, a missing required column).

## Testing

- Business logic should be testable without a live external
  dependency (database, API, cluster) — isolate it behind a function or
  class that can be tested with fixtures.
- See [`testing.md`](testing.md) for test-type selection.

## Maintainability

- Clear, intention-revealing naming over clever abbreviation.
- Avoid deep nesting; prefer early returns and small functions with a
  single responsibility.
- Avoid introducing a new dependency/framework for something the standard
  library or an already-used dependency already does adequately.
