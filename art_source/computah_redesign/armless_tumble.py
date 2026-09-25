"""computah_armless_tumble: the armless Computah hurled out of the ring by Greyson, right after the
cannon goes on (the user, 2026-09-24 playtest: "greyson needs to throw computah out the ring so hes
no longer in the way"). Greyson's side is art_source/greyson_fight/gf_hurl.py.

  f0 held     level on his side, head to the left, boots to the right: how he lies across
              Greyson's fist in the overhead press, and the first beat of the flight. Limp: the
              free arm and the legs hang, the head lolls, the antenna droops, the torn socket up
  f1-f4       the tumble: one full clockwise turn (toward the throw, screen-right) at 90 degree
              steps on the diagonals, every loose part trailing the spin, the torn socket spitting
              a spark on alternate frames, thin motion arcs behind him (his juggle's streaks)

96x96 cells, the body turned about its middle at the cell's centre (48, 48); nothing touches a cell
edge. Nothing is redrawn: every part is the approved rig's (computah_mm), carried by the juggle's
transform (art_source/computah_juggle/jrig.py, imported read-only) so the SHAPES turn and the
cast's upper-left light stays put; the torn socket, its cables and the sparks are computah_armless's
own (armless.py, read-only). Dead eyes and a dead chest, as computah_armless. Keyline #0C111A,
never pure black.

This module only BUILDS frames and writes nothing: armless_tumble_build.py renders, checks and,
only with --ship and only if every check passes, writes the sheet.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
for _p in (HERE, os.path.join(ART, 'computah_juggle')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import armless as A     # noqa: E402  the armless set: the torn socket, cables, sparks
import jrig as J        # noqa: E402  the juggle's transform (read-only)
import poses as JP      # noqa: E402  the juggle's hinged parts (read-only)

M, P = A.M, J.P
assert J.M is M, 'the juggle rig and the armless set must share one computah_mm'

CELL = 96
DEST = (48.0, 48.0)                 # his middle (jrig.COM) sits at the cell's centre
SOCKET_REST = (66.5, 59.0)          # where the cannon's shoulder ball met him, standing
FACE_REST = (0.94, 0.34)            # the way the arm left: out and a little down (armless.FACE)
WOUND_R = 7.6                       # the torn mount (the wrench's tear frame uses 7.6)
STREAK = (0xF2, 0xF8, 0xFF, 255)    # his shell's own highlight, as the juggle's streaks
DEAD = M.CHARGE['dead']


def draw(angle, head, ant, arm, legs, phase=0, sparks=(), dest=DEST, size=CELL):
    """One frame of him, armless: the juggle Pose's parts in its order, minus the cannon, plus the
    torn socket where the cannon was. Limbs are aimed by bearings ON SCREEN (0 right, 90 down).
    -> (canvas, transform, points)."""
    T = J.Tf(angle, dest=dest)
    c = P.Canvas(size, size, M.PAL, M.OUTLINE)
    Th = JP.head_tf(T, *head)
    Tn = J.Tf(T.angle + head[2] * 0.5,
              dest=T.fwd(JP.NECK[0] + head[0] * 0.5, JP.NECK[1] + head[1] * 0.5),
              pivot=JP.NECK, squash=T.sq)
    pts, ball = JP.antenna_chain(Th, ant)
    J.antenna(c, Th, pts, ball, DEAD)
    c.add(J.Shapes(Tn).RR(*JP.NECK_RR, r=3.0, round_r=4.0), 'shell', prio=2)
    with J.placed(T):
        M._torso(c, JP.QUAD, JP.COLLAR, pelvis=JP.PELVIS)
    out = {}
    for i, rest in enumerate((JP.LEG_L, JP.LEG_R)):
        fb, bend = legs[i]
        out['boot_%d' % i] = JP.leg(c, T, rest, fb - T.angle - JP.LEG_REST[i], bend, prio=4)
    ab, abend = arm
    out['hand'] = JP.arm(c, T, ab - T.angle - JP.ARM_REST, abend)
    J.capacitor(c, T, JP.CELL[0], JP.CELL[1], DEAD, cell_w=3, gap=3, bh=6.4, lit=set())
    with J.placed(Th):
        M._helmet(c, JP.HEAD[0], JP.HEAD[1], rx=21.0, ry=13.0, jaw=(11.5, 4.0, 16.5),
                  chin=JP.HEAD[1] + 8.0, pods=(6.0, 6.0), pod_y=5.5, vent=1)
    J.face(c, Th, M.FACE_FRONT, JP.HEAD[0] - 14.0, JP.HEAD[1] - 6.5, J.face_chars(DEAD, 'dead'))
    # the torn shoulder, the cables spilling out of it (they hang: gravity is screen-down)
    sx, sy = T.fwd(*SOCKET_REST)
    fx, fy = T.turn(*FACE_REST)
    hx, hy = A._torn_socket(c, sx, sy, fx, fy, r=WOUND_R, prio=17)
    tips = A._wires(c, hx, hy, fx, fy, phase=phase, prio=26, scale=0.7, sag=True)
    M._finish(c)
    A._spark_tips(c, tips, phase)
    if sparks:
        M._sparks(c, int(round(hx)), int(round(hy)), sparks)
    out['socket'] = (hx, hy)
    out['com'] = T.fwd(*J.COM)
    out['chest'] = T.fwd(*JP.CELL)
    return c, T, out


def grid(c):
    """The finished pixels as rows of RGBA, with any one-texel hole boxed in by keyline on four
    sides closed with keyline (a seam between two parts, not a hole in him)."""
    g = [[(0, 0, 0, 0)] * CELL for _ in range(CELL)]
    for (x, y), col in c.pixels().items():
        g[y][x] = tuple(col)
    key = P._hex(M.OUTLINE)
    for _ in range(2):
        fill = [(x, y) for y in range(1, CELL - 1) for x in range(1, CELL - 1)
                if not g[y][x][3] and all(g[y + dy][x + dx][3]
                                          for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
        for (x, y) in fill:
            g[y][x] = key
    return g


def streak(g, cx, cy, r, a0, a1, ry=None):
    """A thin motion arc (no keyline: it is air, not a part), only over empty cells."""
    ry = r if ry is None else ry
    steps = max(8, int(abs(a1 - a0) * 1.6))
    pts = []
    for i in range(steps + 1):
        a = math.radians(a0 + (a1 - a0) * i / float(steps))
        pts.append((int(round(cx + r * math.cos(a))), int(round(cy + ry * math.sin(a)))))
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        for (x, y) in P.polyline([(x0, y0), (x1, y1)]):
            if 1 <= x < CELL - 1 and 1 <= y < CELL - 1 and not g[y][x][3]:
                g[y][x] = STREAK


def to_image(g):
    from PIL import Image
    im = Image.new('RGBA', (CELL, CELL), (0, 0, 0, 0))
    px = im.load()
    for y in range(CELL):
        for x in range(CELL):
            if g[y][x][3]:
                px[x, y] = g[y][x]
    return im


# ------------------------------------------------------------------------------------ frames

GRIP_REST = (29.5, 66.0)    # the middle of his torso's side edge (the free-arm side), standing:
                            # level in f0 it is his underside, where Greyson's fist holds him up


def extent(g):
    xs = [x for y in range(CELL) for x in range(CELL) if g[y][x][3]]
    ys = [y for y in range(CELL) for x in range(CELL) if g[y][x][3]]
    return min(xs), min(ys), max(xs), max(ys)


TRIAL = 192     # a trial canvas big enough that nothing of him is cut off while he is measured


def centred(make):
    """Measure him on an oversized trial canvas (so nothing is clipped while he is measured),
    then draw him in the cell with his middle moved so the figure is centred in it. At 96 a
    turned helmet reaches the cell's edge from the cell's centre; centring the drawn box keeps a
    margin all round. `make(dest, size)` -> (canvas, transform, points); returns the cell render
    and the dest used. Refuses a pose too big for the cell."""
    off = (TRIAL - CELL) / 2.0
    c, _T, _p = make((DEST[0] + off, DEST[1] + off), TRIAL)
    xy = list(c.pixels())
    x0, x1 = min(p[0] for p in xy) - off, max(p[0] for p in xy) - off
    y0, y1 = min(p[1] for p in xy) - off, max(p[1] for p in xy) - off
    if x1 - x0 > CELL - 3 or y1 - y0 > CELL - 3:
        raise SystemExit('pose is %d x %d texels: too big for a %d cell with a margin; tuck '
                         'the limbs' % (x1 - x0 + 1, y1 - y0 + 1, CELL))
    dest = (DEST[0] + round((CELL - 1) / 2.0 - (x0 + x1) / 2.0),
            DEST[1] + round((CELL - 1) / 2.0 - (y0 + y1) / 2.0))
    c, T, pts = make(dest, CELL)
    return c, T, pts, dest


def held():
    """f0: level across Greyson's fist, limp. Head left, boots right, the free arm hanging bent,
    the legs dangling, the head lolled down, the antenna drooping."""
    def make(dest, size):
        return draw(-90.0, head=(0.0, 0.0, 12.0), ant=(96.0, 84.0, 76.0),
                    arm=(100.0, 80.0), legs=((74.0, 40.0), (34.0, 46.0)), phase=0, dest=dest,
                    size=size)
    c, T, pts, dest = centred(make)
    pts['grip'] = T.fwd(*GRIP_REST)
    pts['dest'] = dest
    return grid(c), pts


# The turn: clockwise, toward the throw. angle, lag (how far every loose limb trails the spin:
# the body turns clockwise, so a trailing limb sits ANTICLOCKWISE of where the body would carry
# it), whether the socket spits a spark. The limbs are tucked (a limp body folds as it spins).
TUMBLE = (
    (-45.0, 18.0, True),
    (45.0, 30.0, False),
    (135.0, 26.0, True),
    (225.0, 14.0, False),
)


def tumble(i):
    ang, lag, spark = TUMBLE[i]
    down = 90.0 + ang                          # the body's own 'down', on screen
    up = down - 180.0                          # and his 'up': the antenna whip trails the spin
                                               # folded back along the helmet, not flung out

    def make(dest, size):
        return draw(ang, head=(0.0, 0.0, -lag * 0.4),
                    ant=(up + 100.0 - lag * 0.5, up + 122.0 - lag * 0.7, up + 142.0 - lag * 0.9),
                    arm=(down + 20.0 - lag, 72.0),
                    legs=((down + 6.0 - lag, 44.0), (down - 20.0 - lag, -44.0)),
                    phase=i % 2, sparks=((5, -4), (-3, -6), (7, 2)) if spark else (), dest=dest,
                    size=size)
    c, T, pts, dest = centred(make)
    g = grid(c)
    a0 = down + 180.0                          # where his head is, on screen
    streak(g, dest[0], dest[1], 44, a0 - 62, a0 - 22, ry=42)
    streak(g, dest[0], dest[1], 44, a0 + 118, a0 + 158, ry=42)
    pts['dest'] = dest
    return g, pts


FRAMES = [('held', held)] + [('tumble_%d' % (i + 1), (lambda i=i: tumble(i))) for i in range(4)]


def render():
    """-> (strip image, [(name, frame image, points)])."""
    from PIL import Image
    frames = []
    for name, fn in FRAMES:
        g, pts = fn()
        frames.append((name, to_image(g), pts))
    sheet = Image.new('RGBA', (CELL * len(frames), CELL), (0, 0, 0, 0))
    for i, (_n, im, _p) in enumerate(frames):
        sheet.paste(im, (CELL * i, 0))
    return sheet, frames
