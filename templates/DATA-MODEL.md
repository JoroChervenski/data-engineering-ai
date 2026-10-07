# Data Model: <project-name>

<!-- Fill per fact table/dimension actually found. Grain must be stated
     explicitly for every fact table, even if the answer is "not
     declared anywhere in the repository." See standards/kimball.md. -->

## Business Processes

<List the business processes modeled, as observed/inferred.>

## Fact Tables

### <fact table name>

- **Grain:** <one sentence — "one row per ..."; or "Not declared;
  inferred as ..."; or "Unknown.">
- **Type:** <transaction / periodic snapshot / accumulating snapshot /
  factless>
- **Key measures:** <...>
- **Dimensions referenced:** <...>

<Repeat per fact table.>

## Dimensions

### <dimension name>

- **Natural/business key:** <...>
- **Surrogate key:** <...>
- **SCD type:** <0 / 1 / 2, and why>
- **Conformed across:** <which fact tables/processes, if applicable>

<Repeat per dimension.>

## Known Anti-Patterns / Findings

<From a kimball-review pass, if one has been performed. Leave as "Not yet
reviewed" otherwise.>

## Semantic Model Notes

<Direct Lake/Import/DirectQuery mode, relationship directions, RLS/OLS,
if observed.>
