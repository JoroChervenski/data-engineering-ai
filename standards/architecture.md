# Architecture Standard

Engineering principles for evaluating and designing architecture. Used by
the [Architect agent](../agents/architect.agent.md) and the
[`architecture-assessment`](../skills/architecture-assessment/SKILL.md) skill.

## Principles

- **Simplicity first.** The simplest architecture that satisfies the
  actual requirement wins. Complexity must be justified by a concrete,
  present need — not a hypothetical future one.
- **Operability.** An architecture the client's actual team cannot run,
  monitor and troubleshoot after handover is a failed architecture,
  regardless of its technical elegance.
- **Scalability.** Design for the realistic growth that has actually been
  stated or observed, not for unbounded hypothetical scale.
- **Availability.** State the availability requirement explicitly before
  designing for it; do not assume high availability is required by
  default.
- **Cost.** Every architectural choice has a cost in compute, storage,
  licensing, and operational effort. State it, even approximately.
- **Governance.** Data ownership, access control and change control must
  be clear for any architecture proposed.
- **Observability.** An architecture must support knowing whether it is
  working: logs, metrics, alerts for the failure modes that matter.
- **Architecture Decision Records (ADRs).** Decisions with lasting
  consequences and real alternatives get an ADR (see
  [`templates/ADR.md`](../templates/ADR.md)), not just a chat answer.
- **Fabric-native preference.** When Microsoft Fabric's native
  capabilities satisfy a requirement without unnecessary operational
  complexity, prefer them over a custom or third-party alternative. See
  [`fabric.md`](fabric.md).

## Architecture Comparison Output

When comparing architectures (current/target/alternatives), structure the
output as:

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

Major decisions get an ADR.

## Classification scale

Use qualitative classifications only, unless a formal documented scoring
model exists for the specific engagement:

- Strong
- Acceptable
- Needs improvement
- High risk
- Critical

## Recommendation labels

Every recommendation is one of:

- **Required fix** — the current state is broken, insecure, or
  non-compliant.
- **Best practice** — widely accepted, low-cost to adopt, strongly
  recommended.
- **Good practice** — beneficial, but a reasonable team could choose
  otherwise.
- **Project-specific recommendation** — fits this engagement's
  constraints specifically; do not generalize it as universal.

## Anti-patterns

- Recommending Medallion, Data Vault, Lakehouse or microservices
  architectures by default/mechanically, without justification against
  observed constraints.
- Presenting a preference as a universal best practice.
- Recommending an architecture the client's team cannot realistically
  operate after handover.
- Optimizing one component for theoretical elegance at the expense of the
  wider platform's operability or cost.
