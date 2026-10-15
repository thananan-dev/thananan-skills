---
name: pre-flight-check
description: Turn the current diff into one interactive page, FLOW.html — the code call chains the change runs through, laid out in layer lanes with arrows, every function (changed or not) clickable to read its file, caller, why it is called, what happens inside step by step, what changed and why its types look that way; plus the impacts, a summary of every changed doc and a test map. By default scope is the uncommitted diff only (staged + unstaged + untracked); pass --branch (or --branch=<base>) to widen it to every commit ahead of the base branch as well. Writes to .claude/reviews/<branch>/. Use when the user says "ช่วยรีวิว", "พารีวิว", "อธิบาย diff", "diff เยอะ อ่านไม่รู้เรื่อง", "review walkthrough", "pre-flight check", "ขอ flow", "walk me through this branch/MR", "รีวิวทั้ง branch/MR", or invokes /pre-flight-check. Not a bug hunt against standards — for that use /code-review; this skill makes the change understandable first.
---

A diff lists files alphabetically; a reviewer needs them in the order the code **runs**, with every step explained in one place. This skill produces exactly one deliverable: **`FLOW.html`**, built from a `flow.json` you write. No chapters, no markdown tour files.

Talk to the user in **Thai**. Code identifiers, file paths and SQL stay as-is.

**Reader = someone new to this project.** Assume they do not know the business, the vocabulary or the code layout, and that the diff was produced by an AI from a requirement they only skimmed. The page must let them understand the whole change without opening another file.

Files in this skill: [`flow-viewer.html`](flow-viewer.html) (the page template), [`build_flow.py`](build_flow.py) (validates `flow.json` and builds the page), [`TEMPLATES.md`](TEMPLATES.md) (the `flow.json` schema — read it before writing).

## 1. Fix the scope

Two modes — pick one before reading anything, and say which one in the `scope` line:

- **Default — uncommitted only:** `git diff HEAD` (staged + unstaged) **+ untracked files** (`git status --porcelain`, read untracked files whole). Committed work has already been read — never include it, even when the branch has commits ahead of its base. The narrowing argument `--staged` limits this further to `git diff --cached` only (no untracked).
- **`--branch` (or `--branch=<base>`) — the whole branch:** everything the default mode covers **plus every commit ahead of the base branch**. Find the base the same way as any MR/PR write-up would — the repo's actual default branch (`git remote show origin` or `git symbolic-ref refs/remotes/origin/HEAD`, typically `main`/`master`/`develop`), or whatever `--branch=<base>` names; ask if it's genuinely ambiguous. Scope is then `git diff <merge-base>...HEAD` (committed, using the triple-dot merge-base form so commits made on the base branch after this branch forked don't leak in) **+** the uncommitted diff on top. Use this mode whenever the user asks to review the branch/MR as a whole, not just the latest edit — "walk me through this branch", "รีวิวทั้ง branch", "ครอบ commit ด้วย" — or whenever they explicitly ask for it.
- In `--branch` mode, commits ahead of the base **are** in scope: mark their functions 🆕/✏️ and grade them for impact exactly like uncommitted code. Code already on the base branch itself (reached before this branch forked) is still read-only context, never marked changed. In the default mode, nothing committed is ever marked 🆕/✏️ — never claim something "is not built yet" without checking recent commits first, it may already be committed (and therefore already in scope or already read, depending on mode).
- If the resolved scope is empty (nothing uncommitted in default mode; branch has no commits ahead of base and nothing uncommitted in `--branch` mode), say so and stop.
- Output dir: `.claude/reviews/<branch-with-/-replaced-by-->/` (git-ignored). Record which mode produced the page as part of `scope` (e.g. include the base branch + its sha for `--branch` mode). If the dir already holds a `flow.json`, compare its recorded `scope` against a freshly computed fingerprint for the **same mode** (current `HEAD` sha + working-tree `--shortstat`, plus — in `--branch` mode — the base's sha and `git diff --shortstat <merge-base>...HEAD`): unchanged → reuse and just send the page; changed, or the requested mode differs from what's recorded → find what moved (`find … -newer flow.json`, then diff), update `flow.json`, rebuild, and tell the user what changed.

## 2. Read everything

Read the full diff — never review from `--stat` alone. Sort files into: schema (migrations), domain/business logic, data access (SQL, ORM queries, repositories), generated (ORM/codegen output such as sqlc, Prisma, an OpenAPI client, a router's generated route tree — confirm it matches its source, don't explain it), flow (application/service layer, infra adapters, handlers/controllers, frontend components/hooks/pages), wiring (module/DI setup, route registration, env/config), test, doc (API-contract files such as OpenAPI/Swagger, a Postman/Bruno/Insomnia collection, a GraphQL schema; specs, ADRs, READMEs) — treat this as a starting shape, not a fixed list: rename or drop a category that doesn't exist in this repo's stack, and add one that does.

Get the business context from the feature's requirement docs (user stories, PRD, ADR — wherever the repo keeps them, e.g. `docs/features/<feature>/`), not only from the diff. Read the repo's `CLAUDE.md`/`AGENTS.md` first for its layers, test commands and conventions.

## 3. Build the chains

Before tracing anything, pick the **lanes** (`flow.json`'s top-level `lanes`, schema in `TEMPLATES.md`) to match this repo's own architecture — don't assume a backend-shaped `api|app|domain|infra|db` split if the diff is frontend-only or the project is laid out differently. `lanes` is shared across every chain/tab in the page, so pick one set wide enough to cover everything this diff touches. A few shapes to start from, but read the actual code structure rather than guessing from the stack name:
- **Backend, layered:** `api | app | domain | infra | db` (the default when `lanes` is omitted).
- **Frontend, component-driven:** e.g. `page | component | hook | store | api-client`.
- **Full-stack diff touching both sides:** one lane set spanning FE → BE (e.g. `ui | client | api | service | db`), then one chain per entry point as usual — a backend-only chain simply leaves the FE lanes empty for its nodes, and vice versa.
3–6 lanes is the usual range; every node's `layer` must be one of the ids declared.

For every entry point the diff touches (boot/migration, each HTTP route, job/CLI mode, frontend page), trace the **function call chain the code actually executes**, through changed **and** unchanged functions, down to storage and back. Verify every node by reading the code and grepping the call site — never infer a chain from file names. Number nodes `[chain.step]`; sub-calls get `[2.4a]`, `[2.4b]` with `sub: true` and a `parent`.

Every node is a card:

| field | content |
|---|---|
| `file`, `line` | where the function is |
| `caller` | who calls it, with line |
| `why` | why it is called — what breaks without it, why it sits here in the order |
| `inside` | **the function body, step by step**: `[line, what it does, why / what it answers when it fails]` — every validation, branch, call, early return, error→HTTP mapping, transaction boundary. **⚪ nodes get it too**: "not changed" is not "understood". Only a pure pass-through may skip it. Every line number comes from the file, never an estimate. |
| `changed` | `[before, after]` for ✏️/🆕 |
| `types` | every type added or changed on this node: `[type, file:line, why it has this shape]` — why a new type instead of an existing one, why this primitive vs another (e.g. `string` vs a dedicated value type), why nullable/optional, why a pointer/reference, generated or not |
| `impact` | the impact that lands on this node, if any |

## 4. Find the impacts

This stays a **behaviour/correctness check, not a standards audit** — a11y, i18n, visual polish and the like belong to `/code-review`, not here. A new file is rarely risky; a changed line in code that already runs is. Hunt for each, grepping callers/consumers before claiming "no impact". Skip an item entirely when nothing in the diff touches that kind of code (e.g. a frontend-only diff has nothing to say about item 5's database half):

1. Changed behaviour in an existing code path (branch, default, ordering, rounding, filter, status transition, loading/error/empty-state transition).
2. Changed function/struct/interface/component/prop signatures → every caller, including tests and any consumer outside this package/module (exported hooks, components, public API).
3. API contract: new/renamed/removed fields, status/error codes, params, routes, permission/auth checks → who consumes it (the frontend's API client, e2e tests, other services) — including **deploy order** between backend and frontend when one can ship before the other.
4. Stale or out-of-sync state: backend — writes outside a transaction boundary, lock ordering, idempotency on retry; frontend — state not reset when its driving prop changes, a client-side cache left stale after a mutation, a fetch resolving after its component has unmounted.
5. Database: effects on existing rows (NOT NULL without default, backfill, index on a big table, rewrites, down migration).
6. Wiring: a route, job, or page registered without the auth/guard the rest of the repo applies on siblings.
7. Config/env/feature flags: new keys present in every deploy env file and its example/template; feature flags enabled where the feature must actually run.
8. Docs ↔ code drift.
9. Test gaps: changed behaviour no test would catch if it regressed.

**Before grading or proposing a fix, re-check each impact** — first impressions over-grade:
- **When can it actually happen?** Trace the exact conditions (e.g. "fails only if the DB drops between two back-to-back queries", "only when the list is empty on first paint") — rare paths are 🟡, not 🟠.
- **Is it the repo's existing pattern?** Compare with sibling features (other handlers, other pages/components built the same way). Matching an accepted pattern is not a finding.
- **Is it already tested elsewhere?** A gap in the new test file may be covered by an older test — grep the function/component name across the test suite.
- **Run the repo's own checks** — read `CLAUDE.md`/`AGENTS.md`/`package.json` scripts/`Makefile` for the actual commands rather than assuming a stack; typically build/typecheck, unit tests of the touched module(s), and integration/e2e tests with the repo's env loader (env-gated tests silently skip without it — check for a `--- SKIP` or equivalent). Check the test DB isn't the dev DB first. A failure is only an impact of this diff after you confirm it is caused by it (e.g. leftover rows in the test DB are not).

Grade: `red` 🔴 ต้องตัดสินใจ/อาจพัง · `orange` 🟠 เปลี่ยนพฤติกรรมเดิม — ต้องรู้ · `yellow` 🟡 ควรดู. Each says what concretely changes for whom and points at a node (or `""` when outside the chains). Never pad.

## 5. Write flow.json and build the page

Write `flow.json` (schema in `TEMPLATES.md`) with:

- `why` — 2–3 lines: before → after, plus a one-line glossary of the terms the cards use.
- `impacts` — from step 4.
- `chains` — one per entry point, nodes in call order.
- `pages` — three content tabs:
  - **เอกสารที่แก้** — every changed doc grouped by format (an API-spec file such as OpenAPI/Swagger or a Postman/Bruno collection, spec/BDD/ADR, README): what a reader of that doc now believes (before → after) and whether the code matches (✅ / ❌ with `file:line`).
  - **Tests** — what was run and the result, each test mapped to the node/impact it proves, what is not covered.
  - **ข้อเสนอ** — **only what you actually recommend doing**, after the re-check above, as one table sorted by criticality: `| ระดับ | ข้อเสนอ | ทำไม | ที่ |`, level 🔴 / 🟠 / 🟡 (same scale as impacts). Nothing else on this tab: no "not doing" list, no scope verdicts, no ready-to-paste MR text, no verification log. If nothing is worth recommending, say so in one line. Verification notes that justify dropping an impact go to the **Tests** tab (or the impact's own text), not here.

Then build it with the script in **this skill's directory** (the base directory shown when the skill loads), open the page in a browser (the in-app browser pane when the host has one) to check it renders at a wide and a phone-sized viewport, and fix anything broken:

```bash
python3 <skill-dir>/build_flow.py .claude/reviews/<branch>/flow.json
```

The script refuses a node without `why`, a bad `layer`/`status`, a sub node without a parent, or a ✏️ node without `changed`.

## 6. Hand it over

1. Send `FLOW.html` with SendUserFile (`display: "render"`) when the host has it; otherwise give its path and the command to open it (`open` on macOS, `xdg-open` on Linux, `start` on Windows).
2. In chat keep it short: the scope line, the why (2–3 lines), the 🔴/🟠 impacts as a short list, and which node to click first. Do not paste chain tables or cards into chat — the page is the deliverable.
3. When the reviewer asks something: answer from the code (read it again), and if the answer reveals a new impact or a mistake, fix `flow.json`, rebuild, re-send, and say what changed. Do not edit source code — this is review only.

## Rules

- Accuracy over coverage: every claim cites `file:line`; if unsure, write "ยังไม่ได้ยืนยัน" and check.
- Don't restate the diff. Explain *why the code does it* and *what it means for the system*.
- No markdown tour files, no chapters, no Mermaid, no ASCII diagrams — only `flow.json` → `FLOW.html`.
