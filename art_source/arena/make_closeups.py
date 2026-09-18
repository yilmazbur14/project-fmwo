"""
Close-up sheets cut straight out of the full-size mockups.

The art is authored at 1 art px = 3 screen px, so a 1:1 crop of the 1920x1080
mockup already IS the 3x view. Each sheet also carries blow-ups of small
patches so the actual pixel work can be inspected.

    python make_closeups.py --out <dir> --keys a,b,c
"""

import argparse
import os

from PIL import Image

GUT = 10
BG = (16, 16, 20)


def crop(im, box, factor=1):
    c = im.crop(box)
    if factor == 1:
        return c
    return c.resize((c.width * factor, c.height * factor), Image.NEAREST)


def col(tiles):
    """Stack tiles vertically, left-aligned."""
    w = max(t.width for t in tiles)
    h = sum(t.height for t in tiles) + GUT * (len(tiles) - 1)
    out = Image.new("RGB", (w, h), BG)
    y = 0
    for t in tiles:
        out.paste(t, (0, y))
        y += t.height + GUT
    return out


def row(tiles):
    """Lay columns out left to right, top-aligned, on a padded canvas."""
    w = sum(t.width for t in tiles) + GUT * (len(tiles) + 1)
    h = max(t.height for t in tiles) + GUT * 2
    out = Image.new("RGB", (w, h), BG)
    x = GUT
    for t in tiles:
        out.paste(t, (x, GUT))
        x += t.width + GUT
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--keys", default="a,b,c")
    args = ap.parse_args()

    for k in args.keys.split(","):
        m = Image.open(os.path.join(args.out, f"mockup_{k}.png")).convert("RGB")

        # --- mat: painted corner, centre crest, bare canvas at 2x (= 6x art)
        row([crop(m, (113, 570, 613, 970)),        # border lines + corner arc
             crop(m, (700, 330, 1220, 730)),       # emblem + centre ring
             crop(m, (500, 380, 750, 580), 2),     # bare canvas grain
             ]).save(os.path.join(args.out, f"closeup_mat_{k}.png"))

        # --- ringside: the left band full height and at 3x, then the bottom
        #     band's dressing and the corner where the two mitre together
        row([crop(m, (0, 190, 130, 810)),          # left band, top to bottom
             crop(m, (0, 380, 100, 580), 3),       # the same bands at 3x
             col([crop(m, (700, 960, 1250, 1080), 2),   # desk, cases, cables
                  crop(m, (40, 930, 590, 1050), 2),     # bottom-left mitre
                  ]),
             ]).save(os.path.join(args.out, f"closeup_ringside_{k}.png"))
        print("closeups for", k)


if __name__ == "__main__":
    main()
