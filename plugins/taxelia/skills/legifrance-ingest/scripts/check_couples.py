#!/usr/bin/env python3
"""Count (source, target) couples carrying several edges, fallback included (rule: one edge per couple).

  check_couples.py            # live export of the workspace of ingest.json
  check_couples.py <dir>      # every graph of <dir>/*.json (generator output)
  check_couples.py -v …       # list each couple and its edges
Exit code 1 when a couple has several edges.
"""
import collections
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _cfg import call, config, ws_path  # noqa: E402


def cond_str(e):
    if e.get("fallback"):
        return "(repli)"
    sep = " OU " if e.get("match") == "any" else " ET "
    return sep.join(f"{c['key']} {c['operator']} {c['value']}" for c in e.get("conditions", []))


def main():
    args = [a for a in sys.argv[1:] if a != "-v"]
    dirs = [a for a in args if os.path.isdir(a)]
    if dirs:
        graphs = {}
        for p in sorted(glob.glob(os.path.join(dirs[0], "*.json"))):
            for g in json.load(open(p)).get("graphs", []):
                graphs[g["id"]] = g
        graphs = list(graphs.values())
    else:
        cfg = config()
        st, res = call(cfg, "GET", ws_path(cfg, "/graphs/export"))
        if st != 200:
            print(st, res)
            return 1
        graphs = res["graphs"]
    total = 0
    for g in sorted(graphs, key=lambda x: x["id"]):
        by = collections.defaultdict(list)
        for e in g["edges"]:
            by[(e["from"], e["to"])].append(e)
        bad = {k: v for k, v in by.items() if len(v) > 1}
        if not bad:
            continue
        total += len(bad)
        print(f"{g['id']}: {len(bad)} couple(s)")
        if "-v" in sys.argv:
            for (f, t), es in bad.items():
                print(f"  {f} -> {t}")
                for e in es:
                    print("     ", cond_str(e))
    print(f"graphs: {len(graphs)}  couples with several edges: {total}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
