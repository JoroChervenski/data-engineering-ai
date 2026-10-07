# Security Standard

Engineering guidance for secrets, identities and least privilege. Used by
the [Reviewer agent](../agents/reviewer.agent.md) and checked during
[`code-review`](../skills/code-review/SKILL.md). The severity model used
across every review skill is defined in
[`skills/code-review/SKILL.md`](../skills/code-review/SKILL.md#severity-model);
any committed secret is always **Critical** under that model.

## Secrets

Never place secrets (passwords, tokens, connection strings, API keys,
private keys, certificates) in:

- source code
- `AGENTS.md`, project manifests, or any `.ai/` documentation
- committed `.env` files
- prompts, skill definitions, or agent definitions
- notebooks, pipeline definitions, or configuration committed to Git

Secrets belong in approved secure mechanisms: Key Vault, managed
identity/workload identity, a credential manager, or a CI/CD secret
store. If a secret is found committed, treat it as compromised — flag it
as Critical and recommend rotation, not just removal from the file.

## Identities and access

- Prefer managed identity/workload identity over service principal
  secrets where the platform supports it.
- Apply least privilege: grant the minimum role/scope an identity
  actually needs, not a broad admin role for convenience.
- Keep environments (dev/test/prod) under separate identities/roles so a
  compromised dev credential cannot reach production.

## RLS/OLS and sensitive data

- Apply Row-Level Security (RLS) and Object-Level Security (OLS) in
  semantic models deliberately, based on actual access requirements —
  verify, do not assume a pattern from another project still applies.
- Treat PII according to the client's actual data-classification
  requirements; when unknown, flag it as an open question rather than
  assuming no restriction applies.

## External operations

Before any operation against Azure/Fabric/remote environments, verify
where possible: tenant, subscription, resource group,
workspace/environment, target branch, and deployment stage. A command
that is safe in dev can be destructive in production — confirm the
target before acting.

Destructive or production-changing operations require explicit human
approval. This framework's Phase 1 scope does not include any such
operation (see [Tool classification](#tool-classification) below) —
Phase 1 is read/local-write only.

## Tool classification

Design and reason about external tool access using these levels:

| Level | Capability |
|---|---|
| L0 | Observe/read only |
| L1 | Modify local working tree/branch |
| L2 | Push branch / create remote PR |
| L3 | Change/deploy cloud environments |

Use the lowest level a task actually requires. Phase 1 of this framework
only uses L0 and L1. Production deployment (L3) stays human-controlled
until that is explicitly changed in a later phase.

Example conceptual tool categories:

```text
READ           e.g. fabric.list_items, sql.query_readonly
WRITE_LOCAL    e.g. git.modify_worktree
WRITE_REMOTE   e.g. github.create_pull_request
EXECUTE        e.g. running a local test suite
DEPLOY         e.g. fabric.deploy_to_prod
```

## Unsafe commits

Before any commit, check for: secrets, real tenant/subscription
identifiers, real client data, and production endpoints. If any of these
would be introduced, stop and flag it rather than committing.
