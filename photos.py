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

# Dropped, with the reason, so a rerun cannot quietly bring them back.
SKIP = {
    "Welcome-Center-Exterior-2.jpeg":
        "crops to a lone M in a strip, and it is Walmart's visitor centre",
    "images.jpeg":
        "596x335 source, enlarged 4.5x to fill the strip — visibly mushy",
    "00biz-walmart-cool-rebrand-01-tfwz-articleLarge.webp":
        "600x400 source, enlarged 3.8x, and Walmart property",
    "shutterstock-1366855787.webp":
        "grainy at 2.2x, and the sign in it reads WALTON",
}

# Anything needing more than this much enlargement will look soft however good
# the original composition is. It is tighter than the vertical version could
# afford: cropping landscape sources to landscape bands needs barely any
# enlargement, so the bar can be raised rather than lowered to keep six.
MAX_UPSCALE = 1.9
OUT = os.path.join(HERE, "assets", "bentonville")
W, H = 1400, 540           # 2.6:1. The block is three horizontal bands, and
                           # the sources are landscape, so this crops with the
                           # grain of the photographs instead of against it.
                           # The vertical version threw away most of every
                           # frame and needed far more enlargement to do it.

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
    # Only the files this script produces. It used to clear the whole
    # directory, which deleted SOURCES.md — the note recording that these
    # photographs are not cleared for publication. Losing that note is worse
    # than losing a picture, and nothing complained either way.
    for old in glob.glob(os.path.join(OUT, "*.webp")) + [os.path.join(OUT, "manifest.json")]:
        if os.path.exists(old):
            os.remove(old)

    made = []
    for f in files:
        base = os.path.basename(f)
        if base in SKIP:
            print(f"  skipped {base[:42]:42}  {SKIP[base]}")
            continue
        probe = Image.open(f)
        probe = ImageOps.exif_transpose(probe)
        up = max(W / probe.width, H / probe.height)
        if up > MAX_UPSCALE:
            print(f"  skipped {base[:42]:42}  would need {up:.1f}x enlargement")
            continue
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
