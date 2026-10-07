"""LIAM'S PUPPET, THE FULL SET (approved 2026-10-06: "approve all, ash fur, keep liam's size").

Every sheet keeps its live Elements sheet's name, 96x96 cells, frame count and anchor (48, 96) (the juggle:
128x96, feet (64, 95)), built on his approved rig (the scratch copy, proven pixel-identical to all eleven
live sheets) and run through the approved puppet treatment (take B), with NO STAFF anywhere (the approved
Avatar look is staff-less; his fists stay where they gripped it).

  AVATAR sheets (channel, blow, ignite, cast_left, cast_right, slam_rise): the approved float body - the
    figure raised 12 rows (BODY (16, 20)), legs hanging, shoes toe-down - doing each live sheet's beat with
    his arms, mouth and the element in his hand. Each has a <sheet>_avatar.png ADDITIVE strip: the blazing
    lenses, the arrow marks, the glowing mouth on the open-mouthed frames, and a 2-texel rim of light.
  the rest (wobble, fall, downed, defeat, juggle): the live poses exactly, minus the staff.

Element FX drawn in-cell (fire in his fist, the water ribbon round his hand, breath, speed lines) keep his
own element colours (the roster's FX rule) and carry no keyline; they are composited over the treated body.
"""
import math
from ge_common import *
import le_rig as R
import le_poses as P
import le_posedefs as D
import le_parts as X
import le_staff as S
import le_full as F
import le_a34poses3 as Q
import le_fire as FI
import liam_avatar as LA
import liam_puppet as LP

FW = FH = 96
AV_BX, AV_BY = 16, 20          # the float body (LA.BX, LA.BY)
ST_BX, ST_BY = 16, 32          # his live rig's standing body
SET = LA.SET


def B(x, y, dy=0):
    return (x + AV_BX, y + AV_BY + dy)


# ------------------------------------------------------------------ no staff, anywhere
_REAL_STAFF = S.staff


def _no_staff(w, h, *a, **k):
    return R.blank(w, h)


class staffless:
    def __enter__(self):
        S.staff = _no_staff

    def __exit__(self, *a):
        S.staff = _REAL_STAFF


# ------------------------------------------------------------------ the float body, posed
FLOAT_FAR = ((11.0, 31.5, 5.3), (10, 33, 4, 39, 4.8, 4.0), (4, 39, -2.5, 43.5, 3.6, 3.2))
FLOAT_NEAR = ((49.0, 31.0, 5.3), (50, 33, 56, 39, 4.8, 4.0), (56, 39, 62.5, 43.5, 3.6, 3.2))


def far_palm():
    rows = [r[::-1] for r in X.OPEN_PALM]
    return [r.replace('a', '\0').replace('d', 'a').replace('\0', 'd') for r in rows]


def arm(spec, dy):
    d, u, f = spec
    return P.arm(delt=d, up=u, fore=f, dy=AV_BY - ST_BY + dy)


def legs(dy):
    L = LA.legs_hanging()
    return R.shift(L, 0, dy) if dy else L


def compose(far, near, hands, mouth, lens='flash', tails='up', dy=0, hdy=0, tdy=0, fx_back=None, fx_front=None):
    """One float frame: (body canvas, fx back, fx front, forearms {side: (elbow, wrist)} in body coords + dy)."""
    Hd = P.place(X.head(mouth, lens), dy=AV_BY - ST_BY + dy + hdy)
    A = arm(far, dy + tdy)
    N = arm(near, dy + tdy)
    cv = R.compose([D.tails(AV_BY - ST_BY + dy + hdy, tails), legs(dy), P.body('torso', dy=AV_BY - ST_BY + dy + tdy),
                    A, N, Hd], FW, FH)
    for kind, (x, y), side in hands:
        fx_, fy_ = B(x, y, dy + tdy)
        if kind == 'palm':
            X.hand(cv, far_palm() if side == 'far' else X.OPEN_PALM, fx_, fy_)
        elif kind == 'fist':
            P.fist_at(cv, fx_, fy_)
        elif kind == 'fist_up':
            X.hand(cv, X.FIST_UP if side == 'near' else [r[::-1] for r in X.FIST_UP], fx_, fy_)
    fore = {'far': (far[2][:2], far[2][2:4]), 'near': (near[2][:2], near[2][2:4])}
    fore = {k: ((a[0], a[1] + dy + tdy), (b[0], b[1] + dy + tdy)) for k, (a, b) in fore.items()}
    return cv, fx_back if fx_back is not None else R.blank(FW, FH), fx_front if fx_front is not None else R.blank(FW, FH), \
        {'fore': fore, 'head_dy': dy + hdy, 'dy': dy, 'mouth': mouth}


def mouth_pt(hdy):
    return B(27.5, 23 + hdy)


# ------------------------------------------------------------------ the Avatar sheets
def channel():
    """6-frame float loop (0.12): the approved float, a one-texel bob, the arms drifting on the updraft, the
    band's tails whipping, sparks of his element rising past him."""
    out = []
    for k in range(6):
        bob = (0, 0, -1, -1, 0, 0)[k]
        lift = (0, 0.5, 1.0, 1.0, 0.5, 0)[k]
        far = (FLOAT_FAR[0], FLOAT_FAR[1][:2] + (4, 39 - lift) + FLOAT_FAR[1][4:],
               (4, 39 - lift, -2.5, 43.5 - 2 * lift, 3.6, 3.2))
        near = (FLOAT_NEAR[0], FLOAT_NEAR[1][:2] + (56, 39 - lift) + FLOAT_NEAR[1][4:],
                (56, 39 - lift, 62.5, 43.5 - 2 * lift, 3.6, 3.2))
        hands = [('palm', (-5.0, 47.0 - 2 * lift), 'far'), ('palm', (65.0, 47.0 - 2 * lift), 'near')]
        fl = R.blank(FW, FH)
        t = k / 6.0
        for i in range(3):
            life = (t + i / 3.0) % 1.0
            x = B(6 + i * 26, 0)[0] + math.sin(life * 5 + i) * 2
            y = B(0, 64 - life * 70)[1]
            FI.plot(fl, x, y, ('l', 'b', 'W')[i] if life < 0.6 else 'w')
        out.append(compose(far, near, hands, SET, 'flash', ('up', 'flick')[k % 2], dy=bob, fx_front=fl))
    return out


def _blow_fx(fx, m, k):
    fl = R.blank(FW, FH)
    if fx in ('in1', 'in2'):
        n_ = 2 if fx == 'in1' else 3
        for i in range(n_):
            for side in (-1, 1):
                y0 = m[1] - 6 + i * 5
                x0 = m[0] + side * (22 - i * 3)
                x1 = m[0] + side * (9 - i)
                R.line(fl, int(x0), int(y0), int(x1), int(m[1] - 1 + i), 'w' if i else 'W')
    elif fx.startswith('out'):
        reach = {'out1': 9, 'out2': 12, 'out3': 7}[fx]
        FI.puff(fl, m[0], m[1] + 3, 2.2 if fx != 'out3' else 1.6, ramp=('W', 'W', 'w'), seed=k)
        for i, a in enumerate((25, 45, 135, 155)):
            ar = math.radians(a)
            for j in range(4, reach + 4):
                if (j + i + k) % 4 == 3:
                    continue
                curl = (j - 4) * 0.12 * (1 if a < 90 else -1)
                x = m[0] + math.cos(ar) * j * 1.5
                y = m[1] + 3 + math.sin(ar) * j * 0.5 + curl * j * 0.3
                FI.plot(fl, x, y, 'W' if j < reach * 0.5 else ('w' if j < reach * 0.85 else 'v'))
    return fl


def blow():
    """6 frames (the live blow's beats): inhale, inhale deeper (arms drawn up and back, head back), BLOW (both
    palms thrust out, the breath bursting), blow on, tailing off, recover. The gust FX sheet sits on the mouth."""
    out = []
    IN_FAR = ((11.0, 31.5, 5.3), (10, 33, 6, 40, 4.8, 4.0), (6, 40, 5, 46, 3.6, 3.3))
    IN_NEAR = ((49.0, 31.0, 5.3), (50, 33, 54, 40, 4.7, 4.0), (54, 40, 56, 46, 3.8, 3.4))
    BACK_FAR = ((11.5, 30.5, 5.2), (11, 31, 4, 27, 4.6, 3.7), (4, 27, -1, 21, 3.4, 3.1))
    BACK_NEAR = ((49.0, 31.0, 5.3), (50, 31, 57, 27, 4.6, 3.8), (57, 27, 61, 21, 3.6, 3.2))
    PUSH_FAR = ((11.0, 31.5, 5.3), (10, 32, 4, 37, 4.8, 4.0), (4, 37, -1.5, 40, 3.6, 3.2))
    PUSH_NEAR = ((49.0, 31.0, 5.3), (50, 32, 56, 37, 4.8, 4.0), (56, 37, 61.5, 40, 3.6, 3.2))
    specs = [  # head dy, torso dy, mouth, lens, tails, arms, fx
        (-1, 0, X.PUFF, 'dim', 'down', 'in', 'in1'),
        (-3, -1, X.PUFF, 'dim', 'mid', 'back', 'in2'),
        (1, 1, 'blow', 'flash', 'up', 'push', 'out1'),
        (1, 1, 'blow', 'flash', 'flick', 'push', 'out2'),
        (0, 0, 'blow', 'flash', 'up', 'float', 'out3'),
        (0, 0, X.TALK, 'dim', 'down', 'float', 'rest'),
    ]
    for k, (hdy, tdy, mouth, lens, tl, arms, fx) in enumerate(specs):
        if arms == 'in':
            far, near = IN_FAR, IN_NEAR
            hands = [('fist', (4.5, 48.0), 'far'), ('fist', (56.5, 48.0), 'near')]
        elif arms == 'back':
            far, near = BACK_FAR, BACK_NEAR
            hands = [('palm', (-2.0, 17.5), 'far'), ('palm', (62.5, 17.5), 'near')]
        elif arms == 'push':
            far, near = PUSH_FAR, PUSH_NEAR
            hands = [('palm', (-4.0, 43.0), 'far'), ('palm', (64.0, 43.0), 'near')]
        else:
            far, near = FLOAT_FAR, FLOAT_NEAR
            hands = [('palm', (-5.0, 47.0), 'far'), ('palm', (65.0, 47.0), 'near')]
        fl = _blow_fx(fx, mouth_pt(hdy), k)
        out.append(compose(far, near, hands, mouth, lens, tl, hdy=hdy, tdy=tdy, fx_front=fl))
    return out


def _flames_at(x, y, t, power, seed):
    return Q.staff_flames(x, y, t, power=power, seed=seed)


def ignite():
    """5 frames (the live ignite's beats, the fire in his own fist now): raise (the fire wakes in his raised
    fist), FLARE (it bursts, a ring of sparks), the throw (the arm swept down and out, streaks of fire leaving
    it), the hold, the settle."""
    out = []
    RAISE_FAR = ((11.5, 30.5, 5.2), (11, 31, 6.5, 22, 4.6, 3.6), (6.5, 22, 6, 14, 3.4, 3.1))
    RAISE_NEAR = ((49.0, 31.0, 5.3), (50, 31, 56, 26, 4.6, 3.9), (56, 26, 59, 19, 3.6, 3.2))
    for k in range(5):
        t = k / 5.0
        if k <= 1:
            lift = 1.0 if k else 0.0
            far = (RAISE_FAR[0], RAISE_FAR[1][:2] + (6.5, 22 - lift) + RAISE_FAR[1][4:], (6.5, 22 - lift, 6, 14 - lift, 3.4, 3.1))
            near = RAISE_NEAR
            fist = (6.0, 11.5 - lift)
            hands = [('fist', fist, 'far'), ('fist', (59.5, 17.0), 'near')]
            mouth, hdy, tl = ('big', -1, 'mid') if k == 0 else ('shout', -2, 'up')
            dx = 0
        else:
            far = ((11.5, 31.0, 5.2), (11, 32, 5, 37, 4.6, 3.8), (5, 37, -1, 41, 3.4, 3.1))
            near = ((49.0, 31.0, 5.3), (50, 32, 55, 38, 4.7, 4.0), (55, 38, 51, 42, 3.8, 3.4))
            fist = (-2.5, 42.5)
            hands = [('fist', fist, 'far'), ('fist', (50.0, 43.0), 'near')]
            mouth, hdy, tl = (('shout', 0, 'flick'), ('big', 0, 'mid'), ('smirk', 0, 'mid'))[k - 2]
        tip = B(*fist)
        power = (0.3, 1.0, 0.9, 0.7, 0.45)[k]
        fl = _flames_at(tip[0], tip[1] - 2, t, power, k)
        if k == 1:
            for i in range(10):
                a = math.radians(i * 36 + 10)
                FI.plot(fl, tip[0] + math.cos(a) * 11, tip[1] - 2 + math.sin(a) * 10, 'a' if i % 2 else '6')
        if k == 2:
            for i in range(3):
                a = math.radians(115 + i * 22)
                for j in range(4, 14):
                    if (j + i) % 4 == 3:
                        continue
                    FI.plot(fl, tip[0] + math.cos(a) * j, tip[1] + math.sin(a) * j, 'a' if j < 8 else '6')
        out.append(compose(far, near, hands, mouth, 'flash', tl, hdy=hdy, fx_front=fl))
    return out


def _water_ring(ox, oy, **kw):
    back, front = F.water_ring(ox, oy, **kw)
    return back, front


def cast_left():
    """3 frames (the live cast_left's beats): wind-up (far hand raised, the water ring spun up round it), the
    swing out over the left half (the arm flung out, spray streaming off it), the follow-through."""
    out = []
    for k in range(3):
        if k == 0:
            far = ((11.5, 30.5, 5.2), (11, 31, 6.5, 22, 4.6, 3.6), (6.5, 22, 5, 14, 3.4, 3.1))
            palm = (4.5, 10.0)
            ring = dict(rx=9.8, ry=4.2, tilt=-16)
        elif k == 1:
            far = ((11.5, 30.5, 5.2), (11, 31, 4, 27, 4.6, 3.6), (4, 27, -3, 24, 3.4, 3.1))
            palm = (-6.0, 22.5)
            ring = dict(rx=8.5, ry=3.6, tilt=-30)
        else:
            far = ((11.5, 30.5, 5.2), (11, 32, 4, 35, 4.6, 3.7), (4, 35, -3, 36, 3.4, 3.1))
            palm = (-6.0, 37.5)
            ring = dict(rx=6.5, ry=3.6, tilt=-20)
        hands = [('palm', palm, 'far'), ('palm', (65.0, 47.0), 'near')]
        ox, oy = B(palm[0] + 0.5, palm[1] - 1)
        fx_b, fx_f = _water_ring(ox, oy, **ring)
        if k >= 1:
            spray = R.blank(FW, FH)
            if k == 1:
                pts, radii = [], []
                for i in range(14):
                    u = i / 13
                    pts.append((ox - 3 - u * 8, oy + 3 + u * 10 + math.sin(u * 4) * 1.2))
                    radii.append(1.5 - 1.0 * u)
                _bk, fr_ = D.ribbon_fx(pts, radii, lambda i: True)
                R.composite(spray, fr_)
                D.dots(spray, [(ox - 10, oy + 6), (ox - 9, oy + 11), (ox - 7, oy + 15), (ox + 5, oy - 5)], 'l')
            else:
                D.dots(spray, [(ox - 6, oy + 6), (ox - 5, oy + 10), (ox - 3, oy + 13), (ox + 5, oy + 6)], 'l')
            R.composite(fx_f, spray)
        mouth = 'big'
        out.append(compose(far, FLOAT_NEAR, hands, mouth, 'flash', 'up' if k == 1 else 'mid', hdy=-1,
                           fx_back=fx_b, fx_front=fx_f))
    return out


def cast_right():
    """3 frames (the live cast_right's beats): both arms up (the water ring round his raised far hand), the near
    palm thrust out over the right half with water streaming off it, the follow-through."""
    out = []
    SURGE_FAR = ((11.5, 30.5, 5.2), (11, 31, 5, 23, 4.6, 3.6), (5, 23, 0.5, 15, 3.4, 3.1))
    for k in range(3):
        if k == 0:
            near = ((49.0, 31.0, 5.3), (50, 31, 56, 23, 4.6, 3.8), (56, 23, 58, 15, 3.6, 3.2))
            npalm = (58.5, 11.0)
        elif k == 1:
            near = ((49.0, 31.0, 5.3), (50, 31.5, 57, 29, 4.6, 3.9), (57, 29, 61, 25, 3.6, 3.2))
            npalm = (62.5, 21.0)
        else:
            near = ((49.0, 31.0, 5.3), (50, 32, 57, 33, 4.6, 3.9), (57, 33, 60, 31, 3.6, 3.2))
            npalm = (61.5, 27.0)
        hands = [('palm', (-0.5, 10.5), 'far'), ('palm', npalm, 'near')]
        ox, oy = B(0.0, 9.5)
        fx_b, fx_f = _water_ring(ox, oy, rx=7.0 if k else 5.5, ry=3.2)
        px_, py_ = B(*npalm)
        spray = R.blank(FW, FH)
        if k == 1:
            pts, radii = [], []
            for i in range(16):
                u = i / 15
                pts.append((px_ + 2 + u * 13, py_ - 4 + u * 10 + math.sin(u * 5) * 1.5))
                radii.append(1.6 - 1.1 * u)
            _bk, fr_ = D.ribbon_fx(pts, radii, lambda i: True)
            R.composite(spray, fr_)
            D.dots(spray, [(px_ + 8, py_ - 7), (px_ + 12, py_ - 3), (px_ + 15, py_ + 1), (px_ + 10, py_ + 8)], 'l')
        elif k == 2:
            D.dots(spray, [(px_ + 5, py_ + 2), (px_ + 9, py_ + 6), (px_ + 12, py_ + 11), (px_ + 7, py_ + 12)], 'l')
            D.dots(spray, [(px_ + 8, py_ + 4), (px_ + 11, py_ + 9)], 'b')
        spray[:, 92:] = '.'
        R.composite(fx_f, spray)
        out.append(compose(SURGE_FAR, near, hands, 'big', 'flash', 'up', hdy=-1, fx_back=fx_b, fx_front=fx_f))
    return out


def slam_rise():
    """3 frames (the live slam_rise's beats): both fists hauled up overhead (a wince), driven down (the summoning
    slam: a shout, speed lines), then the palms lifted, raising the stone."""
    out = []
    UP_FAR = ((11.0, 31.5, 5.3), (10, 33, 6, 26, 4.7, 3.8), (6, 26, 4, 18, 3.6, 3.2))
    UP_NEAR = ((49.0, 31.0, 5.3), (50, 33, 54, 26, 4.7, 3.8), (54, 26, 56, 18, 3.6, 3.2))
    DN_FAR = ((11.0, 31.5, 5.3), (10, 33, 8, 40, 4.8, 4.0), (8, 40, 10, 46, 3.6, 3.3))
    DN_NEAR = ((49.0, 31.0, 5.3), (50, 33, 52, 40, 4.8, 4.0), (52, 40, 50, 46, 3.6, 3.3))
    LIFT_FAR = ((11.0, 31.5, 5.3), (10, 33, 3, 33, 4.8, 4.0), (3, 33, -2, 28, 3.6, 3.2))
    LIFT_NEAR = ((49.0, 31.0, 5.3), (50, 33, 57, 33, 4.8, 4.0), (57, 33, 62, 28, 3.6, 3.2))
    for k in range(3):
        if k == 0:
            far, near, dy = UP_FAR, UP_NEAR, 1
            hands = [('fist', (4.0, 16.0), 'far'), ('fist', (56.0, 16.0), 'near')]
            mouth, tl = X.WINCE, 'down'
            fl = R.blank(FW, FH)
        elif k == 1:
            far, near, dy = DN_FAR, DN_NEAR, 3
            hands = [('fist', (10.5, 48.0), 'far'), ('fist', (49.5, 48.0), 'near')]
            mouth, tl = 'shout', 'up'
            fl = R.blank(FW, FH)
            for (x0, y0, x1, y1) in ((4, 52, 4, 58), (14, 54, 14, 61), (46, 54, 46, 61), (56, 52, 56, 58)):
                R.line(fl, *B(x0, y0, dy), *B(x1, y1, dy), 'w')
        else:
            far, near, dy = LIFT_FAR, LIFT_NEAR, 1
            hands = [('palm', (-3.5, 24.5), 'far'), ('palm', (63.5, 24.5), 'near')]
            mouth, tl = X.TALK, 'up'
            fl = R.blank(FW, FH)
            for (x, y, c) in ((-6, 18, 'G'), (-3, 15, 'K'), (64, 17, 'G'), (61, 14, 'K'), (-1, 12, 'G'), (66, 12, 'G')):
                D.dots(fl, [B(x, y, dy)], c)
        out.append(compose(far, near, hands, mouth, 'flash', tl, dy=dy, fx_front=fl))
    return out


AVATAR = [  # name, builder, live frame times
    ('channel', channel, [0.12] * 6),
    ('blow', blow, [0.15, 0.2, 0.12, 0.16, 0.14, 0.13]),
    ('ignite', ignite, [0.06] * 5),
    ('cast_left', cast_left, [0.15] * 3),
    ('cast_right', cast_right, [0.15] * 3),
    ('slam_rise', slam_rise, [0.15, 0.1, 0.75]),
]


# ------------------------------------------------------------------ the rest: the live poses, staff-less
def plain_frames(name):
    with staffless():
        if name == 'juggle':
            frames, info = F.juggle()
            return frames, info
        q = {n: fn for n, fn, *_ in Q.ALL}
        f = {n: fn for n, fn, _t in F.SHEETS if fn}
        fn = q.get(name) or f[name]
        return [c for c, _ in fn()], None


PLAIN = [('wobble', [0.12] * 4), ('fall', [0.15] * 4), ('downed', [0.3] * 3), ('defeat', [0.12, 0.12, 0.14, 0.2, 1.0])]
