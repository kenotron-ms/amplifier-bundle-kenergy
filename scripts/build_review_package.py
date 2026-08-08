#!/usr/bin/env python3
"""Build the review packet for build_like_ken.dot's BuildReviewPackage node.

Contract (called as: python3 scripts/build_review_package.py --task "${task_id}"
--state-dir "${state_dir}" --round "${round}")
------------------------------------------------------------------------------
${task_id} / ${state_dir} are tool_command substitution tokens resolved from context (set by
NextTask's parse_json="true" JSON object); ${round} is set the same way by CheckRound's own
parse_json="true" output -- none of these are uppercase environment variables.
Ports recipes/single-task-pipeline.yaml's "build-review-package" step directly
(the exact diff/log/stat assembly, including the double-interpolation fix already
applied there): base SHA read from the durable per-task base-sha file, HEAD SHA
read fresh from git, package written to
  $STATE_DIR/review-packages/<task-slug>-round-<round>.md
containing Base/Head, Diff Stat, Commits, and full Diff sections.

Output contract
---------------
Prints exactly the review package PATH (not its content) on stdout -- matching
the just-fixed `review_package_path` pattern from the recipe. The reviewer node
downstream reads the package by path; it does not consume this script's stdout
as a routing token (BuildReviewPackage -> Reviewer is a plain edge).

Fail-closed: missing base-sha file, missing state dir, or any git failure exits
non-zero with a message on stderr -- never writes a partial/empty package.
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


def run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        fail(f"command failed ({' '.join(cmd)}): {result.stderr.strip()}")
    return result.stdout


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--round", required=True)
    args = parser.parse_args()

    task_id = args.task.strip()
    if not task_id:
        fail("--task is empty")

    slug = slugify(task_id)
    state_dir = Path(args.state_dir).expanduser()
    base_path = state_dir / "task-briefs" / f"{slug}.base-sha"
    if not base_path.is_file():
        fail(f"task base SHA not found: {base_path}")

    base_sha = base_path.read_text(encoding="utf-8").strip()
    if not base_sha:
        fail("task base SHA file is empty")

    head_sha = run(["git", "rev-parse", "HEAD"]).strip()

    diff_stat = run(["git", "diff", "--stat", f"{base_sha}..{head_sha}"])
    commit_log = run(["git", "log", "--oneline", f"{base_sha}..{head_sha}"])
    full_diff = run(["git", "diff", f"{base_sha}..{head_sha}", "--"])

    packages_dir = state_dir / "review-packages"
    packages_dir.mkdir(parents=True, exist_ok=True)
    package_path = packages_dir / f"{slug}-round-{args.round}.md"

    content = (
        "# Review Package\n\n"
        f"Base: {base_sha}\nHead: {head_sha}\n\n"
        "## Diff Stat\n\n```text\n"
        f"{diff_stat}"
        "```\n\n## Commits\n\n```text\n"
        f"{commit_log}"
        "```\n\n## Diff\n\n```diff\n"
        f"{full_diff}"
        "```\n"
    )
    package_path.write_text(content, encoding="utf-8")
    print(str(package_path))


if __name__ == "__main__":
    main()
