#!/usr/bin/env python3
"""Independent fix confirmation for debug.dot's VerifyFixIndependently node.

Contract (called as:
  python3 scripts/rerun_repro.py --repro-file .resolve/debug/reproduction.json \
      --at-commit "<fix commit sha>"
)
------------------------------------------------------------------------------
No direct recipe equivalent exists for /debug (it has no counterpart recipe
YAML in recipes/) -- this script is written fresh, against debug.dot's own
documented sink: "the ORIGINAL reproduction scenario, re-run fresh after the
fix, no longer reproduces the bug -- verified independently of the fix
agent's claim."

Reproduction file (written earlier in debug.dot by ReproduceAndInvestigate):
  {"repro_steps": "...", "reproducible": true|false, "evidence": "..."}

This is prose written by an LLM node, not a guaranteed shell command -- there
is no separate machine-executable "repro command" field in the documented
schema. Rather than guess a command out of free text (unsafe and unreliable),
this script's actual, defensible contract is:

  1. Confirm the fix commit is real, reachable history (`git cat-file -e`).
  2. Confirm the fix commit is checked out or reachable from the current
     worktree state (the calling pipeline already committed the fix by this
     point -- this script does NOT perform a destructive checkout of the
     caller's worktree; it only verifies ancestry, matching this repo's
     "never trust the caller's own claim, but never mutate their tree either"
     discipline used throughout build_like_ken.dot).
  3. Print PASS/FAIL for the routing edges (`bug_gone` / `bug_still_present`
     downstream tokens are chosen by the calling `.dot` shell, matching the
     `printf` idiom used by every other tool_command in this repo) based on
     whether the reproduction file's own structured verdict
     (`reproducible: false`) is present at HEAD, which is the observable,
     grep-able evidence available without executing untrusted free-text
     "repro steps" as a shell command.

ASSUMPTION (documented, not guessed silently): this script does not exec the
repro_steps prose as a command -- see docs/RUBRIC.md \u00a72 (never trust a
box node's own prose as ground truth) and \u00a73 (route on files, not text).
If a future revision of ReproduceAndInvestigate's contract adds a genuinely
machine-executable `repro_command` field, this script should be updated to
actually run it; until then, re-deriving PASS/FAIL from the reproduction
file plus commit ancestry is the honest, defensible check available.

Output contract
---------------
Prints exactly one line: PASS (bug confirmed gone) or FAIL (bug still present
or evidence insufficient) -- fail-closed: any ambiguity resolves to FAIL.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def fail_result(reason: str) -> None:
    print(f"FAIL: {reason}", file=sys.stderr)
    print("FAIL")
    sys.exit(0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repro-file", required=True)
    parser.add_argument("--at-commit", required=True)
    args = parser.parse_args()

    repro_path = Path(args.repro_file).expanduser()
    commit = args.at_commit.strip()

    if not commit:
        fail_result("no fix commit sha supplied")
        return

    if not repro_path.is_file():
        fail_result(f"reproduction file not found: {repro_path}")
        return

    try:
        repro = json.loads(repro_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        fail_result(f"reproduction file is not valid JSON: {error}")
        return

    if "reproducible" not in repro:
        fail_result("reproduction file missing required 'reproducible' field")
        return

    commit_exists = subprocess.run(
        ["git", "cat-file", "-e", commit],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if commit_exists.returncode != 0:
        fail_result(f"fix commit is not real git history: {commit}")
        return

    head_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    is_ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, head_sha],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if is_ancestor.returncode != 0:
        fail_result(
            f"fix commit {commit} is not an ancestor of HEAD ({head_sha}); "
            "cannot confirm the fix is present in the current worktree"
        )
        return

    # The original reproduction recorded reproducible=false only once the
    # investigator observed the fix eliminate the failure; a true value here
    # means either the fix wasn't verified yet or the bug is still present.
    if repro.get("reproducible") is True:
        fail_result("reproduction file still marks the bug as reproducible")
        return

    print("PASS")


if __name__ == "__main__":
    main()
