# pre-flight-check — design decisions

Not loaded by the skill at review time — this is for whoever edits `SKILL.md`/`TEMPLATES.md`/`flow-viewer.html`/`build_flow.py` next. These 12 decisions came from repeated real-world use of this skill's predecessor (`guided-review`, a single-project version of the same idea) and each one exists because the opposite was tried and failed. Keep them when generalizing or trimming the skill further — re-introducing what they guard against is easy to do by accident while simplifying something else.

| # | Decision | Why |
|---|---|---|
| 1 | Review only what is not committed yet, as the **default** (`--branch` opts into the whole branch) | Committed work has already been read, and you must check recent commits before claiming anything "isn't built yet" |
| 2 | The flow is code-level, not business-level | A business-level A → B → C flow can't be traced through actual code — it has to be `Handler → Service → domain → Repo → SQL` |
| 3 | Every node states its file, who calls it, and why | The reviewer reads the code alongside the page — they need to know why this file, why this function, why this type change |
| 4 | An unchanged node still gets its `inside` steps traced | "Not changed" isn't the same as "understood" |
| 5 | One single web page — no markdown, no chapters | The reviewer needs the whole picture in one place, not a trail of links |
| 6 | No ASCII arrows or wide tables in chat | Wrapped lines look like new steps, and a wide table with long links is unreadable in a narrow chat column |
| 7 | Small diagram, wide resizable detail pane | A cramped detail pane makes the explanation unreadable |
| 8 | Every line number comes from the real file | Early runs had 20+ estimated line numbers that were simply wrong — every one now has to be grepped, and `build_flow.py` now also opens the file at build time to check the node's name actually appears near that line |
| 9 | Re-check every impact before grading it | The first pass over-graded things that only happen when the DB drops mid-query, that match an existing repo pattern, or that are already covered by another test |
| 10 | Run integration tests for real, with the repo's env loader | Without loading env first, env-gated tests silently skip and the run looks green when it proved nothing |
| 11 | The proposals tab holds only what's actually recommended | No "decided not to do this" list, no scope verdicts, no ready-to-paste MR text, no verification log |
| 12 | Re-check scope on every call | The branch may have been rebased or gained new commits between review sessions — the page has to catch that and rebuild |

## Later hardening (2026-10-16, from first real multi-project use)

Found by actually running the skill against real diffs after the Go+React-only version was generalized — `build_flow.py` previously accepted all of these silently or crashed instead of explaining what was wrong:

- A sub-node's `id` not matching `<parent><letter>` (e.g. parent `2.2`, child should be `2.2a`) — was never actually checked.
- `line` numbers that don't correspond to where the named function/component actually is — `build_flow.py` now opens `file` at `line` and checks the node's `name` appears nearby, instead of trusting the written number (this is decision #8 enforced in code, not just in prose).
- `"lanes": ["ui"]` (a list of strings instead of lane objects) crashed with an `AttributeError` instead of a readable error.
- `"lanes": []` produced the same confusing `layer must be one of []` message repeated once per node instead of one clear explanation.
- `SKILL.md` said lanes are "3–6" while `TEMPLATES.md` said "2–6", and neither was enforced — now 2–6 is the one canonical range and `build_flow.py` enforces it.
- The default lane descriptions still carried project-specific wording (`infra` read "repository / BigQuery") that would leak into any repo that didn't set its own `lanes`.

## Later hardening, round 2 (2026-10-16, the file/line check's own false positives)

The `file`/`line` check added in round 1 above (whole-string match in a ±few-line window) was itself wrong in exactly the way decision #8 exists to prevent — found by running it against a real `flow.json` that had every line number right and still got 17 nodes rejected:

- It matched the **whole display name** as a literal substring (`"CriteriaConfigHandlers.Update"`), but a display name isn't source text — Go writes that as `func (h CriteriaConfigHandlers) Update(`, never dotted. Every receiver method, and every name with a prefix like `SQL ...`/`migration ...`, failed this way. Fixed: extract identifier-like tokens (≥3 chars, whole-word match) from the name instead of matching the string verbatim; for a dotted `Type.Method` or `(*Type).Method` name, only the member name counts — the type name also appears on the constructor and on sibling methods, so matching it lets the wrong line pass.
- The window (`line-3` to `line+5`) was wide enough that an off-by-one or off-by-two citation — the exact mistake this check exists to catch — still passed. Fixed: the cited line must itself match (a comment/doc-comment line one above the real declaration doesn't count, except sqlc's `-- name: X`); if it doesn't, the nearest real declaration within ±15 lines is suggested as "did you mean line N?" instead of silently accepting a nearby line.
- A sub-node nested under another sub-node (parent chain `2.2` → `2.2a` → `2.2b`) was forced into `2.2aa` instead of `2.2b`. Fixed: walk the `parent` chain up to the nearest non-sub ancestor (the main numbered step) before checking the letter suffix, with a cycle guard.

Known gaps, left as-is: a node `name` with no real identifier in it (pure prose) gets a loose/skipped check; `inside` step line numbers aren't checked at all; `#` in `COMMENT_PREFIXES` means a cited C/C++ `#define` line is (wrongly) treated as a comment.
