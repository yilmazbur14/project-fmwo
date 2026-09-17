"""Eric bear hug v2: the approved v1 beats re-fitted to the 75 px body (256x192 frames, feet on y=191).
Joint positions are the approved v1 ones mapped through R.M (0.8 about the feet centre); body offsets x0.8."""
import math
import bh2 as B
from bh2 import R, FX, M, off8, body, upper_arm, fore_arm, stamp, head_variant, hand, layered
import player2 as P2

ORDER = ['charge0', 'charge1', 'charge2', 'lunge0', 'lunge1', 'whiff0', 'whiff1', 'grab',
         'squeeze0', 'squeeze1', 'squeeze2', 'toss0', 'toss1', 'retrieve0', 'retrieve1']
F = {}
PS = 0.767            # victim scale: ~30 px standing


def frame(name):
    def deco(fn):
        F[name] = fn
        return fn
    return deco


SL1, SR1 = (38, 85), (89, 85)


def shoulders(U, S):
    a, b = M(*SL1), M(*SR1)
    return (a[0] + U[0] + S[0], a[1] + U[1] + S[1]), (b[0] + U[0] + S[0], b[1] + U[1] + S[1])


def add(p, d):
    return (p[0] + d[0], p[1] + d[1])


# ============================================================== charge
def charge_pose(phase, tremble=(0, 0)):
    tx, ty = tremble
    U, S, Hd = (tx, 6 + ty), (0, -2), (0, 2)
    bf = R.Frame()
    sl, sr = shoulders(U, S)
    el, er = add(M(17, 87), tremble), add(M(110, 87), tremble)
    wl, wr = add(M(11, 74), tremble), add(M(116, 74), tremble)
    hl, hr = add(M(12, 66), tremble), add(M(115, 66), tremble)

    def ua(fr):
        upper_arm(fr, sl, el)
        upper_arm(fr, sr, er)
    body(bf, upper=U, shoulders=S, headx=Hd, cape=(0.0, 4.8 + 0.8 * (phase % 2), 4.0), torso=(2.0, 0.8),
         legs=((0, 0), (0, 0)), tassets=((-1, 2), (1, 2)), skip=('armR_front',), under_pauldrons=ua,
         head=head_variant('roar'))
    fore_arm(bf, el, wl)
    fore_arm(bf, er, wr)
    stamp(bf, hand('up_l'), hl[0], hl[1], shadow=False)
    stamp(bf, hand('up'), hr[0], hr[1], shadow=False)

    def back(fr):
        for x, y, ch in B.aura(bf, phase=phase, thick=4.0, tongues=10.4):
            fr.set(x, y, ch)
        B.planted_sword(fr)

    def front(fr):
        B.energy_streaks(fr, phase, [int(M(x, 0)[0]) for x in (6, 20, 34, 94, 108, 121)], 98, 146)
        for i, p in enumerate([(2, 104), (122, 100), (44, 18), (86, 14)]):
            q = M(*p)
            fr.stamp(B.PEBBLE, int(q[0]), int(q[1]) - (phase + i) % 2 * 2)
        for i, p in enumerate([(30, 18), (100, 26), (4, 60), (123, 58), (64, 8)]):
            q = M(*p)
            if (i + phase) % 2 == 0:
                B.spark(fr, int(q[0]), int(q[1]), 2, 'Z', 'G')
            else:
                B.spark(fr, int(q[0]) + 1, int(q[1]) + 2, 1, 'Z', 'g')
    return layered(back, bf, front)


def quiver(fr, x, y0, y1, side):
    for y in range(y0, y1, 5):
        for dx, dy in [(0, 0), (side, 1), (side, 2), (0, 3)]:
            if fr.get(x + dx, y + dy) is None:
                fr.set(x + dx, y + dy, 'W')


@frame('charge0')
def charge0():
    """has just rammed the greatsword into the ground beside him and lets go; arms swing wide, aura igniting"""
    U, S = (-1, 2), (0, 0)
    bf = R.Frame()
    sl, sr = shoulders(U, S)
    el, er = (95, 156), M(107, 97)
    wl, wr = (88, 144), M(117, 86)
    hl, hr = (86, 136), M(116, 78)

    def ua(fr):
        upper_arm(fr, sl, el)
        upper_arm(fr, sr, er)
    body(bf, upper=U, shoulders=S, cape=(-0.8, 2.0, 1.2), torso=(0.8, 0.4), legs=((0, 0), (0, 0)),
         tassets=((0, 1), (0, 1)), skip=('armR_front',), under_pauldrons=ua, head=head_variant('strain'))
    fore_arm(bf, el, wl)
    fore_arm(bf, er, wr)
    stamp(bf, hand('up_l'), hl[0], hl[1], shadow=False)
    stamp(bf, hand('up'), hr[0], hr[1], shadow=False)

    def back(fr):
        for x, y, ch in B.aura(bf, phase=3, thick=2.0, tongues=4.0):
            fr.set(x, y, ch)
        B.planted_sword(fr)

    def front(fr):
        quiver(fr, B.SWX - 21, 97, 124, -1)
        quiver(fr, B.SWX + 21, 97, 124, 1)
        for x, y, sm in [(B.SWX - 26, 179, False), (B.SWX + 16, 181, True), (B.SWX - 24, 171, True), (B.SWX + 8, 176, True)]:
            FX.puff(fr, x, y, small=sm)
        for x, y in [(B.SWX + 20, 160), (B.SWX - 30, 156), (B.SWX + 26, 170)]:
            fr.stamp(B.CLOD, x, y)
        B.spark(fr, int(M(96, 44)[0]), int(M(96, 44)[1]), 1, 'Z', 'g')
        B.spark(fr, int(M(64, 26)[0]), int(M(64, 26)[1]), 1, 'Z', 'g')
    return layered(back, bf, front)


@frame('charge1')
def charge1():
    return charge_pose(0)


@frame('charge2')
def charge2():
    return charge_pose(1, tremble=(1, 0))


# ============================================================== lunge (active grab frames)
def lunge(step):
    bf = R.Frame()
    if step == 0:
        U, S, Hd = (0, 3), (0, 1), (0, 2)
        el, er, wl, wr = M(14, 80), M(113, 80), M(8, 66), M(119, 66)
        hl, hr = M(9, 58), M(118, 58)
        legs, tass = ((0, 0), (0, -4)), ((0, 2), (0, -2))
        cape = dict(rise=6, spread=0, flutter=0)
        face = 'roar'
    else:
        U, S, Hd = (0, 5), (0, 2), (0, 3)
        el, er, wl, wr = M(13, 95), M(114, 95), M(8, 83), M(119, 83)
        hl, hr = M(9, 75), M(118, 75)
        legs, tass = ((0, -3), (0, 0)), ((0, -1), (0, 2))
        cape = dict(rise=11, spread=1, flutter=2)
        face = 'grin'
    sl, sr = shoulders(U, S)

    def ua(fr):
        upper_arm(fr, sl, el)
        upper_arm(fr, sr, er)
    B.cape_fly(bf, **cape)
    body(bf, upper=U, shoulders=S, headx=Hd, torso=(1.2, 0.4), legs=legs, tassets=tass,
         skip=('cape', 'armR_front'), under_pauldrons=ua, head=head_variant(face))
    fore_arm(bf, el, wl)
    fore_arm(bf, er, wr)
    stamp(bf, hand('up_l'), hl[0], hl[1], shadow=False)
    stamp(bf, hand('up'), hr[0], hr[1], shadow=False)

    def back(fr):
        if step == 1:
            B.ghost(fr, bf, -6, 'B')

    def front(fr):
        B.speed_burst(fr, M(64, 78), 40 if step == 0 else 37, 72, n=26 if step == 0 else 34, seed=3 + step)
        for p, sm in ([((20, 116), False), ((96, 118), True)] if step == 0 else
                      [((4, 114), False), ((104, 115), False), ((28, 110), True)]):
            q = M(*p)
            FX.puff(fr, int(q[0]), int(q[1]), small=sm)
    return layered(back, bf, front)


@frame('lunge0')
def lunge0():
    return lunge(0)


@frame('lunge1')
def lunge1():
    return lunge(1)


# ============================================================== hug rig
def hug(face='grin', U=(0, -1), S=(0, 0), Hd=(0, -1), torso=(0.8, 0.0), cape=(0.0, 0.8, 0.0),
        el=(107, 170), er=(149, 170), band=(118, 138, 164), pl=None, legs=None, tass=None,
        fx_front=None, grip='open'):
    """band = (x_left, x_right, y_centre) of the hands; pl = (pose, origin, angle, scale) for the victim"""
    bf = R.Frame()
    sl, sr = shoulders(U, S)
    xl, xr, cy = band
    wl, wr = (xl + 2.4, cy + 0.8), (xr - 2.4, cy + 0.8)

    def ua(fr):
        upper_arm(fr, sl, el)
        upper_arm(fr, sr, er)
    body(bf, upper=U, shoulders=S, headx=Hd, torso=torso, cape=cape, legs=legs, tassets=tass,
         skip=('armR_front',), under_pauldrons=ua, head=head_variant(face))
    box = None
    if pl:
        tmp = R.Frame()
        P2.draw(tmp, *pl)
        pts = [(x, y) for y in range(B.FH) for x in range(B.FW) if tmp.px[y][x] is not None]
        R.cast_shadow(bf, pts, 1, 1)
        R.cast_shadow(bf, pts, 2, 2)
        box = P2.draw(bf, *pl)
    fore_arm(bf, el, wl)
    fore_arm(bf, er, wr)
    if grip == 'clasp':
        g = B.clasp(int(round(xr - xl)) + 1)
        rows = g.split(chr(10))
        x0, y0 = int(round(xl)), int(round(cy)) - len(rows) // 2
        pts = [(x0 + c, y0 + r) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch not in '. ']
        R.cast_shadow(bf, pts, 0, 1)
        bf.stamp(g, x0, y0)
    else:
        stamp(bf, hand('out_r'), xl + 4, cy, shadow=True)
        stamp(bf, hand('out_l'), xr - 4, cy, shadow=True)
    return layered(lambda fr: None, bf, fx_front), box


def mp(p):
    q = M(*p)
    return (int(round(q[0])), int(round(q[1])))


# ============================================================== whiff
@frame('whiff0')
def whiff0():
    """arms slam shut on empty air: puffs of squeezed air, snap lines"""
    def front(fr):
        for p in [(55, 80), (68, 78), (61, 74)]:
            q = mp(p)
            FX.puff(fr, q[0], q[1], small=True)
        B.emphasis(fr, M(64, 60), 29, 35, [-160, -140, -40, -20])
    xl, cy = M(55, 90)
    xr, _ = M(73, 90)
    fr, _ = hug(face='strain', U=(0, 2), S=(0, -2), Hd=(0, 2), torso=(1.6, 0.4), cape=(0.0, 2.4, 1.6),
                el=M(36, 97), er=M(91, 97), band=(xl, xr, cy), legs=((0, 0), (0, 0)), tass=((0, 1), (0, 1)),
                fx_front=front, grip='clasp')
    return fr


@frame('whiff1')
def whiff1():
    """off balance: teeters forward onto one foot, arms flung out, sweating - punish window"""
    bf = R.Frame()
    U, S, Hd = (3, 2), (1, 0), (2, 1)
    sl, sr = shoulders(U, S)
    el, er, wl, wr = M(18, 78), M(112, 102), M(8, 66), M(121, 112)

    def ua(fr):
        upper_arm(fr, sl, el)
        upper_arm(fr, sr, er)
    body(bf, upper=U, shoulders=S, headx=Hd, cape=(-3.2, 2.4, 0.8), torso=(1.2, 0.4),
         legs=((0, -5), (0, 0)), tassets=((2, -2), (2, 1)), skip=('armR_front',), under_pauldrons=ua,
         head=head_variant('wobble'))
    fore_arm(bf, el, wl)
    fore_arm(bf, er, wr)
    stamp(bf, hand('up_l'), *M(10, 58), shadow=False)
    stamp(bf, hand('down'), *M(118, 118), shadow=False)

    def front(fr):
        for p in [(26, 125), (44, 125)]:
            x0, y0 = mp(p)
            for dx, dy in ((0, 0), (1, -1), (2, -1), (3, 0)):
                if fr.get(x0 + dx, y0 + dy) is None:
                    fr.set(x0 + dx, y0 + dy, 'W')
        for p0, p1 in [((98, 118), (101, 116)), ((101, 114), (104, 112))]:
            B.line(fr, mp(p0), mp(p1), 'W')
        for p in [(50, 44), (88, 40), (94, 52)]:
            q = mp(p)
            FX.sweat(fr, q[0], q[1])
    return layered(lambda fr: None, bf, front)


# ============================================================== grab + squeeze
def band_of(xl, xr, y):
    a, b = M(xl, y), M(xr, y)
    return (a[0], b[0], a[1])


@frame('grab')
def grab():
    def front(fr):
        B.emphasis(fr, M(64, 60), 27, 34, [-160, -140, -120, -60, -40, -20])
    fr, box = hug(face='grin', pl=(P2.HUGGED, M(64, 94), 0, PS), band=band_of(47, 81, 88), el=M(28, 97), er=M(99, 97),
                  U=(0, -1), Hd=(0, -2))
    front(fr)
    fr.box = box
    return fr


@frame('squeeze0')
def squeeze0():
    """CRUSH (damage tick): hands clamp in, shoulders hunch, head sinks, belly bulges; victim squashed flat, impact pops"""
    fr, box = hug(face='crush', U=(0, 1), S=(0, -2), Hd=(0, 1), torso=(2.8, 0.8), cape=(0.0, 2.4, 0.0),
                  pl=(P2.SQUASH, M(64, 95), 0, PS), band=band_of(46, 82, 95), el=M(30, 101), er=M(97, 101))
    B.emphasis(fr, M(64, 62), 29, 35, [-165, -145, -125, -55, -35, -15])
    for sx in (-1, 1):
        for dy in (-3, 0, 3):
            x, y = M(64 + sx * 50, 96)
            B.line(fr, (x, y + dy), (x + sx * 3, y + dy - 1), 'W')
    for p, big in [((44, 92), True), ((84, 92), True), ((64, 70), False)]:
        q = mp(p)
        B.pop_star(fr, q[0], q[1], big)
    fr.box = box
    return fr


@frame('squeeze1')
def squeeze1():
    """HOLD: still clamped, victim dazed with stars"""
    fr, box = hug(face='strain', U=(0, 0), S=(0, -1), Hd=(0, -2), torso=(1.6, 0.4), cape=(0.0, 1.2, 0.0),
                  pl=(P2.DAZED, M(64, 94), 0, PS), band=band_of(48, 80, 89), el=M(30, 98), er=M(97, 98))
    B.stars(fr, mp((66, 74)), 1)
    fr.box = box
    return fr


@frame('squeeze2')
def squeeze2():
    """LOOSEN: grip eases a touch, shoulders drop, victim sags and gasps (then the crush repeats)"""
    fr, box = hug(face='grin', U=(0, -1), S=(0, 0), Hd=(0, -2), torso=(0.8, 0.0), cape=(0.0, 0.8, 0.0),
                  pl=(P2.LOOSE, M(64, 95), 0, PS), band=band_of(46, 82, 90), el=M(28, 99), er=M(99, 99))
    B.stars(fr, mp((64, 75)), 2)
    q = mp((75, 79))
    FX.sweat(fr, q[0], q[1])
    fr.box = box
    return fr


# ============================================================== toss
@frame('toss0')
def toss0():
    """flings the crushed victim up and away with his left arm (viewer-right); the other arm swings back"""
    bf = R.Frame()
    U, S, Hd = (2, -2), (1, -2), (2, -2)
    sl, sr = shoulders(U, S)
    el, er, wl, wr = M(20, 100), M(111, 72), M(10, 108), M(117, 56)

    def ua(fr):
        upper_arm(fr, sl, el)
        upper_arm(fr, sr, er)
    body(bf, upper=U, shoulders=S, headx=Hd, cape=(-2.4, 1.6, 1.6), torso=(0.4, 0.0),
         legs=((0, 0), (0, 0)), tassets=((0, 0), (1, 0)), skip=('armR_front',), under_pauldrons=ua,
         head=head_variant('roar'))
    fore_arm(bf, el, wl)
    stamp(bf, hand('down_l'), *M(9, 115), shadow=False)
    fr = layered(lambda f: None, bf, None)
    c = M(100, 84)
    FX.smear_arc(fr, (c[0], c[1]), 22, 1, 5, 195, 272)
    fore_arm(fr, er, wr)
    stamp(fr, hand('up'), *M(116, 49), shadow=False)
    for p0, p1 in [((88, 50), (97, 42)), ((92, 55), (101, 47)), ((95, 44), (101, 38))]:
        B.line(fr, mp(p0), mp(p1), 'W')
    fr.box = P2.draw(fr, P2.FLYING, M(106, 28), -35, PS)
    return fr


BREATH_BIG = """
......kkk...
....kkAWWk..
..kkAWWWAWk.
.kAWWAAWWAk.
kWWAABBAAk..
.kkBBkkBk...
...kk..k....
"""


@frame('toss1')
def toss1():
    """exhales, satisfied: arms drop, breath puff"""
    bf = R.Frame()
    U, S, Hd = (0, 2), (0, 1), (0, 1)
    sl, sr = shoulders(U, S)
    el, er, wl, wr = M(27, 102), M(100, 102), M(30, 114), M(97, 114)

    def ua(fr):
        upper_arm(fr, sl, el)
        upper_arm(fr, sr, er)
    body(bf, upper=U, shoulders=S, headx=Hd, cape=(-0.8, 0.4, 0.0), torso=(1.2, 0.4), skip=('armR_front',),
         under_pauldrons=ua, head=head_variant('exhale'))
    fore_arm(bf, el, wl)
    fore_arm(bf, er, wr)
    R.fist(bf, *M(31, 118))
    R.fist(bf, *M(96, 118))

    def front(fr):
        fr.stamp(BREATH_BIG, 141, 137)
    return layered(lambda f: None, bf, front)


# ============================================================== retrieve
@frame('retrieve0')
def retrieve0():
    """turns back to the planted sword, grabs the end of the crossguard and starts wrenching it out"""
    bf = R.Frame()
    U, S, Hd = (-4, -1), (0, 0), (-2, 0)
    sl = shoulders(U, S)[0]
    el = (91, 150)
    fist_c = (B.SWX + 17, B.GUARD_Y - 3)

    def ua(fr):
        upper_arm(fr, sl, el)
    body(bf, upper=U, shoulders=S, headx=Hd, cape=(1.6, 0.4, 0.0), torso=(0.4, 0.0), under_pauldrons=ua,
         head=head_variant('look'))

    def back(fr):
        B.sword_upright(fr, lift=3)
        B.ground_lip(fr)
        FX.puff(fr, B.SWX - 24, 179)
        FX.puff(fr, B.SWX + 12, 181, small=True)

    def front(fr):
        fore_arm(fr, el, (fist_c[0] + 2, fist_c[1] + 4))
        R.fist(fr, *fist_c)
        for x, y in [(B.SWX - 20, 170), (B.SWX + 18, 172)]:
            fr.stamp(B.CLOD, x, y)
        B.emphasis(fr, fist_c, 7, 9, [-120, -90, -60])
    return layered(back, bf, front)


@frame('retrieve1')
def retrieve1():
    """rips it out and swings it up onto his shoulder, landing in the v2 idle pose"""
    fr = R.Frame()
    FX.smear_arc(fr, (96, 150), 58, 2, 10, 118, 250)
    R.compose(fr)
    R.idle_weapon(fr)
    for x, y in [(62, 170), (70, 156), (86, 176)]:
        fr.stamp(B.CLOD, x, y)
    FX.puff(fr, B.SWX - 6, 182, small=True)
    return fr


def render(i):
    fr = F[ORDER[i]]()
    B.seal(fr)
    return fr
