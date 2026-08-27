# The blog, built and then withdrawn

Justin does not want to publish weekly, so the Blog tab came off the site on
2026-08-27 and the generated pages were deleted.

Everything needed to bring it back is here: `blog.py`, and `posts/` with the
one drafted article. Nothing else was thrown away.

**It lives in this folder rather than the site root on purpose.** The usual
rebuild is `python3 blog.py && python3 chrome.py && python3 sitemap.py`, and
leaving blog.py where it was would have quietly regenerated blog.html and the
post on the next rebuild — a blog would have reappeared on the site without
anyone deciding it should.

To restore it: move `blog.py` and `posts/` back to the site root, put
`("Blog", "blog.html", "#top")` back into `NAV` in `chrome.py`, and add
`"blog.html": ("0.8", "weekly")` to `PRIORITY` in `sitemap.py`.

**A one-post blog is worse than no blog.** If it ever comes back it needs
someone committed to posting, because a page whose most recent entry is months
old says something about the business that no design fixes.
