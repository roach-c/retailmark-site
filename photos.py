#!/usr/bin/env python3
"""
photos.py — prepare the hero slideshow images.

    python3 photos.py "~/Desktop/RetailMark Photos"

Reads whatever is in the source folder, centre-crops each to the hero panel's
4:5, resizes, strips metadata and writes WebP into assets/bentonville/ plus a
manifest the page reads.

Greyscale is applied in CSS, not baked in here, for two reasons: one asset
serves both if the decision ever changes, and a filter is a single line to
remove where re-exporting ten files is not.
"""

import json
import os
import sys
import glob
from PIL import Image, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assets", "bentonville")
W, H = 1000, 1250          # 4:5, at 2x the panel's largest rendered size

def slug(name):
    s = os.path.splitext(os.path.basename(name))[0].lower()
    return "".join(c if c.isalnum() else "-" for c in s).strip("-")[:44]

def main(src):
    src = os.path.expanduser(src)
    files = sorted(f for f in glob.glob(os.path.join(src, "*"))
                   if not os.path.basename(f).startswith(".")
                   and os.path.splitext(f)[1].lower() in
                   (".jpg", ".jpeg", ".png", ".webp", ".heic"))
    if not files:
        raise SystemExit(f"no images in {src}")
    os.makedirs(OUT, exist_ok=True)
    for old in glob.glob(os.path.join(OUT, "*")):
        os.remove(old)

    made = []
    for f in files:
        im = Image.open(f)
        # honour the EXIF rotation flag before cropping, or a portrait shot
        # gets centre-cropped along the wrong axis
        im = ImageOps.exif_transpose(im).convert("RGB")
        im = ImageOps.fit(im, (W, H), Image.LANCZOS, centering=(0.5, 0.42))
        name = slug(f) + ".webp"
        # save() from a fresh copy, so nothing from the original's metadata
        # rides along into a file that goes on a public server
        clean = Image.new("RGB", im.size)
        clean.putdata(list(im.getdata()))
        clean.save(os.path.join(OUT, name), "WEBP", quality=82, method=6)
        made.append({"file": name, "from": os.path.basename(f)})
        print(f"  {os.path.basename(f)[:44]:44} -> {name}  "
              f"{os.path.getsize(os.path.join(OUT,name))/1024:.0f}K")

    with open(os.path.join(OUT, "manifest.json"), "w") as fh:
        json.dump(made, fh, indent=1)
    print(f"\n  {len(made)} images, "
          f"{sum(os.path.getsize(os.path.join(OUT,m['file'])) for m in made)/1024:.0f}K total")
    return made

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "~/Desktop/RetailMark Photos")
