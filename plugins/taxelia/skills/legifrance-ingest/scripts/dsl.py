"""Tiny DSL to write Taxelia import files from Python generators.

    import sys; sys.path.insert(0, "<skill>/scripts")
    from dsl import G, t, lb, info, inv, L, dump, set_code

    set_code("CIBS")                                   # prefix of legal_basis values ("CIBS L. 213-151")
    g = G("taux_niveau", "Conversion du niveau de taux", "Convertit rate_level en tax_rate (L. 213-151).", "tn_start")
    g.q("tn_start", "Niveau de taux ?")
    g.r("tn_normal", "Taux normal", t("tax_rate", "20"), lb("L. 213-151"))
    g.e("tn_start", "tn_normal", ("rate_level", "eq", "normal"), name="Normal")
    g.fb("tn_start", "tn_other", name="Sinon")        # the fallback
    dump("graphs/taux_niveau.json", g)                 # checks the structure, then writes

Rules enforced by `dump` (import would refuse them, or they are defects):
- one edge per (source, target) couple, fallback included (OR → match="any", or a follow-up node with g.cont);
- a question has outgoing edges, a result/reference has none, every node but the start is reached;
- edges point to declared nodes.
Temporary name: every graph gets name = "t__<id>" (testable through /search); pass name=... for the primary.
"""
import json

_CODE = {"prefix": ""}


def set_code(prefix):
    """Prefix put before every legal_basis article ("CIBS", "CGI", "LPF"…)."""
    _CODE["prefix"] = prefix.strip() + " " if prefix else ""


class G:
    def __init__(self, gid, title, description, start, name=None):
        self.g = {"id": gid, "name": name or "t__" + gid, "title": title, "description": description,
                  "start": start, "nodes": [], "edges": []}
        self.keys = set()

    def _node(self, key, typ, name=None, outputs=None, ref=None):
        assert key not in self.keys, "duplicate node key: " + key
        self.keys.add(key)
        n = {"key": key, "type": typ}
        if name:
            n["name"] = name
        if outputs:
            n["outputs"] = outputs
        if ref:
            n["ref"] = ref
        self.g["nodes"].append(n)
        return key

    def q(self, key, name, *outs):
        """Question node (may carry outputs, emitted when the path passes; readable by its own edges)."""
        return self._node(key, "question", name, flat(outs) or None)

    def r(self, key, name, *outs):
        """Result node (leaf)."""
        return self._node(key, "result", name, flat(outs))

    def ref(self, key, target):
        """Reference node: tail call into graph `target` (no name, no outgoing edge)."""
        return self._node(key, "reference", None, None, target)

    def e(self, frm, to, *conds, name=None, match="all"):
        """Conditional edge; conds = (key, operator, value) tuples. Order of calls = priority."""
        assert conds, "an edge without condition must be a fallback: use g.fb"
        ed = {"from": frm, "to": to, "match": match,
              "conditions": [{"key": k, "operator": op, "value": v} for (k, op, v) in conds]}
        if name:
            ed["name"] = name
        self.g["edges"].append(ed)

    def fb(self, frm, to, name=None):
        """Fallback edge (taken when no other edge of `frm` matches)."""
        ed = {"from": frm, "to": to, "fallback": True, "conditions": []}
        if name:
            ed["name"] = name
        self.g["edges"].append(ed)

    def cont(self, frm, key, name, *outs, fb_name="Non"):
        """Follow-up question `key`, reached by the fallback of `frm`, that carries the NEXT edges of `frm` in the
        same priority order — the way to keep one edge per couple when two rules of `frm` lead to the same target."""
        self.q(key, name, *outs)
        self.fb(frm, key, name=fb_name)
        return key

    def check(self):
        seen = {}
        for e in self.g["edges"]:
            c = (e["from"], e["to"])
            assert c not in seen, (f"{self.g['id']}: two edges on {c[0]} -> {c[1]} ({seen[c]!r} and {e.get('name')!r}): "
                                   f"merge them (match='any') or use a follow-up node (g.cont)")
            seen[c] = e.get("name")
        froms = {e["from"] for e in self.g["edges"]}
        tos = {e["to"] for e in self.g["edges"]}
        fallbacks = [e["from"] for e in self.g["edges"] if e.get("fallback")]
        assert len(fallbacks) == len(set(fallbacks)), f"{self.g['id']}: several fallbacks on one node"
        for n in self.g["nodes"]:
            k = n["key"]
            if n["type"] == "question":
                assert k in froms, "question without edge: " + k
            else:
                assert k not in froms, "leaf/reference with an edge: " + k
            if k != self.g["start"]:
                assert k in tos, "unreachable node: " + k
        for e in self.g["edges"]:
            assert e["from"] in self.keys and e["to"] in self.keys, e


def flat(outs):
    res = []
    for o in outs:
        res.extend(o if isinstance(o, list) else [o])
    return res


def t(key, value, cum=False):
    """Text output; value may be "$other_key" (input, path output, or an EARLIER output of the same node)."""
    o = {"key": key, "type": "text", "value": value}
    if cum:
        o["cumulative"] = True
    return o


def lb(*arts):
    """legal_basis outputs (cumulative), e.g. lb("L. 213-151", "L. 213-152")."""
    return [t("legal_basis", _CODE["prefix"] + a, True) for a in arts]


def info(v):
    return t("info", v, True)


def inv(v):
    return t("invoice_mention", v, True)


def L(*vals):
    """List value for in/nin: L("FR", "MC") -> "[FR,MC]"."""
    return "[" + ",".join(vals) + "]"


def dump(path, *graphs):
    for g in graphs:
        g.check()
    with open(path, "w") as f:
        json.dump({"graphs": [g.g for g in graphs]}, f, ensure_ascii=False, indent=1)
    for g in graphs:
        print(g.g["id"], "nodes", len(g.g["nodes"]), "edges", len(g.g["edges"]))
