# Microsoft Fabric Standard

Engineering guidance for working with Microsoft Fabric. Used by the
[Architect agent](../agents/architect.agent.md) for platform decisions
and the [Data Engineer agent](../agents/data-engineer.agent.md) for
implementation.

## Lakehouse vs. Warehouse

Choose based on the actual workload:

- **Lakehouse** — Spark-first workloads, flexible schema evolution,
  file-based/Delta-native processing, data science workloads alongside
  engineering.
- **Warehouse** — T-SQL-first workloads, workloads that need full
  transactional T-SQL semantics, teams/tools that expect a traditional
  warehouse surface.

Do not default to one without checking the workload and team skillset
that will actually use it.

## OneLake

Treat OneLake as the single logical storage layer across Fabric items.
Prefer **shortcuts** over physically copying data between
Lakehouses/Warehouses when the source is already in OneLake or an
already-supported external location.

## Direct Lake

- Prefer Direct Lake for Power BI semantic models over Lakehouse/
  Warehouse data when the model can tolerate Direct Lake's refresh and
  fallback semantics, for the performance and freshness benefits over
  Import.
- Understand the conditions that cause Direct Lake to fall back to
  DirectQuery, and design the Gold layer so fallback is unlikely for the
  reporting patterns actually in use.
- Use Import or DirectQuery instead when the workload's requirements
  (complex DAX time intelligence, row-level security patterns, data
  volume/freshness trade-offs) fit them better.

## Spark and notebooks

- Right-size the Spark pool/session for the actual workload; do not
  default to the largest available configuration.
- Keep notebook logic structured and parameterized so it can run
  unattended via a pipeline, not only interactively.

## Pipelines, Dataflows Gen2, notebooks

Choose the orchestration/transformation tool based on the actual need:

- **Pipelines** for orchestration and control flow.
- **Notebooks (PySpark/Spark SQL)** for complex transformation logic.
- **Dataflows Gen2** for low-code transformation where the team's skills
  and maintenance model favor it over notebook code.

Do not add a tool because it exists in Fabric; add it because it is the
best fit for the actual requirement.

## Git integration and deployment

- Keep Fabric workspace items under Git integration so changes are
  reviewable, consistent with [Git as the system of record](../AGENTS.md).
- Use workspace/environment separation (dev/test/prod) with Fabric
  deployment pipelines or an equivalent promotion process; do not let
  developers edit a production workspace directly.

## Capacity awareness

Be explicit about which Fabric capacity a workload runs against and its
expected consumption; a design that works on a test capacity may not be
viable on the capacity the client actually pays for.

## Security and monitoring

- Use workspace roles and item-level permissions for least-privilege
  access; do not grant broad admin access by default.
- Use Fabric/Azure Monitor capabilities appropriate to the workload for
  pipeline/job observability; do not rely on manual checking.
- Apply RLS/OLS in semantic models deliberately, verified against actual
  requirements — not copied from an unrelated project.
