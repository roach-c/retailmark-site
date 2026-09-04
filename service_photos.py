#!/usr/bin/env python3
"""
service_photos.py — prepare the nine photos on the homepage service cards.

    python3 service_photos.py

Downloads each chosen Pexels photo, centre-crops it to the card banner's 16:9,
resizes, strips metadata and writes WebP into assets/services/.

Same two conventions as photos.py, for the same two reasons:

  * Greyscale is applied in CSS, not baked in here. One asset serves both if the
    decision ever changes, and a filter is a line to delete where re-exporting
    nine files is not.
  * The picks live in this file rather than in a folder of loose downloads, so a
    rerun reproduces exactly what is on the page and a swap is a one-line edit.

Pexels licenses all of these for commercial use with no attribution required.
CREDITS is kept anyway: it is the only record of where a file came from once it
is a .webp on disk, and it is what a rights question a year from now needs.
"""

import io
import json
import os
import subprocess
from PIL import Image, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assets", "services")

# 16:9. The card is a banner over a title, not a portrait, and at the 3-up grid
# a card is ~452px wide — so 900 is a 2x asset for a retina screen and no more.
W, H = 900, 506

# slug -> Pexels photo id. Order matches the numbered cards on the homepage.
PICKS = [
    # (slug, pexels id, optional crop box as fractions of the source before the
    # 16:9 fit — used only where a centre crop puts the subject off-frame)
    ("sales-strategy",         29397977),   # boardroom table set for a session
    ("forecasting-analytics",    577210),   # dashboard on a laptop, clean desk
    ("item-creation",           7843978),   # barcode and QR labels on a carton
    ("replenishment-planning",  4487364),   # stocked racking, aisle in depth
    ("supply-chain-planning",  17653244),   # trailers lined up at a yard
    ("reporting",               7605981),   # printed performance pages
    ("e-commerce",              6956903),   # packed order beside a laptop
    ("trend-management",        5498228),   # a category wall, shelf to shelf
    ("pitch-deck-development",  7948041, (0.06, 0.22, 0.94, 0.98)),  # deck on screen
]

SRC = ("https://images.pexels.com/photos/{id}/pexels-photo-{id}.jpeg"
       "?auto=compress&cs=tinysrgb&w=1800")


def fetch(pid):
    """curl, not urllib: Pexels 403s the stdlib user agent."""
    r = subprocess.run(
        ["curl", "-sL", "--max-time", "60", SRC.format(id=pid)],
        capture_output=True)
    if len(r.stdout) < 20000:
        raise SystemExit(f"photo {pid} came back short ({len(r.stdout)}B)")
    return r.stdout


def main():
    os.makedirs(OUT, exist_ok=True)
    manifest = []
    for slug, pid, *rest in PICKS:
        im = Image.open(io.BytesIO(fetch(pid)))
        im = ImageOps.exif_transpose(im).convert("RGB")
        if rest:
            l, t, r, b = rest[0]
            im = im.crop((int(im.width * l), int(im.height * t),
                          int(im.width * r), int(im.height * b)))
        if im.width < W or im.height < H:
            raise SystemExit(f"{slug}: source {im.size} is smaller than {W}x{H}")
        im = ImageOps.fit(im, (W, H), Image.LANCZOS, centering=(0.5, 0.5))
        dst = os.path.join(OUT, f"{slug}.webp")
        im.save(dst, "WEBP", quality=82, method=6)   # no exif= : metadata dropped
        kb = os.path.getsize(dst) / 1024
        manifest.append({"slug": slug, "pexels_id": pid,
                         "page": f"https://www.pexels.com/photo/{pid}/",
                         "file": f"assets/services/{slug}.webp",
                         "kb": round(kb, 1)})
        print(f"{slug:26s} {pid:>9}  {kb:6.1f} KB")
    with open(os.path.join(OUT, "credits.json"), "w") as f:
        json.dump({"license": "Pexels License — free for commercial use, "
                              "no attribution required",
                   "photos": manifest}, f, indent=2)
    print(f"\n{len(manifest)} files -> assets/services/")


if __name__ == "__main__":
    main()
