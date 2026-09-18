"""demon_strike.png and demon_parry_break.png - the two outcomes of one read.

These are the feedback for getting it right or getting it wrong, so they are
designed as a contrasting PAIR rather than as two nice explosions.  The player
should know which one happened from the corner of their eye:

  STRIKE       violet, soft-edged, ragged.  Torn slashes and a broken ring,
               peaking on the very first frame and gone quickly - it is a
               punishment, it should feel like being hit and not like a firework.
  PARRY BREAK  white and gold, hard-edged, geometric.  A four-point star, a
               clean expanding ring and a spray of straight-sided shards, which
               run longer and further than the strike does, with violet smoke
               left behind where the clone was.  Brighter, crisper, bigger.

Both are additive and both are front-loaded.  Frame 0 of the strike is already
the full hit rather than a wind-up: at 30fps a build-up costs 33ms of the
player not knowing what happened.
"""
import math
from fxlib import Mask, Cv, ell, poly, ray, ramp, sheet, hexc

S = 96
C = 48.0
VO = ramp('void')          # e2a2f4 b45ae0 7c2eb0 4e1878 2e0c4c 19062a
GO = ramp('gold')          # fffce0 ffe45c ffc21e d68a12 8a5208 4a2a04
EM = ramp('ember')
WHITE = hexc('ffffff')
PINK = hexc('ffd2d8')


def _burst(n, r0, r1, w0, w1, seed=0, jitter=7.0):
    """n tapered spikes around the centre at irregular angles"""
    m = Mask(S, S)
    for i in range(n):
        a = i * 360.0 / n + math.sin(seed * 1.7 + i * 2.3) * jitter
        m = m | ray(S, S, C, C, a, r0, r1, w0, w1)
    return m


def _ringm(r, thick, squash=1.0):
    return (ell(S, S, C, C, r, r * squash)
            - ell(S, S, C, C, max(0.0, r - thick), max(0.0, (r - thick) * squash)))


def _core(r, lumps=7, seed=0):
    """an irregular blob - a clean circle reads as a bubble, not an impact"""
    pts = []
    for i in range(lumps * 2):
        a = i * math.pi / lumps
        rr = r * (0.72 + 0.40 * abs(math.sin(seed * 2.1 + i * 1.9)))
        pts.append((C + math.cos(a) * rr, C + math.sin(a) * rr))
    return poly(S, S, pts)


# ------------------------------------------------------------------- STRIKE

def strike(f):
    cv = Cv(S, S)
    # frame 0 is already the full hit
    core_r = (16.0, 12.5, 8.5, 4.0, 0.0, 0.0)[f]
    ring_r = (17.0, 27.0, 36.0, 43.0, 47.0, 0.0)[f]
    ring_t = (5.0, 4.5, 3.5, 2.5, 1.5, 0.0)[f]
    sl_r0 = (10.0, 17.0, 25.0, 33.0, 40.0, 44.0)[f]
    sl_r1 = (34.0, 44.0, 48.0, 48.0, 48.0, 48.0)[f]
    sl_w0 = (4.6, 3.8, 3.2, 2.6, 1.8, 1.2)[f]
    # thinning the slashes as fast as the rest turned them into dashed crosses;
    # they have to stay solid streaks or the hit loses its radiating lines
    thin = (16, 16, 14, 12, 9, 6)[f]

    # slashes first, so the core sits on top of their roots
    sl = _burst(7, sl_r0, sl_r1, sl_w0, 0.5, seed=1)
    cv.paint(sl.dither(thin), VO[3])
    cv.paint(sl.erode(1).dither(thin), VO[2])
    if f <= 2:
        cv.paint(sl.erode(2).dither(thin), VO[1])

    if ring_r > 0:
        rg = _ringm(ring_r, ring_t, squash=0.88)
        if f >= 2:                     # the ring tears open as it grows - a
            # few wide gaps, not many narrow ones, which left it as brackets
            rg = rg - _burst(3, 0, 50, 5, 9, seed=4)
        cv.paint(rg.dither(min(16, thin + 3)), VO[2])
        cv.paint(rg.erode(1).dither(thin), VO[1])
        if f <= 1:
            cv.paint(rg.erode(2), PINK)

    if core_r > 0:
        cr = _core(core_r, 7, seed=2)
        cv.paint(cr, VO[1])
        cv.paint(cr.erode(1), WHITE if f <= 1 else (PINK if f == 2 else VO[1]))
        if f <= 1:
            cv.paint(cr.erode(3), WHITE)
        # Carter's red, right at the point of contact
        cv.paint(cr.ring(1) & _core(core_r * 1.3, 5, seed=5), EM[2])

    for i in range(10 - f):            # sparks thrown off
        a = i * 37.0 + f * 11.0
        r = 18 + f * 6 + (i % 4) * 5
        cv.set(int(C + math.cos(math.radians(a)) * r),
               int(C + math.sin(math.radians(a)) * r * 0.9),
               VO[1] if i % 3 else PINK)
    return cv


# -------------------------------------------------------------- PARRY BREAK

def parry_break(f):
    cv = Cv(S, S)
    star = (30.0, 46.0, 38.0, 24.0, 12.0, 0.0)[f]
    ring_r = (13.0, 24.0, 33.0, 41.0, 46.0, 0.0)[f]
    ring_t = (5.5, 5.0, 4.0, 3.0, 2.0, 0.0)[f]
    shard_r = (13.0, 21.0, 30.0, 39.0, 45.0, 47.0)[f]
    core_r = (13.0, 10.0, 7.0, 4.0, 0.0, 0.0)[f]
    thin = (16, 16, 14, 11, 8, 5)[f]

    # ---- violet smoke where the body was, laid down first.  Evenly spaced
    # same-size ellipses came out as polka dots; each puff is two offset
    # ellipses at an irregular radius so no two are the same shape.
    if f >= 2:
        sm = Mask(S, S)
        for i in range(14):
            # golden angle plus a sqrt radius fills a DISC evenly.  Spacing the
            # puffs round a ring, as the first two passes did, left a necklace
            # of separate purple dots instead of one cloud coming apart.
            a = math.radians(i * 137.5 + f * 11)
            frac = ((i + 0.5) / 14.0) ** 0.5
            d = frac * (6.0 + (f - 1) * 7.5)
            px = C + math.cos(a) * d
            py = C + math.sin(a) * d * 0.95
            r = 11.5 - frac * 3.0          # big enough that they merge
            sm = sm | ell(S, S, px, py, r, r * 0.85)
        cv.paint(sm.dither((0, 0, 12, 11, 9, 6)[f], off=1), VO[3])
        cv.paint(sm.erode(4).dither((0, 0, 12, 10, 8, 5)[f], off=2), VO[2])

    # ---- straight-sided shards of the broken clone
    sh = Mask(S, S)
    for i in range(12):
        a = i * 30.0 + 7.0
        ln = 6.0 + (i % 3) * 3.0
        sh = sh | ray(S, S, C, C, a, shard_r, shard_r + ln,
                      3.4 - (i % 3) * 0.6, 0.6)
    cv.paint(sh.dither(thin), GO[2])
    cv.paint(sh.erode(1).dither(thin), GO[0])

    # ---- the clean expanding ring
    if ring_r > 0:
        rg = _ringm(ring_r, ring_t, squash=0.92)
        if f >= 3:                     # only now does it break into arcs
            rg = rg - _burst(6, 0, 50, 5, 9, seed=8)
        cv.paint(rg, GO[2])
        cv.paint(rg.erode(1), GO[1])
        if f <= 2:
            cv.paint(rg.erode(2), GO[0])
        if f <= 1:
            cv.paint(rg.erode(3), WHITE)

    # ---- the four-point star: the signature of a correct read
    if star > 0:
        st = Mask(S, S)
        for a in (0, 90, 180, 270):
            st = st | ray(S, S, C, C, a, 0, star, 5.2, 0.5)
        for a in (45, 135, 225, 315):
            st = st | ray(S, S, C, C, a, 0, star * 0.42, 2.6, 0.5)
        cv.paint(st, GO[1])
        cv.paint(st.erode(1), GO[0])
        cv.paint(st.erode(2), WHITE)

    if core_r > 0:
        cr = ell(S, S, C, C, core_r, core_r)
        cv.paint(cr, GO[0])
        cv.paint(cr.erode(2), WHITE)

    for i in range(12 - f):
        a = i * 31.0 + f * 13.0
        r = 20 + f * 5 + (i % 5) * 4
        cv.set(int(C + math.cos(math.radians(a)) * r),
               int(C + math.sin(math.radians(a)) * r * 0.95),
               WHITE if i % 3 else GO[1])
    return cv


def build(path_strike, path_break):
    sheet([strike(i) for i in range(6)], path_strike)
    sheet([parry_break(i) for i in range(6)], path_break)
    return path_strike, path_break
