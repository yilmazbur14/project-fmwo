"""Entrance frames 9-15: grip, heave, strain, pull, raise, point, point-breath.

The hand-off is frame 9. The world's planted sword hides on that frame and this
sheet's drawn sword takes over, so frame 9's blade-to-ground contact must land on
PLANT_PIXEL = (160, 186) - 32 texels to the VIEWER'S RIGHT of his centreline, so
he reaches down beside himself rather than across his chest. The buried sword art
puts its grip 22 texels above that contact, which lands at (160, 164) in his
frame: just above his belt, a natural two-handed height.

Frames 12-15 use his own sheet frame 0 MIRRORED. Unmirrored he carries the blade
up across his left; mirrored it is up across his right, which is the side the
sword came out of. That also means the arms gripping it are his own drawn arms,
not something I invented.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vs_card"))
from PIL import Image
from pxlib import plate, poly, seam, px
import parts as P
import walk as W
import sword as SW

FW, FH = W.FW, W.FH
FLOOR, CX = W.FLOOR, W.CX
PLANT = (160, 186)                     # EricEntranceLayout.PLANT_PIXEL
GRIP = (PLANT[0], PLANT[1] - (SW.CONTACT[1] - SW.GRIP_CENTRE[1]))    # (160, 164)
SHEET_BOX = P.SHEET_BOX

PL, PL_LT, PL_SH = P.PL, P.PL_LT, P.PL_SH
ST_LT, ST, ST_DK = P.ST_LT, P.ST, P.ST_DK
DUST = W.DUST


def buried_at(im, rise=0):
    """The planted sword, its ground contact on PLANT_PIXEL, lifted by `rise`."""
    s = SW.build()
    im.alpha_composite(s, (PLANT[0] - SW.CONTACT[0], PLANT[1] - SW.CONTACT[1] - rise))


STEEL = {(163, 168, 174), (124, 129, 135), (92, 96, 103), (65, 68, 75), (43, 45, 51), (212, 216, 220)}
WOOD = {(156, 96, 56), (116, 67, 42), (78, 44, 28), (51, 28, 18), (196, 138, 88)}
BLADE_CUT_Y = 120          # above this is blade and crossguard.
#                            127 clipped his upper GAUNTLET, which sits at y127 -
#                            the very hand that has to close on the hilt.
BLADE_CUT_X = 67           # his plate reaches x66 at those rows; stay right of it
HIGH_CUT_Y, HIGH_CUT_X = 100, 58   # above his head nothing of him is present


def sheet_mirrored(strip_blade=False):
    """Sheet frame 0, flipped, so the blade rides up across his RIGHT.

    strip_blade removes his own sword so the buried one can take its place.
    His blade and his gauntlets are the same steel, so colour alone cannot
    separate them - region does the finding (steel above y127 and right of x58
    is blade and crossguard; below that is haft and hands) and colour only
    protects what must survive. His plate armour, head and cape are different
    families entirely and are never touched."""
    f = Image.open(P.SHEET).convert("RGBA").crop(SHEET_BOX).transpose(Image.FLIP_LEFT_RIGHT)
    if not strip_blade:
        return f
    px = f.load()
    for y in range(f.height):
        for x in range(f.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            c = (r, g, b)
            # The blade's own black KEYLINE has to go with it, or the erase
            # leaves a hollow outline of a sword. Black is everything's outline,
            # so it is only cut where nothing of him can be: right of his plate
            # below his head, and anywhere above it.
            in_blade = (y < BLADE_CUT_Y and x >= BLADE_CUT_X) or                        (y < HIGH_CUT_Y and x >= HIGH_CUT_X)
            if c in WOOD or ((c in STEEL or c == (0, 0, 0)) and in_blade):
                px[x, y] = (0, 0, 0, 0)
    return f


def hands(im, x, y):
    """Both gauntlets closed on the hilt, stacked."""
    for dy in (0, 7):
        plate(im, [(x - 5, y + dy - 1), (x + 5, y + dy - 1), (x + 6, y + dy + 3),
                   (x + 3, y + dy + 6), (x - 3, y + dy + 6), (x - 6, y + dy + 3)],
              ST_LT, hi=PL_LT, sh=ST)
        poly(im, [(x - 4, y + dy + 1), (x + 4, y + dy + 1), (x + 4, y + dy + 3),
                  (x - 4, y + dy + 3)], ST_DK)


def gripping_arm(im, ox, oy, side, hx, hy):
    """Upper arm hangs exactly as it does in the walk; only the FOREARM bends.

    Drawing a whole arm from shoulder to hilt is what left floating limbs twice -
    a drawn arm only attaches at the pixels it was drawn at. The elbow is a joint
    I control, so the upper arm is reused unchanged and the forearm swings off it
    to meet the hilt. The far arm crosses at belt height, below the chest cross."""
    cx = ox + W.ARM_CX[0 if side < 0 else 1]
    t = oy + W.ARM_TOP
    e = t + 11                                   # elbow, beside the hip
    plate(im, [(cx - 4, t), (cx + 4, t), (cx + 4, e), (cx - 4, e)], PL, hi=PL_LT, sh=PL_SH)
    dx = 1 if hx > cx else -1
    plate(im, [(cx - 3, e - 1), (cx + 3, e - 1), (hx + dx * 3, hy + 4),
               (hx - dx * 3, hy + 2)], PL, hi=PL_LT, sh=PL_SH)


def strain_dust(im, x, y, level):
    for i, (ddx, ddy, r) in enumerate(((-11, 0, 3), (-5, -4, 2), (5, -5, 2), (12, -1, 3),
                                       (-17, 2, 2), (18, 2, 2))[: 3 + level]):
        poly(im, [(x + ddx - r, y + ddy), (x + ddx, y + ddy - r), (x + ddx + r, y + ddy),
                  (x + ddx, y + ddy + r // 2)], DUST[i % 3])


# Measured, not guessed: in mirrored frame 0 his own upper hand grips at
# (163, 167) and the buried sword's hilt is at (160, 164). Three texels apart,
# so the figure nudges by that and his OWN hands land on the hilt - no drawn
# limbs, no deeper burial, crossguard still above the mat, PLANT_PIXEL unchanged.
# An earlier reading said the gap was 19 texels; that had found a sabaton.
HAND_NUDGE = (-3, -3)
SHEET_AT = (CX - 107 // 2, FH - 152)        # where the mirrored tight frame lands


def figure(strip_blade, dx=0, dy=0):
    im = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
    m = sheet_mirrored(strip_blade)
    im.alpha_composite(m, (SHEET_AT[0] + HAND_NUDGE[0] + dx, SHEET_AT[1] + HAND_NUDGE[1] + dy))
    return im


def frame_grip(dy, dust_level, rise=0):
    """9-11: he grips the buried hilt with his own hands."""
    im = figure(True, 0, dy)
    buried_at(im, rise)
    im.alpha_composite(figure(True, 0, dy), (0, 0))     # hands sit over the hilt
    if dust_level:
        strain_dust(im, PLANT[0], PLANT[1] - 1, dust_level)
    return im


def frame_out(dy, debris=0, socket=True):
    """12-15: blade is free, so his own sheet pose carries it."""
    im = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
    if socket:
        sk = SW.build(False, SW.SOCKET_W, SW.SOCKET_H, SW.SOCKET_CONTACT)
        im.alpha_composite(sk, (PLANT[0] - SW.SOCKET_CONTACT[0], PLANT[1] - SW.SOCKET_CONTACT[1]))
    im.alpha_composite(figure(False, 0, dy), (0, 0))
    if debris:
        strain_dust(im, PLANT[0], PLANT[1] - 2, debris)
    return im


def build():
    return [
        frame_grip(0, 0),              # 9  grip
        frame_grip(3, 1),              # 10 heave
        frame_grip(4, 2, rise=2),      # 11 strain
        frame_out(3, debris=2),        # 12 pull - blade breaks free
        frame_out(0, debris=1),        # 13 raise
        frame_out(0),                  # 14 point   (placeholder - see report)
        frame_out(1),                  # 15 point, breathing
    ]


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    fr = build()
    strip = Image.new("RGBA", (FW * len(fr), FH), (0, 0, 0, 0))
    for i, f in enumerate(fr):
        strip.alpha_composite(f, (i * FW, 0))
    strip.save(os.path.join(out, "_pull_strip.png"))
    prev = Image.new("RGBA", (FW * len(fr), FH), (34, 32, 52, 255))
    prev.alpha_composite(strip)
    prev.resize((int(prev.width * 1.1), int(prev.height * 1.1)), Image.NEAREST).convert("RGB").save(
        os.path.join(out, "_pull_preview.png"))
    print("frames 9-15:", len(fr))
