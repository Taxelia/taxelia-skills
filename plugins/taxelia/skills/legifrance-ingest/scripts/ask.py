#!/usr/bin/env python3
"""Ask the engine one question and print a readable answer (outputs, required, defaulted, result).

  ask.py '<json inputs>' [--tree <name>] [--outputs tax_rate,other] [--raw]

Default tree = primary_name of ingest.json. Use it to demonstrate a request to the user and to probe which
questions a request triggers (answer `required` step by step, like a chatbot would).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _cfg import call, config  # noqa: E402


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    cfg = config()
    tree = a[a.index("--tree") + 1] if "--tree" in a else cfg["primary_name"]
    body = {"workspace": cfg["workspace"], "tree": tree, "language": "fr",
            "conditions": [{"key": k, "value": v} for k, v in json.loads(a[0]).items()]}
    if "--outputs" in a:
        body["outputs"] = a[a.index("--outputs") + 1].split(",")
    st, r = call(cfg, "POST", "/search", body, auth=False)
    if "--raw" in a or st != 200:
        print("request:", json.dumps(body, ensure_ascii=False, indent=1))
        print("response:", st, json.dumps(r, ensure_ascii=False, indent=1))
        return 0 if st == 200 else 1
    for o in r["outputs"]:
        vals = o.get("values") or [t for tr in o.get("translations", []) for t in tr["texts"]]
        print(f"{o['key']}: {vals}")
    print("required:", [x["key"] for x in r["inputs"]["required"]])
    print("defaulted:", [(x["key"], x["value"]) for x in r["inputs"].get("defaulted", [])])
    print("result:", r.get("result"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
