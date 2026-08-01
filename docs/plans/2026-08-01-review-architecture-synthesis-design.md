# Kenergy Review-Architecture & Interruption-Reduction Synthesis Design

## Goal

Apply the mechanism-level performance lessons from obra/superpowers v6.0-v6.2, as reported in Prime Radiant's "Superpowers 6" blog post and verified against the actual upstream skill files, to kenergy's review architecture and execution model. Reframe those lessons around Verification-Driven Development (VDD) rather than Test-Driven Development (TDD), while fixing several pre-existing bugs discovered during the audit.

The explicit design principle threaded through every decision is:

> Interrupt the human only at genuine forks; human attention is the costliest resource.

## Background

Prime Radiant's autoresearch loop found that Superpowers' speed and cost wins came from eliminating redundant context reconstruction, not from cutting rigor:

1. Precomputing review diff and metadata packets instead of letting reviewers re-derive them through git commands produced an approximately 10% win.
2. Merging the spec-compliance and code-quality reviewers into one dispatch with two verdicts produced an approximately 15% win because the reviewers shared roughly 90% of their context.
3. A terse verdict contract reduced reviewer output by 41% without changing verdicts.
4. Trimming orchestrator narration was a pure win, reducing it by 54% with zero variance, but capping orchestrator thinking backfired: turns rose from 92 to 138. Thinking buys efficiency; narration does not.
5. Plan word-budget caps gutted verification content by 62% even when code was nominally exempt. Interfaces, verification, and structure carry a plan's review-quality signal, not fully written code bodies.
6. Reviewers given only a diff, without a task brief, silently redefined "spec" as the global constraints and false-passed the work. Zero of five reviewers caught a missing brief.

Kenergy's own bundle had a matching bug: `single-task-pipeline.yaml` only ran the full two-stage review for "complex" tasks, ran a single weaker combined review for "standard" tasks, and ran no review for "trivial" tasks. This was an inconsistency, not an intentional design.

The current obra/superpowers `subagent-driven-development` skill was cross-checked directly. Obra has no complexity tiers. Every task, without exception, follows this lifecycle:

```text
implementer -> merged task-reviewer -> resume-based fix loop if needed -> next task
```

Cost control lives entirely in per-dispatch model judgment:

- Mechanical or isolated task: cheap model.
- Integration or judgment task: standard model.
- Architecture or design task: most capable model.
- Reviews scale the same way according to diff size and risk.
- Fix-loop escalation goes one tier above the original selection.

Obra also runs fully continuous execution with zero pauses between tasks: "Do not pause to check in with your human partner between tasks." Prompts such as "Should I continue?" waste the human's time. Narration is capped to one line, and a ledger file, not todos, provides resumability because conversation memory does not survive compaction. Re-dispatching completed work was "the single most expensive failure observed."

## Approach

Adopt a full synthesis, not a clone. Apply every mechanism-level lesson above while preserving kenergy's VDD and goal-driven framing.

Where obra's shipped skill and the blog's aspirational or experimental findings diverge, kenergy defers rather than copies blindly. In particular, the blog's claim that code bodies are marginal comes from an unshipped internal experiment log. Prime Radiant explicitly stated that further validation is still owed before it ships as skill text. That proposal remains an explicit open and deferred decision in this design rather than an adopted change.

## Architecture

The resulting development path has two human checkpoints: one design approval before planning and one pre-merge, PR, or discard decision in `/finish`. Planning becomes a direct artifact-generation step after design approval. Execution performs one pre-flight conflict scan, then runs continuously through a uniform per-task lifecycle with explicit model selection, precomputed review context, a merged three-axis review, bounded resume-and-escalate fixes, and plan-scoped durable state.

## Components

### 1. Merged Reviewer Agent

Retire `kenergy:verifier` and `kenergy:quality-reviewer` as separate task-level agents. Create one new agent, `kenergy:reviewer`, dispatched once per task and returning three verdicts in a single pass:

1. **Spec/Goal compliance:** The implementation matches what was asked, with nothing more and nothing less.
2. **Quality:** The implementation demonstrates clean code, appropriate error handling, maintainability, and sound design.
3. **Verification adequacy:** Kenergy's distinctive third axis, not present in obra's two-verdict reviewer. The reviewer determines whether the real-execution proof exercised the claimed behavior or whether a non-verification is masquerading as proof.

Verification adequacy includes a falsifiability discipline adapted from obra's `writing-good-tests.md` but reframed for VDD real-execution checks rather than unit tests. Before accepting a verification method, the reviewer must name the production change that would make it fail. It must reject:

- The **string-presence trap**: grepping for text is not verification of behavior.
- The **change-detector trap**: an assertion that remains true regardless of correctness, such as asserting a constant's literal value.

`kenergy:code-reviewer`, the existing holistic whole-branch and session-scope reviewer used in `/finish`, is out of scope. It serves a different scope and remains untouched.

The merged reviewer must always receive the task's specific goal or spec text alongside the diff. Reviewing a diff-only input is explicitly forbidden. If the dispatch omits the goal text, the reviewer must stop and request it rather than silently substituting the plan's Global Constraints as the review bar. This directly guards against the failure mode in which zero of five reviewers caught a missing brief.

The verdict output must be a compact templated block rather than free-form prose. Each axis returns `PASS`/`FAIL` or `Approved`/`Needs fixes`, plus a short evidence pointer such as `file:line` or the command run. This mirrors the finding that a terse contract reduced output by 41% while preserving verdicts.

### 2. Precomputed Review Packet

Before dispatching `kenergy:reviewer`, or the implementer for a fix round, add a `bash` step to the recipe that generates a diff, log, and stat review packet. Use `git diff`, `git log`, and `git diff --stat` scoped to the task's commit range, then pass the result as a `{{review_package}}` template variable in the dispatch prompt.

This is kenergy's native equivalent of obra's `review-package` and `task-brief` scripts. It prevents each agent from spending context and tool calls re-deriving the same git state.

### 3. Fix Loop: Resume, Escalate, Adjudicate

Use a bounded five-round fix loop:

- **Rounds 1-3:** Resume the original implementer through `delegate(session_id=..., ...)`, not a fresh dispatch. Its context remains intact, the operation is cheaper, and the implementer knows its prior choices.
- **Rounds 4-5:** Dispatch a fresh implementer on an escalated `model_role`, at least one tier above the role used previously. A loop that survives three resumes usually means the original implementer cannot see its own problem.
- **At the round-five cap:** The orchestrator, not a subagent, adjudicates every remaining open finding. Park non-load-bearing or contestable findings in the ledger with a recorded reason. For load-bearing findings, stop and report `BLOCKED` to the human. This is one of the few legitimate interruption points because it is a genuine fork, not a check-in.

This replaces kenergy's checkpoint bug, where a task could be marked complete in `.kenergy-checkpoint.json` after an exhausted but unresolved review loop. The previous write condition checked only `impl_status`, never the review outcome.

### 4. Plan-Scoped State Ledger

Replace the global `.kenergy-checkpoint.json` and `.kenergy-project-brief.txt` files with a plan-scoped directory:

```text
.kenergy/sdd/<plan-slug>/
```

Derive `<plan-slug>` from the plan filename, mirroring obra's `.superpowers/sdd/<plan-basename>/`. The directory contains the ledger, task briefs, and review packages for that plan only.

This fixes a cross-plan contamination bug: a second plan running in the same repository could previously read the first plan's checkpoint or brief as its own progress.

The ledger's first line records its own plan file identity. A controller resuming after context loss checks that identity before trusting any progress data and treats `git log` as more trustworthy than its own recollection.

### 5. Continuous Execution Without Tiering

Remove all complexity-tier-based review-skipping logic from `single-task-pipeline.yaml`, including the current trivial, standard, and complex distinction where trivial tasks receive no review and standard tasks receive a weaker single-reviewer path.

Every task, without exception, receives the same lifecycle:

```text
implementer -> kenergy:reviewer -> fix loop if needed -> next task
```

`subagent-driven-development.yaml` and `single-task-pipeline.yaml` stop pausing between tasks or in batches. Narration is capped to at most one short status line between steps. There are no "Should I continue?" prompts. The only legitimate stop conditions during a build are:

- A `BLOCKED` status that the fix loop cannot resolve.
- All tasks complete.

Before dispatching Task 1 of any plan, add one pre-flight step that scans the whole plan for internal conflicts: tasks that contradict one another, tasks that conflict with the plan's Global Constraints, or plan mandates that the review rubric would classify as defects. Present any findings as one batched question before execution begins. This is a genuine and worthwhile fork, unlike the removed per-task and per-batch check-ins.

### 6. Judgment-Based Model Selection

Replace the fixed trivial, standard, and complex tier system's role in selecting review depth with per-dispatch judgment about model selection, mapped to Amplifier's `model_role` system:

- Mechanical or isolated tasks with a clear spec and one or two files: `fast` or `coding`.
- Integration, multi-file, or judgment tasks: `coding`.
- Architecture- or design-sensitive tasks: `reasoning`.

Review dispatches scale in the same way according to the diff's size and risk:

- Small mechanical diff: cheaper model tier.
- Larger or riskier diff: `reasoning` or `critique`.

Fix-loop escalation in rounds 4-5 always moves at least one tier above the model used previously.

Every `delegate()` call in these recipes must explicitly set `model_role`. No dispatch may rely on an inherited or unnamed default because an unnamed model silently inherits the session's, often most expensive, model.

### 7. Plan Structure Additions

Update `kenergy:plan-writer` and `writing-plans.yaml` with two required blocks adapted from obra's shipped, not experimental, `writing-plans` skill:

1. **Plan-level Global Constraints:** Project-wide rules such as version floors, dependency limits, naming requirements, and exact values. Copy them verbatim so every task implicitly inherits them.
2. **Per-task Interfaces:** Explicit `Consumes` and `Produces` sub-fields. `Consumes` records exact signatures used from earlier tasks. `Produces` records what later tasks may rely on. This is required because an isolated task's implementer sees only its own task text.

The currently mandated complete, copy-pasteable code per task remains unchanged. Whether to de-emphasize that requirement in favor of Interfaces and Verification as the only mandatory fields is explicitly deferred. Prime Radiant has not shipped that idea and described it as unproven: "the N=5 gate battery is still owed before any of it ships as skill text." Do not remove or weaken the full-code requirement in this pass. Revisit it only after this design has been built and used.

### 8. Interruption-Reduction Mechanism

This mechanism changes kenergy's own process, not only the subject under review.

Rewrite the `think-like-ken` mode's hard gate. Replace the fixed rule to present the design in 200-300-word sections with a checkpoint after every section with a genuine-forks-only principle:

- When a design decision has a defensible engineering answer backed by evidence, precedent, or research, the orchestrator decides it directly and includes the choice with brief reasoning in a consolidated review. It does not stop and ask.
- The orchestrator may optionally sanity-check its judgment inline through a persona lens such as `restless-old-brian`, `cranky-old-sam`, or `crusty-old-engineer`, as appropriate. These are inline skills the orchestrator can embody without a separate dispatch.
- Only genuine personal-preference questions or facts only the user knows receive a direct question.
- Questions are batched by topic, never split into one micro-decision per message.
- When zero non-AI-decidable choices remain, skip directly to one final TL;DR-style review instead of section-by-section gating.

Collapse kenergy's overall checkpoint model from four moments—after design, after plan, between execution batches, and before merge or PR—to exactly two:

1. Design approval, once.
2. The pre-merge, PR, or discard decision in `/finish`, once. This remains because it gates an irreversible action.

Change `/plan-like-ken` from an interactive conversation about task breakdown, dependencies, and granularity into a direct action. It reads the approved design, dispatches `kenergy:plan-writer` with full context to produce the plan according to the updated `writing-plans` template, saves the plan, and hands directly to execution. There is no "Does this plan look right?" gate and no task-by-task negotiation with the human.

This principle is self-referential: it was applied live during the design conversation once no further human-only decisions remained.

### 9. Bundled Bug Fixes

These are straightforward corrections with no open design decisions.

#### `context/philosophy.md`: Restore VDD Consistency

The file currently says "Test-Driven Development is Non-Negotiable" and instructs the agent to delete code written before tests. This directly contradicts VDD, which every other kenergy file—README, `kenergy-reference`, `plan-writer`, and `plan-like-ken`—correctly uses. Because `context/philosophy.md` loads on every turn through `behaviors/kenergy.yaml`, rewrite this section and the related thought and rationalization table entries to be VDD-consistent with the rest of the bundle. For example, replace entries such as "TDD will slow me down" and "TDD is faster than debugging" with VDD-consistent guidance.

#### `context/instructions.md`: Correct Kenergy-Native Names

Fix naming drift. The file currently references `superpowers-full-development-cycle`, `superpowers:recipes/subagent-driven-development.yaml`, and `load_skill("superpowers-reference")`, none of which exist in kenergy. Update all such references to the correct kenergy-native names, including `kenergy-full-development-cycle.yaml` and `kenergy-reference`.

#### Remove Dangling Visual-Companion References

`README.md` and `agents/design-writer.md` currently reference `context/visual-companion-guide.md`, a browser-based visual brainstorming companion, even though no server or script implementation exists anywhere in the repository and the feature is explicitly not wanted. Delete `context/visual-companion-guide.md` and remove every reference to it from `README.md` and `agents/design-writer.md`.

#### `recipes/finish-branch.yaml`: Fix Worktree Path Staleness

Fix the worktree-path-staleness bug in `recipes/finish-branch.yaml`, and in `modes/finish.md` if it has the same pattern. Paths are currently detected once early in the recipe, then later steps change directories, check out branches, or remove directories before reusing that stale value.

Apply a capture-on-entry, consume-after-`cd` pattern: capture `worktree_path`, and any other directory-sensitive values, into variables before any step changes the working directory. All later cleanup steps consume those captured values rather than recomputing them or assuming the original directory is still valid.

## Data Flow

1. The human approves the design once.
2. `/plan-like-ken` sends the approved design directly to `kenergy:plan-writer`. The resulting plan includes Global Constraints, per-task Interfaces with `Consumes` and `Produces`, verification requirements, and the unchanged complete-code-per-task content.
3. Before Task 1, the controller scans the complete plan once for conflicts. Any conflicts are presented as one batched human question. If there are none, execution continues without interruption.
4. The controller creates or resumes `.kenergy/sdd/<plan-slug>/`, verifies that the ledger's first-line plan identity matches the active plan, and reconciles progress against `git log`.
5. For each task, the controller selects and explicitly names an appropriate `model_role`, then dispatches the implementer with that task's brief.
6. A recipe `bash` step generates the task-scoped diff, log, and stat review packet and stores or passes it as `{{review_package}}`.
7. `kenergy:reviewer` receives both the task's specific goal text and the review packet, then returns compact verdicts for Spec/Goal compliance, Quality, and Verification adequacy.
8. If all three axes pass, the ledger records completion and execution moves immediately to the next task.
9. If an axis fails, rounds 1-3 resume the original implementer. Rounds 4-5 use a fresh implementer on an escalated model. Each fix round receives a precomputed review packet.
10. At the cap, the orchestrator records parked non-load-bearing findings or stops with `BLOCKED` for unresolved load-bearing findings.
11. After all tasks complete, `/finish` retains the separate holistic `kenergy:code-reviewer` scope and presents the one final human decision: merge, open a PR, or discard the work.

## Error Handling and Known Risk

### Error Handling

- **Missing task goal:** `kenergy:reviewer` stops and requests the specific goal or spec instead of reviewing a diff-only input.
- **Unresolved review finding:** At round five, the orchestrator records a reason when parking a non-load-bearing or contestable finding. It stops with `BLOCKED` when a load-bearing finding remains unresolved.
- **Stale or cross-plan state:** The controller rejects ledger progress whose first-line plan identity does not match the active plan. It uses `git log` as the more trustworthy record when memory and repository history disagree.
- **Directory-sensitive cleanup:** Finish and cleanup flows capture worktree and directory-sensitive values before changing directories and consume the captured values afterward.

### Known Risk

This design has no eval suite behind it, unlike Prime Radiant's Superpowers 6 work, where a 25-experiment autoresearch campaign validated the merge before shipping. The three-verdict merged reviewer format is therefore provisional rather than proven at kenergy's scale.

Watch for this failure smell: a reviewer axis that previously caught an issue starts waving it through because it was folded into a larger combined dispatch. If observed, split the affected axis back into a separate reviewer dispatch. This reversal is explicitly permitted and is not considered a design failure.

## Explicitly Out of Scope

- `kenergy:code-reviewer`, the holistic whole-branch reviewer, remains untouched because its scope differs from the per-task merged reviewer.
- The full-code-per-task requirement in `plan-writer` is not removed or weakened. The idea is explicitly deferred.
- TDD-specific content, terminology, or workflow—such as red/green/refactor framing or "delete code written before tests"—is excluded throughout. VDD framing is preserved everywhere.
- Obra's browser-based visual brainstorming companion is excluded. This design removes kenergy's dangling references to it; it does not add or port any part of the feature.

## Verification Approach

Because this design changes text and behavior-shaping bundle files—agents, modes, recipes, context, and skills—rather than application code, verification requires:

1. Validate every changed YAML recipe for syntactic correctness before considering the task complete.
2. After renames and retirements, grep cross-file references across the whole bundle to confirm that no dangling references remain to `kenergy:verifier` or `kenergy:quality-reviewer`.
3. Read the merged `kenergy:reviewer` agent and the rewritten recipes end to end after implementation to confirm internal consistency.

There is no existing eval suite to run automatically. That absence is retained as the explicit known risk above.

## Open Questions

- Whether to eventually de-emphasize full-code-per-task in `plan-writer` in favor of Interfaces and Verification alone. This remains deferred as described in the plan-structure decision.
- Whether the genuine-forks-only interruption principle should also be written formally into `plan-like-ken.md` and `build-like-ken.md`, or whether removing their explicit approval-gate language is sufficient. This is an implementation-level detail to resolve during planning.
