#!/usr/bin/env python3
"""Fork-answer recorder for think_like_ken.dot's ResolveForks node.

Contract (called as:
  python3 scripts/append_fork_answers.py --reply "$LAST_RESPONSE"
  printf 'recorded'
)
------------------------------------------------------------------------------
Appends the human's freeform reply (the batched fork-question answers) to a
running JSONL log so later nodes in think_like_ken.dot (SynthesizeDecisions,
DelegateDesignWriter) -- and any human re-reading the session later -- have a
durable, append-only record of every fork resolution, not just whatever is
still in the conversation window.

The calling shell always prints the literal 'recorded' after this script exits
0 -- there is no downstream condition on this script's own stdout (ForkGate's
routing already happened before ResolveForks runs).

State: .resolve/think/fork_answers.jsonl -- one JSON object per line:
  {"timestamp": "<ISO 8601 UTC>", "reply": "<the human's reply text>"}

Fail-closed: an empty --reply is a hard error (a blank answer is not a real
fork resolution and must not be silently recorded as one).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(".resolve/think/fork_answers.jsonl")


def fail(message: str) -> None:
    print(f"BLOCKED: {message}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reply", required=True)
    args = parser.parse_args()

    reply = args.reply.strip()
    if not reply:
        fail("--reply is empty")

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "reply": reply,
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


if __name__ == "__main__":
    main()
