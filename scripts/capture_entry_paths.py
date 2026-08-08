#!/usr/bin/env python3
"""Entry-state capture for finish.dot's CaptureEntryPaths node.

Contract (called as:
  python3 scripts/capture_entry_paths.py --worktree "${WORKTREE_PATH:-$(pwd)}"
)
------------------------------------------------------------------------------
Ports recipes/finish-branch.yaml's "capture-entry-paths" step directly: resolve
and freeze the worktree path, current branch, and the main repository path
(the common Git dir's parent) once, at entry, before any later finish.dot node
mutates state (merge/PR/discard) -- matching the recipe's "Immutable entry
paths" convention referenced throughout finish-branch.yaml (every later step
reads {{entry_paths.*}} rather than recomputing).

Output contract
---------------
Prints "KEY=value" lines for the three fields the recipe's own JSON output
carries as `entry_paths.worktree_path` / `entry_paths.branch_name` /
`entry_paths.main_repo_path` (this DOT graph's convention: uppercase env keys
map 1:1 to the lowercase ${entry_paths.*} context fields referenced
elsewhere):

  ENTRY_WORKTREE_PATH=/abs/path
  ENTRY_BRANCH_NAME=feature/example-branch
  ENTRY_MAIN_REPO_PATH=/abs/path/to/main/checkout

This node has a plain (unconditional) outgoing edge in finish.dot -- no
downstream condition reads its own last line -- so no separate routing token
is required; the KEY=value lines are the contract.

Fail-closed: a detached HEAD (no current branch) is a hard error, matching the
recipe's own "ERROR: captured worktree is detached; a branch is required".
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worktree", required=True)
    args = parser.parse_args()

    supplied = args.worktree.strip()
    if supplied:
        worktree = Path(supplied).expanduser().resolve()
    else:
        try:
            worktree = Path(
                subprocess.check_output(
                    ["git", "rev-parse", "--show-toplevel"], text=True
                ).strip()
            ).resolve()
        except subprocess.CalledProcessError as error:
            fail(f"unable to resolve current worktree: {error}")
            return

    if not worktree.is_dir():
        fail(f"worktree path does not exist: {worktree}")
        return

    try:
        branch = subprocess.check_output(
            ["git", "-C", str(worktree), "branch", "--show-current"], text=True
        ).strip()
    except subprocess.CalledProcessError as error:
        fail(f"unable to determine current branch: {error}")
        return

    if not branch:
        fail("captured worktree is detached; a branch is required")
        return

    try:
        common_dir = Path(
            subprocess.check_output(
                [
                    "git",
                    "-C",
                    str(worktree),
                    "rev-parse",
                    "--path-format=absolute",
                    "--git-common-dir",
                ],
                text=True,
            ).strip()
        ).resolve()
    except subprocess.CalledProcessError as error:
        fail(f"unable to determine common git dir: {error}")
        return

    main_repo = common_dir.parent

    print(f"ENTRY_WORKTREE_PATH={worktree}")
    print(f"ENTRY_BRANCH_NAME={branch}")
    print(f"ENTRY_MAIN_REPO_PATH={main_repo}")


if __name__ == "__main__":
    main()
