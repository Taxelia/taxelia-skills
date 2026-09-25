#!/usr/bin/env python3
"""Replay /search scenarios against the API of ingest.json and report mismatches.

  run_scenarios.py <tests/*.json> [--work <dir>]

Scenario file: a JSON list of
  {"name": "...", "tree": "<graph name>", "inputs": {"key": "value", ...},
   "outputs": ["tax_rate"],               # optional: requested outputs sent with the request
   "expect": {"key": "value"},            # first value (text) or first text (localized) must equal, as string
   "contains": {"key": "substring"},      # some value/text of the key contains the substring
   "absent": ["key", ...],                # key must not be in the outputs
   "required": ["key", ...],              # these keys must be in inputs.required
   "not_required": ["key", ...],          # these keys must NOT be in inputs.required
   "defaulted": ["key", ...],             # these keys must be in inputs.defaulted
   "result": {"complete": true, "missingOutputs": []}}   # optional exact check of the result block
Expected values come from the LAW, never from what the graph returns. Exit code 1 when any scenario fails.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _cfg import call, config  # noqa: E402


def values_of(resp, key):
    for o in resp.get("outputs") or []:
        if o["key"] != key:
            continue
        if o.get("values") is not None:
            return [str(v) for v in o["values"]]
        return [t for tr in o.get("translations") or [] for t in tr.get("texts", [])]
    return None


def check(cfg, s):
    body = {"workspace": cfg["workspace"], "tree": s["tree"], "language": "fr",
            "conditions": [{"key": k, "value": v} for k, v in s.get("inputs", {}).items()]}
    if s.get("outputs"):
        body["outputs"] = s["outputs"]
    st, resp = call(cfg, "POST", "/search", body, auth=False)
    if st != 200:
        return [f"HTTP {st}: {str(resp)[:300]}"]
    errs = []
    for k, v in (s.get("expect") or {}).items():
        got = values_of(resp, k)
        if not got or got[0] != str(v):
            errs.append(f"{k}: expected {v!r}, got {got!r}")
    for k, sub in (s.get("contains") or {}).items():
        if not any(sub in g for g in values_of(resp, k) or []):
            errs.append(f"{k}: expected to contain {sub!r}, got {values_of(resp, k)!r}")
    for k in s.get("absent") or []:
        if values_of(resp, k) is not None:
            errs.append(f"{k}: expected absent, got {values_of(resp, k)!r}")
    inputs = resp.get("inputs") or {}
    req = [r["key"] for r in inputs.get("required", [])]
    dft = [d["key"] for d in inputs.get("defaulted", [])]
    for k in s.get("required") or []:
        if k not in req:
            errs.append(f"required {k} missing (required={req})")
    for k in s.get("not_required") or []:
        if k in req:
            errs.append(f"not_required {k} is required (required={req})")
    for k in s.get("defaulted") or []:
        if k not in dft:
            errs.append(f"defaulted {k} missing (defaulted={dft})")
    if "result" in s and resp.get("result") != s["result"]:
        errs.append(f"result: expected {s['result']}, got {resp.get('result')}")
    if errs:
        errs.append("outputs=" + json.dumps({o['key']: values_of(resp, o['key']) for o in resp.get('outputs') or []},
                                            ensure_ascii=False) + " required=" + json.dumps(req))
    return errs


def main():
    paths = [a for a in sys.argv[1:] if a.endswith(".json")]
    if not paths:
        sys.exit(__doc__)
    cfg = config()
    total = failed = 0
    for p in paths:
        for s in json.load(open(p)):
            total += 1
            errs = check(cfg, s)
            if errs:
                failed += 1
                print(f"FAIL [{os.path.basename(p)}] {s['name']}")
                for e in errs:
                    print("    " + e)
    print(f"{total - failed}/{total} scenarios passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
