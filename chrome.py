#!/usr/bin/env python3
"""
chrome.py — one definition of the header and footer, written into every page.

The site has no build step, which is deliberate: what is on disk is what is
served. The cost of that is six copies of the nav, and six copies of a nav is
a nav that is wrong on two of them within a month. So the nav lives here once
and this script writes it out.

    python3 chrome.py            rewrite every page
    python3 chrome.py --check    say what would change, write nothing

It replaces only what is between <header class="site-header"> ... </header> and
<footer class="site-footer"> ... </footer>. Everything else in the file is
untouched, so page content is still edited in the page.
"""

import re
import sys
import glob
import os

# label, href, and the anchor that href becomes when you are already on the
# page it points at (None means it is simply a link to itself)
NAV = [
    ("Home",     "index.html",     "#top"),
    ("Services", "services.html",  "#top"),
    ("Why Us",   "why-us.html",    "#top"),
    ("Partners", "partners.html",  "#top"),
    ("Glossary", "glossary.html",  "#top"),
    ("Contact",  "contact.html",   "#top"),
]

# The call to action goes to the contact page, except on the contact page
# itself, where it scrolls to the form rather than reloading the same page.
CTA = ("Book a Strategy Call", "contact.html", "#form")

HEADER = """<header class="site-header">
  <div class="container header-inner">
    <a href="{home}" class="logo" aria-label="RetailMark home">
      <img src="assets/retailmark-wordmark.png" alt="RetailMark" class="logo-img">
    </a>
    <span class="lockup-tagline">Connecting Brands to Retail</span>
    <nav class="main-nav">
{links}
    </nav>
    <a href="{cta_href}" class="btn btn-primary btn-nav">{cta_label}</a>
    <button class="nav-toggle" id="navToggle" aria-label="Toggle menu">
      <span></span><span></span><span></span>
    </button>
  </div>
</header>"""

FOOTER = """<footer class="site-footer">
  <div class="container footer-inner">
    <span class="footer-tagline">From Opportunity to On Shelf.</span>
    <nav class="footer-nav" aria-label="Footer">
{links}
    </nav>
    <span>&copy; <span id="year"></span> RetailMark. All rights reserved.</span>
    <span class="footer-badge">
      <img src="assets/bentonville-arkansas.png" alt="Bentonville, Arkansas">
    </span>
  </div>
</footer>"""


def header_for(page):
    links = ""
    for label, href, self_href in NAV:
        if href == page:
            links += (f'      <a href="{self_href}" class="current" '
                      f'aria-current="page">{label}</a>\n')
        else:
            links += f'      <a href="{href}">{label}</a>\n'
    cta_label, cta_href, cta_self = CTA
    return HEADER.format(home="#top" if page == "index.html" else "index.html",
                         links=links.rstrip("\n"),
                         cta_href=cta_self if page == cta_href else cta_href,
                         cta_label=cta_label)


def footer_for(page):
    links = ""
    for label, href, self_href in NAV:
        if label == "Home":
            continue                      # the wordmark above already is home
        target = self_href if href == page else href
        links += f'      <a href="{target}">{label}</a>\n'
    return FOOTER.format(links=links.rstrip("\n"))


def rewrite(path, check=False):
    page = os.path.basename(path)
    src = open(path).read()
    out = src
    for pattern, replacement in (
        (r'<header class="site-header">.*?</header>', header_for(page)),
        (r'<footer class="site-footer">.*?</footer>', footer_for(page)),
    ):
        if not re.search(pattern, out, re.S):
            return f"{page}: no {pattern.split()[0][1:]} block, skipped"
        out = re.sub(pattern, lambda _m: replacement, out, count=1, flags=re.S)
    if out == src:
        return f"{page}: already current"
    if not check:
        open(path, "w").write(out)
    return f"{page}: {'would update' if check else 'updated'}"


if __name__ == "__main__":
    check = "--check" in sys.argv
    here = os.path.dirname(os.path.abspath(__file__))
    for path in sorted(glob.glob(os.path.join(here, "*.html"))):
        print(" ", rewrite(path, check))
