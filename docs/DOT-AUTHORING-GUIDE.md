# DOT Authoring Guide

Guidance for authors adding or reviewing `tool_command` nodes in Kenergy's
attractor `.dot` pipelines. Start here before adding any node with internal
`if`/`else`/`case` branching.

## The Q1/Q2 Rule: No Embedded Routing Logic

A pipeline's real control flow must be visible as DOT graph edges, not buried
inside a shell or python `tool_command` script. If a script internally
decides which of several semantically different downstream paths to take,
that decision is a hidden fork the topology diagram can never show — and it
can silently drift out of sync with the visible edges (see
`docs/designs/kenergy-pipeline-embedded-routing-logic.md` for the bug class
this rule was written to prevent).

Apply this two-part test to every `tool_command` node that contains internal
`if`/`case` logic:

**Q1 — Is the branch value already decided elsewhere?**
Is the value an existing enum or boolean produced upstream (an LLM box node's
JSON write, or a human hexagon's own fixed `options=` choice)? If the shell
only reads and re-emits that value verbatim — as a route token, or with an
existence/threshold check — it is translation/validation, and is legitimate.
If the shell *invents* new classification or synthesis itself, that is a
decision that does not belong in a shell script, and is suspect.

**Q2 — Do the branches produce different semantic payloads for the same
downstream node?**
Does every branch emit a different semantic payload aimed at the SAME
downstream node, where the branches are also distinguishable by *which
upstream caller/edge* produced the input? If yes, this is the anti-pattern:
the graph already has the topology to know why we are here, and recomputing
it in a script duplicates that information while hiding a real fork from the
diagram.

### One-line test

> If I deleted the DOT edges and looked only at the shell script, would I
> discover a NEW fork in the workflow that isn't already visible as multiple
> incoming edges or multiple existing upstream-written enum values?

Yes = hidden routing, split it out. No = legitimate deterministic gate, keep it.

### Corollary: always-legitimate patterns

The following are always legitimate under this rule, because they re-derive
ground truth rather than deciding business meaning:

- numeric/bounded-retry checks (`count < N`)
- existence and well-formedness checks
- "does the file the previous node claims to have written actually contain
  what it claims" checks

## Worked Examples

**Hidden routing (anti-pattern):** a `python3` one-liner computes a 4-way
classification from two independent upstream booleans, but only 3 of the 4
possible outputs have a matching DOT edge. Fix: replace the combinatorial
gate with two sequential independent boolean gates, each a trivial one-line
JSON emit with no `if`.

**Hidden routing (anti-pattern):** a bash `case` statement collapses four
semantically distinct upstream outcomes into a binary artifact check,
discarding real business-meaningful distinctions. Fix: expose an explicit
gate node with one edge per real outcome.

**Legitimate gate:** a case statement validates a human's freeform-adjacent
reply against an already-fixed `options=` enum and only echoes matched values
or `invalid`. All real dispatching happens via separately DOT-conditioned
edges downstream, not inside the shell.

## When Adding a New `tool_command` Node

Before adding any node with internal branching, apply the Q1/Q2 test above.
If it fails (hidden routing), split the decision out into an explicit
`shape=parallelogram` gate with `condition=` edges — one edge per real
outcome — so the diagram shows every fork a reader would otherwise have to
discover by opening the script.
