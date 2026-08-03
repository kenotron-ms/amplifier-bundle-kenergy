#!/usr/bin/env python3
"""Ledger completion writer for build_like_ken.dot's WriteLedger node.

Contract (called as:
  python3 scripts/write_ledger.py --state-dir "$STATE_DIR" --task "$TASK_ID" --outcome "$OUTCOME"
  printf 'ledger_written'
)
------------------------------------------------------------------------------
Ports recipes/single-task-pipeline.yaml's "write-ledger-checkpoint" step: append
a safe completion entry ("- [x] <task> \u2014 <head-sha> \u2014 <outcome>") to the
plan-scoped ledger, refusing (fail-closed) unless the outcome is one of the two
safe values (PASS, APPROVED_WITH_PARKED) this graph is only ever supposed to
reach here through -- ConfirmVerdictAgainstRepo or a clean AdjudicationGate
"approved_with_parked" route.

The calling shell always prints the literal 'ledger_written' after this script
exits 0 -- this script itself does not need to print a routing token (there is
no downstream condition on WriteLedger's own stdout), only to succeed or fail.

Ledger layout (mirrors ValidateLedgerIdentity's own bootstrap in
build_like_ken.dot and recipes/single-task-pipeline.yaml's ledger contract):
  # Plan: <plan path>

  ## Completed Tasks
  - [x] task-1 \u2014 <sha> \u2014 PASS

  ## Parked Findings

Fail-closed: missing ledger, missing required sections, an already-recorded
entry for this exact task, or an unsafe outcome are all hard errors -- this
script never writes a partial or duplicate entry.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SAFE_OUTCOMES = {"PASS", "APPROVED_WITH_PARKED"}


def fail(message: str) -> None:
    print(f"BLOCKED: {message}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--outcome", required=True)
    args = parser.parse_args()

    task_id = args.task.strip()
    outcome = args.outcome.strip()
    if not task_id:
        fail("--task is empty")
    if outcome not in SAFE_OUTCOMES:
        fail(f"refusing ledger write for unsafe outcome: {outcome!r}")

    # The ledger lives one level above per-plan STATE_DIR (ValidateLedgerIdentity
    # writes it at $execution_root/.kenergy/sdd/ledger.md; STATE_DIR, per
    # next_task.py, is the plan-slug sibling directory one level below that).
    state_dir = Path(args.state_dir).expanduser()
    ledger_path = state_dir.parent / "ledger.md"
    if not ledger_path.is_file():
        fail(f"ledger not found: {ledger_path}")

    lines = ledger_path.read_text(encoding="utf-8").splitlines()
    if not lines or not lines[0].startswith("# Plan:"):
        fail("ledger identity line missing or malformed")

    try:
        completed_index = lines.index("## Completed Tasks")
        parked_index = lines.index("## Parked Findings")
    except ValueError:
        fail(
            "ledger missing required '## Completed Tasks' or '## Parked Findings' section"
        )
        return
    if completed_index > parked_index:
        fail("ledger sections are out of order")

    head_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if not head_sha:
        fail("git rev-parse HEAD returned an empty SHA")

    entry_prefix = f"- [x] {task_id} \u2014"
    if any(line.startswith(entry_prefix) for line in lines):
        fail(f"ledger already has a completion entry for {task_id}")

    entry = f"- [x] {task_id} \u2014 {head_sha} \u2014 {outcome}"
    lines[parked_index:parked_index] = [entry, ""]
    ledger_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
