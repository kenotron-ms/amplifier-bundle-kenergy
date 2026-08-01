# Review Architecture Synthesis Implementation Plan

> **For execution:** Use `/build-like-ken` mode.

**Goal:** Replace Kenergy's tiered two-reviewer execution path with one goal-aware, three-axis reviewer; continuous plan execution; plan-scoped durable state; and two genuine human checkpoints.

**Architecture:** The execution controller derives a plan-specific state directory, performs one pre-flight conflict scan, then runs every incomplete task through the same implement-review-fix-ledger lifecycle. Review context is precomputed from the task's commit range, every agent dispatch names a `model_role`, early fixes resume the original implementer session, late fixes use a fresh escalated model, and unresolved review findings can never be checkpointed as complete. Planning becomes direct artifact generation and execution after the single design approval.

**Tech Stack:** Amplifier bundle Markdown/frontmatter, Amplifier recipe YAML, shell and Python snippets embedded in recipe `bash` steps, Git commit ranges, and the existing `delegate`/`recipes` mechanisms.

**Verification approach:** For every changed recipe, parse the exact YAML file with `yaml.safe_load`. For Markdown/frontmatter and deletions, use full-file read-backs and exact cross-reference greps. The final retirement sweep must find no live references to the two retired agent IDs outside the immutable design and implementation-plan artifacts.

**Design Source:** `docs/plans/2026-08-01-review-architecture-synthesis-design.md`

## Global Constraints

- Interrupt the human only at genuine forks; human attention is the costliest resource.
- The normal development path has exactly two unconditional human checkpoints: one design approval and one `/finish` decision to merge, open a PR, keep, or discard. A pre-flight plan-conflict question appears only when the plan actually contradicts itself or its Global Constraints.
- Every task uses the same lifecycle: implementer -> `kenergy:reviewer` -> bounded fix loop if needed -> ledger completion. No task may skip review because it is small.
- The reviewer always receives the task's specific goal/spec text and a precomputed diff/log/stat packet. Diff-only review must be refused.
- The reviewer returns terse verdicts for Spec/Goal, Quality, and Verification Adequacy. Verification Adequacy must apply name-the-break falsifiability and reject string-presence and change-detector traps.
- State lives only under `.kenergy/sdd/<plan-slug>/`; the ledger's first line is `# Plan: <absolute-plan-path>`. Never recreate `.kenergy-checkpoint.json` or `.kenergy-project-brief.txt`.
- `git log` is authoritative when remembered/ledger state and repository history disagree.
- Every agent step in `single-task-pipeline.yaml` and `subagent-driven-development.yaml` explicitly names `model_role`; no inherited model defaults.
- Model judgment mapping is: mechanical/isolated -> `fast` or `coding`; integration/multi-file -> `coding`; architecture/design-sensitive -> `reasoning`; review roles scale by diff risk; escalation ladder is `fast -> coding -> reasoning -> critical-ops`.
- Recipe agent steps do not natively expose a child session ID to later steps or resume a prior child. Do not fake resume with another ordinary agent step. The initial implementer must report its injected full session ID, and rounds 1-3 must use a controller step whose only action is an explicit `delegate(session_id=..., instruction=..., model_role=...)` call. Missing/unresumable IDs are `BLOCKED`, not a reason to silently fresh-dispatch.
- The complete, copy-pasteable implementation requirement in plan-writing guidance remains exactly in force. Do not weaken it while adding Global Constraints and Interfaces.
- `kenergy:code-reviewer` remains the holistic whole-branch reviewer. Only stale wording that names the retired task reviewers may change.
- Do not add or port a visual companion.
- All file reads/writes inside embedded Python use `encoding="utf-8"`; path inputs use `Path(...).expanduser()` before resolution.

---

## Phase 1: Reviewer and Continuous Execution Core

### Task 1: Create and register the merged three-axis reviewer

**Files:**
- Create: `agents/reviewer.md`
- Modify: `behaviors/kenergy.yaml:6-14`

**Interfaces:**
- Consumes: a dispatch containing `TASK GOAL` plus `REVIEW PACKAGE`; actual repository files named by the packet.
- Produces: a terse `REVIEW: PASS|FAIL|REFUSED` block with one verdict/evidence pointer per axis and severity-tagged findings.

**Implementation**

Create `agents/reviewer.md` by merging the useful checks from `agents/verifier.md` and `agents/quality-reviewer.md`. Use this complete contract:

````markdown
---
meta:
  name: reviewer
  description: |
    Use after an implementer completes a task to review goal compliance, quality,
    and whether the claimed verification could actually detect broken behavior.

    The task's specific goal/spec text is mandatory. Refuse diff-only reviews.

  model_role: [critique, reasoning, general]
tools:
  - module: tool-filesystem
    source: git+https://github.com/microsoft/amplifier-module-tool-filesystem@main
  - module: tool-bash
    source: git+https://github.com/microsoft/amplifier-module-tool-bash@main
  - module: tool-search
    source: git+https://github.com/microsoft/amplifier-module-tool-search@main
  - module: tool-python-check
    source: git+https://github.com/microsoft/amplifier-bundle-python-dev@main#subdirectory=modules/tool-python-check
---

# Task Reviewer

Review one completed task on three independent axes. You are a task-scoped
reviewer, not the holistic whole-branch `kenergy:code-reviewer`.

## Required Input Guard

Your dispatch MUST contain both:

1. `TASK GOAL` — the task's specific description, specification, acceptance
   criteria, and interfaces.
2. `REVIEW PACKAGE` — precomputed task-scoped `git diff`, `git log`, and
   `git diff --stat` output.

If `TASK GOAL` is missing, empty, or replaced only by plan-wide constraints,
stop. Do not inspect the diff and do not invent a review bar. Return exactly:

```text
REVIEW: REFUSED
MISSING: TASK_GOAL
ACTION: Re-dispatch with the task's specific goal/spec text.
```

If `REVIEW PACKAGE` is missing or empty, stop. Do not reconstruct it. Return
exactly:

```text
REVIEW: REFUSED
MISSING: REVIEW_PACKAGE
ACTION: Re-dispatch with the precomputed diff/log/stat review package.
```

Never run Git merely to reconstruct the packet. The controller owns that work.
You may read named files and run an exact static-analysis or verification command
when independent confirmation is needed.

## Axis 1: Spec/Goal Compliance

Check the implementation against the supplied task goal:
- every requested behavior exists;
- behavior matches the goal and acceptance criteria;
- no unrequested behavior or speculative scope was added;
- declared Consumes/Produces interfaces remain exact.

## Axis 2: Quality

Check correctness, clarity, error handling, maintainability, security where
relevant, minimal design, and absence of dead or speculative code. Style-only
preferences are advisory and never load-bearing.

## Axis 3: Verification Adequacy

Verification is evidence only when it is falsifiable.

Before accepting a verification command, answer **name the break**: name one
specific production change that would make this check fail. If no such change
can be named, the check does not verify the claimed behavior.

Reject these traps:
- **String-presence trap:** finding expected text proves text exists, not that the
  behavior works. Grep is valid for reference cleanup, not runtime behavior.
- **Change-detector trap:** an assertion remains true regardless of correctness,
  such as checking a literal constant against itself or only confirming a file
  changed.

Judge the evidence at the proper VDD level: static analysis as the floor; direct
execution for scripts/CLIs; live HTTP for endpoints; browser observation for UI;
unit tests for library behavior; isolated reality checks when environment
fidelity is part of the claim. Require the actual command and observed output.

## Finding Severity

- `[LOAD-BEARING]`: required behavior is missing/wrong, safety or correctness is
  compromised, or the claimed behavior has no falsifiable real-execution proof.
- `[ADVISORY]`: contestable or non-essential improvement that may be parked with
  a reason after the bounded fix loop.

## Output Contract

Return only this compact block; no essay, strengths section, or repeated packet:

```text
REVIEW: PASS | FAIL
SPEC_GOAL: PASS | FAIL — <file:line or goal clause>
QUALITY: PASS | FAIL — <file:line or command>
VERIFICATION: PASS | FAIL — <command/evidence pointer; include named break>
FINDINGS:
- [LOAD-BEARING|ADVISORY] <file:line or evidence pointer> — <specific issue>
REQUIRED_FIXES:
- <minimal action, or NONE>
```

`REVIEW: PASS` is allowed only when all three axes pass and there are no
load-bearing findings.

## Scope Boundary

Do not implement fixes. Do not push, merge, open PRs, deploy, or redefine the
workflow. Return the verdict to the controller.

@foundation:context/LANGUAGE_PHILOSOPHY.md
@foundation:context/shared/common-agent-base.md
@kenergy:context/philosophy.md
````

Add `kenergy:reviewer` to `behaviors/kenergy.yaml` now, but retain the old two registrations temporarily until Task 15 so intermediate commits remain loadable while their call sites are migrated.

**Verification**

```bash
cat agents/reviewer.md
grep -n "name: reviewer\|Required Input Guard\|name the break\|String-presence trap\|Change-detector trap\|SPEC_GOAL:\|VERIFICATION:" agents/reviewer.md
grep -n "kenergy:reviewer" behaviors/kenergy.yaml
```

Expected: the full file reads consistently; every required contract anchor appears; the new agent is registered exactly once.

**Commit**

```bash
git add agents/reviewer.md behaviors/kenergy.yaml
git commit -m "feat: add merged three-axis task reviewer" \
  -m "🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)" \
  -m "Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
```

### Task 2: Add plan-scoped state and task-brief plumbing

**Files:**
- Modify: `recipes/subagent-driven-development.yaml:36-168`
- Modify: `recipes/single-task-pipeline.yaml:8-60`

**Interfaces:**
- Consumes: `plan_path`, parsed task objects, current Git history.
- Produces: `plan_identity`, `plan_slug`, `state_dir`, `ledger_path`, task brief files, and the task's pre-implementation base SHA.

**Implementation**

In the parent recipe, expand each parsed task with `goal`, `interfaces`, `implementation_model_role`, `review_model_role`, and `escalated_model_role`. Require roles to be selected by judgment using the Global Constraints mapping, not by file-count/word-count tiers.

Insert an `initialize-plan-state` bash step after plan validation. Use this exact state initialization logic:

```yaml
- id: "initialize-plan-state"
  type: "bash"
  timeout: 30
  command: |
    set -eu
    python3 - <<'PYEOF'
    import json
    import re
    from pathlib import Path

    raw = Path("{{plan_path}}").expanduser()
    plan = raw.resolve()
    if not plan.is_file():
        raise SystemExit(f"BLOCKED: plan not found: {plan}")

    slug = re.sub(r"[^a-z0-9]+", "-", plan.stem.lower()).strip("-")
    if not slug:
        raise SystemExit("BLOCKED: plan filename produced an empty slug")

    state_dir = Path(".kenergy") / "sdd" / slug
    briefs = state_dir / "task-briefs"
    packets = state_dir / "review-packages"
    briefs.mkdir(parents=True, exist_ok=True)
    packets.mkdir(parents=True, exist_ok=True)

    ledger = state_dir / "ledger.md"
    identity = str(plan)
    first_line = f"# Plan: {identity}"
    if ledger.exists():
        actual = ledger.read_text(encoding="utf-8").splitlines()
        if not actual or actual[0] != first_line:
            raise SystemExit(
                "BLOCKED: ledger identity mismatch; refusing cross-plan state"
            )
    else:
        ledger.write_text(
            first_line + "\n\n## Completed Tasks\n\n## Parked Findings\n",
            encoding="utf-8",
        )

    print(json.dumps({
        "plan_identity": identity,
        "plan_slug": slug,
        "state_dir": str(state_dir),
        "ledger_path": str(ledger),
    }))
    PYEOF
  parse_json: true
  output: "plan_state"
```

Before `per-task-pipeline`, add a read-only reconciliation step that compares ledger entries with `git log --oneline` and reports discrepancies; it must never mark a task done solely from conversation memory.

Pass these exact values to the sub-recipe:

```yaml
context:
  current_task: "{{current_task}}"
  plan_identity: "{{plan_state.plan_identity}}"
  state_dir: "{{plan_state.state_dir}}"
  ledger_path: "{{plan_state.ledger_path}}"
```

In `single-task-pipeline.yaml`, replace both global state filenames with those four context values. The first bash step must re-read the ledger first line and refuse mismatches. Then add this exact task-state preparation step:

```yaml
- id: "prepare-task-state"
  type: "bash"
  timeout: 30
  command: |
    set -eu
    python3 - <<'PYEOF'
    import json
    import os
    import re
    import subprocess
    from pathlib import Path

    task_id = os.environ["TASK_ID"].strip()
    slug = re.sub(r"[^a-z0-9]+", "-", task_id.lower()).strip("-")
    if not slug:
        raise SystemExit("BLOCKED: task ID produced an empty slug")

    state_dir = Path(os.environ["STATE_DIR"])
    brief_path = state_dir / "task-briefs" / f"{slug}.md"
    base_path = state_dir / "task-briefs" / f"{slug}.base-sha"
    brief = """# Task Brief: {task_id}

## Goal
{description}

## Specification
{specification}

## Acceptance Criteria
{acceptance}

## Interfaces
{interfaces}

## Files
{files}
""".format(
        task_id=task_id,
        description=os.environ["TASK_DESCRIPTION"],
        specification=os.environ["TASK_SPEC"],
        acceptance=os.environ["TASK_ACCEPTANCE"],
        interfaces=os.environ["TASK_INTERFACES"],
        files=os.environ["TASK_FILES"],
    )
    brief_path.write_text(brief, encoding="utf-8")
    if not base_path.exists():
        base_path.write_text(
            subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() + "\n",
            encoding="utf-8",
        )

    print(json.dumps({
        "task_slug": slug,
        "task_brief_path": str(brief_path),
        "task_base_sha_path": str(base_path),
    }))
    PYEOF
  env:
    TASK_ID: "{{current_task.task_id}}"
    TASK_DESCRIPTION: "{{current_task.description}}"
    TASK_SPEC: "{{current_task.spec}}"
    TASK_ACCEPTANCE: "{{current_task.acceptance_criteria}}"
    TASK_INTERFACES: "{{current_task.interfaces}}"
    TASK_FILES: "{{current_task.files}}"
    STATE_DIR: "{{state_dir}}"
  parse_json: true
  output: "task_state"

- id: "load-plan-brief"
  type: "bash"
  timeout: 10
  command: |
    cat "{{ledger_path}}"
  output: "project_brief"
```

Use `{{task_state.task_slug}}`, `{{task_state.task_brief_path}}`, and `{{task_state.task_base_sha_path}}` in later steps; do not invent parallel path variables. Keeping an existing `.base-sha` on resume preserves the full task commit range. The plan-scoped ledger supplies the read-only project brief from prior tasks.

Delete every read/write of `.kenergy-checkpoint.json` and `.kenergy-project-brief.txt`.

**Static Analysis / Syntax**

```bash
python3 -c "import pathlib,yaml; [yaml.safe_load(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('recipes/subagent-driven-development.yaml','recipes/single-task-pipeline.yaml')]; print('YAML OK: state plumbing')"
```

Expected: `YAML OK: state plumbing`.

**Verification**

```bash
grep -n "initialize-plan-state\|# Plan:\|task-briefs\|review-packages\|plan_identity\|ledger_path" recipes/subagent-driven-development.yaml recipes/single-task-pipeline.yaml
if grep -n "\.kenergy-checkpoint\.json\|\.kenergy-project-brief\.txt" recipes/subagent-driven-development.yaml recipes/single-task-pipeline.yaml; then exit 1; else echo "legacy global state absent"; fi
```

Expected: all plan-scoped anchors appear; final line is `legacy global state absent`.

**Commit**

```bash
git add recipes/subagent-driven-development.yaml recipes/single-task-pipeline.yaml
git commit -m "refactor: scope execution state to each plan" \
  -m "🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)" \
  -m "Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
```

### Task 3: Replace tiered per-task review with uniform packet-driven review and bounded fixes

**Files:**
- Modify: `recipes/single-task-pipeline.yaml:18-535`

**Interfaces:**
- Consumes: task brief, base SHA, explicit model-role fields, plan-scoped paths, and `kenergy:reviewer`.
- Produces: a reviewed task commit, review packages for every round, a `PASS|APPROVED_WITH_PARKED|BLOCKED` outcome, and a ledger entry only for safe completion.

**Implementation**

Replace the tier classifier, split review loops, standard combined review, and old checkpoint/brief generator with one lifecycle. Keep `check-task-complete`, but make it trust only a matching ledger plus corroborating Git history.

Use conditional agent steps so `model_role` is explicit and never a template hidden in an inherited default:

```yaml
- id: "implement-fast"
  condition: "{{task_already_done}} != 'true' and {{current_task.implementation_model_role}} == 'fast'"
  agent: "kenergy:implementer"
  model_role: "fast"
  prompt: &implementation_prompt |
    IMPLEMENT ONE TASK
    ==================

    TASK GOAL
    =========
    Task ID: {{current_task.task_id}}
    Description: {{current_task.description}}
    Specification: {{current_task.spec}}
    Acceptance Criteria: {{current_task.acceptance_criteria}}
    Interfaces: {{current_task.interfaces}}
    Files: {{current_task.files}}

    PLAN-SCOPED PROJECT BRIEF
    =========================
    {{project_brief}}

    Implement exactly this task and nothing else. Run the task's exact static
    analysis and VDD verification commands, record the actual output, and make
    one atomic commit. Do not substitute a string-presence check for behavioral
    proof. Do not push, merge, open a PR, or deploy.

    RESPONSE CONTRACT
    =================
    STATUS: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
    SESSION_ID: Copy the full Session ID from your injected environment context.
    TASK_ID: {{current_task.task_id}}
    FILES_CHANGED: list exact paths
    STATIC_ANALYSIS: exact command and output
    VERIFICATION: exact command, expected result, and actual output
    COMMIT: full commit hash and subject
    CONCERNS: NONE or specific concerns
    BLOCKER: NONE or the exact blocker
  output: "task_implementation"
  timeout: 3600
  retry:
    max_attempts: 3
    backoff: exponential
    initial_delay: 5
    max_delay: 120

- id: "implement-coding"
  condition: "{{task_already_done}} != 'true' and {{current_task.implementation_model_role}} == 'coding'"
  agent: "kenergy:implementer"
  model_role: "coding"
  prompt: *implementation_prompt
  output: "task_implementation"
  timeout: 3600
  retry:
    max_attempts: 3
    backoff: exponential
    initial_delay: 5
    max_delay: 120

- id: "implement-reasoning"
  condition: "{{task_already_done}} != 'true' and {{current_task.implementation_model_role}} == 'reasoning'"
  agent: "kenergy:implementer"
  model_role: "reasoning"
  prompt: *implementation_prompt
  output: "task_implementation"
  timeout: 3600
  retry:
    max_attempts: 3
    backoff: exponential
    initial_delay: 5
    max_delay: 120
```

The prompt includes the task goal/spec, acceptance criteria, Interfaces, exact files, project brief, and the mandatory full `SESSION_ID` status field.

Extract and validate the full session ID. Missing ID sets the task outcome to `BLOCKED`; it must not trigger a fresh replacement during rounds 1-3.

Add a five-iteration `while_condition` review loop. The first step in every iteration is a `bash` review-package generator scoped from the saved base SHA through current `HEAD`:

```yaml
- id: "build-review-package"
  type: "bash"
  timeout: 30
  command: |
    set -eu
    BASE_SHA=$(cat "{{task_state.task_base_sha_path}}")
    HEAD_SHA=$(git rev-parse HEAD)
    PACKAGE="{{state_dir}}/review-packages/{{task_state.task_slug}}-round-{{_loop_iteration}}.md"
    {
      printf '# Review Package\n\n'
      printf 'Base: %s\nHead: %s\n\n' "$BASE_SHA" "$HEAD_SHA"
      printf '## Diff Stat\n\n```text\n'
      git diff --stat "$BASE_SHA..$HEAD_SHA"
      printf '```\n\n## Commits\n\n```text\n'
      git log --oneline "$BASE_SHA..$HEAD_SHA"
      printf '```\n\n## Diff\n\n```diff\n'
      git diff "$BASE_SHA..$HEAD_SHA" --
      printf '```\n'
    } > "$PACKAGE"
    cat "$PACKAGE"
  output: "review_package"
```

Dispatch `kenergy:reviewer` on every task and every round. Duplicate the step for `fast`, `critique`, and `reasoning` review roles, each with an explicit matching `model_role`. Every prompt must have these two separate headings:

```text
TASK GOAL
=========
Task ID: {{current_task.task_id}}
Description: {{current_task.description}}
Specification: {{current_task.spec}}
Acceptance Criteria: {{current_task.acceptance_criteria}}
Interfaces: {{current_task.interfaces}}

REVIEW PACKAGE
==============
{{review_package}}
```

Parse only the exact `REVIEW: PASS` line as approval.

For rounds 1-3, use a controller agent step with `model_role: fast`. Its prompt must forbid direct edits and require exactly one tool action:

```text
Call delegate exactly once to resume the original implementer:

delegate(
  session_id="{{implementer_session_id}}",
  instruction="Fix only the load-bearing findings in this review, using this precomputed packet instead of re-running Git discovery: {{review_verdict}}\n\nREVIEW PACKAGE:\n{{review_package}}\n\nRerun the task's exact verification, commit, and return the full STATUS/SESSION_ID report.",
  model_role="{{current_task.implementation_model_role}}"
)

Return the delegate result verbatim. Do not edit files yourself. If resume fails,
return STATUS: BLOCKED with the exact error.
```

Use `agent: "kenergy:plan-writer"` only as this thin controller because recipe agent steps cannot resume prior children directly; its output is the resumed implementer's report. Do not ask it to plan or write an artifact.

For rounds 4-5, fresh-dispatch `kenergy:implementer` with `current_task.escalated_model_role`; branch into explicit `coding`, `reasoning`, and `critical-ops` steps. Supply the full original goal, current packet, all open findings, and instruction to fix only those findings.

At the fifth failed review, the recipe controller must consume the reviewer's severity tags:

- append every `[ADVISORY]` finding under `## Parked Findings` with task ID, round, and the reason `non-load-bearing after bounded review`; set outcome `APPROVED_WITH_PARKED` only when no load-bearing finding remains;
- if any `[LOAD-BEARING]` finding remains, set outcome `BLOCKED`, print one concise blocker report, and stop the sub-recipe;
- never turn an unclassified failure into a pass.

The ledger write condition must be exactly equivalent to:

```text
(task status is DONE or DONE_WITH_CONCERNS)
AND (review outcome is PASS or APPROVED_WITH_PARKED)
AND (no load-bearing finding remains)
```

Append `- [x] <task-id> — <HEAD> — <review-outcome>` under `## Completed Tasks`. Remove all `review_tier`, `classify-tier`, split spec/quality approvals, and silent unresolved-warning steps.

**Static Analysis / Syntax**

```bash
python3 -c "import pathlib,yaml; yaml.safe_load(pathlib.Path('recipes/single-task-pipeline.yaml').read_text(encoding='utf-8')); print('YAML OK: single-task-pipeline')"
```

Expected: `YAML OK: single-task-pipeline`.

**Verification**

```bash
cat recipes/single-task-pipeline.yaml
grep -n "build-review-package\|git diff --stat\|git log --oneline\|TASK GOAL\|REVIEW PACKAGE\|SESSION_ID:\|max_while_iterations: 5\|APPROVED_WITH_PARKED\|LOAD-BEARING" recipes/single-task-pipeline.yaml
if grep -n "review_tier\|classify-tier\|standard tier\|trivial tier\|spec-review-loop\|quality-review-loop" recipes/single-task-pipeline.yaml; then exit 1; else echo "tiered review absent"; fi
```

Expected: the full recipe reads as one coherent lifecycle; all new anchors appear; final line is `tiered review absent`.

**Commit**

```bash
git add recipes/single-task-pipeline.yaml
git commit -m "refactor: unify per-task review and fix convergence" \
  -m "🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)" \
  -m "Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
```

### Task 4: Make parent execution pre-flight once and then run continuously

**Files:**
- Modify: `recipes/subagent-driven-development.yaml:1-437`

**Interfaces:**
- Consumes: complete parsed plan plus plan state from Task 2.
- Produces: either one batched `BLOCKED` conflict report before Task 1 or uninterrupted task execution ending in one concise completion result.

**Implementation**

After state initialization and before the `foreach`, add one `preflight-conflict-scan` agent step with `model_role: reasoning`. Require strict JSON:

```json
{"status":"CLEAR","conflicts":[]}
```

or, when an actual contradiction exists:

```json
{"status":"CONFLICTS","conflicts":[{"tasks":["task-2","task-4"],"constraint":"Global Constraints require Python 3.12 but task-4 pins Python 3.11","question":"Which Python version is authoritative?"}]}
```

Its prompt must scan the whole plan once for tasks that contradict each other, Global Constraints, or mandates that the review rubric would necessarily reject. Add a bash gate: if conflicts exist, print all questions together under `BLOCKED: PLAN CONFLICTS` and exit nonzero; if clear, print `Pre-flight clear.` Do not ask one question per conflict.

Make the per-task sub-recipe sequential and fail-fast:

```yaml
- id: "per-task-pipeline"
  foreach: "{{plan_data.tasks}}"
  as: "current_task"
  parallel: false
  checkpoint_iterations: true
  on_error: "fail"
  type: "recipe"
  recipe: "single-task-pipeline.yaml"
  context:
    current_task: "{{current_task}}"
    plan_identity: "{{plan_state.plan_identity}}"
    state_dir: "{{plan_state.state_dir}}"
    ledger_path: "{{plan_state.ledger_path}}"
  collect: "completed_tasks"
```

Remove the final-review approval stage, approval-prep stage, and merge-options stage. The execution recipe does not ask whether to continue and does not duplicate `/finish`. End with one `model_role: fast` summary step whose output is at most one status line plus ledger path and `ALL_TASKS_COMPLETE` or `BLOCKED`.

Add explicit `model_role` to every remaining agent step in this recipe. Parsing/summarizing uses `fast`; conflict scan uses `reasoning`; do not leave unnamed defaults.

Update comments, description, version, and tags so they describe merged review, continuous execution, and ledger state rather than two-stage/tiered review and approval gates.

**Static Analysis / Syntax**

```bash
python3 -c "import pathlib,yaml; yaml.safe_load(pathlib.Path('recipes/subagent-driven-development.yaml').read_text(encoding='utf-8')); print('YAML OK: subagent-driven-development')"
```

Expected: `YAML OK: subagent-driven-development`.

**Verification**

```bash
cat recipes/subagent-driven-development.yaml
grep -n "preflight-conflict-scan\|BLOCKED: PLAN CONFLICTS\|checkpoint_iterations: true\|on_error: \"fail\"\|ALL_TASKS_COMPLETE" recipes/subagent-driven-development.yaml
if grep -ni "should I continue\|human approval required\|approval prep\|two-stage-review\|tiered-review" recipes/subagent-driven-development.yaml; then exit 1; else echo "execution pauses absent"; fi
```

Expected: pre-flight is single-shot and batched; normal execution has no approval/pause language; final line is `execution pauses absent`.

**Commit**

```bash
git add recipes/subagent-driven-development.yaml
git commit -m "refactor: execute plans continuously after pre-flight" \
  -m "🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)" \
  -m "Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
```

### Task 5: Align secondary execution recipes with the merged reviewer and two-checkpoint path

**Files:**
- Modify: `recipes/executing-plans.yaml:1-369`
- Modify: `recipes/validate-implementation.yaml:1-293`
- Modify: `recipes/kenergy-full-development-cycle.yaml:1-452`

**Interfaces:**
- Consumes: existing public recipe entry points and `kenergy:reviewer`.
- Produces: backward-compatible continuous execution, merged validation verdicts, and a full-cycle recipe with design and finish approvals only.

**Implementation**

Replace `executing-plans.yaml` with a compatibility wrapper so old callers no longer enter batch checkpoints:

```yaml
name: "executing-plans"
description: "Compatibility entry point for continuous subagent-driven plan execution"
version: "2.0.0"
author: "Kenergy Bundle"
tags: ["implementation", "planning", "vdd", "continuous-execution"]

context:
  plan_path: ""
  batch_size: 3  # Accepted for compatibility; intentionally ignored.

steps:
  - id: "execute-continuously"
    type: "recipe"
    recipe: "subagent-driven-development.yaml"
    context:
      plan_path: "{{plan_path}}"
    output: "execution_result"
```

In `validate-implementation.yaml`, merge the two per-task reviewer calls into one `kenergy:reviewer` call. Generate one read-only review packet for the externally completed range before `foreach`, pass each task's complete goal plus the packet, and summarize its three axes. Add an explicit risk-scaled `model_role` to the reviewer and explicit roles to every other agent step. Keep this recipe single-pass; do not add a fix loop.

In `kenergy-full-development-cycle.yaml`:

- retain approval after design and the final finish-action approval;
- remove the plan approval entirely;
- run planning directly into `subagent-driven-development.yaml`;
- replace the old task-verification dispatch after SDD with `kenergy:code-reviewer` for holistic branch review, explicitly `model_role: critique`;
- do not add any mid-build approval;
- ensure all changed agent steps explicitly name `model_role`.

**Static Analysis / Syntax**

```bash
python3 -c "import pathlib,yaml; [yaml.safe_load(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('recipes/executing-plans.yaml','recipes/validate-implementation.yaml','recipes/kenergy-full-development-cycle.yaml')]; print('YAML OK: secondary recipes')"
```

Expected: `YAML OK: secondary recipes`.

**Verification**

```bash
grep -n "kenergy:reviewer\|kenergy:code-reviewer\|execute-continuously" recipes/executing-plans.yaml recipes/validate-implementation.yaml recipes/kenergy-full-development-cycle.yaml
printf 'full-cycle approvals: '; grep -c '^[[:space:]]*approval:' recipes/kenergy-full-development-cycle.yaml
if grep -n "kenergy:verifier\|kenergy:quality-reviewer" recipes/executing-plans.yaml recipes/validate-implementation.yaml recipes/kenergy-full-development-cycle.yaml; then exit 1; else echo "legacy reviewer IDs absent"; fi
```

Expected: full-cycle approval count is `2`; final line is `legacy reviewer IDs absent`.

**Commit**

```bash
git add recipes/executing-plans.yaml recipes/validate-implementation.yaml recipes/kenergy-full-development-cycle.yaml
git commit -m "refactor: align secondary recipes with continuous review" \
  -m "🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)" \
  -m "Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
```

### Task 6: Rewrite build-mode and skill guidance around the uniform reviewer lifecycle

**Files:**
- Modify: `modes/build-like-ken.md:27-246`
- Modify: `skills/kenergy-reference/SKILL.md:6-131`
- Modify: `skills/vdd-walkthrough/SKILL.md:6-68`

**Interfaces:**
- Consumes: the execution behavior implemented in Tasks 2-5.
- Produces: accurate manual-mode and on-demand reference guidance for reviewer packets, resume/escalate fixes, model judgment, and continuous execution.

**Implementation**

Rewrite `build-like-ken.md` from a three-agent/two-stage pipeline to this state machine:

```text
LOAD PLAN -> validate ledger identity -> pre-flight conflicts once
  FOR EACH INCOMPLETE TASK:
    choose explicit implement/review/escalation roles
    save task brief and base SHA
    DELEGATE implementer
    build diff/log/stat review package
    DELEGATE kenergy:reviewer with TASK GOAL + REVIEW PACKAGE
      FAIL rounds 1-3 -> delegate(session_id=<original>, model_role=<original>)
      FAIL rounds 4-5 -> fresh implementer, model_role=<escalated>
      FAIL at cap -> park advisory with reason; BLOCKED on load-bearing
    write ledger only after accepted review
  ALL DONE -> one-line result -> /finish
```

Require no per-task questions, no "Should I continue?", and no todos as durable state. Preserve the orchestrator's no-write boundary; subagents still create artifacts. Update delegate examples so every call has `model_role`, reviewers always receive goal + packet, and fix examples reuse `session_id` for rounds 1-3.

Update `kenergy-reference` agent table to one task reviewer with three axes, change key rules from two-stage review to merged three-axis review, and record exactly two checkpoints. Update `vdd-walkthrough` examples and call shapes to a single reviewer and the five-round resume/escalate loop.

**Verification**

```bash
cat modes/build-like-ken.md
cat skills/kenergy-reference/SKILL.md
cat skills/vdd-walkthrough/SKILL.md
grep -n "TASK GOAL\|REVIEW PACKAGE\|session_id\|rounds 1-3\|rounds 4-5\|kenergy:reviewer\|human attention" modes/build-like-ken.md skills/kenergy-reference/SKILL.md skills/vdd-walkthrough/SKILL.md
```

Expected: all three files describe the same lifecycle and contain no split-review instructions.

**Commit**

```bash
git add modes/build-like-ken.md skills/kenergy-reference/SKILL.md skills/vdd-walkthrough/SKILL.md
git commit -m "docs: align build guidance with merged review" \
  -m "🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)" \
  -m "Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
```

---

## Phase 2: Direct Planning and Genuine-Fork Interaction

### Task 7: Add Global Constraints and Interfaces to the plan-writer contract

**Files:**
- Modify: `agents/plan-writer.md:53-101`

**Interfaces:**
- Consumes: an approved design and repository exploration.
- Produces: plans with plan-wide inherited constraints and exact per-task boundary contracts.

**Implementation**

Add the exact shipped Obra blocks to the existing Kenergy template, adapted only to preserve the `/build-like-ken` header. After Tech Stack and Verification approach, add:

```markdown
## Global Constraints

[The spec's project-wide requirements — version floors, dependency limits,
naming and copy rules, platform requirements — one line each, with exact
values copied verbatim from the spec. Every task's requirements implicitly
include this section.]
```

After every task's Files block, add:

```markdown
**Interfaces:**
- Consumes: [what this task uses from earlier tasks — exact signatures]
- Produces: [what later tasks rely on — exact function names, parameter
  and return types. A task's implementer sees only their own task; this
  block is how they learn the names and types neighboring tasks use.]
```

Update `Before Writing`, Content Rules, and Red Flags so omissions are errors. Do not remove or soften `**Complete code.** Not "add validation" — show the actual code.` or any copy-pasteable-code language.

**Verification**

```bash
cat agents/plan-writer.md
grep -n "## Global Constraints\|\*\*Interfaces:\*\*\|Consumes:\|Produces:\|\*\*Complete code\.\*\*" agents/plan-writer.md
```

Expected: both new blocks and the unchanged complete-code rule appear.

**Commit**

```bash
git add agents/plan-writer.md
git commit -m "feat: add plan constraints and interfaces" \
  -m "🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)" \
  -m "Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
```

### Task 8: Make the writing-plans recipe generate, save, and execute without approval

**Files:**
- Modify: `recipes/writing-plans.yaml:1-278`

**Interfaces:**
- Consumes: `design_path`, optional `feature_name`, and the updated plan-writer contract.
- Produces: a saved implementation plan with Global Constraints/Interfaces, then direct execution via `subagent-driven-development.yaml`.

**Implementation**

Update design analysis to extract exact project-wide constraints. Update task breakdown to produce Interfaces/Consumes/Produces and explicit model-role recommendations without complexity tiers. Insert the exact Global Constraints and Interfaces blocks from Task 7 into the `create-plan` prompt.

Keep these requirements verbatim in the prompt:

```text
2. Every code block must be COMPLETE and copy-pasteable
3. NO placeholders like "..." or "// add your code here"
```

Remove the planning-stage `approval:` block. Remove `offer-execution` and all choice/batch-checkpoint language. After `save-plan`, add:

```yaml
- id: "execute-plan"
  type: "recipe"
  recipe: "subagent-driven-development.yaml"
  context:
    plan_path: "{{saved_plan_path}}"
  output: "execution_result"
```

Ensure `saved_plan_path` is only the normalized path string, not prose, so it can be passed as `plan_path`. Every agent step must explicitly use `model_role: reasoning` for plan synthesis or `model_role: fast` for metadata/path-only work.

**Static Analysis / Syntax**

```bash
python3 -c "import pathlib,yaml; yaml.safe_load(pathlib.Path('recipes/writing-plans.yaml').read_text(encoding='utf-8')); print('YAML OK: writing-plans')"
```

Expected: `YAML OK: writing-plans`.

**Verification**

```bash
grep -n "## Global Constraints\|\*\*Interfaces:\*\*\|Consumes:\|Produces:\|type: \"recipe\"\|subagent-driven-development.yaml" recipes/writing-plans.yaml
if grep -ni "implementation plan ready for review\|approve to save\|what would you like to do\|batch execution" recipes/writing-plans.yaml; then exit 1; else echo "plan approval and choices absent"; fi
```

Expected: new structure and direct execution appear; final line is `plan approval and choices absent`.

**Commit**

```bash
git add recipes/writing-plans.yaml
git commit -m "refactor: make planning a direct execution step" \
  -m "🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)" \
  -m "Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
```

### Task 9: Rewrite plan-like-ken as the direct action used in this session

**Files:**
- Modify: `modes/plan-like-ken.md:27-231`

**Interfaces:**
- Consumes: one approved design document path.
- Produces: one delegated implementation plan and immediate handoff to `/build-like-ken`/continuous execution.

**Implementation**

Replace the interactive hybrid-planning role with:

```markdown
PLAN-LIKE-KEN MODE: Turn an approved design directly into an executable plan.

<CRITICAL>
Design approval is the planning authorization. Do not negotiate task breakdown,
granularity, ordering, or file decomposition with the human unless the approved
design contains a fact only they can supply.

Read the approved design, inspect the repository, delegate the complete planning
job to `kenergy:plan-writer`, save the resulting plan, then hand it directly to
execution. There is no plan-approval gate and no task-by-task negotiation.

You cannot write the plan yourself. The plan-writer owns the artifact.
</CRITICAL>
```

The process becomes exactly:

1. Read the approved design and repository conventions.
2. Resolve implementation-level details with engineering judgment.
3. Delegate once to `kenergy:plan-writer` with the design path, repository patterns, authoritative verification method, and save path.
4. Confirm the file exists and contains Global Constraints plus Interfaces.
5. Transition to `/build-like-ken` and execute without asking whether the plan looks right.

Update the delegate example to `context_depth="none"` with a fully self-contained instruction and `model_role="reasoning"`. Update Announcement and Do NOT lists. Preserve VDD hierarchy and the full-code plan requirement.

**Verification**

```bash
cat modes/plan-like-ken.md
grep -n "Design approval is the planning authorization\|There is no plan-approval gate\|kenergy:plan-writer\|model_role=\"reasoning\"\|Global Constraints\|Interfaces" modes/plan-like-ken.md
if grep -ni "discuss plan structure\|agree on scope\|does this plan look right\|confirm the task breakdown" modes/plan-like-ken.md; then exit 1; else echo "interactive planning gate absent"; fi
```

Expected: the file matches the direct flow actually used to create this plan; final line is `interactive planning gate absent`.

**Commit**

```bash
git add modes/plan-like-ken.md
git commit -m "refactor: make plan-like-ken non-interactive" \
  -m "🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)" \
  -m "Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
```

### Task 10: Replace think-like-ken section gating with genuine-forks-only review

**Files:**
- Modify: `modes/think-like-ken.md:26-215`

**Interfaces:**
- Consumes: user intent plus evidence, precedent, research, and optional inline persona lenses.
- Produces: a complete design with one consolidated TL;DR review unless a genuine user-only fork exists.

**Implementation**

Replace the existing `<HARD-GATE>`, one-question-per-message rules, Phase 4, anti-rationalization rows, Do NOT list, Key Principles, and Announcement with the design's exact policy:

```markdown
<HARD-GATE>
Interrupt the human only at genuine forks; human attention is the costliest resource.

- When a design decision has a defensible engineering answer backed by evidence,
  precedent, or research, decide it directly and include the choice with brief
  reasoning in one consolidated review. Do not stop and ask.
- You may optionally sanity-check judgment inline through a persona lens such as
  `restless-old-brian`, `cranky-old-sam`, or `crusty-old-engineer`. These are
  inline skills to embody, not separate dispatches.
- Ask directly only for genuine personal-preference questions or facts only the
  user knows.
- Batch questions by topic; never split one topic into micro-decisions across
  messages.
- When zero non-AI-decidable choices remain, skip directly to one final
  TL;DR-style review instead of section-by-section gating.

Do not delegate the design document until that one final design review is
explicitly approved.
</HARD-GATE>
```

Keep the single final design approval and design-writer delegation. Remove fixed 200-300-word sections, `Does this look right so far?`, mandatory one-question cadence, and the claim that every simple project requires section-by-section validation.

**Verification**

```bash
cat modes/think-like-ken.md
grep -n "Interrupt the human only at genuine forks\|restless-old-brian\|Batch questions by topic\|zero non-AI-decidable choices\|TL;DR-style review\|explicitly approved" modes/think-like-ken.md
if grep -n "200-300 words\|After EACH section\|Does this look right so far\|Ask ONE question per message" modes/think-like-ken.md; then exit 1; else echo "fixed cadence absent"; fi
```

Expected: exact genuine-fork policy appears; final line is `fixed cadence absent`.

**Commit**

```bash
git add modes/think-like-ken.md
git commit -m "refactor: gate design only at genuine forks" \
  -m "🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)" \
  -m "Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
```

### Task 11: Restore always-loaded philosophy to VDD and two checkpoints

**Files:**
- Modify: `context/philosophy.md:1-140`
- Modify: `context/shared-anti-rationalization.md:1-20`
- Modify: `context/using-superpowers-amplifier.md:20-60`

**Interfaces:**
- Consumes: the VDD and checkpoint behavior now implemented by modes/recipes.
- Produces: non-contradictory always-loaded guidance.

**Implementation**

Rename the philosophy title to `# Kenergy Philosophy`. Replace Principle 1 with:

````markdown
### 1. Verification-Driven Development is Non-Negotiable

Define the claim, choose the cheapest real check that could falsify it, run that
check, read the actual output, and only then claim completion.

The cycle:

```text
CLAIM: State the behavior that must be true
  -> METHOD: Choose a check that would fail if the behavior broke
  -> EXECUTE: Run the real path at the appropriate VDD level
  -> EVIDENCE: Record the exact command and observed output
  -> REVIEW: Confirm the evidence proves the original claim
```

Static analysis is the floor. Unit tests are appropriate for library behavior.
Use direct execution, live HTTP, browser observation, or an isolated reality
check when those are the real production path. Mocks-only evidence does not prove
non-library product behavior.
````

Replace the two-stage reviewer section with one three-axis reviewer section. Replace Principle 7 with exactly:

```markdown
### 7. Human Checkpoints Only at Genuine Forks

The normal development path has two checkpoints:
1. Design approval, once.
2. The pre-merge, PR, keep, or discard decision in `/finish`, once.

Planning mechanics and execution progress are engineering work, not human
checkpoints. A pre-flight conflict is surfaced only when an actual contradiction
requires a human decision.
```

Rewrite the workflow diagram to `DESIGN (approve once) -> PLAN (automatic) -> WORKTREE -> EXECUTE (continuous) -> FINISH (choose once)`. Replace TDD/test-first rationalization rows with VDD rows about choosing a falsifiable method, running the real path, and documenting output.

In `shared-anti-rationalization.md`, replace test-first instructions with claim/method/evidence discipline. In `using-superpowers-amplifier.md`, replace `code-quality-reviewer` examples with `reviewer` and label VDD/debugging as rigid disciplines.

**Verification**

```bash
cat context/philosophy.md
cat context/shared-anti-rationalization.md
cat context/using-superpowers-amplifier.md
grep -n "Verification-Driven Development is Non-Negotiable\|Human Checkpoints Only at Genuine Forks\|Design approval, once\|pre-merge, PR, keep, or discard\|three-axis" context/philosophy.md
if grep -n "Test-Driven Development is Non-Negotiable\|start with TDD\|TDD will slow\|write the test first\|two-stage review" context/philosophy.md context/shared-anti-rationalization.md context/using-superpowers-amplifier.md; then exit 1; else echo "always-loaded TDD workflow absent"; fi
```

Expected: three files agree on VDD and the two-checkpoint path; final line is `always-loaded TDD workflow absent`.

**Commit**

```bash
git add context/philosophy.md context/shared-anti-rationalization.md context/using-superpowers-amplifier.md
git commit -m "fix: restore VDD philosophy consistency" \
  -m "🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)" \
  -m "Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
```

---

## Phase 3: Naming, Dangling Features, Finish Safety, and Retirement

### Task 12: Correct Kenergy-native names in standing instructions

**Files:**
- Modify: `context/instructions.md:53-118`

**Interfaces:**
- Consumes: actual recipe and skill names in this bundle.
- Produces: resolvable Kenergy-native standing instructions.

**Implementation**

Apply these exact substitutions throughout `context/instructions.md`:

```text
superpowers-full-development-cycle
  -> kenergy-full-development-cycle
superpowers:recipes/superpowers-full-development-cycle.yaml
  -> kenergy:recipes/kenergy-full-development-cycle.yaml
superpowers:recipes/subagent-driven-development.yaml
  -> kenergy:recipes/subagent-driven-development.yaml
load_skill(skill_name="superpowers-reference")
  -> load_skill(skill_name="kenergy-reference")
```

Update the autopilot paragraph to say it has the design and finish decision gates, not approval at every stage. Update bite-sized examples from test-first steps to task implementation plus its attached real verification.

**Verification**

```bash
cat context/instructions.md
grep -n "kenergy-full-development-cycle\|kenergy:recipes/kenergy-full-development-cycle.yaml\|kenergy:recipes/subagent-driven-development.yaml\|kenergy-reference" context/instructions.md
if grep -n "superpowers-full-development-cycle\|superpowers:recipes\|superpowers-reference" context/instructions.md; then exit 1; else echo "naming drift absent"; fi
```

Expected: all Kenergy names appear; final line is `naming drift absent`.

**Commit**

```bash
git add context/instructions.md
git commit -m "fix: use kenergy-native workflow names" \
  -m "🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)" \
  -m "Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
```

### Task 13: Remove the unsupported visual companion and its references

**Files:**
- Delete: `context/visual-companion-guide.md`
- Modify: `README.md:63-70`
- Modify: `agents/design-writer.md:88-91`
- Modify: `behaviors/kenergy.yaml:44-48`

**Interfaces:**
- Consumes: existing dangling documentation references.
- Produces: no visual-companion capability claim or context mention.

**Implementation**

Delete `context/visual-companion-guide.md`. Remove its bullet from README, its `@kenergy:` mention from `agents/design-writer.md`, and its name from the behavior's unloaded-context comment. Do not add a replacement server, script, tool, or fallback feature.

While editing README's workflow overview, update `/plan-like-ken` to direct planning and `/build-like-ken` to implementer -> merged reviewer with continuous execution. Do not perform the final retirement sweep here; Task 15 owns the complete cross-reference check.

**Verification**

```bash
test ! -e context/visual-companion-guide.md && echo "visual companion deleted"
if grep -rn --exclude='2026-08-01-review-architecture-synthesis-design.md' --exclude='2026-08-01-review-architecture-synthesis-implementation.md' "visual-companion-guide" README.md agents behaviors context; then exit 1; else echo "live visual references absent"; fi
```

Expected: `visual companion deleted` and `live visual references absent`.

**Commit**

```bash
git add README.md agents/design-writer.md behaviors/kenergy.yaml
git rm context/visual-companion-guide.md
git commit -m "fix: remove unsupported visual companion references" \
  -m "🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)" \
  -m "Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
```

### Task 14: Capture worktree paths before finish operations mutate directories

**Files:**
- Modify: `recipes/finish-branch.yaml:28-417`
- Modify: `modes/finish.md:104-244`

**Interfaces:**
- Consumes: the entry worktree, branch, Git common directory, and user's final action.
- Produces: safe merge/discard/cleanup operations using immutable captured paths.

**Implementation**

Add the first recipe step `capture-entry-paths` as a bash step before any agent can `cd`, check out, or remove anything:

```yaml
- id: "capture-entry-paths"
  type: "bash"
  timeout: 30
  command: |
    set -eu
    python3 - <<'PYEOF'
    import json
    import subprocess
    from pathlib import Path

    supplied = "{{worktree_path}}".strip()
    worktree = Path(supplied).expanduser().resolve() if supplied else Path(
        subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True
        ).strip()
    ).resolve()
    branch = "{{branch_name}}".strip() or subprocess.check_output(
        ["git", "-C", str(worktree), "branch", "--show-current"], text=True
    ).strip()
    common = Path(subprocess.check_output(
        ["git", "-C", str(worktree), "rev-parse", "--path-format=absolute", "--git-common-dir"],
        text=True,
    ).strip()).resolve()
    main_repo = common.parent
    print(json.dumps({
        "worktree_path": str(worktree),
        "branch_name": branch,
        "main_repo_path": str(main_repo),
    }))
    PYEOF
  parse_json: true
  output: "entry_paths"
```

Use only `{{entry_paths.worktree_path}}`, `{{entry_paths.branch_name}}`, and `{{entry_paths.main_repo_path}}` in later prompts. Merge/discard/cleanup instructions must `cd "{{entry_paths.main_repo_path}}"` before `git worktree remove "{{entry_paths.worktree_path}}"`. Never recompute the worktree path after checkout or removal.

Replace the task-quality agent used for change summarization with `kenergy:code-reviewer` at explicit `model_role: critique`, because this is a holistic branch operation. Replace the blocked-merge formatter with `foundation:git-ops` at explicit `model_role: fast`. Add explicit model roles to every changed agent step.

In `modes/finish.md`, add a capture-on-entry snippet before Step 1:

```bash
worktree_path="$(git rev-parse --show-toplevel)"
feature_branch="$(git branch --show-current)"
git_common_dir="$(git rev-parse --path-format=absolute --git-common-dir)"
main_repo_path="$(dirname "$git_common_dir")"
```

All merge/discard/cleanup examples must consume those variables after `cd "$main_repo_path"`.

**Static Analysis / Syntax**

```bash
python3 -c "import pathlib,yaml; yaml.safe_load(pathlib.Path('recipes/finish-branch.yaml').read_text(encoding='utf-8')); print('YAML OK: finish-branch')"
```

Expected: `YAML OK: finish-branch`.

**Verification**

```bash
cat recipes/finish-branch.yaml
cat modes/finish.md
grep -n "capture-entry-paths\|entry_paths.worktree_path\|entry_paths.main_repo_path\|--path-format=absolute\|cd \"\$main_repo_path\"" recipes/finish-branch.yaml modes/finish.md
if grep -n "kenergy:verifier\|kenergy:quality-reviewer" recipes/finish-branch.yaml; then exit 1; else echo "finish legacy reviewers absent"; fi
```

Expected: captured paths are used after directory mutations; final line is `finish legacy reviewers absent`.

**Commit**

```bash
git add recipes/finish-branch.yaml modes/finish.md
git commit -m "fix: preserve worktree paths through finish cleanup" \
  -m "🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)" \
  -m "Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
```

### Task 15: Retire old agents and sweep every live reference

**Files:**
- Delete: `agents/verifier.md`
- Delete: `agents/quality-reviewer.md`
- Modify: `behaviors/kenergy.yaml:6-14`
- Modify: `agents/code-reviewer.md:15-40`
- Modify: `README.md:13-35`
- Modify: `bundle.md:22-29`
- Modify: any remaining live file returned by the retirement grep, excluding the two design/plan artifacts named below

**Interfaces:**
- Consumes: all migrations from Tasks 1-14.
- Produces: one registered task reviewer, no dangling live references, valid changed recipes, and consistent end-to-end documentation.

**Implementation**

Remove the two old registrations from `behaviors/kenergy.yaml`, leaving `kenergy:reviewer` exactly once. Delete both retired agent files.

In `agents/code-reviewer.md`, replace stale names with `kenergy:reviewer` while preserving the holistic boundary: the merged reviewer is task-scoped; code-reviewer is branch/session-scoped.

Update README and `bundle.md` to state:

```text
/think-like-ken -> consolidated design review -> one approval
/plan-like-ken  -> direct plan generation -> automatic execution handoff
/build-like-ken -> implementer -> three-axis reviewer -> bounded fix loop
/finish         -> merge / PR / keep / discard decision
```

Run the retirement grep across the repository. The approved design and this implementation plan intentionally document the migration and are immutable evidence, so exclude those two artifacts; every live bundle surface must return zero matches. Fix every live match found, including comments and examples.

Finally validate every recipe touched by this plan and read the two central rewritten recipes end to end.

**Static Analysis / Syntax**

```bash
python3 - <<'PYEOF'
from pathlib import Path
import yaml

files = [
    "recipes/single-task-pipeline.yaml",
    "recipes/subagent-driven-development.yaml",
    "recipes/executing-plans.yaml",
    "recipes/validate-implementation.yaml",
    "recipes/kenergy-full-development-cycle.yaml",
    "recipes/writing-plans.yaml",
    "recipes/finish-branch.yaml",
]
for name in files:
    yaml.safe_load(Path(name).read_text(encoding="utf-8"))
    print(f"YAML OK: {name}")
PYEOF
```

Expected: one `YAML OK` line for each of the seven recipes.

**Verification**

```bash
test ! -e agents/verifier.md
test ! -e agents/quality-reviewer.md

grep -n "kenergy:reviewer" behaviors/kenergy.yaml

grep -rn \
  --exclude='2026-08-01-review-architecture-synthesis-design.md' \
  --exclude='2026-08-01-review-architecture-synthesis-implementation.md' \
  "kenergy:verifier\|kenergy:quality-reviewer" .

cat recipes/single-task-pipeline.yaml
cat recipes/subagent-driven-development.yaml
```

Expected:

- both `test ! -e` commands succeed;
- behavior grep returns exactly one registration;
- retirement grep returns no output and exit status 1 (no live matches);
- both central recipes read coherently end to end.

**Commit**

```bash
git add behaviors/kenergy.yaml agents/code-reviewer.md README.md bundle.md
git add -u
git commit -m "refactor: retire split task reviewers" \
  -m "🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)" \
  -m "Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
```

---

## Final Execution Evidence

After Task 15, collect the following evidence before claiming the design is implemented:

```bash
# All changed recipes parse.
python3 - <<'PYEOF'
from pathlib import Path
import yaml
for path in sorted(Path("recipes").glob("*.yaml")):
    yaml.safe_load(path.read_text(encoding="utf-8"))
print("All recipe YAML parsed")
PYEOF

# No global execution-state files remain in live configuration.
grep -rn ".kenergy-checkpoint.json\|.kenergy-project-brief.txt" recipes modes agents context skills behaviors README.md bundle.md

# No review tiering remains in the per-task pipeline.
grep -n "review_tier\|classify-tier\|standard tier\|trivial tier\|complex tier" recipes/single-task-pipeline.yaml

# Every agent step in the two core recipes names a role. Inspect every result.
grep -n "^[[:space:]]*agent:\|^[[:space:]]*model_role:" recipes/single-task-pipeline.yaml recipes/subagent-driven-development.yaml

# Planning has no approval gate; full cycle has exactly two.
printf 'writing-plans approvals: '; grep -c '^[[:space:]]*approval:' recipes/writing-plans.yaml || true
printf 'full-cycle approvals: '; grep -c '^[[:space:]]*approval:' recipes/kenergy-full-development-cycle.yaml

# Unsupported visual feature is gone.
test ! -e context/visual-companion-guide.md

git status --short
git log --oneline -15
```

Expected:

- `All recipe YAML parsed`.
- The two state/tier greps return no matches.
- Each `agent:` line in the two core recipes has an adjacent explicit `model_role:` on read-back.
- Writing-plans approval count is `0`; full-cycle approval count is `2`.
- Visual companion file is absent.
- Git status is clean after the final commit.
- Git log shows the 15 ordered task commits.
