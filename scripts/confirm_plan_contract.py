#!/usr/bin/env python3
"""Evidence gate for plan_like_ken.dot's ConfirmPlanArtifact node.

Contract (called as:
  python3 scripts/confirm_plan_contract.py --plan-path-file .resolve/plan/plan_path.txt
)
------------------------------------------------------------------------------
This is THE GATE plan_like_ken.dot's own header names as its sink: "Plan file
demonstrably contains every field the executor requires, confirmed by grep,
not by the plan-writer's claim." Cross-checked against agents/plan-writer.md's
authoritative field contract and the exact fields
recipes/subagent-driven-development.yaml's execution step actually consumes
per task (description, goal, spec, acceptance_criteria, interfaces, files,
implementation_model_role, review_model_role, escalated_model_role) plus one
plan-wide '## Global Constraints' block.

Checks performed
----------------
1. The plan-path file exists and names a real, existing plan document.
2. The plan document has exactly one '## Global Constraints' block.
3. The plan document has at least one '### Task N:' section.
4. Every '### Task N:' section has non-empty
   Description / Goal / Specification / Acceptance Criteria / Files fields.
5. Every task section has an **Interfaces:** block with non-empty
   Consumes and Produces lines.
6. Every task section has a **Model Roles:** block with valid, correctly
   ordered implementation_model_role / review_model_role / escalated_model_role
   values (escalated strictly above implementation on the fast < coding <
   reasoning < critical-ops ladder, mirroring
   recipes/subagent-driven-development.yaml's own validate-plan step).

Output contract
---------------
Prints exactly one routing token as the last line, matching
plan_like_ken.dot's edges:
  ConfirmPlanArtifact -> HandoffToExecution [condition="...=contract_satisfied"]
  ConfirmPlanArtifact -> FixPlanArtifact    [condition="...=contract_violated"]

On violation, prints the specific missing field(s) per task to stderr (which
FixPlanArtifact's prompt reads via ${tool.last_output}) before the final
"contract_violated" token.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

IMPLEMENTATION_ROLE_ORDER = {"fast": 0, "coding": 1, "reasoning": 2}
ESCALATED_ROLE_ORDER = {"coding": 1, "reasoning": 2, "critical-ops": 3}
REVIEW_ROLES = {"fast", "critique", "reasoning"}

TASK_HEADER_RE = re.compile(r"^###\s+Task\s+(\d+)\s*:\s*(.*)$", re.MULTILINE)
REQUIRED_FIELDS = [
    "Description",
    "Goal",
    "Specification",
    "Acceptance Criteria",
    "Files",
]


def extract_field(block: str, label: str) -> str:
    pattern = re.compile(
        rf"\*\*{re.escape(label)}:\*\*\s*(.*?)(?=\n\*\*[A-Za-z][A-Za-z ]*:\*\*|\n##|\Z)",
        re.DOTALL,
    )
    match = pattern.search(block)
    return match.group(1).strip() if match else ""


def extract_interfaces(block: str) -> tuple[str, str]:
    section = extract_field(block, "Interfaces")
    consumes_match = re.search(r"-\s*Consumes:\s*(.+)", section)
    produces_match = re.search(r"-\s*Produces:\s*(.+)", section)
    consumes = consumes_match.group(1).strip() if consumes_match else ""
    produces = produces_match.group(1).strip() if produces_match else ""
    return consumes, produces


def extract_model_role(block: str, key: str) -> str:
    pattern = re.compile(rf"-\s*{re.escape(key)}:\s*`?([a-zA-Z_-]+)`?")
    match = pattern.search(block)
    return match.group(1).strip() if match else ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan-path-file", required=True)
    args = parser.parse_args()

    violations: list[str] = []

    plan_path_file = Path(args.plan_path_file).expanduser()
    if not plan_path_file.is_file():
        print(f"plan path file not found: {plan_path_file}", file=sys.stderr)
        print("contract_violated")
        return

    plan_path = Path(plan_path_file.read_text(encoding="utf-8").strip()).expanduser()
    if not plan_path.is_file():
        print(f"plan document does not exist: {plan_path}", file=sys.stderr)
        print("contract_violated")
        return

    plan_text = plan_path.read_text(encoding="utf-8")

    if len(re.findall(r"^##\s+Global Constraints\s*$", plan_text, re.MULTILINE)) != 1:
        violations.append("plan must have exactly one '## Global Constraints' section")

    headers = list(TASK_HEADER_RE.finditer(plan_text))
    if not headers:
        violations.append("plan has zero '### Task N:' sections")

    for i, header in enumerate(headers):
        start = header.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(plan_text)
        block = plan_text[start:end]
        task_label = f"Task {header.group(1)}"

        for field in REQUIRED_FIELDS:
            if not extract_field(block, field):
                violations.append(f"{task_label}: missing or empty '{field}'")

        consumes, produces = extract_interfaces(block)
        if not consumes:
            violations.append(f"{task_label}: Interfaces block missing 'Consumes'")
        if not produces:
            violations.append(f"{task_label}: Interfaces block missing 'Produces'")

        implementation_role = extract_model_role(block, "implementation_model_role")
        review_role = extract_model_role(block, "review_model_role")
        escalated_role = extract_model_role(block, "escalated_model_role")

        if implementation_role not in IMPLEMENTATION_ROLE_ORDER:
            violations.append(
                f"{task_label}: invalid or missing implementation_model_role "
                f"({implementation_role!r})"
            )
        if review_role not in REVIEW_ROLES:
            violations.append(
                f"{task_label}: invalid or missing review_model_role ({review_role!r})"
            )
        if escalated_role not in ESCALATED_ROLE_ORDER:
            violations.append(
                f"{task_label}: invalid or missing escalated_model_role ({escalated_role!r})"
            )
        elif (
            implementation_role in IMPLEMENTATION_ROLE_ORDER
            and ESCALATED_ROLE_ORDER[escalated_role]
            <= IMPLEMENTATION_ROLE_ORDER[implementation_role]
        ):
            violations.append(
                f"{task_label}: escalated_model_role ({escalated_role}) must be strictly "
                f"above implementation_model_role ({implementation_role})"
            )

    if violations:
        for violation in violations:
            print(violation, file=sys.stderr)
        print("contract_violated")
        return

    print("contract_satisfied")


if __name__ == "__main__":
    main()
