"""Render the platform labels that have no obtainable public wordmark.

    python3 tools/make-platform-labels.py

Three of the four systems on the partners page do not publish a mark this site
can use. Supplier One and NOVA are tools inside Walmart's supplier portal and
have no public brand asset at all; Circana has one, but it is behind a brand
portal rather than a URL, and their site is a Wix build that serves no clean
wordmark file.

So these are set type, not anybody's logo, matched to the `item360.png` they
replaced — Helvetica Neue Light at its exact ink colour and bounding box, so
they sit in the row at the same weight and optical size. The row is greyscaled
by CSS anyway, and the file they replaced was itself only a wordmark.

If a real asset is ever obtained, drop it in at 400x240 with a transparent
ground and delete that entry from LABELS.
"""
from PIL import Image, ImageDraw, ImageFont

W, H = 400, 240                       # every other file in assets/platforms/
INK = (72, 72, 72, 255)               # sampled off item360.png
TARGET_W, TARGET_H = 330, 65          # its ink bbox: x 31..361, y 89..154
FONT = "/System/Library/Fonts/HelveticaNeue.ttc"
LIGHT = 7                             # face index of Helvetica Neue Light

#: filename stem -> the words on it
LABELS = {
    "supplier-one": "Supplier One",
    "circana": "Circana",
    "nova": "NOVA",
}


def ink(text, size):
    """The text as a tight alpha mask, at a given size."""
    f = ImageFont.truetype(FONT, size, index=LIGHT)
    t = Image.new("L", (W * 3, H * 3), 0)
    ImageDraw.Draw(t).text((60, 60), text, font=f, fill=255)
    return t.crop(t.getbbox())


def shared_size():
    """One point size for every label, set by whichever is longest.

    Fitting each label to the box on its own is the obvious thing and it is
    wrong: a short word hits the height limit and a long one hits the width
    limit, so they come out at different type sizes and the row reads as if
    two of the four logos were scaled up. "Circana" rendered 88pt against
    "Supplier One" at 59 and looked it. A row of wordmarks wants one size.
    """
    for size in range(200, 29, -1):
        if all(ink(t, size).width <= TARGET_W and ink(t, size).height <= TARGET_H
               for t in LABELS.values()):
            return size
    raise SystemExit("no size fits every label")


def main():
    size = shared_size()
    for stem, text in LABELS.items():
        mask = ink(text, size)
        layer = Image.new("RGBA", mask.size, INK)
        layer.putalpha(mask)
        card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        card.alpha_composite(layer, ((W - mask.width) // 2, (H - mask.height) // 2))
        out = f"assets/platforms/{stem}.png"
        card.save(out)
        print(f"{text:14} {size:>4}pt  ink {mask.width}x{mask.height}  -> {out}")


if __name__ == "__main__":
    main()
