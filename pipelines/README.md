# Kenergy Attractor Pipelines

Attractor-shaped DOT renderings of Kenergy's six modes. Each mode is its own
top-level pipeline; each pipeline's shared, invocable knowledge is a
subgraph. Built following the doctrine in
[kenotron-ms/attractor-pipelines](https://github.com/kenotron-ms/attractor-pipelines)
(`docs/primer.md` for the *why*, `docs/RUBRIC.md` for the *checklist*) --
read those first if you're modifying anything here.

## Why these exist

`kenotron-ms/attractor-pipelines` already had a kenergy-aligned pipeline
(`pipelines/idea_to_shipped/`), but it was built against kenergy's old
three-agent review pipeline (`implementer -> verifier -> quality-reviewer`)
and an old plan-approval gate that no longer exists. Rather than patch that
one big SDLC-arc pipeline, this set restructures the same real behavior as
six independent top-level graphs -- one per mode -- so each can be pointed at
directly (`git+https://...#subdirectory=pipelines/build_like_ken/build_like_ken.dot`)
without pulling in the whole lifecycle.

## Design order, applied to every graph here

Per `docs/primer.md` §3, every graph below was designed in this order, not
"write the steps and hope for a basin":

1. **Name the sink** -- what command, run by a machine, proves this mode's
   goal is actually done?
2. **Build the gate** -- a deterministic node that checks the sink, never a
   box node's own claim.
3. **Build the loop** -- failure routes back to whichever phase can actually
   fix it.
4. **Only then** were the work nodes written.

Each `.dot` file's header comment states its sink/gate/loop explicitly so
this isn't left implicit.

## The six top-level graphs, standalone

Each of these runs on its own -- point the attractor bundle at it directly
via its own `git+https://...#subdirectory=pipelines/<name>/<name>.dot` URL
without pulling in the rest of the lifecycle.

| Graph | Mode | Sink |
|---|---|---|
| `build_like_ken/build_like_ken.dot` | `/build-like-ken` | Reviewer verdict independently confirmed against real `git log`, not the reviewer's own claim |
| `think_like_ken/think_like_ken.dot` | `/think-like-ken` | Design doc self-reviewed + adversarially reviewed + explicitly approved before delegation |
| `plan_like_ken/plan_like_ken.dot` | `/plan-like-ken` | Plan file demonstrably contains every field the executor requires, confirmed by grep, not by the plan-writer's claim |
| `debug/debug.dot` | `/debug` | Original reproduction re-run fresh and confirmed gone, independent of the fix agent's claim |
| `verify/verify.dot` | `/verify` | All four checks backed by real captured command output, held to the bar by the kenergy skill's post-work gate |
| `finish/finish.dot` | `/finish` | Chosen action (merge/PR/keep/discard) independently confirmed against real Git/GitHub state |

## The seventh graph: the full cycle, composed

`kenergy_full_cycle/kenergy_full_cycle.dot` -- the master orchestrator that
composes all six mode-graphs above into the complete idea-to-finish arc,
mirroring `kenergy-reference/SKILL.md`'s own manual-path diagram:

```text
/think-like-ken -> /plan-like-ken -> /build-like-ken -> /verify (recommended) -> /finish
```

with `/debug` reachable as shared recovery from both a blocked build and
unverified evidence, and a human `ResumeRoute` hexagon deciding whether a
fix resumes the build, the plan, or the design -- matching `debug.md`'s own
Dynamic Transitions guidance, which leaves that call to a human rather than
a file-state gate.

Named after `recipes/kenergy-full-development-cycle.yaml` deliberately --
same lifecycle, DOT rendering instead of recipe YAML.

**Composition mechanics:** the six mode-graphs and their five skill-subgraphs
are duplicated into `kenergy_full_cycle/subgraphs/` and
`kenergy_full_cycle/subgraphs/subgraphs/` respectively, preserving each
graph's *exact original relative folder depth* to its own subgraphs (e.g.
`build_like_ken.dot`'s `dot_file="subgraphs/kenergy_reality_check.dot"`
resolves identically whether the file lives at
`build_like_ken/build_like_ken.dot` or here at
`kenergy_full_cycle/subgraphs/build_like_ken.dot` -- both have a sibling
`subgraphs/` folder one level down). One canonical copy of each mode's logic,
reused two ways: standalone, and composed here. This is the same reuse
discipline `docs/RUBRIC.md` §5 already requires for `deliver_pr.dot`, applied
one level deeper.

**The one new foot-gun this composition specifically has to dodge**
(`docs/RUBRIC.md` §3.7): a `shape=folder` subgraph node silently returns its
*last internal outcome* to the parent graph even when nothing meaningful
happened inside it. `CheckBuildVerdict` and `CheckVerifyVerdict` exist
specifically so this graph never treats "the `BuildLikeKen` node returned"
as success -- both explicitly read the context field
(`context.build.verdict`, `context.verify.verdict`) each subgraph is
contracted to write before routing anywhere.

## Skill-to-subgraph mapping

Of this bundle's eight skills, five have genuine invocable steps and became
subgraphs. Three did not -- forcing them into subgraph form would have been
exactly the unnecessary structure `cranky-old-sam`'s own skill argues
against, so they're accounted for differently:

| Skill | Becomes | Where |
|---|---|---|
| `kenergy` | `kenergy_reality_check.dot` subgraph (pre-work + post-work modes) | `build_like_ken/subgraphs/`, `verify/subgraphs/` |
| `scenario-verification` | `scenario_verification.dot` subgraph | `build_like_ken/subgraphs/`, `verify/subgraphs/` |
| `integration-testing-discipline` | `integration_testing_gate.dot` subgraph | `build_like_ken/subgraphs/` |
| `cranky-old-sam` | `cosam_lens.dot` subgraph (inline, not a separate dispatch) | `think_like_ken/subgraphs/` |
| `crusty-old-engineer` | `coe_lens.dot` subgraph (inline, not a separate dispatch) | `think_like_ken/subgraphs/` |
| `vdd-walkthrough` | **Not a subgraph.** It's the spec `build_like_ken.dot`'s own nodes render -- the graph IS the DOT-ification, not an invocation of the doc. |
| `kenergy-reference` | **Not a subgraph.** Master reference table consulted while authoring every graph above; it has no invocable steps of its own. |
| `voice-check` | **Not mapped.** Blog-post voice/anti-slop judge -- doesn't fit any of the six dev-workflow modes' actual flow. Forcing a subgraph here for the sake of "every skill gets one" would itself be the kind of unnecessary structure this bundle's own simplicity lens exists to catch. |

## Shared subgraph duplication

`kenergy_reality_check.dot` and `scenario_verification.dot` are duplicated
(not symlinked) into both `build_like_ken/subgraphs/` and `verify/subgraphs/`
-- this matches `attractor-pipelines`' own convention (its `deliver_pr.dot` is
duplicated identically across `hello_world/`, `idea_to_shipped/`, and
`ship_ready/`), since each pipeline folder is fetched independently via its
own `git+https://` subdirectory URL and `dot_file=` paths resolve relative to
the fetching pipeline's own folder, not across pipelines.

**If you fix a bug in one copy, fix it in the other too** -- per
`docs/RUBRIC.md` §5's reuse discipline, check every consumer of a shared
subgraph, not just the one that surfaced the bug.

## Foot-guns specifically audited against, repo-wide

- **No `shape=diamond` anywhere.** Every branch is `shape=parallelogram` +
  `condition="context.tool.last_line=..."`.
- **Every claimed external side effect has an independent verification
  node downstream** reading real state (git log, `gh pr view`, a written
  JSON file) -- never a box node's own printed claim. This is the
  self-reported-claims-not-evidence rule `docs/RUBRIC.md` §2 exists because
  of a real, repeated bug class in the upstream repo.
- **`fidelity="full"` is used only where a human's own freeform reply is
  being routed on** (approval/discard-confirmation gates) -- everywhere else,
  gates read files, never truncated `$last_response` prose.
- **Every loop is bounded and the bound is a decision point**, not a fuse:
  `build_like_ken.dot`'s five-fix/six-review cap adjudicates (park advisory,
  block load-bearing); `debug.dot`'s 3-attempt cap escalates to a human
  architecture question; `verify.dot`'s 2-round evidence-gathering cap
  reports NOT VERIFIED and hands off to `/debug`.

## What's still a stub

Every `tool_command` that shells out to a `scripts/*.py` helper (e.g.
`scripts/next_task.py`, `scripts/confirm_plan_contract.py`,
`scripts/capture_entry_paths.py`) names the exact contract that script must
satisfy in its surrounding node, but the scripts themselves are not yet
written -- they're the deterministic-gate equivalent of kenergy's real
Python-in-YAML logic already proven in `recipes/single-task-pipeline.yaml`,
`recipes/subagent-driven-development.yaml`, and `recipes/finish-branch.yaml`.
Porting that logic into standalone scripts callable from these `.dot` files
is the next real step before these pipelines can actually run end to end.
