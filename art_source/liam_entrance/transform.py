"""Transformation: 3 key frames between normal Bixby and the approved beast (bixby_transform_keys.png).
Frames 320x256.  Ground contact (Bixby's feet) at row 251, centre x 160.
  0 GLOW   Bixby (headband snagged on the middle head) splitting with lava cracks, eyes igniting, heat aura, embers
  1 SWELL  a dark silhouette ~75% of the beast's size, wings tearing out, horns, light beams from the cracks
  2 FLASH  radial burst filling the frame, the exact bixby_beast.png frame-0 silhouette backlit with its glowing
           eyes / mouth fire / cracks; its hover anchor (96,152) sits at (160,211), i.e. 40 px above the ground,
           matching the arena mockup's hover gap.  Pair it with a full-screen white flash in code."""
import math
import os
import random
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from pal import *
from liamkit import BIX_PNG
import swallow
import fx
import view
from pngio import read_png

TW, TH = 320, 256
CX = TW // 2
GROUND = 251
BIX_POS = (CX - 32, GROUND - 63)
BEAST_PNG = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Bixby/bixby_beast.png'
BEAST_POS = (CX - 96, GROUND - 40 - 152)
BOUND = (CX, 139, 156, 116)     # every ray / beam stays inside this ellipse (cx, cy, rx, ry)

GLOW_KEYS = {hx('fff7a0'), hx('fbf236'), hx('f58a38'), hx('df7126')}
CRIMSON = WING          # e0524a ac3232 8a1f38 5e142c 3c0c20
SHADOW_BLACK = HORN[4]  # 121016


def beast_frame0():
    w, h, px = read_png(BEAST_PNG)
    cv = Canvas(192, 160)
    for y in range(160):
        for x in range(192):
            p = tuple(px[y][x])
            if p[3]:
                cv.px[y][x] = p
    return cv


def post_gulp_bixby():
    cv = from_png(BIX_PNG)
    tie = {'k': BLACK, 'T': L_TIE[1], 'y': L_TIE[2], 'm': L_STEEL[0], 'M': L_STEEL[1], 'e': L_STEEL[2], 'E': L_STEEL[3]}
    cv.stamp(swallow.HEADBAND_ON_BIX, 20, 2, tie)
    return cv


def crack(cv, x, y, ang, length, rnd, mask, branch=True):
    """jagged 1px lava crack with orange edges, confined to mask"""
    pts = []
    a = math.radians(ang)
    for i in range(length):
        a += rnd.uniform(-0.55, 0.55)
        x += math.cos(a)
        y += math.sin(a)
        p = (int(round(x)), int(round(y)))
        if p not in mask:
            break
        pts.append(p)
        if branch and i > 3 and rnd.random() < 0.12:
            crack(cv, x, y, math.degrees(a) + rnd.choice((-50, 50)), length // 3, rnd, mask, branch=False)
    for p in pts:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (p[0] + dx, p[1] + dy)
            c = cv.get(*q)
            if q in mask and c is not None and c != BLACK and c not in (LAVA[1], LAVA[2]):
                cv.put(*q, LAVA[4])
    for i, p in enumerate(pts):
        cv.put(*p, LAVA[1] if i % 5 else LAVA[2])


def aura(cv, colors):
    """solid (alpha 0/255) heat outline rings grown outward from the sprite"""
    for c in colors:
        outline_outside(cv, c)


def embers(cv, rnd, box, n, cols=(LAVA[2], LAVA[3], LAVA[1])):
    x0, y0, x1, y1 = box
    for _ in range(n):
        x, y = rnd.randint(x0, x1), rnd.randint(y0, y1)
        if cv.get(x, y) is None:
            c = rnd.choice(cols)
            cv.put(x, y, c)
            if rnd.random() < 0.5 and cv.get(x, y + 1) is None:
                cv.put(x, y + 1, LAVA[4])


# ------------------------------------------------------------------ 0 GLOW
def frame_glow():
    rnd = random.Random(7)
    cv = Canvas(TW, TH)
    b = post_gulp_bixby()
    # warm the whole dog one step toward red where it is dark saddle
    body = Canvas(TW, TH)
    body.blit(b, *BIX_POS)
    m = body.mask()
    inner = erode(m, 1)
    for (x, y) in list(inner):
        c = body.get(x, y)
        if c in B_SADDLE[1:]:
            body.put(x, y, CRIMSON[3] if c == B_SADDLE[1] else CRIMSON[4])
    ox, oy = BIX_POS
    for (sx, sy, ang, ln) in ((6, 30, 70, 16), (3, 42, 10, 18), (48, 40, 110, 12), (56, 44, 190, 14), (30, 48, 80, 14),
                              (22, 36, 200, 10), (40, 30, 60, 12), (31, 3, 90, 8), (12, 18, 120, 8), (52, 18, 60, 8),
                              (16, 52, 95, 10), (46, 52, 85, 10)):
        crack(body, ox + sx, oy + sy, ang, ln, rnd, inner)
    # eyes ignite
    for (x, y) in ((25, 11), (26, 11), (36, 11), (37, 11), (10, 24), (17, 24), (46, 23), (54, 23)):
        body.put(ox + x, oy + y, LAVA[1])
    for (x, y) in ((25, 10), (37, 10), (11, 24), (16, 24), (47, 23), (53, 23)):
        body.put(ox + x, oy + y, LAVA[2])
    # scorch glow on the ground under him
    pool = ell(CX, GROUND - 1, 44, 7)
    for (x, y) in pool:
        d = math.hypot((x + 0.5 - CX) / 44, (y + 0.5 - GROUND + 1) / 7)
        cv.put(x, y, LAVA[2] if d < 0.45 else (LAVA[3] if d < 0.75 else LAVA[5]))
    cv.outline(pool, CRIMSON[4])
    cv.blit(body)
    # glare crosses on the six igniting eyes
    for (x, y) in ((25, 11), (37, 11), (10, 24), (17, 24), (46, 23), (54, 23)):
        for dx, dy in ((0, -2), (0, 2), (-2, 0), (2, 0)):
            if cv.get(ox + x + dx, oy + y + dy) is None:
                cv.put(ox + x + dx, oy + y + dy, LAVA[0])
    aura(cv, [LAVA[2], LAVA[4], CRIMSON[2]])
    # flame tongues licking up off the back and heads
    for (x, h) in ((4, 9), (12, 13), (20, 16), (27, 11), (33, 20), (40, 12), (47, 17), (54, 12), (60, 8)):
        cols = [y for (xx, y) in cv.mask() if xx == ox + x and y > oy - 30]
        top = min(cols) if cols else oy + 20
        tongue = poly([(ox + x - 3, top + 2), (ox + x + 3, top + 2), (ox + x + 1, top - h * 0.55), (ox + x - 0.5, top - h)])
        for p in tongue:
            if cv.get(*p) is None:
                cv.put(*p, LAVA[1] if p[1] > top - h * 0.3 else (LAVA[2] if p[1] > top - h * 0.65 else LAVA[3]))
        cv.outline(tongue - body.mask(), CRIMSON[2])
    # heat shimmer lines and embers
    for (x, y, l) in ((ox - 10, oy - 6, 5), (ox + 72, oy - 2, 4), (ox - 4, oy - 30, 4), (ox + 66, oy - 26, 4), (ox + 30, oy - 44, 5)):
        for i in range(l):
            if cv.get(x, y - i) is None:
                cv.put(x, y - i, LAVA[2] if i == 0 else LAVA[3])
    embers(cv, rnd, (ox - 30, oy - 70, ox + 94, oy + 20), 90)
    return cv


# ------------------------------------------------------------------ 1 SWELL
def scaled_mask(mask, s, ax, ay):
    """nearest-neighbour scale of a mask about anchor (ax, ay)"""
    out = set()
    xs = [p[0] for p in mask]
    ys = [p[1] for p in mask]
    X0 = int(ax + (min(xs) - ax) * s) - 2
    X1 = int(ax + (max(xs) - ax) * s) + 2
    Y0 = int(ay + (min(ys) - ay) * s) - 2
    Y1 = int(ay + (max(ys) - ay) * s) + 2
    for y in range(Y0, Y1 + 1):
        for x in range(X0, X1 + 1):
            sx = int(math.floor((x + 0.5 - ax) / s + ax))
            sy = int(math.floor((y + 0.5 - ay) / s + ay))
            if (sx, sy) in mask:
                out.add((x, y))
    # smooth: majority filter
    for _ in range(2):
        add, rem = set(), set()
        for y in range(Y0, Y1 + 1):
            for x in range(X0, X1 + 1):
                n = sum((x + dx, y + dy) in out for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy)
                if (x, y) in out and n <= 2:
                    rem.add((x, y))
                elif (x, y) not in out and n >= 6:
                    add.add((x, y))
        out = (out | add) - rem
    return out


def in_bound(p):
    bx, by, rx, ry = BOUND
    return ((p[0] + 0.5 - bx) / rx) ** 2 + ((p[1] + 0.5 - by) / ry) ** 2 <= 1.0


def spikes(cv, cx, cy, n, r_base, r_tip, base_deg, rnd, cols, sy=0.86, outline=None):
    """sunburst spikes: triangles whose base sits on an inner ellipse and whose tip points outward"""
    for i in range(n):
        a = (360 / n) * i + rnd.uniform(-4, 4)
        w = base_deg * rnd.uniform(0.7, 1.15)
        rt = r_tip * rnd.uniform(0.8, 1.0)

        def P(ang, r):
            return (cx + math.cos(math.radians(ang)) * r, cy + math.sin(math.radians(ang)) * r * sy)
        tri = poly([P(a - w / 2, r_base), P(a + w / 2, r_base), P(a, rt)])
        tri = {p for p in tri if in_bound(p)}
        col = cols[i % len(cols)]
        for p in tri:
            if cv.get(*p) is None:
                cv.put(*p, col)
        if outline:
            for p in edge(tri):
                if cv.get(*p) == col:
                    cv.put(*p, outline)


def beams(cv, cx, cy, n, width_deg, reach, rnd, cols=(LAVA[1], LAVA[2]), edge_col=None):
    """light shafts: wedges from (cx, cy); two-tone (pale core, coloured edge) when edge_col is given"""
    for i in range(n):
        a = (360 / n) * i + rnd.uniform(-8, 8)
        w = width_deg * rnd.uniform(0.6, 1.2)
        r = reach * rnd.uniform(0.7, 1.0)
        pts = [(cx, cy)] + [(cx + math.cos(math.radians(a + t)) * r, cy + math.sin(math.radians(a + t)) * r) for t in (-w / 2, w / 2)]
        wedge = poly(pts)
        col = cols[i % len(cols)]
        core = poly([(cx, cy)] + [(cx + math.cos(math.radians(a + t)) * r * 0.97, cy + math.sin(math.radians(a + t)) * r * 0.97)
                                  for t in (-w / 5, w / 5)])
        for p in wedge:
            if cv.get(*p) is None and in_bound(p):
                cv.put(*p, edge_col if (edge_col and p not in core) else col)


def frame_swell():
    rnd = random.Random(11)
    cv = Canvas(TW, TH)
    beast = beast_frame0()
    bmask = {(x + BEAST_POS[0], y + BEAST_POS[1]) for (x, y) in beast.mask()}
    # growing from the ground: scale about the feet
    sil = scaled_mask(bmask, 0.74, CX, GROUND)
    x0, y0, x1, y1 = bbox(sil)
    chest = (CX, int(y0 + (y1 - y0) * 0.55))
    beams(cv, chest[0], chest[1], 14, 12, 190, rnd, cols=(LAVA[0], LAVA[1]), edge_col=LAVA[2])
    # silhouette body: glowing crimson core fading to near-black at the edges, rim-lit
    dist = chamfer(sil)
    for (x, y) in sil:
        dcore = math.hypot(x - chest[0], (y - chest[1]) * 1.2)
        v = dcore / 70.0 - min(dist[(x, y)], 6) / 30.0
        cv.put(x, y, CRIMSON[2] if v < 0.18 else (CRIMSON[3] if v < 0.45 else CRIMSON[4]))
    rim = edge(sil)
    for (x, y) in rim:
        cv.put(x, y, BLACK)
    inner_rim = edge(erode(sil, 1))
    for (x, y) in inner_rim:
        if x < CX:
            cv.put(x, y, LAVA[3])
        elif rnd.random() < 0.5:
            cv.put(x, y, CRIMSON[1])
    # glowing features carried over from the beast (eyes, fire, cracks), scaled
    for (x, y) in sil:
        sx = int(math.floor((x + 0.5 - CX) / 0.74 + CX)) - BEAST_POS[0]
        sy = int(math.floor((y + 0.5 - GROUND) / 0.74 + GROUND)) - BEAST_POS[1]
        c = beast.get(sx, sy)
        if c in GLOW_KEYS:
            cv.put(x, y, LAVA[1] if c in (hx('fff7a0'), hx('fbf236')) else LAVA[3])
    core = erode(sil, 3)
    for (sx, sy, ang, ln) in ((142, 182, 60, 30), (177, 182, 120, 30), (160, 207, 90, 20), (132, 202, 200, 18),
                              (188, 200, -20, 18), (160, 162, -90, 16)):
        crack(cv, sx, sy, ang, ln, rnd, core)
    aura(cv, [LAVA[3], LAVA[1]])
    embers(cv, rnd, (72, 42, 248, 232), 120, cols=(LAVA[0], LAVA[1], LAVA[2]))
    return cv


# ------------------------------------------------------------------ 2 FLASH
def frame_flash():
    rnd = random.Random(5)
    cv = Canvas(TW, TH)
    beast = beast_frame0()
    ax, ay = CX, BOUND[1]
    # burst: rays to the frame edges, then nested rings white -> pale yellow -> yellow -> orange
    spikes(cv, ax, ay, 22, 118, 190, 11, rnd, (LAVA[3], LAVA[4]), outline=CRIMSON[1])
    spikes(cv, ax, ay, 22, 118, 160, 9, random.Random(9), (LAVA[2], LAVA[1]))
    rings = [(124, LAVA[2]), (112, LAVA[1]), (99, WHITE)]
    for r, c in rings:
        disc = ell(ax, ay, r, r * 0.86)
        for p in disc:
            cv.put(*p, c)
    # crisp white shock ring just outside the burst
    shock = ell(ax, ay, 131, 131 * 0.86) - ell(ax, ay, 129, 129 * 0.86)
    for p in shock:
        cv.put(*p, WHITE)
    # backlit beast silhouette with its own glowing eyes / mouth fire / cracks
    bx, by = BEAST_POS
    m = {(x + bx, y + by) for (x, y) in beast.mask()}
    for p in m:
        cv.put(*p, SHADOW_BLACK)
    for (x, y) in edge(m):
        cv.put(x, y, BLACK)
    for y in range(160):
        for x in range(192):
            c = beast.get(x, y)
            if c in GLOW_KEYS:
                cv.put(x + bx, y + by, LAVA[1] if c in (hx('fff7a0'), hx('fbf236')) else LAVA[3])
    # thin white rim light where the silhouette meets the white core
    for (x, y) in outer_edge(m):
        if cv.get(x, y) == WHITE:
            pass
    for (x, y) in edge(m):
        if any(cv.get(x + dx, y + dy) == WHITE for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            cv.put(x, y, CRIMSON[0])
    return cv


def build():
    return [frame_glow(), frame_swell(), frame_flash()]


if __name__ == '__main__':
    fr = build()
    view.row(fr, 3, 'transform_keys_3x.png', panel=(40, 44, 52, 255))
    print('ok')
