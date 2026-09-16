"""Deliverable 2 (elbow_target, 2x48x48) and 3 (elbow_impact, 4x64x64) effects."""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pngio import write_png

C = {
    '.': (0, 0, 0, 0),
    'K': (0, 0, 0, 255),
    # warning reds
    'R': (0xe0, 0x28, 0x2a, 255),   # rim base
    'r': (0x9c, 0x14, 0x14, 255),   # rim dark
    'Q': (0xff, 0x6b, 0x4a, 255),   # rim light
    'Y': (0xff, 0xd2, 0x4a, 255),   # hot yellow (pulse / flash)
    'W': (0xff, 0xff, 0xff, 255),
    'H': (0xff, 0x2a, 0x1a, 90),    # red halo (pulse)
    'O': (0xff, 0x45, 0x2a, 255),   # bright red-orange (pulse rim)
    # shadow (semi-transparent)
    '1': (0, 0, 0, 80),
    '2': (0, 0, 0, 120),
    '3': (0, 0, 0, 160),
    # flash
    'F': (0xff, 0x9c, 0x2a, 255),   # orange
    'f': (0xb8, 0x4a, 0x12, 255),   # dark orange edge
    # dust ramp (warm beige-grey)
    'a': (0xf4, 0xea, 0xd0, 255),
    'b': (0xda, 0xc8, 0xa0, 255),
    'c': (0xb2, 0x9c, 0x76, 255),
    'd': (0x86, 0x72, 0x58, 255),
    # faded dust (settling)
    'A': (0xf4, 0xea, 0xd0, 170),
    'B': (0xda, 0xc8, 0xa0, 150),
    'C': (0xb2, 0x9c, 0x76, 130),
    'D': (0x4a, 0x3a, 0x2a, 110),
    # light dust ramp + warm dark outline (effects precedent: rocket explosion uses dark red-brown edges)
    'p': (0xfb, 0xf6, 0xe8, 255),
    'q': (0xe6, 0xdc, 0xc2, 255),
    's': (0xc4, 0xb4, 0x94, 255),
    't': (0x97, 0x87, 0x69, 255),
    'e': (0x5a, 0x4a, 0x3a, 255),
    'm': (0x6e, 0x1e, 0x0a, 255),   # flash edge (dark red-brown)
    'P': (0xfb, 0xf6, 0xe8, 150),
    'S': (0xc4, 0xb4, 0x94, 150),
    # debris
    'g': (0x8a, 0x7a, 0x64, 255),
    'G': (0x5a, 0x4a, 0x3a, 255),
    # shockwave
    'w': (0xd8, 0xe8, 0xe8, 255),
    'v': (0xd8, 0xe8, 0xe8, 150),
}


def canvas(w, h):
    return [['.'] * w for _ in range(h)]


def in_ell(x, y, cx, cy, rx, ry):
    dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
    return dx * dx + dy * dy <= 1.0


def fill_ell(g, cx, cy, rx, ry, ch, only=None):
    for y in range(len(g)):
        for x in range(len(g[0])):
            if in_ell(x, y, cx, cy, rx, ry) and (only is None or g[y][x] in only):
                g[y][x] = ch


def ring(g, cx, cy, rx, ry, wx, wy, ch):
    """ring between outer (rx,ry) and inner (rx-wx, ry-wy)"""
    for y in range(len(g)):
        for x in range(len(g[0])):
            if in_ell(x, y, cx, cy, rx, ry) and not in_ell(x, y, cx, cy, rx - wx, ry - wy):
                g[y][x] = ch


def outline_mask(g, mask_chars, ch='K', diag=False):
    H, W = len(g), len(g[0])
    adds = []
    nb = ((1, 0), (-1, 0), (0, 1), (0, -1))
    if diag:
        nb = nb + ((1, 1), (1, -1), (-1, 1), (-1, -1))
    for y in range(H):
        for x in range(W):
            if g[y][x] != '.':
                continue
            for dx, dy in nb:
                xx, yy = x + dx, y + dy
                if 0 <= xx < W and 0 <= yy < H and g[yy][xx] in mask_chars:
                    adds.append((x, y))
                    break
    for x, y in adds:
        g[y][x] = ch


def symmetric_check(g, name):
    W = len(g[0])
    bad = sum(1 for y in range(len(g)) for x in range(W) if g[y][x] != g[y][W - 1 - x])
    print(name, 'horizontal asymmetric px:', bad)


# =====================================================================  TARGET MARKER
def target(pulse):
    W = H = 48
    cx, cy = 24.0, 24.0
    g = canvas(W, H)
    grow = 1.0 if pulse else 0.0
    rx, ry = 21.0 + grow, 10.5 + grow * 0.5
    # shadow interior (darker when pulsing)
    fill_ell(g, cx, cy, rx - 2.0, ry - 1.0, '3' if pulse else '2')
    ring(g, cx, cy, rx - 2.0, ry - 1.0, 1.2, 0.6, '2' if pulse else '1')
    # rim: thick at sides, thin top/bottom (ground perspective)
    ring(g, cx, cy, rx, ry, 2.6, 1.3, 'O' if pulse else 'R')
    for y in range(H):
        for x in range(W):
            if g[y][x] in 'RO':
                if y + 0.5 < cy - ry * 0.45:
                    g[y][x] = 'Y' if pulse else 'Q'
                elif y + 0.5 > cy + ry * 0.55:
                    g[y][x] = 'R' if pulse else 'r'
    # bullseye ring + centre pip
    ring(g, cx, cy, 8.0 + grow, 4.0 + grow * 0.2, 1.6, 0.9, 'O' if pulse else 'R')
    for x, y in ((23, 23), (24, 23), (23, 24), (24, 24)):
        g[y][x] = 'Y' if pulse else 'Q'
    # crosshair ticks pointing inward from the rim
    tick = 'O' if pulse else 'R'
    L = 5 if pulse else 4
    xl = int(round(cx - rx)) + 1
    for i in range(L):
        for y in (23, 24):
            g[y][xl + 2 + i] = tick
            g[y][W - 1 - (xl + 2 + i)] = tick
    yt = int(round(cy - ry)) + 1
    for i in range(3 if pulse else 2):
        for x in (23, 24):
            g[yt + 1 + i][x] = tick
            g[H - 1 - (yt + 1 + i)][x] = tick
    # single pure-black outline around the marker
    outline_mask(g, 'RrQYO', 'K')
    return g


def write_strip(path, frames):
    fw, fh = len(frames[0][0]), len(frames[0])
    img = [[(0, 0, 0, 0)] * (fw * len(frames)) for _ in range(fh)]
    for i, fr in enumerate(frames):
        for y in range(fh):
            for x in range(fw):
                img[y][i * fw + x] = C[fr[y][x]]
    write_png(path, fw * len(frames), fh, img)


# =====================================================================  IMPACT EFFECT
LIGHT = (-0.5, -0.8, 0.65)
_n = math.sqrt(sum(v * v for v in LIGHT))
LIGHT = tuple(v / _n for v in LIGHT)


def layer_onto(base, top):
    for y in range(len(base)):
        for x in range(len(base[0])):
            if top[y][x] != '.':
                base[y][x] = top[y][x]


def puff_group(W, H, circles, ramp='abcd', outline='K', bias=0.0):
    """union of shaded circles -> own layer with its own outline"""
    g = canvas(W, H)
    for y in range(H):
        for x in range(W):
            best = None
            for cx, cy, r in circles:
                dx, dy = x + 0.5 - cx, y + 0.5 - cy
                d2 = dx * dx + dy * dy
                if d2 <= r * r:
                    nz = math.sqrt(1 - d2 / (r * r))
                    h = nz * r - cy * 0.02   # higher & lower-on-screen circles win
                    if best is None or h > best[0]:
                        best = (h, dx / r, dy / r, nz)
            if best:
                _, nx, ny, nz = best
                I = nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2] + bias
                g[y][x] = ramp[0] if I > 0.80 else ramp[1] if I > 0.38 else ramp[2] if I > 0.0 else ramp[3]
    if outline:
        outline_mask(g, ramp, outline)
    return g


def star(cx, cy, spikes, inner_rx, inner_ry, rot=0.0):
    """spikes: list of (angle_deg, length). returns polygon alternating spike tips and inner valleys"""
    pts = []
    spikes = sorted(spikes)
    n = len(spikes)
    for i, (a, L) in enumerate(spikes):
        ar = math.radians(a + rot)
        pts.append((cx + math.cos(ar) * L, cy + math.sin(ar) * L))
        a2 = spikes[(i + 1) % n][0]
        if a2 <= a:
            a2 += 360
        am = math.radians((a + a2) / 2 + rot)
        pts.append((cx + math.cos(am) * inner_rx, cy + math.sin(am) * inner_ry))
    return pts


def pip(x, y, pts):
    inside = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi):
            inside = not inside
        j = i
    return inside


def fill_poly(g, pts, ch):
    for y in range(len(g)):
        for x in range(len(g[0])):
            if pip(x + 0.5, y + 0.5, pts):
                g[y][x] = ch


def scale_pts(pts, cx, cy, s):
    return [(cx + (x - cx) * s, cy + (y - cy) * s) for x, y in pts]


ROCK_BIG = [" KKK ", "KqggK", "KgGGK", " KKK "]
ROCK_MED = [" KK ", "KqgK", "KgGK", " KK "]
ROCK_SML = ["KK ", "KgK", " K "]


def put(g, x, y, spr):
    for j, row in enumerate(spr):
        for i, ch in enumerate(row):
            if ch != ' ' and 0 <= y + j < len(g) and 0 <= x + i < len(g[0]):
                g[y + j][x + i] = ch


def mirror_x(W, x, spr_w):
    return W - x - spr_w


GCX, GCY = 32.0, 32.0   # ground impact centre = exact frame centre (same anchor as the target marker)


def dither_edges(g, chars, keep_parity=0):
    """remove checkerboard pixels on the outer 1px of a shape -> dissipating look"""
    H, W = len(g), len(g[0])
    rm = []
    for y in range(H):
        for x in range(W):
            if g[y][x] in chars and (x + y) % 2 == keep_parity:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if not (0 <= xx < W and 0 <= yy < H) or g[yy][xx] == '.':
                        rm.append((x, y))
                        break
    for x, y in rm:
        g[y][x] = '.'


def cloud(W, H, cx, cy, r, n=5, seed=0, squash=0.8):
    """cauliflower cluster of circles around (cx,cy)"""
    import random
    rnd = random.Random(seed)
    circles = [(cx, cy, r)]
    for i in range(n):
        a = math.pi * (1.0 + i / max(1, n - 1))   # spread across the upper half
        d = r * rnd.uniform(0.55, 0.85)
        circles.append((cx + math.cos(a) * d * 1.15, cy + math.sin(a) * d * squash, r * rnd.uniform(0.55, 0.75)))
    return circles


def mirror_circles(circles):
    return [(64.0 - cx, cy, r) for cx, cy, r in circles]


def dust(g, circles, outline='e', ramp='pqst'):
    layer_onto(g, puff_group(64, 64, circles, ramp=ramp, outline=outline))


def cracks(g):
    for pts in (((30, 34), (27, 35), (24, 35), (21, 36), (18, 36)),
                ((27, 35), (25, 37), (23, 38)),
                ((33, 34), (36, 35), (39, 35), (42, 36), (45, 36)),
                ((36, 35), (38, 37), (40, 38))):
        for x, y in pts:
            g[y][x] = 'e'


def soften_edges(g, mapping):
    """outermost pixels of dust -> semi-transparent versions"""
    H, W = len(g), len(g[0])
    ch = []
    for y in range(H):
        for x in range(W):
            if g[y][x] in mapping:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if not (0 <= xx < W and 0 <= yy < H) or g[yy][xx] == '.':
                        ch.append((x, y))
                        break
    for x, y in ch:
        g[y][x] = mapping[g[y][x]]


def band(*clouds):
    out = []
    for c in clouds:
        out += c
    return out


def impact(frame):
    W = H = 64
    g = canvas(W, H)
    if frame == 0:
        cracks(g)
        ring(g, GCX, GCY, 21.0, 8.0, 2.4, 1.2, 'W')
        spikes = [(0, 28), (180, 28), (-24, 18), (-156, 18), (-56, 21), (-124, 21), (-90, 26),
                  (24, 11), (156, 11), (90, 7)]
        c0 = (GCX, GCY - 1.5)
        outer = star(c0[0], c0[1], spikes, 9.5, 6.0)
        fill_poly(g, outer, 'F')
        fill_poly(g, scale_pts(outer, c0[0], c0[1], 0.66), 'Y')
        fill_poly(g, scale_pts(outer, c0[0], c0[1], 0.36), 'W')
        outline_mask(g, 'FYW', 'm')
        for x, y in ((9, 17), (53, 17), (17, 8), (45, 8)):
            for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
                g[y + dy][x + dx] = 'Y'
            g[y][x] = 'W'
    elif frame == 1:
        ring(g, GCX, GCY, 26.0, 10.2, 2.4, 1.2, 'W')
        B = cloud(W, H, GCX - 11, GCY - 7, 3.4, n=3, seed=1)
        dust(g, band(B, mirror_circles(B)))
        fill_ell(g, GCX, GCY - 1.5, 7.0, 3.6, 'F')
        fill_ell(g, GCX, GCY - 1.5, 5.0, 2.6, 'Y')
        fill_ell(g, GCX, GCY - 1.5, 2.6, 1.4, 'W')
        S = cloud(W, H, GCX - 19, GCY - 1, 4.4, n=4, seed=2)
        F = cloud(W, H, GCX - 9, GCY + 6, 4.6, n=4, seed=3)
        dust(g, band(S, mirror_circles(S)))
        dust(g, band(F, mirror_circles(F)))
        put(g, 12, 14, ROCK_BIG)
        put(g, 47, 12, ROCK_BIG)
        put(g, 22, 7, ROCK_MED)
        put(g, 38, 8, ROCK_MED)
        put(g, 5, 23, ROCK_SML)
        put(g, 56, 25, ROCK_SML)
    elif frame == 2:
        ring(g, GCX, GCY, 29.5, 12.0, 1.4, 0.8, 'w')
        B = cloud(W, H, GCX - 12, GCY - 10, 4.0, n=4, seed=4)
        dust(g, band(B, mirror_circles(B)))
        S = cloud(W, H, GCX - 21, GCY - 3, 5.0, n=5, seed=6)
        F = cloud(W, H, GCX - 11, GCY + 7, 5.4, n=5, seed=7)
        dust(g, band(S, mirror_circles(S), F, mirror_circles(F)))
        put(g, 7, 9, ROCK_BIG)
        put(g, 52, 8, ROCK_BIG)
        put(g, 19, 2, ROCK_MED)
        put(g, 41, 2, ROCK_MED)
        put(g, 2, 21, ROCK_SML)
        put(g, 59, 22, ROCK_SML)
    elif frame == 3:
        tmp = canvas(W, H)
        S = cloud(W, H, GCX - 21, GCY + 2, 4.4, n=4, seed=9)
        F = cloud(W, H, GCX - 9, GCY + 9, 4.0, n=3, seed=10)
        B = cloud(W, H, GCX - 12, GCY - 6, 3.0, n=3, seed=11)
        dust(tmp, band(S, mirror_circles(S), F, mirror_circles(F), B, mirror_circles(B)), outline=None, ramp='pqqs')
        soften_edges(tmp, {'p': 'P', 'q': 'P', 's': 'S'})
        layer_onto(g, tmp)
        for x, y, spr in ((6, 37, ROCK_SML), (55, 38, ROCK_SML), (15, 45, ROCK_MED), (45, 46, ROCK_MED), (30, 47, ROCK_SML)):
            put(g, x, y, spr)
    return g


if __name__ == '__main__':
    t = [target(0), target(1)]
    for i, fr in enumerate(t):
        symmetric_check(fr, 'target%d' % i)
    write_strip(os.path.join(HERE, 'elbow_target_wip.png'), t)
    imp = [impact(i) for i in range(4)]
    for i, fr in enumerate(imp):
        edge = [(x, y) for y in range(64) for x in range(64) if fr[y][x] != '.' and (x in (0, 63) or y in (0, 63))]
        if edge:
            print('WARN impact frame', i, 'touches frame edge at', edge[:6])
    write_strip(os.path.join(HERE, 'elbow_impact_wip.png'), imp)
    print('ok')
