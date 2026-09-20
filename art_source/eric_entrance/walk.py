"""Eric's entrance walk: frames 0-7 looping, frame 8 arrival.

Brief: strong, menacing, walking up to his sword. The code drives six discrete
heavy steps - a push then a plant, with a screen shake on the plant - so this is
NOT a smooth even gait. It is built around the plant: the contact frame is the
lowest point of the bob, it carries dust at the foot, and the two frames after
it hold that weight before the next push.

He is a short, heavy, armoured figure: about 88px crown to sole with tassets
covering most of the thigh. So the walk reads through the body bob, the tassets,
and the sabatons stepping out from under the skirt - not through leg swing.
Shoulders stay square and the head stays fixed forward the whole cycle; he is
not hurried and he is not looking anywhere but at the player.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vs_card"))
from PIL import Image
from pxlib import plate, poly, hx
import parts as P

FW, FH = 256, 192
FLOOR = 191                     # feet on this row
CX = 128                        # body centred on this column
BODY_CX = 48                    # the chest cross's x inside the body part
TASSET_BOTTOM = 176             # where the skirt ends and the sabatons start

PL_HI, PL_LT, PL, PL_MD, PL_SH = P.PL_HI, P.PL_LT, P.PL, P.PL_MD, P.PL_SH
ST_LT, ST, ST_DK = P.ST_LT, P.ST, P.ST_DK
BK = P.BK
DUST = ["#A3B1C2", "#7A86A0", "#525A74"]

# per frame: body bob (+ is down), front sabaton dx, back sabaton dx, dust level
#            f0 plant  f1 settle f2 push  f3 lift  f4 plant f5 settle f6 push f7 lift  f8 arrive
BOB = [3, 4, 1, -2, 3, 4, 1, -2, 0]
LEAD = [1, 1, 1, 1, -1, -1, -1, -1, 0]      # which foot is forward (+1 = his left)
STEP = [9, 9, 5, 2, 9, 9, 5, 2, 0]          # how far the lead foot is forward
DUSTF = [2, 1, 0, 0, 2, 1, 0, 0, 0]


ARM_TOP, ARM_BOT = 47, 68
ARM_CX = (27, 84)               # arm centre columns inside the body part


def draw_arm(im, ox, oy, side, dy):
    """Upper arm tight to the torso, forearm dropping, closed fist at the hip.

    A front-on walk reads the swing as a small rise and fall of the fists
    opposed to the legs, not as a wide arc - so the travel here is 2px."""
    cx = ox + ARM_CX[0 if side < 0 else 1]
    t, b = oy + ARM_TOP + dy, oy + ARM_BOT + dy
    plate(im, [(cx - 4, t), (cx + 4, t), (cx + 4, b - 8), (cx + 3, b),
               (cx - 3, b), (cx - 4, b - 8)], PL, hi=PL_LT, sh=PL_SH)
    poly(im, [(cx - 3, t + 9), (cx + 3, t + 9), (cx + 3, t + 11), (cx - 3, t + 11)], PL_SH)
    plate(im, [(cx - 4, b - 1), (cx + 4, b - 1), (cx + 5, b + 3), (cx + 2, b + 7),
               (cx - 2, b + 7), (cx - 5, b + 3)], ST_LT, hi=PL_LT, sh=ST)
    poly(im, [(cx - 3, b + 2), (cx + 3, b + 2), (cx + 3, b + 4), (cx - 3, b + 4)], ST_DK)


def leg(im, x, y, back=False, push=False):
    """One leg: greave and sabaton as a SINGLE plate with an internal ankle seam.

    Drawing them as two plates gave every leg two keylines and pushed the sheet
    to 26.6% black against his sprite's 20.1% - small plated shapes are mostly
    outline. One silhouette per leg brings it back in range and reads cleaner at
    this size."""
    h = 16
    top = y - h
    if push:                                   # back foot rolling onto the toe
        pts = [(x + 2, top), (x + 12, top), (x + 13, top + 9), (x + 15, y - 3),
               (x + 15, y), (x + 3, y), (x + 1, y - 4)]
    elif back:
        pts = [(x + 2, top), (x + 12, top), (x + 12, top + 9), (x + 15, top + 12),
               (x + 15, y), (x, y), (x + 1, top + 10)]
    else:
        pts = [(x + 2, top), (x + 12, top), (x + 13, top + 9), (x + 16, top + 12),
               (x + 16, y), (x, y), (x + 1, top + 10)]
    plate(im, pts, PL, hi=PL_LT, sh=PL_SH)
    poly(im, [(x + 2, top + 9), (x + 13, top + 9), (x + 13, top + 11), (x + 2, top + 11)], PL_SH)
    poly(im, [(x + 1, y - 3), (x + 15, y - 3), (x + 15, y - 1), (x + 1, y - 1)], PL_MD)


def dust(im, x, y, level):
    """Impact puff at the planted foot - this is the frame the arena shakes on."""
    if not level:
        return
    spread = [(-9, -1, 3), (-4, -4, 2), (4, -5, 2), (10, -2, 3), (-14, 0, 2), (15, 1, 2)]
    for i, (dx, dy, r) in enumerate(spread[: 4 + level]):
        c = DUST[min(2, (i + 2 - level) % 3)]
        poly(im, [(x + dx - r, y + dy), (x + dx, y + dy - r), (x + dx + r, y + dy),
                  (x + dx, y + dy + r // 2)], c)


CROSS_BOX = (42, 36, 68, 62)   # the chest cross, restored after mirroring
BODY_CENTRE = 56            # his centreline inside the body part (the two pauldron crosses)
TASSET_BOTTOM_Y = 71        # last row of the skirt inside the body part
BODY_TOP = 111              # so the skirt ends at 182 and the sabatons stand on 191


def symmetric_body():
    """Square his shoulders by mirroring his own right side onto his left.

    The source frame has one arm raised in a bear-hug gesture. Cutting that arm
    out and re-placing a mirrored copy left the gauntlets floating off his
    pauldrons - the arm only connects at the exact pixels it was drawn at. So
    instead mirror the whole right half about his centreline: every joint stays
    attached because it is the same drawing, and square shoulders is what the
    brief asks for anyway."""
    body, _ = P.body()
    right = body.crop((BODY_CENTRE, 0, body.width, body.height))
    out = Image.new("RGBA", (BODY_CENTRE + right.width, body.height), (0, 0, 0, 0))
    out.alpha_composite(right.transpose(Image.FLIP_LEFT_RIGHT), (BODY_CENTRE - right.width, 0))
    out.alpha_composite(right, (BODY_CENTRE, 0))
    # His chest cross sits at x~53, not on the x=56 seam, so mirroring cuts its
    # left arm off and leaves a red bar. Put the original cross back over the top.
    out.alpha_composite(body.crop(CROSS_BOX), (CROSS_BOX[0], CROSS_BOX[1]))
    # swap the neutral bear-hug face for his angry idle face off the main sheet
    out.alpha_composite(P.angry_head(), P.HEAD_AT)
    strip_bearhug_arms(out)
    return out


CAPE_RGB = {tuple(int(c[k:k + 2], 16) for k in (1, 3, 5)) for c in (P.CP_HI, P.CP, P.CP_DK)}


def strip_bearhug_arms(im):
    """Remove the inherited arms, keep the pauldrons and the cape.

    The source frame is a man mid-grab, so its arms angle out and away with the
    gauntlets floating in the air. Mirroring only gave me two of them. They are
    cleared here by region-plus-colour - everything outside the torso columns
    below the pauldron line that is not cape - and redrawn hanging in draw_arm()."""
    px = im.load()
    for y in range(42, im.height):
        for x in list(range(0, 34)) + list(range(72, im.width)):
            r, g, b, a = px[x, y]
            if a > 0 and (r, g, b) not in CAPE_RGB:
                px[x, y] = (0, 0, 0, 0)


def compose(i, body):
    im = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
    bob, lead, step = BOB[i], LEAD[i], STEP[i]
    by = BODY_TOP + bob
    foot_y = FLOOR - 8
    front_x = CX - 7 + lead * step
    back_x = CX - 7 - lead * max(0, step - 3)

    # back leg first so the front one overlaps it
    leg(im, back_x, FLOOR, back=True, push=(i in (2, 6)))
    leg(im, front_x, FLOOR)

    ox, oy = CX - BODY_CENTRE, by
    im.alpha_composite(body, (ox, oy))
    # Arms go on AFTER the body: drawn behind it their inner keyline is hidden
    # and they merge into the tassets as two white columns.
    swing = [1, 2, 1, -1, 1, 2, 1, -1, 0][i]
    draw_arm(im, ox, oy, -1, swing * lead if lead else 0)
    draw_arm(im, ox, oy, 1, -swing * lead if lead else 0)
    dust(im, front_x + 7, FLOOR - 1, DUSTF[i])
    return im


def build():
    body = symmetric_body()
    return [compose(i, body) for i in range(9)]


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    frames = build()
    strip = Image.new("RGBA", (FW * len(frames), FH), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        strip.alpha_composite(f, (i * FW, 0))
    strip.save(os.path.join(out, "_walk_strip.png"))
    prev = Image.new("RGBA", (FW * len(frames), FH), (34, 32, 52, 255))
    prev.alpha_composite(strip)
    prev.resize((prev.width * 2, prev.height * 2), Image.NEAREST).convert("RGB").save(
        os.path.join(out, "_walk_preview.png"))
    print("frames:", len(frames))
