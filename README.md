# amplifier-bundle-kenergy

Opinionated development workflow for Amplifier — VDD modes, persona reviewer skills, and a philosophy stack built around one principle: **human attention is the most sacred resource**.

## Install

```bash
amplifier bundle add git+https://github.com/kenotron-ms/amplifier-bundle-kenergy@main
```

## What You Get

### Four Workflow Phases

The phases form a complete development loop. Use them in order.

**`/think-like-ken`** — Design before code.

Explore evidence, batch genuine user-only questions by topic, and decide engineering
questions directly. Present one consolidated TL;DR review for explicit approval,
then delegate document creation to `kenergy:design-writer` — the orchestrator
converses, the agent writes the artifact.

**`/plan-like-ken`** — Direct planning from the approved design.

Reads the approved design, maps dependencies, and decides the exact verification method for every task (not "write a test" — decide whether that means `curl`, `playwright-cli`, or `python -c`). Delegates plan creation directly to `kenergy:plan-writer`, then hands the saved plan automatically to continuous execution.

**`/build-like-ken`** — Continuous execution with real verification.

For each task: `kenergy:implementer` → merged `kenergy:reviewer` → bounded resume/escalate/adjudicate remediation loop, continuing through the plan without an approval gate between tasks. The orchestrator never writes code. Real execution output is required. Mocks-only = not verified.

**`/finish`** — Make the final integration decision.

After verified execution, choose once: merge, open a PR, keep the branch, or discard it.

```
/think-like-ken -> consolidated design review -> one approval
/plan-like-ken  -> direct plan generation -> automatic execution handoff
/build-like-ken -> implementer -> three-axis reviewer -> bounded fix loop
/finish         -> merge / PR / keep / discard decision
```

### Five Persona Reviewer Skills

Load at any checkpoint — brainstorm, design, plan, implement, or review.

**`crusty-old-engineer`** (`COE`) — Grounded engineering skeptic. Asks: "What have you tried and what could go wrong?" Evidence-linked judgment anchored in real incident post-mortems (Knight Capital, Therac-25, Ariane 5). Triggers on `coe`, `reality check`, `what could go wrong`.

**`cranky-old-sam`** (`COSam`) — Simplicity zealot. First question is always "why does this exist at all?" not "what's missing?" Treats every unnecessary abstraction as a personal affront. Triggers on `cosam`, `simplify`, `too complex`, `do we need this`.

**`kenergy`** — Verification anchor. Two modes: (1) pre-work — define what "working" means for a real user and set the minimum proof before delegating; (2) post-work — hold the claim of done to that bar. Asks: "does this earn its place, and have you actually proven it?" Triggers on `kenergy`, `prove it`, `define done`, `did you verify`, `minimum proof`.

**`scenario-verification`** — Goal-language UI verification scenarios. Write verification as user intent + observable outcome — never DOM selectors, never CSS classes. Scenarios survive a full UI redesign without edits. Triggers on `verify the feature`, `scenario test`.

**`voice-check`** — Anti-slop + voice authenticity judge for blog posts. Runs mechanical lint (em-dash density, AI trigger words, hedging phrases) then LLM evaluation across 8 dimensions. Returns `PUBLISH / REVISE / REWRITE`. Requires per-project `VOICE.md` (see setup below).

### Philosophy Stack (Always in Context)

Five short context files that enforce the shared discipline:

| File | What it does |
|------|-------------|
| `instructions.md` | Core mandate: check skills/modes BEFORE any response |
| `philosophy.md` | The 7-principle philosophy (TDD, systematic, evidence, simplicity, structured planning, isolation, human checkpoints) |
| `using-superpowers-amplifier.md` | Amplifier-specific meta-instructions and red-flag thought table |
| `shared-anti-rationalization.md` | YAGNI enforcement, false completion prevention, three-fix escalation rule |
| `verification-failure-memories.md` | Five cautionary vignettes of false completion patterns |

Three heavier reference files live in `context/` but are **not** always loaded (to preserve token budget):

- `spec-document-review-prompt.md` — antagonistic spec reviewer dispatch template (referenced by `/think-like-ken`)
- `debugging-techniques.md` — root-cause tracing reference
- `tdd-depth.md` — TDD iron law, anti-patterns, and extended rebuttals

To always load any of these, add them to your `~/.amplifier/context/`.

### Triage Coordinator Bundle

`kenergy:bundles/coordinator` — a minimal bundle that outputs only:

```json
{"decision": "approve" | "deny" | "escalate", "reason": "<one sentence>"}
```

For autonomous agent pipelines that need a policy gate.

## voice-check Setup

The `voice-check` skill requires a per-project voice profile:

**1. Create `.amplifier/VOICE.md`** in your project:

```markdown
# Voice Profile

## Tone
[How you sound — direct, skeptical, warm, technical, etc.]

## Patterns to Avoid
[Your specific anti-patterns — em-dash overuse, hedge words, etc.]

## Examples of Your Writing
[Paste 2–3 paragraphs that sound like you]
```

**2. (Optional) Create `scripts/lint-voice.sh`** for mechanical pre-checks:

```bash
#!/bin/bash
# Check for common AI tells in the target file
grep -c "—" "$1"  # em-dash count
grep -ic "leverage\|utilize\|seamless\|robust" "$1"  # AI trigger words
```

## Dependencies

This bundle automatically installs:

- **[amplifier-bundle-superpowers](https://github.com/microsoft/amplifier-bundle-superpowers)** — provides the superpowers recipe infrastructure and base agents that kenergy extends

## Philosophy

### Verification Driven Development (VDD)

The modes are grounded in one idea: **human attention is finite and precious**. Don't spend it on:

- Reviewing mocks that prove the mock works
- Watching tests pass that have never touched production code paths
- Approving plans where "verification" means "write a test"

The verification hierarchy (pick the cheapest one that proves the claim):

| Level | Method | Use when |
|-------|--------|----------|
| 1 | Static analysis (`ruff`, `ty`, `tsc`, `oxc`) | Always — zero cost |
| 2 | Run the code directly | Scripts, CLIs, importable modules |
| 3 | `curl` / HTTP call | API endpoints |
| 4 | Browser via `playwright-cli` | UI changes |
| 5 | Reality Check / DTU | True isolation required |

Unit tests are right for **library code**. For everything else, run the real thing.

### The Hybrid Pattern

The modes use a split-responsibility architecture:

- **The orchestrator** (you, in the session) handles **conversation** — questions, trade-offs, validation, decisions
- **Agents** handle **artifacts** — design documents, implementation plans, code

This preserves real-time dialogue for what it's good at, and uses focused agents for what they're good at.

### Genuine Forks Only

`/think-like-ken` interrupts the user only for personal preferences or facts only
they know, batching related questions by topic. It decides evidence-backed
engineering questions directly, then presents one consolidated TL;DR design
review for a single approval.

## License

MIT
