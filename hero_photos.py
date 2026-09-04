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

Four rules the picks are chosen against.

No people: the hero is type over a photograph and a face pulls the eye off the
headline, and Caleb asked for the site's stock photography to be people-free.

No Walmart marks, signage or store livery: RetailMark sells into five banners
and does not trade on anyone's trademark.

No legible foreign-language signage. Justin read the first set as "Asian and
Indian" — they were in fact Brazilian, Hebrew and Turkish, which is the point:
a viewer does not identify the language, they just register that the picture is
from somewhere else, and a Bentonville brokerage's hero should not. Aisle
photography is where this bites hardest, because a shop is mostly signage. What
survives is the back of the operation — racking, pallets, cartons — which looks
the same in every country and carries almost no type at all.

Depth. Every frame needs somewhere to look down. A close crop of folded towels
was in this list and came out: at full bleed a texture fills the frame and
reads as a grey blur rather than as a place.

`market-hall` is the one shop-floor frame and it is here because Justin asked
for in-store pictures — of Walmart and TJ Maxx specifically, which is not
possible twice over: no stock library licenses their interiors, and putting a
retailer's livery on this site would be the endorsement the whole no-marks rule
exists to avoid. So it is an unbranded store instead, chosen against the same
three rules as everything else. Caleb picked it over a better-composed big-box
aisle *because* that one had shoppers in the far distance and this one has
none. Do not quietly swap it back.

It keeps the plain centred crop, and that was checked rather than assumed. The
band catches a wall banner reading "450 Canadian growers", and a country cue is
the exact thing that got the first set of photographs replaced — but judged
where it actually lands, greyscaled and under the scrim behind the buttons, the
word is not readable. Cropping past it was tried and made the picture worse: the
only band low enough is a chilled deli case, flat and close, and the only band
high enough is ceiling. Judge a frame in the hero, not in the file.
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
PICKS = [
    ("market-hall",    18139921),   # the only frame on the shop floor — see below
    ("warehouse-aisle", 5775099),   # racked aisle, vanishing point down the run
    ("club-racking",    4483610),   # club-format racking, pallets overhead
    ("pallet-stacks",  34221998),   # palletised cartons, floor line through them
    ("racking-run",     4170172),   # a second run, higher and darker
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
