"""nugget_meteor.png - 4-frame loop, 48x64 frames.
A breaded chicken nugget falling down-left (20 degrees off vertical) trailing fire and hot
grease up-right. Seamless loop: every moving element (flame licks, grease drops, smoke)
advances exactly one spacing over the 4 frames."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fxlib import *

FW, FH = 48, 64
ANG = math.radians(20.0)
V = (-math.sin(ANG), math.cos(ANG))        # travel direction (down-left)
B = (-V[0], -V[1])                          # trail direction (up-right)
P = (math.cos(ANG), math.sin(ANG))          # sideways axis of the trail
C = (16.5, 48.0)                            # nugget centre (continuous coords)
L = 40.0                                    # trail length from the nugget centre
SP = 8.0                                    # flame lick spacing (loop period)


def to_world(s, t):
    return (C[0] + B[0] * s + P[0] * t, C[1] + B[1] * s + P[1] * t)


def local(x, y):
    dx, dy = x - C[0], y - C[1]
    return dx * B[0] + dy * B[1], dx * P[0] + dy * P[1]


def hash01(x, y, seed=0):
    h = (x * 374761393 + y * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


# ----------------------------------------------------------------------------- flame
def flame_mask(f):
    licks = [(1.5, 0.0, 8.0, 1.15)]            # main body hugging the back of the nugget
    n = int(L / SP) + 2
    for k in range(-1, n):
        s = 4.0 + k * SP + f * SP / 4.0
        if s < 4.0 or s > L:
            continue
        u = s / L
        r = 7.9 * (1.0 - u) ** 0.8 + 0.8
        t = (2.2 if k % 2 else -2.2) * min(1.0, s / 10.0) * (1.0 + 0.5 * u)
        licks.append((s, t, r, 1.8))
    m = set()
    for y in range(FH):
        for x in range(FW):
            s, t = local(x + 0.5, y + 0.5)
            if s < -1.5:                       # only a thin glow may wrap the front
                continue
            for (ls, lt, r, el) in licks:
                ds = (s - ls) / el
                if ds * ds + (t - lt) ** 2 <= r * r:
                    m.add((x, y))
                    break
    return m


def inner_distance(mask):
    """4-connected steps to the nearest pixel outside the mask"""
    from collections import deque
    dist = {}
    q = deque()
    for p in mask:
        if any((p[0] + dx, p[1] + dy) not in mask for dx, dy in N4):
            dist[p] = 1
            q.append(p)
    while q:
        p = q.popleft()
        for dx, dy in N4:
            n = (p[0] + dx, p[1] + dy)
            if n in mask and n not in dist:
                dist[n] = dist[p] + 1
                q.append(n)
    return dist


def paint_flame(g, fmask):
    dist = inner_distance(fmask)
    for (x, y) in fmask:
        s, t = local(x + 0.5, y + 0.5)
        d = dist[(x, y)]
        u = max(0.0, s) / L
        if d >= 4 and u < 0.30:
            c = F_CORE
        elif d >= 3 and u < 0.62:
            c = F_YEL
        elif d >= 2 or u < 0.25:
            c = F_ORG
        else:
            c = F_RED if u > 0.35 else F_ORG
        put(g, x, y, c)
    for p in outline_of(fmask):
        put(g, p[0], p[1], F_EDGE)
    return fmask


# ----------------------------------------------------------------------------- nugget
RX, RY = 8.0, 6.8
NM_WARM = hx('#C27C3E')   # warm golden-brown mid (fire-lit breading)
BUMPS = [(0.05, 2, 1.3), (0.09, 3, 0.2), (0.04, 5, 2.2), (0.06, 11, 0.8)]
LIGHT = (-0.55, -0.62, 0.56)
_n = math.sqrt(sum(c * c for c in LIGHT))
LIGHT = tuple(c / _n for c in LIGHT)


def nugget_pixels(cx, cy, rot):
    m = {}
    cr, sr = math.cos(rot), math.sin(rot)
    for y in range(int(cy - 12), int(cy + 13)):
        for x in range(int(cx - 12), int(cx + 13)):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            u = dx * cr + dy * sr
            v = -dx * sr + dy * cr
            th = math.atan2(v / RY, u / RX)
            lim = 1.0 + sum(a * math.cos(k * th + ph) for a, k, ph in BUMPS)
            d = math.hypot(u / RX, v / RY) / lim
            if d <= 1.0:
                m[(x, y)] = (u, v, d)
    return m


def paint_nugget(g, cx, cy, rot, f):
    m = nugget_pixels(cx, cy, rot)
    cr, sr = math.cos(rot), math.sin(rot)
    rim_px = inner_edge(set(m))
    for (x, y), (u, v, d) in m.items():
        # dome normal in local space, rotated back to screen space
        # pillow profile: flat top, shading concentrated toward the rim
        k_ = min(1.0, d) ** 3
        nzl = math.sqrt(max(0.0, 1.0 - k_)) * 0.85 + 0.15
        nul, nvl = (u / RX) * k_ ** 0.5, (v / RY) * k_ ** 0.5
        nx = nul * cr - nvl * sr
        ny = nul * sr + nvl * cr
        ln = math.sqrt(nx * nx + ny * ny + nzl * nzl) or 1.0
        nx, ny, nz = nx / ln, ny / ln, nzl / ln
        I = nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]
        # crunchy breading: per-pixel crumb noise attached to the nugget surface
        lu, lv = int(math.floor(u + 20)), int(math.floor(v + 20))
        I += (hash01(lu, lv, 7) - 0.5) * 0.16
        if I > 0.74:
            c = N_HI
        elif I > 0.42:
            c = N_BASE
        elif I > 0.14:
            c = NM_WARM
        else:
            c = N_DEEP
        # crunchy crumb speckle: light crumbs catch the light, dark pockets sit between them
        hc = hash01(lu, lv, 31)
        if d < 0.86:
            if hc > 0.84 and c == N_BASE and I > 0.50:
                c = N_HI
            elif hc < 0.13 and c == N_BASE:
                c = NM_WARM
            elif hc < 0.10 and c == NM_WARM:
                c = N_DEEP
        # warm firelight on the trailing (up-right) rim
        dx, dy = x + 0.5 - cx, y + 0.5 - cy
        dl = math.hypot(dx, dy) or 1.0
        back = (dx * B[0] + dy * B[1]) / dl
        if (x, y) in rim_px and back > 0.35:
            c = F_ORG if c in (N_MID, N_DEEP) else F_YEL
        put(g, x, y, c)
    # a few deep crunchy pits (surface-attached so they tumble with the nugget)
    for (pu, pv) in ((-3.0, -1.5), (2.5, 2.2), (4.2, -2.4), (-0.5, 3.2), (-5.2, 1.8)):
        x = int(math.floor(cx + pu * cr - pv * sr))
        y = int(math.floor(cy + pu * sr + pv * cr))
        if (x, y) in m and (x, y) not in rim_px:
            put(g, x, y, N_DEEP if g[y][x] != N_DEEP else N_DARK)
    for p in outline_of(set(m)):
        put(g, p[0], p[1], K)
    return set(m)


# ----------------------------------------------------------------------------- grease + smoke
def paint_grease(g, f):
    D = 12.0
    for side, off in ((1, 0.0), (-1, 6.0)):
        for k in range(-1, 6):
            s = 7.0 + off + k * D + f * D / 4.0
            if s < 8.0 or s > L - 2:
                continue
            t = side * (7.9 * (1 - s / L) ** 0.8 + 4.4)
            x, y = to_world(s, t)
            xi, yi = int(math.floor(x)), int(math.floor(y))
            if s < 26:
                drop = [(xi, yi), (xi + 1, yi), (xi, yi + 1), (xi + 1, yi + 1), (xi + 1, yi - 1), (xi + 2, yi - 2)]
                hi = (xi, yi)
            else:
                drop = [(xi, yi), (xi + 1, yi), (xi, yi + 1), (xi + 1, yi + 1)]
                hi = (xi, yi)
            ds = set(drop)
            for p in outline_of(ds):
                if get(g, *p)[3] == 0:
                    put(g, p[0], p[1], G_EDGE)
            for p in drop:
                put(g, p[0], p[1], G_MID)
            put(g, hi[0], hi[1], G_HI)


def paint_smoke(g, f):
    D = 9.0
    for k in range(-1, 3):
        s = L - 7.0 + k * D + f * D / 4.0
        if s < L - 7.0 or s > L + 6.0:
            continue
        u = (s - (L - 7.0)) / 13.0
        r = 2.3 - 1.0 * u
        t = (1.5 if k % 2 else -1.5)
        cx, cy = to_world(s, t)
        pm = {(x, y) for y in range(int(cy - 4), int(cy + 5)) for x in range(int(cx - 4), int(cx + 5))
              if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r}
        if not pm:
            continue
        for p in outline_of(pm):
            if get(g, *p)[3] == 0:
                put(g, p[0], p[1], S_DK)
        for (x, y) in pm:
            if get(g, x, y) in (T, S_DK):
                put(g, x, y, S_LT if (x + 0.5 - cx) + (y + 0.5 - cy) < -0.5 else S_MID)


def meteor_frame(f, spin=True):
    g = canvas(FW, FH)
    paint_flame(g, flame_mask(f))
    paint_grease(g, f)
    rot = 0.3 + ((f * math.pi / 2.0) if spin else 0.0)
    nm = paint_nugget(g, C[0], C[1], rot, f)
    return g, nm


def leading_tip(frames_masks):
    """most-forward outline pixel along the travel direction, per frame"""
    tips = []
    for g, nm in frames_masks:
        ol = outline_of(nm) | nm
        best = max(ol, key=lambda p: (p[0] + 0.5) * V[0] + (p[1] + 0.5) * V[1])
        tips.append(best)
    return tips


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'nugget_meteor_wip.png'
    spin = not (len(sys.argv) > 2 and sys.argv[2] == 'nospin')
    fm = [meteor_frame(f, spin) for f in range(4)]
    sheet = strip([g for g, _ in fm])
    check_alpha(sheet, 'meteor')
    edge_touch(sheet, FW, FH, 'meteor')
    save(out, sheet)
    print('wrote', out, len(sheet[0]), len(sheet), 'colours', len(colours(sheet)))
    print('nugget centre', C, 'leading tips', leading_tip(fm))
