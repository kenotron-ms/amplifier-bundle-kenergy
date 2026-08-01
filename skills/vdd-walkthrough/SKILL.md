---
name: vdd-walkthrough
description: Use when about to orchestrate a build-like-ken session — provides five realistic task outcomes with one merged task reviewer, explicit model roles, packet review, and the five-fix/six-review resume-escalate loop
---

# VDD Walkthrough

**Purpose:** Load this before orchestrating `/build-like-ken`. It shows the
uniform task lifecycle in action: one implementer, one merged task reviewer,
packet-based reviews, bounded remediation, durable ledger state, and continuous
execution after the plan-level pre-flight is clear.

The normal path is
`subagent-driven-development.yaml`. Direct `delegate()` orchestration is also
valid for bootstrap/manual work, but it must use the same lifecycle rather than
an ad-hoc review sequence.

## Lifecycle at a Glance

```text
load plan -> validate ledger identity -> pre-flight conflicts once
  -> choose task roles -> save task brief/base SHA -> implement
  -> build review packet -> merged review
  -> resume original session (rounds 1-3)
  -> fresh escalation (rounds 4-5)
  -> cap adjudication (review 6) -> accepted ledger entry or BLOCKED
  -> next incomplete task without a pause
```

The initial review is round 1. A failed review in rounds 1-3 resumes the same
original implementer session. Failed reviews in rounds 4-5 use a fresh,
stronger implementer. Review 6 rechecks the fifth fix and never launches a
sixth fix.

## Required Task Inputs

Before delegating an implementer, preserve these plan-scoped artifacts:

- A ledger whose identity line matches the exact absolute plan path.
- A task brief with the task goal, specification, acceptance criteria,
  interfaces, expected files, and chosen roles.
- The task's base SHA, captured before the first implementation attempt.
- A review package rebuilt for every review from base SHA through current `HEAD`:
  `git diff --stat`, `git log --oneline`, and the full `git diff`.

The root orchestrator does not write these artifacts. Recipe steps create them
in recipe execution; direct orchestration delegates artifact creation to a
write-capable child. Todos may show progress but are not durable state.

## Quick Reference: delegate() Call Shapes

Every call has an explicit `model_role`. Replace angle-bracket values with the
roles chosen for the task.

```python
# Initial implementer: fresh context, one task, one atomic commit.
delegate(
    agent="kenergy:implementer",
    instruction="""IMPLEMENT ONE TASK

EXECUTION ROOT: <worktree>

TASK GOAL
=========
Task ID: <task-id>
Goal: <goal>
Specification: <spec>
Acceptance Criteria: <criteria>
Interfaces: <consumes-and-produces>

Implement only this task. Run static analysis and the specified VDD verification,
record exact output, commit once, and return STATUS, SESSION_ID, changed files,
analysis, verification, commit, concerns, and blocker.""",
    context_depth="none",
    model_role="<implementation-model-role>",
)

# One merged reviewer: the goal and package are mandatory.
delegate(
    agent="kenergy:reviewer",
    instruction="""TASK GOAL
=========
Task ID: <task-id>
Goal: <goal>
Specification: <spec>
Acceptance Criteria: <criteria>
Interfaces: <consumes-and-produces>

REVIEW PACKAGE
==============
<base-to-head diff stat, commit log, and full diff>

Review goal/spec compliance, quality, and verification adequacy in one compact
verdict. Return PASS only if all three axes pass with no load-bearing finding.""",
    context_depth="none",
    model_role="<review-model-role>",
)

# Review failures in rounds 1-3: preserve the initial implementer's context.
delegate(
    session_id="<original-implementer-session-id>",
    instruction="""Work only in <worktree>.

TASK GOAL: <full-task-goal>

Fix only the open load-bearing findings. Use this supplied packet instead of
re-running Git discovery. Rerun the exact verification, commit the minimal fix,
and return the complete STATUS/SESSION_ID report.

REVIEW FINDINGS:
<review-verdict>

REVIEW PACKAGE:
<current-base-to-head-package>""",
    model_role="<original-implementation-model-role>",
)

# Review failures in rounds 4-5: use a fresh stronger implementation session.
delegate(
    agent="kenergy:implementer",
    instruction="""FRESH ESCALATED REVIEW FIX

EXECUTION ROOT: <worktree>

TASK GOAL
=========
<full-task-goal>

REVIEW PACKAGE
==============
<current-base-to-head-package>

OPEN FINDINGS
=============
<review-verdict>

Fix only the open load-bearing findings. Run static analysis and the exact VDD
verification, commit once, and return the complete STATUS/SESSION_ID report.""",
    context_depth="none",
    model_role="<escalated-model-role>",
)
```

After every fix, rebuild the packet from the original base SHA through current
`HEAD`, then use the single reviewer call again. Do not convert a failure into a
separate quality or verification stage.

## Status Handling Cheat Sheet

| Status | Meaning | Orchestrator action |
|--------|---------|---------------------|
| `DONE` | Task implementation completed with real verification and a commit | Build the packet and dispatch `kenergy:reviewer`. |
| `DONE_WITH_CONCERNS` | Completed but has a stated concern | Preserve the concern in the packet context; dispatch the merged reviewer. |
| `NEEDS_CONTEXT` | Required context is missing | Resolve from the plan or repository evidence, then re-delegate. If unavailable, stop `BLOCKED`; do not solicit a task-level decision. |
| `BLOCKED` | The task cannot complete | Preserve artifacts, do not write ledger completion, and return the exact blocker. |

## Review Verdict Handling

The reviewer returns one verdict containing three axes:

```text
REVIEW: PASS | FAIL
SPEC_GOAL: PASS | FAIL — <goal clause or file:line>
QUALITY: PASS | FAIL — <file:line or command>
VERIFICATION: PASS | FAIL — <command/evidence pointer and named break>
FINDINGS:
- [LOAD-BEARING|ADVISORY] <pointer> — <specific issue>
REQUIRED_FIXES:
- <minimal action or NONE>
```

- Accept `PASS` only when all axes pass and no load-bearing finding remains.
- A malformed or unclassified failure is fail-closed and becomes load-bearing at
  the cap.
- Review evidence must be falsifiable: name a production break that would make
  the claimed command fail. A string-presence check cannot prove runtime behavior.

## Five Worked Outcomes

### 1. Happy path: Task passes on review round 1

**Task:** Validate an email address in a library function.

1. Save the brief and base SHA.
2. Delegate `kenergy:implementer` with `model_role="coding"`.
3. The report returns `STATUS: DONE`, direct execution output, and a commit.
4. Build the base-to-HEAD package.
5. Delegate `kenergy:reviewer` with `model_role="critique"`, `TASK GOAL`, and
   `REVIEW PACKAGE`.
6. The reviewer returns all three axes PASS.
7. A write-capable child records `PASS` and current `HEAD` in the ledger.
8. Continue immediately to the next incomplete task.

### 2. Review round 1 fails: resume the original session

**Task:** Add a domain-reachability check that must return `False`, not raise,
for an unreachable domain.

The reviewer finds `[LOAD-BEARING]` goal noncompliance: the implementation
raises an exception. This is a round-1 failure, so reuse the reported original
session ID with `model_role` equal to the original role. Supply the full goal,
verdict, and current review packet. The resumed implementer fixes only the
failure, re-runs the real check, and commits. Rebuild the packet and review
again at round 2.

Do not start a replacement implementer in this case; early rounds preserve the
agent's working context and its responsibility for the first implementation.

### 3. A concern is not acceptance: DONE_WITH_CONCERNS still receives review

**Task:** Add an in-memory rate limiter.

The implementer reports `DONE_WITH_CONCERNS` because multi-worker deployment is
incompatible with the in-memory design. The orchestrator does not mark the task
complete from that report. It builds the packet and sends the task goal and
packet to the merged reviewer.

- If multi-worker support is in the task goal, the finding is load-bearing and
  follows the bounded fix loop.
- If it is outside the goal, the reviewer may classify it advisory. It is still
  recorded at cap if it remains, never silently accepted from implementer prose.

### 4. Rounds 4-5: fresh escalation after original-session attempts

**Task:** Wire a validation endpoint and prove its error response over HTTP.

Assume review rounds 1, 2, and 3 each return load-bearing findings after the
original session's fixes. At review round 4, do not resume that session again.
Dispatch a fresh `kenergy:implementer` using the selected stronger role, such as
`model_role="reasoning"`, with the full task goal, current packet, and open
findings. Repeat this only for round 5 if needed.

The fresh agent must not expand scope. It fixes the stated load-bearing issue,
runs the live HTTP verification from the task, and returns a new committed
report. Every re-review still uses the same one reviewer and all three axes.

### 5. Cap review: advisory may park; load-bearing blocks

**Task:** Add an error-response handler.

After the fifth remediation, rebuild the packet and run review round 6. This is
adjudication only.

- If the remaining findings are classified `[ADVISORY]` and no load-bearing
  finding remains, write `APPROVED_WITH_PARKED` to the ledger and include each
  advisory finding plus why it was parked.
- If any `[LOAD-BEARING]` finding remains, or the verdict fails without a
  valid classification, stop `BLOCKED`. Do not write a completed-task ledger
  entry and do not start task N+1.

There is no sixth fix attempt. The bounded loop is five remedies and six reviews,
not an invitation to retry until a reviewer gives up.

## Continuous Execution Rules

1. Validate ledger identity and run the plan conflict scan once before Task 1.
2. Choose implementation, review, and escalation roles per task before dispatch.
3. After a safe accepted ledger entry, begin the next incomplete task without a
   per-task pause.
4. Never write code or durable task artifacts in the root orchestrator session.
5. When all tasks have accepted ledger entries, report the concise completion
   result and transition to `/finish`.
