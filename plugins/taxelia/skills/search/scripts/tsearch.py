#!/usr/bin/env python3
"""Taxelia /search client for the `search` skill. Every answer comes from the API, nothing else.

Configuration: ~/.config/taxelia/search.json  {"api": "https://taxelia.bizyness.fr"}  (optional; default API)
API key (read access is enough; needed for the catalog and workspace list, /search itself needs none):
~/.config/taxelia/apikey (chmod 600) — never printed.

  tsearch.py workspaces                          list workspaces (id, name, strict) and their main graph
  tsearch.py main <ws>                           the named graphs of a workspace (the main graph = the only one)
  tsearch.py outputs <ws>                        catalog outputs (key, label, description)
  tsearch.py keys <ws> <key> [<key> …]           catalog entries of these inputs (label, type, description, options, default)
  tsearch.py find <ws> "<words>"                 inputs whose key/label/description/options match the words
  tsearch.py run <ws> '<inputs json>' [--tree <name>] [--outputs a,b] [--language fr]
                                                 calls POST /search and prints the EXACT request and response JSON,
                                                 then the catalog entries of inputs.required (to ask the user)
Options: --api <url> overrides the configured API for one call.
"""
import json
import os
import re
import ssl
import sys
import unicodedata
import urllib.error
import urllib.request

CONF_DIR = os.path.expanduser("~/.config/taxelia")
DEFAULT_API = "https://taxelia.bizyness.fr"


def _ssl_context():
    # python.org Python on macOS ships without root certificates: fall back to certifi, then the system bundle.
    ctx = ssl.create_default_context()
    if ctx.cert_store_stats().get("x509_ca", 0):
        return ctx
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        pass
    for bundle in ("/etc/ssl/cert.pem", "/etc/ssl/certs/ca-certificates.crt"):
        if os.path.exists(bundle):
            return ssl.create_default_context(cafile=bundle)
    return ctx


SSL = _ssl_context()


def api_base(args):
    if "--api" in args:
        return args[args.index("--api") + 1].rstrip("/")
    conf = os.path.join(CONF_DIR, "search.json")
    if os.path.exists(conf):
        return json.load(open(conf)).get("api", DEFAULT_API).rstrip("/")
    return DEFAULT_API


def key():
    path = os.path.join(CONF_DIR, "apikey")
    if not os.path.exists(path):
        sys.exit(f"missing API key: ask the user for a Taxelia API key and store it in {path} (chmod 600)")
    return open(path).read().strip()


def call(base, method, path, body=None, auth=True):
    headers = {"Content-Type": "application/json"}
    if auth:
        headers["X-Api-Key"] = key()
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(base + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120, context=SSL) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except ValueError:
            return e.code, raw


def need(st, res):
    if st != 200:
        sys.exit(f"API error {st}: {json.dumps(res, ensure_ascii=False)[:500]}")
    return res


def named_graphs(base, ws):
    return [g for g in need(*call(base, "GET", f"/workspaces/{ws}/graphs")) if g.get("name")]


def main_graph(base, ws):
    # the main graph is the only named graph; with zero or several, the user must choose (--tree)
    named = named_graphs(base, ws)
    return named[0] if len(named) == 1 else None


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s)


def show_key(k):
    print(f"- {k['key']} — {k.get('label')}  [{k.get('fieldType')}]  default={k.get('defaultValue')}")
    if k.get("description"):
        print(f"    {k['description']}")
    for o in k.get("options") or []:
        print(f"    • {o['value']} — {o.get('name')}" + (f" : {o['description']}" if o.get("description") else ""))


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    base = api_base(a)
    cmd = a[0]
    if cmd == "workspaces":
        for w in need(*call(base, "GET", "/workspaces")):
            named = named_graphs(base, w["id"])
            main = f"{named[0]['name']} ({named[0].get('title')})" if len(named) == 1 else \
                f"AMBIGUOUS, {len(named)} named graphs: {[g['name'] for g in named]}"
            print(f"{w['id']:20} {w['name']:28} strict={w.get('strictInputs')}  main graph: {main}")
        return 0
    if cmd == "main":
        named = named_graphs(base, a[1])
        print(json.dumps([{"name": g["name"], "title": g.get("title"), "description": g.get("description")} for g in named],
                         ensure_ascii=False, indent=1))
        if len(named) != 1:
            print(f"{len(named)} named graphs: ask the user which one to query (--tree <name>)", file=sys.stderr)
        return 0
    if cmd == "outputs":
        for k in need(*call(base, "GET", f"/workspaces/{a[1]}/outputs")):
            print(f"- {k['key']} — {k.get('label')} : {(k.get('description') or '')[:200]}")
        return 0
    if cmd == "keys":
        wanted = [x for x in a[2:] if not x.startswith("--")]
        cat = {k["key"]: k for k in need(*call(base, "GET", f"/workspaces/{a[1]}/inputs"))}
        for w in wanted:
            show_key(cat[w]) if w in cat else print(f"- {w}: not in the catalog")
        return 0
    if cmd == "find":
        words = [w for w in norm(a[2]).split() if len(w) > 2]
        found = []
        for k in need(*call(base, "GET", f"/workspaces/{a[1]}/inputs")):
            txt = norm(" ".join(filter(None, [k["key"], k.get("label"), k.get("description")] +
                                   [f"{o['value']} {o.get('name')} {o.get('description') or ''}" for o in k.get("options") or []])))
            score = sum(1 for w in words if w in txt)
            if score:
                found.append((score, k))
        for score, k in sorted(found, key=lambda x: -x[0])[:10]:
            print(f"[{score}]", end=" ")
            show_key(k)
        return 0
    if cmd == "run":
        ws, inputs = a[1], json.loads(a[2])
        tree = a[a.index("--tree") + 1] if "--tree" in a else (main_graph(base, ws) or {}).get("name")
        if not tree:
            sys.exit(f"no single main graph in {ws}: run `main {ws}`, ask the user, then pass --tree <name>")
        body = {"workspace": ws, "tree": tree, "language": a[a.index("--language") + 1] if "--language" in a else "fr",
                "conditions": [{"key": k, "value": str(v)} for k, v in inputs.items()]}
        if "--outputs" in a:
            body["outputs"] = a[a.index("--outputs") + 1].split(",")
        st, res = call(base, "POST", "/search", body, auth=False)
        print(f"POST {base}/search")
        print("REQUEST")
        print(json.dumps(body, ensure_ascii=False, indent=2))
        print(f"RESPONSE (HTTP {st})")
        print(json.dumps(res, ensure_ascii=False, indent=2))
        required = [r["key"] for r in ((res or {}).get("inputs") or {}).get("required") or []] if st == 200 else []
        if required:
            # not part of the API response: catalog entries of the keys the engine asks for, to phrase the questions
            print("CATALOG OF REQUIRED INPUTS (GET /workspaces/{ws}/inputs)".replace("{ws}", ws))
            cat = {k["key"]: k for k in need(*call(base, "GET", f"/workspaces/{ws}/inputs"))}
            for r in required:
                show_key(cat[r]) if r in cat else print(f"- {r}: not in the catalog")
        return 0 if st == 200 else 1
    sys.exit(__doc__)


if __name__ == "__main__":
    sys.exit(main())
