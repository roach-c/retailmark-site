#!/usr/bin/env python3
"""
blog.py — turn posts/*.md into blog.html and blog/<slug>.html.

    python3 blog.py          build
    python3 blog.py --check  say what would change, write nothing

Writing a post:

    posts/2026-09-02-what-a-line-review-decides.md

    ---
    title: What a line review actually decides
    date: 2026-09-02
    description: One sentence for Google and for the card on the index.
    ---

    Body in markdown. Blank line between paragraphs. ## for subheads,
    - for bullets, **bold**, [text](https://url).

The filename's date prefix is optional — `date:` in the front matter is what
counts. The slug is the filename with the date prefix and .md stripped, so
renaming a file changes its URL; don't rename one that has been shared.

Then: python3 blog.py && python3 chrome.py && python3 sitemap.py

There is deliberately no third-party markdown library. The site has no build
step and no package.json, and a dependency for the six constructs a business
blog actually uses would be the first one — after which "no build step" stops
being true.
"""

import glob
import html
import os
import re
import sys

# one definition, in chrome.py — see the note there about launch day
from chrome import ORIGIN
HERE = os.path.dirname(os.path.abspath(__file__))
ASSET_V = "20260828i"        # keep in step with the ?v= on the other pages


# --------------------------------------------------------------------------
# the markdown subset
# --------------------------------------------------------------------------
def inline(t):
    """Escape first, then add markup. The other order lets a post inject tags."""
    t = html.escape(t, quote=False)
    t = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', r'<a href="\2">\1</a>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', t)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    return t


def render(md):
    out, lines, i = [], md.split("\n"), 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            i += 1
        elif line.startswith("## "):
            out.append(f"<h2>{inline(line[3:].strip())}</h2>"); i += 1
        elif line.startswith("### "):
            out.append(f"<h3>{inline(line[4:].strip())}</h3>"); i += 1
        elif line.startswith("> "):
            block = []
            while i < len(lines) and lines[i].startswith("> "):
                block.append(inline(lines[i][2:].strip())); i += 1
            out.append("<blockquote><p>" + " ".join(block) + "</p></blockquote>")
        elif re.match(r'^[-*] ', line):
            items = []
            while i < len(lines) and re.match(r'^[-*] ', lines[i].rstrip()):
                items.append(f"  <li>{inline(lines[i].rstrip()[2:])}</li>"); i += 1
            out.append("<ul>\n" + "\n".join(items) + "\n</ul>")
        elif re.match(r'^\d+\. ', line):
            items = []
            while i < len(lines) and re.match(r'^\d+\. ', lines[i].rstrip()):
                items.append(f"  <li>{inline(re.sub(r'^\\d+\\. ', '', lines[i].rstrip()))}</li>"); i += 1
            out.append("<ol>\n" + "\n".join(items) + "\n</ol>")
        else:
            para = []
            while i < len(lines) and lines[i].strip() and not re.match(r'^(#{2,3} |[-*] |\d+\. |> )', lines[i]):
                para.append(inline(lines[i].strip())); i += 1
            out.append("<p>" + " ".join(para) + "</p>")
    return "\n      ".join(out)


def parse(path):
    raw = open(path).read()
    m = re.match(r'^---\n(.*?)\n---\n(.*)$', raw, re.S)
    if not m:
        raise SystemExit(f"{os.path.basename(path)}: no --- front matter block")
    meta = {}
    for line in m.group(1).split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    for need in ("title", "date", "description"):
        if need not in meta:
            raise SystemExit(f"{os.path.basename(path)}: front matter needs '{need}:'")
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', meta["date"]):
        raise SystemExit(f"{os.path.basename(path)}: date must be YYYY-MM-DD")
    name = os.path.basename(path)[:-3]
    meta["slug"] = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', name)
    meta["body"] = m.group(2)
    words = len(re.sub(r'[^\w\s]', '', m.group(2)).split())
    meta["minutes"] = max(1, round(words / 220))
    return meta


def pretty(d):
    y, mo, dy = d.split("-")
    months = ["January", "February", "March", "April", "May", "June", "July",
              "August", "September", "October", "November", "December"]
    return f"{months[int(mo) - 1]} {int(dy)}, {y}"


# --------------------------------------------------------------------------
# the pages
# --------------------------------------------------------------------------
def head(title, desc, canonical, extra=""):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<!-- STAGING ONLY. Delete this tag and robots.txt on the day it goes live. -->
<meta name="robots" content="noindex, nofollow">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc, quote=True)}">
<link rel="canonical" href="{canonical}">

  <!-- meta:start -->
  <!-- meta:end -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{extra}styles.css?v={ASSET_V}">
<script>
if (!matchMedia('(prefers-reduced-motion: reduce)').matches)
  document.documentElement.classList.add('js-reveal');
</script>
</head>

<body>

<header class="site-header">
</header>
"""


def post_page(p):
    schema = {
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": p["title"], "datePublished": p["date"],
        "dateModified": p["date"], "description": p["description"],
        "url": f"{ORIGIN}/blog/{p['slug']}.html",
        "mainEntityOfPage": {"@type": "WebPage", "@id": f"{ORIGIN}/blog/{p['slug']}.html"},
        "author": {"@type": "Organization", "name": "RetailMark", "url": f"{ORIGIN}/"},
        "publisher": {"@id": f"{ORIGIN}/#organization"},
        "isAccessibleForFree": True,
    }
    import json
    return head(f"{p['title']} | RetailMark", p["description"],
                f"{ORIGIN}/blog/{p['slug']}.html", extra="../") + f"""
<main id="top">
  <article class="post" data-tone="light">
    <div class="container">
      <div class="crumbs"><a href="../index.html">Home</a> <span>/</span>
        <a href="../blog.html">Blog</a> <span>/</span> {html.escape(p['title'])}</div>
      <h1>{html.escape(p['title'])}</h1>
      <p class="post-meta">
        <time datetime="{p['date']}">{pretty(p['date'])}</time>
        <span>&middot;</span> {p['minutes']} min read
      </p>
      <div class="post-body">
      {render(p['body'])}
      </div>
      <p class="post-back"><a href="../blog.html">&larr; All posts</a></p>
    </div>
  </article>
</main>

<section class="glossary-cta" data-tone="dark">
  <div class="container">
    <h2>Getting a product onto a shelf?</h2>
    <p>The first conversation is free, and it is usually the useful one.</p>
    <a href="../contact.html" class="btn btn-primary btn-lg">Book Your Free Strategy Call</a>
  </div>
</section>

<footer class="site-footer">
</footer>

<script type="application/ld+json">
{json.dumps(schema, indent=2)}
</script>
<script src="../script.js?v={ASSET_V}"></script>
</body>
</html>
"""


def index_page(posts):
    if posts:
        cards = ""
        for p in posts:
            cards += f"""      <article class="post-card">
        <time datetime="{p['date']}">{pretty(p['date'])}</time>
        <h2><a href="blog/{p['slug']}.html">{html.escape(p['title'])}</a></h2>
        <p>{html.escape(p['description'])}</p>
        <span class="post-card-more">Read it &rarr;</span>
      </article>

"""
        body = f'    <div class="post-list">\n{cards}    </div>'
    else:
        body = ('    <p class="post-empty">Nothing published yet. Drop a markdown file in '
                '<code>posts/</code> and run <code>python3 blog.py</code>.</p>')

    return head("Blog | RetailMark",
                "Notes on getting a product onto a retail shelf: line reviews, "
                "forecasting, item setup and the calendar the whole category runs on.",
                f"{ORIGIN}/blog.html") + f"""
<main id="top">

  <section class="page-hero" data-tone="light">
    <div class="container">
      <div class="crumbs"><a href="index.html">Home</a> <span>/</span> Blog</div>
      <h1>Notes from the buyer's side</h1>
      <p class="page-hero-sub">What we learn getting products onto shelves, written for
        the people trying to do it. No fluff, and nothing we would not say on a call.</p>
    </div>
  </section>

  <section class="blog-index" data-tone="light">
    <div class="container">
{body}
    </div>
  </section>

</main>

<footer class="site-footer">
</footer>

<script src="script.js?v={ASSET_V}"></script>
</body>
</html>
"""


if __name__ == "__main__":
    check = "--check" in sys.argv
    files = sorted(glob.glob(os.path.join(HERE, "posts", "*.md")))
    posts = sorted((parse(f) for f in files), key=lambda p: p["date"], reverse=True)

    slugs = [p["slug"] for p in posts]
    dupes = {s for s in slugs if slugs.count(s) > 1}
    if dupes:
        raise SystemExit(f"two posts share a slug, so one would overwrite the "
                         f"other: {', '.join(sorted(dupes))}")

    os.makedirs(os.path.join(HERE, "blog"), exist_ok=True)
    wrote = []
    for p in posts:
        path = os.path.join(HERE, "blog", f"{p['slug']}.html")
        if not check:
            open(path, "w").write(post_page(p))
        wrote.append(f"blog/{p['slug']}.html")
    if not check:
        open(os.path.join(HERE, "blog.html"), "w").write(index_page(posts))

    # a post file that was deleted or renamed leaves its page behind, and a
    # stale page is worse than a missing one: it stays linked from the sitemap
    keep = {f"{p['slug']}.html" for p in posts}
    for old in glob.glob(os.path.join(HERE, "blog", "*.html")):
        if os.path.basename(old) not in keep:
            print(f"  removing orphan {os.path.basename(old)}")
            if not check:
                os.remove(old)

    print(f"  {'would write' if check else 'wrote'} blog.html + {len(posts)} post page(s)")
    for w in wrote:
        print(f"    {w}")
    print("  now run: python3 chrome.py && python3 sitemap.py")
