"""Mech ground-pound effects: impact burst (6x128x64) and shockwave segment (4x24x24)."""
import math
from fxlib import *
from pngio import write_png, scale

IW, IH = 128, 64
CX, CY = 64.0, 63.5          # impact centre = bottom-middle
FLOOR = (136, 180, 99, 255)  # arena floor green for previews

# ------------------------------------------------------------------ impact pieces

CRACKS = [
    [(64, 62), (57, 60), (51, 61), (45, 58), (38, 58), (32, 55), (24, 56), (16, 53)],
    [(45, 58), (41, 55), (37, 53)],
    [(32, 55), (28, 58), (22, 60)],
    [(64, 62), (71, 59), (77, 60), (84, 57), (91, 58), (98, 55), (106, 56), (113, 53)],
    [(77, 60), (81, 62)],
    [(91, 58), (95, 54), (99, 51)],
    [(64, 62), (61, 57), (65, 53), (62, 49)],
    [(64, 62), (57, 55), (51, 52)],
    [(64, 62), (71, 55), (77, 51)],
]

def poly_len(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))

def crack_pixels(pts, frac):
    """pixels along the polyline up to `frac` of its length, with distance-from-start."""
    total = poly_len(pts) * frac
    out = []
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        n = int(seg) + 1
        for i in range(n + 1):
            d = acc + seg * i / n
            if d > total:
                return out
            x = int(round(a[0] + (b[0] - a[0]) * i / n))
            y = int(round(a[1] + (b[1] - a[1]) * i / n))
            out.append((x, y, d))
        acc += seg
    return out

def draw_cracks(cv, t):
    frac = [0.35, 0.8, 1, 1, 1, 0.55][t]
    for ci, pts in enumerate(CRACKS):
        f = frac if ci in (0, 3, 6, 7, 8) else max(0.0, (frac - 0.6) / 0.4)
        if f <= 0:
            continue
        px = crack_pixels(pts, f)
        for x, y, d in px:
            if t == 5:
                cv.put(x, y, PALC['f'])
                continue
            main = ci in (0, 3)
            # lip below the crack (depth)
            if main and d < 30:
                cv.put(x, y + 1, PALC['g'] if t < 4 else PALC['f'])
            if t <= 2 and d < 22 and ci in (0, 3, 6):
                cv.put(x, y, PALC['R'] if (t < 2 or d < 12) else PALC['X'])
                cv.put(x, y - 1, BLACK)
            else:
                cv.put(x, y, BLACK)

def draw_crater(cv, t):
    rx = [9, 14, 15, 15, 14, 11][t]
    ry = [3.5, 5, 5.5, 5.5, 5, 4][t]
    m = ell_mask(IW, IH, CX, CY + 0.5, rx, ry)
    lip = ell_mask(IW, IH, CX, CY + 0.5, rx + 3, ry + 2)
    rim = sub(lip, m)
    # rim of broken-up soil, then the dark hole
    render(cv, union(rim, m), SOIL[:2] + [PALC['g']], R=2, th=[0.9, 0.6])
    for y in range(IH):
        for x in range(IW):
            if m[y][x]:
                inner = ((x + 0.5 - CX) / (rx - 1.5)) ** 2 + ((y + 1 - CY) / max(ry - 1.5, 1)) ** 2 <= 1
                cv.px[y][x] = PALC['V'] if (inner and t <= 1) else PALC['g']
    for x in range(IW):
        for y in range(IH):
            if m[y][x] and (y == 0 or not m[y - 1][x]):
                cv.px[y][x] = BLACK

def ground_ring(cv, t):
    spec = {0: (30, 7, 'WPr'), 1: (46, 10, 'Pr'), 2: (58, 12, 'rR')}
    if t not in spec:
        return
    rx, ry, cols = spec[t]
    for y in range(IH):
        for x in range(IW):
            d = math.sqrt(((x + 0.5 - CX) / rx) ** 2 + ((y + 0.5 - CY) / ry) ** 2)
            band = (1.0 - d) * min(rx, ry * 3) / 3.0
            if 0 <= band < len(cols):
                if t == 2 and (x // 3 + y) % 2:
                    continue
                cv.put(x, y, PALC[cols[len(cols) - 1 - int(band)]])

def flash(cv, t):
    if t == 0:
        # upward starburst dome at the slam point
        nsp = 11
        for y in range(IH):
            for x in range(IW):
                dx, dy = x + 0.5 - CX, (y + 0.5 - CY) * 1.25
                if dy > 0.5:
                    continue
                r = math.hypot(dx, dy)
                a = math.atan2(-dy, dx)
                u = (a * nsp / math.pi) % 1.0
                tri = 1 - abs(u - 0.5) * 2
                R = 17 + 26 * (tri ** 2.4) * (1.0 if int(a * nsp / math.pi) % 2 == 0 else 0.65)
                if r <= R:
                    c = 'W' if r < 12 else ('P' if r < 16 else ('r' if r < R - 3 else 'R'))
                    cv.put(x, y, PALC[c])
    elif t == 1:
        for y in range(IH):
            for x in range(IW):
                d = math.hypot(x + 0.5 - CX, (y + 0.5 - CY) * 1.4)
                if d < 5:
                    cv.put(x, y, PALC['W'])
                elif d < 8:
                    cv.put(x, y, PALC['P'])
                elif d < 10 and (x + y) % 2 == 0:
                    cv.put(x, y, PALC['r'])

# dust puffs per frame: (cx, cy, r)
PUFFS = {
    1: [(64, 51, 9), (57, 43, 7), (71, 44, 7), (64, 37, 6), (47, 57, 6), (82, 57, 6), (37, 59.5, 4.5), (92, 59.5, 4.5)],
    2: [(64, 48, 11), (54, 39, 9), (74, 38, 9), (64, 31, 9), (64, 21, 8), (55, 22, 6.5), (73, 23, 6), (42, 55, 8), (87, 55, 8),
        (29, 58, 6.5), (100, 58, 6.5), (18, 60, 4.5), (110, 60, 4.5)],
    3: [(64, 49, 10), (51, 43, 8.5), (77, 42, 8.5), (60, 33, 9), (69, 31, 9), (64, 22, 9), (54, 19, 7), (75, 18, 7),
        (64, 13, 6), (37, 54, 9), (91, 54, 9), (23, 57, 7.5), (105, 57, 7.5), (11, 60, 5), (117, 60, 5)],
    4: [(50, 36, 8), (78, 35, 8), (59, 19, 7.5), (71, 15, 6.5), (65, 46, 6.5), (64, 27, 5), (33, 53, 8.5), (95, 53, 8.5),
        (19, 56, 6.5), (109, 56, 6.5), (8, 59, 4), (120, 59, 4), (44, 48, 5), (84, 48, 5)],
    5: [(47, 28, 3.5), (81, 27, 3.5), (61, 10, 3.5), (72, 8, 2.5), (29, 50, 4.5), (99, 49, 4.5),
        (13, 54, 3.5), (115, 54, 3.5), (56, 40, 2.5), (87, 41, 2.5)],
}

def dust(cv, t):
    if t == 0:
        return
    m = union(*[ell_mask(IW, IH, x, y, r * 1.1, r * 0.88) for x, y, r in PUFFS[t]])
    if t <= 3:
        ramp, th, R, oc = DUST, TH5, 5, BLACK
    elif t == 4:
        ramp, th, R, oc = [DUST[0], DUST[0], DUST[1], DUST[2], DUST[3]], TH5, 4, BLACK
    else:
        ramp, th, R, oc = [DUST[0], DUST[1], DUST[2], DUST[2]], TH4, 2, PALC['4']
    render(cv, m, ramp, R=R, th=th, outline_col=oc)
    if t <= 4:
        billows(cv, [(x, y, r * 1.1, r * 0.88) for x, y, r in PUFFS[t]], m, PALC['4'] if t <= 3 else PALC['3'])

def billows(cv, puffs, union_mask, col):
    """draw the upper edge of each nearer (lower) puff where it overlaps a puff behind it"""
    order = sorted(range(len(puffs)), key=lambda i: puffs[i][1])
    masks = {i: ell_mask(cv.w, cv.h, *puffs[i]) for i in order}
    for rank, i in enumerate(order):
        behind = [masks[j] for j in order[:rank]]
        if not behind:
            continue
        mi = masks[i]
        for y in range(cv.h):
            for x in range(cv.w):
                if not mi[y][x] or cv.px[y][x] == BLACK:
                    continue
                cx, cy = puffs[i][0], puffs[i][1]
                if y + 0.5 > cy:
                    continue
                edge = False
                for dx, dy in ((0, -1), (-1, 0), (1, 0)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < cv.w and 0 <= yy < cv.h and not mi[yy][xx] and union_mask[yy][xx]                             and any(b[yy][xx] for b in behind):
                        edge = True
                        break
                if edge:
                    cv.px[y][x] = col

# rubble: (vx, vy, variant, spin)
ROCKS = [(-12, 19, 2, 0), (-8, 24, 1, 1), (-4, 16, 0, 0), (-2, 27, 1, 1), (3, 22, 2, 1), (6, 15, 0, 0),
         (9, 25, 1, 1), (12, 18, 0, 0), (-15, 12, 0, 1), (15, 13, 1, 0)]
ROCK_ART = [
    """
.kk.
kabk
kbck
.kk.
""",
    """
.kkk.
kaabk
kbcdk
.kkk.
""",
    """
..kkk.
.kabbk
kabbck
kbccdk
.kkkk.
""",
]

def flipv(art):
    rows = art.strip('\n').split('\n')
    return '\n'.join(reversed(rows))

def fliph(art):
    rows = art.strip('\n').split('\n')
    return '\n'.join(r[::-1] for r in rows)

def rubble(cv, t):
    g = 9.0
    for i, (vx, vy, var, spin) in enumerate(ROCKS):
        T = t + 0.55
        x = CX + vx * T
        y = CY - 3 - (vy * T - 0.5 * g * T * T)
        landed = y > CY - 3
        if landed:
            if t >= 5 and i % 3:
                continue
            tl = 2 * vy / g
            x = CX + vx * tl
            y = CY - 3 + (i % 3)
        art = ROCK_ART[var]
        if not landed and (t + spin) % 2:
            art = flipv(fliph(art))
        rows = art.strip('\n').split('\n')
        x0 = int(round(x - len(rows[0]) / 2))
        y0 = int(round(y - len(rows) / 2))
        if t == 0:
            if i % 3:
                continue
            x0 = int(round(CX + vx * 1.2 - 2))
            y0 = int(round(CY - 14 - vy * 0.3))
        cv.stamp(art, x0, y0)

def sparks(cv, t):
    if t not in (1, 2, 3):
        return
    for i, a in enumerate(range(15, 180, 22)):
        d = [0, 26, 40, 50][t] + (i % 3) * 3
        x = CX + d * math.cos(math.radians(a)) * 1.2
        y = CY - 4 - d * math.sin(math.radians(a)) * 0.8
        ux, uy = math.cos(math.radians(a)) * 1.2, -math.sin(math.radians(a)) * 0.8
        n = [0, 4, 3, 1][t]
        for s in range(n):
            c = 'W' if s == 0 else ('P' if s == 1 else 'r')
            cv.put(int(round(x - ux * s)), int(round(y - uy * s)), PALC[c] if t < 3 else PALC['r'])
        if t == 3 and i % 2:
            cv.put(int(round(x)), int(round(y)), PALC['R'])

def impact_frame(t):
    cv = Canvas(IW, IH)
    draw_cracks(cv, t)
    draw_crater(cv, t)
    ground_ring(cv, t)
    dust(cv, t)
    flash(cv, t)
    rubble(cv, t)
    sparks(cv, t)
    return cv

# ------------------------------------------------------------------ shockwave segment

SW, SH = 24, 24

SEG_ROCK = """
.kk.
kabk
kbck
.kk.
"""
SEG_PEBBLE = """
kk
kc
"""

def seg_frame(t):
    """One flame-dome of the travelling shockwave. Rounded, fully outlined, so a chain of
    them overlapping at any spacing reads as one scalloped rolling crest."""
    cv = Canvas(SW, SH)
    cxm = 12.0
    licks = [[(6.5, 2.0), (12, 3.0), (17.5, 1.5)], [(7, 3.0), (12.5, 1.5), (17, 2.5)],
             [(6.5, 1.5), (11.5, 2.5), (17.5, 3.0)], [(7.5, 2.5), (12, 2.0), (16.5, 1.5)]][t]
    def ytop(x):
        u = abs(x + 0.5 - cxm) / 12.0
        y = 8.5 + 10.5 * u ** 2.6
        for lx, lh in licks:
            y -= lh * max(0.0, 1 - abs(x + 0.5 - lx) / 2.2)
        return y
    def ybot(x):
        u = (x + 0.5 - cxm) / 12.0
        return 19.5 + 2.5 * math.sqrt(max(0.0, 1 - u * u))
    m = empty_mask(SW, SH)
    for x in range(SW):
        for y in range(SH):
            if ytop(x) <= y + 0.5 <= ybot(x):
                m[y][x] = True
    # emissive colouring: white-hot at the foot, cooling to red at the rim
    for y in range(SH):
        for x in range(SW):
            if not m[y][x]:
                continue
            dx = (x + 0.5 - cxm) / 12.5
            dy = (y + 0.5 - 18.5) / (10.5 if y + 0.5 < 18.5 else 3.5)
            e = math.sqrt(dx * dx + dy * dy)
            fl = 0.06 * [0, 1, 0, -1][t] * math.cos(3 * x)
            e += fl
            c = 'W' if e < 0.42 else ('P' if e < 0.62 else ('r' if e < 0.82 else 'R'))
            cv.put(x, y, PALC[c])
    for y in range(SH):
        for x in range(SW):
            if m[y][x]:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if not (0 <= xx < SW and 0 <= yy < SH) or not m[yy][xx]:
                        cv.put(x, y, BLACK)
                        break
    # darker lower rim so it sits on the floor
    for x in range(SW):
        yb = None
        for y in range(SH - 1, -1, -1):
            if m[y][x]:
                yb = y
                break
        if yb is not None and yb - 1 >= 0 and cv.get(x, yb - 1) not in (None, BLACK):
            cv.put(x, yb - 1, PALC['X'] if abs(x + 0.5 - cxm) > 5 else PALC['R'])
    # hot streaks rising through the flame
    streak = [(9, 13, 17), (12, 15, 18), (10, 14, 17), (13, 16, 18)][t]
    cv.put(streak[0], streak[1], PALC['W'], only_empty=False)
    cv.put(streak[0], streak[1] + 1, PALC['W'])
    # rubble tossed over the crest, dark grit churned up inside the foot of the wave
    hop = [4, 1, 0, 2]
    ra = SEG_ROCK if t % 2 == 0 else flipv(fliph(SEG_ROCK))
    cv.stamp(ra, 4 + (t % 2), hop[t])
    rb = SEG_PEBBLE if t % 2 else fliph(SEG_PEBBLE)
    cv.stamp(rb, 17, hop[(t + 2) % 4] + 1)
    grit = [[(5, 19), (15, 20), (19, 18)], [(7, 20), (14, 19), (18, 19)],
            [(5, 18), (10, 20), (17, 20)], [(6, 20), (12, 19), (19, 19)]][t]
    for gx, gy in grit:
        if cv.get(gx, gy) not in (None, BLACK):
            cv.put(gx, gy, PALC['c'])
    SP = {0: [(11, 2, 'W'), (21, 9, 'r'), (9, 5, 'P')], 1: [(13, 1, 'W'), (21, 7, 'P'), (2, 9, 'r')],
          2: [(10, 1, 'P'), (20, 5, 'W'), (2, 10, 'r')], 3: [(14, 3, 'r'), (19, 2, 'W'), (1, 11, 'W')]}
    for x, y, c in SP[t]:
        cv.put(x, y, PALC[c], only_empty=True)
    return cv

# ------------------------------------------------------------------ output

def strip(frames, w, h):
    out = [[(0, 0, 0, 0)] * (w * len(frames)) for _ in range(h)]
    for i, cv in enumerate(frames):
        rg = cv.rgba()
        for y in range(h):
            for x in range(w):
                out[y][i * w + x] = rg[y][x]
    return out

if __name__ == '__main__':
    imp = [impact_frame(t) for t in range(6)]
    s = strip(imp, IW, IH)
    write_png('impact_strip.png', IW * 6, IH, s)
    write_png('impact_8x_a.png', IW * 3 * 6, IH * 6, scale([row[:IW * 3] for row in s], 6, FLOOR))
    write_png('impact_8x_b.png', IW * 3 * 6, IH * 6, scale([row[IW * 3:] for row in s], 6, FLOOR))
    seg = [seg_frame(t) for t in range(4)]
    s2 = strip(seg, SW, SH)
    write_png('segment_strip.png', SW * 4, SH, s2)
    write_png('segment_12x.png', SW * 4 * 12, SH * 12, scale(s2, 12, FLOOR))
    print('ok')
