---
name: moon-scout
description: |
  Scouts a UI screenshot, mockup, or SVG section by section and confirms what's actually in it before any component code gets written. Use this whenever the user shares a UI image (screenshot, PNG, JPG, SVG, Figma export) and wants it built, implemented, cloned, replicated, or turned into code — including phrasing like "build this screen", "implement this design", "turn this into a component", "code this UI", "make this page", "clone this design", "ทำ UI ตามรูปนี้", "สร้าง component จากรูป", "แปลงรูปเป็นโค้ด", "ช่วยเขียนหน้านี้ให้หน่อย", "ทำหน้านี้ให้หน่อย". Run this even when the request sounds simple or the user seems in a hurry — implementing straight from an image without first confirming what's actually visible in it is the single biggest source of wrong, invented UI. Never jump straight to writing component code when an image is the source of truth; land here first.
---

# moon-scout

You're scouting unfamiliar terrain before committing to a build. A picture only shows what it shows — anything you can't actually make out, you ask about instead of filling in from a guess. Guessing here is expensive: it produces UI that looks plausible but is wrong in ways that are tedious to find and fix later.

## How to ask

Every confirmation or choice point in this skill — Step 1's big-picture check, Step 2's hierarchy check, Step 3's "which node first," Phase 2's "which node next," Phase 3's readiness check, Phase 4's library question — should go through a structured, clickable multiple-choice question (e.g. this environment's `AskUserQuestion` tool) instead of a plain question typed into prose. The user should be able to pick an option instead of typing a reply every time this skill needs a decision. Build the options from what's actually being decided:

- Big picture / hierarchy checks: an option for "yes, that's right" and one for "no, something's off" (a free-text option for the correction comes with the tool automatically).
- "Which node next": one option per remaining node.
- UI library: a few common libraries relevant to the stack if it's visible from context, plus room for something else.

Only fall back to asking in plain text if no structured-question tool is available in the current environment.

## Phase 1 — Landing survey

Work through three checkpoints in order. Don't jump to structure before the big picture is confirmed, and don't jump to per-element detail before the structure is confirmed and a starting point is chosen — each checkpoint changes how the next one should be read.

### Step 1: Big picture

State what the image actually is, in plain terms — what screen/app/state this looks like and what it's for (e.g., "a search filter form for an employee performance report, in its default state, no results loaded yet"). Confirm: *"I read this as [X]. Is that right, or is it something else?"*

Wait for confirmation before moving on.

### Step 2: Component hierarchy

Break the layout into a **nested outline**, not a flat list of equally-ranked sections. Real UIs are made of containers with children, and getting that nesting right matters for implementation: a set of form fields and the action buttons that submit/clear them usually belong to the *same* component, sharing the same state — peeling the buttons out into their own top-level "Actions" section loses that relationship and leads to code that splits state across the wrong boundaries. Ask, for each element: is this a top-level region on its own (like a persistent sidebar or top bar), or does it actually live inside another component nearby?

Present it as a nested outline:

```
1. [top-level region]
2. [top-level region]
   2.1 [child]
   2.2 [container component]
       ├─ [child of container]
       └─ [child of container]
```

Confirm: *"Does this structure match how you'd break it down, or should I adjust it?"*

Wait for confirmation before going further. A wrong hierarchy compounds into wrong analysis for every node after it.

### Step 3: Choose where to drill in

Don't default to walking the hierarchy top-to-bottom on your own — ask which node to look at first: *"Which section do you want to drill into first — [list the top-level and container nodes from Step 2]?"*

## Phase 2 — Section by section

Cover **one node at a time**, starting with whichever the user picked — never dump the whole image's analysis in a single pass. Going node by node keeps each piece small enough to actually verify, instead of producing one long analysis nobody can review.

For each node, describe its layout in a line or two, then list its elements in a compact table — cheaper to write and easier to scan than a long bullet list. Include the control type (dropdown, radio, checkbox, text input, button, link, icon, etc.) wherever it's visually identifiable — a filled circle reads as a selected radio, a checked square as a checked checkbox, a chevron-suffixed field as a dropdown:

```
## [Node name]

**Layout:** [how its children are arranged — rows, columns, alignment]

| Element | Type | Visible content | Default value | Unclear? |
|---|---|---|---|---|
| [element] | [dropdown / radio / checkbox / input / button / etc.] | [label/copy if legible, or "not legible"] | [what's actually pre-filled/selected, or "none" — not the same as a placeholder] | [specific question — leave blank if clear] |
```

Keep "Default value" separate from a placeholder or hint text — a grayed-out placeholder like "Select an option" means the default value is *none*, not that value itself. Confusing the two is a common source of components that silently start in the wrong state.

For anything you can't make out cleanly — a low-res icon, cropped text, a color that could be one of several shades, an ambiguous component (is that a button or a tag? a checkbox or a toggle?) — fill in the "Unclear?" column with a specific question about that exact detail rather than picking the most likely answer, and leave "Type" as "unclear" too if even the control kind isn't certain. "Probably a button" is a guess; naming exactly what's unclear and asking is not. Don't pad the table with questions where nothing is actually unclear — an empty "Unclear?" column across the board is a fine outcome.

Present one node, then ask which node to look at next from what's left — keep asking until every node from Step 2 has been covered.

## Phase 3 — Summarize everything

Once every node has been covered, pull it all back together into one final artifact — the per-node tables were shown one at a time, scattered across several messages, so the user needs a single place with the full detail to review before implementation starts. Reproduce every node's complete table here, not a shortened recap:

```
## Summary

[1-2 sentence recap of what this screen/image is — from Step 1]

### Structure
[the Step 2 hierarchy outline, re-drawn with each node annotated by what Phase 2 actually found in it — e.g. control counts or a short tally. This isn't a copy-paste of Step 2: use it as a correctness check, walking every node and confirming everything captured in its Phase 2 table is accounted for here, and that nothing surfaced during drill-in belongs under a different parent than Step 2 assumed. If drilling in revealed the hierarchy should change, fix it here and say so.

Example:
1. Top bar
2. Sidebar
3. Content area
   3.1 Page header — title + timestamp
   3.2 Search filter card
       ├─ Work period fields — 2 radios, 1 date range input, 2 dropdowns
       ├─ Evaluation criteria — 1 dropdown
       ├─ Evaluation options — 6 checkboxes
       └─ Actions — 2 buttons
]

### [Node name]
| Element | Type | Visible content | Default value | Unclear? |
|---|---|---|---|---|
| ... full table exactly as confirmed in Phase 2 for this node ... |

### [Node name]
| Element | Type | Visible content | Default value | Unclear? |
|---|---|---|---|---|
| ... repeat for every node ... |

## Open questions before implementation

1. [question]
2. [question]
```

If the open-questions list is empty, say so explicitly and confirm the user is ready for implementation to start. If it's not empty, resolve every item before writing any code — don't start implementing the nodes that were clear while questions on other nodes are still open, since answers can change how the whole hierarchy is read.

## Phase 4 — Adapter

Once Phase 3's summary is clean, ask which UI library or component system this project uses (e.g. shadcn/ui, Ant Design, MUI, Chakra, a custom internal library) — don't assume or guess it, every project's answer is different and it changes which concrete component every element below maps to.

Once you have the answer, go through every element captured in Phase 3 and map it to a concrete component in that library. Keep the component name and any notes in separate columns — cramming both into one cell is harder to scan. **One row per element, exactly matching Phase 3's rows** — never merge several elements into one row just because they share a type or sit in the same group (six checkboxes are six rows, not one row summarizing "6 checkboxes"):

```
## Component mapping — [library name]

| Element | Component | Notes |
|---|---|---|
| [element] | `<ComponentName>` | [props/usage notes, or an uncertainty flag] |
| [next element] | `<ComponentName>` | ... |
```

Apply the same no-guessing rule here as everywhere else in this skill: if you're not confident the library actually has a matching component for something, leave "Component" as "unclear" and put the specific question in "Notes" (e.g. "not sure this library has X — does it, or should this be composed from Y + Z?") instead of naming a component that might not exist — a confidently wrong component name is worse than an honest "not sure, does it?"

### After the mapping

Ask whether the mapping is correct, using a structured question like every other checkpoint in this skill. If the user flags something, fix it and ask again.

Once approved, produce one more artifact: a compact dump of everything gathered across every phase, meant to be handed to the implementation step as context — not for a human to re-read, so don't reuse the readable markdown tables from Phase 2-4. Optimize for token count over presentation here specifically; a terse notation is fine even though it wouldn't be in the earlier phases. A nested-hierarchy shape is usually natural, but use whatever's most compact for what was actually found — one line per node, elements packed densely, open items marked with a short inline flag instead of a full sentence:

```
[NodeName]: Element(Component, key fact, ⚠open question) Element(Component, key fact) ...
[NodeName]: ...
```

## Non-negotiable rules

- **Never state something is in the image that you can't actually verify is there.** If a detail is illegible, cropped, ambiguous, or just not visible at the resolution you have, say so and ask — don't fill the gap with what would typically be there.
- **Preserve real component structure.** Don't flatten a child element (like a form's own action buttons) into a top-level sibling section just because it's visually distinct — nest it under the container it actually belongs to.
- **One node at a time.** Resist compressing the whole image into a single summary.
- **Text first.** Plain text — the nested outline and the element tables — is the default presentation and costs nothing extra to produce. Only reach for a rendered diagram if the user explicitly asks for one or the spatial layout is genuinely too complex to describe in text; it's not the default, since generating one costs meaningfully more (loading design-system guidance before it can even draw a box).
- **Never assume the UI library.** Ask in Phase 4 — don't infer it from the screenshot's visual style or default to whatever's most common.
- **Every single confirmation point uses the structured question tool, no exceptions.** This includes the "which node next" ask at the end of every Phase 2 node, not just the big checkpoints — it's easy to let that one slide back into plain prose since it feels like a small aside, but it's still a decision point and needs to be clickable too. If a response ends without one of these when a decision is pending, that's a miss to correct next turn, not a one-off allowed to slide.
- **No code before Phase 4 is clean.** The analysis and the component mapping are the deliverables of this skill; implementation only starts once the hierarchy, every open question, and the component mapping are all confirmed.
- If the user pushes back on a hierarchy call, a read of an element, or a component mapping, redo that piece — don't defend the original guess.
