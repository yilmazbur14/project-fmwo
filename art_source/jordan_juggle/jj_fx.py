"""The effects drawn into Jordan's juggle frames, in his approved 40 colours and his rig's own FX
grammar (janim_base.FX_KEYS: glints and sparkles float free of any keyline):

  jolt      black speed lines flying off his head on the blow (the game draws the blow itself)
  streaks   the swept arc behind a turning body: a near-white core ('W') fading to his grey ('9')
            at its tail, one texel wide, trailing a COUNTER-clockwise turn (he goes over backwards)
  dust      round puffs kicked off the canvas: off-white ('0') lit, grey ('9') body, slate ('3') on
            the shadow side and underneath, no rim
  motes     single grains ('9')
  glint     the approved glint (janim_idle.sparkle: a white centre with pink arms) on the box: it
            came through without a scratch

Every effect is drawn only where he is not, and a texel clear of his outline, so nothing is
ever painted over him and nothing boxes a pinhole in against him.
"""
import math

import jj_base as J


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
    segs = []
    for a in angles:
        t = math.radians(a)
        c, s = math.cos(t), math.sin(t)
        segs.append(((cx + c * r0, cy + s * r0), (cx + c * r1, cy + s * r1)))
    lines(px, fx, segs, k)


def arc(px, fx, cx, cy, r, a0, a1, ry=None, tail='9', core='W'):
    """A streak along an ellipse from angle a0 to a1 (degrees); the third nearest a0 is the tail."""
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
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            u, v = (x + 0.5 - cx) / r, (y + 0.5 - cy) / r
            d2 = u * u + v * v
            if d2 > 1.0:
                continue
            lit = -(u * 0.6 + v * 0.8)
            if d2 > 0.62 and lit < -0.1:
                k = '3'
            elif lit > 0.35:
                k = '0'
            else:
                k = '9'
            put(px, fx, x, y, k)


def motes(px, fx, pts, k='9'):
    for (x, y) in pts:
        put(px, fx, x, y, k)


def glint(px, fx, cx, cy):
    """janim_idle.sparkle: a white centre, pink arms; laid over the box, which is his."""
    for (dx, dy, k) in ((0, 0, 'W'), (1, 0, 'Q'), (-1, 0, 'Q'), (0, 1, 'Q'), (0, -1, 'Q')):
        q = (cx + dx, cy + dy)
        px[q] = k
        fx.add(q)


def box_corner(owner, which):
    """A corner of the box as drawn in this frame (its owned pixels): 'top-right' etc."""
    pts = [q for q, o in owner.items() if o == 'box']
    if not pts:
        return None
    if which == 'top':
        y = min(p[1] for p in pts)
        xs = sorted(p[0] for p in pts if p[1] == y)
        return (xs[-1], y)
    x = max(p[0] for p in pts)
    ys = sorted(p[1] for p in pts if p[0] == x)
    return (x, ys[0])


# ------------------------------------------------------------------------------ per frame
def add(i, spec, px, body, owner):
    fx = set()
    x0, y0, x1, y1 = J.bbox(body)
    cx = (x0 + x1) / 2.0
    gy = J.FEET[1]
    if i == 0:
        # jolt lines off his head, thrown back and to the left
        head = [q for q, o in owner.items() if o == 'head']
        hx0, hy0, hx1, hy1 = J.bbox({q: 1 for q in head})
        hc = ((hx0 + hx1) / 2.0, (hy0 + hy1) / 2.0)
        burst(px, fx, hc[0], hc[1], 16, 21, (160, 190, 215, 240))
        for (x, r) in ((72, 3.0), (79, 2.2), (116, 3.0), (109, 2.2)):
            puff(px, fx, x, gy - r, r)
        motes(px, fx, [(66, gy - 1), (122, gy - 2), (75, gy - 7), (113, gy - 8)])
    elif i == 1:
        for (x, a, b) in ((82, 131, 138), (92, 133, 141), (102, 130, 137), (74, 125, 131)):
            lines(px, fx, [((x, a), (x, b))], '9')
        for (x, r) in ((66, 3.6), (74, 2.6), (122, 3.6), (114, 2.6), (58, 2.0), (130, 2.0)):
            puff(px, fx, x, gy - r, r)
        motes(px, fx, [(62, gy - 9), (126, gy - 10), (70, gy - 13), (119, gy - 14)])
    elif i == 2:
        # the stall: barely a streak, grains drifting up past him, placed off his own middle and
        # kept below his top row, so his headroom is set by him and not by a mote
        cxp, cyp = spec.pf
        arc(px, fx, cxp, cyp, 50, 40, 10, ry=48)
        motes(px, fx, [(cxp + dx, max(y0 + 2, cyp + dy)) for (dx, dy) in
                       ((-50, -30), (-44, -22), (50, -32), (55, -20), (-54, -4), (56, 14))])
    elif 3 <= i <= 6:
        # the arc swept behind his head and his feet, trailing the counter-clockwise turn
        th = spec.theta
        head = (th - 90) % 360            # screen bearing of his head from the pivot
        feet = (head + 180) % 360
        cxp, cyp = spec.pf
        arc(px, fx, cxp, cyp, 50, head + 58, head + 20, ry=48)
        arc(px, fx, cxp, cyp, 42, feet + 52, feet + 20, ry=40)
    elif i == 7:
        for (x, r) in ((x0 - 8, 4.0), (x0 - 18, 3.0), (x1 + 8, 4.0), (x1 + 18, 3.0),
                       (x0 - 26, 2.2), (x1 + 26, 2.2)):
            puff(px, fx, x, gy - r, r)
        for (sx, ex) in ((x0 - 4, -1), (x1 + 4, 1)):
            lines(px, fx, [((sx, gy - 10), (sx + ex * 6, gy - 15)),
                           ((sx + ex * 2, gy - 4), (sx + ex * 9, gy - 7)),
                           ((sx - ex * 2, gy - 15), (sx + ex * 2, gy - 22))])
        motes(px, fx, [(x0 - 32, gy - 3), (x1 + 32, gy - 4), (x0 - 13, gy), (x1 + 13, gy)])
    elif i == 8:
        for (x, r) in ((cx - 56, 3.6), (cx - 46, 2.6), (cx + 56, 3.6), (cx + 47, 2.6)):
            puff(px, fx, x, gy - r - 2, r)
        motes(px, fx, [(int(cx - 40), gy - 11), (int(cx + 42), gy - 12), (int(cx - 28), gy),
                       (int(cx + 28), gy)])
    elif i == 9:
        for (x, r) in ((cx - 62, 3.2), (cx - 52, 2.2), (cx + 62, 3.2), (cx + 53, 2.2)):
            puff(px, fx, x, gy - r, r)
        motes(px, fx, [(int(cx - 72), gy - 2), (int(cx + 72), gy - 3), (int(cx - 46), gy - 7),
                       (int(cx + 46), gy - 8)])
    elif i == 10:
        # out cold, and the box without a scratch on it
        c = box_corner(owner, 'right')
        if c:
            glint(px, fx, c[0] + 1, c[1] - 1)
        motes(px, fx, [(int(cx - 62), gy), (int(cx + 64), gy), (int(cx - 50), gy - 2)])
    else:
        motes(px, fx, [(int(cx - 63), gy), (int(cx + 65), gy), (int(cx + 52), gy - 2)])
    return fx
