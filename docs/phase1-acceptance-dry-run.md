# Phase 1 acceptance dry-run

Executes the acceptance test in section 28 of
[the implementation spec](../AI_DATA_ENGINEERING_PLATFORM_IMPLEMENTATION_SPEC.md)
against a fictitious fixture, [tests/fixtures/example-retail](../tests/fixtures/example-retail).

- Date: 2026-10-08. Framework commit: `89be5f9`.
- Procedure: [`/bootstrap-project`](../commands/bootstrap-project.md) steps 1–6, using
  [`repository-discovery`](../skills/repository-discovery/SKILL.md) and the
  [templates](../templates/). The overlay was written to a scratch folder, not to this repository.
- **Limits.** One session did both the fixture and the run, so this is not a blind test.
  No subagent was invoked. Only `AGENTS.md`, `.ai/manifest.yaml` and `.ai/PROJECT.md` were
  generated; ARCHITECTURE, DATA-MODEL, GLOSSARY, STANDARDS and TECH-DEBT were not.

## Fixture ground truth

The fixture contains these facts and flaws. The fixture itself does not say so.

| # | Planted | Where |
|---|---|---|
| 1 | Three silver tables are read but nothing produces them | `silver.customers`, `silver.order_lines`, `silver.payments` |
| 2 | Deploy script referenced, not in the repository | `.github/workflows/deploy.yml` |
| 3 | Push to `main` deploys to production, no test or approval step | `deploy.yml` |
| 4 | `.collect()` of a whole table only to count rows | `notebooks/bronze_orders.py` |
| 5 | `dropDuplicates` with no ordering, full overwrite, unguarded cast | `notebooks/silver_orders.py` |
| 6 | `SELECT *`, no surrogate key, full replace | `sql/gold/dim_customer.sql` |
| 7 | Grain undeclared; `LEFT JOIN` to payments can repeat line rows | `sql/gold/fact_sales.sql` |
| 8 | Bidirectional relationship | `semantic_model/definition/model.tmdl` |
| 9 | The only test imports no pipeline code and is not matched by default test discovery | `tests/silver_orders_checks.py` |

## The ten questions

"Executed" means done against the fixture. "By reading" means checked in the framework's
documents only.

| # | Question | Result | Basis |
|---|---|---|---|
| 1 | What technologies are present? | Pass | Executed. PySpark, Delta, SQL, TMDL Direct Lake, GitHub Actions. |
| 2 | Known vs inferred? | Pass, with finding F1 | Executed. Fabric, lakehouse and Kimball are labelled Inferred or template default. |
| 3 | Which files define architecture or deployment? | Pass | Executed. Pipeline, `sql/gold`, semantic model, `deploy.yml`. No architecture document exists. |
| 4 | Which overlay should be created? | Pass | Executed for `AGENTS.md`, `.ai/manifest.yaml` and `.ai/PROJECT.md`; the other overlay files were not generated. |
| 5 | What information is missing? | Pass | Executed. Six open questions, covering planted items 1, 2, 3 and 9 and the unstated grain and SQL engine. |
| 6 | Which architectural risks are visible? | Partial | Not run. Discovery by design makes no recommendations; this needs `/architecture-review`. By reading, the standards and the `code-review` skill cover items 4, 6, 7 (join cardinality, duplicate records, grain) and 8, and the approval rule behind item 3. Item 5 is only partly covered (`standards/sql.md` on determinism; nothing on `dropDuplicates`). |
| 7 | What should the agent do before modifying code? | Pass | By reading. Discovery, then an approved plan: [orchestration](../skills/orchestration/SKILL.md) steps 2–5. |
| 8 | Which specialist for a given task? | Pass | By reading. The orchestration role table; a review goes to the Reviewer subagent. |
| 9 | How is a PR prepared? | Pass | By reading. [`pull-request`](../skills/pull-request/SKILL.md) needs the diff, test results and review findings, and refuses unreviewed work. |
| 10 | How is client leakage prevented? | Pass, instruction-level only | By reading. Rules in the repository-analyst agent, bootstrap command, orchestration skill and templates. Nothing enforces them technically. |

**Result: Phase 1 acceptance passed, with the limits above and three findings.**

## Findings about the framework

None of these is fixed here. Each is a candidate for the [inbox](../inbox/README.md).

- **F1. Template defaults can pass as observations.** [manifest.yaml](../templates/manifest.yaml)
  pre-fills `platform.primary: microsoft-fabric` and `modelling.analytical_standard: kimball`.
  Booleans such as `warehouse: false` cannot say Unknown. The bootstrap command says to
  leave unobserved fields as "the template's defaults/unknown markers", which allows both.
  The dry-run worked around it with inline comments.
- **F2. No place for a human approval gate.** The orchestration skill stops at "anything the
  overlay names as a separate human approval gate", but
  [templates/AGENTS.md](../templates/AGENTS.md) has no field for one. The dry-run put a
  "Proposed rule" in section 8.
- **F3. Discovery does not record test-runner facts.** The fixture's only test is outside default
  discovery and exercises no pipeline code. The discovery output format has a Testing section,
  but nothing prompts for "is it run by anything?".
