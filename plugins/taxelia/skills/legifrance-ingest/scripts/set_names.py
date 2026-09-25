#!/usr/bin/env python3
"""Put or remove the temporary names `t__<id>` of the secondary graphs (so per-graph suites can run).

  set_names.py on            # every secondary graph gets name = t__<id>
  set_names.py off           # secondary graphs lose their name (production state: one named graph)
  set_names.py off --only=id1,id2
  set_names.py on --dry

The graphs are taken from the LIVE export (their content is not changed, only `name`), so this works whatever the
generators produced. The primary graph (`primary_id` of ingest.json) always keeps `primary_name`.
Remember: re-importing a single generated graph brings its t__ name back → run `off` again afterwards.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _cfg import call, config, ws_path  # noqa: E402


def main():
    a = sys.argv[1:]
    if not a or a[0] not in ("on", "off"):
        sys.exit(__doc__)
    cfg = config()
    only = next((x.split("=", 1)[1].split(",") for x in a if x.startswith("--only=")), None)
    st, res = call(cfg, "GET", ws_path(cfg, "/graphs/export"))
    if st != 200:
        print(st, res)
        return 1
    graphs = [g for g in res["graphs"] if not only or g["id"] in only]
    for g in graphs:
        if g["id"] == cfg["primary_id"]:
            g["name"] = cfg["primary_name"]
        elif a[0] == "on":
            g["name"] = "t__" + g["id"]
        else:
            g.pop("name", None)
    tmp = os.path.join(cfg["work"], ".set_names.json")
    import json
    json.dump({"graphs": graphs}, open(tmp, "w"), ensure_ascii=False)
    imp = [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "imp.py"), tmp,
           "--work", cfg["work"]] + (["--dry"] if "--dry" in a else [])
    return subprocess.call(imp)


if __name__ == "__main__":
    sys.exit(main())
