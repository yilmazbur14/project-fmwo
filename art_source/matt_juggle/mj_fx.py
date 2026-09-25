"""The effects drawn into Matt's juggle frames.

Matt's house rule for effects (art_source/matt/matt.py, his sound rings; art_source/matt_fx, his
stomp dust): no black keyline round an effect, an edge tone instead so it holds on the pale mat.
Everything here is from his approved 41 colours:

  contact   black speed lines bursting out round the blow, as Mason's juggle draws its contact
  streaks   the swept arc behind a turning body: a near-white core ('z') fading to pale lavender
            ('Z') at its tail, one texel wide
  dust      round puffs kicked off the canvas: white ('W') lit, cool grey ('X') body, darker grey
            ('x') on the shadow side and underneath, no rim
  motes     single dust grains ('X') drifting off the mat

Every effect is drawn only where he is not, and a texel clear of his outline, so nothing is
ever painted over him and nothing boxes a pinhole in against him.
"""
import math

import mj_base as J


def put(px, fx, x, y, k):
    """An effect pixel, only where he is not and never touching him: an effect keeps a clear texel
    all round his outline (8-neighbours), so it can never box a gap in against him (a pinhole)."""
    if not (0 <= x < J.W and 0 <= y < J.H) or (x, y) in px:
        return
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            q = (x + dx, y + dy)
            if q in px and q not in fx:
                return
    px[(x, y)] = k
    fx.add((x, y))


def bres(x0, y0, x1, y1):
    out = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        out.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
    return out


def lines(px, fx, segs, k='k'):
    for (a, b) in segs:
        for (x, y) in bres(int(round(a[0])), int(round(a[1])), int(round(b[0])), int(round(b[1]))):
            put(px, fx, x, y, k)


def burst(px, fx, cx, cy, r0, r1, angles, k='k'):
    """Speed lines radiating from (cx, cy) between radii r0 and r1, one per angle (degrees)."""
    segs = []
    for a in angles:
        t = math.radians(a)
        c, s = math.cos(t), math.sin(t)
        segs.append(((cx + c * r0, cy + s * r0), (cx + c * r1, cy + s * r1)))
    lines(px, fx, segs, k)


def arc(px, fx, cx, cy, r, a0, a1, ry=None, tail='Z', core='z'):
    """A streak along an ellipse from angle a0 to a1 (degrees, clockwise); the last third, where
    it trails off, in the tail tone."""
    ry = r if ry is None else ry
    steps = max(8, int(abs(a1 - a0) * max(r, ry) / 20.0))
    pts = []
    for i in range(steps + 1):
        t = math.radians(a0 + (a1 - a0) * i / steps)
        pts.append((int(round(cx + r * math.cos(t))), int(round(cy + ry * math.sin(t)))))
    seen = []
    for i in range(len(pts) - 1):
        for p in bres(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1]):
            if not seen or seen[-1] != p:
                seen.append(p)
    n = len(seen)
    for j, (x, y) in enumerate(seen):
        put(px, fx, x, y, tail if j < n / 3.0 else core)


def puff(px, fx, cx, cy, r):
    """A dust ball: lit from the upper left, shaded under and to the right, no rim."""
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            u, v = (x + 0.5 - cx) / r, (y + 0.5 - cy) / r
            d2 = u * u + v * v
            if d2 > 1.0:
                continue
            lit = -(u * 0.6 + v * 0.8)
            if d2 > 0.62 and lit < -0.1:
                k = 'x'
            elif lit > 0.35:
                k = 'W'
            else:
                k = 'X'
            put(px, fx, x, y, k)


def motes(px, fx, pts, k='X'):
    for (x, y) in pts:
        put(px, fx, x, y, k)


# ------------------------------------------------------------------------------ per frame
def body_box(body):
    return J.bbox(body)


def add(i, spec, px, body):
    fx = set()
    x0, y0, x1, y1 = body_box(body)
    cx = (x0 + x1) / 2.0
    gy = J.FEET[1]
    if i == 0:
        # The blow itself is the game's (FinisherArtLayout's uppercut impact, spawned on his chin),
        # so the sheet draws his shock instead: jolt lines flying off his head through the gaps
        # between the flared spikes.
        crown = (96, 73)
        burst(px, fx, crown[0], crown[1], 36, 42, (202, 248, 292, 338))
        burst(px, fx, crown[0], crown[1], 44, 48, (225, 315))
        # the canvas he is about to leave, puffing at his feet
        for (x, r) in ((70, 3.2), (78, 2.4), (121, 3.2), (113, 2.4)):
            puff(px, fx, x, gy - r, r)
        motes(px, fx, [(64, gy - 1), (128, gy - 2), (74, gy - 7), (118, gy - 8)])
    elif i == 1:
        # he is going up: short speed lines streaming off below him
        for (x, a, b) in ((84, 128, 136), (95, 131, 141), (106, 126, 135), (74, 120, 127),
                          (116, 117, 124)):
            lines(px, fx, [((x, a), (x, b))], 'Z')
        for (x, r) in ((64, 4.0), (73, 2.8), (128, 4.0), (119, 2.8), (56, 2.0), (136, 2.0)):
            puff(px, fx, x, gy - r, r)
        motes(px, fx, [(60, gy - 9), (132, gy - 10), (68, gy - 13), (125, gy - 14)])
    elif i == 2:
        # the stall at the top: barely a streak, and grains drifting up past him, all placed off his
        # own middle and kept below his top row, so his headroom is set by him and not by a mote
        cxp, cyp = spec.pf
        arc(px, fx, cxp, cyp, 60, 150, 190, ry=54)
        motes(px, fx, [(cxp + dx, max(y0 + 2, cyp + dy)) for (dx, dy) in
                       ((-56, -28), (-50, -20), (54, -30), (59, -18), (-60, 0), (62, 16))], 'z')
    elif 3 <= i <= 6:
        # the swept arc behind whatever is furthest out, trailing the clockwise turn
        th = spec.theta % 360
        # the arc trails the head (the crest's sweep) and the feet on the opposite side
        head = (th - 90) % 360          # screen bearing of his head from the pivot
        feet = (head + 180) % 360
        cxp, cyp = spec.pf
        arc(px, fx, cxp, cyp, 60, head - 62, head - 22, ry=58)
        arc(px, fx, cxp, cyp, 46, feet - 58, feet - 24, ry=44)
    elif i == 7:
        # the mat takes him: dust thrown out FLAT along the canvas from both ends of him, and the
        # impact lines kicking up and out off each end, clear of his outline
        for (x, r) in ((x0 - 8, 4.5), (x0 - 19, 3.5), (x1 + 8, 4.5), (x1 + 19, 3.5),
                       (x0 - 28, 2.5), (x1 + 28, 2.5)):
            puff(px, fx, x, gy - r, r)
        for (sx, ex) in ((x0 - 4, -1), (x1 + 4, 1)):
            lines(px, fx, [((sx, gy - 11), (sx + ex * 7, gy - 17)),
                           ((sx + ex * 2, gy - 5), (sx + ex * 10, gy - 8)),
                           ((sx - ex * 2, gy - 17), (sx + ex * 2, gy - 25))])
        motes(px, fx, [(x0 - 34, gy - 3), (x1 + 34, gy - 4), (x0 - 14, gy), (x1 + 14, gy)])
    elif i == 8:
        # the dust from the impact, bigger and higher, still rolling out
        for (x, r) in ((cx - 64, 5.0), (cx - 51, 4.0), (cx + 64, 5.0), (cx + 52, 4.0),
                       (cx - 74, 2.5), (cx + 74, 2.5)):
            puff(px, fx, x, gy - r - 2, r)
        motes(px, fx, [(int(cx - 44), gy - 12), (int(cx + 46), gy - 13), (int(cx - 30), gy),
                       (int(cx + 30), gy)])
    elif i == 9:
        # thinning and settling
        for (x, r) in ((cx - 68, 3.5), (cx - 57, 2.5), (cx + 68, 3.5), (cx + 58, 2.5)):
            puff(px, fx, x, gy - r, r)
        motes(px, fx, [(int(cx - 78), gy - 2), (int(cx + 78), gy - 3), (int(cx - 50), gy - 8),
                       (int(cx + 50), gy - 9)])
    else:
        # the last of it on the mat
        motes(px, fx, [(int(cx - 70), gy), (int(cx + 72), gy), (int(cx - 58), gy - 2)] if i == 10
              else [(int(cx - 71), gy), (int(cx + 73), gy), (int(cx + 60), gy - 2)])
    return fx
