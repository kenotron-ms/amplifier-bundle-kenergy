---
name: scenario-verification
description: >
  Objective-driven verification scenarios for UI and integration flows. Write verification
  as sequences of user goals and observable outcomes — never DOM elements, never CSS selectors.
  Each step is what a user is trying to do and what they can observe. Use when verifying
  any feature a human would interact with: browser flows, API journeys, CLI workflows.
  Triggers on: "verify the feature", "write a verification scenario", "browser verify",
  "end-to-end check", "scenario test", "objective verification".
user-invocable: true
allowed-tools:
  - bash
  - read_file
  - delegate
model_role: coding
context: fork
---

# Scenario Verification

Verification that proves a feature works by running it the way a user would use it.

Steps are written in terms of **user goals and observable outcomes** — not page elements,
not CSS selectors, not DOM structure. The page is an implementation detail. The goal is what
matters.

---

## The Format

A scenario is a named sequence of objective steps. Each step has:
- **Action** — what the user is trying to accomplish (goal language)
- **Observable outcome** — what the user can see or confirm (factual, not structural)

```
Scenario: [name — describes the goal being verified]

1. [Action]
   → [Observable outcome]

2. [Action]
   → [Observable outcome]
```

No element references. No selectors. No "click the button with id X". If you find yourself
describing the page structure, stop — describe what the user is trying to do instead.

---

## Worked Example

```
Scenario: Shopping cart — add a product

1. Start the dev server
   → Server is running and reachable

2. Open the app in a browser
   → The home page loads

3. Log in with a test user
   → The user is authenticated and sees their account

4. Navigate to the shopping cart
   → The cart is empty — no items

5. Search for men's shoes
   → Results appear

6. Find the price of a result
   → A price is visible for at least one item

7. Add an item to the cart
   → The cart reflects one item added
```

That's it. No mention of what the nav looks like, where the search box is, what the cart
icon says, or how the price is formatted. The scenario survives a complete redesign.

---

## Writing Good Steps

**Goal language (right):**
- "Log in with a test user"
- "Navigate to the shopping cart"
- "Search for men's shoes"
- "Find the price of a result"
- "Add an item to the cart"

**Element language (wrong — never do this):**
- "Click the Login button in the top-right nav"
- "Click the cart icon in the header"
- "Type 'men's shoes' into the search input"
- "Read the `.price` span text"
- "Click the 'Add to cart' button below the product image"

Element language breaks when the UI changes. Goal language doesn't — because the goal
doesn't care how the UI is built.

**Observable outcomes (right):**
- "The cart is empty — no items"
- "Results appear"
- "A price is visible for at least one item"
- "The cart reflects one item added"

**DOM assertions (wrong):**
- "The `.cart-count` span shows 0"
- "The `.results-grid` has at least one child"
- "The `data-price` attribute is non-empty"
- "The cart badge increments by 1"

---

## Execution

Run scenarios through a browser agent using `playwright-cli` or `browser-tester`.
Instruct the agent with the scenario text and let it find its own way through the UI.

The agent's job is to achieve each goal using whatever the UI provides — it should not
be given element hints. If it can't achieve a goal, that's a real finding: the feature
is hard to use or broken.

Example delegation:
```
delegate(
  agent="behavioral-anchor:agents/explorer",
  instruction="""Execute this verification scenario against http://localhost:3000.

[paste scenario]

For each step: attempt to achieve the goal, report what you observed.
Do not describe page elements — describe whether you achieved the goal and what you saw.
If you cannot achieve a goal, that is a FAIL for that step — report exactly what blocked you."""
)
```

---

## Where Scenarios Fit in the Verification Hierarchy

```
Level 1: Static analysis (ruff, ty, oxc, tsc) — always, free
Level 2: Run the code directly — scripts, CLIs
Level 3: curl / HTTP calls — API endpoints
Level 4: Scenario verification ← HERE — UI and integration flows
Level 5: Reality Check / DTU — true isolation required
```

Use scenario verification for any change a human would see and interact with.
Skip it for pure backend logic, library code, or changes with no user-facing surface.

---

## Where to Put Scenarios in a Plan

Scenarios belong in the plan as the verification step for any task that produces a
user-facing feature. They replace or supplement curl calls when the feature requires
navigation, state, or visual confirmation.

```markdown
**Verification**
Run scenario: [scenario name]
Tool: playwright-cli / browser-tester against http://localhost:3000

[paste scenario inline]
```

---

## Multiple Scenarios

Features often need several scenarios to cover the objective space:

- Happy path (the main flow works)
- Empty / zero state (nothing breaks when there's no data)
- Error / rejection (the user is told something useful when it fails)
- Permission boundary (unauthorized users can't reach it)

Each scenario is independent and runnable on its own. They do not share state.

---

## Quality Bar

A scenario is complete when:
- Every step is achievable by a browser agent with no element hints
- Every observable outcome is a fact a user would notice, not a DOM assertion
- The scenario can be re-run after a full UI redesign without edits
- A new team member could read it and understand what the feature does

If you have to explain the page structure to make a step make sense, the step is wrong.
Rewrite it as a goal.
