"""Shared configuration and HTTP helpers for the legifrance-ingest scripts.

The work directory holds `ingest.json` ({"api", "workspace", "primary_id", "primary_name"}) and `.apikey`.
It is found, in order: `--work <dir>` on the command line, the INGEST_WORK environment variable, the current
directory or one of its parents. The API key is read from `<work>/.apikey` and never printed.
"""
import json
import os
import ssl
import sys
import urllib.error
import urllib.request


def _ssl_context():
    # Python from python.org (macOS) ships without root certificates until "Install Certificates.command" is
    # run: HTTPS to the public API then fails with CERTIFICATE_VERIFY_FAILED. Fall back to certifi, then to
    # the system bundle.
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


_SSL = _ssl_context()


def work_dir():
    argv = sys.argv
    if "--work" in argv:
        return os.path.abspath(argv[argv.index("--work") + 1])
    if os.environ.get("INGEST_WORK"):
        return os.path.abspath(os.environ["INGEST_WORK"])
    d = os.getcwd()
    while True:
        if os.path.exists(os.path.join(d, "ingest.json")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            sys.exit("ingest.json not found: pass --work <dir>, set INGEST_WORK, or run from the work directory")
        d = parent


def config():
    w = work_dir()
    cfg = json.load(open(os.path.join(w, "ingest.json")))
    cfg["work"] = w
    return cfg


def api_key(cfg):
    path = os.path.join(cfg["work"], ".apikey")
    if not os.path.exists(path):
        sys.exit(f"missing {path} (ask the user for a write key, store it there with chmod 600)")
    return open(path).read().strip()


def call(cfg, method, path, body=None, auth=True):
    """Returns (status, parsed JSON or text)."""
    headers = {"Content-Type": "application/json"}
    if auth:
        headers["X-Api-Key"] = api_key(cfg)
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(cfg["api"].rstrip("/") + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=600, context=_SSL) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except ValueError:
            return e.code, raw[:2000]


def ws_path(cfg, suffix=""):
    return f"/workspaces/{cfg['workspace']}{suffix}"
