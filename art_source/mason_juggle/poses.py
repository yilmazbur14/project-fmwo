"""Mason's juggle key poses.

The read we are after is WEIGHT.  Eric is a knight: the uppercut pops him and he
cartwheels at a steady spin.  Mason is a very heavy man in a chicken suit, so
every beat is the opposite of that:

  launch  the gut DENTS round the fist and he has barely left the mat.  Knees
          dangling, wings thrown out and DOWN -- heavy arms cannot fly up.  A
          light body pops; a heavy one deforms first and leaves late.
  hang    (extra, not in Eric's set)  the apex, where a heavy mass visibly
          stalls.  Tipped back, belly coming up, the low wing hanging PLUMB
          under gravity while the high one flops back past his head.  This is
          the beat Eric does not have and the one that sells the mass.
  tumble  horizontal, belly up, TURNING OVER rather than spinning -- both wings
          trailing the turn instead of pinwheeling with it.
  crash   back-first, and the body pancakes against the mat: squashed, spread,
          wings slapped out flat, dust thrown sideways rather than up.
  down    settled, belly a dome, soles up, head lolled, nothing left.

Head, torso, legs and chicken feet all come from the approved rig
(art_source/mason/rig.py) rendered in Mason's own frame and then PLACED into the
128x96 juggle frame under a rotation and a mat-squash.  Two things are done in
the juggle frame instead:

  * the cream volumes are re-lit (jlib.relight), because rotating a sprite
    rotates its shading with it and the cast's key light does not move; and
  * the wings are drawn where they point in the FRAME, so "hanging straight
    down" means straight down on screen however he is lying.
"""
import math

import jlib as J
import rig
from frames import sole_foot
from jlib import CREAM_HI

# Mason's centre of mass in his own 64x64 frame: the middle of the BELLY, not the
# middle of the silhouette.  His torso is rows 31-52 and its centroid is row 42;
# the whole silhouette's centroid is row 35.  We pivot on the gut, because that
# is the whole design -- a big low mass with a light hood and tiny feet -- and it
# is why he flops instead of cartwheeling.
COM = (31.5, 42.0)

# The rig is rendered onto a canvas with a margin, because raster()'s flood fill
# leaks the moment the silhouette touches an edge.  Poses stay written in Mason's
# own 64x64 coordinates and `at` moves them onto it.
SHIFT = (12, 10)

# Wing roots on the body's sides, from the rig's own posed wings.
ARM_R = (49, 42)
ARM_L = (14, 42)
BASE = dict(wing_r_mode='off', wing_l_mode='off', sym=False)


def at(p):
    return (p[0] + SHIFT[0], p[1] + SHIFT[1])


class Placed:
    """A posed Mason sitting in the juggle frame, and the transform that put him
    there, so wings and props can be aimed in frame space."""

    def __init__(self, g, M, pdst, ctx):
        self.g, self.M, self.pdst, self.ctx = g, M, pdst, ctx

    def root(self, local_point):
        """Where a point of Mason's own frame ends up in the juggle frame.  It goes
        through the rig's body transform first, so a shoulder on a squashed body is
        the shoulder that body actually has -- not the one the neutral pose had."""
        return J.frame_point(self.M, at(COM), self.pdst,
                             rig.tb(self.ctx, local_point))

    def wing(self, local_root, deg, reach=10):
        """One chicken wing, its ball sitting `reach` px from the shoulder along
        FRAME bearing `deg` (0 right, 90 down).  Aimed in the frame because a limp
        arm hangs the way gravity points, not the way the body happens to lie."""
        rx, ry = self.root(local_root)
        a = math.radians(deg)
        return J.wing_arm(self.g, (rx, ry),
                          (rx + math.cos(a) * reach, ry + math.sin(a) * reach),
                          flip=local_root[0] < 32)


def build(pose, angle, pdst, post_sx=1.0, post_sy=1.0):
    p = dict(pose)
    bd = p.get('body', (0, 0, 1.0, 1.0))
    p['body'] = (bd[0] + SHIFT[0], bd[1] + SHIFT[1], bd[2], bd[3])
    for k in ('foot_r', 'foot_l'):
        f = p.get(k, (0, 0))
        p[k] = (f[0] + SHIFT[0], f[1] + SHIFT[1])
    g = J.blank()
    M = J.matrix(angle, post_sx=post_sx, post_sy=post_sy)
    ctx = rig.make_ctx(p)
    umap = J.place(g, J.render_local(p), M, at(COM), pdst)
    J.relight(g, umap, ctx, angle)
    J.ticks(g, M, at(COM), pdst, ctx)
    return Placed(g, M, pdst, ctx)


def soles(*specs):
    """sole_foot pieces, written in Mason's own coordinates."""
    return [sole_foot(at(h), [at(t) for t in toes]) for (h, toes) in specs]


# ---------------------------------------------------------------- launch -----
# Dead upright, so the placement is an exact whole-pixel copy and this frame is
# the rig's own art untouched.  A few degrees of lean read as nothing at 3x and
# shear his chicken toes into a staircase; the squash, the splayed legs and the
# burst carry the pose on their own.
LAUNCH_ANGLE, LAUNCH_AT = 0, (64, 60)


def launch():
    """The uppercut lands.  The gut dents round the fist, his knees are already
    dangling, and the dust is still down where he was standing."""
    p = build(dict(BASE,
                   body=(0, 0, 1.18, 0.84), head=(0, 4),
                   face='strain', googly='knocked',
                   foot_r=(6, -1), foot_l=(-7, -1)),
              LAUNCH_ANGLE, LAUNCH_AT)
    g = p.g
    # Wings thrown out sideways and a little DOWN.  Eric's go up in a V.
    p.wing(ARM_L, 209, 10)
    p.wing(ARM_R, -29, 10)
    J.finish(g)

    # The contact: burst straight out of the gut, and the mat he has just left.
    J.lines(g, [[(64, 50), (64, 42)], [(55, 52), (50, 44)], [(73, 51), (78, 43)],
                [(45, 58), (36, 54)], [(84, 57), (93, 53)],
                [(30, 68), (21, 65)], [(99, 67), (108, 64)],
                [(47, 77), (40, 84)], [(82, 76), (89, 83)]])
    J.puff(g, 40, 92, 4)
    J.puff(g, 88, 93, 4)
    J.puff(g, 27, 94, 3)
    J.puff(g, 101, 94, 3)
    J.speck(g, [(17, 91), (111, 92), (33, 87), (96, 88), (11, 95), (116, 95)])
    return g


# ------------------------------------------------------------------ hang -----
HANG_ANGLE, HANG_AT = 54, (60, 47)


def hang():
    """Apex.  A heavy body stalls here.  The low wing hangs plumb under gravity
    while the high one flops back past his head, and he has barely turned."""
    p = build(dict(BASE,
                   body=(0, 0, 0.97, 1.05), head=(0, 0),
                   face='dizzy', googly='wall',
                   foot_r=(4, 0), foot_l=(-4, -1)),
              HANG_ANGLE, HANG_AT)
    g = p.g
    p.wing(ARM_L, 248, 12)    # thrown up and back past his head
    p.wing(ARM_R, 90, 12)     # hanging plumb, straight down the screen
    J.finish(g)

    # Barely a streak: he is hardly turning.  Motes drifting UP past him say he is
    # at the top of the arc rather than pinned to the air.
    J.arc(g, 68, 47, 40, -160, -118, ry=34)
    # Kept below his own top row, so the finisher's headroom is set by HIM and not
    # by a decorative mote drifting two pixels higher.
    J.speck(g, [(22, 26), (25, 33), (101, 22), (97, 28), (16, 54), (110, 42),
                (30, 18), (90, 17)], CREAM_HI)
    return g


# ---------------------------------------------------------------- tumble -----
TUMBLE_ANGLE, TUMBLE_AT = 102, (57, 50)


def tumble():
    """Horizontal, belly up, turning over.  Both wings trail the turn -- a heavy
    body drags its limbs behind it instead of pinwheeling them."""
    p = build(dict(BASE,
                   body=(0, 0, 1.0, 1.03), head=(0, 0),
                   face='dizzy', googly='crossed',
                   foot_r=(5, 0), foot_l=(-6, -1)),
              TUMBLE_ANGLE, TUMBLE_AT)
    g = p.g
    p.wing(ARM_L, 286)        # the high wing, dragged up behind the turn
    p.wing(ARM_R, 106)        # the low wing, dragged down behind the turn
    J.finish(g)

    J.arc(g, 63, 49, 47, 114, 208, ry=41)
    J.arc(g, 63, 49, 41, -64, -22, ry=36)
    J.speck(g, [(13, 20), (18, 15), (106, 80), (100, 85), (9, 32), (112, 68)], CREAM_HI)
    return g


# ----------------------------------------------------------------- crash -----
CRASH_ANGLE, CRASH_AT = 96, (55, 70)


def crash():
    """Back-first into the mat, and the whole body pancakes.  Dust goes sideways,
    not up -- the weight is spreading along the canvas."""
    p = build(dict(BASE, feet_detached=True,
                   body=(0, 0, 1.0, 1.06), head=(0, 0),
                   face='pain', googly='knocked',
                   over=soles(((25, 59), [(19, 52), (25, 50), (31, 52)]),
                              ((40, 60), [(35, 53), (41, 51), (46, 54)]))),
              CRASH_ANGLE, CRASH_AT, post_sx=1.12, post_sy=0.74)
    g = p.g
    p.wing(ARM_L, 254, 9)    # one wing punched up out of the mass
    p.wing(ARM_R, 44, 12)    # the other slapped flat along the mat
    J.finish(g)

    # The mat throwing dust out FLAT.  Weight goes sideways; it does not billow.
    for (x, y, r) in ((16, 89, 5), (29, 93, 4), (101, 90, 5), (113, 88, 4), (6, 93, 3)):
        J.puff(g, x, y, r)
    J.lines(g, [[(22, 78), (8, 72)], [(33, 75), (24, 67)],
                [(96, 76), (110, 69)], [(86, 72), (94, 63)],
                [(48, 53), (42, 42)], [(64, 52), (69, 41)], [(56, 51), (56, 39)]])
    J.speck(g, [(3, 85), (14, 80), (120, 82), (106, 77), (38, 95), (80, 95)])
    return g


# ------------------------------------------------------------------ down -----
DOWN_ANGLE, DOWN_AT = 92, (53, 73)


def down():
    """Settled.  Belly a dome, soles up, head lolled, nothing left."""
    p = build(dict(BASE, feet_detached=True,
                   body=(0, 0, 1.0, 1.04), head=(-2, 1),
                   face='dizzy', googly='wall',
                   over=soles(((25, 59), [(20, 51), (25, 49), (30, 51)]),
                              ((40, 60), [(35, 52), (40, 50), (45, 52)]))),
              DOWN_ANGLE, DOWN_AT, post_sx=1.14, post_sy=0.72)
    g = p.g
    p.wing(ARM_L, 212, 12)
    p.wing(ARM_R, 26, 13)
    J.finish(g)

    # Settled dust, and the mat still ringing under him.
    J.puff(g, 18, 92, 3)
    J.puff(g, 100, 93, 3)
    J.speck(g, [(27, 94), (10, 95), (92, 95), (109, 91), (40, 95), (80, 95)])
    return g


KEYS = [('launch', launch), ('hang', hang), ('tumble', tumble),
        ('crash', crash), ('down', down)]


# ============================================================ the full sheet ==
# Twelve frames.  Eric's ten are hit 2, cartwheel 4, crash 2, bounce 1, lying 1.
# Mason gets two beats a knight does not need, and they are the whole reason the
# sheet is twelve rather than ten:
#
#   the STALL.  A heavy mass visibly hangs at the top of its arc.  `hang` is the
#   tumble loop's first frame and is held nearly three times as long as any other
#   frame in the loop; the loop's four turning frames then whip through the
#   head-down half.  Even angular steps with wildly uneven durations is what
#   "slow up, long hang, fast down" looks like on a rotation cycle.
#
#   the SECOND SLUMP.  A heavy body does not bounce.  It hits, heaves once
#   without ever really leaving the mat, and slumps again flatter than it landed.
#   Eric's single bounce frame is replaced by a heave and a second, softer slump.
#
# The five approved keys ARE frames 0, 2, 3, 7 and 10 -- not redraws of them.
# build.py asserts that against mason_juggle_keys.png before it writes the sheet.

# The tumble loop's angles, after the stall at 54 and the approved 102: steps of
# 48, 82, 84, 76, 70 degrees.  Smallest either side of the stall, biggest through
# the head-down half, and slowing on the way back up into the next stall.  The
# durations in FRAMES do the same thing four times harder.
TUMBLE_TURN = (184, 268, 344)


def launch_lift():
    """A beat after contact: the dent springs back, he is finally moving, and his
    knees and wings are still down where the mat left them."""
    p = build(dict(BASE,
                   body=(0, 0, 1.03, 1.0), head=(0, 1),
                   face='strain', googly='knocked',
                   foot_r=(2, 3), foot_l=(-3, 3)),
              24, (64, 52))
    g = p.g
    p.wing(ARM_L, 152, 11)    # both wings still trailing below him
    p.wing(ARM_R, 32, 11)
    J.finish(g)

    J.lines(g, [[(50, 66), (44, 77)], [(78, 64), (85, 75)], [(64, 68), (64, 79)],
                [(31, 62), (21, 68)], [(95, 59), (105, 64)]])
    # The dust he left behind, now spreading and thinning.
    J.puff(g, 34, 91, 5)
    J.puff(g, 94, 92, 5)
    J.puff(g, 19, 94, 3)
    J.puff(g, 109, 94, 3)
    J.speck(g, [(10, 92), (118, 93), (46, 94), (82, 95), (27, 87), (101, 88)])
    return g


def _tumble_turn(i, angle, pdst, googly, feet, lag, arcs):
    """One of the loop's four turning frames.  `lag` is how far behind the body's
    own axis the wings swing: it grows through the whip and comes back as he
    slows into the stall, which is the secondary motion of a limp heavy limb."""
    p = build(dict(BASE,
                   body=(0, 0, 1.0, 1.03), head=(0, 0),
                   face='dizzy', googly=googly,
                   foot_r=feet[0], foot_l=feet[1]),
              angle, pdst)
    g = p.g
    p.wing(ARM_L, angle + 180 + lag)
    p.wing(ARM_R, angle + lag)
    J.finish(g)
    for (cx, cy, r, a0, a1, ry) in arcs:
        J.arc(g, cx, cy, r, a0, a1, ry=ry)
    return g


def tumble_b():
    """Head down, and turning fastest.  The wings have swung furthest behind."""
    return _tumble_turn(1, TUMBLE_TURN[0], (64, 50), 'wall', ((4, 1), (-5, 0)), 20,
                        [(64, 56, 46, 200, 262, 32), (64, 56, 40, 20, 78, 28)])


def tumble_c():
    """Round past the bottom, head to the trailing side, still whipping."""
    return _tumble_turn(2, TUMBLE_TURN[1], (72, 50), 'crossed', ((6, -1), (-4, 1)), 30,
                        [(66, 56, 46, 288, 352, 32), (66, 56, 40, 108, 162, 28)])


def tumble_d():
    """Coming back up and slowing down -- the next frame is the stall."""
    return _tumble_turn(3, TUMBLE_TURN[2], (62, 50), 'knocked', ((3, 1), (-6, -1)), 16,
                        [(64, 58, 44, 16, 74, 34)])


def crash_heave():
    """The heave.  He never really leaves the mat -- the mass just unsquashes once
    and the dust it punched out keeps going."""
    p = build(dict(BASE, feet_detached=True,
                   body=(0, 0, 1.0, 1.06), head=(0, -1),
                   face='pain', googly='knocked',
                   over=soles(((25, 59), [(19, 52), (25, 50), (31, 52)]),
                              ((40, 60), [(35, 53), (41, 51), (46, 54)]))),
              94, (54, 66), post_sx=1.06, post_sy=0.88)
    g = p.g
    p.wing(ARM_L, 268, 10)
    p.wing(ARM_R, 32, 12)
    J.finish(g)

    # The dust from the impact, now bigger, higher and further out.
    for (x, y, r) in ((13, 85, 6), (29, 90, 5), (98, 86, 6), (112, 84, 5),
                      (6, 93, 3), (119, 92, 3)):
        J.puff(g, x, y, r)
    J.lines(g, [[(24, 74), (8, 66)], [(98, 72), (116, 64)]])
    J.speck(g, [(20, 78), (106, 76), (40, 95), (80, 95), (60, 95)])
    return g


def crash_slump():
    """The second slump.  A heavy body does not bounce; it gives up twice, and the
    second time it does not compress -- it SPREADS.  This is the widest and
    flattest frame on the sheet, wider than the landing itself."""
    p = build(dict(BASE, feet_detached=True,
                   body=(0, 0, 1.0, 1.06), head=(-1, 1),
                   face='dizzy', googly='wall',
                   over=soles(((25, 59), [(19, 52), (25, 50), (31, 53)]),
                              ((40, 60), [(35, 53), (41, 51), (46, 54)]))),
              93, (54, 76), post_sx=1.21, post_sy=0.65)
    g = p.g
    p.wing(ARM_L, 196, 13)
    p.wing(ARM_R, 16, 14)
    J.finish(g)

    # Thinning out and drifting low.
    for (x, y, r) in ((14, 90, 4), (30, 93, 3), (100, 91, 4), (114, 92, 3)):
        J.puff(g, x, y, r)
    J.speck(g, [(5, 93), (22, 87), (121, 88), (106, 86), (44, 95), (84, 95), (64, 95)])
    return g


def down_breathe():
    """The same slump with his belly up on a breath: the only thing still moving."""
    p = build(dict(BASE, feet_detached=True,
                   body=(0, 0, 1.0, 1.04), head=(-2, 1),
                   face='dizzy', googly='wall',
                   over=soles(((25, 59), [(20, 51), (25, 49), (30, 51)]),
                              ((40, 60), [(35, 52), (40, 50), (45, 52)]))),
              92, (53, 71), post_sx=1.14, post_sy=0.78)
    g = p.g
    p.wing(ARM_L, 212, 12)
    p.wing(ARM_R, 26, 13)
    J.finish(g)

    J.puff(g, 18, 93, 2)
    J.speck(g, [(27, 95), (10, 95), (92, 95), (109, 93), (40, 95), (80, 95)])
    return g


# name, frame builder, hold in seconds.  The loop's shape lives in these numbers
# as much as in the art: frame 2 (the stall) is held 0.20s against 0.05s for the
# two frames of the whip, so the apex reads as a hang rather than a pause.
FRAMES = [
    ('launch_contact', launch,       0.06),
    ('launch_lift',    launch_lift,  0.07),
    ('hang',           hang,         0.20),
    ('tumble_a',       tumble,       0.08),
    ('tumble_b',       tumble_b,     0.05),
    ('tumble_c',       tumble_c,     0.05),
    ('tumble_d',       tumble_d,     0.07),
    ('crash_impact',   crash,        0.05),
    ('crash_heave',    crash_heave,  0.09),
    ('crash_slump',    crash_slump,  0.12),
    ('down_rest',      down,         0.55),
    ('down_breathe',   down_breathe, 0.55),
]
assert len(FRAMES) == 12

# Which sheet frames the approved keys are, for build.py's regression check.
APPROVED_AT = {'launch': 0, 'hang': 2, 'tumble': 3, 'crash': 7, 'down': 10}

# The tags the finisher asks for by name, as (first, last, loops).
TAGS = {
    'launch': (0, 1, False),
    'tumble': (2, 6, True),      # the stall, then the turn
    'crash': (7, 9, False),
    'down': (10, 11, True),      # a slow wheeze while he lies there
}
