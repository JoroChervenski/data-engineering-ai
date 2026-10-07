# `/prepare-pr`

## Purpose

Build a PR description from the actual diff, test results and review
findings.

## Expected Inputs

- The actual diff/branch.
- The original ticket/request and implementation plan, if available.
- Test results.
- Review findings from a completed [`/review-pr`](review-pr.md) (and
  [`/review-data-model`](review-data-model.md), if applicable).

## Skills / Roles Invoked

- [`pull-request`](../skills/pull-request/SKILL.md).

## Ordered Execution Steps

1. Confirm implementation and review have both actually happened; do not
   proceed if review has not yet run.
2. Run the [`pull-request`](../skills/pull-request/SKILL.md) procedure
   against the real diff, test results and review findings.
3. Carry forward any open Critical/High review finding into the Risks
   section — never omit it.
4. Return the PR description using
   [`templates/PR.md`](../templates/PR.md).

## Expected Output

Branch name, PR title, summary, business reason, technical changes,
architecture impact, data impact, testing, deployment, rollback, risks,
reviewer checklist — per `templates/PR.md`.

## Safety Constraints

- Does not create, push, or merge anything — it only produces the
  description text. Creating/pushing a branch or PR is a later-phase,
  higher-privilege capability (see the implementation spec's Phase 5).
- Never contradicts the actual diff; never claims a test ran if it did
  not.
