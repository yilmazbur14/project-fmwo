"""elbow_target_v2.png (2 x 76x76) and elbow_impact_v2.png (4 x 104x104).

The same designs as art_source/carter_elbow/effects.py (elbow_target.png, elbow_impact.png),
redrawn natively at ~1.6x: every shape is re-rasterised from the original geometry with the
radii scaled, outlines stay 1px, rocks are redrawn as larger sprites. The target's rim is
sized so the new ~55 screen-px damage radius sits inside the rim band at 3x.

Alpha: the old marker's shadow used 80/120/160-alpha black and the old dust edges 150-alpha;
here those are the exact opaque colours they produced on the arena mat (136,180,99), and the
settling dust dissolves with dithering, so every pixel is alpha 0 or 255."""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pngio import write_png

MAT = (136, 180, 99)


def over_mat(a):
    k = a / 255.0
    return tuple(int(MAT[i] * (1 - k)) for i in range(3)) + (255,)


C = {
    '.': (0, 0, 0, 0),
    'K': (0, 0, 0, 255),
    'R': (0xe0, 0x28, 0x2a, 255), 'r': (0x9c, 0x14, 0x14, 255), 'Q': (0xff, 0x6b, 0x4a, 255),
    'Y': (0xff, 0xd2, 0x4a, 255), 'W': (0xff, 0xff, 0xff, 255), 'O': (0xff, 0x45, 0x2a, 255),
    '1': over_mat(80), '2': over_mat(120), '3': over_mat(160),
    'F': (0xff, 0x9c, 0x2a, 255), 'f': (0xb8, 0x4a, 0x12, 255), 'm': (0x6e, 0x1e, 0x0a, 255),
    'p': (0xfb, 0xf6, 0xe8, 255), 'q': (0xe6, 0xdc, 0xc2, 255), 's': (0xc4, 0xb4, 0x94, 255),
    't': (0x97, 0x87, 0x69, 255), 'e': (0x5a, 0x4a, 0x3a, 255),
    'g': (0x8a, 0x7a, 0x64, 255), 'G': (0x5a, 0x4a, 0x3a, 255),
    'w': (0xd8, 0xe8, 0xe8, 255),
    'b': (0xa8, 0xc8, 0xd0, 255),      # shockwave edge (a step darker than 'w', so the ring holds on the mat)
}


def canvas(w, h):
    return [['.'] * w for _ in range(h)]


def in_ell(x, y, cx, cy, rx, ry):
    dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
    return dx * dx + dy * dy <= 1.0


def fill_ell(g, cx, cy, rx, ry, ch):
    for y in range(len(g)):
        for x in range(len(g[0])):
            if in_ell(x, y, cx, cy, rx, ry):
                g[y][x] = ch


def ring(g, cx, cy, rx, ry, wx, wy, ch):
    for y in range(len(g)):
        for x in range(len(g[0])):
            if in_ell(x, y, cx, cy, rx, ry) and not in_ell(x, y, cx, cy, rx - wx, ry - wy):
                g[y][x] = ch


def outline_mask(g, mask_chars, ch='K'):
    H, W = len(g), len(g[0])
    adds = []
    for y in range(H):
        for x in range(W):
            if g[y][x] != '.':
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
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
    return bad


def write_strip(path, frames):
    fw, fh = len(frames[0][0]), len(frames[0])
    img = [[(0, 0, 0, 0)] * (fw * len(frames)) for _ in range(fh)]
    for i, fr in enumerate(frames):
        for y in range(fh):
            for x in range(fw):
                img[y][i * fw + x] = C[fr[y][x]]
    write_png(path, fw * len(frames), fh, img)


# =============================================================================  TARGET v2
TW = 76
TC = 38.0
T_RX, T_RY = 35.5, 19.5        # rim outer edge (old: 21 x 10.5)
S = 1.6                        # scale for the inner details


def target(pulse):
    g = canvas(TW, TW)
    cx = cy = TC
    grow = 1.0 if pulse else 0.0
    rx, ry = T_RX + grow * 0.5, T_RY + grow * 0.5
    # shadow interior (darker when pulsing)
    fill_ell(g, cx, cy, rx - 2.0 * S, ry - 1.0 * S, '3' if pulse else '2')
    ring(g, cx, cy, rx - 2.0 * S, ry - 1.0 * S, 1.2 * S, 0.6 * S, '2' if pulse else '1')
    # rim: thick at the sides, thin at top/bottom
    ring(g, cx, cy, rx, ry, 2.6 * S, 1.3 * S + 0.3, 'O' if pulse else 'R')
    for y in range(TW):
        for x in range(TW):
            if g[y][x] in 'RO':
                if y + 0.5 < cy - ry * 0.45:
                    g[y][x] = 'Y' if pulse else 'Q'
                elif y + 0.5 > cy + ry * 0.55:
                    g[y][x] = 'R' if pulse else 'r'
    # bullseye ring + centre pip
    ring(g, cx, cy, (8.0 + grow) * S, (4.0 + grow * 0.2) * S, 1.6 * S + 0.6, 0.9 * S + 0.7, 'O' if pulse else 'R')
    for (x, y) in ((37, 36), (38, 36), (36, 37), (37, 37), (38, 37), (39, 37),
                   (36, 38), (37, 38), (38, 38), (39, 38), (37, 39), (38, 39)):
        g[y][x] = 'Y' if pulse else 'Q'
    # crosshair ticks pointing inward from the rim
    tick = 'O' if pulse else 'R'
    L = 8 if pulse else 6
    xl = int(round(cx - rx)) + 1
    for i in range(L):
        for y in (36, 37, 38, 39):
            if y in (36, 39) and i == L - 1:
                continue                      # rounded tip
            g[y][xl + 3 + i] = tick
            g[y][TW - 1 - (xl + 3 + i)] = tick
    yt = int(round(cy - ry)) + 1
    for i in range(5 if pulse else 3):
        for x in (36, 37, 38, 39):
            if x in (36, 39) and i == (4 if pulse else 2):
                continue
            g[yt + 2 + i][x] = tick
            g[TW - 1 - (yt + 2 + i)][x] = tick
    outline_mask(g, 'RrQYO', 'K')
    return g


# =============================================================================  IMPACT v2
IW = 104
GCX = GCY = 52.0
LIGHT = (-0.5, -0.8, 0.65)
_n = math.sqrt(sum(v * v for v in LIGHT))
LIGHT = tuple(v / _n for v in LIGHT)


def layer_onto(base, top):
    for y in range(len(base)):
        for x in range(len(base[0])):
            if top[y][x] != '.':
                base[y][x] = top[y][x]


def puff_group(W, H, circles, ramp='abcd', outline='K'):
    g = canvas(W, H)
    for y in range(H):
        for x in range(W):
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
                g[y][x] = ramp[0] if I > 0.80 else ramp[1] if I > 0.38 else ramp[2] if I > 0.0 else ramp[3]
    if outline:
        outline_mask(g, ramp, outline)
    return g


def star(cx, cy, spikes, inner_rx, inner_ry):
    pts = []
    spikes = sorted(spikes)
    n = len(spikes)
    for i, (a, L) in enumerate(spikes):
        ar = math.radians(a)
        pts.append((cx + math.cos(ar) * L, cy + math.sin(ar) * L))
        a2 = spikes[(i + 1) % n][0]
        if a2 <= a:
            a2 += 360
        am = math.radians((a + a2) / 2)
        pts.append((cx + math.cos(am) * inner_rx, cy + math.sin(am) * inner_ry))
    return pts


def pip(x, y, pts):
    inside = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]; xj, yj = pts[j]
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


# rocks redrawn at the new size (old: 5x4 / 4x4 / 3x3)
ROCK_BIG = ["  KKK  ", " KqqgK ", "KqggggK", "KggGGGK", " KGGGK ", "  KKK  "]
ROCK_MED = [" KKK ", "KqqgK", "KggGK", " KGK ", "  K  "]
ROCK_SML = [" KK ", "KqgK", "KgGK", " KK "]


def put(g, x, y, spr):
    for j, row in enumerate(spr):
        for i, ch in enumerate(row):
            if ch != ' ' and 0 <= y + j < len(g) and 0 <= x + i < len(g[0]):
                g[y + j][x + i] = ch


def mirror_spr(spr):
    return [row[::-1] for row in spr]


def put_pair(g, x, y, spr):
    """sprite at (x, y) and its mirror image about the frame centre"""
    put(g, x, y, spr)
    put(g, IW - x - len(spr[0]), y, mirror_spr(spr))


def cloud(cx, cy, r, n=5, seed=0, squash=0.8):
    rnd = random.Random(seed)
    circles = [(cx, cy, r)]
    for i in range(n):
        a = math.pi * (1.0 + i / max(1, n - 1))
        d = r * rnd.uniform(0.55, 0.85)
        circles.append((cx + math.cos(a) * d * 1.15, cy + math.sin(a) * d * squash, r * rnd.uniform(0.55, 0.75)))
    return circles


def mirror_circles(circles):
    return [(IW - cx, cy, r) for cx, cy, r in circles]


def dust(g, circles, outline='e', ramp='pqst'):
    layer_onto(g, puff_group(IW, IW, circles, ramp=ramp, outline=outline))


def P(v):
    """scale an old offset from the 64px frame's centre"""
    return v * S


def shock(g, rx, ry, w_core, w_edge, core='W', edge='b'):
    """stronger shockwave: a bright core band with a darker blue-white band outside it
    (band widths: horizontal w, vertical w/2 - same proportions as the original rings)"""
    tw = w_core + w_edge
    ring(g, GCX, GCY, rx, ry, tw, tw * 0.5, edge)
    ring(g, GCX, GCY, rx - w_edge, ry - w_edge * 0.5, w_core, w_core * 0.5, core)


def cracks(g):
    def m(x, y):
        return (GCX + (x + 0.5 - 32) * S, GCY + (y + 0.5 - 32) * S)
    paths = [[m(30, 34), m(27, 35), m(24, 35), m(21, 36), m(18, 36)],
             [m(27, 35), m(25, 37), m(23, 38)]]
    for pts in paths:
        for a, b in zip(pts, pts[1:]):
            n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) + 1
            for k in range(n + 1):
                x = int(a[0] + (b[0] - a[0]) * k / n)
                y = int(a[1] + (b[1] - a[1]) * k / n)
                g[y][x] = 'e'
                g[y][IW - 1 - x] = 'e'


def impact(frame):
    W = H = IW
    g = canvas(W, H)
    if frame == 0:
        cracks(g)
        shock(g, P(21.0), P(8.0), 4.4, 1.8)
        spikes = [(0, P(28)), (180, P(28)), (-24, P(18)), (-156, P(18)), (-56, P(21)), (-124, P(21)), (-90, P(26)),
                  (24, P(11)), (156, P(11)), (90, P(7))]
        c0 = (GCX, GCY - P(1.5))
        outer = star(c0[0], c0[1], spikes, P(9.5), P(6.0))
        fill_poly(g, outer, 'F')
        fill_poly(g, scale_pts(outer, c0[0], c0[1], 0.66), 'Y')
        fill_poly(g, scale_pts(outer, c0[0], c0[1], 0.36), 'W')
        outline_mask(g, 'FYW', 'm')
        for x, y in ((15, 28), (28, 14)):
            for dx in range(3):
                for dy in range(3):
                    if (dx, dy) not in ((0, 0), (2, 0), (0, 2), (2, 2)):
                        g[y + dy][x + dx] = 'Y'
                        g[y + dy][IW - 1 - (x + dx)] = 'Y'
            g[y + 1][x + 1] = 'W'
            g[y + 1][IW - 1 - (x + 1)] = 'W'
    elif frame == 1:
        shock(g, P(26.0), P(10.2), 4.4, 2.0)
        B = cloud(GCX - P(11), GCY - P(7), P(3.4), n=3, seed=1)
        dust(g, B + mirror_circles(B))
        fill_ell(g, GCX, GCY - P(1.5), P(7.0), P(3.6), 'F')
        fill_ell(g, GCX, GCY - P(1.5), P(5.0), P(2.6), 'Y')
        fill_ell(g, GCX, GCY - P(1.5), P(2.6), P(1.4), 'W')
        Sd = cloud(GCX - P(19), GCY - P(1), P(4.4), n=4, seed=2)
        Fd = cloud(GCX - P(9), GCY + P(6), P(4.6), n=4, seed=3)
        dust(g, Sd + mirror_circles(Sd))
        dust(g, Fd + mirror_circles(Fd))
        put(g, 20, 23, ROCK_BIG); put(g, 76, 20, ROCK_BIG)
        put(g, 37, 13, ROCK_MED); put(g, 62, 14, ROCK_MED)
        put(g, 9, 38, ROCK_SML); put(g, 91, 41, ROCK_SML)
    elif frame == 2:
        shock(g, P(29.5), P(12.0), 3.2, 2.0, core='w', edge='b')
        B = cloud(GCX - P(12), GCY - P(10), P(4.0), n=4, seed=4)
        dust(g, B + mirror_circles(B))
        Sd = cloud(GCX - P(21), GCY - P(3), P(5.0), n=5, seed=6)
        Fd = cloud(GCX - P(11), GCY + P(7), P(5.4), n=5, seed=7)
        dust(g, Sd + mirror_circles(Sd) + Fd + mirror_circles(Fd))
        put(g, 12, 15, ROCK_BIG); put(g, 84, 14, ROCK_BIG)
        put(g, 32, 5, ROCK_MED); put(g, 67, 5, ROCK_MED)
        put(g, 4, 35, ROCK_SML); put(g, 96, 36, ROCK_SML)
    elif frame == 3:
        # the ring keeps travelling and breaks up
        tmpr = canvas(W, H)
        ring(tmpr, GCX, GCY, P(31.0), P(13.0), 2.6, 1.3, 'b')
        for y in range(H):
            for x in range(W):
                if tmpr[y][x] != '.':
                    ang = math.degrees(math.atan2((y + 0.5 - GCY) / P(13.0), (x + 0.5 - GCX) / P(31.0))) % 360
                    if int(ang // 15) % 2 == 0:
                        g[y][x] = tmpr[y][x]
        tmp = canvas(W, H)
        Sd = cloud(GCX - P(21), GCY + P(2), P(4.4), n=4, seed=9)
        Fd = cloud(GCX - P(9), GCY + P(9), P(4.0), n=3, seed=10)
        B = cloud(GCX - P(12), GCY - P(6), P(3.0), n=3, seed=11)
        dust(tmp, Sd + mirror_circles(Sd) + Fd + mirror_circles(Fd) + B + mirror_circles(B), outline=None, ramp='pqqs')
        # old frame faded its outer dust pixels with 150 alpha; dissolve them with a checker instead
        edge = []
        for y in range(H):
            for x in range(W):
                if tmp[y][x] != '.':
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        xx, yy = x + dx, y + dy
                        if not (0 <= xx < W and 0 <= yy < H) or tmp[yy][xx] == '.':
                            edge.append((x, y))
                            break
        for x, y in edge:
            if (x + y) % 2 == 0:
                tmp[y][x] = '.'
        layer_onto(g, tmp)
        put(g, 11, 60, ROCK_SML); put(g, 89, 62, ROCK_SML)
        put(g, 26, 74, ROCK_MED); put(g, 73, 75, ROCK_MED)
        put(g, 49, 76, ROCK_SML)
    return g


if __name__ == '__main__':
    out_t = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'elbow_target_v2_wip.png')
    out_i = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'elbow_impact_v2_wip.png')
    t = [target(0), target(1)]
    for i, fr in enumerate(t):
        symmetric_check(fr, 'target_v2 %d' % i)
    write_strip(out_t, t)
    imp = [impact(i) for i in range(4)]
    for i, fr in enumerate(imp):
        edge = [(x, y) for y in range(IW) for x in range(IW) if fr[y][x] != '.' and (x in (0, IW - 1) or y in (0, IW - 1))]
        if edge:
            print('WARN impact_v2 frame', i, 'touches frame edge at', edge[:6])
    write_strip(out_i, imp)
    print('ok')
