#!/usr/bin/env python3
"""Persist the task brief and base SHA for build_like_ken.dot's SaveTaskState node.

Contract (called as:
  python3 scripts/save_task_state.py --task "${task_id}" --state-dir "${state_dir}" \
    --goal "${task_goal}" --description "${task_description}" --spec "${task_spec}" \
    --acceptance "${task_acceptance}" --interfaces "${task_interfaces}" --files "${task_files}"
)
-----------------------------------------------------------------------------------------------------
Ports recipes/single-task-pipeline.yaml's "prepare-task-state" step: write a durable task
brief and capture the base SHA once (never overwrite an existing base SHA -- it anchors every
later review package's diff range).

This node has a plain (unconditional) outgoing edge in the DOT graph -- no downstream
condition reads its stdout -- so the only hard contract is: exit 0 on success, non-zero and a
message on stderr on failure (fail-closed), and persist state at the paths save_task_state.py
computes so downstream tool_commands (build_review_package.py, write_ledger.py) can find it
by task id alone.

Task field values arrive as ${task_...} tool_command substitution tokens (populated in
context by NextTask's parse_json="true" JSON object) -- NOT as uppercase environment
variables. An earlier revision of this script read os.environ.get("TASK_GOAL", ...) etc. on
the assumption the engine exports context keys as env vars automatically; it does not (see
next_task.py's contract note) -- those environment reads always silently returned "". Fixed
by taking every field as an explicit CLI flag, substituted directly into tool_command by the
engine's ${key} substitution before this script ever runs.

State layout (mirrors recipes/single-task-pipeline.yaml's task-briefs/ + .base-sha convention):
  $STATE_DIR/task-briefs/<slug>.md          -- the task brief
  $STATE_DIR/task-briefs/<slug>.base-sha    -- HEAD at first save, never overwritten
"""

from __future__ import annotations

import argparse
import re
import subprocess
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
    parser.add_argument("--task", required=True)
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--goal", default="")
    parser.add_argument("--description", default="")
    parser.add_argument("--spec", default="")
    parser.add_argument("--acceptance", default="")
    parser.add_argument("--interfaces", default="")
    parser.add_argument("--files", default="")
    args = parser.parse_args()

    task_id = args.task.strip()
    if not task_id:
        fail("--task is empty")

    slug = slugify(task_id)
    state_dir = Path(args.state_dir).expanduser()
    briefs_dir = state_dir / "task-briefs"
    briefs_dir.mkdir(parents=True, exist_ok=True)

    brief_path = briefs_dir / f"{slug}.md"
    base_path = briefs_dir / f"{slug}.base-sha"

    brief = (
        f"# Task Brief: {task_id}\n\n"
        f"## Goal\n{args.goal}\n\n"
        f"## Description\n{args.description}\n\n"
        f"## Specification\n{args.spec}\n\n"
        f"## Acceptance Criteria\n{args.acceptance}\n\n"
        f"## Interfaces\n{args.interfaces}\n\n"
        f"## Files\n{args.files}\n"
    )
    brief_path.write_text(brief, encoding="utf-8")

    if not base_path.exists():
        try:
            head_sha = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True
            ).strip()
        except subprocess.CalledProcessError as error:
            fail(f"unable to resolve HEAD for base SHA capture: {error}")
            return
        if not head_sha:
            fail("git rev-parse HEAD returned an empty SHA")
            return
        base_path.write_text(head_sha + "\n", encoding="utf-8")

    print(f"task_brief_saved:{brief_path}")


if __name__ == "__main__":
    main()
