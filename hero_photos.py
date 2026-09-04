#!/usr/bin/env python3
"""
hero_photos.py — prepare the photographs that cycle behind the hero.

    python3 hero_photos.py

The hero is a dark grey scrim over a photograph, and the photograph changes on
a timer. These are the photographs. Downloads each chosen Pexels shot, centre
-crops it to the hero band's 16:9, resizes, strips metadata and writes WebP
into assets/hero/.

Three conventions, shared with service_photos.py for the same reasons:

  * Greyscale is applied in CSS, not baked in here. One asset serves both if
    the decision ever changes, and a filter is a line to delete where
    re-exporting five files is not.
  * The picks live in this file rather than in a folder of loose downloads, so
    a rerun reproduces exactly what is on the page and a swap is a one-line
    edit.
  * CREDITS is kept even though the Pexels licence asks for nothing, because a
    .webp on disk has no provenance and a rights question a year from now needs
    one.

Two rules the picks are chosen against. No people: the hero is type over a
photograph and a face pulls the eye off the headline, and Caleb asked for the
site's stock photography to be people-free. No Walmart marks, signage or store
livery: RetailMark sells into five banners and does not trade on anyone's
trademark.
"""

import io
import json
import os
import subprocess
from PIL import Image, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assets", "hero")

# 16:9, and large: this is a full-bleed background, so on a 2560 monitor it is
# the widest thing the site ships. 2400 covers that without a 2x asset, which
# at this size would be most of a megabyte for a picture sitting under a scrim.
W, H = 2400, 1350

# slug -> Pexels photo id. Order is the order they cycle in.
#
# A close crop of folded towels was in here and came out: at full bleed it is a
# wall of texture with no depth, so it read as a grey blur rather than as a
# shop. The ones that survive all have somewhere to look down.
PICKS = [
    ("store-aisle",   5498225),   # supermarket aisle, deep centre perspective
    ("club-racking",   4483610),  # club-format racking, pallets overhead
    ("stocked-aisle",  5951182),  # a stacked display running back into shelves
    ("distribution",   5860937),  # the aisle a pallet leaves from
]

SRC = ("https://images.pexels.com/photos/{id}/pexels-photo-{id}.jpeg"
       "?auto=compress&cs=tinysrgb&w=2600")


def fetch(pid):
    """curl, not urllib: Pexels 403s the stdlib user agent."""
    r = subprocess.run(
        ["curl", "-sL", "--max-time", "90", SRC.format(id=pid)],
        capture_output=True)
    if len(r.stdout) < 20000:
        raise SystemExit(f"photo {pid} came back short ({len(r.stdout)}B)")
    return r.stdout


def main():
    os.makedirs(OUT, exist_ok=True)
    manifest = []
    for slug, pid in PICKS:
        im = Image.open(io.BytesIO(fetch(pid)))
        im = ImageOps.exif_transpose(im).convert("RGB")
        if im.width < W or im.height < H:
            raise SystemExit(f"{slug}: source {im.size} is smaller than {W}x{H}")
        im = ImageOps.fit(im, (W, H), Image.LANCZOS, centering=(0.5, 0.5))
        dst = os.path.join(OUT, f"{slug}.webp")
        im.save(dst, "WEBP", quality=78, method=6)   # no exif= : metadata dropped
        kb = os.path.getsize(dst) / 1024
        manifest.append({"slug": slug, "pexels_id": pid,
                         "page": f"https://www.pexels.com/photo/{pid}/",
                         "file": f"assets/hero/{slug}.webp",
                         "kb": round(kb, 1)})
        print(f"{slug:16s} {pid:>9}  {kb:7.1f} KB")
    with open(os.path.join(OUT, "credits.json"), "w") as f:
        json.dump({"license": "Pexels License — free for commercial use, "
                              "no attribution required",
                   "photos": manifest}, f, indent=2)
    print(f"\n{len(manifest)} files -> assets/hero/")


if __name__ == "__main__":
    main()
