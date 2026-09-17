"""Part B v2: throw_windup 32-33, throw_release 34-35, empty_wait 36-37, recall_catch 38-39 (256x192).
Same beats as the approved v1 frames, re-fitted to the 75 px body and the 1.25x blade."""
import math
from base2 import *
import fx2 as FX
from sword2 import Sword2

FRAMES = {}
M = R.M


def frame(i):
    def deco(fn):
        FRAMES[i] = fn
        return fn
    return deco


# ------------------------------------------------------------------ face edits on the v2 head
_HEADS = {}


def head_edit(kind, edits):
    if kind not in _HEADS:
        img = [row[:] for row in R.layers()['head']]
        for x0, y0, s in edits:
            for i, ch in enumerate(s):
                if ch != '.' and img[y0][x0 + i][3]:
                    img[y0][x0 + i] = PALC[ch]
        _HEADS[kind] = img
    return _HEADS[kind]


def head_grit():        # glare kept, teeth bared
    return head_edit('grit', [(45, 44, "eeeeee"), (45, 45, "kkkkkk")])


def head_look_left():   # left pupil slides toward the raised hand
    return head_edit('lookL', [(41, 36, "ppe")])


# ------------------------------------------------------------------ hands
OPEN_UP_S = """
.k.k.k.k....
kIkJkJkKk...
kIkJkJkKk.k.
kIkJkJkKkkJk
kIJJJJKKLkKk
kIJJJKKKLLLk
kJJKKKKLLMk.
.kKKKLLLMMk.
..kkkkkkkk..
"""

OPEN_FWD_S = """
.kkkkkkk.
kIIIIIJJk
kIJJJJKKk
kkkkkkkkk
kIkJkKkLk
kJkJkKkMk
.k.k.k.k.
"""


def hand(fr, grid, c, shadow=True):
    rows = grid.strip('\n').split('\n')
    x0, y0 = int(round(c[0])) - len(rows[0]) // 2, int(round(c[1])) - len(rows) // 2
    pts = [(x0 + cc, y0 + r) for r, row in enumerate(rows) for cc, ch in enumerate(row) if ch != '.']
    if shadow:
        R.cast_shadow(fr, pts)
    fr.stamp(grid, x0, y0)


def body(fr, U=(0, 0), S=(0, 0), H=(0, 0), cape=None, torso=None, skip=(), hooks=None, off=None, head=None):
    extra = {}
    if cape is not None:
        extra['cape'] = R.cape_layer(*cape)
    if torso is not None:
        extra['torso'] = R.torso_layer(*torso)
    if head is not None:
        extra['head'] = head
    o = {'upper': U, 'shoulders': S, 'headx': H}
    o.update(off or {})
    R.compose(fr, o, skip=skip, extra=extra, hooks=hooks)
    wf()


def upper_arm(fr, a, b):
    R.limb(fr, a, b, 9, ramp='chain')
    wf()


def fore_arm(fr, e, h):
    R.limb(fr, e, h, 9)
    R.cop(fr, e, 4.6, 4.4)
    wf()


def sword_at(fr, grip_xy, ang, sa=1.0, grip_a=-10.0, parts=('blade', 'grip', 'pommel', 'guard')):
    wf()
    a = math.radians(ang)
    u = (math.cos(a), math.sin(a))
    g = (grip_xy[0] - u[0] * grip_a * sa, grip_xy[1] - u[1] * grip_a * sa)
    S = Sword2(g, ang, sa)
    S.draw(fr.canvas(), parts=parts)
    wf()
    return S


def sweep(fr, pose0, pose1, band=30.0, a_tip=115.5, tail=0.12, recency=False, a_floor=-35.0, keep=None, steps=22):
    """v2 sweep smear between two sword poses (guard, ang, sa)."""
    best = {}
    for k in range(steps + 1):
        t = k / steps
        g = (pose0[0][0] + (pose1[0][0] - pose0[0][0]) * t, pose0[0][1] + (pose1[0][1] - pose0[0][1]) * t)
        ang = pose0[1] + (pose1[1] - pose0[1]) * t
        sa = pose0[2] + (pose1[2] - pose0[2]) * t
        S = Sword2(g, ang, sa)
        thick = band * (tail + (1 - tail) * (t ** 0.8))
        a_in = max(a_floor, a_tip - thick)
        pts = [S.P(a, b) for a in (a_in, a_tip) for b in (-14, 14)]
        x0, x1 = max(0, int(min(p[0] for p in pts)) - 1), min(FW - 1, int(max(p[0] for p in pts)) + 1)
        y0, y1 = max(0, int(min(p[1] for p in pts)) - 1), min(FH - 1, int(max(p[1] for p in pts)) + 1)
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                a, b = S.ab(x, y)
                if a_in <= a <= a_tip and abs(b) <= 13.0:
                    q = t if recency else (a - a_in) / max(1e-6, thick)
                    if best.get((x, y), -1) < q:
                        best[(x, y)] = q
    for (x, y), q in best.items():
        if keep is not None and (x, y) in keep:
            continue
        fr.px[y][x] = PALC['W' if q > 0.62 else ('A' if q > 0.3 else 'B')]


def pose(grip_xy, ang, sa=1.0, grip_a=-10.0):
    a = math.radians(ang)
    u = (math.cos(a), math.sin(a))
    return ((grip_xy[0] - u[0] * grip_a * sa, grip_xy[1] - u[1] * grip_a * sa), ang, sa)


def occupied(fr):
    return set((x, y) for y in range(FH) for x in range(FW) if fr.px[y][x] is not None)


# ================================================================ windup
@frame(32)
def windup_heave():
    """heaves the slab back over his right shoulder: blade swings past vertical toward the far side"""
    fr = R.Frame()
    U = (-1, 0)
    E, Hd = (93, 161), (97, 147)

    def first(f):
        sweep(f, pose((100, 164), -100, 1.0), pose(Hd, -58, 0.95), band=38.0, a_tip=100.0)

    def under_paul(f):
        upper_arm(f, (109, 157), E)

    def before_head(f):
        sword_at(f, Hd, -58, sa=0.95)
    body(fr, U=U, cape=(-0.8, 0.5, 0), skip=('head',),
         hooks={'cape': first, 'paulL': under_paul, 'head': before_head}, off={'paulL': (0, -1)})
    fr.put96(R.layers()['head'], U[0], U[1])
    fore_arm(fr, E, Hd)
    R.fist(fr, Hd[0], Hd[1])
    return fr


@frame(33)
def windup_coil():
    """coiled: blade lies back over the shoulder behind his head, elbow cocked low, free fist pulled in"""
    fr = R.Frame()
    U, Hx = (-1, 2), (-1, 1)
    E, Hd = (88, 164), (94, 152)
    E2, H2 = (171, 162), (163, 171)

    def under_paul(f):
        upper_arm(f, (109, 159), E)
        upper_arm(f, (147, 159), E2)

    def before_head(f):
        sword_at(f, Hd, -33, sa=0.96)
    body(fr, U=U, H=Hx, cape=(-1.2, 1.0, 0), torso=(0.4, 0.4), skip=('head', 'armR_front'),
         hooks={'paulL': under_paul, 'head': before_head}, off={'paulL': (0, -2), 'paulR': (1, 1)})
    fr.put96(R.layers()['head'], U[0] + Hx[0], U[1] + Hx[1])
    fore_arm(fr, E, Hd)
    R.fist(fr, Hd[0], Hd[1], horizontal=True)
    fore_arm(fr, E2, H2)
    R.fist(fr, H2[0], H2[1])
    return fr


# ================================================================ release
LOB = dict(pommel_hand_gap=(-13, -15), ang=-21.0, sa=0.86)
RELEASE = {}


@frame(34)
def release():
    """the arm whips up and over; the slab leaves his open hand, tumbling up and away"""
    fr = R.Frame()
    U, S, Hx = (1, -2), (0, -1), (1, -1)
    E, Hd = (92, 144), (98, 130)
    E2, H2 = (167, 165), (163, 176)

    def under_paul(f):
        upper_arm(f, (109, 152), E)
        upper_arm(f, (147, 155), E2)
    body(fr, U=U, S=S, H=Hx, cape=(1.2, 0.5, 1.5), skip=('head', 'armR_front'), hooks={'paulL': under_paul},
         off={'paulL': (0, -2)})
    fr.put96(head_grit(), U[0] + S[0] + Hx[0], U[1] + S[1] + Hx[1])
    ang, sa = LOB['ang'], LOB['sa']
    a = math.radians(ang)
    u = (math.cos(a), math.sin(a))
    pom = (Hd[0] + LOB['pommel_hand_gap'][0], Hd[1] + LOB['pommel_hand_gap'][1])
    # guard so that the pommel centre (a = -32) sits at `pom`
    g = (pom[0] + u[0] * 32 * sa, pom[1] + u[1] * 32 * sa)
    centre = (g[0] + u[0] * 41.75 * sa, g[1] + u[1] * 41.75 * sa)   # middle of pommel end (-35) .. tip (115.5)
    RELEASE['sword_centre'] = (round(centre[0], 1), round(centre[1], 1))
    p1 = (g, ang, sa)
    p0 = ((g[0] - 20, g[1] + 34), -46.0, 0.9)
    sweep(fr, p0, p1, band=150.0, a_tip=108.0, tail=0.22, recency=True, a_floor=-20.0, keep=occupied(fr))
    S2 = Sword2(g, ang, sa)
    wf()
    S2.draw(fr.canvas())
    wf()
    fore_arm(fr, E2, H2)
    R.fist(fr, H2[0], H2[1])
    fore_arm(fr, E, Hd)
    hand(fr, OPEN_UP_S, Hd)
    return fr


@frame(35)
def follow_through():
    """empty-handed follow-through: arm swung down across his front, hand open, body bowed"""
    fr = R.Frame()
    U, S, Hx = (2, 3), (0, 1), (1, 2)
    E, Hd = (101, 172), (114, 180)
    E2, H2 = (168, 160), (169, 147)

    def trail(f):
        import bfx2
        bfx2.crescent(f, 109, 153, 30, 34, 112, 262, 6, 0.5)
        wf()

    def under_paul(f):
        upper_arm(f, (111, 161), E)
        upper_arm(f, (147, 160), E2)
    body(fr, U=U, S=S, H=Hx, cape=(1.8, 1.0, 0.5), skip=('head', 'armR_front'),
         hooks={'cape': trail, 'paulL': under_paul}, off={'paulL': (1, 1), 'paulR': (0, -1)})
    fr.put96(head_grit(), U[0] + S[0] + Hx[0], U[1] + S[1] + Hx[1])
    fore_arm(fr, E2, H2)
    R.fist(fr, H2[0], H2[1])
    fore_arm(fr, E, Hd)
    hand(fr, OPEN_FWD_S, Hd)
    return fr


# ================================================================ empty wait (loop)
def tremor(fr, k):
    for x, y in ([(74, 176), (183, 178)] if k == 0 else [(75, 180), (182, 175)]):
        for d in range(3):
            fr.set(x, y + d, 'W')


def wait(shake, bob, dust_left):
    fr = R.Frame()
    U = (shake, 2 + bob)
    E, Hd = (93 + shake, 168 + bob), (100 + shake, 178 + bob)
    E2, H2 = (163 + shake, 168 + bob), (156 + shake, 178 + bob)

    def under_paul(f):
        upper_arm(f, (109 + shake, 160 + bob), E)
        upper_arm(f, (147 + shake, 160 + bob), E2)
    body(fr, U=U, S=(0, -1), H=(0, 1), cape=(0.0, 1.5 + bob, 0), skip=('head', 'armR_front'),
         hooks={'paulL': under_paul}, off={'legs': (shake, 0), 'flap': (shake, 0), 'tassets': (shake, 0)})
    fr.put96(head_grit(), U[0], U[1] + 0)
    fore_arm(fr, E, Hd)
    R.fist(fr, Hd[0], Hd[1])
    fore_arm(fr, E2, H2)
    R.fist(fr, H2[0], H2[1])
    if dust_left:
        FX.puff(fr, 78, 183)
        FX.puff(fr, 170, 186, small=True)
        FX.rock(fr, 86, 172)
        FX.rock(fr, 176, 168)
        tremor(fr, 0)
    else:
        FX.puff(fr, 168, 183)
        FX.puff(fr, 82, 186, small=True)
        FX.rock(fr, 168, 172)
        FX.rock(fr, 80, 166)
        tremor(fr, 1)
    return fr


@frame(36)
def wait0():
    return wait(0, 0, True)


@frame(37)
def wait1():
    return wait(1, 1, False)


# ================================================================ recall + catch
@frame(38)
def recall_reach():
    """raises his sword hand open to call the slab back"""
    fr = R.Frame()
    U, Hx = (-1, -1), (-1, -1)
    E, Hd = (90, 146), (95, 130)

    def under_paul(f):
        upper_arm(f, (109, 155), E)
    body(fr, U=U, H=Hx, cape=(-0.6, 0.5, 0), skip=('head',), hooks={'paulL': under_paul},
         off={'paulL': (0, -2)})
    fr.put96(head_look_left(), U[0] + Hx[0], U[1] + Hx[1])
    fore_arm(fr, E, Hd)
    hand(fr, OPEN_UP_S, Hd)
    return fr


CATCH = {}


def burst(fr, cx, cy):
    for ang, r0, ln, w in [(-150, 9, 17, 2.6), (-120, 11, 12, 2.0), (175, 9, 17, 2.6), (145, 9, 12, 2.0),
                           (-35, 11, 10, 1.8), (35, 10, 11, 2.0), (105, 9, 10, 1.8), (-80, 11, 9, 1.6)]:
        a = math.radians(ang)
        FX.ray(fr, (cx + math.cos(a) * r0, cy + math.sin(a) * r0),
               (cx + math.cos(a) * (r0 + ln), cy + math.sin(a) * (r0 + ln)), w)
    for x, y in [(cx - 19, cy - 16), (cx + 16, cy - 14), (cx - 23, cy + 7)]:
        FX.sparkle(fr, x, y, 2)


@frame(39)
def recall_catch():
    """catches the returning slab: grip slaps into the fist with an impact burst, weight absorbs down"""
    fr = R.Frame()
    body(fr, U=(0, 2), cape=(-1.0, 1.5, 0))
    fdx, fdy = -1, -2
    cx, cy = R.IDLE_FIST[0] + fdx, R.IDLE_FIST[1] + fdy
    CATCH['fist_centre'] = (cx, cy)
    R.idle_weapon(fr, dx=-1, dy=-3, arm_dx=0, arm_dy=1, fist_dx=fdx, fist_dy=fdy)
    wf()
    burst(fr, cx, cy)
    return fr
