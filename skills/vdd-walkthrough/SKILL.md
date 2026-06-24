---
name: vdd-walkthrough
description: Use when about to orchestrate a build-like-ken session — provides 5 realistic task scenarios with Amplifier delegate() patterns, model_role selection, status handling (DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT), and fix loops for spec and quality issues
---

# VDD Walkthrough

**Purpose:** Load this when about to orchestrate a build-like-ken session. Provides concrete worked examples of all five common task outcomes so you know exactly what delegate() calls to make and how to respond to each reviewer verdict.

## Why This Skill Exists

The kenergy-reference skill describes the process. This skill shows it in action — real delegate() call syntax, realistic reviewer responses, and the decisions an orchestrator makes at each step. Reference it before you start so the patterns are fresh when edge cases appear.

## Scenarios Covered

| # | Task | Outcome Pattern | Key Technique |
|---|------|-----------------|---------------|
| 1 | Validate email format | Happy path: DONE → verifier PASS → quality PASS | context_depth='none', model_role='coding' |
| 2 | Domain reachability check | Spec gap caught: impl raises instead of returns False | Re-delegate with specific gap description |
| 3 | In-memory rate limiter | DONE_WITH_CONCERNS: multi-worker incompatibility | Note concern, proceed to review, surface to user |
| 4 | Validation endpoint wiring | Quality issues: magic number + missing error handling | Fix loop with attempt counter in instruction |
| 5 | Error response handler | NEEDS_CONTEXT: can't find error format | Grep investigation, re-delegate with discovery |

## Quick Reference: delegate() Call Shapes

```python
# Implementer — always fresh context, coding model
delegate(
    agent="kenergy:implementer",
    instruction="...",   # full task spec + context + verification method
    context_depth="none",
    model_role="coding",
)

# Verifier — needs recent agent results to see what was built
delegate(
    agent="kenergy:verifier",
    instruction="...",   # task spec + what was implemented + verification evidence
    context_depth="recent",
    context_scope="agents",
)

# Code quality reviewer — same context shape as verifier
delegate(
    agent="kenergy:quality-reviewer",
    instruction="...",   # commit refs + what was changed
    context_depth="recent",
    context_scope="agents",
)
```

## Status Handling Cheat Sheet

| Status | Meaning | Orchestrator Action |
|--------|---------|---------------------|
| `DONE` | Task complete, verified with real execution, committed | Proceed to verifier |
| `DONE_WITH_CONCERNS` | Complete but flagged an issue | Read concern, note it, proceed to review |
| `NEEDS_CONTEXT` | Missing info to proceed | Investigate (grep/read), re-delegate with context |
| `BLOCKED` | Cannot complete at all | Assess blocker, provide context or escalate |

## VDD-Specific Checks

When the verifier returns, look specifically for:
1. **Was real execution performed?** Not just "tests pass" — was the actual endpoint hit, script run, or browser opened?
2. **Is actual output documented?** The implementer should paste real command output, not just say "it worked".
3. **Was the verification method appropriate?** API endpoint → curl call. UI change → browser open. Script → executed directly.

A verifier FAIL because "only mocked unit tests were run for a non-library task" is legitimate and should trigger an implementer fix with explicit instructions to run the real thing.
