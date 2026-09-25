#!/usr/bin/env python3
"""Import a file (catalog and/or graphs) into the workspace of ingest.json: dry run first, then the real import.

  imp.py <file.json> [more.json …] [--dry] [--chunk 2]

- Several files are merged (catalog entries and graphs by id; a later file wins).
- The catalog, if any, is imported alone first (it must exist before graphs using its keys).
- Graphs are imported in chunks (a single big transaction can exceed MongoDB's transaction lifetime → 500);
  every chunk is retried graph by graph once. A graph referencing another one of the same run must come in the same
  chunk or after it: the input order is kept, so write files bottom-up.
- Validation errors (422) are printed in full: fix the generator, never the API.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _cfg import call, config, ws_path  # noqa: E402


def load(paths):
    inputs, outputs, graphs = {}, {}, {}
    for p in paths:
        d = json.load(open(p))
        cat = d.get("catalog") or {}
        for k in cat.get("inputs", []):
            inputs[k["key"]] = k
        for k in cat.get("outputs", []):
            outputs[k["key"]] = k
        for g in d.get("graphs", []):
            graphs[g["id"]] = g
    catalog = {}
    if inputs:
        catalog["inputs"] = list(inputs.values())
    if outputs:
        catalog["outputs"] = list(outputs.values())
    return catalog, list(graphs.values())


def post(cfg, body, dry):
    return call(cfg, "POST", ws_path(cfg, "/graphs/import" + ("?dryRun=true" if dry else "")), body)


def main():
    args = [a for a in sys.argv[1:]]
    chunk = int(args[args.index("--chunk") + 1]) if "--chunk" in args else 2
    paths = [a for a in args if a.endswith(".json")]
    if not paths:
        sys.exit(__doc__)
    cfg = config()
    catalog, graphs = load(paths)
    body = {k: v for k, v in (("catalog", catalog), ("graphs", graphs)) if v}
    st, res = post(cfg, body, True)
    print("dry run:", st, json.dumps(res, ensure_ascii=False)[:4000])
    if st != 200 or "--dry" in args:
        return 0 if st == 200 else 1
    if catalog:
        st, res = post(cfg, {"catalog": catalog}, False)
        print("catalog:", st, res if st != 200 else f"{res.get('catalogUpserted')} upserted")
        if st != 200:
            return 1
    done = 0
    for i in range(0, len(graphs), chunk):
        part = graphs[i:i + chunk]
        st, res = post(cfg, {"graphs": part}, False)
        if st != 200:
            for g in part:
                st, res = post(cfg, {"graphs": [g]}, False)
                if st != 200:
                    print("import failed on", g["id"], st, json.dumps(res, ensure_ascii=False)[:4000])
                    return 1
                done += 1
            continue
        done += len(part)
    print(f"graphs imported: {done}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
