"""nugget_impact.png - 5 frames of 64x48. Ground impact point = frame centre (32, 24),
the same point as the nugget_target centre, so both sprites can share one position.
f0 flash, f1 fireball + splat + dust ring + crumbs, f2 fireball rises and cools,
f3 smoke + dust breaks up + crumbs falling, f4 settle (crumbs down, splat, last wisp).
Alpha 0/255 only. Shape tools follow the elbow_impact generator (star bands, shaded puffs)."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fxlib import *

FW, FH = 64, 48
GX, GY = 32.0, 24.0
NM_WARM = hx('#C27C3E')
PERSP = 0.42
SMK_HI = hx('#9BADB7')     # DB32
SMK    = hx('#847E87')     # DB32
SMK_SH = hx('#696A6A')     # DB32
SMK_OL = hx('#45283C')     # DB32 dark plum outline (warm, not pure black, like dust's brown edge)

LIGHT = (-0.5, -0.8, 0.65)
_n = math.sqrt(sum(v * v for v in LIGHT))
LIGHT = tuple(v / _n for v in LIGHT)


def mirror_set(s):
    out = set()
    for (x, y) in s:
        out.add((x, y))
        out.add((FW - 1 - x, y))
    return out


def pip(x, y, pts):
    inside = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]; xj, yj = pts[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi):
            inside = not inside
        j = i
    return inside


def star(cx, cy, spikes, irx, iry):
    pts = []
    sp = sorted(spikes)
    for i, (a, L) in enumerate(sp):
        ar = math.radians(a)
        pts.append((cx + math.cos(ar) * L, cy + math.sin(ar) * L))
        a2 = sp[(i + 1) % len(sp)][0]
        if a2 <= a:
            a2 += 360
        am = math.radians((a + a2) / 2.0)
        pts.append((cx + math.cos(am) * irx, cy + math.sin(am) * iry))
    return pts


def poly_mask(pts):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return {(x, y) for y in range(max(0, int(min(ys)) - 1), min(FH, int(max(ys)) + 2))
            for x in range(max(0, int(min(xs)) - 1), min(FW, int(max(xs)) + 2)) if pip(x + 0.5, y + 0.5, pts)}


def scale_pts(pts, cx, cy, s):
    return [(cx + (x - cx) * s, cy + (y - cy) * s) for x, y in pts]


def puffs(circles, ramp, outline):
    """union of shaded circles (cauliflower cloud) -> {(x,y): colour}"""
    out = {}
    for y in range(FH):
        for x in range(FW):
            best = None
            for cx, cy, r in circles:
                dx, dy = x + 0.5 - cx, y + 0.5 - cy
                d2 = dx * dx + dy * dy
                if d2 <= r * r:
                    nz = math.sqrt(1 - d2 / (r * r))
                    h = nz * r - cy * 0.02
                    if best is None or h > best[0]:
                        best = (h, dx / r, dy / r, nz)
            if best:
                _, nx, ny, nz = best
                I = nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]
                out[(x, y)] = ramp[0] if I > 0.80 else ramp[1] if I > 0.38 else ramp[2] if I > 0.0 else ramp[3]
    if outline:
        m = set(out)
        for p in outline_of(m):
            if 0 <= p[0] < FW and 0 <= p[1] < FH:
                out[p] = outline
    return out


def paint(g, d):
    for (x, y), c in d.items():
        put(g, x, y, c)


def mirror_circles(circles):
    return [(FW - cx, cy, r) for cx, cy, r in circles]


# ----------------------------------------------------------------------------- pieces
def flash(g, spikes, irx, iry, cy_off=-2.0):
    cx, cy = GX, GY + cy_off
    outer = star(cx, cy, spikes, irx, iry)
    m_o = mirror_set(poly_mask(outer))
    m_y = mirror_set(poly_mask(scale_pts(outer, cx, cy, 0.64)))
    m_w = mirror_set(poly_mask(scale_pts(outer, cx, cy, 0.34)))
    paint_mask(g, m_o, F_ORG)
    paint_mask(g, m_y, F_YEL)
    paint_mask(g, m_w, F_CORE)
    for p in outline_of(m_o):
        put(g, p[0], p[1], F_EDGE)


def fireball(g, cx, cy, r, cool=False):
    lobes = [(0, 0, r), (-r * 0.68, r * 0.30, r * 0.66), (r * 0.68, r * 0.30, r * 0.66),
             (-r * 0.36, -r * 0.62, r * 0.60), (r * 0.36, -r * 0.62, r * 0.60), (0, r * 0.55, r * 0.62)]
    m = set()
    for (dx, dy, rr) in lobes:
        m |= {(x, y) for y in range(int(cy + dy - rr) - 1, int(cy + dy + rr) + 2)
              for x in range(int(cx + dx - rr) - 1, int(cx + dx + rr) + 2)
              if (x + 0.5 - cx - dx) ** 2 + (y + 0.5 - cy - dy) ** 2 <= rr * rr}
    m = mirror_set(m)
    for (x, y) in m:
        d = math.hypot(x + 0.5 - cx, (y + 0.5 - cy - r * 0.15) * 1.1) / r
        if cool:
            c = F_YEL if d < 0.36 else (F_ORG if d < 0.95 else F_RED)
        else:
            c = F_CORE if d < 0.40 else (F_YEL if d < 0.72 else (F_ORG if d < 1.18 else F_RED))
        put(g, x, y, c)
    for p in outline_of(m):
        put(g, p[0], p[1], F_EDGE)


def smoke(g, circles, faded=False):
    """rising puff after the flame: dust ramp, like elbow_impact's clouds"""
    ramp = (D_P, D_Q, D_S, D_T)
    d = puffs(circles, ramp, D_T if faded else D_E)
    if faded:
        d = {(x, y): c for (x, y), c in d.items() if not (c == D_T and (x + y) % 2 == 0)}
    paint(g, d)


def dust_ring(g, rx, ry, width, broken=False):
    ring = set()
    for y in range(FH):
        for x in range(FW):
            u, v = (x + 0.5 - GX) / rx, (y + 0.5 - GY) / ry
            dd = math.sqrt(u * u + v * v)
            inner = 1.0 - width / ry * (0.55 + 0.45 * abs(v) / max(dd, 1e-6))
            if inner <= dd <= 1.0:
                if broken:
                    ang = math.degrees(math.atan2(v, u)) % 360
                    if int(ang // 30) % 2 == 1:
                        continue
                ring.add((x, y))
    ring = mirror_set(ring)
    for (x, y) in ring:
        put(g, x, y, D_P if y + 0.5 < GY else D_Q)


def dust_puffs(g, rx, ry, scale=1.0, faded=False):
    base = [(GX - rx * 0.95, GY + 0.5, 3.0 * scale), (GX - rx * 0.78, GY + ry * 0.55, 2.6 * scale),
            (GX - rx * 0.62, GY - ry * 0.65, 2.1 * scale)]
    circles = base + mirror_circles(base)
    ramp = ('pqst' if not faded else 'pqqs')
    cols = {'p': D_P, 'q': D_Q, 's': D_S, 't': D_T}
    d = puffs(circles, tuple(cols[c] for c in ramp), D_T if faded else D_E)
    paint(g, d)


def splat(g, s=1.0):
    """ketchup splat on the floor at the impact point: an irregular flat puddle with short
    splash rays and a few loose droplets; one small glint (no lip-like edge shading)"""
    cx, cy = GX, GY + 1.0
    blobs = [(-1.0, 0.0, 5.0, 2.3), (3.5, 0.6, 3.6, 1.9), (-5.2, 0.9, 2.4, 1.5), (1.0, -1.0, 3.0, 1.6)]
    m = set()
    for (dx, dy, rx, ry) in blobs:
        for y in range(int(cy + dy - ry) - 1, int(cy + dy + ry) + 2):
            for x in range(int(cx + dx - rx) - 1, int(cx + dx + rx) + 2):
                if ((x + 0.5 - cx - dx) / rx) ** 2 + ((y + 0.5 - cy - dy) / ry) ** 2 <= 1.0:
                    m.add((x, y))
    rays = set()
    for (ang, length) in ((-160, 4.5), (-35, 3.5), (15, 5.0), (160, 3.0), (-95, 2.5)):
        a = math.radians(ang)
        for k in range(int(length * 2) + 1):
            t = k / 2.0
            x = cx + math.cos(a) * (5.0 + t)
            y = cy + math.sin(a) * (2.2 + t * 0.45)
            rays.add((int(math.floor(x)), int(math.floor(y))))
    drops = [(-12.0, -1.0), (11.0, 2.0), (8.0, -2.5), (-9.5, 3.0)]
    dm = {(int(math.floor(cx + dx)), int(math.floor(cy + dy))) for (dx, dy) in drops}
    for p in outline_of(m | dm):          # outline the puddle and droplets only
        if get(g, *p) in (T, D_P, D_Q) and p not in rays:
            put(g, p[0], p[1], K)
    for (x, y) in m | dm | rays:          # rays are bare streaks of sauce
        put(g, x, y, SC)
    for (x, y) in ((int(cx) - 3, int(cy) - 1), (int(cx) - 2, int(cy) - 1), (int(cx) - 4, int(cy))):
        if (x, y) in m:
            put(g, x, y, SC_HI)
    put(g, int(cx) - 3, int(cy) - 1, WHITE)


CRUMB_SPR = {
    'L': [".hb.", "hbbm", "bbm."],
    'M': ["hb.", "bbm"],
    'S': ["hb", "b."],
}


def crumb(g, x, y, key, flip=False):
    spr = CRUMB_SPR[key]
    pts = {}
    for j, row in enumerate(spr):
        row = row[::-1] if flip else row
        for i, ch in enumerate(row):
            if ch != '.':
                pts[(x + i, y + j)] = {'h': N_HI, 'b': N_BASE, 'm': NM_WARM}[ch]
    for p in outline_of(set(pts)):
        if get(g, *p) in (T, D_P, D_Q, D_S, D_T, SMK, SMK_HI, SMK_SH):
            put(g, p[0], p[1], K)
    for (px_, py_), c in pts.items():
        put(g, px_, py_, c)


# (angle on the ground ellipse, size, speed factor)
CRUMBS = [(-165, 'L', 1.00), (-15, 'L', 1.00), (-125, 'M', 0.85), (-55, 'M', 0.85),
          (150, 'M', 1.05), (30, 'M', 1.05), (110, 'S', 0.75), (70, 'S', 0.75), (-90, 'S', 0.55)]
FLIGHT = [(6.0, 4.0), (13.5, 10.0), (19.5, 12.5), (24.0, 6.5), (26.5, 0.0)]   # (distance, height)


def paint_crumbs(g, f):
    r0, h0 = FLIGHT[f]
    for (a, key, k) in CRUMBS:
        ar = math.radians(a)
        x = GX + math.cos(ar) * r0 * k
        y = GY + math.sin(ar) * r0 * k * PERSP - h0 * (0.75 + 0.25 * k)
        w = len(CRUMB_SPR[key][0]); h = len(CRUMB_SPR[key])
        crumb(g, int(round(x - w / 2.0)), int(round(y - h / 2.0)), key, flip=math.cos(ar) > 0)


def impact_frame(f):
    g = canvas(FW, FH)
    if f == 0:
        dust_ring(g, 10.0, 4.2, 1.3)
        flash(g, [(0, 19), (180, 19), (-26, 14), (-154, 14), (-58, 15), (-122, 15), (-90, 17),
                  (26, 10), (154, 10), (90, 6)], 7.8, 4.6, cy_off=-2.0)
        paint_crumbs(g, 0)
    elif f == 1:
        dust_ring(g, 17.5, 7.4, 1.6)
        dust_puffs(g, 17.5, 7.4, 1.0)
        splat(g, 0.85)
        fireball(g, GX, GY - 7.5, 7.2)
        paint_crumbs(g, 1)
    elif f == 2:
        dust_ring(g, 23.5, 9.8, 1.3)
        dust_puffs(g, 23.5, 9.8, 1.05)
        splat(g, 1.0)
        fireball(g, GX, GY - 11.5, 6.0, cool=True)
        paint_crumbs(g, 2)
    elif f == 3:
        dust_ring(g, 27.0, 11.4, 1.0, broken=True)
        dust_puffs(g, 27.0, 11.4, 0.8, faded=True)
        splat(g, 1.0)
        smoke(g, [(GX, GY - 13.5, 4.4), (GX - 4.6, GY - 11.0, 3.3), (GX + 4.7, GY - 11.5, 3.1), (GX - 1.0, GY - 18.0, 2.9)])
        paint_crumbs(g, 3)
    else:
        splat(g, 1.0)
        smoke(g, [(GX - 1.8, GY - 18.5, 2.6), (GX + 2.2, GY - 20.0, 2.2)], faded=True)
        paint_crumbs(g, 4)
    return g


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'nugget_impact_wip.png'
    frames = [impact_frame(f) for f in range(5)]
    sheet = strip(frames)
    check_alpha(sheet, 'impact')
    edge_touch(sheet, FW, FH, 'impact')
    save(out, sheet)
    print('wrote', out, len(sheet[0]), len(sheet), 'colours', len(colours(sheet)))
