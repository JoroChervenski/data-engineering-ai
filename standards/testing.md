# Testing Standard

Engineering guidance for choosing and writing tests. Used by the
[`testing`](../skills/testing/SKILL.md) skill and checked during
[`code-review`](../skills/code-review/SKILL.md).

## Test types

- **Unit** — isolated logic: pure transformation functions, business
  rules, parsing/validation logic.
- **Integration** — a pipeline/job run end to end against realistic
  (not necessarily production-scale) inputs.
- **Data quality** — nulls, uniqueness, referential integrity, valid
  value ranges, schema conformance on actual data.
- **Reconciliation** — totals/counts match between source and target, or
  between old and new logic during a migration/refactor.
- **Regression** — a previously identified and fixed defect does not
  reappear.
- **Business-rule validation** — a specific documented business rule
  produces the documented outcome, with a test case per rule where rules
  are non-trivial.

Choose the subset that actually matches the risk in the change being
tested; see [`skills/testing/SKILL.md`](../skills/testing/SKILL.md) for
the selection procedure.

## Determinism

Tests must produce the same result on every run given the same input.
Avoid dependence on wall-clock time, execution order, or external live
services unless that dependency is itself what is being tested (and is
then isolated and clearly labeled).

## Production-safe validation

- Never run a test that writes to or mutates a production environment.
- Reconciliation/validation performed against production data should be
  read-only.
- Any test fixture that resembles real client data must be synthetic or
  anonymized — never real client data copied into a test fixture.

## Schema checks

Validate that the actual output schema matches the expected schema
(column names, types, nullability) for any Gold-layer or externally
consumed table/model — schema drift is a common, easy-to-miss defect
class.

## Regression tests

When fixing a defect found via [incident analysis](../skills/incident-analysis/SKILL.md),
add a regression test that would have caught it, as part of the same
change.
