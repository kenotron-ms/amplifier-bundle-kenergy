# Anti-Rationalization — Cross-Phase Reminders

## Spirit vs Letter

Violating the letter of a process rule IS violating the spirit.

Common rationalizations to reject:

- "I'll just quickly add this one thing, then decide how to verify it" — No. State the claim and choose a falsifiable method first.
- "The spec didn't explicitly say I can't do this" — If it wasn't specified, don't add it.
- "I already know it works, the check is just a formality" — Then run the check and record the observed output.
- "This is just a minor cleanup, it doesn't count as a feature" — Scope creep starts with minor things.
- "I'll refactor while I'm in here" — Refactor is its own scoped change; state its claim and verification method.
- "The real-path check would be too hard to run for this" — That is a design or environment signal; identify a falsifiable production-relevant method.

## YAGNI — Ruthless Scope Control

You Aren't Gonna Need It.

- Do not add while-I'm-here improvements — if the task doesn't require it, don't touch it.
- Do not implement hypothetical requirements — build only what is specified now.
- Do not introduce unnecessary abstractions — solve the actual problem with the simplest code.
- Do not apply premature optimization — make it work correctly first; optimize only when measured.

## False Completion Prevention

Done means verified, not "I think it works."

Before claiming any task is complete:

1. State the specific behavior claim from the task.
2. Choose and run the cheapest falsifiable check at the appropriate VDD level.
3. Record the exact command, observed output, and exit status.
4. Confirm the evidence proves the claim and reveals no applicable regression.

## The Three-Fix Escalation

If you find yourself making a third fix to the same problem, stop blind patching.

Three or more fixes to the same area signal an architectural or root-cause issue,
not an implementation detail. At that point:

- Stop applying speculative fixes.
- Reassess the root cause and architecture from the evidence gathered so far.
- Follow the task's bounded resume/escalate/adjudicate loop; do not invent a
  separate escalation path or a progress checkpoint.
- Escalate to the user only when the reassessment reveals a genuine user-only
  decision, or when the loop reaches its defined cap with an actual `BLOCKED`
  condition. Its own adjudication handles non-load-bearing findings.

Repeated failed fixes are a signal to deepen the investigation, not to interrupt
the user by default.
