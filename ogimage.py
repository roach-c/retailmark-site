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

It is built from the hero's own photograph and the hero's own scrim, not from
an approximation of them, which is what keeps the two in step: change the first
frame in hero_photos.py and rerun this, and the card follows.

The scrim is the flat vertical one, which is what the stylesheet uses under
900px — and 1200x630 is a narrow crop of a hero, so that is the correct one of
the two. The left-weighted gradient the wide hero uses is for type set against
the left edge; this lockup is centred, and leaning the grey left would put the
wordmark half on the dark side and half on the picture. It is lightened a
little against the page's, for the reason at SCRIM_STOPS.

Sizes are the standard ones: 1200x630 is what Facebook, LinkedIn, Slack,
iMessage and X all crop to, and anything smaller gets rendered as a small
thumbnail beside the title instead of a full-width card.

The tagline is set in Avenir Next, not Manrope. Manrope is loaded from Google
Fonts at run time and is not on disk, and Avenir Next is the closest geometric
sans macOS ships. If the real font ever lands in assets/, point FONT at it.
"""

import os
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1200, 630

BLACK = (17, 17, 17)
GOLD = (255, 186, 0)
# --gold at the 55% the hero badge's hairline uses
GOLD_RULE = (232, 185, 35)
# --on-dark-muted
MUTED = (201, 201, 204)
# The scrim's colour and stops. The colour and the shape are the stylesheet's
# max-width:900px .hero::after; the alphas are that wash lightened by about
# eight points, because the two are read at different sizes. On the page the
# photograph is 1400px of hero and shows through a 0.92 wash perfectly well.
# In a message the card is about 350px wide, and at that size the same wash
# flattens it to a grey rectangle with a logo on it — the store stops being
# legible as a store, which is the one thing the picture is there to say.
SCRIM = (24, 24, 27)
SCRIM_STOPS = ((0.0, 0.84), (0.6, 0.80), (1.0, 0.88))

# The frame the hero opens on. Named rather than globbed so the card cannot
# quietly change because a file was added to assets/hero/.
PHOTO = "store-aisle.webp"

# The filename carries a version, and that is deliberate. Link-preview
# scrapers — Apple's especially — cache an image by its URL and hold it for a
# long time, so republishing a different picture at the same path is how you
# get a card that is right on disk and wrong in everyone's messages. Bump this
# whenever the card's design changes; leave it alone when only the code moves.
OUT_NAME = "og-card-v2.png"

FONT = "/System/Library/Fonts/Supplemental/Avenir Next.ttc"
DEMI, MEDIUM = 2, 5           # face indices inside the .ttc

BADGE_TEXT = "OMNICHANNEL SUPPLIER SOLUTIONS"
FOOT_TEXT = "BENTONVILLE, ARKANSAS"


def scrim(size):
    """The flat vertical wash, as an alpha ramp between the stylesheet's stops."""
    w, h = size
    a = Image.new("L", (1, h))
    px = a.load()
    for y in range(h):
        t = y / (h - 1)
        for i in range(len(SCRIM_STOPS) - 1):
            (t0, a0), (t1, a1) = SCRIM_STOPS[i], SCRIM_STOPS[i + 1]
            if t0 <= t <= t1:
                k = (t - t0) / (t1 - t0)
                px[0, y] = round(255 * (a0 + (a1 - a0) * k))
                break
    layer = Image.new("RGBA", size, SCRIM + (255,))
    layer.putalpha(a.resize(size))
    return layer


def build():
    # the photograph, cropped to the card and greyscaled exactly as the CSS
    # does it: grayscale(1) contrast(1.06) brightness(1.02)
    photo = Image.open(os.path.join(HERE, "assets", "hero", PHOTO)).convert("RGB")
    card = ImageOps.fit(photo, (W, H), Image.LANCZOS, centering=(0.5, 0.5))
    card = card.convert("L").convert("RGB")
    card = ImageEnhance.Contrast(card).enhance(1.06)
    card = ImageEnhance.Brightness(card).enhance(1.02)
    card = card.convert("RGBA")

    card.alpha_composite(scrim((W, H)))

    # the wordmark, white variant, because this ground is a dark scrim now
    mark = Image.open(os.path.join(HERE, "assets", "retailmark-wordmark.png")).convert("RGBA")
    target_w = 620
    mark = mark.resize((target_w, round(mark.height * target_w / mark.width)), Image.LANCZOS)
    mx = (W - target_w) // 2
    my = 186

    # .hero-logo's drop-shadow(0 4px 14px rgba(17,17,17,.55)) — drawn from the
    # mark's own alpha, so it follows the letterforms rather than boxing them
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ink = Image.new("RGBA", mark.size, BLACK + (140,))
    shadow.paste(ink, (mx, my + 4), mark)
    card.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(9)))
    card.alpha_composite(mark, (mx, my))

    over = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(over)

    # the hero's badge, at the wordmark's width, exactly as on the page: the
    # near-black lozenge plus the gold hairline that gives it an edge back on a
    # ground it would otherwise disappear into
    badge_font = ImageFont.truetype(FONT, 27, index=DEMI)
    tb = d.textbbox((0, 0), BADGE_TEXT, font=badge_font)
    pill_h = 62
    pill_y = my + mark.height + 34
    d.rounded_rectangle((mx, pill_y, mx + target_w, pill_y + pill_h),
                        radius=pill_h // 2, fill=BLACK + (184,),
                        outline=GOLD_RULE + (140,), width=2)
    d.text((mx + (target_w - (tb[2] - tb[0])) / 2 - tb[0],
            pill_y + (pill_h - (tb[3] - tb[1])) / 2 - tb[1]),
           BADGE_TEXT, font=badge_font, fill=GOLD)

    # a quiet line at the bottom, so the card says where this is from
    foot_font = ImageFont.truetype(FONT, 21, index=MEDIUM)
    fb = d.textbbox((0, 0), FOOT_TEXT, font=foot_font)
    d.text(((W - (fb[2] - fb[0])) / 2 - fb[0], H - 74), FOOT_TEXT,
           font=foot_font, fill=MUTED + (215,))

    card.alpha_composite(over)
    card = card.convert("RGB")

    out = os.path.join(HERE, "assets", OUT_NAME)
    card.save(out, optimize=True)
    kb = os.path.getsize(out) / 1024
    print(f"  assets/{OUT_NAME}  {W}x{H}  {kb:.0f} KB")
    if kb > 1024:
        print("  WARNING: over 1MB. Some clients skip large cards.")


if __name__ == "__main__":
    build()
