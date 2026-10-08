"""Liam's FULL pose sheets (after the approval pass): every sheet in Scripts/LiamArtLayout.gd ANIMS, in
96x96 cells, liam.png at (16, 32), anchor point (48, 96); plus liam_juggle (128x96), liam_leap_shadow and
liam_shadow. Every frame is composed from his approved rig (le_poses / le_posedefs / le_parts), so his
identity stays pixel-exact; per-frame points (staff tip, mouth, staff butt, head top, daze) are returned
with the frames for anchors.json.

Sheet functions return a list of (canvas, points) with points in cell texels.
"""
import math

import numpy as np

import le_rig as R
import le_staff as S
import le_poses as P
import le_posedefs as D
import le_parts as X

FW = FH = 96
BODY = P.BODY


def B(x, y):
    return P.P(x, y)


def lay():
    return R.blank(FW, FH)


def comp(layers, staff=None):
    """Compose the layers; if `staff` (one of them) is given, its keyline is sel-outed where it crosses
    his figure: the staff is new, so where it lies over him its edge is its own darkest wood (g), not
    black - his approved lines are never touched."""
    full = R.compose([l for l in layers if l is not None], FW, FH)
    if staff is not None:
        under = R.compose([l for l in layers if l is not None and l is not staff], FW, FH)
        m = (staff == '#') & (full == '#') & (under != '.') & (under != '#')
        full[m] = 'g'
    return full


# ------------------------------------------------------------------ arms (body coords) reused across sheets
def far_staff_side(dx=0, dy=0, orb='neutral', butt_y=61.5, x=4.5):
    """Pose a's arm: staff upright at his side, fist at shoulder height."""
    A = P.arm(delt=(11.0, 31.5, 5.3), up=(10, 33, 6, 40, 4.8, 4.0), fore=(6, 40, 5, 33, 3.6, 3.2), dx=dx, dy=dy)
    st = P.staff_line((x + dx, butt_y + dy), (x + dx, butt_y - 53 + dy), orb=orb)
    return A, st, B(x + dx, 30 + dy), B(x + dx + 0.5, butt_y - 53 + dy + 0.5)


def far_staff_raised(dx=0, dy=0, orb='water', lift=0.0):
    A = P.arm(delt=(11.5, 30.5, 5.2), up=(11, 31, 6.5, 22, 4.6, 3.6), fore=(6.5, 22, 6, 15, 3.4, 3.1), dx=dx, dy=dy)
    st = P.staff_line((6.0 + dx, 61.5 - lift + dy), (6.0 + dx, 8.5 - lift + dy), orb=orb)
    return A, st, B(6.0 + dx, 19.0 + dy), B(6.5 + dx, 9.0 - lift + dy)


def near_hang(dx=0, dy=0):
    """His near arm hanging (the mirror of the approved far arm's line)."""
    A = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 33, 54, 40, 4.8, 4.0), fore=(54, 40, 56, 46, 3.6, 3.3), dx=dx, dy=dy)
    return A, B(56.5 + dx, 49 + dy)


def add_fist(cv, xy, rows=None):
    P.fist_at(cv, xy[0], xy[1], rows)


def water_ring(ox, oy, rx=9.8, ry=4.2, tilt=-16, a0=-60, span=380, thick=1.25):
    pts, radii, fr = [], [], []
    t_ = math.radians(tilt)
    for i in range(121):
        t = math.radians(a0 + span * i / 120)
        ex, ey = rx * math.cos(t), ry * math.sin(t)
        pts.append((ox + ex * math.cos(t_) - ey * math.sin(t_), oy + 2 + ex * math.sin(t_) + ey * math.cos(t_)))
        u = i / 120
        radii.append(0.5 + thick * math.sin(math.pi * u) * (0.55 + 0.45 * max(0, math.sin(t))))
        fr.append(math.sin(t) > -0.1)
    return D.ribbon_fx(pts, radii, lambda i: fr[i])


def dots(cv, pts, ch):
    D.dots(cv, pts, ch)


def sweat(cv, bx, by):
    D.sweat_drop(cv, *B(bx, by))


def lines(cv, segs, ch='#'):
    for (x0, y0, x1, y1) in segs:
        R.line(cv, *B(x0, y0), *B(x1, y1), ch)


# ------------------------------------------------------------------ cutscene: get up, wipe, talks
def get_up():
    """3 frames (also stand_up): sat -> squat with hands on knees -> standing."""
    out = []
    # 0: sat up straighter, hands pushing on the floor, effort
    dy = 12
    Hd = X.head(X.WINCE, None)
    torso = P.body('torso', dy=dy)
    A = P.arm(delt=(11.0, 31.5, 5.3), up=(10, 33, 5, 40, 4.8, 4.0), fore=(5, 40, 2, 45, 3.6, 3.3), dy=dy)
    N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 32.5, 55, 40, 4.7, 4.1), fore=(55, 40, 58, 45, 3.8, 3.4), dy=dy)
    cv = comp([D.tails(dy - 3, 'droop', dx=0), X.legs_sit(hip_y=85), torso, A, N, P.place(Hd, dy=dy - 3)])
    add_fist(cv, B(1, 47 + dy))
    add_fist(cv, B(59, 47 + dy))
    fx = lay()
    for (x, y, r) in ((6, 94, 2.8), (90, 94, 2.8)):
        D.puff(fx, x, y, r)
    cv = comp([fx, cv])
    sweat(cv, 40, dy - 4)
    out.append((cv, {}))
    # 1: squat, hands on knees, rising
    sq = 5
    torso = P.body('torso', dy=sq)
    A = P.arm(delt=(11.0, 31.5, 5.3), up=(10, 33, 13, 41, 4.8, 4.0), fore=(13, 41, 18, 47, 3.6, 3.3), dy=sq)
    N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 33, 47, 41, 4.7, 4.1), fore=(47, 41, 42, 47, 3.8, 3.4), dy=sq)
    cv = comp([D.tails(sq, 'down'), P.place(X.legs_squat(sq)), torso, A, N, P.place(X.head(X.WINCE, None), dy=sq)])
    add_fist(cv, B(18.5, 49 + sq))
    add_fist(cv, B(41.5, 49 + sq))
    fx = lay()
    for (x, y, r) in ((10, 93, 3.2), (86, 93, 3.2), (4, 91, 2.2), (92, 91, 2.2)):
        D.puff(fx, x, y, r)
    cv = comp([fx, cv])
    out.append((cv, {}))
    # 2: standing, a breath, the approved stance and arms
    cv = comp([D.tails(0, 'down'), P.body('legs'), P.body('torso'), P.body('far'), P.body('near'),
               P.place(X.head('smirk', None))])
    out.append((cv, {}))
    return out


def wipe():
    """2-frame loop: the forearm dragged across his beard, slime flicking off, a grimace."""
    out = []
    for k, (fx_, fy_) in enumerate(((27.0, 21.0), (35.0, 21.5))):
        N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 31, 53, 24, 4.6, 3.8), fore=(53, 24, fx_ + 3, fy_, 3.6, 3.2))
        Hd = X.head(X.WINCE, 'flash')
        cv = comp([D.tails(0, 'mid' if k else 'down'), P.body('legs'), P.body('torso'), P.body('far'),
                   P.place(Hd), N])
        add_fist(cv, B(fx_, fy_ + 1))
        drops = [(fx_ - 7, fy_ - 3), (fx_ - 9, fy_ + 1), (fx_ - 5, fy_ - 6)] if k == 0 else \
                [(fx_ + 8, fy_ - 4), (fx_ + 10, fy_), (fx_ + 6, fy_ - 7)]
        for (x, y) in drops:
            X_, Y_ = B(x, y)
            R.blk(cv, int(X_), int(Y_), [".l.", "lMl", ".M."])
        out.append((cv, {}))
    return out


def talk_thanks():
    """Talking / shut: sheepish, hand scratching the back of his head, a sweat drop."""
    out = []
    for mouth in (X.TALK, None):
        N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 31, 55, 21, 4.6, 3.8), fore=(55, 21, 46, 9, 3.6, 3.2))
        cv = comp([D.tails(0), P.body('legs'), P.body('torso'), P.body('far'), N, P.place(X.head(mouth, None))])
        add_fist(cv, B(44.5, 6.5))
        # the head sits in front of the hand's lower half
        Hl = P.place(X.head(mouth, None))
        top = Hl.copy()
        top[:, :B(38, 0)[0]] = '.'
        top[:B(0, 9)[1], :] = '.'
        R.composite(cv, top)
        sweat(cv, 35, 2)
        out.append((cv, {}))
    return out


def talk_explain():
    """Talking / shut: lecturing, index finger up by his shoulder, other hand on the hip, a know-it-all glint."""
    out = []
    for mouth in (X.SMIRK_TALK, 'smirk'):
        A = P.arm(delt=(11.5, 30.5, 5.2), up=(11, 31, 6, 23, 4.6, 3.6), fore=(6, 23, 5, 15, 3.4, 3.1))
        cv = comp([D.tails(0), P.body('legs'), P.body('torso'), P.body('near'), P.place(X.head(mouth, 'dim')), A])
        R.blk(cv, *B(-2, 3), X.FIST_UP)
        out.append((cv, {}))
    return out


def talk_elements():
    """Talking / shut: 'all four' - four fingers up, the other fist on his own chest; proud glare."""
    out = []
    for mouth in (X.TALK, None):
        N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 31, 56, 23, 4.6, 3.8), fore=(56, 23, 57, 14, 3.6, 3.2))
        A = P.arm(delt=(11.0, 31.5, 5.3), up=(10, 33, 13, 40, 4.8, 4.0), fore=(13, 40, 21, 36, 3.6, 3.2))
        cv = comp([D.tails(0, 'up'), P.body('legs'), P.body('torso'), A, N, P.place(X.head(mouth, 'flash'))])
        add_fist(cv, B(23, 35))
        X.hand(cv, X.FOUR, *B(57.5, 8))
        out.append((cv, {}))
    return out


def talk_smug():
    """Talking / shut: the approved glasses push held - finger on the bridge, lenses flashing, the smirk."""
    out = []
    for mouth in (X.SMIRK_TALK, 'smirk'):
        A = P.arm(delt=(11.5, 30.5, 5.2), up=(11, 31, 7, 25, 4.6, 3.5), fore=(7, 25, 17, 21, 3.4, 3.1))
        Hd = P.place(X.head(mouth, 'flash'), dy=-1)
        cv = comp([D.tails(-1, 'hold'), P.body('legs'), P.body('torso'), P.body('near'), Hd, A])
        R.blk(cv, *B(15, 11), X.FIST_UP)
        tw = lay()
        R.star(tw, *B(34, 12), 2)
        R.composite(cv, tw)
        out.append((cv, {}))
    return out


def talk_staff():
    """Talking / shut: 'kept it somewhere safe' - staff held up at his side, patting his belly."""
    out = []
    for mouth in (X.TALK, None):
        A, st, fist, orb = far_staff_side()
        N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 32.5, 53, 40, 4.7, 4.1), fore=(53, 40, 45, 40, 3.8, 3.4))
        cv = comp([D.tails(0), P.body('legs'), P.body('torso'), N, P.place(X.head(mouth, None)), st, A], staff=st)
        add_fist(cv, fist)
        add_fist(cv, B(42.5, 40))
        out.append((cv, {'staff_tip': orb}))
    return out


# ------------------------------------------------------------------ laugh, staff pull, slam rise, ride
def laugh():
    """4-frame loop: the anime laugh - head thrown back, back of the hand at the mouth, shaking."""
    out = []
    line_sets = [
        ((45, -2, 48, -5), (48, 3, 52, 1), (49, 9, 53, 9), (14, -1, 11, -4)),
        ((46, -4, 49, -7), (49, 1, 53, -1), (50, 7, 54, 7), (13, -3, 10, -6), (16, -6, 15, -9)),
        ((44, -3, 47, -6), (48, 2, 53, 1), (49, 8, 52, 10), (13, 0, 10, -2)),
        ((46, -5, 50, -7), (49, 0, 53, -2), (50, 6, 54, 5), (14, -4, 11, -7), (17, -7, 17, -10)),
    ]
    for k in range(4):
        up = k % 2
        A = P.arm(delt=(11.5, 30.5, 5.2), up=(11, 31, 7, 24, 4.6, 3.5), fore=(7, 24, 15, 21, 3.4, 3.1), dy=-up)
        Hd = P.place(X.head('laugh', 'flash'), dy=-2 - up)
        cv = comp([D.tails(-2 - up, 'up' if up else 'flick'), P.body('legs'), P.body('torso', dy=-up),
                   P.body('near', dy=-up), Hd, A])
        R.blk(cv, *B(13, 16 - up), X.BACKHAND)
        fx = lay()
        for (x0, y0, x1, y1) in line_sets[k]:
            R.line(fx, *B(x0, y0), *B(x1, y1))
        R.composite(cv, fx)
        out.append((cv, {}))
    return out


def slime(cv, pts):
    for i, (x, y) in enumerate(pts):
        X_, Y_ = B(x, y)
        if 0 <= int(Y_) < FH and 0 <= int(X_) < FW:
            cv[int(Y_), int(X_)] = '8' if i % 3 else 'W'


def staff_pull():
    """5 frames: reach in, tug, tug, out, planted."""
    out = []
    # 0: reach - hand at the stretched mouth
    N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 31, 53, 21, 4.6, 3.8), fore=(53, 21, 36, 19, 3.6, 3.2))
    cv = comp([D.tails(-2, 'mid'), P.body('legs'), P.body('torso'), P.body('far'),
               P.place(X.head('laugh', 'flash'), dy=-2), N])
    add_fist(cv, B(33, 18.5))
    slime(cv, [(30, 24), (30, 25), (26, 24)])
    out.append((cv, {}))
    # 1: tug - the ring head out, gripped, shaft to the mouth
    N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 31, 54, 19, 4.6, 3.8), fore=(54, 19, 42, 9, 3.6, 3.2))
    st = P.staff_line((28.5, 20.5), (42.0, -2.0), orb='neutral', ferrule=False)
    cv = comp([D.tails(-3, 'mid'), P.body('legs'), P.body('torso'), P.body('far'),
               P.place(X.head('laugh', 'flash'), dy=-3), st, N], staff=st)
    add_fist(cv, B(39.5, 7.5))
    slime(cv, [(30, 24), (31, 22), (34, 16), (35, 17), (29, 26)])
    out.append((cv, {}))
    # 2: second tug - the approved key pose f
    cv, m = D.pose_f_gag()
    out.append((cv, {}))
    # 3: out - the butt leaves his lips on a string of goo; staff held high
    N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 31, 56, 19, 4.6, 3.8), fore=(56, 19, 52, 4, 3.6, 3.2))
    st = P.staff_line((30.5, 17.0), (60.5, -24.0), orb='neutral')
    cv = comp([D.tails(-2, 'up'), P.body('legs'), P.body('torso'), P.body('far'),
               P.place(X.head(X.TALK, 'flash'), dy=-2), st, N], staff=st)
    add_fist(cv, B(51.5, 1.5))
    slime(cv, [(29, 20), (29, 21), (30, 19), (28, 23), (31, 26), (31, 27), (27, 28)])
    out.append((cv, {}))
    # 4: planted at his side, satisfied
    A, st, fist, orb = far_staff_side()
    cv = comp([D.tails(0), P.body('legs'), P.body('torso'), P.body('near'), P.place(X.head('big', None)), st, A], staff=st)
    add_fist(cv, fist)
    slime(cv, [(3, 62), (6, 63), (8, 62), (5, 58)])
    out.append((cv, {'staff_tip': orb}))
    return out


def slam_rise():
    """3 frames: staff hauled up, driven into the floor (the summoning slam), braced as the pillar lifts."""
    out = []
    # 0: raise, crouching a touch, the orb waking green
    dy = 1
    A = P.arm(delt=(11.0, 31.5, 5.3), up=(10, 33, 6, 26, 4.7, 3.8), fore=(6, 26, 3, 18, 3.6, 3.2), dy=dy)
    st = P.staff_line((3.0, 50.0 + dy), (3.0, -3.0 + dy), orb='earth')
    cv = comp([D.tails(dy, 'down'), P.body('legs'), P.body('torso', dy=dy), P.body('near', dy=dy),
               P.place(X.head(X.WINCE, 'flash'), dy=dy), st, A], staff=st)
    add_fist(cv, B(3, 16 + dy))
    out.append((cv, {'staff_butt': B(3.0, 50.0 + dy)}))
    # 1: impact - key pose g's body without its in-cell dust (the slam burst FX goes on the butt)
    dy = 3
    A = P.arm(delt=(11.0, 31.5, 5.3), up=(10, 33, 6, 27, 4.7, 3.8), fore=(6, 27, 3, 20, 3.6, 3.2), dy=dy)
    st = P.staff_line((2.5, 63.0), (2.5, 10.0), orb='earth')
    cv = comp([D.tails(dy, 'up'), P.body('legs'), P.body('torso', dy=dy), P.body('near', dy=dy),
               P.place(X.head('shout', 'flash'), dy=dy), st, A], staff=st)
    add_fist(cv, B(3, 18 + dy))
    lines(cv, [(-4, 6, -4, 11), (9, 5, 9, 10), (-2, 0, -2, 4)], 'w')
    out.append((cv, {'staff_butt': B(2.5, 63.0)}))
    # 2: braced on the rising pillar - narrow stance, staff held at his side, grin
    dy = 1
    A, st, fist, orb = far_staff_side(dy=dy, orb='earth')
    cv = comp([D.tails(dy, 'up'), P.place(P.legs_narrow()), P.body('torso', dy=dy), P.body('near', dy=dy),
               P.place(X.head(X.TALK, 'flash'), dy=dy), st, A], staff=st)
    add_fist(cv, fist)
    out.append((cv, {'staff_butt': B(4.5, 61.5 + dy), 'staff_tip': orb}))
    return out


def ride():
    """2-frame loop: riding the pillar up - narrow stance, staff held, grin, tails streaming."""
    out = []
    for k in range(2):
        A, st, fist, orb = far_staff_side(dy=-k)
        cv = comp([D.tails(-k, 'up' if k == 0 else 'flick'), P.place(P.legs_narrow()), P.body('torso', dy=-k),
                   P.body('near', dy=-k), P.place(X.head(X.TALK if k else 'big', 'flash'), dy=-1 - k), st, A], staff=st)
        add_fist(cv, fist)
        out.append((cv, {'staff_tip': orb}))
    return out


# ------------------------------------------------------------------ perch: idle, casts, wobble, steady, blast
def perch_idle():
    """4-frame loop: key pose a breathing - chin up and down a texel, tails swaying."""
    out = []
    for k, (hdy, tl) in enumerate(((-1, None), (-1, 'down'), (0, None), (0, 'mid'))):
        A, st, fist, orb = far_staff_side()
        cv = comp([D.tails(hdy, tl), P.place(P.legs_narrow()), P.body('torso'), P.body('near'),
                   P.place(X.head('smirk', 'dim'), dy=hdy), st, A], staff=st)
        add_fist(cv, fist)
        out.append((cv, {'staff_tip': orb}))
    return out


def cast_left():
    """3 frames: wind-up (key pose b), the swing out over the left half, the follow-through."""
    out = []
    cv, m = D.pose_b_cast()
    out.append((cv, {'staff_tip': m['orb']}))
    for k in (1, 2):
        A = P.arm(delt=(11.5, 30.5, 5.2), up=(11, 31, 5, 24, 4.6, 3.6), fore=(5, 24, 3, 17, 3.4, 3.1))
        if k == 1:
            butt, headc, fist = (13.0, 58.0), (4.0, 6.5), (3.5, 19.0)
        else:
            butt, headc, fist = (10.0, 60.0), (4.5, 7.5), (4.0, 20.0)
        st = P.staff_line(butt, headc, orb='water')
        ox, oy = B(headc[0] + 0.5, headc[1] + 0.5)
        Hd = P.place(X.head('big', 'flash'), dy=-1)
        fx_b, fx_f = water_ring(ox, oy, rx=8.5 if k == 1 else 6.5, ry=3.6, tilt=-30 if k == 1 else -20)
        cv = comp([D.tails(-1, 'up' if k == 1 else 'mid'), P.place(P.legs_narrow()), P.body('torso'),
                   P.body('near'), Hd, fx_b, st, A, fx_f], staff=st)
        add_fist(cv, B(*fist))
        spray = lay()
        if k == 1:
            pts, radii = [], []
            for i in range(14):
                u = i / 13
                pts.append((ox - 3 - u * 5, oy + 5 + u * 14 + math.sin(u * 4) * 1.2))
                radii.append(1.5 - 1.0 * u)
            bk, fr_ = D.ribbon_fx(pts, radii, lambda i: True)
            R.composite(spray, fr_)
            dots(spray, [(ox - 8, oy + 6), (ox - 7, oy + 11), (ox - 6, oy + 17), (ox - 3, oy + 22),
                         (ox + 9, oy - 5), (ox - 6, oy - 6)], 'l')
            dots(spray, [(ox - 7, oy + 8), (ox - 5, oy + 14), (ox - 3, oy + 19)], 'b')
        else:
            dots(spray, [(ox - 6, oy + 10), (ox - 5, oy + 14), (ox - 3, oy + 18), (ox + 6, oy + 9)], 'l')
        spray[:, :P.PERCH_BOX['left']] = '.'
        R.composite(cv, spray)
        out.append((cv, {'staff_tip': (ox, oy)}))
    return out


def cast_right():
    """3 frames: both arms up (staff raised, palm up), the palm thrust out over the right half with water
    streaming off it, the follow-through."""
    out = []
    for k in range(3):
        A, st, fist, orb = far_staff_raised(orb='water')
        if k == 0:
            N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 31, 56, 23, 4.6, 3.8), fore=(56, 23, 58, 15, 3.6, 3.2))
            palm = B(58.5, 11)
        elif k == 1:
            N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 31.5, 57, 29, 4.6, 3.9), fore=(57, 29, 61, 25, 3.6, 3.2))
            palm = B(62.5, 21)
        else:
            N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 32, 57, 33, 4.6, 3.9), fore=(57, 33, 60, 31, 3.6, 3.2))
            palm = B(61.5, 27)
        ox, oy = orb
        fx_b, fx_f = water_ring(ox, oy, rx=7.0 if k else 5.5, ry=3.2)
        cv = comp([D.tails(-1, 'up'), P.place(P.legs_narrow()), P.body('torso'), N,
                   P.place(X.head('big', 'flash'), dy=-1), fx_b, st, A, fx_f], staff=st)
        add_fist(cv, fist)
        X.hand(cv, X.OPEN_PALM, *palm)
        spray = lay()
        px_, py_ = palm
        if k == 1:
            pts, radii = [], []
            for i in range(16):
                u = i / 15
                pts.append((px_ + 2 + u * 13, py_ - 4 + u * 10 + math.sin(u * 5) * 1.5))
                radii.append(1.6 - 1.1 * u)
            bk, fr_ = D.ribbon_fx(pts, radii, lambda i: True)
            R.composite(spray, fr_)
            dots(spray, [(px_ + 8, py_ - 7), (px_ + 12, py_ - 3), (px_ + 15, py_ + 1), (px_ + 10, py_ + 8)], 'l')
        elif k == 2:
            dots(spray, [(px_ + 5, py_ + 2), (px_ + 9, py_ + 6), (px_ + 12, py_ + 11), (px_ + 7, py_ + 12)], 'l')
            dots(spray, [(px_ + 8, py_ + 4), (px_ + 11, py_ + 9)], 'b')
        spray[:, P.PERCH_BOX['right'] + 1:] = '.'
        R.composite(cv, spray)
        out.append((cv, {'staff_tip': orb}))
    return out


def wobble():
    """4-frame loop: pitched left with the near foot up and the near arm windmilling (key pose c) ->
    arms flung wide -> pitched right with the far foot up -> arms wide again."""
    out = []
    from le_poses import legs_lift_near
    lean = -2
    A = P.arm(delt=(11.0, 31.5, 5.3), up=(10, 33, 5, 39, 4.8, 4.0), fore=(5, 39, 4, 33, 3.6, 3.2), dx=lean)
    N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 30, 57, 23, 4.6, 3.8), fore=(57, 23, 60, 14, 3.6, 3.2), dx=lean)
    st = P.staff_line((9.0, 60.0), (5.5, 8.0), orb='neutral')
    Hd = P.place(X.head('gasp', 'flash'), dx=lean - 2, dy=1)
    fx = lay()
    hx_, hy_ = B(60 + lean, 12)
    D.motion_arc(fx, hx_ - 6, hy_ + 10, 11.0, -150, -15, ramp=('v', 'w', 'W'), thick=1.5)
    D.motion_arc(fx, hx_ - 6, hy_ + 10, 11.0, 15, 95, ramp=('v', 'w'), thick=1.3)
    D.motion_arc(fx, hx_ - 6, hy_ + 10, 7.5, -140, -40, ramp=('v', 'w'), thick=0.9)
    cv = comp([D.tails(1, 'flick', dx=lean - 2), fx, P.place(legs_lift_near(up=6, out=3)), P.body('torso', dx=lean),
               N, Hd, st, A], staff=st)
    add_fist(cv, B(4 + lean, 31))
    add_fist(cv, B(60 + lean, 12))
    sweat(cv, 39, 0)
    wob = lay()
    for (x0, y0, x1, y1) in ((0, 44, -2, 47), (-2, 48, -2, 51), (-2, 52, 0, 55),
                             (63, 42, 65, 45), (65, 46, 65, 50), (65, 51, 63, 54)):
        R.line(wob, *B(x0, y0), *B(x1, y1), 'v')
    cv = comp([wob, cv])
    out.append((cv, {}))
    for k in (1, 2, 3):
        if k == 2:
            lean = 2
            legs = P.place(X.legs_lift_far())
            A = P.arm(delt=(11.0, 31.0, 5.2), up=(10.5, 30, 5, 24, 4.6, 3.8), fore=(5, 24, 6, 16, 3.6, 3.2), dx=lean)
            st = P.staff_line((12.0, 58.0), (4.0 + lean, 7.5), orb='neutral')
            N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 33, 56, 38, 4.7, 4.0), fore=(56, 38, 60, 42, 3.8, 3.4), dx=lean)
            nf = B(60 + lean, 44)
            ff = B(6 + lean, 15)
            hd = (lean + 2, 1)
            tl = 'flick'
        else:
            lean = 0
            legs = P.place(P.legs_narrow())
            A = P.arm(delt=(11.0, 31.5, 5.3), up=(10, 33, 5, 37, 4.8, 4.0), fore=(5, 37, 3, 31, 3.6, 3.2))
            st = P.staff_line((7.0, 58.0) if k == 1 else (6.0, 59.0), (5.0, 6.5), orb='neutral')
            y_n = 27 if k == 1 else 30
            N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 31, 57, y_n, 4.7, 4.0), fore=(57, y_n, 61, y_n - 3, 3.8, 3.4))
            nf = B(62, y_n - 4)
            ff = B(3, 29)
            hd = (0, 0)
            tl = 'mid' if k == 1 else 'up'
        Hd = P.place(X.head(X.TALK if k == 3 else 'gasp', 'flash'), dx=hd[0], dy=hd[1])
        cv = comp([D.tails(hd[1], tl, dx=hd[0]), legs, P.body('torso', dx=lean), N, Hd, st, A], staff=st)
        add_fist(cv, ff)
        add_fist(cv, nf)
        fx = lay()
        if k == 2:
            D.motion_arc(fx, ff[0] + 7, ff[1] + 9, 10.0, -30, -165, ramp=('v', 'w', 'W'), thick=1.4)
        R.composite(cv, fx)
        if k != 3:
            sweat(cv, 44 + (3 if k == 2 else 0), 2 + k % 2)
        else:
            dots(cv, [B(46, 3), B(47, 1), B(50, 5), B(12, 6), B(10, 8)], 'l')
            dots(cv, [B(46, 4), B(11, 7)], 'b')
        arcs = lay()
        if k in (1, 3):
            D.motion_arc(arcs, nf[0] - 6, nf[1] + (6 if k == 1 else -4), 8.0, -80 if k == 1 else 40,
                         20 if k == 1 else 140, ramp=('v', 'w', 'W'), thick=1.2)
            D.motion_arc(arcs, ff[0] + 6, ff[1] + 4, 8.0, 260 if k == 1 else 140, 160 if k == 1 else 240,
                         ramp=('v', 'w', 'W'), thick=1.2)
        for (x0, y0, x1, y1) in ((1, 46, -1, 49), (-1, 50, -1, 53), (62, 44, 64, 47), (64, 48, 64, 52)):
            R.line(arcs, *B(x0 + lean, y0), *B(x1 + lean, y1), 'v')
        arcs[:, :P.PERCH_BOX['left']] = '.'
        arcs[:, P.PERCH_BOX['right'] + 1:] = '.'
        arcs[:P.PERCH_BOX['top'], :] = '.'
        cv = comp([arcs, cv])
        out.append((cv, {}))
    return out


def steady():
    """1 frame: the round closes - feet planted, arms eased out, a relieved 'phew', a last sweat drop."""
    A, st, fist, orb = far_staff_side()
    N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 32, 56, 37, 4.7, 4.0), fore=(56, 37, 60, 37, 3.8, 3.4))
    cv = comp([D.tails(0, 'down'), P.place(P.legs_narrow()), P.body('torso'), N,
               P.place(X.head('blow', None)), st, A], staff=st)
    add_fist(cv, fist)
    add_fist(cv, B(61.5, 38))
    sweat(cv, 43, 3)
    return [(cv, {'staff_tip': orb})]


def blast():
    """3 frames: coil (staff drawn in to the chest, leaning back), the push (key pose d), the hold."""
    out = []
    for k in range(3):
        pull = 4 if k == 0 else 0
        A = P.arm(delt=(11.0, 31.5, 5.3), up=(11, 32, 16, 40, 4.8, 4.2), fore=(16, 40, 18 + pull, 37 - pull * 0.5, 3.8, 3.5))
        N = P.arm(delt=(49.0, 31.0, 5.3), up=(49, 32, 45, 40, 4.7, 4.1), fore=(45, 40, 42 - pull, 37 - pull * 0.5, 3.8, 3.5))
        y = 38.0 - pull * 0.5
        head_c = (58.0 - pull, y)
        st = P.staff_line((5.0 + pull, y), head_c, orb='air')
        hdy = -2 if k == 0 else -1
        mouth = X.WINCE if k == 0 else 'shout'
        Hd = P.place(X.head(mouth, 'flash'), dy=hdy)
        cx, cy = B(*head_c)
        fx = lay()
        if k == 0:
            D.wind_burst(fx, cx, cy, reach=9, spread=70, arcs=2)
        else:
            D.wind_burst(fx, cx - 1, cy + 1, reach=8, spread=70, arcs=2)
            mid = B(31, y + 2)
            D.wind_burst(fx, mid[0], mid[1] + 2, reach=22 if k == 1 else 18, spread=64, arcs=4, swirl=False)
        cv = comp([D.tails(hdy, 'up' if k else 'mid'), P.place(P.legs_narrow()), P.body('torso'), A, N, Hd, st, fx], staff=st)
        add_fist(cv, B(18 + pull, y + 0.5))
        add_fist(cv, B(42 - pull, y + 0.5))
        R.composite(cv, S.head_canvas('air'), int(round(cx - 0.5)) - 8, int(round(cy - 0.5)) - 8)
        out.append((cv, {'staff_tip': (cx, cy)}))
    return out


def breathe():
    """4 frames (liam_breathe.png): inhale (cheeks puffed), blow, blow, recover. No frost in the cell - the
    plume (liam_cold_breath.png) is pinned on the mouth point."""
    out = []
    for k in range(4):
        A, st, fist, orb = far_staff_side(orb='air')
        if k == 0:
            Hd, hdy, tl = X.head(X.PUFF, 'dim'), -1, 'down'
        elif k == 3:
            Hd, hdy, tl = X.head(X.TALK, 'dim'), 0, 'down'
        else:
            Hd, hdy, tl = X.head('blow', 'dim'), (0 if k == 1 else 1), ('mid' if k == 1 else 'flick')
        cv = comp([D.tails(hdy, tl), P.place(P.legs_narrow()), P.body('torso'), P.body('near'),
                   P.place(Hd, dy=hdy), st, A], staff=st)
        add_fist(cv, fist)
        mouth = B(27.5, 23 + hdy)
        fx = lay()
        if k == 0:
            for (x0, y0, x1, y1) in ((13, 22, 17, 23), (12, 25, 16, 25), (44, 22, 40, 23), (45, 25, 41, 25)):
                R.line(fx, *B(x0, y0), *B(x1, y1), 'w')
        elif k == 3:
            dots(fx, [B(28, 27), B(30, 28), B(27, 29)], 'w')
        R.composite(cv, fx)
        pts = {'mouth': mouth} if k in (1, 2) else {'mouth': mouth}
        out.append((cv, pts))
    return out


def slam():
    """4 frames (the tremor slam on the pillar top): lift, highest, impact, recoil. The staff drives down
    beside his near foot onto the slab; the burst FX goes on the reported butt."""
    out = []
    x = 49.0
    for k, (lift, dy, mouth) in enumerate(((8, 0, X.WINCE), (13, -1, X.WINCE), (0, 2, 'shout'), (2, 1, 'big'))):
        fist_y = 20 - lift * 0.35 + dy
        N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 33, 55, 27 - lift * 0.4, 4.7, 3.8),
                  fore=(55, 27 - lift * 0.4, x + 0.5, fist_y + 2, 3.6, 3.2), dy=0)
        butt = (x, 62.5 - lift)
        st = P.staff_line(butt, (x, 9.5 + (1.0 if k == 2 else 0.0)), orb='earth')
        A = P.arm(delt=(11.0, 31.5, 5.3), up=(10, 33, 6, 40, 4.8, 4.0), fore=(6, 40, 9, 45, 3.6, 3.3), dy=dy)
        cv = comp([D.tails(dy, 'up'), P.place(P.legs_narrow()), P.body('torso', dy=dy), A,
                   P.place(X.head(mouth, 'flash'), dy=dy), st, N], staff=st)
        add_fist(cv, B(x, fist_y))
        add_fist(cv, B(9.5, 47 + dy))
        if k == 2:
            lines(cv, [(55, 50, 58, 48), (56, 55, 60, 55), (41, 51, 38, 49)])
        out.append((cv, {'staff_butt': B(x, butt[1] + 0.5)}))
    return out


# ------------------------------------------------------------------ fall, downed, defeat
def flail_figure(stance='narrow', face=('gasp', 'flash'), staff=False):
    """A standing figure with both arms flung up - the base for the fall and juggle rotations."""
    legs = P.place(P.legs_narrow() if stance == 'narrow' else P.B64['legs'])
    A = P.arm(delt=(11.0, 31.0, 5.2), up=(10.5, 30, 5, 22, 4.6, 3.8), fore=(5, 22, 4, 13, 3.6, 3.2))
    N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 30, 56, 22, 4.6, 3.8), fore=(56, 22, 58, 13, 3.6, 3.2))
    cv = comp([D.tails(0, 'flick'), legs, P.body('torso'), A, N, P.place(X.head(*face))])
    add_fist(cv, B(4, 11))
    add_fist(cv, B(58.5, 11))
    return cv


def lying_figure(face=('dazed', 'swirl')):
    """Flat on his back, arms out: a standing KO figure turned 90 degrees (RotSprite), feet to the right."""
    legs = P.place(P.B64['legs'])
    A = P.arm(delt=(11.0, 31.5, 5.3), up=(10, 33, 4, 38, 4.8, 4.0), fore=(4, 38, 0, 43, 3.6, 3.3))
    N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 33, 56, 38, 4.7, 4.0), fore=(56, 38, 60, 43, 3.8, 3.4))
    cv = comp([D.tails(0, 'droop'), legs, P.body('torso'), A, N, P.place(X.head(*face))])
    add_fist(cv, B(-0.5, 45))
    add_fist(cv, B(60.5, 45))
    return cv


def dust(cv, puffs):
    D.puff  # noqa: B018 (keep the helper referenced)
    for (x, y, r) in puffs:
        D.puff(cv, x, y, r)


def fall():
    """4 frames in the standard cell: topples back off the stone, tumbles, crashes flat, bounces up into
    the dazed sit (downed frame 0 follows)."""
    out = []
    fig = flail_figure()
    for k, (ang, pv, opv) in enumerate(((-18, (48, 90), (50, 92)), (-110, (48, 62), (48, 58)))):
        f = X.rotsprite(fig, ang, pivot=pv, out_pivot=opv)
        arcs = lay()
        cx_, cy_ = (50, 60) if k == 0 else (48, 58)
        rr = 34 if k == 0 else 36
        a0 = -60 if k == 0 else 120
        if k == 1:
            for i in range(20):
                a = math.radians(-60 + i * 4)
                for t in range(2):
                    x_, y_ = cx_ + (rr - t) * math.cos(a), cy_ + (rr - t) * 0.85 * math.sin(a)
                    if 0 <= int(x_) < FW and 0 <= int(y_) < FH:
                        arcs[int(y_), int(x_)] = 'W' if i > 13 else ('w' if i > 6 else 'v')
        for i in range(28):
            a = math.radians(a0 + i * 4)
            for t in range(2):
                x_, y_ = cx_ + (rr - t) * math.cos(a), cy_ + (rr - t) * 0.85 * math.sin(a)
                if 0 <= int(x_) < FW and 0 <= int(y_) < FH:
                    arcs[int(y_), int(x_)] = 'W' if i > 18 else ('w' if i > 8 else 'v')
        cvf = comp([arcs, f])
        if k == 1:
            for (x_, y_, ch) in ((20, 30, 'l'), (21, 31, 'b'), (70, 26, 'l'), (71, 27, 'b'), (16, 40, 'l'), (75, 36, 'l')):
                cvf[y_, x_] = ch
        out.append((cvf, {}))
    flat = X.rotsprite(lying_figure(face=(X.WINCE, 'flash')), -90, pivot=(48, 64), out_pivot=(48, 78))
    fx = lay()
    dust(fx, [(14, 90, 5), (82, 90, 5), (48, 93, 4)])
    cv = comp([flat, fx])
    R.star(cv, 48, 74, 4, diag=1)
    out.append((cv, {}))
    cv, m = D.pose_h_dazed()
    out.append((cv, {}))
    return out


def downed():
    """3-frame loop: key pose h - the stars wheel round his head, his head lolls."""
    out = []
    base_dy = 12
    for k in range(3):
        wob = (0, 1, 0)[k]
        Hd = P.place(P.head_variant(mouth='dazed', lens='swirl'), dy=base_dy - 2, dx=1 + wob)
        torso = P.body('torso', dy=base_dy)
        A = P.arm(delt=(11.0, 31.5, 5.3), up=(10, 33, 5, 40, 4.8, 4.0), fore=(5, 40, 1, 45, 3.6, 3.3), dy=base_dy)
        N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 32.5, 56, 40, 4.7, 4.1), fore=(56, 40, 60, 45, 3.8, 3.4), dy=base_dy)
        st = P.staff_line((66.0, 52.0), (72.0, 40.0), orb='neutral', ferrule=False)
        cv = comp([st, D.tails(base_dy - 2, 'droop', dx=1 + wob), A, N, torso, X.legs_sit(hip_y=85), Hd], staff=st)
        add_fist(cv, B(0, 47 + base_dy))
        add_fist(cv, B(61, 47 + base_dy))
        cx, cy = B(31 + wob, base_dy - 8)
        for i in range(4):
            a = 2 * math.pi * (i / 4 + k / 12)
            D.little_star(cv, int(round(cx + 16 * math.cos(a))), int(round(cy + 4 * math.sin(a))))
        head_top = None
        hy = np.nonzero(np.isin(Hd, list('khHr')))[0]
        head_top = (48 + wob, int(hy.min()))
        out.append((cv, {'head_top': head_top, 'daze': (cx, cy)}))
    return out


def downed_hit():
    """2 frames: a punch lands on him while he's down - squashed flinch, then the head snapping back."""
    out = []
    for k in range(2):
        base_dy = 12 + (2 if k == 0 else 0)
        hdy = base_dy - 2 + (0 if k == 0 else -1)
        mouth, lens = (X.WINCE, 'flash') if k == 0 else ('gasp', 'swirl')
        Hd = P.place(X.head(mouth, lens), dy=hdy, dx=1)
        torso = P.body('torso', dy=base_dy)
        A = P.arm(delt=(11.0, 31.5, 5.3), up=(10, 33, 4, 39, 4.8, 4.0), fore=(4, 39, 0, 43, 3.6, 3.3), dy=base_dy)
        N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 32.5, 57, 39, 4.7, 4.1), fore=(57, 39, 61, 43, 3.8, 3.4), dy=base_dy)
        st = P.staff_line((66.0, 52.0), (72.0, 40.0), orb='neutral', ferrule=False)
        cv = comp([st, D.tails(hdy, 'flick' if k else 'droop', dx=1), A, N, torso, X.legs_sit(hip_y=85 + (1 if k == 0 else 0)), Hd], staff=st)
        add_fist(cv, B(-1, 46 + base_dy))
        add_fist(cv, B(62, 46 + base_dy))
        if k == 0:
            sweat(cv, 42, base_dy - 4)
        out.append((cv, {}))
    return out


def defeat():
    """5 frames: reels (staff knocked flying), knees buckle, sits down hard, tips back, KO flat out."""
    out = []
    # 0: reel - head back, arms flung, the staff spinning out of his hand
    A = P.arm(delt=(11.0, 31.0, 5.2), up=(10.5, 30, 4, 24, 4.6, 3.8), fore=(4, 24, 1, 16, 3.6, 3.2))
    N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 30, 57, 24, 4.6, 3.8), fore=(57, 24, 60, 16, 3.6, 3.2))
    st = P.staff_line((-6.0, 22.0), (8.0, -12.0), orb='neutral')
    cv = comp([D.tails(-2, 'flick'), P.body('legs'), P.body('torso'), A, N, P.place(X.head('gasp', 'flash'), dy=-2), st], staff=st)
    add_fist(cv, B(1, 14))
    add_fist(cv, B(60, 14))
    out.append((cv, {}))
    # 1: knees buckle, head lolling, arms dropping
    sq = 4
    A = P.arm(delt=(11.0, 31.5, 5.3), up=(10, 33, 6, 40, 4.8, 4.0), fore=(6, 40, 5, 46, 3.6, 3.3), dy=sq)
    N, nf = near_hang(dy=sq)
    cv = comp([D.tails(sq, 'droop'), P.place(X.legs_squat(sq)), P.body('torso', dy=sq), A, N,
               P.place(X.head('dazed', 'swirl'), dy=sq, dx=-1)])
    add_fist(cv, B(5.5, 48 + sq))
    add_fist(cv, nf)
    out.append((cv, {}))
    # 2: sat down hard (the dazed sit, the staff down behind him)
    cv, m = D.pose_h_dazed()
    out.append((cv, {}))
    # 3: tipping over backward
    lie = lying_figure()
    out.append((X.rotsprite(lie, -45, pivot=(48, 70), out_pivot=(48, 76)), {}))
    # 4: KO flat on his back, swirl lenses, tongue out, stars
    flat = X.rotsprite(lie, -90, pivot=(48, 64), out_pivot=(48, 78))
    cv = comp([flat])
    for (x, y) in ((14, 58), (22, 52), (31, 57)):
        D.little_star(cv, x, y)
    out.append((cv, {}))
    return out


# ------------------------------------------------------------------ juggle (own cell) and shadows
JW, JH = 128, 96
J_FEET = (64, 95)


def _in_juggle(cv96, dx=0, dy=0):
    out = R.blank(JW, JH)
    R.composite(out, cv96, 16 + dx, dy)
    return out


def juggle():
    """12 frames, 128x96, feet (64, 95): launch 0-1, tumble 2-6 (loop), crash 7-9, down 10-11."""
    fig = flail_figure(stance='wide', face=('gasp', 'flash'))
    frames = []
    frames.append(_in_juggle(fig))                                        # 0: struck upward
    f1 = X.rotsprite(fig, 14, pivot=(48, 60), out_size=(JW, JH), out_pivot=(64, 50))      # 1: going up
    st1 = R.blank(JW, JH)
    for x0 in (14, 20, 104, 110):
        for t in range(16):
            y = 52 + t + (x0 % 4)
            if y < JH:
                st1[y, x0] = 'W' if t < 4 else ('w' if t < 10 else 'v')
    f1 = R.compose([st1, f1], JW, JH)
    for (dx_, dy_, ch) in ((0, 0, 'W'), (1, 0, 'c'), (-1, 0, 'c'), (0, 1, 'c'), (0, -1, 'c'), (2, 0, 'c'), (-2, 0, 'c')):
        f1[12 + dy_, 76 + dx_] = ch
    for (x, y, ch) in ((30, 30, 'l'), (31, 31, 'b'), (98, 26, 'l'), (99, 27, 'b'), (26, 44, 'l')):
        f1[y, x] = ch
    frames.append(f1)
    for k in range(5):                                                    # 2-6: the tumble
        ang = 30 + 72 * k
        f = X.rotsprite(fig, ang, pivot=(48, 62), out_size=(JW, JH), out_pivot=(64, 50))
        arc = R.blank(JW, JH)
        for (D_, n0, ramp) in ((41, 36, ('v', 'w', 'W')), (37, 22, ('v', 'w')), (45, 18, ('v', 'w'))):
            for i in range(n0):
                a = math.radians(ang + 180 + i * 4)
                for t in range(2):
                    x, y = 64 + (D_ - t) * math.cos(a), 50 + (D_ - t) * 0.8 * math.sin(a)
                    if 0 <= int(x) < JW and 0 <= int(y) < JH:
                        arc[int(y), int(x)] = ramp[min(len(ramp) - 1, i * len(ramp) // n0)]
        fr_ = R.compose([arc, f], JW, JH)
        for (dx_, dy_) in ((-30, -26), (30, -20), (-34, 8)):
            xx, yy = 64 + dx_ + k, 50 + dy_
            if 0 <= xx < JW - 1 and 0 <= yy < JH - 1:
                fr_[yy, xx] = 'l'
                fr_[yy + 1, xx + 1] = 'b'
        frames.append(fr_)
    lie = lying_figure(face=(X.WINCE, 'flash'))
    for k, (ang, lift) in enumerate(((-90, 0), (-78, 5), (-90, 0))):     # 7-9: the crash
        f = X.rotsprite(lie, ang, pivot=(48, 64), out_size=(JW, JH), out_pivot=(64, 78 - lift))
        fx = R.blank(JW, JH)
        if k == 0:
            for (x, y, r) in ((24, 90, 6), (104, 90, 6), (64, 93, 5)):
                _jpuff(fx, x, y, r)
        elif k == 1:
            for (x, y, r) in ((20, 88, 5), (108, 88, 5)):
                _jpuff(fx, x, y, r)
            for (x, y, ch) in ((30, 60, 'l'), (31, 61, 'b'), (98, 58, 'l'), (99, 59, 'b')):
                fx[y, x] = ch
        frames.append(R.compose([f, fx], JW, JH))
    ko = lying_figure()
    for k in range(2):                                                    # 10-11: down, breathing
        f = X.rotsprite(ko, -90, pivot=(48, 64), out_size=(JW, JH), out_pivot=(64, 78 - k))
        for i, (x, y) in enumerate(((36, 58), (44, 52), (52, 57))):
            D_star = f
            _jstar(D_star, x + (2 if k else 0), y - (1 if (i + k) % 2 else 0))
        frames.append(f)
    tumble_rows = [np.nonzero(fr != '.')[0].min() for fr in frames[2:7]]
    info = dict(frame_size=[JW, JH], feet=list(J_FEET), offset=[0, -48], tumble_centre=[64, 50],
                top_row=int(min(tumble_rows)))
    return frames, info


def _jpuff(L, cx, cy, r):
    h, w = L.shape
    Xc, Yc = R.centres(w, h)
    m = ((Xc - cx) / r) ** 2 + ((Yc - cy) / (r * 0.7)) ** 2 <= 1
    v = R.lambert(R.sphere_normal(Xc, Yc, cx, cy, r, r * 0.7))
    L[m] = np.where(v > 0.7, 'w', np.where(v > 0.35, 'v', 'T'))[m]


def _jstar(L, x, y):
    R.blk(L, x - 2, y - 2, ["..#..", ".#c#.", "#cWc#", ".#c#.", "..#.."])


def shadows():
    """liam_leap_shadow (3 of 64x16: low, mid, high) and liam_shadow (1 of 64x16): solid black ellipses;
    the code sets their alpha, like mason_leap_shadow."""
    def ell(rx, ry):
        cv = R.blank(64, 16)
        Xc, Yc = R.centres(64, 16)
        m = ((Xc - 32) / rx) ** 2 + ((Yc - 8) / ry) ** 2 <= 1
        cv[m] = '#'
        return cv
    leap = [ell(27, 6.5), ell(21, 5.2), ell(14.5, 4.0)]
    ground = [ell(28, 6.0)]
    return leap, ground


SHEETS = [   # (sheet name, function, times) - names and counts from LiamArtLayout.ANIMS
    ('slimed_sit', None, [1.0]),
    ('get_up', get_up, [0.17, 0.17, 0.16]),
    ('wipe', wipe, [0.2, 0.2]),
    ('talk_thanks', talk_thanks, [1.0, 1.0]),
    ('talk_explain', talk_explain, [1.0, 1.0]),
    ('talk_elements', talk_elements, [1.0, 1.0]),
    ('talk_smug', talk_smug, [1.0, 1.0]),
    ('talk_staff', talk_staff, [1.0, 1.0]),
    ('laugh', laugh, [0.1, 0.1, 0.1, 0.1]),
    ('staff_pull', staff_pull, [0.3, 0.3, 0.3, 0.35, 0.35]),
    ('slam_rise', slam_rise, [0.15, 0.1, 0.75]),
    ('ride', ride, [0.2, 0.2]),
    ('perch_idle', perch_idle, [0.2, 0.2, 0.2, 0.2]),
    ('cast_left', cast_left, [0.15, 0.15, 0.15]),
    ('cast_right', cast_right, [0.15, 0.15, 0.15]),
    ('wobble', wobble, [0.12, 0.12, 0.12, 0.12]),
    ('steady', steady, [1.0]),
    ('blast', blast, [0.15, 0.15, 0.3]),
    ('breathe', breathe, [0.3, 0.1, 0.1, 0.2]),
    ('slam', slam, [0.1, 0.1, 0.15, 0.25]),
    ('fall', fall, [0.15, 0.15, 0.15, 0.15]),
    ('downed', downed, [0.3, 0.3, 0.3]),
    ('downed_hit', downed_hit, [0.08, 0.14]),
    ('defeat', defeat, [0.12, 0.12, 0.14, 0.2, 1.0]),
]
PERCH_SHEETS = {'ride', 'perch_idle', 'cast_left', 'cast_right', 'wobble', 'steady', 'blast', 'breathe', 'slam'}
