#!/usr/bin/env python3
"""Compare two workspace exports (before / after an update) and list what changed.

  diff_export.py <before.json> <after.json> [-v]

Graphs added / removed / renamed (name = /search key; a workspace must keep exactly ONE named graph), and per
graph: nodes added / removed / changed (type, name, outputs, ref), edges added / removed / changed (conditions,
match, fallback, order). Catalog: keys added / removed / changed (label, description, fieldType, options,
defaultValue, legalBasis). Use it for the update-mode stop point and in the final report.
Exit code 1 if the after-state has zero or several named graphs.
"""
import json
import sys


def graphs(d):
    return {g["id"]: g for g in d.get("graphs", [])}


def edge_sig(e):
    conds = tuple((c["key"], c["operator"], str(c["value"])) for c in e.get("conditions") or [])
    return (bool(e.get("fallback")), e.get("match") or "all", conds, e.get("name"))


def node_sig(n):
    outs = tuple((o["key"], o.get("value"), json.dumps(o.get("translations"), sort_keys=True), bool(o.get("cumulative")))
                 for o in n.get("outputs") or [])
    return (n.get("type"), n.get("name"), n.get("ref"), outs)


def diff_graph(a, b, verbose):
    out = []
    na, nb = {n["key"]: n for n in a["nodes"]}, {n["key"]: n for n in b["nodes"]}
    for k in nb.keys() - na.keys():
        out.append(f"  + node {k} ({nb[k].get('type')}) {nb[k].get('name') or '→' + str(nb[k].get('ref'))}")
    for k in na.keys() - nb.keys():
        out.append(f"  - node {k} ({na[k].get('type')}) {na[k].get('name') or '→' + str(na[k].get('ref'))}")
    for k in na.keys() & nb.keys():
        if node_sig(na[k]) != node_sig(nb[k]):
            out.append(f"  ~ node {k} {nb[k].get('name') or ''}")
    ea = {(e["from"], e["to"]): (i, e) for i, e in enumerate(a["edges"])}
    eb = {(e["from"], e["to"]): (i, e) for i, e in enumerate(b["edges"])}
    for c in eb.keys() - ea.keys():
        out.append(f"  + edge {c[0]} -> {c[1]} {eb[c][1].get('name') or ''}")
    for c in ea.keys() - eb.keys():
        out.append(f"  - edge {c[0]} -> {c[1]} {ea[c][1].get('name') or ''}")
    for c in ea.keys() & eb.keys():
        if edge_sig(ea[c][1]) != edge_sig(eb[c][1]):
            out.append(f"  ~ edge {c[0]} -> {c[1]} (conditions/match/fallback/name)")
            if verbose:
                out.append(f"      before {edge_sig(ea[c][1])}\n      after  {edge_sig(eb[c][1])}")
    if a.get("start") != b.get("start"):
        out.append(f"  ~ start {a.get('start')} -> {b.get('start')}")
    return out


def diff_catalog(a, b):
    out = []
    for typ in ("inputs", "outputs"):
        ka = {k["key"]: k for k in (a.get("catalog") or {}).get(typ, [])}
        kb = {k["key"]: k for k in (b.get("catalog") or {}).get(typ, [])}
        for k in sorted(kb.keys() - ka.keys()):
            out.append(f"+ {typ[:-1]} {k} — {kb[k].get('label')}")
        for k in sorted(ka.keys() - kb.keys()):
            out.append(f"- {typ[:-1]} {k} — {ka[k].get('label')}")
        for k in sorted(ka.keys() & kb.keys()):
            fields = [f for f in ("label", "description", "fieldType", "defaultValue", "legalBasis", "options")
                      if json.dumps(ka[k].get(f), sort_keys=True) != json.dumps(kb[k].get(f), sort_keys=True)]
            if fields:
                out.append(f"~ {typ[:-1]} {k}: {', '.join(fields)}")
    return out


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    a, b = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
    verbose = "-v" in sys.argv
    ga, gb = graphs(a), graphs(b)
    for gid in sorted(gb.keys() - ga.keys()):
        print(f"+ graph {gid} name={gb[gid].get('name')}")
    for gid in sorted(ga.keys() - gb.keys()):
        print(f"- graph {gid} name={ga[gid].get('name')}")
    for gid in sorted(ga.keys() & gb.keys()):
        lines = diff_graph(ga[gid], gb[gid], verbose)
        if ga[gid].get("name") != gb[gid].get("name"):
            lines.insert(0, f"  ~ name {ga[gid].get('name')} -> {gb[gid].get('name')}")
        if lines:
            print(f"~ graph {gid}")
            print("\n".join(lines))
    print("\n".join(diff_catalog(a, b)))
    named = [g["id"] for g in b.get("graphs", []) if g.get("name")]
    print(f"named graphs after: {named}")
    return 0 if len(named) == 1 else 1


if __name__ == "__main__":
    sys.exit(main())
