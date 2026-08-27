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
# Blog is deliberately not here either. Justin does not want to publish
# weekly, so the tab came off and the generated pages were deleted; see
# _unpublished/README.md for what it takes to bring it back.
#
# Glossary is deliberately not here. Justin asked for the tab to come off — he
# wants that content as a one-pager sent to suppliers, not a nav item. The page
# itself is still published and still in the sitemap, because it is one of the
# only two pages on this site a search engine has any reason to rank; it is
# just not competing for a slot in a six-item nav any more.
NAV = [
    ("Home",     "index.html",     "#top"),
    ("Services", "services.html",  "#top"),
    ("Partners", "partners.html",  "#top"),
    ("Contact",  "contact.html",   "#top"),
]

# The call to action goes to the contact page, except on the contact page
# itself, where it scrolls to the form rather than reloading the same page.
CTA = ("Book a Strategy Call", "contact.html", "#form")

# Where the site is actually served from. Schema and social cards need absolute
# URLs and this is the one place that decides them — sitemap.py imports it
# from here rather than keeping its own copy.
#
# It has to be the host the pages are really on, not the one they are going to.
# Pointed at retailmark.com while the site lived on the preview domain, every
# card image 404'd, so iMessage fell back to scraping the page, found the
# transparent wordmark, and rendered a link as a cropped logo on grey.
#
# ON LAUNCH DAY: change this one line to https://retailmark.com, then
#   python3 chrome.py && python3 sitemap.py
LAUNCH_ORIGIN = "https://retailmark.com"
ORIGIN = "https://retailmark.tetheredcrew.com"

# The build credit in the footer. The Tethered Crew landing page, not a deep
# link into it. The utm_source says which client site sent them, which is the
# only way to tell whether these credits do anything.
CREDIT_URL = ("https://tetheredcrew.com/"
              "?utm_source=retailmark&utm_medium=footer&utm_campaign=site-credit")

# Everything here is already published on the site in plain text. Nothing is
# invented: no street address, no opening hours, and above all no reviews or
# star rating. A fabricated AggregateRating is a manual action, not a shortcut.
BUSINESS = {
    "name": "RetailMark",
    "phone": "+1-479-366-1491",
    "email": "info@retailmark.com",
    "locality": "Bentonville",
    "region": "AR",
    "country": "US",
    "description": ("A Bentonville, Arkansas sales brokerage that gets consumer "
                    "brands onto retail shelves, from line review strategy and "
                    "forecasting through item setup, replenishment and reporting."),
}

# page -> (social card title, social card description)
CARDS = {
    "index.html": ("RetailMark | From Opportunity to On Shelf",
                   "We get consumer brands onto retail shelves. Strategy, forecasting and the line review deck, built by people who sat on the buying side."),
    "services.html": ("What RetailMark Does | Services",
                      "Sales strategy, forecasting, item setup, replenishment, supply chain, reporting, e-commerce, trend management and line review decks."),
    "why-us.html": ("Why Suppliers Choose RetailMark",
                    "We sat on the buying side. What that changes about a pitch, a forecast and a line review."),
    "partners.html": ("Platforms and Brands We Work With",
                      "Retail Link, Item 360, Nielsen, IRi, Canopy and Atlas: the systems we work in daily, and the brands we represent."),
    "glossary.html": ("Retail Glossary: Mod, Line Review, OTIF | RetailMark",
                      "The vocabulary a retail buyer actually uses, defined plainly. Modular, line review, OTIF, MABD, UPSPW and more."),
    "contact.html": ("Contact RetailMark | Bentonville, Arkansas",
                     "Book a free strategy call. Phone, email and the form."),
}


def schema_for(page):
    """Organization and ProfessionalService, once, on the home page.

    Sitewide duplicates of the same @id are how a site ends up telling Google
    two different things about itself; the live mcrayroofing.com does exactly
    that and carries two LocalBusiness blocks with the same @id and different
    phone numbers.
    """
    if page != "index.html":
        return ""
    b = BUSINESS
    return f"""
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@graph": [
      {{
        "@type": "WebSite",
        "@id": "{ORIGIN}/#website",
        "url": "{ORIGIN}/",
        "name": "{b['name']}",
        "publisher": {{ "@id": "{ORIGIN}/#organization" }}
      }},
      {{
        "@type": ["Organization", "ProfessionalService"],
        "@id": "{ORIGIN}/#organization",
        "name": "{b['name']}",
        "url": "{ORIGIN}/",
        "logo": "{ORIGIN}/assets/retailmark-wordmark.png",
        "image": "{ORIGIN}/assets/retailmark-wordmark.png",
        "description": "{b['description']}",
        "telephone": "{b['phone']}",
        "email": "{b['email']}",
        "address": {{
          "@type": "PostalAddress",
          "addressLocality": "{b['locality']}",
          "addressRegion": "{b['region']}",
          "addressCountry": "{b['country']}"
        }},
        "areaServed": {{ "@type": "Country", "name": "United States" }},
        "knowsAbout": [
          "Walmart supplier strategy", "Line review preparation",
          "Retail Link", "Item 360", "Demand forecasting",
          "Replenishment planning", "Retail item setup"
        ],
        "contactPoint": {{
          "@type": "ContactPoint",
          "contactType": "sales",
          "telephone": "{b['phone']}",
          "email": "{b['email']}",
          "areaServed": "US",
          "availableLanguage": "English"
        }}
      }}
    ]
  }}
  </script>"""


def meta_for(page):
    title, desc = CARDS.get(page, (None, None))
    if not title:
        return ""
    url = f"{ORIGIN}/" if page == "index.html" else f"{ORIGIN}/{page}"
    return f"""
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="RetailMark">
  <meta property="og:locale" content="en_US">
  <meta property="og:url" content="{url}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:image" content="{ORIGIN}/assets/og-card.png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="RetailMark — omnichannel supplier solutions, Bentonville, Arkansas">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{desc}">
  <meta name="twitter:image" content="{ORIGIN}/assets/og-card.png">{schema_for(page)}"""

HEADER = """<!-- The black the glass bar sits on. Every page, not just the home page:
     the bar is translucent, so without this it takes its colour from whatever
     is beneath and nearly vanishes over a pale page hero. Its height is set
     from the header's own measured height by script.js. -->
<div class="bar-band" data-tone="dark" aria-hidden="true"></div>

<header class="site-header">
  <div class="container header-inner">
    <a href="{home}" class="logo" aria-label="RetailMark home">
      <!-- The wordmark as its four letter slices, the same ones the brand band
           animates. The home page opens with only the R and the M showing and
           expands to the full mark once you scroll past the hero; every other
           page just renders it open. See .logo-mark in styles.css. -->
      <svg class="logo-mark" viewBox="0 0 1470 294" aria-hidden="true" focusable="false">
        <image class="lm-r"     href="{up}assets/rm-r.png"     x="0"    y="0" width="172" height="294"/>
        <image class="lm-etail" href="{up}assets/rm-etail.png" x="160"  y="0" width="564" height="294"/>
        <image class="lm-m"     href="{up}assets/rm-m.png"     x="749"  y="0" width="237" height="294"/>
        <image class="lm-ark"   href="{up}assets/rm-ark.png"   x="1006" y="0" width="464" height="294"/>
      </svg>
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
  <div class="container footer-top">
    <div class="footer-brand">
      <a href="{home}" class="footer-wordmark">Retail<span>Mark</span></a>
      <p>RetailMark is a Bentonville, Arkansas sales brokerage that gets consumer
        brands onto retail shelves, from line review strategy and forecasting
        through item setup, replenishment and reporting.</p>
      <span class="footer-badge">
        <img src="{up}assets/bentonville-arkansas.png" alt="Bentonville, Arkansas">
      </span>
    </div>

    <nav class="footer-col" aria-label="Footer">
      <h2>Quick Links</h2>
{links}
    </nav>

    <div class="footer-col">
      <h2>Contact</h2>
      <ul class="footer-contact">
        <li><span>Email</span><a href="mailto:info@retailmark.com">info@retailmark.com</a></li>
        <li><span>Call us</span><a href="tel:+14793661491">+1 (479) 366-1491</a></li>
        <li><span>Location</span>Bentonville, Arkansas</li>
      </ul>
    </div>
  </div>

  <div class="container footer-bottom">
    <span class="footer-tagline">From Opportunity to On&nbsp;Shelf.</span>
    <span>&copy; <span id="year"></span> RetailMark. All rights reserved.</span>
    <span class="footer-credit">Powered by <a href="{credit}"
      target="_blank" rel="noopener">Tethered Crew</a></span>
  </div>
</footer>"""


def depth_prefix(page):
    """'' for a page in the site root, '../' for one a directory down.

    Every URL the chrome writes — the nav, the logo slices, the footer badge —
    is relative, so a page in a subdirectory needs them prefixed or they
    resolve against that directory and 404. Nothing sits in a subdirectory
    today; this exists because the blog did, and it is the one thing that would
    have to be right again the moment anything else does.
    """
    return "../" * page.count("/")


def header_for(page):
    up = depth_prefix(page)
    links = ""
    for label, href, self_href in NAV:
        current = href == page
        if current:
            links += (f'      <a href="{self_href}" class="current" '
                      f'aria-current="page">{label}</a>\n')
        else:
            links += f'      <a href="{up}{href}">{label}</a>\n'
    cta_label, cta_href, cta_self = CTA
    return HEADER.format(home="#top" if page == "index.html" else f"{up}index.html",
                         links=links.rstrip("\n"),
                         cta_href=cta_self if page == cta_href else f"{up}{cta_href}",
                         cta_label=cta_label,
                         up=up)


def footer_for(page):
    up = depth_prefix(page)
    links = ""
    for label, href, self_href in NAV:
        target = self_href if href == page else f"{up}{href}"
        links += f'      <a href="{target}">{label}</a>\n'
    return FOOTER.format(links=links.rstrip("\n"),
                         up=up,
                         # & is escaped: a bare one in an attribute is only
                         # legal when it cannot start a character reference
                         credit=CREDIT_URL.replace("&", "&amp;"),
                         home="#top" if page == "index.html" else f"{up}index.html")


def rewrite(path, check=False):
    here = os.path.dirname(os.path.abspath(__file__))
    page = os.path.relpath(os.path.abspath(path), here)
    src = open(path).read()
    out = src
    for pattern, replacement in (
        (r'<!-- meta:start -->.*?<!-- meta:end -->',
         "<!-- meta:start -->" + meta_for(page) + "\n  <!-- meta:end -->"),
        # the optional leading band is part of what gets replaced; without it
        # each run would prepend a second one and they would stack up
        # The comment AND the div, or each run leaves the old comment in place
        # and prepends a fresh one. They stacked four deep before this was
        # noticed, because --check reporting "would update" on an unchanged
        # file looks like nothing at all.
        (r'(?:<!-- The black the glass bar sits on\.[\s\S]*?-->\s*)?'
         r'(?:<div class="bar-band"[^>]*></div>\s*)?'
         r'<header class="site-header">[\s\S]*?</header>',
         header_for(page)),
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
