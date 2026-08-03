#!/usr/bin/env python3
"""Round counter for build_like_ken.dot's CheckRound node.

Contract (called as:
  count=$(python3 scripts/bump_round.py --state-dir "$STATE_DIR" --task "$TASK_ID")
  if   [ "$count" -le 3 ]; then printf 'resume'
  elif [ "$count" -le 5 ]; then printf 'escalate'
  else printf 'adjudicate'
  fi
)
------------------------------------------------------------------------------
The calling shell owns the resume/escalate/adjudicate routing decision; this
script's sole job is to durably increment and return the round count as a bare
integer on stdout, matching recipes/single-task-pipeline.yaml's review-fix loop
bound: rounds 1-3 resume the original implementer, rounds 4-5 escalate to a
fresh implementer, round 6 is adjudication-only (RUBRIC.md's "the round
counter is a decision point, not a fuse").

State: $STATE_DIR/task-briefs/<task-slug>.round -- a plain integer, created at
1 on first call for a task and incremented by 1 on every subsequent call.
Round state is scoped per task (not global) so concurrent/sequential tasks in
the same plan never share a counter.

Fail-closed: a corrupt (non-integer) existing round file is a hard error --
never silently reset to 1, which would let a task quietly bypass the bound.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def fail(message: str) -> None:
    print(f"BLOCKED: {message}", file=sys.stderr)
    sys.exit(1)


def slugify(task_id: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", task_id.lower()).strip("-")
    if not slug:
        fail(f"task id produced an empty slug: {task_id!r}")
    return slug


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--task", required=True)
    args = parser.parse_args()

    slug = slugify(args.task.strip())
    briefs_dir = Path(args.state_dir).expanduser() / "task-briefs"
    briefs_dir.mkdir(parents=True, exist_ok=True)
    round_path = briefs_dir / f"{slug}.round"

    if round_path.exists():
        raw = round_path.read_text(encoding="utf-8").strip()
        if not raw.isdigit():
            fail(
                f"round state file is corrupt (not an integer): {round_path} = {raw!r}"
            )
        count = int(raw) + 1
    else:
        count = 1

    round_path.write_text(str(count) + "\n", encoding="utf-8")
    print(count)


if __name__ == "__main__":
    main()
