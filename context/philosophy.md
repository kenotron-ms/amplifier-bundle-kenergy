# Kenergy Philosophy

## Core Principles

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

### 2. Systematic Over Ad-Hoc

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

Always find the root cause before attempting fixes. Follow the four-phase debugging process: investigate, analyze patterns, form hypotheses, then implement.

### 3. Evidence Over Claims

"It should work" is not verification. "I tested it manually" is not proof.

**The Gate Function — apply before ANY completion claim:**
1. CLAIM: What behavior must be true?
2. METHOD: Which falsifiable check exercises that behavior at the correct VDD level?
3. EXECUTE: Run the real path fresh in this session.
4. EVIDENCE: Record the exact command, output, and exit status.
5. REVIEW: Does the observed evidence prove the original claim?

Every fix must be demonstrated with falsifiable evidence. Unit tests are
appropriate for library behavior; non-library product behavior requires the
relevant real path.

### 4. Complexity Reduction as Primary Goal

Simplicity is not just nice to have - it's the goal. Every abstraction must justify its existence.

YAGNI (You Aren't Gonna Need It) ruthlessly. DRY (Don't Repeat Yourself) pragmatically. Start minimal, grow only as needed.

### 5. Structured Planning Before Implementation

Never jump into code. First understand what you're building through collaborative design. Then create a detailed plan with bite-sized tasks. Then execute systematically.

The plan should be clear enough for "an enthusiastic junior engineer with poor taste, no judgment, no project context, and an aversion to verification" to follow.

### 6. Isolation for Safety

Use git worktrees to isolate feature work. Never work directly on main. Verify a clean applicable baseline before starting. Clean up when done.

### 7. Human Checkpoints Only at Genuine Forks

The normal development path has two checkpoints:
1. Design approval, once.
2. The pre-merge, PR, keep, or discard decision in `/finish`, once.

Planning mechanics and execution progress are engineering work, not human
checkpoints. A pre-flight conflict is surfaced only when an actual contradiction
requires a human decision.

## The Kenergy Workflow

```text
DESIGN (approve once) -> PLAN (automatic) -> WORKTREE -> EXECUTE (continuous) -> FINISH (choose once)
```

Each phase uses the appropriate workflow mechanisms with built-in quality gates.

## The Three-Axis Reviewer

After each task implementation or fix, one `kenergy:reviewer` performs a
three-axis review:

**Spec/Goal Compliance**
- Does implementation match the requested behavior and interfaces?
- Is anything required missing, or anything unrequested added?

**Quality**
- Is the implementation correct, clear, safe where relevant, and minimal?
- Are error handling and maintainability appropriate to the task?

**Verification Adequacy**
- Can the claimed check name a production break that would make it fail?
- Does the evidence exercise the real behavior at the appropriate VDD level?
- Are the exact command and observed output recorded?

All three axes must pass, or resolve to no remaining load-bearing findings after the bounded fix loop; advisory findings may be parked with a reason.

## Anti-Patterns to Avoid

- **Jumping to code** without understanding requirements
- **Skipping verification** for "simple" changes
- **Multiple fixes at once** instead of isolated changes
- **Ignoring failed verification** or marking it as "expected"
- **Working on main** instead of feature branches
- **Claiming success** without verification evidence
- **Rationalizing shortcuts** ("just this once", "too simple to verify")
- **Accepting a check that cannot name the break** — it may not prove behavior
- **Keeping code as "reference"** instead of recording evidence for its behavior
- **"This is different because..."** — it's not different
- **"It's about the spirit, not the letter"** — the letter IS the spirit

## Philosophy in Practice

When you catch yourself thinking any of these, STOP:

| Thought | Action |
|---------|--------|
| "This is too simple to need verification" | State the claim and choose the cheapest falsifiable method. Simple changes still break. |
| "I'll decide the verification method later" | Choose the method before completion work begins; it determines what evidence is required. |
| "Quick fix, then investigate" | Investigate first |
| "It should work now" | Run the real production-relevant path and read its output. |
| "Just one more try" (after 2 failures) | Question the architecture |
| "I know what the problem is" | Prove it with evidence |
| "I already manually tested it" | Name the claim and method, then document the exact command and observed output. |
| "Deleting working code is wasteful" | Sunk cost fallacy. Keeping unverified code is debt. |
| "Need to explore first" | Fine. Treat exploration as disposable, then state the claim and select a falsifiable method. |
| "VDD will slow me down" | The cheapest real check costs less than debugging a false completion later. |
| "A green unit test proves product behavior" | Unit tests prove library behavior; use the relevant real path for non-library product behavior. |
| "I'll keep it as reference" | Reference code is not evidence. Record the result of a falsifiable check. |
| "The real path is hard to run" | That exposes a design or environment gap; find the closest falsifiable production-relevant method. |
| "VDD is dogmatic, I'm being pragmatic" | VDD is pragmatic: unverified success becomes debugging in production. |
| "This is different because..." | It's not different. The process exists because every project thinks it's different. |

## The Goal

Kenergy isn't about following rules for their own sake. It's about:

1. **Higher quality** - Fewer bugs, more reliable software
2. **Faster delivery** - Less debugging, less rework
3. **Sustainable pace** - No firefighting, no technical debt spiral
4. **Confidence** - Know the code works because you proved it

The discipline enables the speed, not the other way around.
