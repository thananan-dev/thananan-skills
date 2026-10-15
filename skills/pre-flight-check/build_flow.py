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
COMMENT_PREFIXES = ("//", "#", "/*", "*", "--", "<!--", '"""', "'''")


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
    """Check that the declaration n["name"] names sits on n["file"]:n["line"] exactly."""
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
    name = str(n.get("name", ""))
    # A node about the file itself (a migration, a config file) names the file:
    # there is no single declaration line to check.
    if path.name in name:
        return None
    # A display name is not a source string: "`CriteriaConfigHandlers.Update`",
    # "(*Employee).VerifyEligibilitiesWith", "SQL `CreateIncentiveUpload`",
    # "`DefaultCriteriaConfigs` (Reset)". Match its identifiers as whole words.
    tokens = [t for t in re.findall(r"[A-Za-z_$][\w$]*", name) if len(t) >= 3]
    # "Type.Method" or "(*Type).Method": only the member is the declaration's own
    # name; the type also appears on its constructor and on sibling methods.
    member = re.search(r"[\w)]\.([A-Za-z_$][\w$]*)", name)
    if member:
        tokens = [member.group(1)]
    if not tokens:
        return None
    pattern = re.compile(r"(?<![\w$])(?:" + "|".join(map(re.escape, tokens)) + r")(?![\w$])")
    # The cited line must be the declaration itself: a window would let an
    # off-by-one or off-by-two line pass, which is the mistake this check exists for.
    # A doc comment usually names its function on the line above, so comment lines
    # never count, except sqlc's "-- name: X", which is the declaration.
    def declares(k: int) -> bool:
        text = lines[k - 1].strip()
        if text.startswith(COMMENT_PREFIXES) and not re.match(r"--\s*name:", text):
            return False
        return bool(pattern.search(text))

    if declares(line):
        return None
    nearby = [k for k in range(max(1, line - 15), min(len(lines), line + 15) + 1) if declares(k)]
    hint = f" — did you mean line {min(nearby, key=lambda k: abs(k - line))}?" if nearby else ""
    return f'none of {tokens} is on {file}:{line}{hint}'


def check(data: dict, root: pathlib.Path | None = None) -> list[str]:
    root = root or pathlib.Path.cwd()
    layers, problems, skip_layer_check = check_lanes(data)
    for chain in data.get("chains", []):
        ids = {n["id"] for n in chain["nodes"]}
        by_id = {n["id"]: n for n in chain["nodes"]}
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
                else:
                    # Sub-calls are lettered off the main step they hang from, nested
                    # or not: under [2.2], lockEligibility is 2.2a and the GetLatest it
                    # calls is 2.2b with parent 2.2a.
                    top, seen = parent, set()
                    while by_id[top].get("sub") and by_id[top].get("parent") in by_id and top not in seen:
                        seen.add(top)
                        top = by_id[top]["parent"]
                    if not re.fullmatch(re.escape(top) + r"[a-z]+", str(n.get("id", ""))):
                        problems.append(f'{where}: sub node id should be its main step\'s id followed by a letter (e.g. "{top}a"), got "{n.get("id")}"')
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
