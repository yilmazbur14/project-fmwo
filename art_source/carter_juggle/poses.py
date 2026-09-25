"""Carter's juggle poses: twelve frames in Mason's order, on the approved three-quarter rig.

  0-1    HIT     the uppercut lands under his beard: the serious Saitama deadpan breaks -- the glowing
                 slits snap open into round white shocked eyes with pinprick pupils, the jaw drops --
                 arms flung, knees gone, heels leaving the mat; then the lift.
  2-6    TUMBLE  2 is the apex hang, level on his back and limp; 3-6 one backward turn with a twist in
                 it, so his back comes round to the camera on 5 and 6 and the 天 shows.  His pupils
                 roll round his eyes as he spins.
  7-9    CRASH   back-first onto the mat, squashed; the bounce; the settle.
  10-11  DOWN    lying there, X-eyed, tongue out, chest rising and falling.

THE AURA IS OFF throughout: the uppercut has knocked him out of the demon state (the brief's call,
and the art agrees -- the eyes' red glow goes with it).

He turns BACKWARDS (negative, anticlockwise angles): drawn facing right, an uppercut throws his head
back to the left, and he comes down on his back with his head to the left.
"""
import math

import kjrig as K
import body as B
from kjrig import L, FC

PIVOT = (48.0, 68.0)                 # his middle: between the chest and the pelvis
UPPER, FORE, FIST = 10.3, 9.5, 3.7   # the approved poses' own arm lengths
THIGH, SHIN = 11.9, 8.8              # and leg lengths

# The standing three-quarter body the juggle poses are built from: DEFEAT[1]'s own torso, shoulders
# and hips (the approved rig's nearest standing pose), facing right.
CHEST = (48.8, 61.6, 10.8)
PELVIS = (47.1, 75.8, 8.6)
SH_NEAR, SH_FAR = (53.8, 62.4), (43.7, 62.4)
HIP_LEAD, HIP_REAR = (51.3, 76.7), (42.9, 76.7)
HEAD_AT = (-1, 5)

# HIS BACK, turned flat to the camera, for the two frames of the turn that show the 天.  The three-
# quarter torso is only ~21px across and its shoulder caps sit on the shoulder blades, so the mark
# would come out in fragments (as it does on the approved rush pass); squared to the camera the back
# is as broad as the approved back view's, the caps ride its edges, and the mark artist's rig fits the
# whole 天 between them.
BACK_CHEST = (47.5, 62.0, 16.0)
BACK_PELVIS = (47.5, 76.0, 11.5)
BACK_SH = ((47.5 + 18.5, 59.0), (47.5 - 18.5, 59.0))       # near (his right), far
BACK_HIP = ((47.5 + 5.5, 78.0), (47.5 - 5.5, 78.0))
BACK_HEAD = (0, 0)


# ------------------------------------------------------------------ faces
EYE_BOX_L = [(x, y) for y in range(37, 42) for x in range(38, 45)]


def _blank_eyes(px):
    """The slits, lashes and lids gone: skin under the brow."""
    for (x, y) in EYE_BOX_L:
        for xx in (x, 95 - x):
            if (xx, y) in px and (y > 37 or px[(xx, y)] in 'kMOV789'):
                px[(xx, y)] = 'v' if y == 38 else 'u'
    return px


def _put(px, pts, key, mirror=True):
    for (x, y) in pts:
        px[(x, y)] = key
        if mirror:
            px[(95 - x, y)] = key


RING = [(40, 37), (41, 37), (42, 37), (39, 38), (43, 38), (39, 39), (43, 39), (39, 40), (43, 40),
        (40, 41), (41, 41), (42, 41)]
WHITE = [(40, 38), (41, 38), (42, 38), (40, 39), (41, 39), (42, 39), (40, 40), (41, 40), (42, 40)]


def face_shock(pupil=(0, 0), jaw=2):
    """The deadpan broken: round white eyes, a pinprick of the red left in each, the jaw dropped.
    `pupil` (dx, dy) moves both pupils the same way on screen (they roll together)."""
    px = FC.head_part(0, jaw, 0, 0)
    _blank_eyes(px)
    _put(px, RING, 'k')
    _put(px, WHITE, 'M')
    dx, dy = pupil
    px[(41 + dx, 39 + dy)] = '8'
    px[(54 + dx, 39 + dy)] = '8'
    return px


def face_squeeze(jaw=2):
    """The crash: both eyes screwed shut, > <."""
    px = FC.head_part(0, jaw, 0, 0)
    _blank_eyes(px)
    _put(px, [(39, 38), (40, 38), (41, 39), (42, 39), (43, 39), (41, 40), (42, 40), (43, 40),
              (39, 41), (40, 41)], 'k')
    return px


def face_ko(tongue=True):
    """Out cold: an X in each round white eye -- the red glow gone out of them -- and his tongue
    lolled out of the open jaw, down over the beard."""
    px = FC.head_part(0, 2, 0, 0)
    _blank_eyes(px)
    _put(px, RING, 'k')
    _put(px, WHITE, 'M')
    _put(px, [(40, 38), (42, 38), (41, 39), (40, 40), (42, 40)], 'k')
    if tongue:
        L.patch(px, [(47, 45, "WWVVWW"), (48, 46, "VVVV"), (49, 46, "kVV7k"),
                     (50, 47, "kV7k"), (51, 47, "kkkk")])
    return px


# ------------------------------------------------------------------ building a pose
def _aim(T, root, deg, ln):
    """A point `ln` from `root` (his own space) along a bearing ON SCREEN."""
    a = math.radians(deg)
    ux, uy = T.unturn(math.cos(a), math.sin(a))
    return (root[0] + ux * ln, root[1] + uy * ln)


def arm(T, sh, deg_up, deg_fore):
    el = _aim(T, sh, deg_up, UPPER)
    wr = _aim(T, el, deg_fore, FORE)
    fi = _aim(T, wr, deg_fore, FIST)
    return (sh, el, wr, fi)


def leg(T, hip, deg_thigh, deg_shin, toe=None):
    """A leg aimed on screen.  `toe` is the foot's bearing on screen; by default the foot hangs off the
    shin's end, pointed (a limp foot plantar-flexes)."""
    kn = _aim(T, hip, deg_thigh, THIGH)
    an = _aim(T, kn, deg_shin, SHIN)
    toe = deg_shin - 58.0 if toe is None else toe
    return (hip, kn, an, toe - T.angle)


class Pose(object):
    def __init__(self, angle, dest, squash=(1.0, 1.0), chest=None, pelvis=None,
                 head=HEAD_AT, face=None, head_turn=0.0, back=False,
                 near=(110.0, 110.0), far=(70.0, 70.0), lead=(90.0, 90.0, None),
                 rear=(90.0, 90.0, None), sway=0.0):
        self.T = K.Tf(angle, dest=dest, pivot=PIVOT, squash=squash)
        T = self.T
        if back:
            sh_n, sh_f = BACK_SH
            hp_l, hp_r = BACK_HIP
            chest, pelvis, head = BACK_CHEST, BACK_PELVIS, BACK_HEAD
        else:
            sh_n, sh_f, hp_l, hp_r = SH_NEAR, SH_FAR, HIP_LEAD, HIP_REAR
        self.p = dict(
            head=head, face=(0, 0), chest=chest or CHEST, pelvis=pelvis or PELVIS,
            near=arm(T, sh_n, near[0], near[1]),
            far=arm(T, sh_f, far[0], far[1]),
            lead=leg(T, hp_l, lead[0], lead[1], lead[2]),
            rear=leg(T, hp_r, rear[0], rear[1], rear[2]),
            tails=None, sway=sway, back=back, mark_clear=back)
        self.head = dict(part=face, turn=head_turn) if (face is not None or head_turn) else None
        self.pts = {}

    def draw(self, floor=None):
        cv = seal(B.draw(self.p, self.T, head=self.head, floor=floor))
        T = self.T
        hx, hy = self.p['head']
        self.pts['chin'] = T.fwd(47.5 + hx, 51.0 + hy)
        self.pts['com'] = T.fwd(*PIVOT)
        return cv


def seal(cv):
    """Close what turning him opens up, before any effect is drawn.  (1) An edge of him that the rig
    never had to keyline -- the neck plug under a tipped head pokes past the silhouette -- gets its
    1px keyline outside it, the way lib.Canvas.stamp keylines every part.  (2) A one-texel hole where
    two parts' keylines meet with a single texel between them becomes keyline: it is a seam."""
    px = cv.px

    def inside(q):
        return 0 <= q[0] < K.W and 0 <= q[1] < K.H

    add = set()
    for (x, y), k in px.items():
        if k == 'k' or not inside((x, y)):
            continue
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in px and inside(q):
                add.add(q)
    for q in add:
        px[q] = 'k'
    for _ in range(2):
        holes = [(x, y) for y in range(1, K.H - 1) for x in range(1, K.W - 1)
                 if (x, y) not in px and all((x + dx, y + dy) in px
                                             for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
        for q in holes:
            px[q] = 'k'
    return cv


# ------------------------------------------------------------------ helpers for effects
def extent(cv):
    xs = [q[0] for q in cv.px if 0 <= q[0] < K.W and 0 <= q[1] < K.H]
    ys = [q[1] for q in cv.px if 0 <= q[0] < K.W and 0 <= q[1] < K.H]
    return min(xs), min(ys), max(xs), max(ys)


def grounded(make, row=143, x_mid=96.0, guess=(96.0, 80.0), floor=True):
    trial = make(guess)
    x0, y0, x1, y1 = extent(trial.draw())
    if y1 >= K.H - 2 or y0 <= 1 or x0 <= 1 or x1 >= K.W - 2:
        raise SystemExit('trial render touches the frame edge; move its guess')
    dx = round(x_mid - (x0 + x1) / 2.0)
    dy = row - y1
    pose = make((guess[0] + dx, guess[1] + dy))
    return pose, pose.draw(floor=row if floor else None)


def to_image(cv):
    return cv.image()


# ------------------------------------------------------------------ effects, in his own palette
def puff(cv, x, y, r):
    """A round kick of mat dust in the wrap's creams.  NO keyline: none of his effects carry one (the
    rush streaks, the aura, the floor glow), so its shaded side takes a darker cream instead."""
    part = {}
    m = L.ellipse(x, y, r, r * 0.62)
    for q in m:
        d = (q[0] - x) + (q[1] - y)
        edge = any((q[0] + a, q[1] + b) not in m for a, b in ((1, 0), (0, 1)))
        part[q] = 'g' if d < -r * 0.5 else ('h' if d < r * 0.4 else ('j' if edge else 'i'))
    cv.stamp(part, outline=False, under=True)


def lines(cv, segs, key='k'):
    """Impact lines: 1px strokes, drawn only where nothing of him is."""
    part = {}
    for (a, b) in segs:
        for q in L.line(int(round(a[0])), int(round(a[1])), int(round(b[0])), int(round(b[1]))):
            if q not in cv.px and 0 <= q[0] < K.W and 0 <= q[1] < K.H:
                part[q] = key
    cv.stamp(part, outline=False)


def arc(cv, cx, cy, r, a0, a1, ry=None, key='g'):
    """A thin motion streak behind the turn -- air, so no keyline."""
    ry = r if ry is None else ry
    steps = max(8, int(abs(a1 - a0) * 1.6))
    pts = [(int(round(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / steps)))),
            int(round(cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / steps)))))
           for i in range(steps + 1)]
    part = {}
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        for q in L.line(x0, y0, x1, y1):
            if q not in cv.px and 0 <= q[0] < K.W and 0 <= q[1] < K.H:
                part[q] = key
    cv.stamp(part, outline=False)


def bloom(cv, cx, cy, r):
    """The light of the blow landing on his skin: combat.bloom's own rule (skin only, a step or two
    lighter near the contact)."""
    for (x, y), k in list(cv.px.items()):
        if k not in 'stuvwW':
            continue
        d = math.hypot(x - cx, y - cy)
        if d < r:
            for _ in range(2 if d < r * 0.5 else 1):
                k = L.LIGHTER.get(k, k)
            cv.px[(x, y)] = k


# ------------------------------------------------------------------ the frames
def launch():
    """0: the fist lands under his beard.  The deadpan breaks into shock; he is thrown up off his
    heels, arms flung out, head snapped back on his shoulders."""
    def make(dest):
        return Pose(-6.0, dest, chest=(47.8, 60.8, 10.8), head=(-3, 0),
                    face=face_shock((0, -1)), head_turn=-8.0,
                    near=(8.0, 38.0), far=(172.0, 146.0),
                    lead=(70.0, 112.0, None), rear=(116.0, 82.0, None))
    p, cv = grounded(make, row=141, floor=False)
    cx, cy = p.pts['chin']
    bloom(cv, cx, cy + 2, 8.0)
    segs = []
    for d in (200, 230, 310, 340):
        a = math.radians(d)
        segs.append(((cx + math.cos(a) * 15, cy + 4 + math.sin(a) * 15),
                     (cx + math.cos(a) * 23, cy + 4 + math.sin(a) * 23)))
    lines(cv, segs)
    x0, _, x1, _ = extent(cv)
    puff(cv, x0 + 6, 140, 4.0)
    puff(cv, x1 - 6, 140, 4.0)
    return cv


def launch_lift():
    """1: off the mat and tipping back; everything loose trails below him."""
    p = Pose(-28.0, (94.0, 96.0), head=(-2, -1), face=face_shock((0, -1)), head_turn=-10.0,
             near=(70.0, 96.0), far=(128.0, 102.0),
             lead=(96.0, 104.0, None), rear=(78.0, 110.0, None))
    cv = p.draw()
    puff(cv, 70, 140, 4.5)
    puff(cv, 124, 140, 4.5)
    lines(cv, [((80, 128), (80, 136)), ((114, 128), (114, 136))], 'g')
    return cv


def hang():
    """2: the apex, level on his back and limp: the low arm hangs plumb, the high one has flopped
    back past his head, the legs dangle."""
    p = Pose(-90.0, (98.0, 94.0), face=face_shock((0, 0), jaw=1),
             near=(252.0, 232.0), far=(94.0, 90.0),
             lead=(94.0, 100.0, None), rear=(8.0, 26.0, None))
    return p.draw()


# The turn, with a twist in it: F front, B his back to the camera (the 天).  angle, where his middle
# sits, how far the loose limbs trail the turn, the pupils' roll.
TUMBLE = (
    (-135.0, (96.0, 94.0), 20.0, False, (0, -1)),
    (-225.0, (96.0, 96.0), 30.0, False, (1, 0)),
    (-315.0, (96.0, 96.0), 26.0, True, None),
    (-405.0, (96.0, 94.0), 14.0, True, None),
)


def _tumble(i):
    ang, dest, lag, back, pupil = TUMBLE[i]
    down = 90.0 + ang
    face = None if back else face_shock(pupil, jaw=2)
    if back:
        p = Pose(ang, dest, back=True,
                 near=(down - 95.0 + lag, down - 60.0 + lag),
                 far=(down + 95.0 + lag, down + 125.0 + lag),
                 lead=(down - 22.0 + lag, down + 2.0 + lag, None),
                 rear=(down + 22.0 + lag, down + 45.0 + lag, None))
    else:
        p = Pose(ang, dest, face=face,
                 near=(down - 70.0 + lag, down - 40.0 + lag),
                 far=(down + 70.0 + lag, down + 95.0 + lag),
                 lead=(down - 25.0 + lag, down + 5.0 + lag, None),
                 rear=(down + 30.0 + lag, down + 55.0 + lag, None))
    cv = p.draw()
    a0 = down + 180.0                          # where his head is, on screen
    arc(cv, dest[0], dest[1], 46, a0 + 25, a0 + 62, ry=42)
    arc(cv, dest[0], dest[1], 46, a0 + 205, a0 + 242, ry=42)
    return cv


def tumble_a():
    return _tumble(0)


def tumble_b():
    return _tumble(1)


def tumble_c():
    return _tumble(2)


def tumble_d():
    return _tumble(3)


LIE_MID = 80.0


def lying(angle, squash, face, near, far, lead, rear, row=143, head=(-1, 5), chest=None):
    def make(dest):
        return Pose(angle, dest, squash=squash, face=face, near=near, far=far, lead=lead,
                    rear=rear, head=head, chest=chest)
    return grounded(make, row=row, x_mid=LIE_MID, guess=(96.0, 84.0), floor=False)


def crash():
    """7: back-first into the mat, squashed; limbs slapped out flat."""
    p, cv = lying(-96.0, (1.10, 0.82), face_squeeze(), (-78.0, -58.0), (104.0, 128.0),
                  (-12.0, 8.0, None), (14.0, 30.0, None))
    x0, _, x1, _ = extent(cv)
    puff(cv, x0 - 2, 139, 5.0)
    puff(cv, x1 + 2, 139, 5.0)
    lines(cv, [((x0 - 6, 128), (x0 - 16, 122)), ((x1 + 6, 128), (x1 + 16, 122)),
               ((x0 - 4, 134), (x0 - 16, 132)), ((x1 + 4, 134), (x1 + 16, 132))], 'g')
    return cv


def crash_bounce():
    """8: the bounce -- off the mat once, everything loose flying up."""
    p, cv = lying(-92.0, (1.0, 1.0), face_squeeze(jaw=1), (-100.0, -125.0), (96.0, 70.0),
                  (-40.0, -15.0, None), (-5.0, 20.0, None), row=134)
    x0, _, x1, _ = extent(cv)
    puff(cv, x0 - 8, 139, 5.5)
    puff(cv, x1 + 8, 139, 5.5)
    return cv


def crash_settle():
    """9: down, and done."""
    p, cv = lying(-90.0, (1.0, 1.0), face_ko(tongue=False), (-62.0, -30.0), (112.0, 150.0),
                  (-8.0, 6.0, None), (12.0, 20.0, None))
    x0, _, x1, _ = extent(cv)
    puff(cv, x0 - 6, 140, 3.5)
    return cv


def down(k):
    """10-11: lying there, X-eyed, tongue out; the chest rises on a breath."""
    # the in-breath: the chest swells toward the ceiling (his front faces up the screen here) --
    # two texels, the size of Mason's own belly heave, so it reads at 0.4 s a frame
    chest = (CHEST[0] + (0.0, 1.6)[k], CHEST[1], CHEST[2] + (0.0, 0.6)[k])
    p, cv = lying(-90.0, (1.0, 1.0), face_ko(), (-62.0, -30.0), (112.0, 150.0),
                  (-8.0, 6.0, None), (12.0, 20.0, None), chest=chest)
    return cv


def down_rest():
    return down(0)


def down_breathe():
    return down(1)


FRAMES = [
    ('launch_contact', launch, 0.06),
    ('launch_lift', launch_lift, 0.08),
    ('hang', hang, 0.16),
    ('tumble_a', tumble_a, 0.07),
    ('tumble_b', tumble_b, 0.07),
    ('tumble_c', tumble_c, 0.07),
    ('tumble_d', tumble_d, 0.07),
    ('crash_impact', crash, 0.06),
    ('crash_bounce', crash_bounce, 0.08),
    ('crash_settle', crash_settle, 0.12),
    ('down_rest', down_rest, 0.40),
    ('down_breathe', down_breathe, 0.40),
]
assert len(FRAMES) == 12

TAGS = {
    'launch': (0, 1, False),
    'tumble': (2, 6, True),
    'crash': (7, 9, False),
    'down': (10, 11, True),
}
