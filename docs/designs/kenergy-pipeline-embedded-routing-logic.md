# Eliminating Embedded Routing Logic in Kenergy Attractor Pipelines

## Goal

Eliminate hidden/embedded routing logic in the kenergy attractor pipelines — the six
mode-graphs (`think_like_ken`, `plan_like_ken`, `build_like_ken`, `verify`, `debug`,
`finish`, composed by `kenergy_full_cycle.dot`) — so that every genuine branching
decision is visible as a DOT graph edge rather than buried inside a shell or python
`tool_command` script.

## Problem

The kenergy pipelines recently went through a 4-commit bug chain (`895badd`, `5dba995`,
`0d2c2ad`, `f5da802`) caused by context-key naming mismatches between folder-node
`outputs=` merges (exact flat-string-key lookup, no dot-nesting) and downstream
substitution tokens. That specific bug class is now fixed.

A structurally similar risk remains one layer up, at routing. Some `tool_command` nodes
contain `if`/`else` or `case`-statement logic that decides which of several semantically
different downstream paths to take, instead of that decision being expressed as DOT
`condition=` edges. The consequence: the graph's real control flow is invisible to anyone
reading the topology diagram. You have to open shell scripts to discover forks that the
picture never shows.

The failure mode this invites is the same one the key-naming chain exhibited — a script's
internal branch space drifting silently out of sync with the visible edges, with nothing
in the diagram to catch it.

### Evidence base and its limits

There is currently **zero** session/telemetry corpus for any of these pipelines —
confirmed via a context-intelligence graph query returning 0 of 13,182 sessions. Every
finding below comes from static/structural review of the `.dot` files themselves, not from
empirical failure data. This constrains confidence and drives the verification plan in
[Testing / Verification](#testing--verification).

## Evidence: the mechanical rule

A two-part test was applied to every `tool_command` node containing internal `if`/`case`
logic.

**Q1 — Is the branch value already decided elsewhere?**
Is the value an existing enum or boolean produced upstream (an LLM box node's JSON write,
or a human hexagon's own fixed `options=` choice)? If the shell only reads and re-emits
that value verbatim — as a route token, or with an existence/threshold check — it is
translation/validation, and is legitimate. If the shell *invents* new classification or
synthesis itself, that is a decision that does not belong in a shell script, and is
suspect.

**Q2 — Do the branches produce different semantic payloads for the same downstream node?**
Does every branch emit a different semantic payload aimed at the SAME downstream node,
where the branches are also distinguishable by *which upstream caller/edge* produced the
input? If yes, this is the anti-pattern: the graph already has the topology to know why we
are here, and recomputing it in a script duplicates that information while hiding a real
fork from the diagram.

**One-line test:**

> If I deleted the DOT edges and looked only at the shell script, would I discover a NEW
> fork in the workflow that isn't already visible as multiple incoming edges or multiple
> existing upstream-written enum values?

Yes = hidden routing, split it out. No = legitimate deterministic gate, keep it.

**Corollary.** The following are always legitimate under this rule, because they re-derive
ground truth rather than deciding business meaning:

- numeric/bounded-retry checks (`count < N`)
- existence and well-formedness checks
- "does the file the previous node claims to have written actually contain what it claims"
  checks

## Findings

Roughly 14 candidate `if`/`else`/`case` instances were audited across all six pipelines
plus the composed `kenergy_full_cycle.dot`. Three are genuine instances of the
anti-pattern.

### Confirmed instances

| # | Location | Nature of the hidden fork |
|---|----------|---------------------------|
| 1 | `kenergy_full_cycle.dot` / `RenameBugDescriptionForDebug` | Two different narrative payloads into the same `Debug` node |
| 2 | `think_like_ken.dot` / `DecisionRoute` | 4-way classification computed in python; one outcome has no edge |
| 3 | `build_like_ken.dot` / `ImplementArtifactGate` | Four implementer outcomes collapsed into a binary artifact check |

#### 1. `kenergy_full_cycle.dot` / `RenameBugDescriptionForDebug`

Branches on `build.blocked_task_id` being non-empty to write one of two semantically
different narrative messages — a "build-blocked task" story versus a "verify gap" story —
into the same downstream `Debug` node. The two cases are already distinguishable by which
upstream edge delivered control.

**Fix:** split into `RenameBugDescriptionForBuildBlocked` and
`RenameBugDescriptionForVerifyGap`, wired respectively from `CheckBuildVerdict`'s
`blocked` edge and `CheckVerifyVerdict`'s `not_verified` edge. Each becomes a trivial
one-line JSON emit with no `if`.

#### 2. `think_like_ken.dot` / `DecisionRoute`

A `python3` one-liner computes a 4-way classification (`both` / `simplicity` /
`consequence` / `none`) from two independent booleans — `needs_simplicity_lens` and
`needs_consequence_lens` — that were already decided by `SynthesizeDecisions`.

Only 3 of the 4 possible outputs have a matching DOT edge today. **`both` has no edge.**
If the LLM ever sets both flags true, the engine hits a fail-loud "no matching edge"
runtime error. This is a live, currently-uncaught bug of exactly the predicted shape: the
shell's internal branch space has silently drifted out of sync with the visible edges.

**Fix:** replace the combinatorial gate with two sequential independent boolean gates:

```
NeedsSimplicityLens?  --true-->  SimplicityLens  --> NeedsConsequenceLens?
                      --false-------------------->  NeedsConsequenceLens?

NeedsConsequenceLens? --true-->  ConsequenceLens --> ConsolidatedReview
                      --false-------------------->  ConsolidatedReview
```

`SimplicityLens` falls through to the consequence-check node rather than straight to
`ConsolidatedReview`. This represents all 4 real combinations using only 2-way gates and
eliminates the combinatorial case statement entirely.

#### 3. `build_like_ken.dot` / `ImplementArtifactGate`

A bash `case` statement collapses four semantically distinct implementer outcomes —
`DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, `BLOCKED` — into a binary `ok`/`missing`
artifact check. `NEEDS_CONTEXT` and `BLOCKED` are routed down the identical path as a
normal `DONE`, into `RouteVerificationLevel`/review. Real business-meaningful distinctions
are discarded inside the case statement.

**Fix:** split into an explicit `ImplementOutcomeGate` with three edges:

- `done` — `DONE`/`DONE_WITH_CONCERNS` → `RouteVerificationLevel`, after the existing
  sha/artifact check
- `needs_context` — → human/escalation or re-implement branch
- `blocked` — → directly to the ledger-blocked path, skipping review entirely

### Confirmed legitimate (no change required)

All other audited candidates pass the rule as deterministic gates:

`ForkGate`, `CheckConsolidatedApproval`, `AdversarialGate`, `DetermineAction`
(`finish.dot`), `CheckDiscardConfirmation`, `verify.dot`'s `OverallGate` and
`CheckRetryCount`, `debug.dot`'s `CheckAttemptCount`, and the various
`*ArtifactGate`/Ledger/Preflight gates across all graphs.

`DetermineAction` in `finish.dot` deserves a note: its case statement looks suspicious at
first glance, but it validates a human's freeform-adjacent reply against an already-fixed
`options=` enum and only echoes matched values or `invalid`. All real dispatching happens
via 5 separate DOT-conditioned edges downstream, not inside the shell. Legitimate.

### Unauditable from the DOT alone

`build_like_ken.dot`'s `ComputeBuildVerdictBlocked` / `ComputeBuildVerdictComplete` shell
out to `scripts/compute_build_verdict.py` with no inline branching in the `.dot` file
itself. Presumed legitimate based on name and header comments, but the same Q1/Q2 test
should be applied directly to that script as follow-up.

## Approach

1. **Fix the 3 confirmed instances**, in priority order:
   1. `#2 DecisionRoute` first — it carries a live uncaught runtime bug (the missing
      `both` edge).
   2. `#1 RenameBugDescriptionForDebug`.
   3. `#3 ImplementArtifactGate`.
2. **Document the mechanical rule** (the Q1/Q2 test above) either as a comment block in
   each pipeline's header or in a shared `docs/DOT-AUTHORING-GUIDE.md` section, so future
   node authors have a canonical test to apply before adding any `tool_command` with
   internal branching. See [Open Questions](#open-questions).
3. **Apply the same Q1/Q2 test** to `scripts/compute_build_verdict.py` and
   `scripts/bump_round.py` as external-script follow-up. Out of scope for the `.dot`
   changes themselves; tracked separately.
4. **Execute one real end-to-end run**, forcing at least the `DecisionRoute` `both` case
   and one Debug-loop iteration, to convert this from purely static analysis into
   empirically validated fixes.

## Changes

| File | Change |
|------|--------|
| `kenergy_full_cycle.dot` | Replace `RenameBugDescriptionForDebug` with `RenameBugDescriptionForBuildBlocked` + `RenameBugDescriptionForVerifyGap`; rewire from `CheckBuildVerdict.blocked` and `CheckVerifyVerdict.not_verified` |
| `think_like_ken.dot` | Replace `DecisionRoute` with two sequential boolean gates (`NeedsSimplicityLens?`, `NeedsConsequenceLens?`); rewire `SimplicityLens` fall-through to the consequence check |
| `build_like_ken.dot` | Replace `ImplementArtifactGate`'s collapsing case with an explicit `ImplementOutcomeGate` exposing `done` / `needs_context` / `blocked` edges |
| Authoring docs | Record the Q1/Q2 rule (location per open question) |

## Risks

- Splitting `DecisionRoute` into two sequential gates changes topology (adds one more
  traversal). Must confirm that `SimplicityLens`/`ConsequenceLens` fall-through wiring does
  not skip `ConsolidatedReview` on any path.
- No pipeline has ever been run and captured in context-intelligence, so these fixes remain
  unverified against real execution until step 4 (the end-to-end run) happens.
- `attractor lint` must be re-run against every edited file after changes.

## Testing / Verification

- `attractor lint` on all edited `.dot` files — all 4 must report OK.
- One live end-to-end run through `kenergy_full_cycle.dot`, forcing:
  - the `DecisionRoute` `both` case;
  - a `build.verdict=blocked` path through the new split
    `RenameBugDescriptionForBuildBlocked`;
  - if reachable, a `NEEDS_CONTEXT`/`BLOCKED` implementer outcome through the new
    `ImplementOutcomeGate`.

## Open Questions

- Should the Q1/Q2 mechanical rule live in `docs/DOT-AUTHORING-GUIDE.md` as a permanent
  lint-adjacent authoring guideline, or stay as inline header comments per-pipeline?
  Recommendation: the former, for reuse beyond kenergy.
- Should `scripts/compute_build_verdict.py` and `scripts/bump_round.py` be audited now, or
  tracked as separate follow-up work?
