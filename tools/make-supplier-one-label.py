"""Render the Supplier One label for the platforms row.

Not Walmart's official mark — set type, matched to the Item 360 file it
replaces so it sits in the row at the same weight and colour. The row is
greyscaled by CSS anyway. Swap in the real asset if one is ever obtained.
"""
from PIL import Image, ImageDraw, ImageFont
import sys

W, H = 400, 240                       # every other file in assets/platforms/
INK = (72, 72, 72, 255)               # sampled off item360.png
TARGET_W, TARGET_H = 330, 65          # its ink bbox: x 31..361, y 89..154
TEXT = "Supplier One"
FONT = "/System/Library/Fonts/HelveticaNeue.ttc"

def fit(index):
    best = None
    for size in range(30, 160):
        f = ImageFont.truetype(FONT, size, index=index)
        t = Image.new("L", (W * 3, H * 3), 0)
        ImageDraw.Draw(t).text((60, 60), TEXT, font=f, fill=255)
        bb = t.getbbox()
        if not bb:
            continue
        w, h = bb[2] - bb[0], bb[3] - bb[1]
        if w <= TARGET_W and h <= TARGET_H:
            best = (size, w, h)
    return best

idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
size, w, h = fit(idx)
f = ImageFont.truetype(FONT, size, index=idx)
t = Image.new("L", (W * 3, H * 3), 0)
ImageDraw.Draw(t).text((60, 60), TEXT, font=f, fill=255)
mask = t.crop(t.getbbox())
layer = Image.new("RGBA", mask.size, INK)
layer.putalpha(mask)
card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
card.alpha_composite(layer, ((W - mask.width) // 2, (H - mask.height) // 2))
out = "assets/platforms/supplier-one.png"
card.save(out)
print(f"face index {idx}  size {size}  ink {mask.size}  -> {out}")
