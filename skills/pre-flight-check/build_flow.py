"""Build a review's FLOW.html from its flow.json.

Usage: python3 <skill-dir>/build_flow.py .claude/reviews/<branch>/flow.json
Run it with the repo root as the working directory — every node's "file" is
resolved relative to cwd, the same way the path would read in a diff.
Writes FLOW.html next to the JSON. The JSON shape is documented in TEMPLATES.md (§ flow.json).
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

DEFAULT_LAYERS = ["api", "app", "domain", "infra", "db"]
STATUSES = {"new", "changed", "same"}
MIN_LANES, MAX_LANES = 2, 6


def check_lanes(data: dict) -> tuple[set, list[str], bool]:
    """Returns (valid layer ids, problems, skip_layer_check)."""
    problems: list[str] = []
    lanes = data.get("lanes")
    if lanes is None:
        return set(DEFAULT_LAYERS), problems, False
    if not isinstance(lanes, list):
        problems.append(f'lanes: must be a list of lane objects, got {type(lanes).__name__}')
        return set(), problems, True
    if len(lanes) == 0:
        problems.append('lanes: if provided, must not be empty — list at least 2 lanes, or omit "lanes" entirely to use the default 5')
        return set(), problems, True
    if not (MIN_LANES <= len(lanes) <= MAX_LANES):
        problems.append(f'lanes: must have {MIN_LANES}-{MAX_LANES} lanes, got {len(lanes)}')
        return set(), problems, True
    ids = []
    for lane in lanes:
        if not isinstance(lane, dict):
            problems.append(f'lanes: each lane must be an object with an id and a name, got {lane!r}')
            continue
        if not lane.get("id") or not lane.get("name"):
            problems.append(f'lanes: each lane needs an id and a name, got {lane}')
            continue
        ids.append(lane["id"])
    if len(ids) != len(set(ids)):
        problems.append("lanes: lane ids must be unique")
    if not ids:
        return set(), problems, True
    return set(ids), problems, False


def check_file_line(n: dict, root: pathlib.Path) -> str | None:
    """Best-effort check that n['name'] actually appears near n['file']:n['line']."""
    file, line = n.get("file"), n.get("line")
    if not file or line is None:
        return None
    try:
        line = int(line)
    except (TypeError, ValueError):
        return f'"line" must be a number, got {n.get("line")!r}'
    path = root / file
    if not path.is_file():
        return f'file not found: "{file}" (resolved against {root})'
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as e:
        return f'could not read "{file}": {e}'
    if not (1 <= line <= len(lines)):
        return f'"{file}" only has {len(lines)} lines, "line": {line} is out of range'
    # Heuristic identifier extraction: strip markdown backticks/JSX angle brackets and
    # any call-style parens, so `` `lockEligibility` ``, "<OrderList>" and
    # "processOrder()" all compare against the raw source line correctly.
    name = re.sub(r"[`<>]", "", str(n.get("name", "")))
    name = re.sub(r"\(.*\)\s*$", "", name).strip()
    if not name:
        return None
    window = lines[max(0, line - 3): line + 5]
    if not any(name in l for l in window):
        return f'"{name}" not found near {file}:{line} (checked lines {max(1, line - 2)}-{line + 5}) — line number looks off'
    return None


def check(data: dict, root: pathlib.Path | None = None) -> list[str]:
    root = root or pathlib.Path.cwd()
    layers, problems, skip_layer_check = check_lanes(data)
    for chain in data.get("chains", []):
        ids = {n["id"] for n in chain["nodes"]}
        for n in chain["nodes"]:
            where = f'{chain.get("tab")} [{n.get("id")}]'
            if not skip_layer_check and n.get("layer") not in layers:
                problems.append(f"{where}: layer must be one of {sorted(layers)} (declared in flow.json's \"lanes\", or the default {DEFAULT_LAYERS} when omitted)")
            if n.get("status") not in STATUSES:
                problems.append(f"{where}: status must be one of {sorted(STATUSES)}")
            if n.get("sub"):
                parent = n.get("parent")
                if parent not in ids:
                    problems.append(f"{where}: sub node needs a parent id from the same chain")
                elif not re.fullmatch(re.escape(parent) + r"[a-z]+", str(n.get("id", ""))):
                    problems.append(f'{where}: sub node id should be its parent id followed by a letter (e.g. "{parent}a"), got "{n.get("id")}"')
            if not n.get("why"):
                problems.append(f"{where}: why is required")
            if n.get("status") == "changed" and not n.get("changed"):
                problems.append(f"{where}: a changed node needs changed: [before, after]")
            file_problem = check_file_line(n, root)
            if file_problem:
                problems.append(f"{where}: {file_problem}")
    return problems


def main() -> None:
    src = pathlib.Path(sys.argv[1])
    data = json.loads(src.read_text(encoding="utf-8"))
    problems = check(data)
    if problems:
        sys.exit("flow.json problems:\n  " + "\n  ".join(problems))
    template = (pathlib.Path(__file__).parent / "flow-viewer.html").read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    out = src.with_name("FLOW.html")
    out.write_text(template.replace("/*FLOW_DATA*/", payload), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
