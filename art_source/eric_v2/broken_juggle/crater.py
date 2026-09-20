"""eric_crash_crater.png: the Knight Breaker crash crater, a floor decal for the green canvas mat.
4 frames of 128x48 (flash, crack, settle, held); crater centre at (64, 25) on every frame.

The ring is canvas over boards, so the crater is a bowl punched into the canvas: a rough raised lip
(lit on its upper-left slope, shadowed lower-right), a bowl whose far wall sits in the lip's shadow,
a jagged tear at the bottom showing the snapped boards, and black cracks running out across the mat in
the house floor-crack style (eric_quake_impact). Greens are arena_mat's own plus three deeper shades.

    python crater.py <out_dir> [frame ...]      (frame names: settle held)
"""
import os
import sys
import math
import random
from PIL import Image

W, H = 128, 48
CX, CY = 64.0, 25.0
SQ = 0.33                     # floor foreshortening (y radius / x radius)

C = {
    'k': (0, 0, 0, 255),
    'g0': (0xa2, 0xc6, 0x82, 255), 'g1': (0x92, 0xbe, 0x6e, 255), 'g2': (0x88, 0xb4, 0x63, 255),
    'g3': (0x7e, 0xa8, 0x5b, 255), 'g4': (0x6a, 0x8e, 0x4b, 255), 'g5': (0x58, 0x7a, 0x3e, 255),
    'g6': (0x46, 0x62, 0x2f, 255), 'g7': (0x33, 0x48, 0x22, 255),
    'q': (0xb8, 0x8a, 0x5a, 255), 'r': (0x8e, 0x64, 0x40, 255), 'z': (0x6a, 0x46, 0x2c, 255),
    'O': (0x4a, 0x2e, 0x1c, 255), 'p': (0x33, 0x1c, 0x12, 255),
    'W': (255, 255, 255, 255), 'A': (0xea, 0xf0, 0xf6, 255), 'B': (0xcd, 0xd7, 0xe2, 255),
}


class Decal:
    def __init__(self):
        self.px = [[None] * W for _ in range(H)]

    def set(self, x, y, c):
        if 0 <= x < W and 0 <= y < H:
            self.px[y][x] = C[c]

    def get(self, x, y):
        return self.px[y][x] if 0 <= x < W and 0 <= y < H else None

    def image(self):
        im = Image.new('RGBA', (W, H))
        im.putdata([p if p is not None else (0, 0, 0, 0) for row in self.px for p in row])
        return im


def rough(seed, n=24, amp=0.07):
    """per-angle radius multipliers for a rough (hand-broken) ellipse"""
    rnd = random.Random(seed)
    vals = [1.0 + rnd.uniform(-amp, amp) for _ in range(n)]

    def f(a):
        t = (a % (2 * math.pi)) / (2 * math.pi) * n
        i = int(t) % n
        u = t - int(t)
        return vals[i] * (1 - u) + vals[(i + 1) % n] * u
    return f


R_OUT = rough(3, amp=0.06)
R_IN = rough(11, amp=0.07)


def polar(x, y):
    u = x + 0.5 - CX
    v = (y + 0.5 - CY) / SQ
    return math.hypot(u, v), math.atan2(v, u)


def line(pts):
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0), 1))
        for i in range(n + 1):
            p = (int(round(x0 + (x1 - x0) * i / n)), int(round(y0 + (y1 - y0) * i / n)))
            if not out or out[-1] != p:
                out.append(p)
    i = 1
    while i < len(out) - 1:
        a, c = out[i - 1], out[i + 1]
        if abs(a[0] - c[0]) <= 1 and abs(a[1] - c[1]) <= 1:
            del out[i]
        else:
            i += 1
    return out


# ------------------------------------------------------------------ lip + bowl
LIP_OUT, LIP_IN = 50.0, 41.0


def crater_body(d):
    for y in range(H):
        for x in range(W):
            r, a = polar(x, y)
            ro = LIP_OUT * R_OUT(a)
            ri = LIP_IN * R_IN(a)
            if r >= ro:
                continue
            ux, uy = math.cos(a), math.sin(a)          # outward direction (floor space)
            lit = -(ux * 0.6 + uy * 0.8)               # >0: faces the top-left light
            if r >= ri:                                # the raised lip
                t = (r - ri) / (ro - ri)               # 0 at the inner crest, 1 at the outer foot
                if t < 0.28:
                    c = 'g0' if uy > -0.2 else 'g1'    # crest catches the light, brightest on the near side
                elif lit > 0.25:
                    c = 'g1' if t < 0.7 else 'g2'
                elif lit > -0.35:
                    c = 'g2' if t < 0.7 else 'g3'
                else:
                    c = 'g3' if t < 0.6 else 'g4'
                d.set(x, y, c)
                continue
            s = r / ri                                 # 0 centre .. 1 at the crest
            # far wall (upper half) sits in the lip's shadow; the near wall is hidden, the floor lighter
            if uy < 0:
                k = 7 if s > 0.78 else (6 if s > 0.5 else 5)
            else:
                k = 5 if s > 0.84 else (4 if s > 0.45 else 5)
            if uy < 0 and ux < -0.2 and s > 0.6:
                k = 7
            d.set(x, y, 'g%d' % k)
    # hard shadow line under the far crest
    for y in range(H):
        for x in range(W):
            r, a = polar(x, y)
            ri = LIP_IN * R_IN(a)
            if math.sin(a) < -0.15 and ri - 1.6 <= r < ri:
                d.set(x, y, 'k')


# ------------------------------------------------------------------ torn canvas + snapped boards
HOLE = [
    "..................k.....................",
    ".......kkkkkkkk..kqk....kkkkkkkkk.......",
    ".....kkqqqqqqqqk.kqk...kqqqqqqqqqkk.....",
    "...kkqqqrrrrrrqk.kqrk..kqrrrrrrrqqqkk...",
    "..k7krrrrrrrrrrkk.krk.kkrrrrrrrrrrrk7k..",
    ".k77kzzzzzzzzzzzk.kzk.kzzzzzzzzzzzzk77k.",
    "k777kOOOOOOOOOOOk..kk.kOOOOOOOOOOOOk777k",
    "k777kkkkkkkkkkkkk7777kkkkkkkkkkkkkkk777k",
    ".k77777pppp777777777777777ppp777777777k.",
    "..kkk777777777777777777777777777777kkk..",
    ".....kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk....",
]
HOLE_C = {'k': 'k', '7': 'g7', 'O': 'O', 'z': 'z', 'r': 'r', 'q': 'q', 'p': 'p'}


def tear(d):
    x0 = int(CX) - len(HOLE[0]) // 2
    y0 = int(CY) - len(HOLE) // 2 + 1
    for r, row in enumerate(HOLE):
        for c, ch in enumerate(row):
            if ch != '.':
                d.set(x0 + c, y0 + r, HOLE_C[ch])
    # torn canvas lip curling up around the tear (lit green flecks on the far edge)
    for x, y in [(x0 + 4, y0 + 1), (x0 + 5, y0), (x0 + 20, y0), (x0 + 21, y0 + 1), (x0 + 36, y0 + 2)]:
        d.set(x, y, 'g2')


# ------------------------------------------------------------------ cracks
CRACKS = [   # (angle deg in floor space, length px, branch)
    (-176, 14, 1), (-156, 10, 0), (-128, 8, 0), (-58, 8, 0), (-24, 12, 1), (-4, 14, 1), (22, 11, 0),
    (158, 12, 1), (140, 9, 0), (100, 9, 0), (70, 9, 1), (40, 10, 0), (120, 8, 0),
]


def cracks(d, grow=1.0, seed=5):
    rnd = random.Random(seed)
    for ang, length, br in CRACKS:
        a = math.radians(ang)
        ux, uy = math.cos(a), math.sin(a)
        start = LIP_IN * R_IN(a) - 2.0
        pts = []
        L = start + length * grow
        rr = start
        wob = 0.0
        while rr <= L:
            wob += rnd.uniform(-0.18, 0.18)
            wob = max(-0.35, min(0.35, wob))
            aa = a + wob
            pts.append((CX + math.cos(aa) * rr, CY + math.sin(aa) * rr * SQ))
            rr += 4.0
        path = line(pts)
        for x, y in path:
            d.set(x, y, 'k')
        for x, y in path:                        # lit ridge on the far side of each crack
            if d.get(x, y - 1) not in (C['k'], None) or polar(x, y - 1)[0] > LIP_OUT:
                if polar(x, y - 1)[0] > LIP_OUT * 0.98:
                    d.set(x, y - 1, 'g1')
        if br and grow > 0.6:
            k = max(1, len(pts) * 2 // 3)
            bx, by = pts[min(k, len(pts) - 1)]
            ba = a + (0.8 if rnd.random() < 0.5 else -0.8)
            bl = length * 0.35 * grow
            for x, y in line([(bx, by), (bx + math.cos(ba) * bl, by + math.sin(ba) * bl * SQ)]):
                d.set(x, y, 'k')


# ------------------------------------------------------------------ debris and dust
CHIP = ["kk.", "k1k", ".kk"]
SPLINTER = ["kk..", "kqkk", ".krk", "..kk"]
PUFF = [".kkk.", "kWWAk", "kABBk", ".kkk."]


def stamp(d, g, x0, y0, cmap):
    for r, row in enumerate(g):
        for c, ch in enumerate(row):
            if ch != '.':
                d.set(x0 + c, y0 + r, cmap.get(ch, ch))


def debris(d, chips=(), splinters=(), puffs=()):
    for x, y in chips:
        stamp(d, CHIP, x, y, {'1': 'g1'})
    for x, y in splinters:
        stamp(d, SPLINTER, x, y, {})
    for x, y in puffs:
        stamp(d, PUFF, x, y, {})


# ------------------------------------------------------------------ frames
C.update({'Z': (0xff, 0xf7, 0xd6, 255), 'gy': (0xff, 0xf0, 0xa8, 255), 'Gy': (0xf2, 0xc4, 0x57, 255),
          'hy': (0xc4, 0x8a, 0x2c, 255)})


def flash():
    """the Knight Breaker impact: a flattened gold-and-white starburst on the mat, dent just forming"""
    d = Decal()
    rays = [(-180, 50), (-158, 44), (-135, 50), (-112, 30), (-90, 26), (-68, 30), (-45, 50), (-22, 44), (0, 50),
            (22, 40), (45, 34), (68, 24), (90, 22), (112, 24), (135, 34), (158, 40)]
    for a, L in rays:
        t = math.radians(a)
        for i in range(0, 200):
            s = i / 200.0
            r = 10 + L * s
            w = 3.2 * (1 - s) + 0.4
            cx = CX + math.cos(t) * r
            cy = CY + math.sin(t) * r * SQ
            for yy in range(int(cy - w), int(cy + w) + 1):
                for xx in range(int(cx - w), int(cx + w) + 1):
                    dist = math.hypot(xx + 0.5 - cx, (yy + 0.5 - cy) / 0.8)
                    if dist <= w:
                        c = 'W' if (s < 0.45 and dist < w * 0.55) else ('gy' if s < 0.7 else 'Gy')
                        if d.get(xx, yy) in (C['W'], C['Z']) and c != 'W':
                            continue
                        d.set(xx, yy, c)
    for y in range(H):
        for x in range(W):
            r, a = polar(x, y)
            if r < 22:
                d.set(x, y, 'Z' if r < 15 else 'W')
            elif r < 25 and d.get(x, y) is None:
                d.set(x, y, 'gy')
    # the thin shock ring racing out across the canvas
    for y in range(H):
        for x in range(W):
            r, a = polar(x, y)
            if 57.0 <= r < 58.6 and math.sin(a) > -0.9:
                d.set(x, y, 'gy' if math.cos(a) < 0.3 else 'Gy')
    # a black keyline so the burst reads on the bright mat
    solid = [[d.px[y][x] is not None for x in range(W)] for y in range(H)]
    for y in range(H):
        for x in range(W):
            if solid[y][x]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < W and 0 <= yy < H and solid[yy][xx] and d.px[yy][xx] in (C['Gy'], C['gy']):
                    if polar(xx, yy)[0] < 50:
                        d.set(x, y, 'hy')
                    break
    return d


def crack():
    """the bowl punched in, cracks racing out, canvas chips thrown up"""
    d = Decal()
    crater_body(d)
    tear(d)
    cracks(d, grow=0.65)
    debris(d, chips=[(20, 4), (104, 2), (60, 1), (36, 10), (88, 8)], splinters=[(48, 3), (76, 0)],
           puffs=[(14, 28), (106, 30), (26, 38), (94, 40), (8, 20), (114, 22)])
    return d


def settle():
    d = Decal()
    crater_body(d)
    tear(d)
    cracks(d)
    debris(d, chips=[(4, 14), (118, 30), (24, 41), (100, 3), (122, 16), (52, 44)],
           splinters=[(12, 33), (106, 40), (80, 1)], puffs=[(0, 24), (121, 38), (30, 1), (88, 43)])
    return d


def held():
    d = Decal()
    crater_body(d)
    tear(d)
    cracks(d)
    debris(d, chips=[(4, 14), (118, 30), (24, 41), (100, 3), (122, 16), (52, 44)],
           splinters=[(12, 33), (106, 40), (80, 1)])
    return d


FRAMES = {'settle': settle, 'held': held}

if __name__ == '__main__':
    out = sys.argv[1]
    names = sys.argv[2:] or list(FRAMES)
    os.makedirs(out, exist_ok=True)
    for n in names:
        im = FRAMES[n]().image()
        im.save(os.path.join(out, 'crater_' + n + '.png'))
        print('crater', n, im.getbbox())
