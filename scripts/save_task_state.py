#!/usr/bin/env python3
"""Persist the task brief and base SHA for build_like_ken.dot's SaveTaskState node.

Contract (called as: python3 scripts/save_task_state.py --task "$TASK_ID" --state-dir "$STATE_DIR")
-----------------------------------------------------------------------------------------------------
Ports recipes/single-task-pipeline.yaml's "prepare-task-state" step: write a durable task
brief and capture the base SHA once (never overwrite an existing base SHA -- it anchors every
later review package's diff range).

This node has a plain (unconditional) outgoing edge in the DOT graph -- no downstream
condition reads its stdout -- so the only hard contract is: exit 0 on success, non-zero and a
message on stderr on failure (fail-closed), and persist state at the paths save_task_state.py
computes so downstream tool_commands (build_review_package.py, write_ledger.py) can find it
by task id alone.

Reads task field values from the same uppercase env vars next_task.py just emitted into
context (TASK_GOAL, TASK_DESCRIPTION, TASK_SPEC, TASK_ACCEPTANCE, TASK_INTERFACES, TASK_FILES)
-- matching this repo's convention that a node's printed KEY=value lines become context vars
available to every later tool_command in the same run.

State layout (mirrors recipes/single-task-pipeline.yaml's task-briefs/ + .base-sha convention):
  $STATE_DIR/task-briefs/<slug>.md          -- the task brief
  $STATE_DIR/task-briefs/<slug>.base-sha    -- HEAD at first save, never overwritten
"""

from __future__ import annotations

import argparse
import os
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
        f"## Goal\n{os.environ.get('TASK_GOAL', '')}\n\n"
        f"## Description\n{os.environ.get('TASK_DESCRIPTION', '')}\n\n"
        f"## Specification\n{os.environ.get('TASK_SPEC', '')}\n\n"
        f"## Acceptance Criteria\n{os.environ.get('TASK_ACCEPTANCE', '')}\n\n"
        f"## Interfaces\n{os.environ.get('TASK_INTERFACES', '')}\n\n"
        f"## Files\n{os.environ.get('TASK_FILES', '')}\n"
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
