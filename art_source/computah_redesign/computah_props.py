"""Computah's props: things that are not his body and so are not 96x96.

Each prop states its own frame size and its own anchor, because they are placed by
different rules - the mine sits on the floor, the thrown arm tumbles through the air,
the picked-up cannon is drawn over the player's hands.

  python computah_props.py <outdir>
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "greyson_computah"))
from pixlib import Canvas, Ellipse, Capsule, Poly, RoundRect, Union, Clip  # noqa: E402
import computah_mm as C                                            # noqa: E402

OUTLINE = C.OUTLINE

PAL = dict(C.PAL)
# Electric cyan, and ONLY cyan.  Red means "parry this" and yellow means "dodge
# this"; a closed mine has no answer to either, so it must never borrow those two.
PAL["spark"] = ["#DCF6FF", "#8CD8FF", "#45A8D8", "#24688F", "#163F5C"]

# ---------------------------------------------------------------------------
# THE MINE
# ---------------------------------------------------------------------------
# 32x32, FLOOR POINT AT (16, 31) - the bottom-centre of the warning ring, not the
# middle of the body, because the ring is what the player is reading and what the
# trigger is measured from.
MINE_FRAME = 32
MINE_ANCHOR = (16, 31)

# THE DRAWN RING IS THE TRIGGER AREA.  Exactly 24 wide by 12 tall, sitting on the
# floor point, and nothing cyan is ever allowed outside it: a player standing just
# beyond the ring they can see must never be caught by it.  checks.py measures this
# on every frame and fails the build if it drifts by one texel.
RING_W, RING_H = 24, 12
RING_X0 = MINE_ANCHOR[0] - RING_W // 2                  # 4
RING_Y0 = MINE_ANCHOR[1] - RING_H + 1                   # 20
RING_BOX = (RING_X0, RING_Y0, RING_X0 + RING_W - 1, RING_Y0 + RING_H - 1)


def _r(v):
    return int(math.floor(v + 0.5))


def _ring(c, level, dash=0):
    """The warning ring, traced parametrically so the extremes land on exact integers
    and the bounding box is the trigger box to the texel.

    The FAR half only draws onto empty pixels, so the body stands in the ring instead
    of being painted over by it; the NEAR half always draws, because it is in front.
    Without that the ring reads as a decal on top of the mine rather than a circle on
    the floor around it."""
    cx = RING_X0 + RING_W / 2.0
    cy = RING_Y0 + RING_H / 2.0
    rx = RING_W / 2.0 - 0.5
    ry = RING_H / 2.0 - 0.5
    col = PAL["spark"][level]
    n = 120
    for i in range(n):
        t = 2.0 * math.pi * i / n
        if dash and (i // dash) % 2:
            continue
        x = _r(cx + rx * math.cos(t) - 0.5)
        y = _r(cy + ry * math.sin(t) - 0.5)
        if not (0 <= x < c.w and 0 <= y < c.h):
            continue
        near = y + 0.5 >= cy
        if near or (c.mat[y][x] is None and c.raw[y][x] is None):
            c.raw_px([(x, y)], col)
            # the near arc gets a second row of shadow inside it so the ring sits on
            # the floor instead of floating - inside only, so the box cannot grow
            if near and y - 1 >= RING_Y0 and c.mat[y - 1][x] is None:
                c.raw_px([(x, y - 1)], PAL["spark"][min(level + 2, 4)])


# leg spread per frame: how far the three anchor spikes have unfolded
MINE_LEGS = (0.0, 0.55, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0)


def _mine_body(c, k, lens, squat=0.0):
    """A small purple puck on three spikes with a cyan lens - his hardware, so it
    wears his armour colour and his chassis grey.  It is deliberately much smaller
    than the ring: the ring is the thing being read, and a body that fills it hides
    the one piece of information the player needs."""
    spread = MINE_LEGS[k]
    base = 25.5 + squat
    for sx, out, drop in ((-1, 8.0, 4.4), (1, 8.0, 4.4), (0, 0.0, 5.4)):
        ex = 16.0 + sx * out * spread
        ey = base + drop * spread
        c.add(Capsule((16.0, base - 1.5), (ex, ey), 1.7, 1.1), "shell", prio=3,
              bias=2)
    body = Union([Ellipse(16.0, base - 3.4 + squat * 0.4, 5.8, 3.6 - squat * 0.5),
                  RoundRect(10.6, base - 3.6, 21.4, base - 0.6, r=1.6,
                            round_r=2.4)], k=1.2)
    c.add(body, "armour", prio=6, bias=2)
    c.add(Clip(Ellipse(16.0, base - 4.4 + squat * 0.4, 4.2, 2.4),
               Poly([(0, -20), (40, -20), (40, base - 3.2), (0, base - 3.2)])),
          "shell", prio=7, bias=1)
    # the lens sits low enough to stay inside the ring box: NO cyan is allowed
    # outside it on any frame, so the box a player sees is the only cyan there is
    c.add(Ellipse(16.0, base - 4.0 + squat * 0.4, 2.2, 1.5), "spark", prio=9,
          flat=lens)


def _jaws(c):
    """The clamp.  It only ever appears already SHUT, on the two sprung frames,
    under whoever it caught - open jaws would read as a second warning, and by then
    the warning is over."""
    for sx in (-1, 1):
        c.add(Union([Capsule((16.0 + sx * 7.6, 26.0), (16.0 + sx * 7.0, 20.0),
                             3.1, 2.7),
                     Capsule((16.0 + sx * 7.0, 20.0), (16.0 + sx * 2.2, 15.0),
                             2.7, 2.2)], k=1.2), "armour", prio=8, bias=1)
    c.add(Capsule((13.4, 14.6), (18.6, 14.6), 2.0, 2.0), "shell", prio=9, bias=1)
    c.add(Ellipse(16.0, 25.0, 6.8, 3.0), "armour", prio=10, bias=3)


def build_mine(k=0):
    """0-2 arming, 3-4 armed (a slow two-frame pulse one ramp step apart, so it can
    never be mistaken for a tell's flicker), 5-6 expiring, 7-8 sprung."""
    c = Canvas(MINE_FRAME, MINE_FRAME, PAL, OUTLINE)
    if k == 0:                       # just landed, still folded
        _mine_body(c, k, lens=3, squat=1.2)
        C._finish(c, gap=2)
        for dx in (-9, -6, 6, 9):
            c.raw_px([(16 + dx, 30), (16 + dx, 29)], "#8091A8")
        return c
    if k <= 2:                       # legs coming out, ring opening dim
        _mine_body(c, k, lens=2 if k == 2 else 3)
        C._finish(c, gap=2)
        _ring(c, 3 if k == 1 else 2)
        return c
    if k <= 4:                       # ARMED.  one step of pulse, no more
        _mine_body(c, k, lens=0 if k == 4 else 1)
        C._finish(c, gap=2)
        _ring(c, 1 if k == 4 else 2)
        return c
    if k <= 6:                       # expiring: the ring breaks up and fades
        _mine_body(c, k, lens=2 if k == 5 else 3)
        C._finish(c, gap=2)
        _ring(c, 2 if k == 5 else 3, dash=4 if k == 5 else 2)
        return c
    _mine_body(c, k, lens=0, squat=1.6)   # sprung: jaws shut, arcs crackling
    _jaws(c)
    C._finish(c, gap=2)
    # the crackle stays inside the ring box too - same rule, no exceptions
    arcs = (((-9, 27), (-7, 24), (-10, 22)), ((9, 27), (7, 24), (10, 22)),
            ((-4, 21), (0, 20), (4, 21)))
    for n, arc in enumerate(arcs):
        if k == 8 and n == 1:
            arc = tuple((x + 1, y - 1) for x, y in arc)
        for i, (dx, dy) in enumerate(arc):
            c.raw_px([(16 + dx, dy)], PAL["spark"][0 if i % 2 else 1])
    return c


# ---------------------------------------------------------------------------
# THE DETACHED CANNON ARM, as a world object
# ---------------------------------------------------------------------------
# 48x48.  Frames 0-3 are the TUMBLE (one turn of the arm through the air, so it can
# be looped at any speed) and 4-5 are the PLANT, where it has landed and is lying on
# the mat waiting to be picked up.  The torn socket is always the trailing end, so
# the thing reads as ripped off him and not as a dropped weapon.
ARM_FRAME = 48
ARM_TUMBLE = (
    ((14, 24), (39, 24)),         # flat, muzzle leading
    ((14, 15), (35, 34)),         # over the nose
    ((24, 12), (24, 37)),         # muzzle straight down
    ((35, 15), (14, 34)),         # coming back round
)
ARM_PLANT = (
    ((14, 33), (38, 31)),         # the bounce
    ((14, 36), (38, 35)),         # settled
)
ARM_R = 6.6
# The row the planted arm rests on, so it can be laid on the floor line instead of
# floated. Measured, not guessed - see arm_points().
ARM_MAT_ROW = 45


def build_arm(k=0):
    sh, mz = (ARM_TUMBLE + ARM_PLANT)[k]
    c = Canvas(ARM_FRAME, ARM_FRAME, PAL, OUTLINE)
    C._cannon(c, sh, mz, r=ARM_R, prio=6)
    C._stump(c, sh[0], sh[1], spray=0.5 if k < 4 else 0.0)
    C._finish(c, gap=2)
    if k >= 4:                                  # a dead glow left in the bore
        ax, ay = C._unit(sh, mz)
        c.raw_px([(int(round(mz[0] + ax * 1.5)), int(round(mz[1] + ay * 1.5)))],
                 C.BEAM_DK)
    return c


def arm_points():
    """grip / muzzle / mat_row, in ARM_FRAME texels."""
    out = {}
    for i, (sh, mz) in enumerate(ARM_TUMBLE + ARM_PLANT):
        ax, ay = C._unit(sh, mz)
        out["tumble%d" % i if i < 4 else "plant%d" % (i - 4)] = {
            "grip": (round(sh[0], 1), round(sh[1], 1)),
            "muzzle": (round(mz[0] + ax * 0.6, 1), round(mz[1] + ay * 0.6, 1)),
        }
    return out


# ---------------------------------------------------------------------------
# THE HELD CANNON - drawn OVER the player's hands once he picks it up
# ---------------------------------------------------------------------------
# 56x32, and drawn at the PLAYER's texel scale, not Computah's.  The player's frame
# is 32x32 with his body origin at the middle of it (his Sprite2D sits on the body
# node with no offset) and CharacterBody2D scale 2; Computah is 96x96 at SCALE 3.
# So one Computah texel is 3/2 of a player texel, and the barrel that measured r 8.2
# and ~31 long on him becomes r ~12 and ~46 long here.  It is longer than the player
# is tall, which is the point.
HELD_FRAME = (64, 40)
HELD_GRIP = (14.0, 21.0)
HELD_MUZZLE = (49.0, 20.0)
HELD_R = 9.6
# Where HELD_GRIP sits relative to the PLAYER'S BODY ORIGIN, in player texels.  Taken
# from the player's body origin and not from anything of Computah's, so nothing I do
# to him can ever move the player's hands.
HELD_PLAYER_GRIP = (2.0, -2.0)

HELD_SET = (
    # (name, body shift along the barrel, bore glow, muzzle blast)
    ("hold", 0.0, 0, 0.0),
    ("charge0", 0.0, 1, 0.0),
    ("charge1", -0.5, 2, 2.5),
    ("charge2", -1.0, 3, 5.0),
    ("fire0", -1.5, 3, 6.5),
    ("fire1", -2.0, 2, 4.0),
    ("fire2", -0.5, 1, 2.0),
)


def build_held(k=0):
    _name, shift, glow, blast = HELD_SET[k]
    w, h = HELD_FRAME
    c = Canvas(w, h, PAL, OUTLINE)
    sh = (HELD_GRIP[0] + shift, HELD_GRIP[1])
    mz = (HELD_MUZZLE[0] + shift, HELD_MUZZLE[1])
    C._cannon(c, sh, mz, r=HELD_R, prio=6)
    C._stump(c, sh[0] - 0.5, sh[1], spray=0.0)
    C._finish(c, gap=2)
    ax, ay = C._unit(sh, mz)
    if glow:
        for t in range(glow * 2):
            c.raw_px([(int(round(mz[0] + ax * (1.0 + t * 0.6))),
                       int(round(mz[1] + ay * (1.0 + t * 0.6))))],
                     (C.BEAM_DK, C.BEAM_MID, C.BEAM_HI, C.BEAM_CORE)[glow])
    if blast:
        C._muzzle_blast(c, (mz[0] + ax * 0.6, mz[1] + ay * 0.6), blast,
                        back=(ax, ay), hot=blast > 4)
    return c


PROPS = {
    "computah_mine": (build_mine, 9, MINE_FRAME),
    "computah_arm": (build_arm, 6, ARM_FRAME),
    "computah_held_cannon": (build_held, 7, HELD_FRAME),
}


def strip(fn, n, frame):
    from PIL import Image
    w, h = frame if isinstance(frame, tuple) else (frame, frame)
    sheet = Image.new("RGBA", (w * n, h), (0, 0, 0, 0))
    for i in range(n):
        sheet.paste(fn(i).to_image(), (i * w, 0))
    return sheet


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else HERE
    C._set_frame(96)
    prev = os.path.join(out, "preview")
    if not os.path.isdir(prev):
        os.makedirs(prev)
    for name, (fn, n, frame) in PROPS.items():
        sheet = strip(fn, n, frame)
        sheet.save(os.path.join(out, "%s.png" % name))
        sheet.resize((sheet.width * 5, sheet.height * 5)).save(
            os.path.join(prev, "%s_5x.png" % name))
        print("%-24s %2d frames  %dx%d  frame %s"
              % (name, n, sheet.width, sheet.height, frame))
    print("mine   anchor (floor point) %s, ring box %s = %dx%d"
          % (MINE_ANCHOR, RING_BOX, RING_W, RING_H))
    for k, v in arm_points().items():
        print("arm    %-9s grip %-12s muzzle %s" % (k, v["grip"], v["muzzle"]))
    print("arm    mat_row %d (the planted frames' lowest drawn row)" % ARM_MAT_ROW)
    print("held   frame %s  grip %s  muzzle %s" % (HELD_FRAME, HELD_GRIP,
                                                   HELD_MUZZLE))
    print("held   player_grip %s, in PLAYER texels from his body origin"
          % (HELD_PLAYER_GRIP,))
    print("ok")
