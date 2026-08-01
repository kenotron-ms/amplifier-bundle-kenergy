---
bundle:
  name: kenergy
  version: 1.0.0
  description: Opinionated development workflow bundle — VDD modes, persona reviewer skills, and a philosophy stack built around the principle that human attention is sacred

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main#subdirectory=experiments/behavioral-anchor/behavioral-anchor.md
  - bundle: kenergy:behaviors/kenergy
---

# Kenergy

Opinionated development workflow for people who believe that:

- **Design before code.** Don't write a line until you understand what you're building and why.
- **Verify with reality.** Mocks prove the mock works. Run the real thing.
- **Human attention is sacred.** Don't waste review cycles on theater.

## What You Get

**Four workflow phases** that form a complete development loop:

| Mode | What it does |
|------|-------------|
| `/think-like-ken` | Consolidated design review → one approval |
| `/plan-like-ken` | Direct plan generation → automatic execution handoff |
| `/build-like-ken` | Implementer → three-axis `kenergy:reviewer` → bounded fix loop |
| `/finish` | Merge / PR / keep / discard decision |

**Five persona reviewer skills** you can load at any checkpoint:

| Skill | Persona | Load trigger |
|-------|---------|-------------|
| `crusty-old-engineer` | Grounded skeptic. "What have you tried and what could go wrong?" | `coe`, `reality check` |
| `cranky-old-sam` | Simplicity zealot. "Why does this exist at all?" | `cosam`, `simplify` |
| `kenergy` | Verification anchor. "Does this earn its place — and have you proven it works?" | `kenergy`, `prove it`, `define done` |
| `scenario-verification` | Goal-language UI verification. No DOM selectors. | `verify the feature` |
| `voice-check` | Anti-slop blog post judge. Requires per-project `VOICE.md`. | `/voice-check` |

**A philosophy stack** always in context — the shared discipline that makes the modes work.

**A triage coordinator bundle** for autonomous pipelines that need approve/deny/escalate decisions.
