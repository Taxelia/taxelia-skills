#!/usr/bin/env python3
"""Workspace operations on the API of ingest.json (key from <work>/.apikey, never printed).

  ws.py list
  ws.py create --id <id> --name "<name>" [--description "<text>"] [--strict]
  ws.py strict on|off                 # PATCH strictInputs (never flip a production workspace without asking)
  ws.py export [--out <file>]         # full catalog + graphs, import format (default <work>/export-<date>.json)
  ws.py graphs                        # id, name, published version of each graph
  ws.py refresh                       # recompile the workspace, prints the duration
"""
import datetime
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _cfg import call, config, ws_path  # noqa: E402


def arg(name, default=None):
    a = sys.argv
    return a[a.index(name) + 1] if name in a else default


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    cfg = config()
    if cmd == "list":
        st, res = call(cfg, "GET", "/workspaces")
        for w in res if st == 200 else []:
            print(f"{w['id']:24} {w['name']:32} graphs={w.get('graphCount')} keys={w.get('catalogCount')} strict={w.get('strictInputs')}")
        return 0 if st == 200 else print(st, res) or 1
    if cmd == "create":
        body = {"id": arg("--id", cfg["workspace"]), "name": arg("--name"), "strictInputs": "--strict" in sys.argv}
        if arg("--description"):
            body["description"] = arg("--description")
        st, res = call(cfg, "POST", "/workspaces", body)
        print(st, res)
        return 0 if st == 201 else 1
    if cmd == "strict":
        st, res = call(cfg, "PATCH", ws_path(cfg), {"strictInputs": sys.argv[2] == "on"})
        print(st, res)
        return 0 if st == 200 else 1
    if cmd == "export":
        out = arg("--out") or os.path.join(cfg["work"], f"export-{datetime.date.today()}.json")
        st, res = call(cfg, "GET", ws_path(cfg, "/graphs/export"))
        if st != 200:
            print(st, res)
            return 1
        json.dump(res, open(out, "w"), ensure_ascii=False, indent=1)
        print(f"{out}: {len(res.get('graphs', []))} graphs, {len(res['catalog'].get('inputs', []))} inputs, "
              f"{len(res['catalog'].get('outputs', []))} outputs")
        return 0
    if cmd == "graphs":
        st, res = call(cfg, "GET", ws_path(cfg, "/graphs"))
        for g in res if st == 200 else []:
            print(f"{g['id']:44} name={g.get('name')!s:28} published={g.get('publishedVersion')}")
        return 0 if st == 200 else 1
    if cmd == "refresh":
        t = time.time()
        st, res = call(cfg, "POST", ws_path(cfg, "/refresh"))
        print(st, f"{time.time() - t:.1f}s")
        return 0 if st == 200 else 1
    sys.exit(__doc__)


if __name__ == "__main__":
    sys.exit(main())
