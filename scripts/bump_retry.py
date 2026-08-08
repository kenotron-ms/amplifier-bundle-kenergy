#!/usr/bin/env python3
"""Retry counter for verify.dot's CheckRetryCount node.

Contract (called as:
  count=$(python3 scripts/bump_retry.py --state-file .resolve/verify/retry_count.json)
  if [ "$count" -le 2 ]; then printf 'retry'; else printf 'exhausted'; fi
)
------------------------------------------------------------------------------
No recipe equivalent needed -- straightforward durable JSON counter matching
verify.dot's own documented bound ("verify.dot's 2-round evidence-gathering
cap reports NOT VERIFIED and hands off to /debug", per pipelines/README.md).

The calling shell owns the retry/exhausted routing decision; this script's
sole job is to durably increment and print the new count as a bare integer.

State: a single JSON file, e.g. {"count": 2} -- created at 1 on first call,
incremented by 1 on every subsequent call.

Fail-closed: a corrupt (non-dict, non-integer "count") existing state file is
a hard error -- never silently reset to 1.
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
        try:
            data = json.loads(raw) if raw else {}
        except json.JSONDecodeError as error:
            fail(f"retry state file is corrupt JSON: {state_path}: {error}")
            return
        if not isinstance(data, dict) or "count" not in data:
            fail(f"retry state file missing 'count' key: {state_path}")
            return
        if not isinstance(data["count"], int):
            fail(f"retry state file 'count' is not an integer: {state_path}")
            return
        count = data["count"] + 1
    else:
        count = 1

    state_path.write_text(json.dumps({"count": count}) + "\n", encoding="utf-8")
    print(count)


if __name__ == "__main__":
    main()
