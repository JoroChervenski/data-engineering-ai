# AI-Assisted Data Engineering Consulting Platform
## Implementation Specification and Bootstrap Instructions

**Document purpose:** This file is the authoritative implementation brief for an AI coding agent working in Visual Studio Code.

**Primary user:** Senior Data Engineer / Data Engineering Consultant working across multiple client projects.

**Primary environment:** Visual Studio Code, Git repositories, Microsoft Fabric, Azure, Power BI, SQL, Python, PySpark, GitHub and/or Azure DevOps.

**Implementation principle:** Build a small, reliable foundation first. Do not attempt to create the entire platform in one pass.

---

# 1. Mission

Build an end-to-end **AI-assisted Data Engineering Consulting Platform** that acts like a virtual Principal Data Engineering team inside Visual Studio Code.

The platform must help with the full engineering lifecycle:

1. Understand an existing repository and reconstruct its architecture.
2. Evaluate current architecture and data modelling.
3. Compare current, target and alternative architectures.
4. Plan implementation work.
5. Implement production-quality changes.
6. Test and validate those changes.
7. Perform independent code, security, data-quality and architecture reviews.
8. Prepare Git branches and pull requests.
9. Support incident investigation and root-cause analysis.
10. Support deployment and operational readiness.
11. Maintain strict isolation between different client projects.

The system must be highly proficient in the Microsoft data ecosystem, especially Microsoft Fabric.

---

# 2. Non-Negotiable Design Principles

These principles override convenience.

## 2.1 Repository truth over AI memory

The repository and approved project documentation are the source of truth.

The AI must not assume that previously observed architecture, configuration or implementation is still correct.

For non-trivial work, inspect the relevant repository state before making architectural or implementation decisions.

---

## 2.2 Strict client isolation

The reusable AI framework must not contain client-specific confidential information.

Do **not** create this structure:

```text
data-engineering-ai/
└── projects/
    ├── client-a/
    ├── client-b/
    └── client-c/
```

Instead use physically/logically separated client working directories and repositories:

```text
work/
├── ai-data-engineering-platform/
├── client-a/
│   ├── repo-1/
│   └── repo-2/
├── client-b/
│   └── repo-1/
└── client-c/
    └── repo-1/
```

The central framework contains reusable engineering knowledge only.

Client-specific facts, rules, architecture, glossary, technical debt and decisions belong inside the corresponding client repository.

Never copy confidential context from one client repository into another.

---

## 2.3 Git is the system of record

AI-generated decisions that matter must become reviewable repository artifacts where appropriate:

- code
- tests
- architecture documentation
- ADRs
- standards
- runbooks
- configuration
- pull request descriptions

Do not build an undocumented AI-only knowledge layer.

---

## 2.4 Agents and skills are different concepts

An **agent** represents a role or responsibility.

A **skill** represents a repeatable engineering procedure.

Example:

```text
Data Engineering Agent
├── pyspark-development
├── sql-development
├── incremental-load
├── cdc
├── api-ingestion
└── delta-lake
```

A skill may be reusable by several agents.

Avoid duplicating the same procedure across multiple agent prompts.

---

## 2.5 Do not over-agent the system

Do not invoke every specialist for every task.

Use:

```text
Request
  ↓
Orchestrator
  ↓
Context discovery
  ↓
Task classification
  ↓
Relevant specialist(s)
  ↓
Review gate
  ↓
PR / result
```

A small Python bug should not automatically invoke the Fabric Architect, Kimball specialist, Power BI specialist and Spark specialist.

Specialists are invoked only when the task scope requires them.

---

## 2.6 Kimball is the default analytical modelling standard, not a universal storage model

Use Kimball dimensional modelling by default for analytical Gold/serving layers and semantic models where dimensional analytics is appropriate.

Do not force raw ingestion, CDC staging, Bronze or canonical Silver structures into dimensions and facts.

Typical pattern:

```text
SOURCE
  ↓
BRONZE
Raw / immutable / source aligned
  ↓
SILVER
Clean / validated / standardized
  ↓
GOLD
Kimball dimensional model
  ↓
SEMANTIC MODEL
  ↓
POWER BI
```

Before creating a fact table, explicitly define its grain.

---

## 2.7 Least privilege

External tools must be separated conceptually into permission levels:

| Level | Capability |
|---|---|
| L0 | Observe/read only |
| L1 | Modify local working tree/branch |
| L2 | Push branch/create remote PR |
| L3 | Change/deploy cloud environments |

Agents should use the lowest level required.

Initial implementation should prioritize L0 and L1.

Production deployment must remain human-controlled until explicitly changed later.

---

# 3. Scope of Expertise

The framework must support expert reasoning and implementation across:

## Microsoft Fabric

- OneLake
- Lakehouse
- Warehouse
- Delta Lake
- Spark
- PySpark
- Fabric Notebooks
- Pipelines
- Data Factory
- Dataflows Gen2
- Eventstream
- Eventhouse
- Real-Time Intelligence
- Shortcuts
- Mirroring
- SQL analytics endpoints
- Semantic Models
- Direct Lake
- Import
- DirectQuery
- Power BI
- Fabric REST APIs
- Fabric CLI
- Git integration
- Deployment Pipelines
- environments
- capacities
- workspaces
- security
- governance
- monitoring

Prefer Fabric-native capabilities when they satisfy the requirement without creating unnecessary operational complexity.

## Azure / Microsoft Data Platform

- Azure Data Factory
- Azure Databricks
- Azure SQL Database
- SQL Server
- Azure SQL Managed Instance
- Azure Data Lake Storage
- Azure Functions
- Logic Apps
- Azure Key Vault
- Azure Monitor
- Log Analytics
- Azure DevOps
- Entra ID
- Managed Identity
- Service Principals
- networking
- Private Endpoints

## Analytics

- Power BI
- Tabular semantic models
- TMDL
- DAX
- Power Query M
- RLS
- OLS
- Direct Lake
- Import
- DirectQuery
- XMLA

## Engineering

- Python
- PySpark
- Spark SQL
- T-SQL
- SQL
- REST APIs
- Microsoft Graph
- YAML
- JSON
- Parquet
- Delta
- Avro
- Git
- CI/CD

---

# 4. Target Logical Architecture

Implement the solution as five logical layers.

```text
┌────────────────────────────────────────────────────────┐
│ EXPERIENCE LAYER                                       │
│ VS Code + Chat + Commands + Git Diff                  │
└───────────────────────┬────────────────────────────────┘
                        │
┌───────────────────────▼────────────────────────────────┐
│ ORCHESTRATION LAYER                                    │
│ Orchestrator + Context Builder + Router + Review Gate │
└───────────────────────┬────────────────────────────────┘
                        │
┌───────────────────────▼────────────────────────────────┐
│ AGENT LAYER                                             │
│ Architect | Fabric | Model | DE | SQL | Spark | BI    │
│ Security | Testing | Reliability | DevOps | PR        │
└───────────────────────┬────────────────────────────────┘
                        │
┌───────────────────────▼────────────────────────────────┐
│ SKILL LAYER                                             │
│ Kimball | SQL | PySpark | Fabric | Testing | Git      │
│ DQ | CDC | APIs | Performance | Security | RCA        │
└───────────────────────┬────────────────────────────────┘
                        │
┌───────────────────────▼────────────────────────────────┐
│ TOOL LAYER                                              │
│ Git | GitHub | Azure DevOps | Fabric | Azure | SQL    │
│ Power BI | REST APIs | MCP | shell | CI/CD            │
└────────────────────────────────────────────────────────┘
```

Each client repository forms a separate context/security boundary around the framework invocation.

---

# 5. Agent Model

The final platform may support the following roles.

Do not implement all of them immediately.

## 5.1 Orchestrator Agent

Responsibilities:

- interpret the request
- determine the current project/repository
- determine required context
- classify the task
- create an execution plan
- select specialist agents/skills
- detect conflicting recommendations
- ensure review gates are executed
- aggregate the final result

The Orchestrator must not perform all specialist work itself.

---

## 5.2 Repository Analyst

Responsibilities:

- inspect repository structure
- detect technologies
- detect configuration
- detect data sources and targets
- identify entry points
- identify orchestration
- identify deployment configuration
- identify CI/CD
- identify semantic model artifacts
- identify Fabric artifacts
- identify infrastructure definitions
- reconstruct dependencies
- reconstruct data flows
- identify possible dead/obsolete code
- identify environment-specific configuration
- identify documentation gaps

Outputs should be evidence-based.

---

## 5.3 Data Architect

Responsibilities:

- current-state architecture
- target architecture
- alternative architectures
- integration architecture
- architectural trade-offs
- scalability
- availability
- disaster recovery
- cost and operational complexity
- architecture diagrams
- ADR proposals
- migration roadmap

Architecture choices must consider:

- scale
- latency
- complexity
- maintainability
- team skills
- budget
- SLA
- security
- governance
- operational ownership
- expected growth

---

## 5.4 Fabric Architect

Responsibilities:

- Fabric workspace architecture
- Lakehouse vs Warehouse decisions
- OneLake
- shortcuts
- Direct Lake
- Spark
- capacity considerations
- pipelines
- deployment
- Git integration
- security
- performance
- monitoring
- Fabric-native alternatives

---

## 5.5 Data Modelling Agent

Primary methodology: Kimball dimensional modelling.

Responsibilities:

- business process identification
- fact grain
- facts
- dimensions
- surrogate keys
- natural/business keys
- conformed dimensions
- role-playing dimensions
- junk dimensions
- degenerate dimensions
- bridge tables
- factless facts
- transaction facts
- periodic snapshots
- accumulating snapshots
- SCD Types 0/1/2
- late-arriving facts/dimensions
- inferred members
- unknown members
- date/time dimensions
- semantic-model compatibility

Review for:

- mixed grains
- snowflaking without justification
- unnecessary many-to-many relationships
- fact-to-fact relationships
- bidirectional filtering
- incorrect SCD handling
- duplicated dimensions
- weak naming
- poor keys
- excessive calculated columns
- high-cardinality attributes
- semantic model performance problems

---

## 5.6 Data Engineering Agent

Responsibilities:

- Python
- PySpark
- Spark SQL
- T-SQL
- ingestion
- transformation
- incremental loading
- CDC
- APIs
- batch
- streaming
- Delta Lake
- schema evolution
- structured logging
- idempotency
- configuration management

---

## 5.7 SQL Specialist

Responsibilities:

- SQL correctness
- data access patterns
- execution plans
- indexing
- statistics
- query rewrites
- table design
- partitioning
- Azure SQL performance
- Fabric Warehouse performance

---

## 5.8 Spark Specialist

Responsibilities:

- Spark physical/logical plans
- joins
- shuffle
- partitioning
- skew
- caching
- AQE
- file sizing
- Delta optimization
- Spark configuration
- avoiding unnecessary driver-side operations

---

## 5.9 Semantic Model Specialist

Responsibilities:

- Power BI semantic models
- Direct Lake
- Import
- DirectQuery
- DAX
- TMDL
- RLS
- OLS
- relationships
- cardinality
- filter direction
- workspace architecture
- performance

---

## 5.10 Security Reviewer

Responsibilities:

- secrets
- Key Vault
- Managed Identity
- workload identities
- RBAC
- service principals
- network isolation
- PII
- RLS/OLS
- least privilege
- environment separation

Any committed secret must be categorized as **Critical**.

---

## 5.11 Testing and Data Quality Reviewer

Responsibilities:

- unit tests
- integration tests
- data-quality tests
- schema validation
- null rules
- uniqueness
- referential integrity
- reconciliation
- regression tests
- business-rule validation

Potential tools include pytest, SQL tests, Spark tests, dbt tests, Great Expectations, Soda or custom frameworks when justified.

---

## 5.12 Production Reliability Reviewer

Responsibilities:

- retries
- idempotency
- structured logging
- alerting
- metrics
- dead-letter handling
- checkpointing
- recovery
- SLA
- RPO
- RTO
- data loss
- duplicate processing
- failure isolation

---

## 5.13 DevOps Agent

Responsibilities:

- Git
- branching
- GitHub
- Azure DevOps
- CI/CD
- automated tests
- environment promotion
- deployment
- rollback
- release strategy

---

## 5.14 PR Agent

Runs near the end of a task.

Inputs:

- ticket/request
- implementation plan
- diff
- tests
- review findings

Outputs:

- branch name
- PR title
- summary
- business reason
- technical changes
- architecture impact
- data impact
- testing
- deployment
- rollback
- risks
- review checklist

Do not automatically approve or merge PRs.

---

# 6. Skill Architecture

A skill must contain a reusable procedure, decision criteria, evidence requirements, expected output and quality checks.

Do not use skills as role/persona documents.

Target skill groups:

```text
skills/
├── architecture/
│   ├── repository-discovery/
│   ├── architecture-discovery/
│   ├── architecture-review/
│   ├── architecture-comparison/
│   └── adr/
│
├── modelling/
│   ├── kimball-design/
│   ├── grain-analysis/
│   ├── scd-design/
│   └── semantic-model-review/
│
├── fabric/
│   ├── fabric-platform-design/
│   ├── direct-lake-review/
│   ├── fabric-cicd/
│   └── capacity-analysis/
│
├── engineering/
│   ├── python-development/
│   ├── pyspark-development/
│   ├── sql-development/
│   ├── incremental-load/
│   ├── cdc/
│   ├── api-ingestion/
│   ├── delta-lake/
│   └── schema-evolution/
│
├── quality/
│   ├── testing/
│   ├── data-quality/
│   └── reconciliation/
│
├── operations/
│   ├── incident-analysis/
│   ├── root-cause-analysis/
│   ├── observability/
│   └── production-readiness/
│
└── delivery/
    ├── code-review/
    ├── security-review/
    ├── git/
    ├── pull-request/
    └── cicd/
```

---

# 7. Central Framework Repository

Create the reusable framework repository with this target structure:

```text
data-engineering-ai/
│
├── README.md
├── AGENTS.md
│
├── agents/
│   ├── orchestrator.agent.md
│   ├── repository-analyst.agent.md
│   ├── architect.agent.md
│   ├── fabric-architect.agent.md
│   ├── data-modeler.agent.md
│   ├── data-engineer.agent.md
│   ├── sql-specialist.agent.md
│   ├── spark-specialist.agent.md
│   ├── semantic-model.agent.md
│   ├── security-reviewer.agent.md
│   ├── quality-reviewer.agent.md
│   ├── reliability-reviewer.agent.md
│   ├── devops.agent.md
│   └── pr.agent.md
│
├── skills/
│   ├── architecture/
│   ├── modelling/
│   ├── fabric/
│   ├── engineering/
│   ├── quality/
│   ├── operations/
│   └── delivery/
│
├── standards/
│   ├── architecture.md
│   ├── fabric.md
│   ├── kimball.md
│   ├── python.md
│   ├── pyspark.md
│   ├── sql.md
│   ├── powerbi.md
│   ├── testing.md
│   ├── security.md
│   └── cicd.md
│
├── templates/
│   ├── AGENTS.md
│   ├── PROJECT.md
│   ├── ARCHITECTURE.md
│   ├── DATA-MODEL.md
│   ├── GLOSSARY.md
│   ├── TECH-DEBT.md
│   ├── ADR.md
│   ├── PR.md
│   ├── RUNBOOK.md
│   └── manifest.yaml
│
├── commands/
│   ├── bootstrap-project.md
│   ├── understand-repository.md
│   ├── architecture-review.md
│   ├── compare-architecture.md
│   ├── plan-ticket.md
│   ├── implement.md
│   ├── review-code.md
│   ├── review-pr.md
│   ├── review-data-model.md
│   ├── investigate.md
│   ├── optimize-sql.md
│   ├── optimize-spark.md
│   ├── review-fabric.md
│   ├── production-readiness.md
│   └── prepare-pr.md
│
├── tools/
│   ├── fabric/
│   ├── azure/
│   ├── github/
│   ├── azure-devops/
│   ├── powerbi/
│   └── sql/
│
└── tests/
    ├── agents/
    ├── skills/
    └── standards/
```

This is the **target** structure, not the requirement for the first implementation milestone.

---

# 8. Client Repository Overlay

Each client repository should receive a thin AI/context layer:

```text
client-repository/
│
├── AGENTS.md
│
├── .ai/
│   ├── PROJECT.md
│   ├── ARCHITECTURE.md
│   ├── DATA-MODEL.md
│   ├── GLOSSARY.md
│   ├── STANDARDS.md
│   ├── TECH-DEBT.md
│   ├── manifest.yaml
│   ├── adr/
│   ├── runbooks/
│   └── skills/
│
├── .github/
│   ├── agents/
│   └── instructions/
│
├── src/
├── tests/
└── ...
```

`.ai/skills/` is for client/project-specific skills only.

Examples:

- custom fiscal calendar
- project-specific RLS rules
- legal entity mapping
- client-specific source-system semantics
- bespoke business calculation rules

Generic engineering knowledge must stay in the central framework.

---

# 9. AGENTS.md Contract

Each project root should contain a concise `AGENTS.md`.

It should answer:

1. What is this project?
2. What are the critical architecture constraints?
3. Where are the important files?
4. What technologies are allowed?
5. What technologies are disallowed or discouraged?
6. What testing is required?
7. What security rules apply?
8. How is deployment performed?
9. What directories must not be modified without explicit reason?
10. Where is deeper documentation located?

Do not turn `AGENTS.md` into a giant engineering handbook.

Link to standards and deeper `.ai/` documentation.

---

# 10. Machine-Readable Project Manifest

Create a project manifest template.

Example:

```yaml
schema_version: 1

project:
  name: example-platform
  type: data-platform

platform:
  primary: microsoft-fabric

source_control:
  provider: github

environments:
  - dev
  - test
  - prod

components:
  lakehouse: true
  warehouse: true
  spark: true
  semantic_models: true

modelling:
  analytical_standard: kimball

documentation:
  architecture: .ai/ARCHITECTURE.md
  data_model: .ai/DATA-MODEL.md
  glossary: .ai/GLOSSARY.md
```

Rules:

- no credentials
- no secrets
- no tokens
- no passwords
- no private keys

The Repository Analyst should eventually compare the manifest against the observed repository state and report drift.

---

# 11. Standard Engineering Workflow

For non-trivial implementation requests use this workflow.

```text
TICKET / REQUEST
      ↓
UNDERSTAND
      ↓
REPOSITORY DISCOVERY
      ↓
IMPACT ANALYSIS
      ↓
IMPLEMENTATION PLAN
      ↓
BRANCH
      ↓
IMPLEMENT
      ↓
TEST
      ↓
SPECIALIST REVIEW
      ↓
SECURITY / QUALITY GATE
      ↓
PR PREPARATION
      ↓
HUMAN REVIEW
      ↓
MERGE
      ↓
DEPLOY
      ↓
VALIDATE
```

## Phase 1 — Understand

Determine:

- business objective
- technical requirement
- current repository
- affected components
- constraints
- acceptance criteria

Do not immediately edit code unless the task is trivially obvious and low risk.

## Phase 2 — Investigate

Inspect relevant:

- source code
- SQL
- notebooks
- pipelines
- schemas
- configuration
- semantic models
- documentation
- tests
- deployment files
- Git history when useful

## Phase 3 — Design

Create a concise plan including:

- affected files
- architecture impact
- data-model impact
- security impact
- performance impact
- backward compatibility
- testing strategy
- deployment considerations

## Phase 4 — Implement

Follow:

- KISS
- DRY where meaningful
- SOLID where applicable
- clear naming
- type hints for Python where appropriate
- structured logging
- explicit configuration
- testability
- deterministic processing
- idempotency for pipelines
- safe error handling

## Phase 5 — Test

Choose relevant tests:

- unit
- integration
- data quality
- reconciliation
- schema
- regression
- business-rule validation

## Phase 6 — Review

Independent reviewer(s) must assess:

- correctness
- data loss
- duplicate processing
- broken idempotency
- wrong joins
- incorrect grain
- schema evolution
- security
- performance
- maintainability
- logging and observability

## Phase 7 — PR

Prepare:

- branch name
- PR title
- summary
- reason
- changed files/components
- architecture impact
- data impact
- tests
- deployment
- rollback
- risks
- reviewer checklist

---

# 12. Review Severity Model

All review findings should use:

- **Critical**
- **High**
- **Medium**
- **Low**
- **Suggestion**

Each finding should contain:

```text
Severity
Location
Evidence
Impact
Recommended fix
Confidence
```

Prioritize production risk over cosmetic style.

---

# 13. Architecture Review Workflow

The `/architecture-review` workflow should eventually perform:

```text
Repository inventory
        ↓
Technology detection
        ↓
Architecture reconstruction
        ↓
Data-flow reconstruction
        ↓
Current-state diagram
        ↓
Risk identification
        ↓
Target architecture
        ↓
Alternative architectures
        ↓
Trade-off analysis
        ↓
Migration roadmap
        ↓
ADR candidates
```

Evaluate:

- ingestion
- storage
- transformation
- orchestration
- serving
- semantic models
- reporting
- APIs
- monitoring
- observability
- CI/CD
- security
- governance
- reliability
- cost
- operational complexity
- maintainability

Use qualitative classifications:

- Strong
- Acceptable
- Needs improvement
- High risk
- Critical

Do not invent fake numerical scores unless a formal scoring model is implemented.

---

# 14. Architecture Comparison Output

When comparing architectures include:

1. Current state
2. Problems
3. Root causes
4. Risks
5. Technical debt
6. Recommended target architecture
7. Alternatives
8. Advantages
9. Disadvantages
10. Migration complexity
11. Cost implications
12. Performance implications
13. Security implications
14. Operational implications
15. Migration roadmap

Use ADRs for major decisions.

---

# 15. Incident Investigation Workflow

The `/investigate` workflow must use evidence-driven root-cause analysis:

```text
Symptom
  ↓
Evidence
  ↓
Potential causes
  ↓
Tests / falsification
  ↓
Root cause
  ↓
Fix
  ↓
Validation
  ↓
Prevention
```

Do not jump from an error message directly to a claimed root cause.

Separate:

- known facts
- hypotheses
- missing evidence
- validated root cause

---

# 16. Performance Philosophy

Always consider the whole-system cost of:

- data movement
- compute
- shuffle
- storage
- concurrency
- memory
- network
- semantic-model refresh
- operational complexity
- capacity constraints

Do not optimize one query in a way that degrades the wider platform.

---

# 17. Consultant Perspective

Technical recommendations must account for:

- client maturity
- budget
- team skills
- delivery deadlines
- implementation effort
- operational ownership
- business impact
- migration risk
- maintainability after handover

Do not recommend an elegant platform that the client cannot realistically operate.

For recommendations, distinguish between:

- **Required fix**
- **Best practice**
- **Good practice**
- **Project-specific recommendation**

Do not describe preferences as universal best practices.

---

# 18. Security Requirements

## Secrets

Never place secrets in:

- `AGENTS.md`
- project manifests
- documentation
- committed `.env` files
- prompts
- skill definitions
- agent definitions

Secrets belong in approved secure mechanisms such as Key Vault, workload identity, credential managers or CI/CD secret stores.

## External operations

Before any operation against Azure/Fabric/remote environments, verify where possible:

- tenant
- subscription
- resource group
- workspace/environment
- target branch
- deployment stage

Destructive or production-changing operations require explicit user approval.

## Tool classification

Design tool adapters using categories such as:

```text
READ
WRITE_LOCAL
WRITE_REMOTE
EXECUTE
DEPLOY
```

Examples:

```text
fabric.list_items          -> READ
sql.query_readonly         -> READ
git.modify_worktree        -> WRITE_LOCAL
github.create_pull_request -> WRITE_REMOTE
fabric.deploy_to_prod      -> DEPLOY
```

---

# 19. Initial Implementation Strategy

Do **not** implement the final target structure immediately.

Use the following phases.

---

# 20. Phase 1 — Foundation

This is the first milestone and the only milestone that should be implemented initially unless explicitly instructed otherwise.

## Goal

Create a minimal, coherent framework that can be committed to Git and used to bootstrap one real client repository.

## Implement these files first

```text
data-engineering-ai/
├── README.md
├── AGENTS.md
│
├── agents/
│   ├── orchestrator.agent.md
│   ├── repository-analyst.agent.md
│   ├── architect.agent.md
│   ├── data-engineer.agent.md
│   └── reviewer.agent.md
│
├── skills/
│   ├── repository-discovery/
│   │   └── SKILL.md
│   ├── architecture-review/
│   │   └── SKILL.md
│   ├── kimball-review/
│   │   └── SKILL.md
│   ├── implementation-plan/
│   │   └── SKILL.md
│   ├── code-review/
│   │   └── SKILL.md
│   ├── testing/
│   │   └── SKILL.md
│   ├── incident-analysis/
│   │   └── SKILL.md
│   └── pull-request/
│       └── SKILL.md
│
├── standards/
│   ├── architecture.md
│   ├── kimball.md
│   ├── python.md
│   ├── pyspark.md
│   ├── sql.md
│   ├── fabric.md
│   ├── testing.md
│   └── security.md
│
├── templates/
│   ├── AGENTS.md
│   ├── PROJECT.md
│   ├── ARCHITECTURE.md
│   ├── DATA-MODEL.md
│   ├── GLOSSARY.md
│   ├── TECH-DEBT.md
│   ├── ADR.md
│   ├── PR.md
│   └── manifest.yaml
│
└── commands/
    ├── bootstrap-project.md
    ├── understand-repository.md
    ├── architecture-review.md
    ├── plan-ticket.md
    ├── review-pr.md
    ├── review-data-model.md
    ├── investigate.md
    └── prepare-pr.md
```

Do not add empty placeholder directories for future integrations unless needed by the current design.

---

# 21. Phase 1 Agent Responsibilities

## Orchestrator

Must:

1. classify the request
2. establish repository/project context
3. identify which role/skill is required
4. require repository discovery for unfamiliar repositories
5. require a plan before non-trivial edits
6. trigger review after implementation
7. prevent unrelated specialists from being invoked
8. ensure no client context is mixed

## Repository Analyst

Must produce an evidence-based project inventory including:

- detected technologies
- key directories/files
- likely entry points
- configuration
- data sources/targets if inferable
- pipelines/orchestration
- testing
- deployment
- semantic model/Fabric artifacts if present
- documentation gaps
- open questions

It must distinguish observed facts from inference.

## Architect

Must:

- reconstruct current state
- identify issues/risks
- propose alternatives
- explain trade-offs
- recommend a target
- identify ADR candidates
- consider team/budget/operations

## Data Engineer

Must:

- implement only after adequate context
- follow repository standards
- preserve backward compatibility unless intentionally changed
- include testing
- consider idempotency, logging, schema evolution and failure modes for data pipelines

## Reviewer

Must review independently of implementation intent.

Focus on:

- correctness
- data loss
- duplicate creation
- incremental-loading defects
- wrong joins
- grain violations
- security
- performance
- maintainability
- tests
- observability

---

# 22. Phase 1 Skill Contract

Every `SKILL.md` should use a consistent structure.

Recommended format:

```markdown
# Skill Name

## Purpose

## When to Use

## Inputs

## Preconditions

## Procedure

## Decision Criteria

## Evidence Required

## Output Format

## Quality Checks

## Common Failure Modes

## Escalation / Specialist Handoff
```

Skills should be concise and actionable.

Do not repeat whole engineering standards inside every skill. Link to the relevant standard.

---

# 23. Phase 1 Standard Documents

Standards should encode engineering guidance, not agent personalities.

## `architecture.md`

Include principles for:

- simplicity
- operability
- scalability
- availability
- cost
- governance
- observability
- architecture decision records
- Fabric-native preference when suitable

## `kimball.md`

Include:

- business process first
- declare grain first
- fact/dimension design
- surrogate keys
- conformed dimensions
- SCD
- late-arriving data
- snapshot fact types
- semantic model considerations
- anti-patterns

## `python.md`

Include:

- type hints where useful
- clear module boundaries
- configuration
- logging
- exceptions
- testing
- no secrets
- maintainability

## `pyspark.md`

Include:

- DataFrame-first approach
- avoid unnecessary driver operations
- avoid Python loops over large distributed datasets
- joins
- shuffle
- partitioning
- skew
- caching
- file sizes
- Delta considerations
- testability

## `sql.md`

Include:

- avoid `SELECT *`
- explicit grain
- deterministic logic
- joins
- null semantics
- casts
- performance
- indexing context
- maintainability
- safe schema changes

## `fabric.md`

Include:

- appropriate use of Lakehouse/Warehouse
- OneLake
- Direct Lake
- semantic models
- Pipelines
- notebooks
- Git/deployment
- workspace/environment separation
- capacity awareness
- security
- monitoring

## `testing.md`

Include:

- unit vs integration vs DQ vs reconciliation
- deterministic tests
- business rules
- schema checks
- regression
- production-safe validation

## `security.md`

Include:

- secrets
- identities
- least privilege
- tenant/environment verification
- sensitive data
- RLS/OLS
- external operations
- unsafe commits

---

# 24. Phase 1 Commands

Command documents are reusable workflows.

They should contain:

- purpose
- expected inputs
- skills/roles invoked
- ordered execution steps
- expected output
- safety constraints

## `/bootstrap-project`

Goal:

Create the client repository AI overlay from the templates.

It should create or propose:

```text
AGENTS.md
.ai/PROJECT.md
.ai/ARCHITECTURE.md
.ai/DATA-MODEL.md
.ai/GLOSSARY.md
.ai/STANDARDS.md
.ai/TECH-DEBT.md
.ai/manifest.yaml
.ai/adr/
.ai/runbooks/
```

The bootstrap must first inspect the repository so it does not fill documents with invented information.

Unknown information should be marked clearly, not guessed.

## `/understand-repository`

Runs repository discovery and provides a structured project model.

## `/architecture-review`

Runs repository discovery plus architecture review.

## `/plan-ticket`

Produces an implementation plan but does not change files.

## `/review-pr`

Reviews a diff/branch as a senior/principal engineer.

## `/review-data-model`

Uses Kimball and semantic-model review procedures.

## `/investigate`

Runs evidence-driven incident analysis.

## `/prepare-pr`

Builds a PR description from the actual diff/tests/reviews.

---

# 25. README Requirements

The root `README.md` should explain:

- what the framework is
- what it is not
- architecture
- agents vs skills
- client isolation
- how to bootstrap a client repo
- how to use commands
- current implementation status
- roadmap
- safety model

Add a simple Mermaid diagram if useful.

---

# 26. Root AGENTS.md Requirements

The framework repository's `AGENTS.md` should instruct coding agents that:

- the repository contains reusable generic engineering knowledge
- client-specific confidential information must never be added
- generic logic belongs in skills/standards
- personas/responsibilities belong in agents
- commands orchestrate skills/agents
- templates must remain generic
- secrets are forbidden
- work should be incremental
- tests/validation must accompany meaningful framework changes
- files should not duplicate the same instructions unnecessarily

---

# 27. Quality Requirements for Phase 1

Before declaring Phase 1 complete, verify:

## Structure

- all required Phase 1 files exist
- no unnecessary empty directories
- naming is consistent
- Markdown links resolve where used

## Separation of concerns

- agents describe responsibility
- skills describe reusable procedure
- standards describe engineering principles
- commands describe workflows
- templates are generic
- no client-specific data exists

## Consistency

- terms are used consistently
- review severities are consistent
- client-isolation rules are consistent
- Kimball guidance is consistent
- security guidance is consistent

## Practicality

A coding agent reading only:

```text
AGENTS.md
commands/bootstrap-project.md
skills/repository-discovery/SKILL.md
templates/*
```

should be able to bootstrap a real repository without needing to read every file in the framework.

## Security

- no secrets
- no real client identifiers
- no tokens
- no tenant IDs
- no subscription IDs
- no production endpoints

---

# 28. Phase 1 Acceptance Test

Perform a dry-run against a fictitious example repository or a minimal test fixture.

The framework should be able to answer:

1. What technologies are present?
2. What is known vs inferred?
3. What files define architecture/deployment?
4. What AI overlay should be created?
5. What information is missing?
6. What architectural risks are visible?
7. What should the agent do before modifying code?
8. Which specialist would be invoked for a given task?
9. How would it prepare a PR?
10. How does it prevent client context leakage?

Do not use real confidential client information for the test fixture.

---

# 29. Phase 2 — Core Workflow

Do not implement until Phase 1 is reviewed.

Add deeper behavior for:

- Orchestrator
- Repository Analyst
- Architect
- Data Engineer
- Reviewer

Expand the skills:

- repository discovery
- architecture review
- Kimball review
- implementation planning
- code review
- testing
- PR creation
- incident analysis

The goal is to make one real repository workflow reliable before adding more specialists.

---

# 30. Phase 3 — Microsoft Specialists

After core workflow reliability, split out:

- Fabric Architect
- SQL Specialist
- Spark Specialist
- Semantic Model Specialist
- Security Reviewer
- Testing/Data Quality Reviewer
- Production Reliability Reviewer
- DevOps Agent
- PR Agent

Only split a specialist when the specialization provides concrete value that cannot be maintained cleanly in the existing core roles.

---

# 31. Phase 4 — External Tool Integrations

Add read-only integrations first.

Potential domains:

- GitHub
- Azure DevOps
- Microsoft Fabric
- Azure
- Power BI
- SQL

Prefer a controlled tool/MCP boundary.

Do not give every agent unrestricted access.

Design integration interfaces so that read and write operations are clearly distinguishable.

Example conceptual interfaces:

```text
fabric.list_workspaces
fabric.list_items
fabric.get_item_definition

azure.get_current_account
azure.list_resources

github.get_pull_request
github.get_diff

ado.get_pull_request
ado.get_build_status

sql.query_readonly
```

Write/deploy tools come later.

---

# 32. Phase 5 — Controlled Write Automation

Possible capabilities:

- create branch
- modify files
- commit
- push branch
- create PR
- trigger development pipeline
- update non-production Fabric workspace

Keep production deployment gated.

---

# 33. Phase 6 — Advanced Automation

Only after trust is established consider:

- automated PR review
- architecture drift detection
- manifest drift detection
- semantic-model linting
- automated documentation refresh
- Fabric deployment validation
- production-readiness reports
- CI enforcement of selected standards

---

# 34. Anti-Patterns to Avoid

Do not:

- create one giant system prompt containing all knowledge
- create dozens of agents before workflows are stable
- duplicate the same instructions across agents and skills
- treat AI memory as authoritative project state
- mix clients in one repository/workspace
- commit credentials
- permit unrestricted cloud writes
- invent architecture facts during repository bootstrap
- mechanically recommend Medallion, Data Vault, Lakehouse or microservices
- force Kimball onto raw/staging layers
- optimize for theoretical elegance over client operability
- add unnecessary frameworks
- introduce abstractions without repeated use cases
- generate documentation that is not tied to observable repository facts

---

# 35. Required Behavior When This Document Is Given to an AI Coding Agent

When you are the AI coding agent receiving this document:

1. Treat this document as the implementation specification.
2. Inspect the current repository before changing files.
3. Determine whether the repository is empty, partially initialized or already contains relevant framework files.
4. Reuse valid existing work instead of overwriting it blindly.
5. Produce a concise implementation plan for **Phase 1 only**.
6. Implement Phase 1.
7. Keep the implementation generic and client-independent.
8. Do not add cloud credentials, tenant IDs, subscription IDs, real endpoints or client data.
9. Do not implement external integrations yet unless specifically requested.
10. Validate internal consistency and links.
11. Run any available linting/tests appropriate to the repository.
12. Summarize:
    - files created/changed
    - architecture decisions made
    - validation performed
    - remaining Phase 1 limitations
    - recommended next step
13. Do not proceed to Phase 2 without explicit instruction.

---

# 36. First Execution Prompt

After placing this document in the repository, the recommended first instruction to the AI coding agent is:

> Read `AI_DATA_ENGINEERING_PLATFORM_IMPLEMENTATION_SPEC.md` completely. Treat it as the authoritative implementation specification. Inspect the current repository, then implement **Phase 1 — Foundation only**. Do not implement later phases or external integrations. Before editing, produce a concise plan based on the current repository state. Keep the framework generic and free of any client-specific information. After implementation, validate the structure and internal consistency, then summarize all changed files, validation performed, limitations, and the recommended next step.

---

# 37. Definition of Success

The project is successful when it evolves into a system where a Senior Data Engineer can open a client repository in VS Code and reliably perform workflows such as:

```text
/understand-repository
/architecture-review
/plan-ticket
/implement
/review-pr
/review-data-model
/investigate
/prepare-pr
```

while receiving:

- repository-grounded analysis
- Microsoft/Fabric-aware architecture guidance
- Kimball-aware analytical modelling
- production-quality implementation support
- independent review
- PR-ready output
- strict project isolation
- controlled external access
- evidence-driven troubleshooting

The system should behave like a disciplined virtual Principal Data Engineering team, not like an unconstrained code generator.
