#!/usr/bin/env python3
"""Deterministic task selection for build_like_ken.dot's NextTask node.

Contract (called as: python3 scripts/next_task.py --plan "$PLAN_PATH" --ledger "$LEDGER_PATH")
-----------------------------------------------------------------------------------------------
Ports the task-selection logic proven in recipes/subagent-driven-development.yaml and
recipes/single-task-pipeline.yaml's "check-task-complete" step: a task only counts as done
when the ledger has a safe-outcome entry (PASS or APPROVED_WITH_PARKED) whose commit sha is
a real ancestor of HEAD -- never a bare "it's mentioned in the ledger" check.

Plan format (agents/plan-writer.md, authoritative):
  ### Task N: <Component Name>
  **Description:** ...
  **Goal:** ...
  **Specification:** ...
  **Acceptance Criteria:** ...
  **Files:** ...
  **Interfaces:**
  - Consumes: ...
  - Produces: ...
  **Model Roles:**
  - implementation_model_role: ...
  - review_model_role: ...
  - escalated_model_role: ...

task_id is deterministically derived as "task-N" from the "### Task N:" header -- the plan
document does not carry a separate free-text task_id field for the DOT path (unlike the
recipe path, where plan-writer's own agent output supplies task_id directly).

Output contract
---------------
On success (a task remains): prints "KEY=value" lines for every field the downstream nodes
need (matching this repo's $VAR / ${var} convention -- uppercase env keys map 1:1 to the
lowercase context vars referenced in build_like_ken.dot's prompts), then a final line with
the routing token the NextTask edges match on:

  TASK_ID=task-3
  TASK_GOAL=...
  TASK_DESCRIPTION=...
  TASK_SPEC=...
  TASK_ACCEPTANCE=...
  TASK_INTERFACES=...
  TASK_FILES=...
  TASK_IMPLEMENTATION_MODEL_ROLE=coding
  TASK_REVIEW_MODEL_ROLE=critique
  TASK_ESCALATED_MODEL_ROLE=reasoning
  STATE_DIR=/abs/path/.kenergy/sdd/<plan-slug>
  has_task

When the plan is exhausted (every task has a safe, ancestor-confirmed ledger entry), prints
exactly one line: "no_tasks".

Fail-closed: a missing plan file, a plan with zero parsed tasks, or a ledger identity mismatch
is a hard error (non-zero exit, message on stderr) -- never silently treated as "no_tasks".
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

SAFE_OUTCOMES = {"PASS", "APPROVED_WITH_PARKED"}
LEDGER_ENTRY_RE = re.compile(
    r"^- \[x\] (?P<task>.+?) \u2014 (?P<sha>[0-9a-f]{7,64}) \u2014 (?P<outcome>.+)$"
)
TASK_HEADER_RE = re.compile(r"^###\s+Task\s+(\d+)\s*:\s*(.*)$", re.MULTILINE)
FIELD_LABELS = [
    "Description",
    "Goal",
    "Specification",
    "Acceptance Criteria",
    "Files",
    "Interfaces",
    "Model Roles",
]


def fail(message: str) -> None:
    print(f"BLOCKED: {message}", file=sys.stderr)
    sys.exit(1)


def extract_field(block: str, label: str) -> str:
    pattern = re.compile(
        rf"\*\*{re.escape(label)}:\*\*\s*(.*?)(?=\n\*\*[A-Za-z][A-Za-z ]*:\*\*|\n##|\Z)",
        re.DOTALL,
    )
    match = pattern.search(block)
    return match.group(1).strip() if match else ""


def extract_model_role(block: str, key: str) -> str:
    pattern = re.compile(rf"-\s*{re.escape(key)}:\s*`?([a-zA-Z_-]+)`?")
    match = pattern.search(block)
    return match.group(1).strip() if match else ""


def flatten(value: str) -> str:
    """Collapse a multi-line field value into a single KEY=value-safe line."""
    return " ".join(value.split())


def parse_tasks(plan_text: str) -> list[dict]:
    headers = list(TASK_HEADER_RE.finditer(plan_text))
    tasks = []
    for i, header in enumerate(headers):
        start = header.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(plan_text)
        block = plan_text[start:end]
        task_num = header.group(1)
        tasks.append(
            {
                "task_id": f"task-{task_num}",
                "description": extract_field(block, "Description"),
                "goal": extract_field(block, "Goal"),
                "spec": extract_field(block, "Specification"),
                "acceptance": extract_field(block, "Acceptance Criteria"),
                "files": extract_field(block, "Files"),
                "interfaces": extract_field(block, "Interfaces"),
                "implementation_model_role": extract_model_role(
                    block, "implementation_model_role"
                ),
                "review_model_role": extract_model_role(block, "review_model_role"),
                "escalated_model_role": extract_model_role(
                    block, "escalated_model_role"
                ),
            }
        )
    return tasks


def load_completed_task_ids(ledger_path: Path) -> set[str]:
    if not ledger_path.is_file():
        # No ledger yet means no tasks are complete -- this is a legitimate first-run
        # state (ValidateLedgerIdentity creates the file before NextTask ever runs),
        # but if it's genuinely missing here that upstream invariant was violated.
        fail(f"ledger not found: {ledger_path}")

    completed: set[str] = set()
    lines = ledger_path.read_text(encoding="utf-8").splitlines()
    for line in lines:
        match = LEDGER_ENTRY_RE.match(line)
        if not match:
            continue
        if match.group("outcome") not in SAFE_OUTCOMES:
            continue
        sha = match.group("sha")
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", sha, "HEAD"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if result.returncode == 0:
            completed.add(match.group("task"))
    return completed


def compute_state_dir(plan_path: Path, ledger_path: Path) -> Path:
    slug = re.sub(r"[^a-z0-9]+", "-", plan_path.stem.lower()).strip("-") or "plan"
    state_dir = ledger_path.parent / slug
    (state_dir / "task-briefs").mkdir(parents=True, exist_ok=True)
    (state_dir / "review-packages").mkdir(parents=True, exist_ok=True)
    return state_dir


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True)
    parser.add_argument("--ledger", required=True)
    args = parser.parse_args()

    plan_path = Path(args.plan).expanduser()
    ledger_path = Path(args.ledger).expanduser()

    if not plan_path.is_file():
        fail(f"plan not found: {plan_path}")

    plan_text = plan_path.read_text(encoding="utf-8")
    tasks = parse_tasks(plan_text)
    if not tasks:
        fail(f"plan {plan_path} contains zero parsed '### Task N:' sections")

    completed = load_completed_task_ids(ledger_path)
    state_dir = compute_state_dir(plan_path, ledger_path)

    for task in tasks:
        if task["task_id"] in completed:
            continue

        missing = [
            field
            for field in ("goal", "spec", "acceptance", "interfaces")
            if not task[field]
        ]
        if missing:
            fail(
                f"{task['task_id']} is missing required field(s): {', '.join(missing)}"
            )

        print(f"TASK_ID={task['task_id']}")
        print(f"TASK_GOAL={flatten(task['goal'])}")
        print(f"TASK_DESCRIPTION={flatten(task['description'])}")
        print(f"TASK_SPEC={flatten(task['spec'])}")
        print(f"TASK_ACCEPTANCE={flatten(task['acceptance'])}")
        print(f"TASK_INTERFACES={flatten(task['interfaces'])}")
        print(f"TASK_FILES={flatten(task['files'])}")
        print(f"TASK_IMPLEMENTATION_MODEL_ROLE={task['implementation_model_role']}")
        print(f"TASK_REVIEW_MODEL_ROLE={task['review_model_role']}")
        print(f"TASK_ESCALATED_MODEL_ROLE={task['escalated_model_role']}")
        print(f"STATE_DIR={state_dir}")
        print("has_task")
        return

    print("no_tasks")


if __name__ == "__main__":
    main()
