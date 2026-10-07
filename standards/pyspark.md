# PySpark Standard

Engineering guidance for Spark/PySpark work. Used by the
[Data Engineer agent](../agents/data-engineer.agent.md) and checked
during [`code-review`](../skills/code-review/SKILL.md).

## DataFrame-first

Prefer DataFrame/Dataset transformations over RDD-level code unless there
is a concrete, stated reason RDDs are necessary. Prefer built-in
functions (`pyspark.sql.functions`) over UDFs where an equivalent
built-in exists — UDFs block many Catalyst/Photon optimizations.

## Avoid unnecessary driver-side operations

- Do not `collect()`, `toPandas()`, or otherwise pull a large distributed
  dataset to the driver unless the result is already known to be small.
- Avoid Python-level loops over large distributed datasets; express the
  logic as a DataFrame transformation instead.

## Joins, shuffle, partitioning, skew

- Be explicit about join type and expected cardinality; verify it is not
  silently fanning out rows.
- Be aware of which joins trigger a shuffle and whether broadcast join is
  appropriate for a small side.
- Watch for data skew on join/group keys; consider salting or
  pre-aggregation if skew is confirmed, not pre-emptively.
- Partition by a column that matches the actual query/filter pattern, not
  by habit.

## Caching

Cache a DataFrame only when it is reused multiple times in the same job
and recomputation would be materially expensive. Unpersist when no longer
needed. Caching everything "to be safe" wastes executor memory.

## Adaptive Query Execution (AQE) and configuration

Prefer relying on AQE for runtime join-strategy and partition-size
decisions over manual tuning, unless a specific workload has proven AQE's
defaults insufficient. Document any manual Spark configuration override
with the reason it was needed.

## File sizing and Delta considerations

- Avoid producing many small files; prefer `OPTIMIZE`/compaction patterns
  appropriate to the platform where small files are a known issue.
- Be explicit about Delta Lake write mode (append/overwrite/merge) and
  its interaction with partitioning and any downstream consumers.
- Consider schema evolution explicitly: is a schema change expected to be
  additive-only, or can it break downstream consumers?

## Testability

Keep transformation logic in functions that accept a DataFrame and
return a DataFrame, so they can be unit-tested against small,
constructed input DataFrames rather than requiring a full pipeline run.
