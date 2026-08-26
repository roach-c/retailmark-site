#!/usr/bin/env python3
"""
sitemap.py — write sitemap.xml from the pages that exist on disk.

    python3 sitemap.py            use today's date for lastmod
    python3 sitemap.py 2026-08-26 pin the date

A sitemap is not what makes a page rank, but it is how a crawler is told the
page exists at all without having to find a link to it first. The live
mcrayroofing.com has none: /sitemap.xml and /sitemap_index.xml both 301 away.

The URLs are absolute against the launch domain, which is the one thing in
here that is not true yet. The site is noindex until the DNS moves, so nothing
reads this in the meantime.
"""

import glob
import os
import sys
from datetime import date

ORIGIN = "https://retailmark.com"

# priority is a hint, and only relative values within one site mean anything
PRIORITY = {
    "index.html":     ("1.0", "weekly"),
    "services.html":  ("0.9", "monthly"),
    "blog.html":      ("0.8", "weekly"),
    "contact.html":   ("0.8", "monthly"),
    "partners.html":  ("0.7", "monthly"),
    "glossary.html":  ("0.7", "monthly"),
}

here = os.path.dirname(os.path.abspath(__file__))
stamp = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()

rows = ""

# Posts are generated, so they are listed by what is on disk rather than by a
# table anyone has to remember to update.
for path in sorted(glob.glob(os.path.join(here, "blog", "*.html"))):
    name = os.path.basename(path)
    rows += (f"  <url>\n    <loc>{ORIGIN}/blog/{name}</loc>\n"
             f"    <lastmod>{stamp}</lastmod>\n"
             f"    <changefreq>yearly</changefreq>\n"
             f"    <priority>0.6</priority>\n  </url>\n")

for path in sorted(glob.glob(os.path.join(here, "*.html")),
                   key=lambda p: -float(PRIORITY.get(os.path.basename(p), ("0",))[0])):
    name = os.path.basename(path)
    if name not in PRIORITY:
        print(f"  skipped {name} (not in PRIORITY — add it if it should be indexed)")
        continue
    loc = f"{ORIGIN}/" if name == "index.html" else f"{ORIGIN}/{name}"
    pri, freq = PRIORITY[name]
    rows += (f"  <url>\n    <loc>{loc}</loc>\n"
             f"    <lastmod>{stamp}</lastmod>\n"
             f"    <changefreq>{freq}</changefreq>\n"
             f"    <priority>{pri}</priority>\n  </url>\n")

out = ('<?xml version="1.0" encoding="UTF-8"?>\n'
       '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
       f'{rows}</urlset>\n')
with open(os.path.join(here, "sitemap.xml"), "w") as fh:
    fh.write(out)
print(f"  sitemap.xml: {rows.count('<url>')} urls, lastmod {stamp}")
