---
name: kenergy-reference
description: "Complete reference tables for Kenergy modes, agents, recipes, and anti-patterns — VDD workflow"
---

# Reference: Kenergy Completion Paths

Kenergy deliberately supports two distinct completion paths.

### Manual/standalone path (interactive)

```text
/think-like-ken  ->  Design document -> design approval
     |
/plan-like-ken   ->  Implementation plan with task goals and verification methods
     |
/build-like-ken  ->  Continuous task lifecycle: implement -> merged three-axis review -> bounded remediation
     |
/verify           ->  Fresh independently interpreted evidence (recommended)
     |
/finish           ->  Finish decision: merge / PR / keep / discard
```

An interactive human may transition directly from `/build-like-ken` to
`/finish`, but `/verify` remains the recommended separate evidence-gathering
step before the finish decision.

### Automated/recipe path (non-interactive)

```text
kenergy-full-development-cycle.yaml
  -> continuous subagent-driven development
  -> holistic kenergy:code-reviewer branch review
  -> required finish approval
```

The automated path does not activate `/verify`. Its holistic branch review is
the automated counterpart to the completion evidence gathered interactively by
`/verify`.

At any point, if a bug needs root-cause investigation: `/debug`.

**Priority order when multiple modes could apply:**
1. Process modes first (`/think-like-ken`, `/debug`) — determine how to approach the task.
2. Implementation modes second (`/plan-like-ken`, `/build-like-ken`) — prepare and execute the plan.
3. Manual completion modes last (`/verify`, `/finish`) — gather final evidence and close out interactive work.

## Reference: Human Checkpoints

There are exactly two human checkpoints in the Kenergy workflow:

1. **Design approval** — after the design document is complete and before planning.
2. **Finish decision** — after accepted task work and completion evidence
   (manual `/verify` when used, or the automated full-cycle branch review),
   choose merge, PR, keep, or discard.

There is no per-task approval, review approval, or continuation prompt after
pre-flight clears. The durable ledger and bounded review lifecycle govern task
progress.

## Reference: Mode Tool

The `mode` tool allows programmatic mode transitions. Use
`mode(operation="set", name="plan-like-ken")` to request a mode change. The
first request will be blocked with a reminder — call again to confirm. This is
useful when an agent needs to request a transition during automated workflows.

## Reference: Modes

| Mode | Shortcut | Purpose | Who Does the Work |
|------|----------|---------|-------------------|
| Think Like Ken | `/think-like-ken` | Design refinement through collaborative dialogue | You (main agent) |
| Plan Like Ken | `/plan-like-ken` | Create a detailed VDD implementation plan | You (main agent) |
| Build Like Ken | `/build-like-ken` | Continuous plan execution through a uniform reviewer lifecycle | Subagents; you orchestrate |
| Debug | `/debug` | Four-phase systematic debugging | You investigate; a subagent fixes |
| Verify | `/verify` | Interactive, evidence-based completion verification for the manual path | You (main agent) |
| Finish | `/finish` | Make the manual finish decision; the automated path uses its required recipe approval | You (main agent) |

## Reference: Agents

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| `kenergy:design-writer` | Writes the approved design document | After the think-like-ken conversation |
| `kenergy:plan-writer` | Creates and parses detailed VDD plans; performs plan-level pre-flight work | During planning and before continuous execution |
| `kenergy:implementer` | Implements one task with static analysis, real verification, exact output, and an atomic commit | Every task and each fresh escalation in `/build-like-ken` |
| `kenergy:reviewer` | Reviews one completed task on three axes: goal/spec compliance, quality, and verification adequacy | Mandatory after each implementation or fix; receives `TASK GOAL` and `REVIEW PACKAGE` |
| `kenergy:code-reviewer` | Holistic review of the complete changeset | Automated full-cycle branch review; optionally during manual `/verify` or `/finish` |

**Delegation rules:**

- **Think-Like-Ken and Plan-Like-Ken:** You own the user conversation. Delegate
  document production to the design-writer or plan-writer after the required
  input is settled.
- **Build-Like-Ken:** You orchestrate; subagents create artifacts and code. Use
  `subagent-driven-development.yaml` for normal continuous execution, or mirror
  its exact lifecycle with direct `delegate()` calls for bootstrap/manual cases.
  You never write implementation code in this mode. Manual completion may use
  `/verify` before `/finish`; the automated full cycle instead runs the holistic
  branch review and required finish approval without activating `/verify`.
- **Merged task review:** Every task uses one `kenergy:reviewer`, not multiple
  per-task review stages. A PASS requires all three axes to pass and no
  load-bearing finding.
- **Bounded remediation:** Review failures in rounds 1-3 resume the original
  implementer session at its original model role. Rounds 4-5 use a fresh
  implementer at the selected escalation role. The sixth cap review either parks
  advisory findings with a reason or blocks on load-bearing findings.
- **Debug:** You investigate Phases 1-3. Delegate Phase 4 fixes to
  `foundation:bug-hunter` or `kenergy:implementer`; write tools remain blocked
  in the root session.
- **Verify and Finish:** You own final evidence and the finish decision. You may
  delegate infrastructure work, but not the decision itself.

**Why the lifecycle preserves focused context:**

- Each task starts with a fresh initial implementer and an explicit task goal.
- Rounds 1-3 preserve the original session only long enough to converge on its
  own review findings.
- Rounds 4-5 add a fresh, stronger implementer only when the original session
  has exhausted its bounded remediation budget.
- A task-scoped review packet prevents plan-wide context from replacing the
  actual task bar.
- The plan-scoped ledger, not conversation history, makes interruption and
  resumption safe.

## Reference: VDD vs TDD

| TDD | VDD |
|-----|-----|
| Write failing test first | Implement, then verify with real execution |
| Red-green-refactor cycle | Static analysis -> run it -> document output |
| Unit tests by default | Unit tests for library code; curl/browser/script for everything else |
| Mock dependencies | Run against real dependencies where the claim requires it |
| Test proves the test works | Execution proves the product works |

**Verification hierarchy (pick the cheapest method that genuinely proves the claim):**

| Level | Method | Use when |
|-------|--------|----------|
| 1 | Static analysis (`ruff`, `ty`, `tsc`, `oxlint`) | Always — zero cost |
| 2 | Run the code directly | Scripts, CLIs, importable modules |
| 3 | `curl` / HTTP call against a live server | API endpoints |
| 4 | Browser via `playwright-cli` | UI changes |
| 5 | Reality Check / DTU | True isolation required |

The reviewer applies a falsifiability check to verification evidence: it must be
possible to name a production break that would make the command fail. Grep and
string presence can prove documentation cleanup; they do not prove runtime
behavior.

## Reference: Durable Execution State

```text
.kenergy/sdd/<plan-slug>/
  ledger.md
  task-briefs/<task>.md
  task-briefs/<task>.base-sha
  review-packages/<task>-round-<n>.md
```

- The ledger identity must match the exact plan path.
- A completed task is trusted only if its recorded commit remains in Git history.
- Task briefs and base SHAs are saved before implementation.
- Each review packet contains the base-to-HEAD diff stat, commit log, and diff.
- Ledger completion occurs only after an accepted review outcome; advisory-only
  cap outcomes include their parked reason.
- Todos may mirror current UI progress but are never resumability state.

## Reference: Recipes

Execute these workflows with the recipes tool:

| Recipe | Purpose | When to Use |
|--------|---------|-------------|
| `kenergy:recipes/subagent-driven-development.yaml` | Plan-scoped ledger setup, one pre-flight scan, and continuous sequential task execution | Normal end-to-end plan execution |
| `kenergy:recipes/single-task-pipeline.yaml` | One uniform implement -> packet review -> bounded remediation -> safe ledger lifecycle | Internal per-task execution and focused recovery |
| `kenergy:recipes/git-worktree-setup.yaml` | Create an isolated workspace | Before implementation when a worktree is needed |
| `kenergy:recipes/finish-branch.yaml` | Complete the development branch | After implementation and final verification |
| `kenergy:recipes/validate-implementation.yaml` | Validate existing work | For externally completed code |
| `kenergy:recipes/executing-plans.yaml` | Compatibility entry point forwarding to continuous subagent-driven execution | Existing callers that still pass `batch_size`; it is accepted and ignored |

## Reference: Anti-Rationalization Table

| Your Excuse | Why It's Wrong | What You Must Do |
|-------------|----------------|------------------|
| "This is a simple/trivial change" | Simple changes still need evidence. | Follow the applicable mode and verification method. |
| "I can do this faster myself" | Root orchestration is not the implementation boundary. | In `/build-like-ken`, delegate implementation and artifacts. |
| "I'll write a unit test to verify it" | A unit test that mocks the product proves the mock, not the product. | Run the real thing: curl, browser, or script as appropriate. |
| "This doesn't need a review" | Every task needs one complete three-axis review. | Dispatch `kenergy:reviewer` with the goal and packet. |
| "One more fix will converge" | Unbounded retries hide a design or evidence problem. | Follow the five-fix/six-review cap; park advisory findings or block load-bearing ones. |
| "I need to debug this myself" | Root-cause work and code changes have different owners. | Use `/debug`; delegate the fix phase. |
| "The plan is obvious" | Exact task goals, interfaces, and verification commands prevent drift. | Use `/plan-like-ken`. |
| "It should work now" | A claim without fresh evidence is not proof. | Run the specified verification and read its output. |
| "No mode applies here" | Mode choice is a deliberate safety and quality boundary. | State the applicable mode and why. |

## Reference: Key Rules

1. **Standing Order First** — Check which mode applies before starting work.
2. **Own Design Conversations, Delegate Artifacts** — You lead design/planning
   conversation; subagents write the resulting documents and implementation.
3. **Continuous Execution** — After a clear pre-flight, process incomplete tasks
   sequentially without per-task pauses.
4. **Ledger Is State** — Validate plan identity, retain task briefs/base SHAs, and
   never use todos or conversation memory to resume work.
5. **One Merged Review** — `kenergy:reviewer` evaluates goal/spec compliance,
   quality, and verification adequacy together for every task.
6. **Bounded Resume and Escalation** — Resume the original session in rounds
   1-3; escalate fresh in rounds 4-5; adjudicate at the sixth review.
7. **Verify with Real Execution** — For non-library code, run the actual thing
   after static analysis and preserve the exact output.
8. **Two Human Checkpoints Only** — Design approval and the finish decision;
   neither task execution nor task review requests a separate checkpoint.

## Philosophy Reference

For core principles, anti-patterns, and VDD discipline, see
`kenergy:context/philosophy.md`.
