"""Liam's attack 3-4 poses, v3, to the ADDENDUM3 E.3 contract ("extra nice": anticipation, smears,
follow-through, more frames). Built from his approved rig, so his identity stays pixel-exact.

  sheet        cell     anchor    frames  play                         points
  blow         96x96    (48,96)   6       once, blow_time 0.9          mouth (every frame)     on the pillar
  ignite       96x96    (48,96)   5       once, ignite_time 0.3        staff_tip (every frame) on the pillar
  channel      96x96    (48,96)   6       loop 0.12                    staff_tip               on the pillar
  vanish       96x96    (48,96)   6       once, vanish_time 0.8        -                       on the pillar
  lunge        144x96   (48,96)   5       once, lunge_show 0.12        staff_tip (last: reach 47)  facing right
  lunge_whiff  144x96   (48,96)   4       once, 0.3                    -                       facing right
  parried      96x96    (48,96)   4       once, 0.3, then downed       -
  impale       96x144   (48,144)  4       once, 0.4                    staff_tip (every frame; held >= 80 up)
  impale_call  96x144   (48,144)  2       loop 0.15                    staff_tip
  water_blast  144x96   (48,96)   5       once, 0.3 (release at 0.15)  staff_tip (release frame)
  teleport     96x96    (48,96)   6       once, teleport_time 0.35     -  (played backward to arrive)

The lunge's last staff tip and the impale's first coincide (both 47 texels right of his feet, 23 up),
so the skewered player never jumps between the two sheets.
"""
import math

import numpy as np

import le_rig as R
import le_staff as S
import le_poses as P
import le_posedefs as D
import le_parts as X
import le_full as F
import le_fire as FI
import le_a34fx as FX

FW = FH = 96
B = F.B
lay = F.lay
add_fist = F.add_fist
BOX = P.PERCH_BOX

# his gem's fire (the staff's flames stay inside his colour count): white-hot, pale, orange, dark
TO_LIAM = {'W': 'W', 'α': 'a', 'β': 'a', 'γ': '6', 'δ': '6', 'ε': 'n', 'ζ': 'n'}
STEAM_TO_LIAM = {'λ': 'W', 'μ': 'w', 'ν': 'v', 'ξ': 'v', 'ϑ': 'Y', 'ϒ': 'y', 'ϖ': 'v', 'ϡ': 'v'}


def fit(cv):
    """Keep a frame inside his colour count: the sparkle yellow (c) and any stray water/steam tones
    fold into his own nearest keys when the frame would pass 38 colours."""
    if R.numbers(cv)[1] > 38:
        cv = cv.copy()
        for a, b in (('c', 'a'), ('=', 'b'), ('+', 'b'), ('%', 'q'), ('λ', 'W'), ('μ', 'w'), ('ν', 'v'),
                     ('ξ', 'v')):
            cv[cv == a] = b
    return cv


def liamize(L):
    """Map fire / smoke keys into his own palette keys (so in-cell FX add no colours)."""
    out = L.copy()
    for k, v in list(TO_LIAM.items()) + list(STEAM_TO_LIAM.items()):
        out[L == k] = v
    return out


# ------------------------------------------------------------------ cells other than 96x96
def in_cell(cv96, w, h, ox=0, oy=0):
    out = R.blank(w, h)
    R.composite(out, cv96, ox, oy)
    return out


def comp_any(layers, staff=None):
    """F.comp for any cell size: compose, and sel-out the staff's keyline where it crosses his figure."""
    h, w = layers[0].shape
    full = R.compose([l for l in layers if l is not None], w, h)
    if staff is not None:
        under = R.compose([l for l in layers if l is not None and l is not staff], w, h)
        m = (staff == '#') & (full == '#') & (under != '.') & (under != '#')
        full[m] = 'g'
    return full


def staff_at(w, h, butt, head, orb='neutral', **kw):
    """The staff in a w x h cell, butt and head centre in CELL coords."""
    return S.staff(w, h, butt, head, orb=orb, **kw)


def body_xy(bx, by, ox=0, oy=0):
    """body coords -> cell coords (the 96 frame sits at (ox, oy) in the cell)."""
    x, y = B(bx, by)
    return x + ox, y + oy


# ------------------------------------------------------------------ legs
def legs_spread(near=6, far=3, base=None):
    """His legs in a wide lunge stance, front view: below the pelvis each leg is sheared outward (the
    near one `near` texels at the sole, the far one `far`), outlines and trouser texture kept."""
    src = P.legs_narrow() if base is None else base
    L = R.blank(64, 64)
    L[:51] = src[:51]
    for y in range(51, 64):
        k = (y - 50) / 13.0
        sn = int(round(near * k))
        sf = int(round(far * k))
        row = src[y]
        for x in range(64):
            ch = row[x]
            if ch == '.':
                continue
            if x >= 31:
                nx = x + sn
                if 0 <= nx < 64:
                    L[y, nx] = ch
            if x <= 31:
                fx = x - sf
                if 0 <= fx < 64:
                    L[y, fx] = ch
    # close the fork: the inner edges of the pelvis rows 50/51 onto each leg
    for y in range(51, 64):
        row = L[y]
        xs = np.nonzero(row != '.')[0]
        if len(xs) == 0:
            continue
    return L


def legs_lunge(hip_dx=0, near=10, far=6, squat=0):
    """His legs in a lunge, front view, as a 96x96 layer: the pelvis sits under the torso (shifted
    hip_dx), the lead (near) foot planted `near` texels out to the right of where it stood and the
    trailing (far) foot `far` out to the left; each leg is sheared between hip and sole, so its outline
    and trouser texture are his own."""
    src = P.place(X.legs_squat(squat, wide=False) if squat else P.legs_narrow())
    hip = 46 + squat + P.BODY[1]
    crotch = 31 + P.BODY[0]
    L = R.blank(FW, FH)
    rows = np.nonzero((src != '.').any(axis=1))[0]
    for y in rows:
        t = max(0.0, (y - hip) / float(FH - 1 - hip))
        pelvis = y <= hip + 4
        sh_all = int(round(hip_dx * (1 - t)))
        sn = int(round(hip_dx * (1 - t) + near * t))
        sf = int(round(hip_dx * (1 - t) - far * t))
        for x in np.nonzero(src[y] != '.')[0]:
            ch = src[y, x]
            if pelvis:
                nx = x + sh_all
                if 0 <= nx < FW:
                    L[y, nx] = ch
                continue
            if x >= crotch:
                nx = x + sn
                if 0 <= nx < FW:
                    L[y, nx] = ch
            if x <= crotch:
                nx = x + sf
                if 0 <= nx < FW:
                    L[y, nx] = ch
    return L


def shear_rows(L, row_shift):
    """Shift each row y of a layer by row_shift(y) texels (a lean)."""
    h, w = L.shape
    out = R.blank(w, h)
    for y in range(h):
        d = int(round(row_shift(y)))
        row = L[y]
        if d > 0:
            out[y, d:] = np.where(row[:w - d] != '.', row[:w - d], out[y, d:])
        elif d < 0:
            out[y, :w + d] = np.where(row[-d:] != '.', row[-d:], out[y, :w + d])
        else:
            out[y] = row
    return out


def lean_fn(hip_dx, top_dx, squat=0):
    """The lean: 0 at the belt (row 46 of his body) growing to top_dx - hip_dx at his shoulders' top
    (row 24), so his hips stay over the pelvis and his chest and head are thrown forward."""
    hip = 46 + squat + P.BODY[1]
    top = 24 + squat + P.BODY[1]

    def f(y):
        k = min(1.0, max(0.0, (hip - y) / float(hip - top)))
        return hip_dx + (top_dx - hip_dx) * k
    return f


def mouth_pt(hdy=0, hdx=0):
    return B(27.5 + hdx, 23 + hdy)


def clip_box(L, top=True, sides=True):
    if sides:
        L[:, :BOX['left']] = '.'
        L[:, BOX['right'] + 1:] = '.'
    if top:
        L[:BOX['top'], :] = '.'
    return L


# ------------------------------------------------------------------ fire on the staff head (his colours)
def staff_flames(cx, cy, t, power=1.0, w=FW, h=FH, up=(0.0, -1.0), seed=0):
    """Flames licking up off the staff's ring head (centre cx, cy): a crown of tongues round the top of
    the ring, flickering and tearing off; drawn in his gem's fire colours."""
    L = R.blank(w, h)
    fd = FI.Field(w, h)
    emb = []
    for i, a in enumerate((-150, -120, -90, -60, -30)):
        ar = math.radians(a)
        bx, by = cx + math.cos(ar) * 6.5, cy + math.sin(ar) * 6.0
        H = (5 + 6 * power) * (1.0 if a == -90 else (0.8 if abs(a + 90) == 30 else 0.6))
        FI.tongue(fd, bx, by, (t + i * 0.23) % 1.0, H, 1.3 + 0.7 * power, seed=320 + seed + i * 1.7, rate=6,
                  up=(math.cos(ar) * 0.4 + up[0], -1.0), embers=emb, ember_every=2, temp=0.9, anchor=False)
    fd.render(L)
    FI.draw_embers(L, emb, smoke=False)
    return liamize(L)


# ================================================================== BLOW (on the pillar)
def blow():
    """6 frames: inhale, inhale deeper (leaning back, chest up), BLOW (lurching forward, near palm
    thrust out), blow on, blow tailing off, recover. The gust FX (liam_blow_gust) sits on `mouth`."""
    out = []
    specs = [  # head dy, torso dy, mouth, lens, tails, near arm, fx
        (-1, 0, X.PUFF, 'dim', 'down', 'hang', 'in1'),
        (-3, -1, X.PUFF, 'dim', 'mid', 'back', 'in2'),
        (1, 1, 'blow', 'flash', 'up', 'thrust', 'out1'),
        (1, 1, 'blow', 'flash', 'flick', 'thrust', 'out2'),
        (0, 0, 'blow', 'flash', 'up', 'ease', 'out3'),
        (0, 0, X.TALK, 'dim', 'down', 'hang', 'rest'),
    ]
    for k, (hdy, tdy, mouth, lens, tl, arm, fx) in enumerate(specs):
        A, st, fist, orb = F.far_staff_raised(orb='air', dy=tdy)
        if arm == 'hang':
            N, nf = F.near_hang(dy=tdy)
            palm = None
        elif arm == 'back':
            N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 31 + tdy, 57, 34 + tdy, 4.7, 4.0),
                      fore=(57, 34 + tdy, 60, 28 + tdy, 3.8, 3.4))
            nf, palm = B(61, 26 + tdy), None
        elif arm == 'thrust':
            N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 32 + tdy, 56, 38 + tdy, 4.7, 4.0),
                      fore=(56, 38 + tdy, 61, 42 + tdy, 3.8, 3.4))
            nf, palm = None, B(62.5, 44 + tdy)
        else:
            N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 32 + tdy, 55, 39 + tdy, 4.7, 4.0),
                      fore=(55, 39 + tdy, 58, 44 + tdy, 3.8, 3.4))
            nf, palm = B(58.5, 46 + tdy), None
        Hd = P.place(X.head(mouth, lens), dy=hdy)
        cv = F.comp([D.tails(hdy, tl), P.place(P.legs_narrow()), P.body('torso', dy=tdy), N, Hd, st, A], staff=st)
        add_fist(cv, fist)
        if nf is not None:
            add_fist(cv, nf)
        if palm is not None:
            X.hand(cv, X.OPEN_PALM, *palm)
        m = mouth_pt(hdy)
        fl = lay()
        if fx in ('in1', 'in2'):
            # air drawn in: streaks converging on his lips from both sides
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
        else:
            D.dots(fl, [B(28, 27), B(30, 28), B(27, 29)], 'w')
        clip_box(fl)
        cv = F.comp([cv, fl])
        out.append((cv, {'mouth': m}))
    return out


# ================================================================== IGNITE (on the pillar)
def ignite():
    """5 frames: raise (the fire gem wakes), FLARE (the ring bursts into flame), the thrust (the staff
    swept down and out over the arena - the fire streaks leave the tip here), the hold, the settle."""
    out = []
    for k in range(5):
        t = k / 5.0
        if k <= 1:
            A, st, fist, orb = F.far_staff_raised(orb='fire', lift=2.0 if k else 1.0)
            N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 31, 56, 26, 4.6, 3.9), fore=(56, 26, 59, 19, 3.6, 3.2))
            nf = B(59.5, 17)
            Hd = P.place(X.head('big' if k == 0 else 'shout', 'flash'), dy=-1 if k == 0 else -2)
            tl = 'mid' if k == 0 else 'up'
            cv = F.comp([D.tails(-1, tl), P.place(P.legs_narrow()), P.body('torso'), N, Hd, st, A], staff=st)
            add_fist(cv, fist)
            add_fist(cv, nf)
            tip = orb
        else:
            # the sweep: staff swung down and out to his far side, over the arena; near fist clenched
            lean = -1 if k == 2 else 0
            A = P.arm(delt=(11.5, 31.0, 5.2), up=(11, 32, 8, 38, 4.6, 3.8), fore=(8, 38, 10, 41, 3.4, 3.1), dx=lean)
            butt, headc = (24.0 + lean, 52.0), ((6.0 + lean, 31.0) if k == 2 else (6.5, 30.0))
            st = P.staff_line(butt, headc, orb='fire')
            N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 32, 55, 38, 4.7, 4.0), fore=(55, 38, 51, 42, 3.8, 3.4))
            Hd = P.place(X.head('shout' if k == 2 else ('big' if k == 3 else 'smirk'), 'flash'), dx=lean - 1)
            cv = F.comp([D.tails(0, 'flick' if k == 2 else 'mid', dx=lean - 1), P.place(P.legs_narrow()),
                         P.body('torso', dx=lean), N, Hd, st, A], staff=st)
            add_fist(cv, B(10.5 + lean, 42))
            add_fist(cv, B(50, 43))
            tip = B(headc[0] + 0.5, headc[1] + 0.5)
        power = (0.3, 1.0, 0.9, 0.7, 0.45)[k]
        fl = staff_flames(tip[0], tip[1], t, power=power, seed=k)
        if k == 1:
            # the flare: a ring of sparks thrown off the gem
            for i in range(10):
                a = math.radians(i * 36 + 10)
                FI.plot(fl, tip[0] + math.cos(a) * 11, tip[1] + math.sin(a) * 10, 'a' if i % 2 else '6')
        if k == 2:
            # the throw: streaks of fire leaving the tip, down and out
            for i in range(3):
                a = math.radians(115 + i * 22)
                for j in range(4, 14):
                    if (j + i) % 4 == 3:
                        continue
                    FI.plot(fl, tip[0] + math.cos(a) * j, tip[1] + math.sin(a) * j, 'a' if j < 8 else '6')
        clip_box(fl)
        cv = F.comp([cv, fl])
        out.append((cv, {'staff_tip': tip}))
    return out


# ================================================================== CHANNEL (on the pillar, loop)
def channel():
    """6-frame loop through the firestorm: the staff raised high and blazing, his near palm thrust out
    over the arena steering the storm, hair tails whipping in the updraft, lenses lit by the fire,
    a slow bob."""
    out = []
    for k in range(6):
        t = k / 6.0
        bob = (0, 0, -1, -1, 0, 0)[k]
        A, st, fist, orb = F.far_staff_raised(orb='fire', lift=1.0, dy=bob)
        N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 31 + bob, 57, 30 + bob, 4.6, 3.9),
                  fore=(57, 30 + bob, 61, 27 + bob, 3.6, 3.2))
        palm = B(63, 25 + bob)
        mouth = ('big', 'big', 'shout', 'shout', 'big', 'big')[k]
        Hd = P.place(X.head(mouth, 'flash'), dy=-1 + bob)
        tl = ('up', 'flick', 'up', 'flick', 'up', 'flick')[k]
        cv = F.comp([D.tails(-1 + bob, tl), P.place(P.legs_narrow()), P.body('torso', dy=bob), N, Hd, st, A], staff=st)
        add_fist(cv, fist)
        X.hand(cv, X.OPEN_PALM, *palm)
        fl = staff_flames(orb[0], orb[1], t, power=1.0, seed=7)
        # heat shimmer / sparks rising past him
        for i in range(3):
            life = (t + i / 3.0) % 1.0
            x = B(8 + i * 22, 0)[0] + math.sin(life * 5 + i) * 2
            y = B(0, 30 - life * 26)[1]
            FI.plot(fl, x, y, 'a' if life < 0.4 else ('6' if life < 0.75 else 'n'))
        clip_box(fl)
        cv = F.comp([cv, fl])
        out.append((cv, {'staff_tip': orb}))
    return out


# ================================================================== VANISH (on the pillar)
def _dissolve(cv, amount, seed=1, into=('λ', 'μ'), keep=None, bottom_up=True):
    """Turn `amount` (0..1) of his texels to steam (into) - from the feet up - and remove the ones that
    went to steam in the previous stage (amount > 1 removes everything but `keep`)."""
    out = cv.copy()
    h, w = cv.shape
    X_, Y_ = np.meshgrid(np.arange(w), np.arange(h))
    n = FI.hash01(np.floor(X_ / 2.0), np.floor(Y_ / 2.0), seed)
    op = out != '.'
    ys = np.nonzero(op.any(axis=1))[0]
    if len(ys) == 0:
        return out
    y0, y1 = ys.min(), ys.max()
    height = (y1 - Y_) / max(1.0, (y1 - y0)) if bottom_up else np.zeros_like(n)
    score = n * 0.6 + (1 - height) * 0.4 if bottom_up else n
    gone = op & (score < amount - 0.35)
    steam = op & (score < amount) & ~gone
    if keep is not None:
        gone &= ~keep
        steam &= ~keep
    out[gone] = '.'
    out[steam] = np.where((X_ + Y_)[steam] % 2 == 0, into[0], into[1])
    return out


def vanish():
    """6 frames: steam boils up round him (he smirks), it climbs him, he turns to steam from the feet up
    (70 %), then all of him but the glint of his glasses, then the glint, then nothing but drifting steam.
    The code also fades his alpha over the last 0.4 s and lowers him on the stump."""
    out = []
    base, pts = F.perch_idle()[0]
    lens_keep = np.zeros(base.shape, bool)
    lx, ly = B(19, 14)
    lens_keep[ly:ly + 3, lx:lx + 15] = np.isin(base[ly:ly + 3, lx:lx + 15], ['W', 'l'])
    for k in range(6):
        u = k / 5.0
        if k <= 1:
            cv = base.copy()
        elif k == 2:
            cv = _dissolve(base, 0.55, keep=lens_keep)
        elif k == 3:
            cv = _dissolve(base, 1.05, keep=lens_keep)
        elif k == 4:
            cv = R.blank(FW, FH)
            cv[lens_keep] = base[lens_keep]
        else:
            cv = R.blank(FW, FH)
        fx_b = lay()
        fx_f = lay()
        rnd = np.random.RandomState(40)
        for i in range(8):
            born = i * 0.06
            if u < born:
                continue
            w_ = min(1.0, (u - born) / 0.7)
            x = 48 + (rnd.rand() - 0.5) * 50
            y = 92 - rnd.rand() * 10 - w_ * (20 + 30 * rnd.rand())
            r = 2.5 + 4.0 * w_
            target = fx_f if i % 2 else fx_b
            FI.puff(target, x, y, r, ramp=('W', 'w', 'v'), dissolve=max(0.0, (u - 0.6) * 2.0), seed=330 + i)
        if k == 4:
            # the last glint of his glasses
            gx, gy = B(26, 15)
            R.star(fx_f, int(gx), int(gy), 3, diag=1)
        clip_box(fx_b)
        clip_box(fx_f)
        cv = F.comp([fx_b, cv, fx_f])
        out.append((cv, {}))
    return out


# ================================================================== LUNGE (144x96, facing right)
LW, LH = 144, 96
REACH = 47                    # texels from his feet to the staff tip at full extension


def _lunge_figure(hip, lean, squat, spread, butt, head, mouth, lens, tails, orb='neutral', cell=(LW, LH), oy=0,
                  far_fist=16.0, near_fist=40.0):
    """His lunge figure in a cell: pelvis shifted `hip`, torso and arms `lean` (>= hip: he leans into it),
    head a texel further; legs in a lunge stance; both hands on a staff from butt to head (CELL coords),
    the fists `far_fist` and `near_fist` texels up the shaft from the butt."""
    w, h = cell
    ln = math.hypot(head[0] - butt[0], head[1] - butt[1])
    ux, uy = (head[0] - butt[0]) / ln, (head[1] - butt[1]) / ln
    ffc = (butt[0] + ux * far_fist, butt[1] + uy * far_fist)
    nfc = (butt[0] + ux * near_fist, butt[1] + uy * near_fist)
    ff = (ffc[0] - P.BODY[0], ffc[1] - oy - P.BODY[1])
    nf = (nfc[0] - P.BODY[0], nfc[1] - oy - P.BODY[1])
    legs = legs_lunge(hip_dx=hip, near=spread[0], far=spread[1], squat=squat)
    lf = lean_fn(hip, lean, squat)
    sh = int(round(lf(31 + squat + P.BODY[1])))            # how far his shoulders moved
    A = P.arm(delt=(11.0, 31.5, 5.3), up=(11, 32, 16, 38, 4.8, 4.2),
              fore=(16, 38, ff[0] - sh, ff[1] - squat, 3.8, 3.5), dx=sh, dy=squat)
    N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 32, 56, 37, 4.7, 4.1),
              fore=(56, 37, nf[0] - sh, nf[1] - squat, 3.8, 3.4), dx=sh, dy=squat)
    Hd = P.place(X.head(mouth, lens), dx=lean + 1, dy=squat)
    torso = shear_rows(P.body('torso', dy=squat), lf)
    body96 = F.comp([D.tails(squat, tails, dx=lean + 1), legs, torso, A, Hd])
    body = in_cell(body96, w, h, 0, oy)
    nearc = in_cell(N, w, h, 0, oy)
    st = staff_at(w, h, butt, head, orb=orb)
    cv = comp_any([body, st, nearc], staff=st)
    add_fist(cv, ffc)
    add_fist(cv, nfc)
    return cv


def _ghosts(cv, heads, orb='neutral'):
    """Afterimages of the staff's ring head along its path (the smear), pale and thinning backward."""
    h, w = cv.shape
    fx = R.blank(w, h)
    ring = S.head_canvas(orb)
    for i, (x, y) in enumerate(heads):
        g = ring.copy()
        g[g != '.'] = ('v', 'w', 'W')[min(2, i)]
        if i < 2:
            X_, Y_ = np.meshgrid(np.arange(g.shape[1]), np.arange(g.shape[0]))
            g[((X_ + Y_ + i) % 2 == 0) & (g != '.')] = '.'
        R.composite(fx, g, int(round(x - 0.5)) - S.HEAD_C[0], int(round(y - 0.5)) - S.HEAD_C[1])
    return comp_any([fx, cv])


def _streaks(cv, x0, x1, ys, ramp=('v', 'w', 'W')):
    """Speed lines: short dashes trailing back from his back, bright at the front."""
    h, w = cv.shape
    fx = R.blank(w, h)
    for i, y in enumerate(ys):
        ln = x1 - x0 - (i % 3) * 3
        for j in range(int(ln)):
            f = j / max(1.0, ln - 1)
            if f < 0.35 and j % 2:
                continue
            FI.plot(fx, x0 + (x1 - x0 - ln) + j, y, ramp[min(2, int(f * 3))])
    return comp_any([fx, cv])


LUNGE_SPECS = [
    # hip lean squat spread    head_x  staff_y(cell) mouth    lens     tails    ghosts
    (-4, -8, 5, (2, 2), 60.0, 80.0, 'big', 'flash', 'hold', None),
    (1, 4, 3, (7, 4), 74.0, 79.0, 'shout', 'flash', 'mid', [60.0]),
    (3, 9, 2, (10, 6), 82.0, 78.0, 'shout', 'flash', 'flick', [62.0, 70.0]),
    (5, 11, 1, (12, 7), 86.0, 77.0, 'shout', 'flash', 'flick', [70.0, 78.0]),
    (5, 11, 1, (12, 7), 87.5, 77.0, 'shout', 'flash', 'up', None),
]


def lunge():
    """5 frames, 0.12 s: COIL (sunk back on his heels, the staff drawn back at the hip like a bayonet,
    steam shed off him as he appears), SPRING (driving off the back foot), SMEAR (ghosts of the ring head
    and speed lines), IMPACT SMEAR (the point arriving), FULL EXTENSION (the hit frame: the lead foot
    planted, torso leaning in, staff tip 47 texels right of his feet)."""
    out = []
    for k, (hip, lean, sq, spread, hx, hy, mouth, lens, tl, ghosts) in enumerate(LUNGE_SPECS):
        head = (hx, hy)
        butt = (hx - 53.0, hy + 1.0)
        cv = _lunge_figure(hip, lean, sq, spread, butt, head, mouth, lens, tl)
        tip = (head[0] + 7.5, head[1])            # the leading edge of the ring head
        if k == 0:
            fx = R.blank(LW, LH)
            for i, (x, y, r) in enumerate(((16, 58, 4), (70, 50, 3.5), (26, 86, 4.5), (64, 88, 4), (12, 40, 3))):
                FI.puff(fx, x, y, r, ramp=('W', 'w', 'v'), dissolve=0.35, seed=340 + i)
            cv = comp_any([fx, cv])
        if ghosts:
            cv = _ghosts(cv, [(g, hy) for g in ghosts])
            cv = _streaks(cv, 4 + k * 3, 30 + lean, (40 + 2 * k, 50, 60, 70 - k))
        if k == 3:
            R.star(cv, int(tip[0]) + 1, int(tip[1]), 4, diag=1)
        if k >= 1:
            dust = R.blank(LW, LH)
            for (x, y, r) in ((24 - 2 * k, 93, 3.0 + 0.3 * k), (16 - 2 * k, 91, 2.2)):
                FI.puff(dust, x, y, r, ramp=('w', 'v', 'T'), seed=int(x) + k)
            cv = comp_any([dust, cv])
        out.append((cv, {'staff_tip': tip}))
    return out


def lunge_whiff():
    """4 frames, 0.3 s: OVERSHOOT (carried past, the point dipping, the back foot kicked up), SKID (heels
    dug in, dust thrown, staff hauled back), RECOVER (upright, staff at his side, glaring), and the steam
    gathering round him to take him again."""
    out = []
    # 0 overshoot: the extension carried on, the point dipping, the trailing foot kicked up
    cv = _lunge_figure(8, 14, 2, (13, 9), (88.0 - 52.0, 70.0), (88.0, 86.0), 'gasp', 'flash', 'flick')
    cv = _streaks(cv, 2, 34, (38, 50, 62))
    out.append((cv, {}))
    # 1 skid
    lean = 5
    legs = P.place(legs_spread(near=6, far=4))
    A = P.arm(delt=(11.0, 31.5, 5.3), up=(11, 32, 16, 40, 4.8, 4.2), fore=(16, 40, 22 - lean, 44, 3.8, 3.5), dx=lean)
    N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 32, 54, 40, 4.7, 4.1), fore=(54, 40, 44 - lean, 43, 3.8, 3.4), dx=lean)
    Hd = P.place(X.head(X.WINCE, 'flash'), dx=lean + 1)
    body = in_cell(F.comp([D.tails(0, 'up', dx=lean + 1), legs, P.body('torso', dx=lean), A, Hd]), LW, LH)
    st = staff_at(LW, LH, (14.0 + lean, 78.0), (66.8 + lean, 73.2), orb='neutral')
    cv = comp_any([body, st, in_cell(N, LW, LH)], staff=st)
    add_fist(cv, B(22, 44.5))
    add_fist(cv, B(44, 44))
    dust = R.blank(LW, LH)
    for (x, y, r) in ((70, 92, 4.2), (80, 90, 3.0), (26, 92, 3.6), (18, 90, 2.4), (88, 91, 2.2)):
        FI.puff(dust, x, y, r, ramp=('w', 'v', 'T'), seed=int(x))
    cv = comp_any([dust, cv])
    out.append((cv, {}))
    # 2 recover, 3 the steam gathering
    for k in (2, 3):
        A, st, fist, orb = F.far_staff_side()
        N, nf = F.near_hang()
        Hd = P.place(X.head(X.TALK if k == 2 else 'smirk', 'dim'))
        cv96 = F.comp([D.tails(0, 'down'), P.body('legs'), P.body('torso'), N, Hd, st, A], staff=st)
        add_fist(cv96, fist)
        add_fist(cv96, nf)
        cv = in_cell(cv96, LW, LH, 4, 0)
        if k == 3:
            fx = R.blank(LW, LH)
            for i, (x, y, r) in enumerate(((30, 88, 5), (80, 86, 5), (40, 70, 4), (70, 66, 4), (56, 90, 4.5))):
                FI.puff(fx, x, y, r, ramp=('W', 'w', 'v'), seed=350 + i)
            cv = comp_any([cv, fx])
        out.append((cv, {}))
    return out


# ================================================================== PARRIED
def parried():
    """4 frames, 0.3 s, then downed: CLANG (the point knocked up and out on his near side, a spark off
    the ring, his arms jolted, glasses flashing), STAGGER (a step back, the staff torn out of his hands
    and spinning up), TOPPLE (tipping back, the staff tumbling down behind him, a sweat drop), SIT
    (landing on his backside with the staff beside him - downed's first frame follows)."""
    out = []
    # 0 clang
    A = P.arm(delt=(11.0, 31.5, 5.3), up=(11, 32, 17, 36, 4.8, 4.2), fore=(17, 36, 30, 33, 3.8, 3.5), dx=-2)
    N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 31, 56, 26, 4.6, 3.9), fore=(56, 26, 58, 18, 3.6, 3.2), dx=-2)
    st = P.staff_line((24.0, 44.0), (66.0, 11.0), orb='neutral')
    Hd = P.place(X.head('gasp', 'flash'), dx=-3, dy=1)
    cv = F.comp([D.tails(1, 'flick', dx=-3), P.place(P.legs_narrow()), P.body('torso', dx=-2), A, Hd, st, N], staff=st)
    add_fist(cv, B(30, 32.5))
    add_fist(cv, B(56.5, 16.5))
    hx, hy = B(66.5, 11.5)
    R.star(cv, int(hx) + 4, int(hy) - 4, 5, diag=2)
    D.dots(cv, [(hx + 10, hy - 9), (hx - 4, hy - 11), (hx + 11, hy + 2), (hx + 3, hy - 13)], 'a')
    arcs = lay()
    for (x0, y0, x1, y1) in ((-4, 30, -8, 26), (-5, 38, -10, 37), (-4, 46, -9, 48)):
        R.line(arcs, *B(x0, y0), *B(x1, y1), 'w')
    F.dust(arcs, [(20, 93, 3.5), (74, 93, 3.5)])
    cv = F.comp([arcs, cv])
    out.append((cv, {}))
    # 1 stagger back, the staff spinning away up and right
    legs = P.place(P.legs_lift_near(up=5, out=2))
    A = P.arm(delt=(11.0, 31.0, 5.2), up=(10.5, 30, 5, 22, 4.6, 3.8), fore=(5, 22, 4, 13, 3.6, 3.2), dx=-5)
    N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 31, 57, 26, 4.6, 3.8), fore=(57, 26, 61, 19, 3.6, 3.2), dx=-5)
    st = P.staff_line((52.0, 10.0), (72.0, -24.0), orb='neutral')
    Hd = P.place(X.head('gasp', 'flash'), dx=-6, dy=2)
    cv = F.comp([D.tails(2, 'flick', dx=-6), legs, P.body('torso', dx=-5, dy=1), A, Hd, N, st], staff=st)
    add_fist(cv, B(-1, 11))
    add_fist(cv, B(56, 17))
    F.sweat(cv, 36, 2)
    arcs = lay()
    D.motion_arc(arcs, *B(62, -7), 14.0, 100, 200, ramp=('v', 'w', 'W'), thick=1.2)
    F.dust(arcs, [(14, 93, 3.8), (30, 94, 3.0), (60, 94, 2.6), (6, 91, 2.4)])
    cv = F.comp([arcs, cv])
    out.append((cv, {}))
    # 2 topple back, the staff falling behind him
    fig = F.flail_figure(face=('gasp', 'flash'))
    f = X.rotsprite(fig, -16, pivot=(48, 90), out_pivot=(44, 93))
    st = P.staff_line((60.0, 30.0), (74.0, 6.0), orb='neutral')
    arcs = lay()
    D.motion_arc(arcs, 60, 60, 30, -95, -40, ramp=('v', 'w', 'W'), thick=1.4)
    D.motion_arc(arcs, 60, 60, 26, -90, -50, ramp=('v', 'w'), thick=1.0)
    F.dust(arcs, [(20, 94, 3.6), (70, 94, 3.2)])
    cv = F.comp([arcs, st, f])
    F.sweat(cv, 40, 4)
    out.append((cv, {}))
    # 3 sit (downed frame 0 - it already has the staff dropped beside him), landing dust
    cv = F.downed()[0][0].copy()
    fx = lay()
    F.dust(fx, [(12, 92, 4.5), (84, 92, 4.5), (48, 94, 3)])
    cv = F.comp([fx, cv])
    out.append((cv, {}))
    return out


# ================================================================== IMPALE (96x144) and IMPALE_CALL
IW, IH = 96, 144
IOY = 48                      # the 96 frame sits 48 rows down (feet on row 143)


def impale():
    """4 frames, 0.4 s: IMPACT (the lunge's hit frame, the player skewered on the point - the same tip
    as the lunge's last frame), HOIST SMEAR (the staff swung up through a blurred arc with him on it),
    HOIST (staff near upright, both hands, straining), HELD (staff straight up, the player high over
    his head: tip 101 texels above his feet)."""
    out = []
    # 0 impact: the lunge's extension in the tall cell (the same figure and tip as lunge frame 4)
    hip, lean, sq, spread, hx, hy = 5, 11, 1, (12, 7), 87.5, 77.0
    cv = _lunge_figure(hip, lean, sq, spread, (hx - 53.0, hy + 1.0 + IOY), (hx, hy + IOY), 'big', 'flash', 'up',
                       cell=(IW, IH), oy=IOY)
    tip = (hx + 7.5, hy + IOY)
    R.star(cv, int(tip[0]) - 2, int(tip[1]) - 1, 4, diag=1)
    dust = R.blank(IW, IH)
    for (x, y, r) in ((16, 141, 4.2), (8, 139, 3.0)):
        FI.puff(dust, x, y, r, ramp=('w', 'v', 'T'), seed=int(x))
    cv = comp_any([dust, cv])
    out.append((cv, {'staff_tip': tip}))
    # 1 hoist smear: the staff at 45 degrees, a blurred arc from level to upright behind it
    A = P.arm(delt=(11.0, 31.5, 5.3), up=(11, 32, 19, 36, 4.8, 4.2), fore=(19, 36, 33, 33, 3.8, 3.5))
    N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 31, 55, 29, 4.6, 3.9), fore=(55, 29, 50, 24, 3.6, 3.2))
    Hd = P.place(X.head(X.WINCE, 'flash'), dy=-1)
    body = in_cell(F.comp([D.tails(-1, 'mid'), P.place(legs_spread(near=4, far=2)), P.body('torso'), A, Hd]), IW, IH, 0, IOY)
    bx, by = body_xy(30, 44, 0, IOY)
    hx, hy = body_xy(63, 3, 0, IOY)
    st = staff_at(IW, IH, (bx, by), (hx, hy), orb='neutral')
    cv = comp_any([body, st, in_cell(N, IW, IH, 0, IOY)], staff=st)
    add_fist(cv, body_xy(33, 33.5, 0, IOY))
    add_fist(cv, body_xy(49.5, 23, 0, IOY))
    arc = R.blank(IW, IH)
    cx0, cy0 = body_xy(30, 44, 0, IOY)
    for i in range(24):
        a = math.radians(-6 - i * 3.2)
        for rr in (52, 54, 56):
            FI.plot(arc, cx0 + rr * math.cos(a), cy0 + rr * math.sin(a), 'W' if i < 8 else ('w' if i < 16 else 'v'))
    cv = comp_any([arc, cv])
    ang = math.atan2(hy - by, hx - bx)
    tip = (hx + 7.5 * math.cos(ang), hy + 7.5 * math.sin(ang))
    out.append((cv, {'staff_tip': tip}))
    # 2 hoist: near upright, both hands, straining
    A = P.arm(delt=(11.0, 31.5, 5.3), up=(11, 32, 20, 33, 4.8, 4.2), fore=(20, 33, 37, 29, 3.8, 3.5))
    N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 30, 53, 22, 4.6, 3.8), fore=(53, 22, 45, 15, 3.6, 3.2))
    Hd = P.place(X.head(X.WINCE, 'flash'), dy=-2)
    body = in_cell(F.comp([D.tails(-2, 'up'), P.place(legs_spread(near=3, far=2)), P.body('torso', dy=-1), A, Hd]),
                   IW, IH, 0, IOY)
    bx, by = body_xy(38, 44, 0, IOY)
    hx, hy = body_xy(44.7, -8.6, 0, IOY)
    st = staff_at(IW, IH, (bx, by), (hx, hy), orb='neutral')
    cv = comp_any([body, st, in_cell(N, IW, IH, 0, IOY)], staff=st)
    add_fist(cv, body_xy(37.5, 29.5, 0, IOY))
    add_fist(cv, body_xy(44.5, 13.5, 0, IOY))
    F.sweat(cv, 38, -2 + IOY)
    dust = R.blank(IW, IH)
    for (x, y, r) in ((22, 141, 3.4), (74, 141, 3.4)):
        FI.puff(dust, x, y, r, ramp=('w', 'v', 'T'), seed=int(x))
    arc = R.blank(IW, IH)
    cx0, cy0 = body_xy(38, 44, 0, IOY)
    for i in range(10):
        a = math.radians(-60 - i * 3.0)
        for rr in (56, 58):
            FI.plot(arc, cx0 + rr * math.cos(a), cy0 + rr * math.sin(a), 'w' if i < 5 else 'v')
    cv = comp_any([dust, arc, cv])
    ang = math.atan2(hy - by, hx - bx)
    tip = (hx + 7.5 * math.cos(ang), hy + 7.5 * math.sin(ang))
    out.append((cv, {'staff_tip': tip}))
    # 3 held: straight up in the near fist, the far fist pumped - a savage grin
    cv, tip = _held(mouth='big', far='pump')
    out.append((cv, {'staff_tip': tip}))
    return out


def _held(mouth='shout', far='cup', hdy=-2, tl='up', k=0):
    """The staff straight up over his head (near fist high on it), the far hand either also on it
    ('both') or cupped at his mouth ('cup') calling for Bixby."""
    N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 30, 55, 20, 4.6, 3.8), fore=(55, 20, 55, 9, 3.6, 3.2))
    if far == 'pump':
        A = P.arm(delt=(11.0, 31.0, 5.2), up=(10.5, 30, 5, 22, 4.6, 3.8), fore=(5, 22, 5, 13, 3.6, 3.2))
    else:
        A = P.arm(delt=(11.5, 30.5, 5.2), up=(11, 31, 9, 24, 4.6, 3.5), fore=(9, 24, 16, 21 + hdy, 3.4, 3.1))
    Hd = P.place(X.head(mouth, 'flash'), dy=hdy)
    body = in_cell(F.comp([D.tails(hdy, tl), P.place(P.legs_narrow()), P.body('torso'), Hd]), IW, IH, 0, IOY)
    bx, by = body_xy(55, 40, 0, IOY)
    hx, hy = body_xy(55, -13, 0, IOY)
    st = staff_at(IW, IH, (bx + 0.5, by), (hx + 0.5, hy), orb='fire')
    arms_b = in_cell(A, IW, IH, 0, IOY)
    arms_n = in_cell(N, IW, IH, 0, IOY)
    cv = comp_any([body, st, arms_n, arms_b], staff=st)
    add_fist(cv, body_xy(55, 7, 0, IOY))
    if far == 'pump':
        add_fist(cv, body_xy(5, 11, 0, IOY))
    else:
        R.blk(cv, *body_xy(13, 16 + hdy, 0, IOY), X.BACKHAND)
        fx = R.blank(IW, IH)
        for (x0, y0, x1, y1) in ((10, 12, 6, 9), (8, 18, 3, 17), (46, 10, 49, 7)):
            R.line(fx, *body_xy(x0, y0 + hdy, 0, IOY), *body_xy(x1, y1 + hdy, 0, IOY))
        cv = comp_any([cv, fx])
    tip = (hx + 0.5, hy - 7.5)
    return cv, tip


def impale_call():
    """2-frame loop, 0.15: staff held high with the player on it, the far hand cupped at his beard,
    bellowing up at the sky for Bixby (shout / laugh, head thrown further back on the second)."""
    out = []
    for k, (mouth, hdy, tl) in enumerate((('shout', -2, 'up'), ('laugh', -3, 'flick'))):
        cv, tip = _held(mouth=mouth, far='cup', hdy=hdy, tl=tl, k=k)
        out.append((cv, {'staff_tip': tip}))
    return out


# ================================================================== WATER BLAST (144x96)
def water_blast():
    """5 frames, 0.3 s, the release on frame 3 (at 0.15 s): YANK (the staff hauled down out of the
    burning player, who hangs in the air; the water gem wakes), WIND-UP (cocked back over his far
    shoulder, sinking), SMEAR (whipped round up-forward through a watery blur), RELEASE (pointed up at
    the player, the gem bursts - the jet leaves the tip), RECOIL (rocked back, water dripping)."""
    out = []
    # 0 yank: staff diagonal down across him, head low right
    A = P.arm(delt=(11.0, 31.5, 5.3), up=(11, 32, 18, 38, 4.8, 4.2), fore=(18, 38, 30, 40, 3.8, 3.5))
    N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 32, 56, 38, 4.7, 4.1), fore=(56, 38, 58, 45, 3.8, 3.4))
    Hd = P.place(X.head(X.WINCE, 'flash'), dy=1)
    body = in_cell(F.comp([D.tails(1, 'mid'), P.place(legs_spread(near=3, far=2)), P.body('torso', dy=1), A, Hd]), LW, LH)
    st = staff_at(LW, LH, B(22, 32), B(68.3, 57.7), orb='water')
    cv = comp_any([body, st, in_cell(N, LW, LH)], staff=st)
    add_fist(cv, B(30, 40.5))
    add_fist(cv, B(57.5, 47))
    spray = R.blank(LW, LH)
    hx0, hy0 = B(68.3, 57.7)
    D.dots(spray, [(hx0 + 9, hy0 - 3), (hx0 + 11, hy0 + 2), (hx0 + 8, hy0 + 6), (hx0 - 2, hy0 - 10), (hx0 + 4, hy0 - 12)], 'l')
    D.dots(spray, [(hx0 + 9, hy0 - 2), (hx0 + 11, hy0 + 3), (hx0 - 2, hy0 - 9)], 'b')
    D.motion_arc(spray[:, :96], hx0 - 20, hy0 - 26, 30.0, 20, 70, ramp=('v', 'w'), thick=1.0)
    cv = comp_any([spray, cv])
    out.append((cv, {}))
    # 1 wind-up: cocked back up-left over the far shoulder, squatting
    sq = 3
    A = P.arm(delt=(11.0, 31.5, 5.3), up=(11, 32, 6, 36, 4.8, 4.0), fore=(6, 36, 3, 30, 3.6, 3.2), dy=sq)
    N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 32, 44, 38, 4.7, 4.0), fore=(44, 38, 26, 37, 3.8, 3.4), dy=sq)
    Hd = P.place(X.head('smirk', 'flash'), dy=sq)
    body = in_cell(F.comp([D.tails(sq, 'hold'), P.place(X.legs_squat(sq, wide=False)), P.body('torso', dy=sq), A, Hd]), LW, LH)
    st = staff_at(LW, LH, B(40, 50 + sq), B(-10, 32 + sq), orb='water')
    cv = comp_any([body, st, in_cell(N, LW, LH)], staff=st)
    add_fist(cv, B(3, 28.5 + sq))
    add_fist(cv, B(26, 36.5 + sq))
    drip = R.blank(LW, LH)
    gx, gy = B(-10, 32 + sq)
    for (dx, dy) in ((-3, 9), (2, 10), (6, 8), (-1, 13), (4, 15), (-5, 5), (8, 3), (-7, 11), (0, 17), (6, 13)):
        FI.plot(drip, gx + dx, gy + dy, 'l')
        FI.plot(drip, gx + dx, gy + dy + 1, 'b')
    D.motion_arc(drip[:, :96], gx + 14, gy + 12, 16.0, 190, 250, ramp=('v', 'w'), thick=1.0)
    cv = comp_any([drip, cv])
    out.append((cv, {}))
    # 2 smear: whipping round, a blur of water from back-left to up-right
    A = P.arm(delt=(11.0, 31.5, 5.3), up=(11, 32, 20, 32, 4.8, 4.2), fore=(20, 32, 32, 28, 3.8, 3.5), dx=2)
    N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 31, 55, 27, 4.6, 3.9), fore=(55, 27, 50, 22, 3.6, 3.2), dx=2)
    Hd = P.place(X.head('shout', 'flash'), dx=2)
    body = in_cell(F.comp([D.tails(0, 'flick', dx=2), P.place(legs_spread(near=5, far=2)), P.body('torso', dx=2), A, Hd]), LW, LH)
    st = staff_at(LW, LH, B(28, 38), B(60, -2), orb='water')
    cv = comp_any([body, st, in_cell(N, LW, LH)], staff=st)
    add_fist(cv, B(32, 27.5))
    add_fist(cv, B(50, 21))
    arc = R.blank(LW, LH)
    cx0, cy0 = B(28, 38)
    for i in range(30):
        a = math.radians(-150 + i * 3.3)
        for rr in (44, 46, 48):
            c = 'q' if i < 8 else ('b' if i < 18 else ('l' if i < 25 else 'W'))
            FI.plot(arc, cx0 + rr * math.cos(a), cy0 + rr * math.sin(a), c)
    for i in range(8):
        a = math.radians(-150 + i * 12)
        FI.plot(arc, cx0 + 51 * math.cos(a), cy0 + 51 * math.sin(a) + i % 3, 'l')
    cv = comp_any([arc, cv])
    out.append((cv, {}))
    # 3 RELEASE: pointing up at the player, the gem bursting; 4 recoil
    for k in (3, 4):
        rec = -2 if k == 3 else -3
        A = P.arm(delt=(11.0, 31.5, 5.3), up=(11, 32, 20, 33, 4.8, 4.2), fore=(20, 33, 34, 27, 3.8, 3.5), dx=rec)
        N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 31, 55, 25, 4.6, 3.9), fore=(55, 25, 52, 17, 3.6, 3.2), dx=rec)
        Hd = P.place(X.head('shout' if k == 3 else 'big', 'flash'), dx=rec - 1, dy=-1)
        body = in_cell(F.comp([D.tails(-1, 'flick' if k == 3 else 'mid', dx=rec - 1),
                               P.place(legs_spread(near=4, far=3)), P.body('torso', dx=rec), A, Hd]), LW, LH)
        butt = B(26 + rec, 40)
        headc = B(59 + rec, -1.4)
        st = staff_at(LW, LH, butt, headc, orb='water')
        cv = comp_any([body, st, in_cell(N, LW, LH)], staff=st)
        add_fist(cv, B(34 + rec, 26.5))
        add_fist(cv, B(52 + rec, 16))
        ang = math.atan2(headc[1] - butt[1], headc[0] - butt[0])
        tip = (headc[0] + 7.5 * math.cos(ang), headc[1] + 7.5 * math.sin(ang))
        spray = R.blank(LW, LH)
        if k == 3:
            for i in range(9):
                a = ang + (i - 4) * 0.28
                for j in range(2, 9):
                    if (i + j) % 3 == 2:
                        continue
                    FI.plot(spray, tip[0] + math.cos(a) * j, tip[1] + math.sin(a) * j, 'W' if j < 5 else 'l')
            R.star(spray, int(tip[0]), int(tip[1]), 3, diag=1)
        else:
            D.dots(spray, [(headc[0] - 3, headc[1] + 9), (headc[0] + 2, headc[1] + 12), (headc[0] - 1, headc[1] + 16)], 'l')
            D.dots(spray, [(headc[0] - 3, headc[1] + 10), (headc[0] + 2, headc[1] + 13)], 'b')
        cv = comp_any([cv, spray])
        out.append((cv, {'staff_tip': tip} if k == 3 else {}))
    return out


# ================================================================== TELEPORT
def teleport():
    """6 frames, 0.35 s (played backward to arrive): the four elements whirl up round him (water, earth,
    fire, air ribbons), tighten and climb as he breaks up into them, his glasses glint last, the whirl
    snaps shut into a burst of the four colours, the last glitter falls."""
    out = []
    A, st, fist, orb = F.far_staff_side(orb='neutral')
    N, nf = F.near_hang()
    base = F.comp([D.tails(0), P.body('legs'), P.body('torso'), N, P.place(X.head('smirk', 'flash')), st, A], staff=st)
    add_fist(base, fist)
    add_fist(base, nf)
    lens_keep = np.zeros(base.shape, bool)
    lx, ly = B(19, 14)
    lens_keep[ly:ly + 3, lx:lx + 15] = np.isin(base[ly:ly + 3, lx:lx + 15], ['W', 'l'])
    cols = (('q', 'b', 'l'), ('Y', '8', '8'), ('n', '6', 'a'), ('v', 'w', 'W'))   # the staff's gem colours
    for k in range(6):
        u = k / 5.0
        if k == 0:
            cv = base.copy()
        elif k == 1:
            cv = _dissolve(base, 0.45, into=('l', 'w'))
        elif k == 2:
            cv = _dissolve(base, 0.95, into=('l', 'w'), keep=lens_keep)
        elif k == 3:
            cv = R.blank(FW, FH)
            cv[lens_keep] = base[lens_keep]
        else:
            cv = R.blank(FW, FH)
        back = lay()
        front = lay()
        if k <= 3:
            rr = 26 - k * 5
            height = 40 + k * 12
            for j, (dk, mid, lt) in enumerate(cols):
                ph = j * math.pi / 2 + k * 1.1
                for i in range(90):
                    f = i / 89.0
                    a = ph + f * math.pi * 3.2
                    x = 48 + rr * math.cos(a) * (1 - 0.3 * f)
                    y = 94 - f * height + rr * 0.22 * math.sin(a)
                    tgt = front if math.sin(a) > 0 else back
                    c = lt if f > 0.75 else (mid if f > 0.3 else dk)
                    FI.plot(tgt, x, y, c)
                    FI.plot(tgt, x, y + 1, dk if f < 0.75 else mid)
        elif k == 4:
            for i in range(24):
                a = i * 0.9
                rr = 6 + (i % 5) * 4
                c = cols[i % 4][1 + (i % 2)]
                FI.plot(front, 48 + math.cos(a) * rr, 50 + math.sin(a) * rr * 0.8, c)
                if i % 3 == 0:
                    R.star(front, int(48 + math.cos(a) * rr), int(50 + math.sin(a) * rr * 0.8), 1, diag=0,
                           core=cols[i % 4][2])
        else:
            for i in range(12):
                c = cols[i % 4][2]
                FI.plot(front, 30 + (i * 13) % 38, 40 + (i * 7) % 30 + i, c)
        if k == 3:
            gx, gy = B(26, 15)
            R.star(front, int(gx), int(gy), 3, diag=1)
        cv = F.comp([back, cv, front])
        out.append((cv, {}))
    return out


# ================================================================== the table
def fitted(fn):
    def run():
        return [(fit(cv), pts) for cv, pts in fn()]
    run.__name__ = fn.__name__
    run.__doc__ = fn.__doc__
    return run


ALL = [
    # name, fn, cell (w, h), anchor, times, on the pillar, exempt frames (vanish frames: numbers not held)
    ('blow', fitted(blow), (96, 96), (48, 96), [0.15, 0.2, 0.12, 0.16, 0.14, 0.13], True, []),
    ('ignite', fitted(ignite), (96, 96), (48, 96), [0.06] * 5, True, []),
    ('channel', fitted(channel), (96, 96), (48, 96), [0.12] * 6, True, []),
    ('vanish', fitted(vanish), (96, 96), (48, 96), [0.12, 0.14, 0.14, 0.14, 0.13, 0.13], True, [2, 3, 4, 5]),
    ('lunge', fitted(lunge), (144, 96), (48, 96), [0.03, 0.02, 0.02, 0.02, 0.03], False, []),
    ('lunge_whiff', fitted(lunge_whiff), (144, 96), (48, 96), [0.07, 0.08, 0.08, 0.07], False, []),
    ('parried', fitted(parried), (96, 96), (48, 96), [0.06, 0.08, 0.08, 0.08], False, []),
    ('impale', fitted(impale), (96, 144), (48, 144), [0.1] * 4, False, []),
    ('impale_call', fitted(impale_call), (96, 144), (48, 144), [0.15, 0.15], False, []),
    ('water_blast', fitted(water_blast), (144, 96), (48, 96), [0.05, 0.05, 0.05, 0.075, 0.075], False, []),
    ('teleport', fitted(teleport), (96, 96), (48, 96), [0.06, 0.06, 0.06, 0.06, 0.06, 0.05], False, [1, 2, 3, 4, 5]),
]
