#!/usr/bin/env python3
"""Search the workspace catalog BEFORE creating an input or output (mandatory in update mode).

  catalog_search.py "<terms>" [more terms …] [--type input|output] [--export <file>] [--all]

Looks for every term (accent- and case-insensitive, word stems) in key, label, description, legalBasis and
option values/names/descriptions of the live catalog (or of an export file), and ranks the entries. Use several
wordings of the need (the legal notion, the raw fact, the article number: "L. 211-83", "plaisance", "bateau").

Reading the result:
- an entry clearly covering the need → REUSE it (do not create a synonym);
- an entry partially covering it (e.g. a select without the needed option, a close notion) → DOUBT;
- DOUBT, or several candidates → STOP and ask the user (AskUserQuestion) with the candidates before creating
  anything; adding an option to an existing select is a change of that key: ask as well.
"""
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s)


def stems(term):
    words = [w for w in norm(term).split() if len(w) > 2 or w.isdigit()]
    return [w[:6] if len(w) > 6 and not w.isdigit() else w for w in words]


def load(args):
    if "--export" in args:
        d = json.load(open(args[args.index("--export") + 1]))
        return d["catalog"].get("inputs", []), d["catalog"].get("outputs", [])
    from _cfg import call, config, ws_path
    cfg = config()
    st, ins = call(cfg, "GET", ws_path(cfg, "/inputs"))
    st2, outs = call(cfg, "GET", ws_path(cfg, "/outputs"))
    if st != 200 or st2 != 200:
        sys.exit(f"catalog read failed: {st} {st2}")
    return ins, outs


def text_of(k):
    parts = [k.get("key"), k.get("label"), k.get("description"), k.get("legalBasis")]
    for o in k.get("options") or []:
        parts += [o.get("value"), o.get("name"), o.get("description")]
    return norm(" ".join(p for p in parts if p))


def main():
    args = sys.argv[1:]
    terms = [a for i, a in enumerate(args) if not a.startswith("--") and (i == 0 or args[i - 1] not in ("--type", "--export"))]
    if not terms:
        sys.exit(__doc__)
    ins, outs = load(args)
    kind = args[args.index("--type") + 1] if "--type" in args else None
    entries = ([("INPUT", k) for k in ins] if kind != "output" else []) + ([("OUTPUT", k) for k in outs] if kind != "input" else [])
    all_stems = [s for t in terms for s in stems(t)]
    ranked = []
    for typ, k in entries:
        txt = text_of(k)
        hits = [s for s in all_stems if s in txt]
        head = norm(f"{k.get('key')} {k.get('label')}")
        score = len(set(hits)) * 2 + sum(1 for s in set(hits) if s in head)
        if score:
            ranked.append((score, typ, k, sorted(set(hits))))
    ranked.sort(key=lambda r: -r[0])
    limit = None if "--all" in args else 15
    for score, typ, k, hits in ranked[:limit]:
        opts = [o["value"] for o in k.get("options") or []]
        print(f"[{score:2}] {typ:6} {k['key']}  —  {k.get('label')}")
        print(f"       {(k.get('description') or '')[:220]}")
        if opts:
            print(f"       options: {opts[:20]}{' …' if len(opts) > 20 else ''}")
        print(f"       legalBasis: {k.get('legalBasis')}  | default: {k.get('defaultValue')}  | matched: {hits}")
    if not ranked:
        print("no candidate: a new key may be justified (still state why in the report)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
