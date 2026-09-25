"""Computah's juggle poses: twelve frames in Mason's order.

  0-1    HIT     the uppercut lands under his chin: head snapped back, faceplate
                 squeezed shut, mouth agape, sparks off the jaw, feet leaving the
                 mat; then the lift, everything that is not bolted down trailing.
  2-6    TUMBLE  2 is the apex hang, limp and startled, the cannon hanging plumb
                 under its own weight; 3-6 are one full backward turn.  His visor
                 glitches and the chest cells flicker out of order while he spins.
  7-9    CRASH   back-first onto the mat, squashed flat; the bounce; the settle.
  10-11  DOWN    lying there, X-eyed, the last cell pulsing and a wisp of smoke
                 coming off his chest vent -- a robot's breathing.

He turns BACKWARDS (negative, anticlockwise angles).  His sheets are drawn facing
right, so an uppercut to the chin throws his head back to the left and his feet
over to the right, and he comes down on his back with his head to the left.

Every part is the approved rig's own (computah_mm), hinged where a part hinges: the
head on the neck, each leg at the hip and knee, the arm at the shoulder and elbow,
the cannon at its shoulder.  See jrig.py for why the geometry turns rather than
the picture.
"""
import math

import jrig as J
from jrig import M, P

# ------------------------------------------------------------------ rest -----
# build_idle frame 0's own numbers: the pose the approved key frame was drawn in.
# Every juggle pose is these parts, re-hinged -- none of them is redrawn.
HEAD = (47.0, 33.5)
NECK = (47.5, 50.0)                 # where the head tips: the top of the neck column
ANT = [(38.0, 25.0), (30.0, 18.0), (24.0, 13.5)]
BALL = (21.0, 11.4, 4.0)
NECK_RR = (41.0, 46.0, 54.0, 57.0)
QUAD = [(28.0, 55.0), (67.0, 55.0), (62.0, 79.0), (33.0, 79.0)]
COLLAR = (29.0, 53.5, 68.0, 60.5)
PELVIS = (30.0, 69.5, 66.0, 80.0)
LEG_L = ((39.5, 75.0), (37.5, 83.0), (37.0, 89.0), (27.5, 86.5, 46.0, 95.0))
LEG_R = ((55.5, 75.0), (57.5, 83.0), (58.0, 89.0), (49.5, 86.5, 68.0, 95.0))
ARM = ((25.5, 60.0), (19.0, 70.0), (16.8, 80.5))
ARM_CAP = (25.6, 58.5, 7.8, 6.9)
GUN_SH = (65.0, 59.0)
GUN_LEN = math.hypot(83.0 - 65.0, 77.5 - 59.0)
CELL = (47.5, 66.0)

# The frame colour the thin motion streaks are drawn in: the shell's own highlight.
STREAK = (0xF2, 0xF8, 0xFF, 255)


# ------------------------------------------------------------ the parts ------
ARM_REST = 113.0          # bearing of the rest arm, shoulder -> wrist, in his frame
LEG_REST = (100.1, 79.9)  # left and right leg, hip -> ankle
ANT_BASE = (38.0, 25.0)


def bearing(a, b):
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def leg(c, T, rest, swing=0.0, bend=0.0, prio=4, far=False, r=(7.0, 6.0, 5.2)):
    """M._leg, hinged: the thigh turns `swing` degrees at the hip, and the shin and
    boot turn a further `bend` at the knee.  Each piece is drawn in its own rest
    orientation, so the knee crease and the boot's sole stay where the rig puts
    them on the limb."""
    hip, knee, ankle, foot = rest
    Tt = T.sub(hip, swing)
    Ts = Tt.sub(knee, bend)
    St, Ss = J.Shapes(Tt), J.Shapes(Ts)
    limb = P.Union([St.CAP(hip, knee, r[0], r[1]), Ss.CAP(knee, ankle, r[1], r[2])],
                   k=1.6 * M.K)
    c.add(limb, "shell", prio=prio, bias=2 if far else 0)
    c.add(Ss.RR(foot[0], foot[1], foot[2], foot[3], r=5.0, round_r=6.0), "armour",
          prio=prio + 1, bias=3 if far else 2)
    if not far:
        c.contour(limb, width=1.4, delta=3, mats=("shell", "armour"),
                  below_prio=prio)
    c.shade_px(St.SPAN(knee[0] - 3, knee[0] + 3, knee[1] - 1), 2, "shell")
    c.shade_px(Ss.SPAN(foot[0] + 1, foot[2] - 1, foot[1] + 2), 2, "armour")
    c.shade_px(Ss.SPAN(foot[0], foot[2], foot[3] - 1), 3, "armour")
    c.shade_px(Ss.SPAN(foot[0], foot[2], foot[3]), 4, "armour")
    return Ts.fwd((foot[0] + foot[2]) / 2.0, foot[3])


def arm(c, T, swing=0.0, bend=0.0, prio=6):
    """M._arm, hinged at the shoulder and the elbow.  The pauldron stays on the
    body: it is bolted to the shoulder, not to the arm."""
    sh, elbow, wrist = ARM
    Tu = T.sub(sh, swing)
    Tl = Tu.sub(elbow, bend)
    Su, Sl, Sb = J.Shapes(Tu), J.Shapes(Tl), J.Shapes(T)
    upper = Su.CAP(sh, elbow, 5.8, 4.9)
    lower = Sl.CAP(elbow, wrist, 4.9, 4.2)
    c.add(P.Union([upper, lower], k=1.6 * M.K), "shell", prio=prio)
    c.add(Sl.E(wrist[0], wrist[1], 5.3, 5.3 * 0.92), "shell", prio=prio + 2, bias=0)
    c.add(Sb.E(*ARM_CAP), "armour", prio=prio + 3, bias=2)
    c.shade_px(Su.SPAN(elbow[0] - 2, elbow[0] + 2, elbow[1]), 2, "shell")
    c.shade_px(Sl.SPAN(wrist[0] - 3, wrist[0] + 3, wrist[1] + 2), 2, "shell")
    c.shade_px(Sl.SPAN(wrist[0] - 3, wrist[0] + 3, wrist[1] - 4), 3, "shell")
    c.shade_px(Sl.SPAN(wrist[0] - 3, wrist[0] + 1, wrist[1] - 2), -2, "shell")
    return Tl.fwd(*wrist)


def muzzle_at(frame_deg, T, reach=GUN_LEN):
    """The barrel's far end, pointing along a bearing ON SCREEN (0 right, 90 down)."""
    return T.aim(GUN_SH, frame_deg, reach)


def head_tf(T, dx=0.0, dy=0.0, tilt=0.0, squash=None):
    """The head, tipped `tilt` degrees on the neck and shifted (dx, dy) with it.
    `squash` defaults to the body's; a rigid helmet passes (1, 1)."""
    return J.Tf(T.angle + tilt, dest=T.fwd(NECK[0] + dx, NECK[1] + dy), pivot=NECK,
                squash=T.sq if squash is None else squash)


def antenna_chain(Th, frame_degs):
    """The antenna's three segments and its ball, each segment laid along a bearing
    ON SCREEN.  Same segment lengths as the rest antenna; it is a whip with a
    weight on the end, so it trails and flops rather than turning with the head."""
    lens = (math.hypot(8.0, 7.0), math.hypot(6.0, 4.5), math.hypot(3.0, 2.1))
    pts = [ANT_BASE]
    for L, d in zip(lens, frame_degs):
        pts.append(Th.aim(pts[-1], d, L))
    ball = pts.pop()
    return pts, (ball[0], ball[1], BALL[2])


class Pose(object):
    """One frame of him.  Every limb is aimed by a bearing ON SCREEN, because that
    is how the frame has to read: a limp limb hangs the way gravity points and a
    trailing limb lags the turn, whatever angle his body is at."""

    def __init__(self, angle, dest, squash=(1.0, 1.0), head=(0.0, 0.0, 0.0),
                 ant=(200.0, 200.0, 200.0), arm=(150.0, 0.0), gun=30.0,
                 legs=((100.0, 0.0), (80.0, 0.0)), far=(False, False), cc=None,
                 lit=None, face=None, mood="calm", gun_prio=16, face_cc=None,
                 head_sq=None):
        self.T = J.Tf(angle, dest=dest, squash=squash)
        self.head, self.ant, self.arm_, self.gun = head, ant, arm, gun
        self.legs, self.far = legs, far
        self.cc = cc or M.CHARGE["full"]
        self.lit, self.face, self.mood, self.gun_prio = lit, face, mood, gun_prio
        self.face_cc = face_cc or self.cc
        self.head_sq = head_sq
        self.pts = {}

    def draw(self):
        T = self.T
        c = J.canvas()
        Th = head_tf(T, *self.head, squash=self.head_sq)
        Tn = J.Tf(T.angle + self.head[2] * 0.5,
                  dest=T.fwd(NECK[0] + self.head[0] * 0.5, NECK[1] + self.head[1] * 0.5),
                  pivot=NECK, squash=T.sq)
        pts, ball = antenna_chain(Th, self.ant)
        J.antenna(c, Th, pts, ball, self.cc)
        c.add(J.Shapes(Tn).RR(*NECK_RR, r=3.0, round_r=4.0), "shell", prio=2)
        with J.placed(T):
            M._torso(c, QUAD, COLLAR, pelvis=PELVIS)
        for i, rest in enumerate((LEG_L, LEG_R)):
            fb, bend = self.legs[i]
            self.pts['boot_%d' % i] = leg(c, T, rest, fb - T.angle - LEG_REST[i], bend,
                                          prio=4, far=self.far[i])
        ab, abend = self.arm_
        self.pts['hand'] = arm(c, T, ab - T.angle - ARM_REST, abend)
        mz = muzzle_at(self.gun, T)
        self.pts['muzzle'] = T.fwd(*J.cannon(c, T, GUN_SH, mz, r=8.0,
                                             prio=self.gun_prio))
        J.capacitor(c, T, CELL[0], CELL[1], self.cc, cell_w=3, gap=3, bh=6.4,
                    lit=self.lit)
        with J.placed(Th):
            M._helmet(c, HEAD[0], HEAD[1], rx=21.0, ry=13.0, jaw=(11.5, 4.0, 16.5),
                      chin=HEAD[1] + 8.0, pods=(6.0, 6.0), pod_y=5.5, vent=1)
        J.face(c, Th, self.face or M.FACE_FRONT, HEAD[0] - 14.0, HEAD[1] - 6.5,
               J.face_chars(self.face_cc, self.mood))
        M._finish(c)
        self.pts['chin'] = Th.fwd(47.5, 51.0)
        self.pts['vent'] = T.fwd(47.5, 57.0)
        self.pts['chest'] = T.fwd(*CELL)
        self.pts['com'] = T.fwd(*J.COM)
        return c


# --------------------------------------------------------------- faces -------
# His face plate is 28x14: rows 0 and 13 the lit rim, eyes in columns 3-8 and
# 19-24 on rows 1-6, the grin on rows 8-11.  Every juggle face is drawn on that same
# plate in the same characters, so it is still HIS face -- only the LEDs change.
def _plate():
    g = [["V"] * 28 for _ in range(14)]
    g[0] = ["v"] * 28
    g[13] = ["v"] * 28
    return g


def _put(g, pts, ch, mirror=True):
    for (x, y) in pts:
        g[y][x] = ch
        if mirror:
            g[y][27 - x] = ch


def _rows(g):
    return ["".join(r) for r in g]


def _grin(g, dy=0):
    """His own grin (FACE_FRONT rows 8-11), optionally dropped by dy rows."""
    src = M.FACE_FRONT
    for y in range(8, 12):
        for x in range(28):
            if src[y][x] in "Mt":
                g[y + dy][x] = src[y][x]


# OUCH: the frame the fist lands.  Eyes squeezed shut as white-hot chevrons
# (the `hit` mood's own white and fringe), mouth wrenched open with the top teeth
# showing.
def face_ouch():
    g = _plate()
    _put(g, [(3, 1), (4, 1), (4, 2), (5, 2), (6, 2), (6, 3), (7, 3), (8, 3),
             (6, 4), (7, 4), (8, 4), (4, 5), (5, 5), (6, 5), (3, 6), (4, 6)], "W")
    _put(g, [(5, 1), (7, 2), (5, 6), (7, 5)], "Y")
    for y in (8, 9, 10, 11, 12):
        lo = 7 if y in (8, 12) else 5
        _put(g, [(x, y) for x in range(lo, 14)], "M")
    _put(g, [(7, 9), (9, 9), (11, 9), (13, 9)], "t")      # top teeth
    _put(g, [(8, 11), (10, 11), (12, 11)], "t")           # bottom teeth
    return _rows(g)


# SHOCK: the apex.  Round hollow "O" eyes and a small round mouth -- limp and
# startled, the beat before he starts to turn.
def face_shock():
    g = _plate()
    ring = [(4, 1), (5, 1), (6, 1), (7, 1), (3, 2), (8, 2), (3, 3), (8, 3), (3, 4),
            (8, 4), (3, 5), (8, 5), (4, 6), (5, 6), (6, 6), (7, 6)]
    _put(g, ring, "R")
    _put(g, [(4, 2), (7, 2), (4, 5), (7, 5)], "G")
    _put(g, [(12, 8), (13, 8), (11, 9), (11, 10), (12, 11), (13, 11)], "t")
    _put(g, [(12, 9), (13, 9), (12, 10), (13, 10)], "M")
    return _rows(g)


# GLITCH: the tumble.  The eye bars tear across the scanlines and a green scan
# line crawls over the plate -- his visor losing sync while he spins.  Three
# variants, so the loop does not stamp the same face every quarter turn.
def _eyes(g, shift=None):
    shift = shift or {}
    for (x0, x1) in ((3, 8), (19, 24)):
        for y in range(1, 7):
            d = shift.get((x0, y), 0)
            for x in range(x0, x1 + 1):
                edge = x in (x0, x1) or y in (1, 6)
                if 0 <= x + d < 28:
                    g[y][x + d] = "G" if edge else "R"


def face_glitch(k):
    g = _plate()
    if k == 0:
        _eyes(g, {(3, 3): 2, (3, 4): 2, (19, 2): -2, (19, 3): -2})
        for x in range(2, 26):
            if g[5][x] == "V":
                g[5][x] = "g"
        _grin(g)
        for x in (6, 15):
            g[10][x] = "M"
    elif k == 1:
        for (x0, x1) in ((3, 8), (19, 24)):
            for x in range(x0, x1 + 1):
                g[3][x] = "R"
                g[4][x] = "R"
                g[2][x] = "G"
                g[5][x] = "G"
        for x in range(4, 24, 3):
            g[7][x] = "c"
        _grin(g)
    else:
        _eyes(g, {(3, 1): -1, (3, 2): -1, (19, 4): 2, (19, 5): 2})
        for x in range(6, 22):
            if g[2][x] == "V":
                g[2][x] = "g"
        _grin(g, 1)
        g[9][20] = "M"
    return _rows(g)


# PAIN: the crash.  Red chevrons squeezed shut and the grin clenched into a full
# row of gritted teeth.
def face_pain():
    g = _plate()
    _put(g, [(3, 1), (4, 1), (4, 2), (5, 2), (6, 2), (6, 3), (7, 3), (8, 3),
             (6, 4), (7, 4), (8, 4), (4, 5), (5, 5), (6, 5), (3, 6), (4, 6)], "R")
    _put(g, [(5, 1), (7, 2), (5, 6), (7, 5)], "G")
    for y in (8, 9, 10):
        _put(g, [(x, y) for x in range(5, 14)], "M")
    _put(g, [(x, 9) for x in range(6, 14, 2)], "t")
    return _rows(g)


# KO: X eyes, and his grin knocked lopsided -- the right half has slipped a row.
def face_ko():
    g = _plate()
    x_eye = [(3, 1), (8, 1), (4, 2), (7, 2), (5, 3), (6, 3), (5, 4), (6, 4), (4, 5),
             (7, 5), (3, 6), (8, 6)]
    glow = {(x + dx, y + dy) for (x, y) in x_eye for dx, dy in ((1, 0), (-1, 0))
            if 3 <= x + dx <= 8} - set(x_eye)
    _put(g, sorted(glow), "G")
    _put(g, x_eye, "R")
    src = M.FACE_FRONT
    for y in range(8, 12):
        for x in range(28):
            if src[y][x] in "Mt":
                yy = y + (1 if x >= 14 else 0)
                g[yy][x] = src[y][x]
    return _rows(g)


FACE_OUCH = face_ouch()
FACE_SHOCK = face_shock()
FACE_GLITCH = [face_glitch(k) for k in range(3)]
FACE_PAIN = face_pain()
FACE_KO = face_ko()


# ------------------------------------------------------------- effects -------
def to_grid(c):
    """The finished frame.  A one-texel hole left where two parts' keylines meet
    with a single texel between them is closed with keyline: it is a seam, and at
    3x a transparent pinhole in the middle of him reads as a hole in the armour."""
    g = J.to_grid(c)
    key = P._hex(J.OUTLINE)
    for _ in range(2):
        fill = [(x, y) for y in range(1, J.H - 1) for x in range(1, J.W - 1)
                if not g[y][x][3]
                and all(g[y + dy][x + dx][3] for dx, dy in ((1, 0), (-1, 0), (0, 1),
                                                            (0, -1)))]
        for (x, y) in fill:
            g[y][x] = key
    return g


def streak(g, cx, cy, r, a0, a1, ry=None, col=STREAK):
    """A thin motion arc on the finished frame (no keyline: it is air, not a part)."""
    ry = r if ry is None else ry
    steps = max(8, int(abs(a1 - a0) * 1.6))
    pts = []
    for i in range(steps + 1):
        a = math.radians(a0 + (a1 - a0) * i / steps)
        pts.append((int(round(cx + r * math.cos(a))), int(round(cy + ry * math.sin(a)))))
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        for (x, y) in P.polyline([(x0, y0), (x1, y1)]):
            if 0 <= x < J.W and 0 <= y < J.H and not g[y][x][3]:
                g[y][x] = col


def line(g, pts, col=STREAK):
    for (x, y) in P.polyline([(int(a), int(b)) for (a, b) in pts]):
        if 0 <= x < J.W and 0 <= y < J.H and not g[y][x][3]:
            g[y][x] = col


# ---------------------------------------------------------------- poses ------
def _extent(c):
    pts = [(x, y) for y in range(J.H) for x in range(J.W)
           if c.mat[y][x] is not None or c.raw[y][x] is not None]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def grounded(make, row=143, x_mid=96.0, guess=(96.0, 80.0)):
    """Build a pose, measure where it really ends, and slide it so its lowest drawn
    texel sits on `row` and its drawn middle on `x_mid`.  The trial render is made at
    `guess`, high enough that nothing is cut off by the frame edge while it is being
    measured -- a clipped trial reads as already on the floor and sinks him into it."""
    trial = make(guess)
    x0, y0, x1, y1 = _extent(trial.draw())
    if y1 >= J.H - 2 or y0 <= 1 or x0 <= 1 or x1 >= J.W - 2:
        raise SystemExit('trial render touches the frame edge; move its guess')
    dx = round(x_mid - (x0 + x1) / 2.0)
    dy = row - (y1 + 1)                       # +1: the keyline under the last fill
    pose = make((guess[0] + dx, guess[1] + dy))
    return pose, pose.draw()


def mat_dust(c, x, row=141):
    """A kick of mat dust whose flat bottom sits on the mat."""
    M._dust(c, int(round(x)), row - 1)


def sparks_at(c, p, pts):
    M._sparks(c, int(round(p[0])), int(round(p[1])), pts)


def launch():
    """0: the fist lands under his chin.  Head snapped back, face squeezed shut,
    mouth agape; arms flung out and down, knees buckling, boots just off the mat."""
    def make(dest):
        return Pose(-2.0, dest, head=(-4.0, -5.0, -6.0),
                    ant=(150.0, 125.0, 115.0),
                    arm=(145.0, 25.0), gun=18.0,
                    legs=((116.0, -30.0), (62.0, 30.0)),
                    face=FACE_OUCH, mood="hit", lit={0, 1, 3})
    p, c = grounded(make, row=140)
    chin = p.pts['chin']
    sparks_at(c, chin, ((-12, 1), (-7, 7), (0, 10), (7, 7), (12, 1), (-16, -5),
                        (16, -5)))
    mat_dust(c, p.pts['boot_0'][0] - 14)
    mat_dust(c, p.pts['boot_1'][0] + 14)
    g = to_grid(c)
    cx, cy = chin
    for d in (200, 235, 305, 340):
        a = math.radians(d)
        line(g, [(cx + math.cos(a) * 17, cy + math.sin(a) * 17 + 8),
                 (cx + math.cos(a) * 25, cy + math.sin(a) * 25 + 8)])
    return g


def launch_lift():
    """1: off the mat and tipping back.  Everything loose trails below him."""
    p = Pose(-30.0, (94.0, 82.0), squash=(0.95, 1.07), head=(-1.0, -2.0, -10.0),
             ant=(150.0, 120.0, 105.0),
             arm=(128.0, 14.0), gun=34.0,
             legs=((108.0, -16.0), (72.0, 14.0)),
             face=FACE_OUCH, mood="hit", lit={0, 2})
    c = p.draw()
    for b in (p.pts['boot_0'], p.pts['boot_1']):
        sparks_at(c, (b[0], b[1] + 10), ((0, 0),))
    mat_dust(c, 70)
    mat_dust(c, 124)
    g = to_grid(c)
    for x in (80, 96, 112):
        line(g, [(x, 128), (x, 138)])
    return g


def hang():
    """2: the apex, and the loop's slow beat.  He hangs level on his back, limp and
    startled: the free arm hangs plumb under gravity, the heavy cannon has flopped
    back past his head, the legs dangle and the antenna droops."""
    p = Pose(-90.0, (98.0, 78.0), head=(0.0, 0.0, 0.0),
             ant=(120.0, 100.0, 92.0),
             arm=(92.0, 8.0), gun=222.0,
             legs=((52.0, 24.0), (2.0, 34.0)),
             face=FACE_SHOCK, mood="calm", lit={0, 1})
    c = p.draw()
    g = to_grid(c)
    for (x, y) in ((58, 34), (62, 28), (138, 36), (134, 30), (40, 64), (156, 60)):
        if not g[y][x][3]:
            g[y][x] = STREAK
    return g


# The turn.  angle, where his middle sits, and LAG: how far every loose limb
# trails the turn.  The body turns anticlockwise (backwards), so a trailing limb sits
# clockwise of where the body would carry it.  It grows through the fast bottom of
# the turn and comes back as he slows into the next hang.
TUMBLE = (
    (-135.0, (96.0, 78.0), 22.0, 0, {1, 2}),
    (-225.0, (96.0, 80.0), 34.0, 1, {0, 3}),
    (-315.0, (96.0, 80.0), 30.0, 2, {2}),
    (-405.0, (96.0, 78.0), 16.0, 0, {0, 1, 2}),
)


def _tumble(i):
    ang, dest, lag, fk, lit = TUMBLE[i]
    down = 90.0 + ang                          # the body's own 'down', on screen
    p = Pose(ang, dest, head=(0.0, 0.0, lag * 0.4),
             ant=(down + 132.0 + lag, down + 150.0 + lag * 1.4,
                  down + 165.0 + lag * 1.8),
             arm=(down + 62.0 + lag, 18.0), gun=down - 80.0 + lag,
             legs=((down + 26.0 + lag, -22.0), (down - 26.0 + lag, 22.0)),
             face=FACE_GLITCH[fk], mood="calm", lit=lit)
    c = p.draw()
    if i in (1, 3):
        n = p.T.fwd(*NECK)
        sparks_at(c, n, ((-10, 3), (9, -4)) if i == 1 else ((8, 6), (-9, -5)))
    g = to_grid(c)
    a0 = down + 180.0                          # where his head is, on screen
    streak(g, dest[0], dest[1], 58, a0 + 20, a0 + 62, ry=54)
    streak(g, dest[0], dest[1], 58, a0 + 200, a0 + 242, ry=54)
    return g


def tumble_a():
    return _tumble(0)


def tumble_b():
    return _tumble(1)


def tumble_c():
    return _tumble(2)


def tumble_d():
    return _tumble(3)


# Where he comes down, across the frame.  An uppercut knocks him BACKWARDS, so he
# lands behind the spot he was standing on -- his head away from the player, his
# boots near where his feet were -- not centred on it, which would put his legs
# under a player standing in front of him.
LIE_MID = 80.0


def lying(angle, squash, head, ant, arm, gun, legs, face, mood, cc, lit, row=143,
          face_cc=None, head_sq=(1.0, 1.0)):
    """He is a robot: on the mat his helmet stays rigid (head_sq), whatever the
    chassis is doing, so his face plate maps texel for texel at a quarter turn."""
    def make(dest):
        return Pose(angle, dest, squash=squash, head=head, ant=ant, arm=arm, gun=gun,
                    legs=legs, cc=cc, lit=lit, face=face, mood=mood, face_cc=face_cc,
                    head_sq=head_sq)
    return grounded(make, row=row, x_mid=LIE_MID, guess=(96.0, 84.0))


def crash():
    """7: back-first into the mat, and he pancakes.  Limbs slapped out flat."""
    p, c = lying(-96.0, (1.14, 0.74), (-2.0, 0.0, -10.0), (170.0, 150.0, 140.0),
                 (160.0, 10.0), -48.0, ((16.0, 0.0), (-14.0, 0.0)),
                 FACE_PAIN, "calm", M.CHARGE["half"], {0, 1}, head_sq=(1.14, 0.74))
    x0, _, x1, _ = _extent(c)
    mat_dust(c, x0 + 4)
    mat_dust(c, x1 - 4)
    sparks_at(c, (p.pts['com'][0], 138), ((-12, 0), (12, 0), (-5, -4), (5, -4)))
    g = to_grid(c)
    for (a, b) in (((x0 - 2, 132), (x0 - 12, 126)), ((x1 + 2, 132), (x1 + 12, 126)),
                   ((x0 - 3, 138), (x0 - 14, 136)), ((x1 + 3, 138), (x1 + 14, 136))):
        line(g, [a, b])
    return g


def crash_bounce():
    """8: the bounce.  He comes off the mat once and everything loose flies up."""
    p, c = lying(-92.0, (1.03, 0.94), (-2.0, -1.0, -14.0), (200.0, 215.0, 230.0),
                 (104.0, 30.0), -64.0, ((-18.0, -10.0), (-40.0, 10.0)),
                 FACE_PAIN, "calm", M.CHARGE["half"], {0}, row=131)
    x0, _, x1, _ = _extent(c)
    mat_dust(c, x0 - 4)
    mat_dust(c, x1 + 4)
    return to_grid(c)


def crash_settle():
    """9: down, and done."""
    p, c = lying(-90.0, (1.04, 0.94), (-2.0, 1.0, 0.0), (160.0, 120.0, 100.0),
                 (172.0, -10.0), -28.0, ((12.0, 0.0), (-10.0, 0.0)),
                 FACE_KO, "calm", M.CHARGE["low"], {0}, face_cc=M.CHARGE["full"])
    x0, _, x1, _ = _extent(c)
    mat_dust(c, x0 - 2)
    return to_grid(c)


def down(k):
    """10-11: lying there.  The only things still moving: the chest rising on a
    breath, the last red cell pulsing, and a wisp of smoke off the chest vent."""
    sq = ((1.0, 1.0), (1.0, 1.04))[k]
    p, c = lying(-90.0, sq, (-2.0, 1.0, 0.0), (160.0, 120.0, 100.0),
                 (172.0, -10.0), -28.0, ((12.0, 0.0), (-10.0, 0.0)),
                 FACE_KO, "calm", M.CHARGE["low"], ({0}, set())[k],
                 face_cc=M.CHARGE["full"])
    m = p.pts['muzzle']
    M._steam(c, int(round(m[0])) + 1, int(round(m[1])) - 2, phase=k)
    return to_grid(c)


def down_rest():
    return down(0)


def down_breathe():
    return down(1)


# name, builder, suggested hold (s)
FRAMES = [
    ("launch_contact", launch, 0.06),
    ("launch_lift", launch_lift, 0.08),
    ("hang", hang, 0.16),
    ("tumble_a", tumble_a, 0.07),
    ("tumble_b", tumble_b, 0.07),
    ("tumble_c", tumble_c, 0.07),
    ("tumble_d", tumble_d, 0.07),
    ("crash_impact", crash, 0.06),
    ("crash_bounce", crash_bounce, 0.08),
    ("crash_settle", crash_settle, 0.12),
    ("down_rest", down_rest, 0.40),
    ("down_breathe", down_breathe, 0.40),
]
assert len(FRAMES) == 12

TAGS = {
    "launch": (0, 1, False),
    "tumble": (2, 6, True),
    "crash": (7, 9, False),
    "down": (10, 11, True),
}


def replay_build_hit0():
    """M.build_hit(0), statement for statement, drawn through the juggle machinery
    at angle 0 and offset (48, 48).  jrig.check_identity() crops it back out and
    compares it with the rig's own frame."""
    c = J.canvas()
    T = J.Tf(0.0, pivot=(0.0, 0.0), dest=(48.0, 48.0))
    cc = M.CHARGE["full"]
    t, s = -6.0, 7.5
    with J.placed(T):
        J.antenna(c, T, [(38 + t, 25), (30 + t * 2.0, 18), (24.0 + t * 2.6, 14)],
                  (21.0 + t * 2.8, 12.0, 4.0), cc)
        c.add(M.RR(41 + t * 0.6, 46, 54 + t * 0.6, 57, r=3.0, round_r=4.0), "shell",
              prio=2)
        M._torso(c, [(28.0 + t * 0.7, 55.0), (67.0 + t * 0.7, 55.0), (62.0, 79.0),
                     (33.0, 79.0)],
                 (29.0 + t * 0.7, 53.5, 68.0 + t * 0.7, 60.5),
                 pelvis=(30.0, 69.5, 66.0, 80.0))
        M._leg(c, (39.5, 75), (36.5, 83), (35.5, 89), (25.5, 86.5, 44.0, 95.0), prio=4)
        M._leg(c, (55.5, 75), (58.5, 83), (59.5, 89), (51.5, 86.5, 70.0, 95.0), prio=4)
        M._arm(c, (25.5 + t * 0.4, 60.0), (17.5 - s * 0.5, 67.0 - s),
               (14.0 - s * 0.8, 75.0 - s * 1.4), hand_r=5.3, r0=5.8, r1=4.9, r2=4.2,
               prio=6, cap=(25.6 + t * 0.4, 58.5, 7.8, 6.9))
        J.cannon(c, T, (65.0 + t * 0.4, 59.0), (86.0 + s * 0.4, 72.0 - s * 1.6),
                 r=8.0, prio=16)
        J.capacitor(c, T, 47.5 + t * 0.4, 66.0, cc, cell_w=3, gap=3, bh=6.4)
        M._helmet(c, 47.0 + t, 33.5, rx=21.0, ry=13.0, jaw=(11.5, 4.0, 16.5),
                  chin=41.5, pods=(6.0, 6.0), pod_y=5.5, vent=1)
        J.face(c, T, M.FACE_BLINK, 33.0 + t, 27.0, J.face_chars(cc, "hit"))
    M._finish(c)
    with J.placed(T):
        M._sparks(c, 47, 24, ((-12, -3), (-9, -6), (-14, -8), (11, -3), (14, -6),
                              (9, -8), (-3, -9), (3, -11)))
    return c.to_image()
