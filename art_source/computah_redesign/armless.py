"""Computah after the fight: armless on the mat, the arm being torn off, and the loose
arm Greyson carries between the tear and the fit.

APPROVED 2026-09-24 ("approve everything so far"): the armless pose and its sparking
loop, the two-frame wrench, and the loose arm in the WORN shape.  The loose arm was
then re-matched to Greyson's shipped greyson_fight_approval.png, whose cannon came
out thicker than the draft it was first matched to.

After Computah is beaten, Greyson walks over, tears the cannon arm off and wears it as
a gauntlet over his LEFT forearm (art_source/greyson_fight/gf_cannon.py).  Computah's
own fight is unchanged.

This module only BUILDS frames.  It writes nothing: armless_build.py renders, checks
and - only with --ship, and only if every check passes - writes the sheets.

  computah_armless   3 x 96x96   frame 0 is the pose; 0-1-2 is the sparking loop
  computah_wrench    2 x 96x96   0 the haul, 1 the tear; then computah_armless 0
  computah_arm_prop  5 x 56x56   torn, carry, lift, fit, hang
"""

import math
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "greyson_computah"))

import computah_mm as M                                           # noqa: E402
from pixlib import Canvas, Union                                  # noqa: E402

M._set_frame(96)
E, CAP, PX = M.E, M.CAP, M.PX
GLINT = "#FFF6C8"               # the spark cream the rig already uses - no new hue
ARC = "#8CD8FF"                 # the spark blue the rig already uses - no new hue


# ---------------------------------------------------------------------------
# the torn socket, oriented
# ---------------------------------------------------------------------------
def _torn_socket(c, sx, sy, fx, fy, r=8.0, prio=17):
    """A ripped mount facing along (fx, fy): what the arm was torn AWAY from.

    The rig's _stump always faces right, which was fine while the arm only ever left
    one way.  Here the same wound faces along his shoulder on the mat and backwards
    off the loose arm, so it takes a direction.  The dark hole sits toward the torn
    face and a ring of bent teeth frames it, so it reads as ripped, never unbolted."""
    px, py = -fy, fx
    body = E(sx, sy, r, r * 0.9)
    c.add(body, "armour", prio=prio, bias=2)
    c.contour(body, width=1.6, delta=3, mats=("shell", "armour"), below_prio=prio)
    hx, hy = sx + fx * r * 0.34, sy + fy * r * 0.34
    c.add(E(hx, hy, r * 0.64, r * 0.58), "dark", prio=prio + 1, flat=4)
    c.add(E(hx + fx * 0.8 - 0.5, hy + fy * 0.8 - 0.5, r * 0.34, r * 0.30),
          "dark", prio=prio + 1, flat=2)
    # Bent teeth round the rim of the hole, biased to the torn side.  ONE priority
    # above the socket, not three: at three the keyline pass inked a black ring round
    # every tooth, which read as rivets and pushed the frame's keyline a point over.
    # They separate by value (alternating light and dark) instead.
    for n in range(7):
        a = -1.9 + n * 0.63
        ca, sa = math.cos(a), math.sin(a)
        tx = hx + (fx * ca - px * sa) * r * 0.80
        ty = hy + (fy * ca - py * sa) * r * 0.80
        c.add(E(tx, ty, r * 0.21, r * 0.21), "armour", prio=prio + 1,
              bias=1 if n % 2 else 3)
    return (hx, hy)


# Cables out of the hole: (material, reach out along the face, droop, side offset,
# radius).  Three, not four - with four they covered the hole, and the dark hole is
# the part that says "torn out".
WIRES = (
    ("dark", 8.5, 8.0, -1.0, 0.95),
    ("armour", 6.0, 9.0, 1.4, 0.90),
    ("shell", 7.0, -3.0, -2.2, 0.80),     # the stiff one that sticks up and twitches
)


def _wires(c, hx, hy, fx, fy, phase=0, prio=21, scale=1.0, floor=None, lip=4.0,
           sag=False):
    """Draws the cables before the finish pass so they get the house keyline and
    shading, and returns their tips so the sparks can find them after it.

    They are rooted on the hole's LOWER, OUTER lip - spilling over the edge - not at
    its centre, so the opening stays dark and readable above them.  Gravity is always
    screen-down, so a cable off the loose arm falls the way one off his shoulder does;
    `sag` makes every cable droop, for the loose arm, where nothing holds one up."""
    px, py = -fy, fx
    rx0, ry0 = hx + fx * lip * 0.6, hy + abs(fx) * lip * 0.55 + fy * lip * 0.2
    tips = []
    for n, (mat, reach, droop, side, rad) in enumerate(WIRES):
        twitch = 1.5 if (n == 2 and phase % 2) else 0.0
        reach *= scale
        droop = (abs(droop) if sag else droop) * scale
        x0, y0 = rx0 + px * side * 0.6, ry0 + py * side * 0.6
        x1 = x0 + fx * reach * 0.55
        y1 = y0 + fy * reach * 0.55 + droop * 0.25 - twitch
        x2 = x0 + fx * reach + px * side * 0.4
        y2 = y0 + fy * reach + droop - twitch * 2.0
        if floor is not None:
            y1, y2 = min(y1, floor), min(y2, floor)
        c.add(Union([CAP((x0, y0), (x1, y1), rad, rad),
                     CAP((x1, y1), (x2, y2), rad, rad * 0.8)], k=0.6),
              mat, prio=prio + n, bias=1 if mat == "shell" else 0)
        tips.append((x2, y2))
    return tips


def _spark_tips(c, tips, phase):
    """Bare ends glint every frame; on alternate frames a different pair arcs."""
    for n, (x, y) in enumerate(tips):
        c.raw_px([PX(x, y)], GLINT)
        if (n + phase) % 2 == 0:
            X, Y = PX(x, y)
            c.raw_px([(X + 1, Y - 1), (X + 2, Y - 2), (X - 1, Y - 2)], ARC)


# ---------------------------------------------------------------------------
# computah_armless - the defeat frame without the arm, and its loop
# ---------------------------------------------------------------------------
# computah_defeat's LAST frame, exactly, with the cannon gone: same body, same head,
# same dead cells and eyes.  checks.py proves the body is byte-identical to that
# frame's own code path with the cannon stubbed out.  The smoke moves from above
# where the cannon lay to the wound itself, which is where it would come from.
SOCKET = (48.0, 84.0)                       # where the cannon joined, on the mat
FACE = (0.94, 0.34)                         # the way the arm went: out along the mat
WOUND_R = 8.2


def body_on_mat(c, cc, dy=0.0, eyes="dead"):
    """computah_mm._floor's body minus the cannon and minus _floor's own finish, so
    the wound and cables go in before the keyline pass instead of after it."""
    M._antenna(c, [(25, 60 + dy), (17, 57 + dy), (10, 59 + dy)],
               (7.0, 60.4 + dy, 4.0), cc)
    M._leg(c, (34.0, 86 + dy * 0.2), (24.0, 91), (18.0, 94),
           (8.0, 91.0, 26.0, 95.0), prio=4, far=True)
    M._leg(c, (40.0, 87 + dy * 0.2), (30.0, 92), (26.0, 94),
           (16.0, 91.5, 34.0, 95.0), prio=6)
    c.add(M.RR(27.0, 76 + dy, 35.0, 83 + dy * 0.6, r=3.0, round_r=4.0), "shell",
          prio=2)
    M._torso(c, [(22.0, 80 + dy), (46.0, 77 + dy), (54.0, 93), (20.0, 94)],
             (22.5, 77.5 + dy, 47.0, 82.0 + dy), pelvis=(22.0, 87.0, 54.0, 95.0))
    M._arm(c, (25.0, 84 + dy * 0.6), (18.0, 90), (13.0, 94), hand_r=5.2,
           r0=5.8, r1=4.9, r2=4.2, prio=9, cap=(24.8, 82.5 + dy * 0.6, 7.4, 6.8),
           gauntlet=True)
    M._capacitor(c, 32.5, 85 + dy * 0.3, cc, cell_w=3, gap=3, bh=5.4, prio=24)
    M._helmet(c, 26.0, 66.0 + dy, rx=16.5, ry=11.5, jaw=(9.0, 3.0, 13.0),
              chin=71.5 + dy, pods=(5.8, 3.0), pod_y=4.4, vent=1)
    M._face(c, M.FACE_LOCK, 16.0, 59.5 + dy, cc, mood=eyes)


def wound_centre():
    """The centre of the dark hole on computah_armless, in 96-frame texels."""
    return (SOCKET[0] + FACE[0] * WOUND_R * 0.34, SOCKET[1] + FACE[1] * WOUND_R * 0.34)


def build_armless(k=0):
    """0 is THE pose.  0-1-2 loop: the wound arcs between cable ends, the stiff cable
    twitches, the smoke cycles."""
    c = Canvas(M.FRAME, M.FRAME, M.PAL, M.OUTLINE)
    body_on_mat(c, M.CHARGE["dead"])
    hx, hy = _torn_socket(c, SOCKET[0], SOCKET[1], FACE[0], FACE[1], r=WOUND_R,
                          prio=17)
    tips = _wires(c, hx, hy, FACE[0], FACE[1], phase=k, prio=26, floor=94.0)
    M._finish(c)
    _spark_tips(c, tips, k)
    arcs = ((3, -6), (6, -4), (5, -9), (8, -7))[k % 2::2]
    M._sparks(c, hx, hy, arcs + (((-2, -7),) if k == 2 else ()))
    M._steam(c, hx + 1, hy - 5, phase=k % 2)
    return c


# ---------------------------------------------------------------------------
# computah_wrench - two frames of the arm being pulled off him
# ---------------------------------------------------------------------------
# Greyson stands to his right, where the cannon lies, and hauls it up and back toward
# himself.  0: the pull - body dragged up off the mat after the arm, head lolling
# behind, the shoulder seam splitting.  1: the tear - the arm is GONE from this
# sprite (it is the loose prop in Greyson's hand from here), the body dropping back,
# the wound spraying.  Then computah_armless 0.  If Greyson comes from his left
# instead, flip_h both frames.
#
# The haul's cannon has the SAME LENGTH (30) AND ANGLE (-25.2 deg) as the prop's
# "torn" frame, so on the tear the loose arm replaces it exactly (checks.py measures
# it).  The first cut had it 37.6 long, and the arm visibly shrank on the tear.
WRENCH_GUN = ((49.0, 75.0), (76.2, 62.2))
TEAR_FACE = (0.9, -0.43)
WRENCH_LIFT = (-9.0, -4.0)                 # how far his chest is dragged up
WRENCH_LEAN = (3.0, 1.0)                   # and toward the pull


def wrench_socket(k):
    return (SOCKET[0] + WRENCH_LEAN[k], SOCKET[1] + WRENCH_LIFT[k])


def build_wrench(k=0):
    c = Canvas(M.FRAME, M.FRAME, M.PAL, M.OUTLINE)
    cc = M.CHARGE["dead"]
    lift, lean = WRENCH_LIFT[k], WRENCH_LEAN[k]
    M._antenna(c, [(24 + lean, 58 + lift), (16 + lean, 58 + lift * 0.6),
                   (9 + lean, 62 + lift * 0.3)],
               (6.0 + lean, 64.0 + lift * 0.3, 4.0), cc)
    M._leg(c, (35.0 + lean * 0.4, 86 + lift * 0.3), (25.0, 91), (18.0, 94),
           (8.0, 91.0, 26.0, 95.0), prio=4, far=True)
    M._leg(c, (41.0 + lean * 0.4, 87 + lift * 0.3), (31.0, 92), (26.0, 94),
           (16.0, 91.5, 34.0, 95.0), prio=6)
    c.add(M.RR(28.0 + lean, 76 + lift, 36.0 + lean, 83 + lift * 0.6, r=3.0,
               round_r=4.0), "shell", prio=2)
    M._torso(c, [(23.0 + lean, 80 + lift), (48.0 + lean * 1.4, 76 + lift * 1.1),
                 (55.0, 93), (21.0, 94)],
             (23.5 + lean, 77.5 + lift, 49.0 + lean * 1.4, 82.0 + lift),
             pelvis=(22.0, 87.0, 55.0, 95.0))
    M._arm(c, (26.0 + lean, 84 + lift * 0.6), (19.0, 90), (13.0, 94),
           hand_r=5.2, r0=5.8, r1=4.9, r2=4.2, prio=9,
           cap=(25.8 + lean, 82.5 + lift * 0.6, 7.4, 6.8), gauntlet=True)
    M._capacitor(c, 33.5 + lean, 85 + lift * 0.5, cc, cell_w=3, gap=3, bh=5.4,
                 prio=24)
    M._helmet(c, 24.0 + lean * 0.3, 66.0 + lift * 0.8, rx=16.5, ry=11.5,
              jaw=(9.0, 3.0, 13.0), chin=71.5 + lift * 0.8, pods=(5.8, 3.0),
              pod_y=4.4, vent=1)
    M._face(c, M.FACE_LOCK, 14.0 + lean * 0.3, 59.5 + lift * 0.8, cc, mood="dead")

    sx, sy = wrench_socket(k)
    fx, fy = TEAR_FACE
    if k == 0:
        sh, mz = WRENCH_GUN
        M._cannon(c, sh, mz, r=7.8, prio=16)
        hx, hy = _torn_socket(c, sx, sy, fx, fy, r=7.0, prio=14)
        tips = _wires(c, hx, hy, fx, fy, phase=0, prio=26, scale=0.55)
        M._finish(c)
        M._sparks(c, hx + 3, hy - 2, ((0, -5), (4, -3), (-2, -8), (5, -7)))
        _spark_tips(c, tips, 0)
        return c
    hx, hy = _torn_socket(c, sx, sy, fx, fy, r=7.6, prio=17)
    tips = _wires(c, hx, hy, fx, fy, phase=1, prio=26, scale=1.15)
    M._finish(c)
    burst = [(math.cos(a) * d, math.sin(a) * d)
             for a in [i * 0.52 - 1.9 for i in range(8)] for d in (7.0, 11.5)]
    M._sparks(c, hx + fx * 2, hy + fy * 2, burst)
    _spark_tips(c, tips, 1)
    return c


# ---------------------------------------------------------------------------
# computah_arm_prop - the loose arm
# ---------------------------------------------------------------------------
# 56x56.  Generated along its own axis for every orientation, never rotated, so each
# is lit from the cast's upper-left (rotating the picture would rotate its shading).
#
# THE SHAPE IS HOW IT IS WORN, per art_source/greyson_fight/gf_cannon.py: the torn
# shoulder BALL cut flat at the socket, its equator a quarter of the way along, a step
# down onto a barrel that swells slightly, then the muzzle ring.  The barrel has to be
# straight because Greyson's forearm is inside it.  On Computah the cannon IS the arm,
# so there it keeps its pinched waist; the one change of shape falls between the haul
# frame and this prop's first frame, inside the tear's spark burst.
#
# PROFILE_WORN is sampled from gf_cannon._profile at its shipped defaults (r_col 8.0,
# r_bar 6.3, r_muz 7.6, L 30).  It is frozen here so the shipped prop rebuilds from
# this folder alone; checks.py re-samples the live profile and fails if they drift.
PROP = 56
PROP_R = 8.0
PROP_LEN = 30.0
PROFILE_WORN = ((0.000, 0.787), (0.050, 0.787), (0.100, 0.835), (0.150, 0.932),
                (0.200, 0.985), (0.247, 1.000), (0.300, 0.980), (0.310, 0.790),
                (0.550, 0.850), (0.790, 0.790), (0.800, 0.950), (0.960, 0.950),
                (0.970, 0.912), (1.000, 0.912))
# (The muzzle ring narrows to r_muz - 0.3 for its last texel, from a = L - 1.  The
# first freeze of this table read 0.950 at t 0.97 - past that lip - and the worn-match
# proof in armless_build.py caught it on its first run.)
PROP_POSES = (
    # name, barrel angle in degrees (0 = muzzle right, -90 = muzzle up)
    ("torn", -25.2),     # the angle it leaves his shoulder at in build_wrench(0)
    ("carry", 0.0),      # held level in Greyson's other hand
    ("lift", -55.0),     # swung up
    ("fit", -90.0),      # socket down, muzzle up: as worn in pose B and the raise
    ("hang", 90.0),      # socket up, muzzle down: as worn in his idle
)
# GRIP IS (28, 25) ON EVERY FRAME.  Greyson's tear sheet is drawn to that point, so it
# must not move; checks.py fails if it does.
GRIP = (28.0, 25.0)
SOCKET_K = 0.82          # the torn face's radius: his FLAT socket cut is floored at
                         # r_bar (0.79 of r_col), not the ball's full equator
SOCKET_IN = 1.5          # how far the torn face sits into the ball


def prop_rig(name):
    ang = dict(PROP_POSES)[name]
    ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    sh = (GRIP[0] - ux * PROP_LEN * 0.5, GRIP[1] - uy * PROP_LEN * 0.5)
    mz = (GRIP[0] + ux * PROP_LEN * 0.5, GRIP[1] + uy * PROP_LEN * 0.5)
    return sh, mz, (ux, uy)


def _socket_centre(sh, u):
    return (sh[0] + u[0] * SOCKET_IN, sh[1] + u[1] * SOCKET_IN)


def _hole(sh, u):
    """The centre of the dark hole: where his forearm goes in."""
    cx, cy = _socket_centre(sh, u)
    r = PROP_R * SOCKET_K
    return (cx - u[0] * r * 0.34, cy - u[1] * r * 0.34)


def build_prop(k=0, profile=PROFILE_WORN, phase=0):
    """The worn shape by default.  Pass profile=M.PROFILE only to compare against
    Computah's own profile - that version was shown, and not the one approved."""
    name = PROP_POSES[k][0]
    sh, mz, (ux, uy) = prop_rig(name)
    c = Canvas(PROP, PROP, M.PAL, M.OUTLINE)
    keep = M.PROFILE
    try:
        M.PROFILE = profile
        M._cannon(c, sh, mz, r=PROP_R, prio=16)
    finally:
        M.PROFILE = keep
    # The torn end faces back, away from the barrel, the width of his flat socket
    # cut and seated 1.5 texels into the ball - which also keeps the socket-up and
    # socket-down frames inside 56 px with the grip held on (28, 25).
    cx, cy = _socket_centre(sh, (ux, uy))
    hx, hy = _torn_socket(c, cx, cy, -ux, -uy, r=PROP_R * SOCKET_K, prio=24)
    tips = _wires(c, hx, hy, -ux, -uy, phase=phase, prio=30, scale=0.55, sag=True)
    M._finish(c)
    _spark_tips(c, tips, phase)
    return c


def prop_points():
    """socket (the torn end, where his forearm goes in), grip (mid-barrel, where his
    other hand carries it) and muzzle (the bore), in 56-frame texels."""
    out = {}
    for name, _a in PROP_POSES:
        sh, mz, (ux, uy) = prop_rig(name)
        hole = _hole(sh, (ux, uy))
        out[name] = {
            "socket": (round(hole[0], 1), round(hole[1], 1)),
            "grip": (round((sh[0] + mz[0]) / 2, 1), round((sh[1] + mz[1]) / 2, 1)),
            "muzzle": (round(mz[0] + ux * 0.6, 1), round(mz[1] + uy * 0.6, 1)),
        }
    return out


def handoff_offset():
    """Where to draw the prop's "torn" frame on the tear, in texels from Computah's
    96-frame origin: it puts the loose arm exactly where the hauled arm was."""
    sh, _mz, _u = prop_rig("torn")
    return (round(WRENCH_GUN[0][0] - sh[0], 1), round(WRENCH_GUN[0][1] - sh[1], 1))


# ---------------------------------------------------------------------------
def strip(images):
    from PIL import Image
    w = sum(i.width for i in images)
    sheet = Image.new("RGBA", (w, max(i.height for i in images)), (0, 0, 0, 0))
    x = 0
    for im in images:
        sheet.paste(im, (x, 0))
        x += im.width
    return sheet


SHEETS = {
    # name: (build, frames, frame size)
    "computah_armless": (build_armless, 3, M.FRAME),
    "computah_wrench": (build_wrench, 2, M.FRAME),
    "computah_arm_prop": (build_prop, len(PROP_POSES), PROP),
}


def render(name):
    fn, n, _size = SHEETS[name]
    return strip([fn(k).to_image() for k in range(n)])
