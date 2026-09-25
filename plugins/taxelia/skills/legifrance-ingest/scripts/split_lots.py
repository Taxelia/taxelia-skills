#!/usr/bin/env python3
"""Inspect and split an extracted Légifrance text into reading lots.

  split_lots.py source.txt --stats
      articles found (headers "Article X"), chapter/section headers, number gaps per series (often articles that
      do not exist — check against the "Articles X à Y" headers before calling them lost), tables found.
  split_lots.py source.txt --lots <dir> [--max-chars 60000]
      writes <dir>/NN-<slug>.txt, cutting at chapter headers ("Chapitre", "Titre", "Livre") and, when a chapter is
      too big, at section headers; prints the lot list with sizes and article counts.
"""
import os
import re
import sys

ART = re.compile(r"^Article\s+(L\.?\s?|R\.?\s?|D\.?\s?)?(\d+(?:-\d+)*)\s*$", re.M)
HEAD = re.compile(r"^(Livre|Titre|Chapitre|Section|Sous-section)\b.*$", re.M)


def articles(text):
    return [(m.start(), (m.group(1) or "").replace(" ", "").replace(".", "") + m.group(2)) for m in ART.finditer(text)]


def stats(text):
    arts = articles(text)
    print(f"characters: {len(text)}  articles: {len(arts)}  markdown tables: {text.count(chr(10) + '| ')}")
    ids = [a for _, a in arts]
    dup = sorted({a for a in ids if ids.count(a) > 1})
    if dup:
        print("duplicated article ids (a table of contents repeats them?):", dup[:20])
    series = {}
    for a in ids:
        m = re.match(r"(.*?)(\d+)$", a)
        if m:
            series.setdefault(m.group(1), []).append(int(m.group(2)))
    for prefix, nums in series.items():
        s = sorted(set(nums))
        gaps = [n for n in range(s[0], s[-1]) if n not in s]
        if gaps and len(s) > 3:
            print(f"series {prefix}*: {s[0]}..{s[-1]}, missing numbers: {gaps[:30]}{' …' if len(gaps) > 30 else ''}")
    print("\nheaders:")
    for m in HEAD.finditer(text):
        print("  " + m.group(0)[:120])


def split(text, out, max_chars):
    os.makedirs(out, exist_ok=True)
    cuts = [m.start() for m in HEAD.finditer(text) if m.group(1) in ("Livre", "Titre", "Chapitre")]
    first_article = articles(text)[0][0] if articles(text) else 0
    cuts = sorted({0, *[c for c in cuts if c >= first_article]})
    blocks = [text[a:b] for a, b in zip(cuts, cuts[1:] + [len(text)])]
    lots, cur = [], ""
    for b in blocks:
        if len(b) > max_chars:  # split a too big chapter at its sections
            subcuts = [0] + [m.start() for m in HEAD.finditer(b) if m.group(1) == "Section"]
            parts = [b[a:c] for a, c in zip(subcuts, subcuts[1:] + [len(b)])]
        else:
            parts = [b]
        for p in parts:
            if cur and len(cur) + len(p) > max_chars:
                lots.append(cur)
                cur = ""
            cur += p
    if cur.strip():
        lots.append(cur)
    for i, lot in enumerate(lots, 1):
        first = HEAD.search(lot)
        slug = re.sub(r"[^a-z0-9]+", "-", (first.group(0) if first else "lot").lower())[:40].strip("-")
        path = os.path.join(out, f"{i:02d}-{slug}.txt")
        open(path, "w").write(lot)
        print(f"{os.path.basename(path)}  {len(lot)} chars  {len(articles(lot))} articles")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    txt = open(a[0]).read()
    if "--stats" in a:
        stats(txt)
    if "--lots" in a:
        mc = int(a[a.index("--max-chars") + 1]) if "--max-chars" in a else 60000
        split(txt, a[a.index("--lots") + 1], mc)
