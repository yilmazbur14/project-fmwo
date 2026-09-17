"""Burak rig: procedural block-in parts driven by a pose dict."""
import math
from blib import *

HOOD = 'EDCBA'          # dark -> light
HOOD_TH = [0.16, 0.36, 0.60, 0.84]
PANTS = 'zQqp'
PANTS_TH = [0.22, 0.48, 0.80]
SKIN = 'gfdsa'
SKIN_TH = [0.15, 0.35, 0.62, 0.88]
SHOE = 'xOo'
SHOE_TH = [0.35, 0.75]


def rot(px, py, ang):
    c, s = math.cos(ang), math.sin(ang)
    return px * c - py * s, px * s + py * c


# ------------------------------------------------------------------ torso
TORSO_PTS = [(-7.0, 3.0), (-7.4, -2.5), (-7.4, -7.5), (-7.0, -11.0), (-6.0, -13.6), (-4.2, -15.4), (-1.5, -16.2),
             (1.5, -16.0), (4.3, -14.6), (6.2, -12.0), (7.0, -8.0), (7.3, -3.5), (7.6, -0.5), (7.2, 3.0)]


def torso_xform(pose):
    hx, hy = pose['hip']
    s = pose.get('slouch', 0.0)
    lean = pose.get('lean', 0.0)

    def f(x, y):
        t = max(0.0, (-y - 5.0) / 11.0)
        x2 = x + s * (t ** 1.6) * 4.2
        y2 = y + s * (t ** 2) * 2.2
        x2, y2 = rot(x2, y2, lean)
        return hx + x2, hy + y2
    return f


def build_torso(pose):
    f = torso_xform(pose)
    pts = [f(x, y) for x, y in TORSO_PTS]
    m = poly_mask(pts)
    hx, hy = pose['hip']
    L = layer()
    s = pose.get('slouch', 0.0)

    def fn(x, y):
        # centre line drifts forward with height (slouch)
        ly = y + 0.5 - hy
        t = max(0.0, (-ly - 5.0) / 11.0)
        cx = hx + s * (t ** 1.6) * 4.2
        nx = (x + 0.5 - cx) / 8.0
        nx = max(-0.98, min(0.98, nx))
        n = (nx * 0.9, -0.25 + 0.3 * t * s, math.sqrt(1 - nx * nx))
        return quant(lambert_wrap(n, wrap=0.2), HOOD, HOOD_TH)
    paint_part(L, m, fn)
    # hem band: 2px rib at the bottom
    for y in range(H):
        for x in range(W):
            if m[y][x] and L[y][x] != '#' and y >= hy + 1:
                L[y][x] = 'D' if L[y][x] in 'EDC' else 'C'
    for x in range(W):
        y = int(hy + 0.5)
        if 0 <= y < H and m[y][x] and L[y][x] != '#':
            L[y][x] = 'E'
    return L, m


# ------------------------------------------------------------------ legs
def ik2(hx, hy, ax, ay, l1, l2, bend=1):
    dx, dy = ax - hx, ay - hy
    d = math.hypot(dx, dy)
    d = min(d, l1 + l2 - 0.01)
    a = math.atan2(dy, dx)
    cosb = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    b = math.acos(max(-1, min(1, cosb)))
    ang = a - b * bend
    return hx + l1 * math.cos(ang), hy + l1 * math.sin(ang)


def build_leg(hip, ankle, shade='near', knee=None, l1=8.0, l2=8.0):
    hx, hy = hip
    ax, ay = ankle
    if knee is None:
        # knee bends forward (+x): in screen coords y down, forward bend => choose sign
        k1 = ik2(hx, hy, ax, ay, l1, l2, 1)
        k2 = ik2(hx, hy, ax, ay, l1, l2, -1)
        knee = k1 if k1[0] >= k2[0] else k2
    kx, ky = knee
    L = layer()
    m1 = tcapsule_mask(hx, hy, kx, ky, 3.5, 3.1)
    m2 = tcapsule_mask(kx, ky, ax, ay, 3.1, 3.0)
    m = m_or(m1, m2)
    th = PANTS_TH if shade == 'near' else [t + 0.25 for t in PANTS_TH]

    def nfn(x, y):
        d1 = seg_t(x + .5, y + .5, hx, hy, kx, ky)
        d2 = seg_t(x + .5, y + .5, kx, ky, ax, ay)
        e1 = math.hypot(x + .5 - d1[1], y + .5 - d1[2])
        e2 = math.hypot(x + .5 - d2[1], y + .5 - d2[2])
        if e1 <= e2:
            return tcapsule_normal(x, y, hx, hy, kx, ky, 3.5, 3.1)
        return tcapsule_normal(x, y, kx, ky, ax, ay, 3.1, 3.0)
    paint_part(L, m, shade_fn(nfn, PANTS, th))
    return L, knee


def foot_poly(ax, ay, ang):
    # local foot, ankle at origin, facing +x, sole at y=+4
    loc = [(-2.6, -1.0), (1.5, -1.2), (4.0, 0.6), (6.6, 1.6), (7.2, 3.0), (7.0, 4.0), (-3.0, 4.0), (-3.2, 1.5)]
    return [(ax + p[0], ay + p[1]) for p in [rot(x, y, ang) for x, y in loc]]


def build_shoe(ankle, ang=0.0, dark=False):
    ax, ay = ankle
    pts = foot_poly(ax, ay, ang)
    m = poly_mask(pts)
    L = layer()
    th = SHOE_TH if not dark else [t + 0.2 for t in SHOE_TH]

    def fn(x, y):
        lx, ly = rot(x + .5 - ax, y + .5 - ay, -ang)
        if ly > 2.6:
            return 'e' if not dark else 'l'
        n = sphere_normal(x, y, ax + 2 * math.cos(ang), ay + 1.4, 6.0, 3.6)
        return quant(lambert_wrap(n), SHOE, th)
    paint_part(L, m, fn)
    return L


# ------------------------------------------------------------------ arm (sleeve)
def build_sleeve(sh, el, wr, r0=3.4, r1=2.9, r2=2.6, dark=False):
    sx, sy = sh
    ex, ey = el
    wx, wy = wr
    m = m_or(tcapsule_mask(sx, sy, ex, ey, r0, r1), tcapsule_mask(ex, ey, wx, wy, r1, r2))
    L = layer()
    th = HOOD_TH if not dark else [t + 0.2 for t in HOOD_TH]

    def nfn(x, y):
        d1 = seg_t(x + .5, y + .5, sx, sy, ex, ey)
        d2 = seg_t(x + .5, y + .5, ex, ey, wx, wy)
        e1 = math.hypot(x + .5 - d1[1], y + .5 - d1[2])
        e2 = math.hypot(x + .5 - d2[1], y + .5 - d2[2])
        if e1 <= e2:
            return tcapsule_normal(x, y, sx, sy, ex, ey, r0, r1)
        return tcapsule_normal(x, y, ex, ey, wx, wy, r1, r2)
    paint_part(L, m, shade_fn(nfn, HOOD, th, wrap=0.35))
    return L, m


# ------------------------------------------------------------------ head block-in
def build_head(cx, cy, tilt=0.0):
    L = layer()
    rx, ry = 10.0, 9.5
    hood = ellipse_mask(cx, cy, rx, ry)
    # bottom flare into the shoulders
    flare = poly_mask([(cx - 8.5, cy + 4), (cx + 5, cy + 4), (cx + 6, cy + 11), (cx - 7.5, cy + 11)])
    hm = m_or(hood, flare)
    paint_part(L, hm, shade_fn(lambda x, y: sphere_normal(x, y, cx, cy, rx, ry + 2), HOOD, HOOD_TH))
    ocx, ocy = cx + 5.0, cy + 2.5
    om = m_and(ellipse_mask(ocx, ocy, 6.2, 7.2), hm)
    rim = m_and(m_sub(ellipse_mask(ocx - 0.3, ocy, 7.6, 8.4), om), hm)
    for y in range(H):
        for x in range(W):
            if rim[y][x] and L[y][x] != '#':
                L[y][x] = 'B' if y < ocy else 'C'
            if om[y][x] and L[y][x] != '#':
                L[y][x] = 'F'
    fm = ellipse_mask(ocx + 1.6, ocy + 1.0, 5.0, 6.2)
    paint_part(L, fm, shade_fn(lambda x, y: sphere_normal(x, y, ocx + 1.6, ocy + 1.0, 5.0, 6.2), SKIN, SKIN_TH))
    return L


def build_frame(pose):
    hx, hy = pose['hip']
    f = torso_xform(pose)
    layers = []
    # far leg + shoe
    fa = pose['far_ankle']
    FL, _ = build_leg((hx + 0.5, hy + 1), fa, shade='far')
    FS = build_shoe(fa, pose.get('far_foot', 0.0), dark=True)
    NA = pose['near_ankle']
    NL, _ = build_leg((hx - 0.5, hy + 1), NA, shade='near')
    NS = build_shoe(NA, pose.get('near_foot', 0.0))
    T, tm = build_torso(pose)
    sh = f(0.0, -12.5)
    el = f(-1.8, -5.5)
    wr = f(4.5, -2.0)
    A, am = build_sleeve(sh, el, wr)
    neck = f(0.0, -16.0)
    s = pose.get('slouch', 0.0)
    Hd = build_head(neck[0] + 1.5 + s * 1.0, neck[1] - 8.0 + s * 1.0)
    return compose([FL, FS, NL, NS, T, A, Hd])


if __name__ == '__main__':
    p1 = dict(hip=(30, 46), slouch=1.0, far_ankle=(33, 59), near_ankle=(27, 59))
    p2 = dict(hip=(30, 46), slouch=0.0, far_ankle=(33, 59), near_ankle=(27, 59))
    a = build_frame(p1)
    b = build_frame(p2)
    preview([a, b], 'rig_8x.png', s=8)
    print('ok')


# ------------------------------------------------------------------ v2 shoe / leg (supersampled, clean sole)
SHOE_LOC = [(-2.8, -1.2), (1.6, -1.4), (3.2, -0.2), (5.4, 0.9), (6.9, 1.5), (7.9, 2.6), (8.1, 4.0), (7.6, 5.0), (-3.0, 5.0), (-3.4, 3.6), (-3.4, 1.0)]


def ss_poly_mask(pts, ss=4, thresh=0.5):
    m = empty_mask()
    n = len(pts)
    ys = [p[1] for p in pts]
    y0, y1 = max(0, int(min(ys)) - 1), min(H, int(max(ys)) + 2)
    for y in range(y0, y1):
        for x in range(W):
            cnt = 0
            for sy in range(ss):
                yc = y + (sy + 0.5) / ss
                xs = []
                for i in range(n):
                    xa, ya = pts[i]
                    xb, yb = pts[(i + 1) % n]
                    if (ya <= yc < yb) or (yb <= yc < ya):
                        xs.append(xa + (yc - ya) * (xb - xa) / (yb - ya))
                xs.sort()
                for sx in range(ss):
                    xc = x + (sx + 0.5) / ss
                    inside = False
                    for k in range(0, len(xs) - 1, 2):
                        if xs[k] <= xc <= xs[k + 1]:
                            inside = True
                            break
                    cnt += inside
            if cnt >= thresh * ss * ss:
                m[y][x] = True
    return m


def build_shoe2(ankle, ang=0.0, dark=False):
    ax, ay = ankle
    pts = [(ax + p[0], ay + p[1]) for p in [rot(x, y, ang) for x, y in SHOE_LOC]]
    m = ss_poly_mask(pts)
    L = layer()
    body, hi, sh, sole = ('x', 'O', 'x', 'O') if dark else ('O', 'o', 'x', 'e')

    def fn(x, y):
        lx, ly = rot(x + .5 - ax, y + .5 - ay, -ang)
        if ly < 0.6 and lx > 2.0:
            return hi
        if lx < -1.5 and ly > 1.0:
            return sh
        return body
    paint_part(L, m, fn)
    # sole: lowest interior pixel of each column
    for x in range(W):
        low = None
        for y in range(H):
            if m[y][x] and L[y][x] != '#':
                low = y
        if low is not None and low + 1 < H and L[low + 1][x] == '#':
            lx, ly = rot(x + .5 - ax, low + .5 - ay, -ang)
            if ly > 2.2:
                L[low][x] = sole
    return L


def build_leg2(hip, ankle, shade='near', l1=6.2, l2=6.2, r=(3.7, 3.3, 3.4)):
    hx, hy = hip
    ax, ay = ankle
    k1 = ik2(hx, hy, ax, ay, l1, l2, 1)
    k2 = ik2(hx, hy, ax, ay, l1, l2, -1)
    kx, ky = k1 if k1[0] >= k2[0] else k2
    L = layer()
    r0, r1, r2 = r
    m = m_or(tcapsule_mask(hx, hy, kx, ky, r0, r1), tcapsule_mask(kx, ky, ax, ay, r1, r2))
    th = PANTS_TH if shade == 'near' else [t + 0.3 for t in PANTS_TH]

    def nfn(x, y):
        d1 = seg_t(x + .5, y + .5, hx, hy, kx, ky)
        d2 = seg_t(x + .5, y + .5, kx, ky, ax, ay)
        e1 = math.hypot(x + .5 - d1[1], y + .5 - d1[2])
        e2 = math.hypot(x + .5 - d2[1], y + .5 - d2[2])
        if e1 <= e2:
            return tcapsule_normal(x, y, hx, hy, kx, ky, r0, r1)
        return tcapsule_normal(x, y, kx, ky, ax, ay, r1, r2)
    paint_part(L, m, shade_fn(nfn, PANTS, th, wrap=0.3))
    return L, (kx, ky)
