# Kimball Dimensional Modelling Standard

The default analytical modelling standard for Gold/serving layers and
semantic models where dimensional analytics is appropriate — not a
universal storage model. Do not force Bronze/Silver/staging/CDC
structures into facts and dimensions. Used by the
[Data Modelling work in the Architect agent](../agents/architect.agent.md)
and the [`kimball-review`](../skills/kimball-review/SKILL.md) skill.

## Core sequence

1. **Business process first.** Identify the business process a fact
   table represents before designing anything.
2. **Grain first.** Declare the fact table's grain explicitly before
   adding a single column. "One row per X" must be statable in one
   sentence.
3. **Facts.** Design measures appropriate to the grain; avoid mixing
   grains in one fact table.
4. **Dimensions.** Design around surrogate keys, with natural/business
   keys retained for traceability.

## Dimension design

- **Surrogate keys** for every dimension; natural/business keys kept as
  attributes.
- **Conformed dimensions** shared across fact tables/business processes
  where the same real-world entity is involved — do not duplicate a
  dimension that should be conformed.
- **Role-playing dimensions** where one dimension plays multiple roles
  (e.g., a date dimension used as order date and ship date) via views or
  aliasing, not by duplicating the table.
- **Junk dimensions** for small, low-cardinality flags/indicators that
  would otherwise clutter the fact table.
- **Degenerate dimensions** kept on the fact table when there is no
  additional attribute to warrant a separate dimension (e.g., a
  transaction number).
- **Bridge tables** for legitimate many-to-many relationships, with a
  clear weighting/allocation rule if needed for additive measures.

## Fact table types

- **Transaction facts** — one row per event.
- **Periodic snapshot facts** — one row per entity per period.
- **Accumulating snapshot facts** — one row per process instance, updated
  as it progresses through milestones.
- **Factless facts** — track occurrence/coverage without a numeric
  measure.

## Slowly Changing Dimensions (SCD)

- **Type 0** — attribute never changes once set.
- **Type 1** — overwrite; no history kept. Use only when history of that
  attribute genuinely has no business value.
- **Type 2** — new row with effective dating; use when history matters
  for correct point-in-time analysis.
- Match the SCD type to how the attribute is actually used downstream —
  do not default to Type 2 for every attribute, and do not default to
  Type 1 just because it's simpler to implement.

## Late-arriving data, inferred and unknown members

- Define explicit handling for late-arriving facts (the dimension row
  may not exist yet) and late-arriving dimension updates (facts already
  loaded against an old dimension row).
- Use inferred members for dimension rows that must exist before full
  attribute data is available, and backfill them explicitly later.
- Always provide an unknown member for a dimension so fact rows are never
  silently dropped or orphaned due to a missing dimension key.

## Semantic-model considerations

- Keep relationships single-directional unless a bidirectional filter is
  a deliberate, justified choice — not a default.
- Avoid fact-to-fact relationships.
- Keep high-cardinality attributes out of the model where they are not
  needed for filtering/grouping, for Direct Lake/Import performance.

## Anti-patterns to flag in review

- Mixed grain within a single fact table.
- Snowflaking without stated justification.
- Unnecessary many-to-many relationships.
- Fact-to-fact relationships.
- Bidirectional filtering used to patch a modelling gap.
- Incorrect SCD type for how the attribute is actually used.
- Duplicated dimensions that should be conformed.
- Weak/ambiguous naming, poor or missing surrogate keys.
- Excessive calculated columns that belong in ETL or as measures instead.
- High-cardinality attributes causing semantic-model performance
  problems.
