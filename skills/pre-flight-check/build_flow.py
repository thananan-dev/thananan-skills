"""Build a review's FLOW.html from its flow.json.

Usage: python3 <skill-dir>/build_flow.py .claude/reviews/<branch>/flow.json
Writes FLOW.html next to the JSON. The JSON shape is documented in TEMPLATES.md (§ flow.json).
"""

import json
import pathlib
import sys

DEFAULT_LAYERS = ["api", "app", "domain", "infra", "db"]
STATUSES = {"new", "changed", "same"}


def check(data: dict) -> list[str]:
    problems = []
    lanes = data.get("lanes")
    if lanes is not None:
        layers = []
        for lane in lanes:
            if not lane.get("id") or not lane.get("name"):
                problems.append(f"lanes: each lane needs an id and a name, got {lane}")
            else:
                layers.append(lane["id"])
        if len(layers) != len(set(layers)):
            problems.append("lanes: lane ids must be unique")
    else:
        layers = DEFAULT_LAYERS
    layers = set(layers)
    for chain in data.get("chains", []):
        ids = {n["id"] for n in chain["nodes"]}
        for n in chain["nodes"]:
            where = f'{chain.get("tab")} [{n.get("id")}]'
            if n.get("layer") not in layers:
                problems.append(f"{where}: layer must be one of {sorted(layers)} (declared in flow.json's \"lanes\", or the default {DEFAULT_LAYERS} when omitted)")
            if n.get("status") not in STATUSES:
                problems.append(f"{where}: status must be one of {sorted(STATUSES)}")
            if n.get("sub") and n.get("parent") not in ids:
                problems.append(f"{where}: sub node needs a parent id from the same chain")
            if not n.get("why"):
                problems.append(f"{where}: why is required")
            if n.get("status") != "same" and not n.get("changed") and n.get("status") == "changed":
                problems.append(f"{where}: a changed node needs changed: [before, after]")
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
