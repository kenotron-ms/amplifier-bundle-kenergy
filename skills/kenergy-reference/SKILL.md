---
name: kenergy-reference
description: "Complete reference tables for Kenergy modes, agents, recipes, and anti-patterns — VDD workflow"
---

## Reference: The Kenergy Pipeline

The full development workflow:

```
/think-like-ken  ->  Design document (user validates each section)
     |
/plan-like-ken  ->  Implementation plan (VDD tasks with verification methods)
     |
/build-like-ken  ->  Subagent-driven development (implement -> verifier -> quality-reviewer per task)
     |
/verify  ->  Fresh evidence that everything works
     |
/finish  ->  Merge / PR / Keep / Discard
```

At any point, if bugs arise: `/debug` (4-phase systematic debugging).

**Priority order when multiple modes could apply:**
1. Process modes first (`/think-like-ken`, `/debug`) -- determine HOW to approach the task
2. Implementation modes second (`/plan-like-ken`, `/build-like-ken`) -- guide execution
3. Completion modes last (`/verify`, `/finish`) -- close out work

## Reference: Mode Tool

The `mode` tool allows programmatic mode transitions. Use `mode(operation="set", name="plan-like-ken")` to request a mode change. The first request will be blocked with a reminder — call again to confirm. This is useful when agents need to request transitions during automated workflows.

## Reference: Modes

| Mode | Shortcut | Purpose | Who Does The Work |
|------|----------|---------|-------------------|
| Think Like Ken | `/think-like-ken` | Design refinement through collaborative dialogue | You (main agent) |
| Plan Like Ken | `/plan-like-ken` | Create detailed VDD implementation plan | You (main agent) |
| Build Like Ken | `/build-like-ken` | Subagent-driven development with three-agent pipeline | Subagents (you orchestrate) |
| Debug | `/debug` | 4-phase systematic debugging | You (main agent) |
| Verify | `/verify` | Evidence-based completion verification | You (main agent) |
| Finish | `/finish` | Complete branch -- verify, merge/PR/keep/discard | You (main agent) |

## Reference: Agents

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| `kenergy:design-writer` | Design document writer | MANDATORY — after think-like-ken conversation, delegate document creation |
| `kenergy:plan-writer` | Detailed VDD plan creation | MANDATORY — after plan-like-ken conversation, delegate plan creation |
| `kenergy:implementer` | Implements tasks with VDD (real verification, documented output) | MANDATORY -- every task in `/build-like-ken` |
| `kenergy:verifier` | Verifies implementation against spec AND confirms real execution | MANDATORY -- every task in `/build-like-ken`, after implementer |
| `kenergy:quality-reviewer` | Reviews code quality and best practices | MANDATORY -- every task in `/build-like-ken`, after verifier |
| `kenergy:code-reviewer` | Holistic pre-PR review of complete changeset | Pre-merge, or in `/verify` and `/finish` modes |

**Delegation rules:**
- **Think-Like-Ken and Plan-Like-Ken: YOU own the conversation.** When it's time to write the artifact, delegate to the design-writer/plan-writer agent. The back-and-forth with the user is what makes these phases effective. The agent writes the document after you've validated everything.
- **Build-Like-Ken: YOU delegate everything.** You are the orchestrator. Every task goes through the three-agent pipeline (implementer -> verifier -> quality-reviewer). You never write code in this mode.
- **Debug: YOU investigate (Phases 1-3). Fixes MUST be delegated** to `foundation:bug-hunter` or `kenergy:implementer` (Phase 4). You own the investigation process but cannot write fixes directly — write tools are blocked in debug mode.
- **Verify, Finish: YOU do the work directly.** You may delegate infrastructure (shadow environments, test runners) in verify mode, but you own verification and completion.

**Why fresh subagents per task:**
- **Clean context** — No pollution from previous work
- **Focused attention** — Single task, single responsibility
- **Quality gates** — Review checkpoints catch issues early
- **Parallel safety** — Subagents don't interfere with each other

## Reference: VDD vs TDD

The core difference:

| TDD | VDD |
|-----|-----|
| Write failing test first | Implement, then verify with real execution |
| Red-green-refactor cycle | Static analysis → run it → document output |
| Unit tests by default | Unit tests for library code; curl/browser/script for everything else |
| Mock dependencies | Run against real dependencies |
| Test proves the test works | Execution proves the product works |

**Verification hierarchy (pick the cheapest that genuinely proves the claim):**

| Level | Method | Use when |
|-------|--------|----------|
| 1 | Static analysis (`ruff`, `ty`, `tsc`, `oxlint`) | Always — zero cost |
| 2 | Run the code directly | Scripts, CLIs, importable modules |
| 3 | `curl` / HTTP call against live server | API endpoints |
| 4 | Browser via `playwright-cli` | UI changes |
| 5 | Reality Check / DTU | True isolation required |

## Reference: Recipes

Execute these workflows using the recipes tool:

| Recipe | Purpose | When to Use |
|--------|---------|-------------|
| `kenergy:recipes/subagent-driven-development.yaml` | Fresh agent per task + reviews | For same-session execution with foreach |
| `kenergy:recipes/git-worktree-setup.yaml` | Create isolated workspace | Before implementation |
| `kenergy:recipes/finish-branch.yaml` | Complete development branch | After implementation done |
| `kenergy:recipes/validate-implementation.yaml` | Validate existing work | For externally-completed code |
| `kenergy:recipes/executing-plans.yaml` | Execute plans in batches | Batch execution with checkpoints |

## Reference: Anti-Rationalization Table

| Your Excuse | Why It's Wrong | What You MUST Do |
|-------------|---------------|------------------|
| "This is a simple/trivial change" | Simple changes cause production outages. They still need verification. | Follow the appropriate mode's process. |
| "I can do this faster myself" | Speed is not the goal. Verified, reviewed, quality code is the goal. | In `/build-like-ken`: delegate. In `/think-like-ken`: follow the process. |
| "The user seems to want a quick response" | The user chose the Kenergy methodology. They want quality. | Give them the full process for the active mode. |
| "I'll write a unit test to verify it" | A unit test that mocks everything proves the mock works, not the product. | Run the real thing: curl, playwright-cli, or execute the script. |
| "This doesn't need a review" | Everything in `/build-like-ken` needs review. Both reviews. | Delegate to verifier, then quality-reviewer. |
| "I need to debug this myself" | Use `/debug` mode and follow the 4-phase framework. | Activate debug mode. Phase 1 before any fixes. |
| "I already know what to build" | Then the design questions will be fast. That's not a reason to skip design. | Follow `/think-like-ken` process. Assumptions kill designs. |
| "The plan is obvious" | If it's obvious, writing exact verification commands will be fast. Vague plans produce bad implementations. | Follow `/plan-like-ken` process. Every task needs a verification method. |
| "Should work now" | Run the verification. "Should" is not evidence. | Use `/verify`. Run the command. Read the output. THEN claim. |
| "Just one more fix attempt" | 3+ failed fixes = architectural problem. Stop fixing symptoms. | Question the architecture. Discuss with user. |
| "No mode applies here" | If there's even a 1% chance, suggest it. Let the user decide. | State which mode might apply and why. |

## Reference: Key Rules

1. **Standing Order First** -- Check which mode applies before starting any work. Suggest it even if you're only 1% sure.
2. **Own Design Conversations, Delegate Artifacts** -- You design and plan through conversation. When it's time to produce the document, delegate to the design-writer/plan-writer agent.
3. **Delegate in Execution** -- Every task in `/build-like-ken` goes through the three-agent pipeline. No exceptions.
4. **Verify with Real Execution** -- For non-library code, run the actual thing. Static analysis first, then execution.
5. **Verify Everything** -- Evidence before claims, fresh commands before assertions.
6. **Systematic Debugging** -- Root cause before fixes, 4 phases in order.
7. **Human Checkpoints** -- Validate designs section by section, approval gates at critical points.
8. **Two-Stage Review** -- Spec/verification compliance first, then code quality -- for EVERY task in execution.

## Philosophy Reference

For deep understanding of the principles, see:
- `kenergy:context/philosophy.md` -- Core principles, anti-patterns, and the two-stage review pattern
