"""Defensive hit effects (DB32, alpha 0/255), drawn at the player's 2x scale.
  block_spark       : 4 frames of 32x32, centre (16, 16) on the contact point. Dull grey 'absorbed' thud.
  parry_flash       : 5 frames of 64x64, centre (32, 32) on the contact point. White-gold tink star + shock ring.
  guard_break_stars : 6 frames of 32x16, pivot (16, 9) on the top of the player's head. 3 stars orbit, looped.
"""
import sys
sys.dont_write_bytecode = True
import math
from dh_common import *


def put(c, x, y, ch):
    c.set(int(x), int(y), C[ch])


def disc(c, cx, cy, r, ch, only_empty=False):
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            if math.hypot(x - cx, y - cy) <= r:
                if only_empty and c.get(x, y) is not None:
                    continue
                put(c, x, y, ch)


def outline(c, col='K', diag=False):
    solid = {(x, y) for y in range(c.h) for x in range(c.w) if c.p[y][x]}
    nb = ((1, 0), (-1, 0), (0, 1), (0, -1)) + (((1, 1), (-1, 1), (1, -1), (-1, -1)) if diag else ())
    for (x, y) in solid:
        for dx, dy in nb:
            q = (x + dx, y + dy)
            if q not in solid and c.inb(*q):
                c.p[q[1]][q[0]] = C[col]


def layer_over(dst, src):
    dst.blit(src, 0, 0)


def ring(c, cx, cy, r, cols, gaps=()):
    th = len(cols)
    for y in range(c.h):
        for x in range(c.w):
            d = math.hypot(x - cx, y - cy)
            k = int(math.floor(d - r))
            if 0 <= k < th:
                a = math.degrees(math.atan2(y - cy, x - cx)) % 360
                if any((a0 <= a <= a1) if a0 <= a1 else (a >= a0 or a <= a1) for a0, a1 in gaps):
                    continue
                put(c, x, y, cols[k])


def sparkle(c, x, y, size, core='W', tip='Y'):
    put(c, x, y, core)
    for k in range(1, size + 1):
        col = core if k < size else tip
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            put(c, x + dx, y + dy, col)


def needle(c, cx, cy, ang, r0, r1, cols):
    """1 px line from radius r0 to r1, colours along its length"""
    a = math.radians(ang)
    n = int(r1 - r0) + 1
    for k in range(n):
        r = r0 + k
        put(c, round(cx + r * math.cos(a)), round(cy + r * math.sin(a)), cols[min(len(cols) - 1, k * len(cols) // n)])


def astroid(c, cx, cy, rx, ry, p, fill, edge):
    """concave 4-point star: (|dx|/rx)^p + (|dy|/ry)^p <= 1 (p < 1 pinches the arms)"""
    inside = set()
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            dx, dy = abs(x - cx), abs(y - cy)
            if (dx / rx) ** p + (dy / ry) ** p <= 1.0:
                inside.add((x, y))
    for (x, y) in inside:
        e = any((x + ddx, y + ddy) not in inside for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        put(c, x, y, edge if e else fill)
    return inside


# ------------------------------------------------------------------ parry flash (64x64)
PS, PC_ = 64, 32


def parry_frame(i):
    cx = cy = PC_
    c = Canvas(PS, PS)
    if i == 0:
        # contact 'tink': a small, very bright 4-point star with needle glints
        for ang, ln in ((0, 17), (180, 17), (-90, 14), (90, 12)):
            needle(c, cx, cy, ang, 6, ln, ['W', 'W', 'Y'])
        body = Canvas(PS, PS)
        astroid(body, cx, cy, 8, 7, 0.55, 'W', 'Y')
        disc(body, cx, cy, 1.5, 'W')
        outline(body)
        layer_over(c, body)
    elif i == 1:
        # peak: big clean 4-point star, long needles, short diagonal glints
        for ang, ln in ((0, 30), (180, 30), (-90, 27), (90, 23)):
            needle(c, cx, cy, ang, 14, ln, ['W', 'W', 'Y', 'T'])
        for ang in (45, 135, 225, 315):
            needle(c, cx, cy, ang, 5, 11, ['W', 'Y', 'T'])
        body = Canvas(PS, PS)
        astroid(body, cx, cy, 15, 13, 0.55, 'W', 'Y')
        disc(body, cx, cy, 3.2, 'W')
        outline(body)
        layer_over(c, body)
    elif i == 2:
        # shock ring (white inside, gold outside), star shrinks, 8 sparks streak outward
        ring(c, cx, cy, 16, ['W', 'Y'])
        body = Canvas(PS, PS)
        astroid(body, cx, cy, 8, 7, 0.55, 'W', 'Y')
        outline(body)
        layer_over(c, body)
        for k in range(8):
            needle(c, cx, cy, 22.5 + 45 * k, 20, 25, ['W', 'Y', 'T'])
    elif i == 3:
        # ring thins to gold arcs, star becomes a twinkle, sparks fly further and shorten
        ring(c, cx, cy, 22, ['Y'], gaps=[(35, 55), (125, 145), (215, 235), (305, 325)])
        sparkle(c, cx, cy, 3, 'W', 'Y')
        for k in range(8):
            needle(c, cx, cy, 22.5 + 45 * k, 26, 28, ['Y', 'T'])
    else:
        # last glints: short arc stubs at the cardinal points and a few twinkles
        for k in range(4):
            for da in range(-8, 9, 2):
                aa = math.radians(90 * k + da)
                put(c, round(cx + 26 * math.cos(aa)), round(cy + 26 * math.sin(aa)), 'T' if abs(da) > 4 else 'Y')
        for (x, y, sz) in ((cx - 12, cy - 15, 1), (cx + 14, cy + 11, 1), (cx + 17, cy - 19, 2), (cx - 19, cy + 16, 1)):
            sparkle(c, x, y, sz, 'W', 'Y')
    return c


def parry_flash():
    return [parry_frame(i) for i in range(5)]


# ------------------------------------------------------------------ block spark (32x32)
BS, BC = 32, 16
BLOCK_SPARKS = [(-155, 'a'), (-115, 'b'), (-60, 'a'), (-20, 'b'), (160, 'b'), (35, 'a')]


def jagged_star(c, cx, cy, verts, inner, fill, edge):
    inside = set()
    for y in range(int(cy) - 10, int(cy) + 11):
        for x in range(int(cx) - 10, int(cx) + 11):
            dx, dy = x - cx, y - cy
            r = math.hypot(dx, dy)
            a = math.degrees(math.atan2(dy, dx)) % 360
            best = inner
            for va, vr in verts:
                d = min(abs(a - va), 360 - abs(a - va))
                best = max(best, vr - d * (vr - inner) / 26.0)
            if r <= best:
                inside.add((x, y))
    for (x, y) in inside:
        e = any((x + ddx, y + ddy) not in inside for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        put(c, x, y, edge if e else fill)
    return inside


def block_frame(i):
    cx = cy = BC
    c = Canvas(BS, BS)
    if i == 0:
        # blunt, uneven impact star: pale core, grey edge, black outline - flatter than a hit spark
        body = Canvas(BS, BS)
        jagged_star(body, cx, cy, [(0, 7.5), (58, 5), (115, 6), (180, 7), (235, 5.5), (295, 6.5)], 3.0, 'P', 's')
        put(body, cx, cy, 'W')
        put(body, cx - 1, cy, 'W')
        put(body, cx, cy - 1, 'W')
        outline(body)
        layer_over(c, body)
    elif i == 1:
        # the burst is swallowed into a squashed grey puff; stubby sparks glance off
        stamp(c, [
            "..KKKK...",
            ".KsPPsKK.",
            "KsPsssshK",
            "KhsshhhhK",
            ".KhhhjjK.",
            "..KKKKK..",
        ], cx - 4, cy - 3)
        for ang, kind in BLOCK_SPARKS:
            r = 8 if kind == 'a' else 7
            aa = math.radians(ang)
            x, y = cx + r * math.cos(aa), cy + r * math.sin(aa)
            put(c, round(x), round(y), 's')
            put(c, round(x - math.cos(aa)), round(y - math.sin(aa)), 'P' if kind == 'a' else 's')
    elif i == 2:
        # smoke puff, sparks slow down and drop
        for (x, y, ch) in ((0, -1, 'h'), (-1, 0, 'h'), (0, 0, 's'), (1, 0, 'h'), (-1, 1, 'j'), (0, 1, 'h'),
                           (1, 1, 'j'), (2, 0, 'j'), (-2, 0, 'j'), (1, -1, 'j')):
            put(c, cx + x, cy + y, ch)
        for ang, kind in BLOCK_SPARKS:
            r = 11 if kind == 'a' else 10
            aa = math.radians(ang)
            x, y = cx + r * math.cos(aa), cy + r * math.sin(aa) + 1.5
            put(c, round(x), round(y), 'h')
            put(c, round(x - math.cos(aa)), round(y - math.sin(aa)), 'j')
    else:
        for (x, y, ch) in ((0, -1, 'j'), (-1, 0, 'k'), (1, 0, 'k'), (0, 1, 'k')):
            put(c, cx + x, cy + y - 1, ch)
        for ang, kind in BLOCK_SPARKS:
            r = 13 if kind == 'a' else 12
            aa = math.radians(ang)
            put(c, round(cx + r * math.cos(aa)), round(cy + r * math.sin(aa) + 4), 'k')
    return c


def block_spark():
    return [block_frame(i) for i in range(4)]


# ------------------------------------------------------------------ guard break stars (32x16)
GW, GH = 32, 16
G_CX, G_CY, G_RX, G_RY = 16, 9, 11.0, 3.2

STAR_FRONT = [
    "...K...",
    "..KYK..",
    "KKKYKKK",
    "KYWYYTK",
    ".KYYTK.",
    ".KYKTK.",
    ".KK.KK.",
]
STAR_BACK = [
    "...K...",
    "..KTK..",
    "KKKTKKK",
    "KTTTDDK",
    ".KTDDK.",
    ".KTKDK.",
    ".KK.KK.",
]


def stars_frame(f):
    c = Canvas(GW, GH)
    items = []
    for k in range(3):
        a = math.radians(120 * k + 20 * f + 10)
        x = G_CX + G_RX * math.cos(a)
        y = G_CY + G_RY * math.sin(a)
        items.append((math.sin(a), x, y))
    items.sort()
    for depth, x, y in items:
        spr = STAR_FRONT if depth > -0.2 else STAR_BACK
        h, w = len(spr), len(spr[0])
        stamp(c, spr, int(round(x - w / 2.0)), int(round(y - h / 2.0)))
    return c


def guard_break_stars():
    return [stars_frame(f) for f in range(6)]


def build():
    return {'block_spark': block_spark(), 'parry_flash': parry_flash(), 'guard_break_stars': guard_break_stars()}


if __name__ == '__main__':
    A = build()
    for name, frames in A.items():
        s = strip(frames)
        z = 8 if frames[0].w <= 32 else 5
        save_zoom(s, work('%s_z.png' % name), z, bg=(136, 180, 99), grid=(frames[0].w, frames[0].h))
        print(name, s.w, s.h, 'non-DB32', s.colours() - DB32)
