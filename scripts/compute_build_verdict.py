#!/usr/bin/env python3
"""Build verdict computation for build_like_ken.dot's ComputeBuildVerdict node.

Contract (called as:
  python3 scripts/compute_build_verdict.py --ledger "${ledger_path}" [--blocked-task "${task_id}"]
)
------------------------------------------------------------------------------
build_like_ken.dot's own header documents context outputs build.verdict /
build.tasks_completed / build.blocked_task_id, and both Report and the parent
kenergy_full_cycle.dot's CheckBuildVerdict gate read them -- but no node ever
actually wrote them (a real, silent sharp edge: the "Report" box node's prompt
merely *referenced* ${build.tasks_completed}/${build.verdict} as if some prior
node had set them; none had). This script is the deterministic writer that
closes that gap, invoked immediately before Report (all-tasks-complete path)
and before Blocked (blocked path).

Reads the same ledger.md the whole build loop maintains and counts safe
completion entries (mirrors next_task.py's own SAFE_OUTCOMES check, without
re-deriving ancestor-of-HEAD each time -- the loop's own gates already only
ever write a safe entry after independent confirmation).

Output (single line, parse_json="true" on the calling node -- keys are the exact dotted
context keys build_like_ken.dot's own header documents as this graph's outputs):
  {"build.verdict": "all_tasks_complete", "build.tasks_completed": <int>}
  {"build.verdict": "blocked", "build.tasks_completed": <int>, "build.blocked_task_id": "task-N"}

Fail-closed: missing ledger is a hard error -- never silently reports zero
tasks completed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SAFE_OUTCOMES = {"PASS", "APPROVED_WITH_PARKED"}
LEDGER_ENTRY_RE = re.compile(
    r"^- \[x\] (?P<task>.+?) \u2014 (?P<sha>[0-9a-f]{7,64}) \u2014 (?P<outcome>.+)$"
)


def fail(message: str) -> None:
    print(f"BLOCKED: {message}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--blocked-task", default="")
    args = parser.parse_args()

    ledger_path = Path(args.ledger).expanduser()
    if not ledger_path.is_file():
        fail(f"ledger not found: {ledger_path}")
        return

    completed = 0
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        match = LEDGER_ENTRY_RE.match(line)
        if match and match.group("outcome") in SAFE_OUTCOMES:
            completed += 1

    blocked_task = args.blocked_task.strip()
    if blocked_task:
        print(
            json.dumps(
                {
                    "build.verdict": "blocked",
                    "build.tasks_completed": completed,
                    "build.blocked_task_id": blocked_task,
                }
            )
        )
    else:
        print(
            json.dumps(
                {"build.verdict": "all_tasks_complete", "build.tasks_completed": completed}
            )
        )


if __name__ == "__main__":
    main()
