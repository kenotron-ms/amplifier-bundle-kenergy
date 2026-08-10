#!/usr/bin/env python3
"""Deterministic cycle counter for think_like_ken.dot's AdversarialGate node.

Contract (called as:
  python3 scripts/bump_cycle.py --state-file "${execution_root}/.resolve/design/adversarial_cycle.count"
)
Prints a single JSON object: {"cycle": <int>}.

------------------------------------------------------------------------------
Replaces a prior scheme where the review loop's own cycle count was
self-reported by the LLM into adversarial_review.json (a "cycle" key inside the
same file the model was asked to write its pass/fail verdict to). A value the
loop body itself invents is not a cap -- observed in production: at execution
#14 the model wrote {"cycle": 1} again, so `d['cycle'] >= 3` never tripped and
the loop ran unbounded (in one Resolve instance: 27 SelfReview + 17
AdversarialReview + 27 FixSelfReview executions over ~80 minutes).

This script durably increments a plain integer counter file OUTSIDE the
model's own JSON write, exactly once per AdversarialGate execution (which runs
exactly once per full loop iteration: AdversarialReview -> AdversarialGate).
The gate then combines this deterministic cycle count with the model's
self-reported pass/fail verdict (verdict content, unlike a loop-bound counter,
is legitimately the model's judgment call) -- see AdversarialGate's
tool_command in think_like_ken.dot.

Mirrors bump_round.py's pattern (build_like_ken.dot's CheckRound node): a
plain integer file, created at 1 on first call, incremented by 1 on every
subsequent call, fail-closed on corruption -- never silently reset to 1,
which would let the loop quietly bypass its own bound.

State: <state-file> -- a plain integer. Scoped to a single design review (one
file per pipeline run), unlike bump_round.py's per-task scoping, since
think_like_ken.dot reviews exactly one design document per execution.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def fail(message: str) -> None:
    print(f"BLOCKED: {message}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-file", required=True)
    args = parser.parse_args()

    state_path = Path(args.state_file).expanduser()
    state_path.parent.mkdir(parents=True, exist_ok=True)

    if state_path.exists():
        raw = state_path.read_text(encoding="utf-8").strip()
        if not raw.isdigit():
            fail(f"cycle state file is corrupt (not an integer): {state_path} = {raw!r}")
        count = int(raw) + 1
    else:
        count = 1

    state_path.write_text(str(count) + "\n", encoding="utf-8")

    print(json.dumps({"cycle": count}))


if __name__ == "__main__":
    main()
