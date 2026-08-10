# pipelines/goals — goaltractor infrastructure

This directory holds the runnable building blocks for the `/goaltractor` skill
(`skills/goaltractor/SKILL.md`).

## What goaltractor does

`/goaltractor` takes a pile of work — issues, design docs, a big feature —
and compiles it into one attractor `.dot` pipeline: batched,
dependency-ordered, parallel `/goal` execution, runnable locally or
submitted once to a remote resolve service (`dot-graph` resolver). See the
skill file for the full interactive flow (decomposition → batch plan review
→ compile → execution target → monitor).

**Prerequisite for remote submission:** a resolve service must already be
reachable before you can submit to it. The Amplifier app CLI reaches one via
the `bundle-resolve` bundle; other agents (delegated sub-agents, non-CLI
callers) should use the resolve MCP server rather than driving HTTP calls by
hand. Without one of these configured, `/goaltractor` falls back to local
execution.

## Files here

### `goal_runner.dot`

The reusable per-goal worker sub-pipeline. Every `/goaltractor`-compiled
pipeline references this via `folder`-shape nodes:

```dot
SomeGoal [
    shape=folder,
    dot_file="goal_runner.dot",
    context.goal="<the goal text, including its Definition of Done>",
    context.output_file="path/to/expected/artifact.md",
    context.min_words="300"
]
```

It implements the standard attractor convergence-loop pattern:

```
implement -> evidence gate (file exists + word-count floor) -> retry-on-fail
```

The gate is mechanical, not an LLM self-report: it checks the filesystem
(`test -f` + `wc -w`) and routes back to `implement` with the failure reason
in `gate_output.txt` if the artifact is missing or too thin. This is what
makes the loop an actual attractor rather than a hope that the worker did
the right thing.

**Verified:** lints clean with `attractor lint`, and has been run end-to-end
producing real multi-thousand-word artifacts that passed the gate.

## How a compiled pipeline uses this

A `/goaltractor`-authored pipeline is typically shaped like:

```dot
Batch1 [shape=component, max_parallel="N"]   // parallel goals in this batch
Goal_a [shape=folder, dot_file="goal_runner.dot", context.goal="..."]
Goal_b [shape=folder, dot_file="goal_runner.dot", context.goal="..."]
Join1  [shape=tripleoctagon]                 // fan-in
Check1 [shape=hexagon]                       // optional human checkpoint
Batch2 [shape=folder, dot_file="goal_runner.dot", ...]  // next batch, depends on Join1
Final  [shape=folder, dot_file="goal_runner.dot", ...]  // integration/review
```

`goaltractor` itself doesn't ship example/demo pipelines in this repo —
those are generated per-use into the target repo you're compiling work for,
not committed here. `goal_runner.dot` is the one piece of shared
infrastructure every compiled pipeline depends on, so it lives here
permanently.

## Running a compiled pipeline

```bash
attractor lint pipelines/goals/<your-compiled-pipeline>.dot
attractor run pipelines/goals/<your-compiled-pipeline>.dot --cwd <target-dir>
```

Drop `--on-human-gate auto-approve` if you want to actually stop and answer
any `hexagon` checkpoints interactively (the default `console` mode will
prompt you).

## Related

- `skills/goaltractor/SKILL.md` — the skill itself (decomposition, batching,
  compilation, execution-target selection)
- `behaviors/goaltractor.yaml` — standalone behavior that wires just this
  skill (and points at `goal_runner.dot`) without pulling in the rest of
  kenergy's workflow stack; see its own comments for composition details
