#!/usr/bin/env python3
"""
palette.py — recolour the whole brand without touching a single letterform.

    python3 palette.py --list
    python3 palette.py <name>
    python3 palette.py <name> --check     contrast report only, writes nothing

Justin's colours were never chosen — they came with the logo. The shape is
fixed, because the hats are imprinted with it, so this only ever rewrites
COLOUR: it maps existing pixels to new ones and never touches the alpha
channel, which is what carries the shape and its antialiasing.

Every asset is regenerated from the two-tone masters in assets/. The wordmark
is white "Retail" plus gold "Mark", and the four RM slices split on the same
line — r and etail are the ink half, m and ark are the accent half — so a
palette is really just two colours plus their tints.

Contrast is checked, not assumed. The gold this started with fails WCAG AA for
body text on cream at 2.1:1, which is why --gold-dark had to exist at all.
"""

import os
import re
import shutil
import sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, "assets")
MASTERS = os.path.join(A, "masters")

# ink, accent, accent-light, accent-dark (for text on a light ground),
# charcoal, cream, gray, gray-light, border
PALETTES = {
    "gold": dict(ink="#111111", accent="#E8B923", light="#EFCE64", dark="#8D6D0F",
                 charcoal="#222226", cream="#FAF8F3", gray="#6B6B6F",
                 gray_light="#9A9A9E", border="#E8E6DF",
                 note="what it has now — the colours that came with the logo"),

    "clay": dict(ink="#14110F", accent="#CC5A31", light="#DB8769", dark="#A8451F",
                 charcoal="#241E1A", cream="#FBF7F2", gray="#6E6660",
                 gray_light="#9C948C", border="#E8E0D6",
                 note="ink and clay — warm, food-adjacent, unlike anyone in this market"),

    "navy": dict(ink="#0F1B2D", accent="#C8873C", light="#D8A974", dark="#9D6523",
                 charcoal="#1B2A40", cream="#F9F7F3", gray="#5F6A78",
                 gray_light="#93A0AE", border="#DFE4EA",
                 note="deep navy and warm brass — the classic trustworthy retail pairing"),


    "signal": dict(ink="#15171A", accent="#E2542C", light="#EB876B", dark="#BE401D",
                   charcoal="#22262B", cream="#F8F8F6", gray="#63686E",
                   gray_light="#969BA1", border="#E3E5E2",
                   note="slate and signal orange — retail energy, high visibility"),

    "espresso": dict(ink="#1A1310", accent="#B08D4F", light="#C6AD80", dark="#8A6C35",
                     charcoal="#2A211B", cream="#FAF7F1", gray="#6E655B",
                     gray_light="#9C9287", border="#E9E1D5",
                     note="espresso and brass — where the current gold was going, done properly"),
}


# ---------------------------------------------------------------- contrast
def lum(hexcol):
    c = [int(hexcol[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def ratio(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def report(p):
    checks = [
        ("body text: gray on cream", p["gray"], p["cream"], 4.5),
        ("headline: ink on cream", p["ink"], p["cream"], 4.5),
        ("link text: accent-dark on cream", p["dark"], p["cream"], 4.5),
        ("button label: ink on accent", p["ink"], p["accent"], 4.5),
        ("nav hover: accent on ink", p["accent"], p["ink"], 4.5),
        ("wordmark half: accent on ink", p["accent"], p["ink"], 3.0),
    ]
    worst, lines = 99, []
    for label, fg, bg, need in checks:
        r = ratio(fg, bg)
        worst = min(worst, r / need)
        lines.append(f"    {'ok ' if r >= need else 'FAIL'} {label:34} {r:.2f}:1 (needs {need})")
    return lines, worst


# ---------------------------------------------------------------- artwork
def recolour(src, dst, ink_to, accent_to, ink_is_white=True):
    """Map the two source colours to two new ones. Alpha is never touched, so
    the letterforms and their antialiasing come out identical."""
    im = Image.open(src).convert("RGBA")
    px, (w, h) = im.load(), im.size
    out = Image.new("RGBA", (w, h))
    op = out.load()
    ink_rgb = tuple(int(ink_to[i:i + 2], 16) for i in (1, 3, 5))
    acc_rgb = tuple(int(accent_to[i:i + 2], 16) for i in (1, 3, 5))
    for y in range(h):
        for x in range(w):
            r, g, b, al = px[x, y]
            if al == 0:
                op[x, y] = (0, 0, 0, 0)
            elif max(r, g, b) - min(r, g, b) < 40:     # achromatic = the ink half
                op[x, y] = ink_rgb + (al,)
            else:                                       # coloured = the accent half
                op[x, y] = acc_rgb + (al,)
    out.save(dst)


def ensure_masters():
    """Keep untouched originals, or the second recolour is a copy of the first."""
    os.makedirs(MASTERS, exist_ok=True)
    for f in ("retailmark-wordmark.png", "rm-r.png", "rm-etail.png",
              "rm-m.png", "rm-ark.png", "bentonville-arkansas.png"):
        m = os.path.join(MASTERS, f)
        if not os.path.exists(m):
            shutil.copyfile(os.path.join(A, f), m)


def apply(name):
    p = PALETTES[name]
    ensure_masters()

    # on the black header the ink half is white; on the cream hero it is the ink
    for f, on_dark, on_light in (
        ("retailmark-wordmark.png", "#FFFFFF", None),
        ("rm-r.png", "#FFFFFF", None),
        ("rm-etail.png", "#FFFFFF", None),
        ("rm-m.png", "#FFFFFF", None),
        ("rm-ark.png", "#FFFFFF", None),
        ("bentonville-arkansas.png", "#FFFFFF", None),
    ):
        recolour(os.path.join(MASTERS, f), os.path.join(A, f), on_dark, p["accent"])
    recolour(os.path.join(MASTERS, "retailmark-wordmark.png"),
             os.path.join(A, "retailmark-wordmark-dark.png"), p["ink"], p["accent"])

    # Derived, not hand-specified: five more tokens all sit a fixed step off
    # the ink, so a new palette only ever has to name two real colours.
    ink = tuple(int(p["ink"][i:i + 2], 16) for i in (1, 3, 5))
    step = lambda n: "#%02X%02X%02X" % tuple(min(255, v + n) for v in ink)
    derived = {
        "--ink-rgb": f"{ink[0]}, {ink[1]}, {ink[2]}",
        "--ink-raised": step(3),
        "--card-dark": step(9),
        "--card-border": step(36),
        "--on-dark-muted": "#%02X%02X%02X" % tuple(min(255, v + 190) for v in ink),
    }

    css = os.path.join(HERE, "styles.css")
    s = open(css).read()
    for tok, val in (("--black", p["ink"]), ("--charcoal", p["charcoal"]),
                     ("--gold", p["accent"]), ("--gold-light", p["light"]),
                     ("--gold-dark", p["dark"]), ("--cream", p["cream"]),
                     ("--gray", p["gray"]), ("--gray-light", p["gray_light"]),
                     ("--border", p["border"])):
        s = re.sub(rf'(  {re.escape(tok)}: )#[0-9A-Fa-f]{{6}};', rf'\g<1>{val};', s, count=1)
    for tok, val in derived.items():
        s = re.sub(rf'(  {re.escape(tok)}: )[^;]+;', rf'\g<1>{val};', s, count=1)
    acc = tuple(int(p["accent"][i:i + 2], 16) for i in (1, 3, 5))
    dark = tuple(int(p["dark"][i:i + 2], 16) for i in (1, 3, 5))
    s = re.sub(r'rgba\(232,\s*185,\s*35,', f'rgba({acc[0]}, {acc[1]}, {acc[2]},', s)
    s = re.sub(r'rgba\(199,\s*154,\s*21,', f'rgba({dark[0]}, {dark[1]}, {dark[2]},', s)
    open(css, "w").write(s)
    return p


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--list" in sys.argv or not args:
        for n, p in PALETTES.items():
            lines, worst = report(p)
            flag = "" if worst >= 1 else "   <- has a contrast failure"
            print(f"  {n:10} {p['ink']} + {p['accent']}   {p['note']}{flag}")
        sys.exit(0)
    name = args[0]
    if name not in PALETTES:
        raise SystemExit(f"unknown palette {name!r}; try --list")
    lines, _ = report(PALETTES[name])
    print(f"  {name}: {PALETTES[name]['note']}")
    print("\n".join(lines))
    if "--check" not in sys.argv:
        apply(name)
        print(f"\n  applied. now: python3 ogimage.py && python3 chrome.py")
