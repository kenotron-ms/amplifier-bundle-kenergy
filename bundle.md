---
bundle:
  name: kenergy
  version: 1.0.0
  description: Opinionated development workflow bundle — VDD modes, persona reviewer skills, and a philosophy stack built around the principle that human attention is sacred

includes:
  - bundle: git+https://github.com/microsoft/amplifier-bundle-superpowers@main
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main#subdirectory=experiments/behavioral-anchor/behavioral-anchor.md
  - bundle: kenergy:behaviors/kenergy
---

# Kenergy

Opinionated development workflow for people who believe that:

- **Design before code.** Don't write a line until you understand what you're building and why.
- **Verify with reality.** Mocks prove the mock works. Run the real thing.
- **Human attention is sacred.** Don't waste review cycles on theater.

## What You Get

**Three interlocking modes** that form a complete development loop:

| Mode | What it does |
|------|-------------|
| `/brainstorm` | Explore → question → propose approaches → validate design section-by-section |
| `/write-plan` | Review design → discuss task breakdown → delegate plan creation to an agent |
| `/execute-plan` | Three-agent pipeline: implementer → verifier → code-quality-reviewer |

**Four persona reviewer skills** you can load at any checkpoint:

| Skill | Persona | Load trigger |
|-------|---------|-------------|
| `crusty-old-engineer` | Grounded skeptic. "What have you tried and what could go wrong?" | `coe`, `reality check` |
| `cranky-old-sam` | Simplicity zealot. "Why does this exist at all?" | `cosam`, `simplify` |
| `scenario-verification` | Goal-language UI verification. No DOM selectors. | `verify the feature` |
| `voice-check` | Anti-slop blog post judge. Requires per-project `VOICE.md`. | `/voice-check` |

**A philosophy stack** always in context — the shared discipline that makes the modes work.

**A triage coordinator bundle** for autonomous pipelines that need approve/deny/escalate decisions.
