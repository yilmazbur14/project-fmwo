"""ERIC - the greatsword levelled at Burak.

Built from his own pixels: eric_sheet_v2.png frame 3, the earthquake wind-up, where he holds the
blade flat over his head. Here it points the other way, at Burak, and runs out of his half through
the seam, which cuts it (STYLE.md: nothing crosses into the other half) - so the blade reads as
reaching Burak without being drawn over him.

What moves and what does not (all at 1x, in frame-3 coordinates, before the 2x):
  * the body - head, beard, pauldrons, chest, cape, belt - is frame 3's, unmoved and unmirrored,
    so it keeps the cast's upper-left light
  * the blade is mirrored about his centreline (x = 56.5); its shading runs along the blade, so a
    mirror keeps it lit from above
  * the crossguard, grip and pommel are TRANSLATED to the other end rather than mirrored, so their
    own left-lit shading survives; the same for both arms, which swap sides
The parts are cut along their own keylines (segment.py), so every seam is one of his lines.

Then Scale2x to 2x, and the hand pass (detail(), which the 1x sprite has no room for): a gleam
across the flat of the blade near the end that points at Burak.
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pxkit as P                                                             # noqa: E402
import segment as S                                                           # noqa: E402

SOURCE = "Eric/eric_sheet_v2.png"
FRAME = 3
OX = 36                     # canvas margin on the left, for the blade that now points that way

# component ids in frame 3's crop (segment.components order), checked by tint_view
BLADE, GUARD, POMMEL, GRIP = [1], [0], [2], [4]
FIST_GRIP = [3, 5, 6, 7]            # the gauntlet on the grip
ARM_GRIP = [9, 16, 19, 23]          # its vambrace and elbow
FIST_FLAT = [10, 13, 14, 15]        # the gauntlet under the flat of the blade
ARM_FLAT = [17, 18, 22, 26, 27]

# where each part goes (dx at 1x, frame-3 coordinates); the blade is mirrored instead
AXIS2 = 113                 # mirror line x = 56.5, his centreline
MOVE = {"guard": 44, "fist_grip": 61, "arm_grip": 61, "grip": 85, "pommel": 107,
        "fist_flat": -61, "arm_flat": -61}


def frame3():
    f = P.load(SOURCE, (FRAME * 256, 0, FRAME * 256 + 256, 192))
    return f.crop(f.getbbox())


def layer_at(img, x, y, size):
    """img placed at (x, y) on an empty canvas of `size` - clipped, negative offsets allowed."""
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    out.paste(img, (x, y), img)
    return out


def assemble():
    """The re-posed figure at 1x, on a canvas OX wider on the left."""
    f = frame3()
    comps = S.components(f)
    size = (f.width + OX, f.height)
    part = lambda ids: S.take(f, comps, ids)

    moved = set(BLADE + GUARD + POMMEL + GRIP + FIST_GRIP + ARM_GRIP + FIST_FLAT + ARM_FLAT)
    # The body keeps every keyline it touches: only the moved parts' colour leaves it, and the black
    # that ringed them stays wherever it also rings a piece of the body.
    body = S.take(f, comps, [c["id"] for c in comps if c["id"] not in moved], ring=True)

    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    # the sword, behind everything: the blade mirrored about his centreline, the hilt translated
    src = part(BLADE)
    blade = Image.new("RGBA", size, (0, 0, 0, 0))
    sp, bp = src.load(), blade.load()
    for y in range(src.height):
        for x in range(src.width):
            if sp[x, y][3] > 128:
                nx = OX + (AXIS2 - 1 - x)
                if 0 <= nx < size[0]:
                    bp[nx, y] = sp[x, y]
    canvas.alpha_composite(blade)
    for ids, key in ((GUARD, "guard"), (GRIP, "grip"), (POMMEL, "pommel")):
        canvas.alpha_composite(layer_at(part(ids), OX + MOVE[key], 0, size))
    # the body, over the blade (his head is in front of it in frame 3 too)
    canvas.alpha_composite(layer_at(body, OX, 0, size))
    # both arms, over the body
    for ids, key in ((ARM_FLAT, "arm_flat"), (FIST_FLAT, "fist_flat"),
                     (ARM_GRIP, "arm_grip"), (FIST_GRIP, "fist_grip")):
        canvas.alpha_composite(layer_at(part(ids), OX + MOVE[key], 0, size))
    return canvas


BLADE_FLAT = "#7C8187"
GLEAM_EDGE, GLEAM_CORE = "#D4D8DC", "#FFFFFF"   # his steel's top tone, and the white of his sparkle


def detail(im):
    """The 2x pass. The blade carries a gleam near the end that points at Burak: a streak of his
    steel's lightest tone with a white core, slanting across the flat of the blade - the anime
    glint his sheet only has room for as the four-point sparkle - and a thinner echo beside it. It
    is painted only onto the flat, so the bevels and the keyline are untouched."""
    px = im.load()
    flat = P.rgba(BLADE_FLAT)

    def streak(x_top, width):
        for y in range(16, 44):
            x = x_top - (y - 16) * 7 // 12
            for i in range(width):
                xx = x + i
                if 0 <= xx < im.width and px[xx, y] == flat:
                    edge = i == 0 or i == width - 1
                    px[xx, y] = P.rgba(GLEAM_EDGE if edge else GLEAM_CORE)

    streak(118, 4)
    streak(126, 2)
    return im


def build():
    base = assemble()
    return detail(P.scale2x(base))


if __name__ == "__main__":
    out = sys.argv[1]
    a = assemble()
    P.save_zoom(a, os.path.join(out, "eric_pose_1x_8x.png"), 8)
    b = build()
    P.save_zoom(b, os.path.join(out, "eric_pose_2x_4x.png"), 4)
    print("1x", a.size, P.numbers(a))
    print("2x", b.size, P.numbers(b))
