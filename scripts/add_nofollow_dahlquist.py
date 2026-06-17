#!/usr/bin/env python3
"""
Add rel="nofollow" to every <a> link pointing to dahlquist.se / dahlquist.nu
across all landing pages (pages/ + deploys/ index.html).

Why: these 47 owned doorway domains dropped ~312 *dofollow* links with branded,
navigational and CTA anchors to dahlquist.se. That self-built link network is a
manual-action / link-scheme risk. nofollow neutralises the equity-passing signal
(and makes the anchor over-optimisation moot) while keeping the sites live.

Idempotent: safe to re-run (won't double-add nofollow).
"""

import re
from pathlib import Path

ROOT = Path("/Users/niklasdahlquist/GIT/dahlquist-seo-landingpages")
DIRS = [ROOT / "pages", ROOT / "deploys"]

A_TAG = re.compile(r'<a\b[^>]*>', re.IGNORECASE)
HREF = re.compile(r'href\s*=\s*"([^"]*)"', re.IGNORECASE)
REL = re.compile(r'rel\s*=\s*"([^"]*)"', re.IGNORECASE)
DQ = re.compile(r'https?://(www\.)?dahlquist\.(se|nu)\b', re.IGNORECASE)

changed_links = 0


def fix_tag(m):
    global changed_links
    tag = m.group(0)
    href = HREF.search(tag)
    if not href or not DQ.search(href.group(1)):
        return tag  # not a dahlquist link
    rel = REL.search(tag)
    if rel:
        vals = rel.group(1).split()
        if any(v.lower() == "nofollow" for v in vals):
            return tag  # already nofollow -> idempotent
        new_rel = rel.group(1).rstrip() + " nofollow"
        changed_links += 1
        return tag[:rel.start(1)] + new_rel + tag[rel.end(1):]
    # no rel attribute -> insert one before the closing '>'
    changed_links += 1
    return tag[:-1].rstrip() + ' rel="nofollow">'


def main():
    files = 0
    for base in DIRS:
        if not base.exists():
            continue
        for f in sorted(base.rglob("index.html")):
            src = f.read_text(encoding="utf-8")
            out = A_TAG.sub(fix_tag, src)
            if out != src:
                f.write_text(out, encoding="utf-8")
                files += 1
    print(f"Files updated: {files}")
    print(f"Links nofollowed: {changed_links}")


if __name__ == "__main__":
    main()
