"""The controls room's sparring dummy, drawn from the numbers in Scripts/TrainingDummyArtLayout.gd.

It is a prop, not a character: a leather sparring bot bolted to a weighted spring base, with a crude
screen-face and one padded swing arm. So it is drawn to the locker room's own palette rather than the
anime-character target the bosses use - every colour here is one of the 19 in controls_bg.png, and the
red pad is the same red as the gloves already hanging on the Arena #1 door.

COORDINATES. Two spaces, both in texels:
  frame   a pixel of a 64x64 cell, origin top-left, as the sheet stores it;
  origin  texels from the dummy's node, which is what the layout's boxes are in.
`Layout.frame_texel` says origin = frame - (32, 34), so ANCHOR (32, 58) is origin (0, 24) - the floor
point, one row under the lowest drawn pixel.

THE RIG is the stand-in's rig, so the sheet and the code-drawn placeholder animate identically and
flipping USE_FINAL_DUMMY changes nothing but the rendering (TrainingDummyScript._build_placeholder):

  base, foot      bolted down. Never move.
  figure          rotated `tip` degrees about PIVOT, then moved `lean` texels along x.
                  Carries the barrel, the strap, the screen-face and the spring's top.
  arm             a child of the figure, rotated a further `arm` degrees about SHOULDER.

POSES are Layout.PLACEHOLDER_POSES, copied here and asserted equal by build.py. ART_POSES adds what
only a drawing needs: `squash` along the figure's own length, because a rigid 78-degree tip would
throw the barrel 6 texels out of the cell, and a sparring bot folding over its spring should compress
anyway. LUNGE_PUSH is NOT baked in - TrainingDummyScript adds it to sprite.offset.

SHADING is worked out in world space from one light up and to the left, so a barrel lying on its side
after a crash is lit on its new top rather than on the side that used to face up. The strap, the seam
and the screen-face are local overrides on top of that.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------- palette
# Every entry is DB32 AND one of the 19 colours controls_bg.png is drawn with, so the dummy cannot
# read as an import into the room. build.py checks both.
PAL = {
    'K': (0, 0, 0),          # keyline. 1px, everywhere, like the bench legs and the hanging gloves
    'N': (34, 32, 52),       # dark navy: bezel, coil gaps, the deepest steel
    'P': (69, 40, 60),       # plum: leather's darkest turn (the room's own brick)
    'B': (102, 57, 49),      # leather shadow
    'M': (143, 86, 59),      # leather base
    'T': (217, 160, 102),    # leather highlight / the strap
    'A': (238, 195, 154),    # the strap's lit edge
    'G': (138, 111, 48),     # strap shadow and the buckle's dark side
    'S': (89, 86, 82),       # steel base
    's': (105, 106, 106),    # steel mid
    'H': (132, 126, 135),    # steel light
    'C': (155, 173, 183),    # pale steel: wrist cuff, the lit screen
    'W': (203, 219, 252),    # glare
    'D': (48, 96, 130),      # the screen, unlit
    'R': (172, 50, 50),      # glove red, the door gloves' red
    'r': (217, 87, 99),      # glove highlight
}

# ---------------------------------------------------------------- geometry (mirrors the .gd)
# The body is 34 texels tall, which is 102 px on screen at SCALE 3 - about 1.6x the player, where the
# first pass stood 159. It is redrawn smaller in texels rather than dropped to a smaller SCALE,
# because a 2x prop beside a 3x player puts two different pixel sizes on one screen.
FRAME = 64
FRAME_ORIGIN = (32, 42)      # frame pixel of origin (0, 0); Layout.frame_texel's offset
SHEET_FRAMES = 19
ANCHOR_Y = 8                 # origin y of the floor; the lowest drawn row is 7
PIVOT = (0.0, 3.0)           # Layout.PLACEHOLDER_PIVOT: where the figure tips, inside the collar
# The arm is bolted out at the bag's shoulder rather than in on its chest, and is shorter to
# compensate, so the reach from the origin is the same 16 texels. That is not styling: with the bolt
# inboard, the red wind-up swung the glove up behind the head plate and it all but vanished, and the
# cocked arm is half of what makes the red telegraph read.
SHOULDER = (5.0, -12.0)      # Layout.PLACEHOLDER_SHOULDER: where the arm turns
HURT_BOX = (-8, -21, 16, 29)    # Layout.HURT_BOX in origin texels: the barrel's width and top
BODY_BOX = (-8, -1, 16, 9)      # Layout.BODY_BOX in origin texels: the coil and the weight

SWITCH_W, SWITCH_H = 24, 40
SWITCH_FRAMES = 2

# Layout.PLACEHOLDER_POSES, frame -> (lean, arm, tip). build.py asserts this equals the .gd.
# `tip` and `arm` are degrees, so they carry over to a smaller body untouched. `lean` is TEXELS, and
# it does not: 7 texels was a quarter of the old 24-texel bag and is nearly half of this 16-texel
# one, which threw the lunge's whole figure - glove included - past its own hitbox. Every lean is
# drawn at LEAN_SCALE of the table's value, which is the same fraction the body shrank by.
# The .gd's own leans want the same scaling when this lands; build.py prints the table to apply, and
# once it has, LEAN_SCALE goes to 1.0 and nothing else changes.
#
# A scaled lean is quantised, and the DRAWING uses the quantised value - not the raw product. That is
# the whole point: the number build.py prints for the .gd and the number this file draws with have to
# be the same number. They were not the first time round. The renderer used the full-precision
# product while the printer rounded to two places for display, so a lean of 0.5 x 0.65 = 0.325 was
# published as 0.33, applied literally, and moved a pixel.
LEAN_SCALE = 1.0
LEAN_DECIMALS = 3


def scaled_lean(lean):
    """A table lean as it is actually drawn: scaled, then quantised so it can be written down."""
    return round(lean * LEAN_SCALE, LEAN_DECIMALS)
POSES = {
    0:  (0.0, 10.0, 0.0),     1:  (0.325, -6.0, 1.5),
    2:  (-3.25, 26.0, -6.0),   3:  (-1.3, 16.0, -2.0),
    4:  (-1.95, -70.0, -3.0),  5:  (-2.6, -84.0, -4.0),
    6:  (0.65, -30.0, 0.0),    7:  (2.6, 40.0, 5.0),
    8:  (1.3, 62.0, 3.0),     9:  (-2.6, 4.0, -5.0),
    10: (-3.9, 2.0, -7.0),    11: (4.55, 12.0, 9.0),
    12: (3.25, 14.0, 7.0),     13: (1.95, 20.0, 4.0),
    14: (-1.95, -14.0, -4.0),  15: (0.0, -40.0, -20.0),
    16: (0.0, 70.0, 78.0),    17: (-1.3, 30.0, 30.0),
    18: (-2.6, 34.0, -10.0),
}

# What only the drawing needs, on top of POSES.
#   squash    scales the figure along its own length about PIVOT: under 1 it folds into the spring,
#             over 1 it stretches. A rigid 78-degree tip would throw the head six texels out of the
#             cell, and a bot folding over its own spring should compress anyway.
#   arm_bias  degrees added to the arm, for where the stand-in's angle would drive the glove through
#             the floor: once the body is lying down, an arm that still hangs "down" from its
#             shoulder is hanging into the ground.
#   rise      texels the figure is lifted straight up, for the crash frames. The coil does not just
#             turn about PIVOT, it bends, and PIVOT sits five texels over the floor while a bag lying
#             on its side is eight texels thick - so a pure rotation buries its lower edge. Lifting
#             it puts the bag ON the floor and lets the coil stretch to meet it, which is what a
#             folded spring actually does.
#   face      which screen glyph is lit.
ART_POSES = {
    0:  dict(squash=1.00, face='idle'),
    1:  dict(squash=0.99, face='idle_blink'),
    2:  dict(squash=0.92, face='ow'),
    3:  dict(squash=0.97, face='squint'),
    4:  dict(squash=1.01, face='angry'),
    5:  dict(squash=1.02, face='angry_hot'),
    6:  dict(squash=1.02, face='angry_hot'),
    7:  dict(squash=0.96, face='shout'),
    8:  dict(squash=0.98, face='squint'),
    9:  dict(squash=1.00, face='stare'),
    10: dict(squash=1.01, face='stare_hot'),
    11: dict(squash=1.01, face='shout'),
    12: dict(squash=0.99, face='shout'),
    13: dict(squash=0.98, face='swirl_a'),
    14: dict(squash=0.98, face='swirl_b'),
    15: dict(squash=1.06, face='shock'),
    16: dict(squash=0.92, rise=4.0, face='dead'),
    17: dict(squash=0.96, rise=1.0, face='dead'),
    18: dict(squash=0.96, face='swirl_b'),
}

# ---------------------------------------------------------------- what the .gd has to become
# The redraw moves numbers that live in Scripts/TrainingDummyArtLayout.gd. build.py compares these
# with the file and prints whatever still has to change, so the sheet and the boxes cannot drift.
#
# ANCHOR and SORT_POINT together are the whole reason the small body works. SORT_POINT is how far the
# node sits above the floor, and BODY_BOX has to reach the floor, so its bottom edge is 3*SORT_POINT.y
# px below the origin - and the player standing IN FRONT is pushed out by exactly that, plus their own
# half height. The attacks radiate from the origin, so leaving SORT_POINT at (0, 24) while the body
# shrank would hold the player 98 px out while the arm reached 48: the yellow lunge could not have
# landed from anywhere the player can punch from, which is the dodge lesson breaking a second time.
# Dropping the origin to the drum takes that standoff to 50 px and the lunge's window goes from
# 23 px (as shipped) to 46 px.
PROPOSAL = {
    'ANCHOR': (32, 50),                 # was (32, 58): the floor row, and the cell's middle across
    'SORT_POINT': (0, 8),               # was (0, 24)
    'PLACEHOLDER_PIVOT': (0, 3),        # was (0, 14): the coil's root, where the figure tips
    'PLACEHOLDER_SHOULDER': (5, -12),   # was (5, -8): out at the bag's shoulder, same x
    'BODY_BOX': (24, 41, 16, 9),        # was (20, 34, 24, 24): the coil and the drum, down to ANCHOR
    'HURT_BOX': (24, 21, 16, 29),       # was (20, 12, 24, 46): the barrel's width and top, to ANCHOR
    'SWING_BOX': (4, -8, 12, 16),       # was (9, -11, 24, 22): now what the padded arm actually covers
    'LUNGE_BOX': (5, -8, 19, 16),       # was (9, -9, 26, 18): what the lunged body plus LUNGE_PUSH covers
    'LUNGE_PUSH': 4.0,                  # was 6.0
    'DAZE_ANCHOR_OFFSET': (0, -112),    # was (0, -124): 34 px over the screen-face, as before
    'TELL_ANCHOR_OFFSET': (0, -92),     # was (0, -98): 14 px over the head, as before
    'JUGGLE_POINT_OFFSET': (0, -38),    # was (0, -21): the middle of the barrel
    'JUGGLE_HEADROOM': 300.0,           # was 330.0: see the note at the foot of this file
}

# ---------------------------------------------------------------- the screen-face
# 8 wide x 5 tall, the lit area of the panel. '.' unlit (D), 'C' lit, 'W' the brightest pixels.
# The two telegraphs are drawn with different eye shapes - brows down for the red swing, a round
# stare for the yellow lunge - so which one is coming reads before the badge's colour does.
# The finisher draws its own daze stars over frames 13-14, so the daze face carries the read alone.
FACES = {
    'idle': [
        "........",
        ".CC..CC.",
        "........",
        ".CCCCCC.",
        "........",
    ],
    'idle_blink': [
        "........",
        "........",
        ".CC..CC.",
        "........",
        ".CCCCCC.",
    ],
    'ow': [                       # knocked: eyes blown wide, mouth open
        "CCC..CCC",
        "C.C..C.C",
        "CCC..CCC",
        "..CCCC..",
        "..CCCC..",
    ],
    'squint': [
        "........",
        "........",
        "CCC..CCC",
        "........",
        ".CCCCCC.",
    ],
    'angry': [                    # brows down toward the middle: the red swing
        "C......C",
        ".CC..CC.",
        "..CCCC..",
        "........",
        ".CCCCCC.",
    ],
    'angry_hot': [
        "W......W",
        ".WW..WW.",
        "..WWWW..",
        "........",
        ".WWWWWW.",
    ],
    'shout': [
        "........",
        ".CC..CC.",
        "........",
        "..CCCC..",
        ".CCCCCC.",
    ],
    'stare': [                    # a round stare: the yellow lunge, told apart at a glance
        ".CC..CC.",
        "C..CC..C",
        ".CC..CC.",
        "........",
        "..CCCC..",
    ],
    'stare_hot': [
        ".WW..WW.",
        "W..WW..W",
        ".WW..WW.",
        "........",
        "..WWWW..",
    ],
    'swirl_a': [                  # dazed: the two spin between the frames
        "CC...CC.",
        "C.C..C.C",
        "C.C...CC",
        "........",
        ".C.CC.C.",
    ],
    'swirl_b': [
        ".CC..CC.",
        "C.C..C.C",
        "CC....CC",
        "........",
        "C.CC.C..",
    ],
    'shock': [                    # launched
        ".CC..CC.",
        ".CC..CC.",
        ".CC..CC.",
        "..CCCC..",
        "..CCCC..",
    ],
    'dead': [                     # crashed: X eyes
        "C.C..C.C",
        ".C....C.",
        "C.C..C.C",
        "........",
        ".CCCCCC.",
    ],
}

# ---------------------------------------------------------------- the barrel's profile
# Half-width at each origin row of the leather barrel, top (-22) to bottom (7). 12 is HURT_BOX's own
# half-width, so the widest rows are exactly what the player punches.
BARREL_TOP, BARREL_BOT = -21, -4
BARREL_HW = [5, 7, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 7, 7, 6, 5]
BARREL_MID = (BARREL_TOP + BARREL_BOT) / 2.0
STRAP_TOP, STRAP_BOT = -11, -9      # the waist belt, with the buckle
BAND_TOP, BAND_BOT = -18, -18       # a second, plainer belt, clear of the head plate's keyline
# The seam sits on the shaded side. Down the lit side it took one of the four columns the highlight
# band has to work with and read as a stripe rather than as stitching.
SEAM_X = 2
# A stencilled target ring on the chest: what the prop is for, said on the prop, and the one thing
# that keeps nineteen identical rows of a cylinder from reading as a barrel of nothing.
# The larger pass carried a stencilled target ring on the chest. A ring needs about seven rows to
# stay a ring and a filled patch reads as a slot, and there are five rows here between the head plate
# and the strap - so on a sixteen-texel bag the belts, the seam and the screen-face carry it instead.
# If the target comes back it wants its own pass, not a shrunk copy of the old one.

# The base: a narrow collar stepping out to a heavy drum - the weight. Half width per row, 2 to 7.
# It is drawn 2 texels proud of BODY_BOX on each side, the way the first pass's was, so the player is
# stopped at the drum's face rather than inside its flare.
# The coil goes straight into the drum: at this size a separate collar between them is one shape
# change too many in eight rows, and it was eating the coil's only room.
BASE_TOP, BASE_BOT = 3, 7
BASE_HW = [6, 9, 9, 9, 8]
BASE_RIM = 4                        # the drum's top plane, where the shoulder steps out to the weight
SPRING_ROOT = (0.0, 4.5)            # inside the drum, so the coil is seen leaving it
SPRING_HEAD = (0.0, -4.0)           # where it enters the barrel, in figure space
SPRING_R = 3.0
SPRING_PITCH = 3.0                  # texels of coil per turn: the rest of it lit, 1 in the gap

# The screen-face panel, in figure space: 10 wide, rows -26..-20, with an 8x5 screen inside it.
FACE_BOX = (-5.0, -26.0, 10.0, 7.0)
FACE_SCREEN = (-4.0, -25.0, 8.0, 5.0)

# The arm, in arm space: x runs out along the limb from the shoulder bolt at (0, 0).
# The limb reaches 11.0 texels from the shoulder bolt, which sits at origin x 5 - so the glove tips
# out to origin x 16, and SWING_BOX's own reach is 16. At this size the drawing covers its box, which
# it could not at the first pass's scale. See the note at the foot of this file.
ARM_SHAFT = ((1.4, 0.0), (4.6, 0.0), 1.9)      # p0, p1, radius
ARM_BOLT_R = 2.0
CUFF = (4.2, 5.6, 2.4)                         # x0, x1, half height
GLOVE_C, GLOVE_RX, GLOVE_RY = (7.6, 0.2), 3.4, 3.2
THUMB_C, THUMB_R = (6.2, 2.5), 1.7

# Up, a little to the left, and toward the viewer, like the room's ceiling fixtures. The z term is
# what makes a barrel read as a barrel: the brightest band sits inboard of the lit edge and the edge
# itself turns away again, instead of the whole left half going flat light and the right half flat
# dark.
LIGHT = (-0.62, -0.32, 0.72)


# ---------------------------------------------------------------- maths
def row_of(y):
    """The frame row a sample sits on. Pixel centres are always at .5, where round() rounds to
    even and so alternates between the row above and the row below - floor is the only lookup that
    keeps one texel of y on one row of a profile."""
    return int(math.floor(y))


def rot(p, deg):
    """Godot's rotation: +x turns toward +y, which on a screen with y down is clockwise."""
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def norm(v):
    m = math.hypot(v[0], v[1])
    return (0.0, 0.0) if m < 1e-9 else (v[0] / m, v[1] / m)


class Pose:
    """The two nested transforms the stand-in uses, and their inverses for shading lookups."""

    def __init__(self, index):
        self.lean, self.arm, self.tip = POSES[index]
        self.lean = scaled_lean(self.lean)
        art = ART_POSES[index]
        self.squash = art['squash']
        self.rise = art.get('rise', 0.0)
        self.arm = self.arm + art.get('arm_bias', 0.0)
        self.face = art['face']

    # origin texels -> origin texels
    def figure(self, p):
        q = sub(p, PIVOT)
        q = (q[0], q[1] * self.squash)
        q = rot(q, self.tip)
        return (q[0] + PIVOT[0] + self.lean, q[1] + PIVOT[1] - self.rise)

    def unfigure(self, p):
        q = (p[0] - PIVOT[0] - self.lean, p[1] - PIVOT[1] + self.rise)
        q = rot(q, -self.tip)
        return (q[0] + PIVOT[0], q[1] / self.squash + PIVOT[1])

    def unarm(self, p):
        """origin texels -> arm space, where the limb runs along +x from (0, 0)."""
        return rot(sub(self.unfigure(p), SHOULDER), -self.arm)

    def figure_angle(self):
        return self.tip

    def arm_angle(self):
        return self.tip + self.arm


# ---------------------------------------------------------------- shading
CUTS = (0.90, 0.45, -0.05)          # light -> dark, tuned so the mid tone carries most of a surface


def tone_of(across, along, world_deg, ramp):
    """Pick from a four-step ramp for a rounded surface.

    `across` is -1 at the left edge of the form and +1 at the right, `along` is -1 at the end that
    faces up and +1 at the end that faces down, both before the part is posed. The surface normal is
    the point of the unit sphere they name, so the part is shaded as the round thing it is; only its
    x and y turn with the pose, which is what keeps a barrel lit on top once it has fallen over.
    """
    along = max(-1.0, min(1.0, along))
    across = max(-1.0, min(1.0, across)) * math.sqrt(max(0.0, 1.0 - along * along))
    nz = math.sqrt(max(0.0, 1.0 - across * across - along * along))
    ax, ay = rot((across, along), world_deg)
    d = ax * LIGHT[0] + ay * LIGHT[1] + nz * LIGHT[2]
    if d > CUTS[0]:
        return ramp[0]
    if d > CUTS[1]:
        return ramp[1]
    if d > CUTS[2]:
        return ramp[2]
    return ramp[3]


LEATHER = ('T', 'M', 'B', 'P')
STEEL = ('H', 's', 'S', 'N')
IRON = ('s', 'S', 'N', 'N')      # the weight: the same steel, one step down
# The door's hanging gloves are ac3232 over 45283c with a d95763 catchlight and nothing else; the
# pad is the same three, so it reads as one of them taken off the hook and bolted on.
GLOVE = ('r', 'R', 'P', 'P')
CUFF_RAMP = ('W', 'C', 'H', 'S')


# ---------------------------------------------------------------- the parts
def barrel_hw(y):
    i = row_of(y) - BARREL_TOP
    if i < 0 or i >= len(BARREL_HW):
        return -1.0
    return float(BARREL_HW[i])


def in_barrel(p):
    if not (BARREL_TOP <= row_of(p[1]) <= BARREL_BOT):
        return False
    return abs(p[0]) <= barrel_hw(row_of(p[1]))


def barrel_tone(p, world_deg):
    x, y = p
    row = row_of(y)
    hw = max(barrel_hw(row), 1.0)
    # cap term: only the last few rows of either end turn away from the side of the cylinder
    along = 0.0
    if row <= BARREL_TOP + 2:
        along = -0.45 * (BARREL_TOP + 3 - row) / 3.0
    elif row >= BARREL_BOT - 2:
        along = 0.45 * (row - BARREL_BOT + 3) / 3.0
    t = tone_of(x / hw, along, world_deg, LEATHER)

    # The belts are re-mapped off the leather's own tone rather than painted flat. Flat was tried and
    # on a sixteen-texel bag a belt that is pale for eleven of them is a bar across the middle, not a
    # strap: it has to turn with the barrel like everything else.
    if STRAP_TOP <= row <= STRAP_BOT:
        # the buckle sits out on the lit side, clear of the shoulder bolt the arm turns on
        if -6.0 <= x <= -3.0:
            if row == STRAP_BOT or row_of(x) == -6:
                return 'G'
            return 'H' if x < -4.5 else 's'
        if row == STRAP_BOT:
            return 'G' if t in ('T', 'M') else 'B'
        if row == STRAP_TOP:
            return {'T': 'A', 'M': 'T', 'B': 'G', 'P': 'G'}[t]
        return {'T': 'T', 'M': 'T', 'B': 'G', 'P': 'G'}[t]
    if BAND_TOP <= row <= BAND_BOT:
        return {'T': 'A', 'M': 'T', 'B': 'G', 'P': 'G'}[t]

    # one stitched panel seam, a shade under whatever it crosses
    if row_of(x) == SEAM_X:
        return LEATHER[min(LEATHER.index(t) + 1, 3)]
    return t


def base_hw(row):
    i = row - BASE_TOP
    if i < 0 or i >= len(BASE_HW):
        return -1.0
    return float(BASE_HW[i])


def in_base(p):
    return abs(p[0]) <= base_hw(row_of(p[1]))


def base_tone(p):
    x, y = p
    row = row_of(y)
    hw = max(base_hw(row), 1.0)
    if row == BASE_BOT:                              # where it meets the floor
        return 'N'
    # the two bolts holding it down
    for bx in (-6.0, 6.0):
        if abs(x - bx) <= 0.6 and BASE_BOT - 2 <= row <= BASE_BOT - 1:
            return 'N' if row == BASE_BOT - 1 else 'H'
    if row == BASE_TOP:                              # the lit shoulder where the coil enters
        return 'N' if x > hw - 2.5 else 'H'
    if row == BASE_RIM:                              # the drum's top plane
        return 'N' if x > hw - 5.0 else 'H'
    return tone_of(x / hw, 0.0, 0.0, STEEL)


def seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    vx, vy = bx - ax, by - ay
    wx, wy = p[0] - ax, p[1] - ay
    L = vx * vx + vy * vy
    t = 0.0 if L < 1e-9 else max(0.0, min(1.0, (wx * vx + wy * vy) / L))
    return math.hypot(wx - t * vx, wy - t * vy), t


def bezier(a, c, b, t):
    u = 1.0 - t
    return (u * u * a[0] + 2 * u * t * c[0] + t * t * b[0],
            u * u * a[1] + 2 * u * t * c[1] + t * t * b[1])


def spring_path(pose):
    """The coil leaves the bolted base straight up and bends over to wherever the barrel went."""
    head = pose.figure(SPRING_HEAD)
    ctrl = (SPRING_ROOT[0], SPRING_ROOT[1] - 2.6)
    return SPRING_ROOT, ctrl, head


def in_gap(arc):
    """A turn is SPRING_PITCH texels of coil: two lit, one in the shade behind the next turn.
    Measuring in texels rather than in a fraction of the path is what keeps the gap a whole pixel
    wide however far the coil has been stretched or bent."""
    return (arc % SPRING_PITCH) >= SPRING_PITCH - 1.0


def coil_radius(_arc):
    return SPRING_R


def spring_polyline(pose):
    a, c, b = spring_path(pose)
    pts, arcs, total = [a], [0.0], 0.0
    steps = 40
    for i in range(1, steps + 1):
        cur = bezier(a, c, b, i / steps)
        total += math.hypot(cur[0] - pts[-1][0], cur[1] - pts[-1][1])
        pts.append(cur)
        arcs.append(total)
    return pts, arcs


def spring_hit(p, pose):
    """(distance across, texels along the coil, signed side) or None."""
    pts, arcs = spring_polyline(pose)
    best = None
    for i in range(1, len(pts)):
        d, t = seg_dist(p, pts[i - 1], pts[i])
        arc = arcs[i - 1] + t * (arcs[i] - arcs[i - 1])
        if best is None or d < best[0]:
            ax, ay = pts[i - 1]
            bx, by = pts[i]
            near = (ax + t * (bx - ax), ay + t * (by - ay))
            # how far across the coil the sample is, measured the way the light runs rather than
            # along the path's own normal, so a coil bent over in a crash is still lit from the left
            best = (d, arc, p[0] - near[0])
    if best[0] > coil_radius(best[1]):
        return None
    return best


def spring_tone(hit, pose):
    d, arc, side = hit
    if in_gap(arc):
        return 'N'
    return tone_of(side / SPRING_R, 0.0, 0.0, STEEL)


def in_face_panel(p):
    x, y, w, h = FACE_BOX
    return x - 0.0 <= p[0] <= x + w - 1.0 + 0.5 and y <= p[1] <= y + h - 1.0 + 0.5


def face_tone(p, pose, glyph_deg):
    x, y, w, h = FACE_BOX
    sx, sy, sw, sh = FACE_SCREEN
    if sx <= p[0] <= sx + sw - 0.5 and sy <= p[1] <= sy + sh - 0.5:
        # sample the glyph on a grid snapped to the nearest quarter turn, so a 1px eye stays a 1px eye
        c = (sx + sw / 2.0, sy + sh / 2.0)
        q = rot(sub(p, c), -glyph_deg)
        gx = int(math.floor(q[0] + sw / 2.0))
        gy = int(math.floor(q[1] + sh / 2.0))
        rows = FACES[pose.face]
        if 0 <= gy < len(rows) and 0 <= gx < len(rows[0]):
            ch = rows[gy][gx]
            if ch != '.':
                return ch
            if gy == 0 and gx <= 1:                  # the glare off the top-left of the glass
                return 'S'
        return 'D'
    # bezel, with a mounting screw at each bottom corner
    for bx in (x + 1.0, x + w - 2.0):
        if abs(p[0] - bx) <= 0.5 and abs(p[1] - (y + h - 2.0)) <= 0.5:
            return 'H'
    return 'S' if p[1] < y + 1.0 else 'N'


def in_arm(p):
    d, _ = seg_dist(p, ARM_SHAFT[0], ARM_SHAFT[1])
    if d <= ARM_SHAFT[2]:
        return True
    if math.hypot(p[0], p[1]) <= ARM_BOLT_R:
        return True
    if CUFF[0] <= p[0] <= CUFF[1] and abs(p[1]) <= CUFF[2]:
        return True
    dx = (p[0] - GLOVE_C[0]) / GLOVE_RX
    dy = (p[1] - GLOVE_C[1]) / GLOVE_RY
    if dx * dx + dy * dy <= 1.0:
        return True
    return math.hypot(p[0] - THUMB_C[0], p[1] - THUMB_C[1]) <= THUMB_R


def arm_tone(p, world_deg):
    dx = (p[0] - GLOVE_C[0]) / GLOVE_RX
    dy = (p[1] - GLOVE_C[1]) / GLOVE_RY
    in_glove = dx * dx + dy * dy <= 1.0
    in_thumb = math.hypot(p[0] - THUMB_C[0], p[1] - THUMB_C[1]) <= THUMB_R
    if in_glove or in_thumb:
        if in_thumb and not in_glove:
            n = norm(sub(p, THUMB_C))
            return tone_of(n[0], n[1], world_deg, GLOVE)
        # the glove is a ball: along the arm is its own axis, so it lights like a fist, not a tube
        return tone_of(dx, dy, world_deg, GLOVE)
    if CUFF[0] <= p[0] <= CUFF[1] and abs(p[1]) <= CUFF[2]:
        return tone_of(p[1] / CUFF[2], 0.0, world_deg + 90.0, CUFF_RAMP)
    r = math.hypot(p[0], p[1])
    if r <= ARM_BOLT_R:
        return tone_of(p[0] / ARM_BOLT_R, p[1] / ARM_BOLT_R, world_deg, STEEL)
    # the shaft and the cuff are tubes lying along the arm, so their cross-section is the arm's
    # own across - a quarter turn from the body's.
    return tone_of(p[1] / ARM_SHAFT[2], 0.0, world_deg + 90.0, LEATHER)


# ---------------------------------------------------------------- rasterising
def blank():
    return [[' '] * FRAME for _ in range(FRAME)]


def to_origin(px, py):
    return (px + 0.5 - FRAME_ORIGIN[0], py + 0.5 - FRAME_ORIGIN[1])


ORTHO = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIAG = ((1, 1), (1, -1), (-1, 1), (-1, -1))


def stamp(grid, covered, mask, colour_of):
    """A part's own 1px keyline, then its fill - so every piece is outlined where it crosses another,
    the way Danny's arm is outlined where it crosses his shirt.

    Outside the figure the keyline takes the diagonals too, which is what keeps the silhouette from
    leaking at a corner. Where it crosses another part it does not: on a bag sixteen texels wide the
    arm's inner outline was cutting a black wedge out of the leather, and the diagonals were most of
    it. `covered` is every part stamped so far, so the two cases can be told apart.
    """
    ring = set()
    for (px, py) in mask:
        for dx, dy in ORTHO + DIAG:
            q = (px + dx, py + dy)
            if q in mask or not (0 <= q[0] < FRAME and 0 <= q[1] < FRAME):
                continue
            if q in covered and (dx, dy) in DIAG:
                continue
            ring.add(q)
    for (px, py) in sorted(ring):
        grid[py][px] = 'K'
    for (px, py) in sorted(mask):
        grid[py][px] = colour_of(px, py)
    covered |= mask


def frame_grid(index):
    pose = Pose(index)
    grid = blank()
    fdeg = pose.figure_angle()
    adeg = pose.arm_angle()
    # the glyph grid snaps to quarter turns so small features stay crisp when the bot folds over
    glyph_deg = round(fdeg / 90.0) * 90.0

    pts = [(px, py) for py in range(FRAME) for px in range(FRAME)]
    covered = set()

    # 1. the coil and the drum it is rooted in, stamped as one piece of steel
    mask, tones = set(), {}
    for px, py in pts:
        p = to_origin(px, py)
        hit = spring_hit(p, pose)
        if hit:
            mask.add((px, py))
            tones[(px, py)] = spring_tone(hit, pose)
    for px, py in pts:
        p = to_origin(px, py)
        if in_base(p):
            mask.add((px, py))
            tones[(px, py)] = base_tone(p)
    stamp(grid, covered, mask, lambda px, py: tones[(px, py)])

    # 3. the leather barrel
    mask, tones = set(), {}
    for px, py in pts:
        q = pose.unfigure(to_origin(px, py))
        if in_barrel(q):
            mask.add((px, py))
            tones[(px, py)] = barrel_tone(q, fdeg)
    stamp(grid, covered, mask, lambda px, py: tones[(px, py)])

    # 4. the padded swing arm, over the leather but under the head plate. The plate wins because
    #    the face IS the telegraph - brows for the red swing, a round stare for the yellow lunge -
    #    and on the wind-up frames the glove comes up level with it and would cover half the screen.
    mask, tones = set(), {}
    for px, py in pts:
        q = pose.unarm(to_origin(px, py))
        if in_arm(q):
            mask.add((px, py))
            tones[(px, py)] = arm_tone(q, adeg)
    stamp(grid, covered, mask, lambda px, py: tones[(px, py)])
    # 5. the screen-face, over the arm
    mask, tones = set(), {}
    for px, py in pts:
        q = pose.unfigure(to_origin(px, py))
        if in_face_panel(q):
            mask.add((px, py))
            tones[(px, py)] = face_tone(q, pose, glyph_deg - fdeg)
    stamp(grid, covered, mask, lambda px, py: tones[(px, py)])

    return grid


# ---------------------------------------------------------------- the mode post
# 24x40, the cell's bottom centre being the floor point it stands on (TrainingRoomScript sets the
# sprite offset to -w/2, -h). A steel column with a two-cell head plate: the live mode is a lit block
# with its word knocked out dark, the other is dark with its word dim. The block is what reads from
# across the room - pale for BAG, the door-glove red for SPAR - and the word resolves up close.
POST_COLUMN = (-5, 5, -26, -4)          # x0, x1, y0, y1 in origin texels
POST_FOOT = (-8, 8, -4, -1)
POST_PLATE = (-9, 9, -39, -25)
# word -> (top row of its 5-row line, backing bar when live, word colour when live)
POST_LINES = {'BAG': (-37, 'D', 'W'), 'SPAR': (-31, 'P', 'r')}
POST_RIVETS = (-22, -10)
# A 3x5 alphabet, only the six letters the two words need.
POST_FONT = {
    'B': ["CC.", "C.C", "CC.", "C.C", "CC."],
    'A': [".C.", "C.C", "CCC", "C.C", "C.C"],
    'G': ["CCC", "C..", "CCC", "C.C", "CCC"],
    'S': ["CCC", "C..", "CCC", "..C", "CCC"],
    'P': ["CCC", "C.C", "CCC", "C..", "C.."],
    'R': ["CCC", "C.C", "CCC", "CC.", "C.C"],
}


def post_word(word):
    """The word as rows of texels, letters one texel apart."""
    return [' '.join(POST_FONT[ch][r] for ch in word).replace(' ', '.') for r in range(5)]


def post_grid(sparring):
    grid = [[' '] * SWITCH_W for _ in range(SWITCH_H)]
    ox, oy = SWITCH_W // 2, SWITCH_H          # origin: bottom centre of the cell

    mask, tones = set(), {}
    for py in range(SWITCH_H):
        for px in range(SWITCH_W):
            x, y = px - ox + 0.5, py - oy + 0.5
            for box, steel in ((POST_COLUMN, True), (POST_FOOT, True), (POST_PLATE, False)):
                x0, x1, y0, y1 = box
                if x0 <= x <= x1 and y0 <= y <= y1:
                    mask.add((px, py))
                    tones[(px, py)] = tone_of((x - 0.5) / (x1 + 0.5), 0.0, 0.0, STEEL) if steel else 'N'
    # rivets down the column, so it reads as bolted gear and not as a length of pipe
    for ry in POST_RIVETS:
        for rx in (-3, 3):
            tones[(rx + ox, ry + oy)] = 'H'
            tones[(rx + ox, ry + 1 + oy)] = 'N'
    stamp_post(grid, mask, tones)

    for word, (top, bar, hot) in POST_LINES.items():
        live = (word == 'SPAR') == sparring
        art = post_word(word)
        x0 = ox - len(art[0]) // 2
        for ry in range(5):
            for cx in range(-8, 9):
                grid[top + ry + oy][cx + ox] = bar if live else 'N'
        for ry, line in enumerate(art):
            for rx, ch in enumerate(line):
                if ch != '.':
                    grid[top + ry + oy][x0 + rx] = hot if live else 'S'
    return grid


def stamp_post(grid, mask, tones):
    ring = set()
    for (px, py) in mask:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            q = (px + dx, py + dy)
            if q not in mask and 0 <= q[0] < SWITCH_W and 0 <= q[1] < SWITCH_H:
                ring.add(q)
    for (px, py) in sorted(ring):
        grid[py][px] = 'K'
    for (px, py) in sorted(mask):
        grid[py][px] = tones[(px, py)]


# ---------------------------------------------------------------- the cell and the boxes
# At the first pass's size this was a problem: ANCHOR is (32, 50), so the dummy is centred across its
# cell and the frame ends 31 texels to its right, while SWING_BOX reached 33 and LUNGE_BOX 35. No
# drawing anchored at the middle of a 64-wide cell could cover them, and the arm stopped a dozen
# texels short of where the swing actually connected.
#
# The smaller body settles it. The arm tips out to origin x 16 and SWING_BOX reaches 16; the lunged
# body plus LUNGE_PUSH reaches 25 and LUNGE_BOX reaches 24. Both are inside the cell with fifteen
# texels to spare, and build.py fails if either drifts more than four texels from its box.
#
# JUGGLE_HEADROOM is the one number here that is a judgement rather than a measurement. With the node
# at (1150, 948) the head sits at y 870, and the reference cards above the play band end at y 570,
# so 300 is the most an uppercut can lift it and still show the whole dummy under them. Scaling the
# old 330 by how much the body shrank would give 215 instead, which keeps the throw proportional to
# the dummy but takes air off the finisher; 300 is the better trade and the cards are the reason.
