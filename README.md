# thananan-skills

Personal Claude Code skills, named like a mission log — each one scouts the terrain before it lets you touch a single line of code. No npm registry publish, installed straight from this GitHub repo.

## Install

```sh
npx skills@latest add thananan-dev/thananan-skills
```

This picks up the skills listed in `.claude-plugin/plugin.json` and walks you through choosing which ones to install and for which coding agent(s).

## Skills

- **moon-scout** — analyzes a UI screenshot/SVG section by section before writing any component code, and asks instead of guessing when something is unclear.
- **mission-log** — drafts a Merge/Pull Request description (Summary / Changes / Test plan) from the branch's git history, after asking for the context that isn't in the diff.
- **pre-flight-check** — turns the current uncommitted diff into one interactive page (`FLOW.html`): the call chains the change runs through, every function's file/caller/why/what-changed, and the impacts — so a reviewer can walk the whole change without opening another file.
