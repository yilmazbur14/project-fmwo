"""FX v2 air (no keyline): the round-blast gust burst, the launched player's trail, attack 2's cold breath, and NEW the
downdraft that blows straight down the ring during the maze build (a tileable floor overlay plus lone streaks).

Shapes of wind: streaks with a bright head and a fading tail (motion smears), curling eddies, crescent pressure fronts,
and dust or slate chips caught in the flow. Colours: the shipped gust/breath whites (W l w v), the frost aqua (~) and his
spray blue (b); debris uses the ridges' slate (t T y); the downdraft overlay uses the floor's own semi-transparent shine
and rim keys (] [ ^ ") so it sits on the ice and water like the flood does.
"""
import math
import sys

sys.dont_write_bytecode = True

import numpy as np

import fx_common as C


# ------------------------------------------------------------------ gust burst: 48 x 48, pivot (24, 24) on the staff tip
BURST_FRAMES = 7
BURST_TIMES = [0.03, 0.03, 0.04, 0.04, 0.04, 0.05, 0.06]       # 0.29 s: the shipped burst's length
BURST_PIVOT = (24, 24)


def _smear(cv, x0, y0, x1, y1, keys=('W', 'l', 'w', 'v')):
    """A motion smear from its tail (x0, y0) to its bright head (x1, y1)."""
    def ch(u):
        return keys[0] if u > 0.8 else (keys[1] if u > 0.5 else (keys[2] if u > 0.2 else keys[3]))
    C.line(cv, x0, y0, x1, y1, None, chars=ch)


def _hook(cv, x, y, r, turns, rot, side, chs):
    """An open wind hook: a spiral that never closes (so it reads as air curling off, not as an eye)."""
    n = max(12, int(turns * 2 * math.pi * r * 1.6))
    for i in range(n):
        u = i / (n - 1)
        a = rot + side * 2 * math.pi * turns * u
        rr = r * (1.0 - 0.55 * u)
        C.plot(cv, x + rr * math.cos(a), y + rr * 0.85 * math.sin(a), chs[0] if u < 0.45 else chs[1])


def gust_burst(k):
    """0 the air sucked in: inflow arcs spiralling into a tight vortex on the staff tip; 1 the release: a bright
    blast cone punching down the ring inside a thick pressure crescent, speed lines fanning; 2 the crescent rolls out,
    air curling back off its ends in open hooks, chips kicked up; 3 a second front behind the first, streaks smearing
    past the cell's foot; 4-6 fronts thin and break, the hooks unwind, the last wisps and chips drift out."""
    cv = C.blank(48, 48)
    cx, cy = BURST_PIVOT
    if k == 0:
        for i in range(3):
            rot = math.radians(90 + 120 * i)
            n = 26
            for j in range(n):
                u = j / (n - 1)
                ang = rot + 1.9 * u
                rr = 13.0 - 8.5 * u
                C.plot(cv, cx + rr * math.cos(ang), cy + rr * 0.85 * math.sin(ang),
                       'w' if u < 0.4 else ('l' if u < 0.8 else 'W'))
        C.spiral(cv, cx, cy, 3.4, 1.4, 0.6, 'W', 'l')
        C.plot(cv, cx, cy, 'W')
        return cv
    if k == 1:
        # the release: a lit puff of air bursting off the tip (overlapping balls, lit from the top-left), the pressure
        # crescent just under it, speed lines fanning down the ring
        X, Y = C.R.centres(48, 48)
        for (px_, py_, r) in ((cx, cy + 1, 4.2), (cx - 4, cy + 3, 3.2), (cx + 4, cy + 3, 3.4), (cx, cy + 5, 3.6)):
            m = ((X - px_) / r) ** 2 + ((Y - py_) / (r * 0.85)) ** 2 <= 1
            v = C.R.lambert(C.R.sphere_normal(X, Y, px_, py_, r, r * 0.85))
            cv[m] = np.where(v > 0.55, 'W', np.where(v > 0.25, 'l', 'w'))[m]
        for t in range(3):
            C.arc(cv, cx, cy + 4, 11.5 - t, 9 - t * 0.8, 20, 160, 'W' if t < 2 else 'l')
        C.arc(cv, cx, cy + 4, 8.2, 6.4, 30, 150, 'b')
        for a in range(38, 150, 16):
            ar = math.radians(a)
            _smear(cv, cx + 13 * math.cos(ar), cy + 4 + 10 * math.sin(ar), cx + 20 * math.cos(ar),
                   cy + 4 + 16.5 * math.sin(ar))
        return cv
    front = {2: [(14.5, 'W', 3, 0)], 3: [(19, 'W', 2, 5), (12.5, 'l', 2, 0)], 4: [(21.5, 'l', 2, 4), (16, 'w', 1, 3)],
             5: [(23, 'w', 1, 3), (19, 'v', 1, 2)], 6: [(23.5, 'v', 1, 2)]}[k]
    for (r, ch, thick, gap) in front:
        for t in range(thick):
            C.arc(cv, cx, cy + 2, r - t, (r - t) * 0.8, 24, 156, ch if t < 2 else 'l',
                  gaps=(lambda u, gap=gap: gap and int(u * 26) % (gap + 2) == 0))
        if thick >= 2 and k <= 3:
            C.arc(cv, cx, cy + 2, r - thick, (r - thick) * 0.8, 34, 146, 'b',
                  gaps=(lambda u: int(u * 20) % 4 == 0))
    reach = {2: (15, 23), 3: (19, 24), 4: (21, 24), 5: (22, 24), 6: (23, 24)}[k]
    keys = {2: ('W', 'l', 'w', 'v'), 3: ('W', 'l', 'w', 'v'), 4: ('l', 'w', 'v', 'v'), 5: ('w', 'v', 'v', 'v'),
            6: ('v', 'v', 'v', 'v')}[k]
    for i, a in enumerate(range(44, 140, 12)):
        if k >= 5 and i % 2:
            continue
        ar = math.radians(a)
        r0, r1 = reach
        r0 = r0 - (3 if i % 2 else 0)
        _smear(cv, cx + r0 * math.cos(ar), cy + r0 * 0.85 * math.sin(ar) + 2,
               cx + r1 * math.cos(ar), cy + r1 * 0.85 * math.sin(ar) + 2, keys=keys)
    # air curling back off the front's two ends in open hooks - not a matched pair: one leads, one trails
    if k <= 5:
        a = k - 2
        chs = (('W', 'l'), ('l', 'w'), ('w', 'v'), ('v', 'v'))[a]
        for side, lag in ((-1, 0.0), (1, 0.7)):
            r = 3.2 + 1.1 * (a + lag)
            ex = cx + side * (12.5 + 2.6 * (a + lag))
            ey = cy + 4 + 1.6 * (a + lag)
            _hook(cv, ex, ey, r, 0.8 - 0.12 * a, (math.pi if side < 0 else 0.0) - side * 0.8, -side, chs)
    chips = [(-9, 15, 2), (6, 17, 2), (13, 13, 1), (-15, 12, 1), (1, 19, 1)]
    for i, (dx, dy, size) in enumerate(chips):
        a = k - 2
        x = cx + dx * (1 + 0.25 * a)
        y = cy + dy + 3.5 * a
        if 0 <= y < 47 and 0 <= x < 47:
            if size == 2 and a < 3:
                C.chip(cv, x, y, 2)
            else:
                C.plot(cv, x, y, 'T' if i % 2 else 'y')
    return cv


# ------------------------------------------------------------------ launch trail: 24 x 32, pivot (12, 31), loop
TRAIL_FRAMES = 6
TRAIL_TIME = 0.05
TRAIL_PIVOT = (12, 31)


def gust_trail(k):
    """The wind that carries a launched player down the ring (pivot on their feet; the code loops it): streaks rushing
    down past both sides of the body five rows a frame, an eddy tumbling down each side, a pressure crescent pressing
    on the head, and grit in the flow. Everything wraps every 30 rows, so it loops; the middle stays clear so the
    player reads."""
    cv = C.blank(24, 32)
    P = 30
    lanes = [(1.5, 0, 13, 1.0), (4.5, 11, 10, 1.0), (7.5, 5, 6, 0.55), (16.5, 20, 6, 0.55), (19.5, 7, 10, 1.0),
             (22.5, 17, 13, 1.0)]
    for (x, ph, ln, strength) in lanes:
        head = (ph + 5 * k) % P
        for i in range(ln):
            y = head - i
            yy = y % P + 1
            if yy > 30:
                continue
            u = 1 - i / ln
            if strength < 1:
                ch = 'l' if u > 0.7 else ('w' if u > 0.35 else 'v')
            else:
                ch = 'W' if u > 0.72 else ('l' if u > 0.4 else ('w' if u > 0.18 else 'v'))
            sway = 1 if ((y // 5) % 2 and x > 12) else (-1 if ((y // 5) % 2) else 0)
            C.plot(cv, x + sway * 0.5, yy, ch)
            if strength >= 1 and u > 0.55:
                C.plot(cv, x + sway * 0.5 + (1 if x < 12 else -1), yy, 'l' if u > 0.8 else 'w', under=set('.'))
    # an eddy tumbling down each side, spinning as it goes
    for (ex, ph, d) in ((4.0, 3, -1), (20.0, 18, 1)):
        ey = (ph + 5 * k) % P + 1
        if 3 <= ey <= 28:
            C.spiral(cv, ex, ey, 2.8, 1.2, d * 1.05 * k, 'W', 'l', squash=0.9, direction=d)
    # the pressure pressing on the head: a crescent that bears down and thins
    cy = (0.5, 1.5, 2.5, 3.0, 1.0, 0.0)[k]
    cr = (5.5, 6.0, 6.5, 7.0, 5.0, 5.2)[k]
    C.arc(cv, 12, cy, cr, 2.2, 25, 155, 'W' if k < 3 else 'l', gaps=(lambda u: k >= 3 and int(u * 12) % 3 == 0))
    # grit: flecks of dust and slate flung down faster than the streaks
    for (gx, ph, ch) in ((6.5, 2, 'T'), (17.5, 14, 't'), (9.5, 23, 'v'), (2.5, 27, 't')):
        gy = (ph + 10 * k) % P + 1
        C.plot(cv, gx, gy, ch)
        C.plot(cv, gx, gy - 1, 'v')
    return cv


# ------------------------------------------------------------------ cold breath: 40 x 100, pivot (20, 2) on the mouth
# The code's shape (addendum 3 E.2): frame 0 once, then frames 1..n-2 looping, then the last frame as it stops.
BREATH_FRAMES = 8
BREATH_TIME = 0.06
BREATH_TAGS = {'start': (0, 0), 'loop': (1, 6), 'end': (7, 7)}
BREATH_PIVOT = (20, 2)
BREATH_LOOP = 6


def _wisp(cv, pts, radii, core, edge, shade=None):
    """A soft stream of air: a bright core inside a paler edge, optionally a shaded underside."""
    h, w = cv.shape
    for i in range(len(pts) - 1):
        (ax, ay), (bx, by) = pts[i], pts[i + 1]
        m = C.R.tcapsule_mask(ax, ay, bx, by, radii[i], radii[i + 1], w, h)
        m2 = C.R.tcapsule_mask(ax, ay, bx, by, radii[i] * 0.45, radii[i + 1] * 0.45, w, h)
        if shade is not None:
            m3 = C.R.tcapsule_mask(ax + 0.8, ay + 0.8, bx + 0.8, by + 0.8, radii[i], radii[i + 1], w, h)
            cv[m3 & ~m & (cv == '.')] = shade
        cv[m & ~m2 & (cv != core)] = edge
        cv[m2] = core


def _crystal(cv, x, y, big):
    """An ice crystal: a six-armed glint (big) or a four-point sparkle."""
    C.plot(cv, x, y, 'W')
    arms = ((1, 0), (-1, 0), (0, 1), (0, -1)) if not big else ((1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1))
    for dx, dy in arms:
        C.plot(cv, x + dx, y + dy, 'l')
    if big:
        for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            C.plot(cv, x + dx, y + dy, 'l' if abs(dx) else 'W')


def cold_breath(k):
    """0 start: a frosty jet bursting out of his lips, its rolling head halfway to the pillar's foot; 1-6 loop: the plume
    at full length - three streams fanning, curling as swirls travel down them, a veil of frost between them, ice
    crystals glinting in the flow; 7 end: it lets go of his mouth and breaks up into drifting frost."""
    cv = C.blank(40, 100)
    px, py = BREATH_PIVOT
    if k == 0:
        length, phase, start = 58, 0.0, 0.0
    elif k <= 6:
        length, phase, start = 97, (k - 1) / BREATH_LOOP, 0.0
    else:
        length, phase, start = 97, 0.0, 0.34
    fade = k == 7
    for j, side in enumerate((-1, 0, 1)):
        pts, radii = [], []
        for i in range(34):
            u = i / 33.0
            if u < start:
                continue
            spread = side * 17.0 * u ** 0.9
            curl = math.sin(2 * math.pi * (u * 1.6 - phase) + j * 1.7) * (1.1 * u + 0.3)
            pts.append((px + spread + curl, py + u * length))
            radii.append(0.7 + 2.3 * math.sin(math.pi * min(1.0, u * 1.06)) * (0.65 if fade else 1.0))
        if len(pts) > 1:
            core = 'W' if side == 0 else 'l'
            _wisp(cv, pts, radii, core if not fade else 'l', '~', shade='b' if not fade else None)
    # frost motes between the streams: clumps of cold mist flowing down with the plume, a few sparkling
    X, Y = C.R.centres(40, 100)
    u_map = np.clip((Y - py) / 97.0, 0, 1)
    half = 2.5 + 17.0 * u_map ** 0.85
    rel = np.abs(X - px) / half
    inside = (rel < 0.92) & (Y >= py + 97 * start + 3) & (Y <= py + length)
    field = C.vnoise((100, 40), (14, 7), 13, periodic=(True, False))
    rows = ((np.arange(100)[:, None] - int(round(97 * phase))) % 100).repeat(40, 1)
    n = field[rows, np.arange(40)[None, :].repeat(100, 0)]
    thr = 0.64 + (0.06 if fade else 0.0)
    mote = inside & (n > thr) & (cv == '.')
    cv[mote] = np.where(n[mote] > thr + 0.1, 'l', '~')
    spark = inside & (n > thr + 0.17) & (((X + Y).astype(int) + k) % 5 == 0)
    cv[spark] = 'W'
    # swirls: mist balls rolling down the streams, curled edges lit on top and shaded under
    for i in range(5):
        u = ((i / 5.0) + phase) % 1.0 if k >= 1 else (i / 5.0) * (length / 97.0)
        if k == 0 and u * 97 > length - 4:
            continue
        if fade and u < start + 0.12:
            continue
        side = (-1, 1, 0, 1, -1)[i]
        x = px + side * 17.0 * u ** 0.9 * 0.8 + math.sin(2 * math.pi * (u * 2.2 - phase)) * 2
        y = py + u * 97
        r = 2.6 + 2.6 * u
        m = ((X - x) / r) ** 2 + ((Y - y) / (r * 0.8)) ** 2 <= 1
        if fade:
            m &= ((X.astype(int) + Y.astype(int) + k) % 3) != 0
        v = C.R.lambert(C.R.sphere_normal(X, Y, x, y, r, r * 0.8))
        cv[m] = np.where(v > 0.62, 'W', np.where(v > 0.3, 'l', '~'))[m]
        # the eddy curling in it: an open hook turning as it rolls, lit on its outer lip
        rot = 2 * math.pi * phase * 2 + i * 1.3
        for q in range(16):
            t = q / 15.0
            ang = rot + 1.6 * math.pi * t
            rr = r * (1.05 - 0.6 * t)
            C.plot(cv, x + rr * math.cos(ang), y + rr * 0.8 * math.sin(ang), ('b' if not fade else '~') if t > 0.3 else 'W')
    # the start's rolling head
    if k == 0:
        hx, hy = px, py + length - 3
        r = 6.0
        m = ((X - hx) / r) ** 2 + ((Y - hy) / (r * 0.75)) ** 2 <= 1
        v = C.R.lambert(C.R.sphere_normal(X, Y, hx, hy, r, r * 0.75))
        cv[m] = np.where(v > 0.6, 'W', np.where(v > 0.3, 'l', '~'))[m]
        C.spiral(cv, hx, hy, r * 0.75, 1.0, 1.0, 'b', 'l', squash=0.75)
    # ice crystals glinting in the flow: each one sparkles for a frame or two as it drifts down
    rnd = np.random.RandomState(7)
    for i in range(14):
        u0 = rnd.rand()
        side = rnd.uniform(-1, 1)
        born = rnd.randint(0, BREATH_LOOP)
        age = ((k - 1) - born) % BREATH_LOOP if 1 <= k <= 6 else (0 if k == 0 else 2)
        if k == 0 and u0 * 97 > length:
            continue
        u = (u0 + 0.08 * max(0, age)) % 1.0
        x = px + side * 15 * u ** 0.9 + side * 2
        y = py + 4 + u * 94
        if 0 <= age <= 1:
            _crystal(cv, x, y, big=(i % 2 == 0 and age == 0))
        elif age <= 3:
            C.plot(cv, x, y, 'l' if age == 2 else '~')
    return cv


# ------------------------------------------------------------------ NEW the downdraft: liam_downdraft.png
# The code (addendum 3 E.2.7, LiamElementFx.downdraft) spawns one of these every 0.03 s at a random x on the row line
# (y 348), drops it at downdraft_speed x 1.5 (1800 px/s) on the FxLayer and fades it; the sprite only has to be a gust
# of cold wind animating in place. Pivot = its top centre (its tail), so it pours out of the row's foot.
DRAFT_W, DRAFT_H = 20, 80
DRAFT_FRAMES = 6
DRAFT_TIME = 0.04
DRAFT_PIVOT = (10, 0)


def _gust_line(cv, x0, y_tail, y_head, amp, lam, phase, bold=True, curl=0, curl_rot=0.0):
    """A wavy wind line from its tail (top) to its head (bottom): tapered at both ends, two texels wide through its
    middle when bold (a bright core with a paler flank), a spray-blue edge down its right side so it reads on the pale
    ice as well as on the water, its head optionally curling over into an open hook."""
    n = int(y_head - y_tail)
    pts = []
    for j in range(n + 1):
        u = j / max(1, n)                                # 0 tail .. 1 head
        y = y_tail + j
        env = math.sin(math.pi * min(1.0, 0.15 + 0.85 * u))
        x = x0 + amp * math.sin(2 * math.pi * (y / lam) - phase) * env
        pts.append((x, y, u))
    for (x, y, u) in pts:
        if 0.18 < u < 0.94:
            C.plot(cv, x + (2 if bold and 0.3 < u < 0.85 else 1), y, 'b' if 0.3 < u < 0.85 else '~', under=set('.'))
    for (x, y, u) in pts:
        if u < 0.16:
            ch = 'w'
        elif u < 0.4:
            ch = 'l'
        elif u < 0.9:
            ch = 'W'
        else:
            ch = 'l'
        C.plot(cv, x, y, ch)
        if bold and 0.3 < u < 0.85:
            C.plot(cv, x + 1, y, 'l')
    if curl:
        hx, hy, _ = pts[-1]
        for q in range(13):
            t = q / 12.0
            ang = curl_rot + curl * 1.35 * math.pi * t
            rr = 4.0 * (1 - 0.35 * t)
            x = hx + curl * 4.0 - curl * rr * math.cos(ang)
            y = hy - rr * math.sin(ang) - 1
            C.plot(cv, x, y, 'W' if t < 0.4 else ('l' if t < 0.75 else 'w'))
            if t < 0.6:
                C.plot(cv, x + 1, y + 1, 'b', under=set('.'))


def downdraft(k):
    """A gust of the cold downdraft (loops in place while the code drops it down the ring): a long bold wavy line and
    a thinner one beside it, snaking as the ripple runs down them, the long one's head curling over and turning, a
    fleck of frost riding along."""
    cv = C.blank(DRAFT_W, DRAFT_H)
    phase = 2 * math.pi * k / DRAFT_FRAMES
    _gust_line(cv, 7.0, 4, 70, 2.4, 34.0, phase, bold=True, curl=1, curl_rot=phase)
    comp = (0, 2, 4, 5, 3, 1)[k]
    _gust_line(cv, 13.0, 20 + comp, 58 + comp, 1.8, 28.0, phase + 1.3, bold=False)
    fy = (10 + 11 * k) % 70 + 4
    C.plot(cv, 3 if k % 2 else 17, fy, 'W')
    C.plot(cv, 3 if k % 2 else 17, fy - 1, 'l')
    return cv
