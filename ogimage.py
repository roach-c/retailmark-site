#!/usr/bin/env python3
"""
ogimage.py — build assets/og-card.png, the picture that shows up when someone
texts or posts a link to the site.

    python3 ogimage.py

Why it exists: the card was og:image -> the wordmark PNG, which is a
transparent, 5:1 letterbox. Every scraper crops a card to 1.91:1 and paints
whatever is behind the transparency, so a link arrived as a cropped wordmark on
whatever grey the messaging app happened to use. The card is now a real
1200x630 image that reproduces the hero lockup, so the preview looks like the
page it opens.

Sizes are the standard ones: 1200x630 is what Facebook, LinkedIn, Slack,
iMessage and X all crop to, and anything smaller gets rendered as a small
thumbnail beside the title instead of a full-width card.

The tagline is set in Avenir Next, not Manrope. Manrope is loaded from Google
Fonts at run time and is not on disk, and Avenir Next is the closest geometric
sans macOS ships. If the real font ever lands in assets/, point FONT at it.
"""

import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1200, 630

CREAM = (250, 248, 243)
BLACK = (17, 17, 17)
GOLD = (255, 186, 0)

FONT = "/System/Library/Fonts/Supplemental/Avenir Next.ttc"
DEMI, MEDIUM = 2, 5           # face indices inside the .ttc

BADGE_TEXT = "OMNICHANNEL SUPPLIER SOLUTIONS"
FOOT_TEXT = "BENTONVILLE, ARKANSAS"


def radial(size, centre, colour, strength):
    """A soft glow, built small and scaled up.

    Per-pixel over 1200x630 in pure Python is 756,000 iterations; over 120x63
    it is 7,560 and LANCZOS makes the difference invisible on a gradient.
    """
    sw, sh = size[0] // 10, size[1] // 10
    g = Image.new("L", (sw, sh), 0)
    px = g.load()
    cx, cy = centre[0] / 10, centre[1] / 10
    far = (sw ** 2 + sh ** 2) ** 0.5
    for y in range(sh):
        for x in range(sw):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 / far
            px[x, y] = max(0, int(255 * strength * (1 - d) ** 2))
    g = g.resize(size, Image.LANCZOS)
    layer = Image.new("RGB", size, colour)
    return layer, g


def rounded_pill(draw, box, fill):
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=(y1 - y0) // 2, fill=fill)


def build():
    card = Image.new("RGB", (W, H), CREAM)

    # the same warm corner the hero has
    glow, mask = radial((W, H), (W * 0.86, 0), (255, 210, 90), 0.55)
    card.paste(glow, (0, 0), mask)

    # the wordmark, dark variant, because this ground is cream
    mark = Image.open(os.path.join(HERE, "assets", "retailmark-wordmark-dark.png")).convert("RGBA")
    target_w = 620
    mark = mark.resize((target_w, round(mark.height * target_w / mark.width)), Image.LANCZOS)
    mx = (W - target_w) // 2
    my = 186
    card.paste(mark, (mx, my), mark)

    d = ImageDraw.Draw(card)

    # the hero's black pill, at the wordmark's width, exactly as on the page
    badge_font = ImageFont.truetype(FONT, 27, index=DEMI)
    tb = d.textbbox((0, 0), BADGE_TEXT, font=badge_font)
    pill_h = 62
    pill_y = my + mark.height + 34
    rounded_pill(d, (mx, pill_y, mx + target_w, pill_y + pill_h), BLACK)
    d.text((mx + (target_w - (tb[2] - tb[0])) / 2 - tb[0],
            pill_y + (pill_h - (tb[3] - tb[1])) / 2 - tb[1]),
           BADGE_TEXT, font=badge_font, fill=GOLD)

    # a quiet line at the bottom, so the card says where this is from
    foot_font = ImageFont.truetype(FONT, 21, index=MEDIUM)
    fb = d.textbbox((0, 0), FOOT_TEXT, font=foot_font)
    d.text(((W - (fb[2] - fb[0])) / 2 - fb[0], H - 74), FOOT_TEXT,
           font=foot_font, fill=(120, 118, 112))

    out = os.path.join(HERE, "assets", "og-card.png")
    card.save(out, optimize=True)
    kb = os.path.getsize(out) / 1024
    print(f"  assets/og-card.png  {W}x{H}  {kb:.0f} KB")
    if kb > 1024:
        print("  WARNING: over 1MB. Some clients skip large cards.")


if __name__ == "__main__":
    build()
