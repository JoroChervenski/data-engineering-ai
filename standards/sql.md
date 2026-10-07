# SQL Standard

Engineering guidance for SQL/T-SQL/Spark SQL work. Used by the
[Data Engineer agent](../agents/data-engineer.agent.md) and the
[SQL-related checks in `code-review`](../skills/code-review/SKILL.md).

## Explicitness

- Avoid `SELECT *` in production code; name the columns actually needed.
  This protects against upstream schema changes silently breaking or
  silently changing downstream behavior.
- State the grain of every query result explicitly, at least in a
  comment, when the grain is not obvious from a `GROUP BY`.
- Prefer explicit `JOIN ... ON` conditions over implicit joins; be
  explicit about join type (`INNER`/`LEFT`/`FULL`) and the expected
  cardinality.

## Determinism

- Avoid non-deterministic constructs (e.g., unordered `LIMIT`,
  non-deterministic functions without a stable tiebreaker) where the
  result must be reproducible.
- Make null semantics explicit: know whether a comparison, join, or
  aggregate should treat `NULL` as "unknown" (standard SQL semantics) or
  needs a `COALESCE`/`IS NULL` to behave as intended.

## Casts and types

- Cast explicitly when comparing or joining across columns of different
  types; do not rely on implicit coercion rules that vary by engine.
- Be deliberate about precision/scale for numeric types used in
  financial or measure columns.

## Performance

- Understand the query's execution plan for non-trivial queries,
  especially before promoting a query to run on a recurring schedule.
- Use indexing/statistics appropriate to the platform (Azure SQL,
  Fabric Warehouse) rather than assuming a NoSQL-style scan is free.
- Avoid correlated subqueries where a join or window function achieves
  the same result more efficiently.

## Safe schema changes

- Additive changes (new nullable column) are lower risk than
  type changes or column removal; treat the latter as breaking changes
  requiring a compatibility plan.
- Check and update downstream consumers (views, semantic models,
  reports) before/alongside a breaking schema change, not after.

## Maintainability

- Format SQL for readability (consistent indentation, one clause per
  line for non-trivial queries).
- Prefer CTEs over deeply nested subqueries for anything beyond a simple
  query.
