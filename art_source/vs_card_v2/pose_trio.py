"""JORDAN, JOSH and MATT - VS poses built from their own approved frames (STYLE.md).

Each is one frame of the character's sheet, as drawn and unmirrored (so the one upper-left light
holds), enlarged by Scale2x, with at most one effect from the character's own vocabulary:

  JORDAN  jordan_taunt.png frame 2 - the chase box hoisted like a trophy, laughing, turned to Burak.
          His own frame already carries its sparkle; nothing is added. SUPERSEDED on 2026-09-24 by
          pose_jordan_v2 (his approved v2 look); kept for the record, and build_trio no longer uses it.
  JOSH    josh_cards.png frame 1 (v3, approved 2026-09-23) - the card fan held out toward Burak,
          the gold spade card glowing up by his face, the wink. Nothing is added.
  MATT    matt_roar.png frame 2 (the approved intro set) - the roar - with the two sound rings of
          his approved first sprite (matt.png frame 1) behind him: same colours, same radii about
          his face, drawn at 2x with a white core between dark lavender edges, so they read as his
          rings at the card's scale rather than as a doubled 4-px band.

The seam and the band's rules frame every pose (halves.py); each pose's own canvas starts at the
frame's top-left, and PLACE in build_trio puts its eyes on the shared line.
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pxkit as P                                                             # noqa: E402

JORDAN = ("Jordan/jordan_taunt.png", 2, 96)
JOSH = ("Josh/josh_cards.png", 1, 80)
MATT = ("Matt/matt_roar.png", 2, 96)
# matt.png frame 1's rings: centre on his face, the two radii, the core and edge colours
RING_CENTRE_1X = (48, 49)
RING_RADII_1X = (42, 30)
RING_CORE, RING_EDGE = "#F2F3FF", "#4F4D96"


def frame(spec):
    path, i, size = spec
    return P.load(path, (i * size, 0, i * size + size, size))


def jordan():
    return P.scale2x(frame(JORDAN))


def josh():
    return P.scale2x(frame(JOSH))


def rings_2x(size):
    """His two sound rings at 2x: a 2-texel white core with a 1-texel dark lavender edge each side."""
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    px = im.load()
    cx, cy = RING_CENTRE_1X[0] * 2 + 1, RING_CENTRE_1X[1] * 2 + 1
    core, edge = P.rgba(RING_CORE), P.rgba(RING_EDGE)
    for y in range(size[1]):
        for x in range(size[0]):
            d = ((x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2) ** 0.5
            for r in RING_RADII_1X:
                off = abs(d - r * 2)
                if off < 1.0:
                    px[x, y] = core
                elif off < 2.0:
                    px[x, y] = edge
    return im


def matt():
    body = P.scale2x(frame(MATT))
    out = rings_2x(body.size)
    out.alpha_composite(body)
    return out


if __name__ == "__main__":
    out = sys.argv[1]
    for name, fn in (("jordan", jordan), ("josh", josh), ("matt", matt)):
        im = fn()
        P.save_zoom(im, os.path.join(out, "pose_%s_4x.png" % name), 4)
        print(name, im.size, P.numbers(im))
