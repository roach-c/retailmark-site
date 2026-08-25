# RetailMark — marketing site

Static site for RetailMark, a Walmart-focused supplier consultancy in
Bentonville. No build step: plain HTML, CSS and JS, deployed straight to
GitHub Pages.

```
python3 server.py     # local dev on :8000, adds clean URLs + the /admin inbox
```

## Pages

| Path            | What it is                                    |
|-----------------|-----------------------------------------------|
| `index.html`    | The one-page pitch, with the 3D shelf hero    |
| `glossary.html` | Retail vocabulary reference. An SEO asset     |

## The brand wall is generated, not hand-edited

The logo marquee on the homepage lives between `<!-- brands:start -->` and
`<!-- brands:end -->` in `index.html`, and is **written by the RetailMark CRM**:

```
cd ../retailmark-crm && ./venv/bin/flask publish-brands
```

A brand appears there when its CRM supplier record is Active, has a logo, and
has "Show on the public website" ticked. Editing that block by hand works right
up until the next publish overwrites it.

## Going live on retailmark.com

This deployment is **staging**. Two things must be removed on launch day, and
nothing else changes:

1. the `<meta name="robots" content="noindex, nofollow">` in `index.html` and
   `glossary.html`
2. `robots.txt`

Every path in the site is relative and no absolute URL appears anywhere, so
the cutover is a DNS change, not a rebuild. `retailmark.com` is already
RetailMark's own domain — it runs their Microsoft 365 email through Bluehost
DNS. Pointing the site and the CRM at it means **adding** records, never
editing the existing MX or SPF ones, so email is untouched.

## Deploy

Pushing to `main` publishes to GitHub Pages. `server.py` is for local
development only and is not used in production.

## Bump the asset version when you change CSS or JS

`styles.css`, `script.js` and `hero3d.js` are linked with a `?v=` token in both
HTML files. GitHub Pages serves them with `cache-control: max-age=600` and
browsers hold them a good deal longer, so without the token a style change can
sit invisible behind a stale file in someone's browser — during a demo, on the
one machine you cannot hard-refresh.

Change the token whenever those files change. Any new value works; the date
plus a letter is just a readable convention.
