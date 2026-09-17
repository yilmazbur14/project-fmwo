"""Playing cards + gold card-magic glow, drawn as rotated rounded rectangles so every card in the
sprite (hat band, fan, thrown card, orbiting cards) is built from one primitive."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jlib import *

# pip glyphs, 3x3 / 5x5, '1' = pip colour
SPADE5 = ["..1..", ".111.", "11111", "11111", ".1.1."]
SPADE3 = [".1.", "111", ".1."]
DIAMOND3 = [".1.", "111", ".1."]
DIAMOND5 = ["..1..", ".111.", "11111", ".111.", "..1.."]


def card_mask(cx, cy, w, h, ang):
    """Rotated rectangle mask + local (u, v) coords for every covered pixel."""
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    m = mask_empty()
    uv = {}
    for y in range(H):
        for x in range(W):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            u = dx * ca + dy * sa
            v = -dx * sa + dy * ca
            if abs(u) <= w / 2.0 and abs(v) <= h / 2.0:
                # clip the corners so the card reads as rounded, not a hard lozenge
                if abs(u) > w / 2.0 - 1.0 and abs(v) > h / 2.0 - 1.0:
                    continue
                m[y][x] = True
                uv[(x, y)] = (u, v)
    return m, uv


def draw_card(c, cx, cy, w, h, ang, face='n', shade='u', dark='U', pip=None,
              pip_col='#', outline='#', lit=True):
    """One playing card. `lit` puts the highlight on the upper-left long edge."""
    m, uv = card_mask(cx, cy, w, h, ang)
    if not uv:
        return m
    for (x, y), (u, v) in uv.items():
        ch = face
        if lit:
            if u > w / 2.0 - 2.2 or v > h / 2.0 - 2.2:
                ch = shade
            if u > w / 2.0 - 1.4 and v > h / 2.0 - 3.0:
                ch = dark
        c[y][x] = ch
    if pip:
        ph, pw = len(pip), len(pip[0])
        a = math.radians(ang)
        ca, sa = math.cos(a), math.sin(a)
        for j in range(ph):
            for i in range(pw):
                if pip[j][i] != '1':
                    continue
                u, v = i - (pw - 1) / 2.0, j - (ph - 1) / 2.0
                x = int(cx + u * ca - v * sa)
                y = int(cy + u * sa + v * ca)
                if m[y][x]:
                    c[y][x] = pip_col
    if outline:
        ol, _ = outline_pixels(m, prune=False)
        for y in range(H):
            for x in range(W):
                if ol[y][x]:
                    c[y][x] = outline
    return m


GOLD_RAMP = ['K', 'A', 'S', 'D', 'F', 'Y', 'w']     # outer -> core (luminance-monotonic)


def glow(c, pts, radii, over='.', ramp=None, jitter=True):
    """Additive gold bloom around `pts`. Only writes over `over` chars (default: transparent)."""
    ramp = ramp or GOLD_RAMP
    field = {}
    for (px, py, amp) in pts:
        for y in range(H):
            for x in range(W):
                d = math.hypot(x + 0.5 - px, y + 0.5 - py)
                v = amp * max(0.0, 1.0 - d / radii)
                if v > 0:
                    field[(x, y)] = field.get((x, y), 0.0) + v
    for (x, y), v in field.items():
        if c[y][x] not in over:
            continue
        if jitter and ((x * 7 + y * 13) % 5 == 0):
            v *= 0.82
        i = int(v * len(ramp))
        if i <= 0:
            continue
        c[y][x] = ramp[min(i - 1, len(ramp) - 1)]
    return c


def card_glow(c, cx, cy, w, h, ang, amp=1.0, reach=7.0, over='.', ramp=None):
    """Bloom that hugs the card rectangle instead of a fat circle, so the card shape survives."""
    ramp = ramp or GOLD_RAMP
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    for y in range(H):
        for x in range(W):
            if c[y][x] not in over:
                continue
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            u = dx * ca + dy * sa
            v = -dx * sa + dy * ca
            du = max(0.0, abs(u) - w / 2.0)
            dv = max(0.0, abs(v) - h / 2.0)
            d = math.hypot(du, dv)
            val = amp * max(0.0, 1.0 - d / reach) ** 1.35
            if (x * 7 + y * 13) % 5 == 0:
                val *= 0.8
            i = int(val * len(ramp))
            if i <= 0:
                continue
            c[y][x] = ramp[min(i - 1, len(ramp) - 1)]
    return c


def rays(c, cx, cy, angles, lengths, gap=6, ramp=('Y', 'F', 'D', 'A')):
    """Radiating light streaks from a point - the anime 'this is magic' cue."""
    for a, L in zip(angles, lengths):
        r = math.radians(a)
        dx, dy = math.sin(r), -math.cos(r)
        for t in range(gap, gap + L):
            x, y = int(cx + dx * t), int(cy + dy * t)
            if not (0 <= x < W and 0 <= y < H) or c[y][x] not in '.KASD':
                continue
            k = (t - gap) * len(ramp) // max(1, L)
            c[y][x] = ramp[min(k, len(ramp) - 1)]
    return c


def rim_light(c, region_chars, src_pt, col='D', reach=44.0, xmax=None):
    """Gold rim on the SILHOUETTE edges facing `src_pt` - the 1px band just inside the black
    outline, so the card reads as the light source without speckling the interior."""
    src = copy(c)
    sx, sy = src_pt
    for y in range(H):
        for x in range(W):
            if src[y][x] not in region_chars:
                continue
            if xmax is not None and x > xmax:
                continue
            d = math.hypot(x - sx, y - sy)
            if d > reach or d < 0.5:
                continue
            dx, dy = (sx - x) / d, (sy - y) / d
            X1, Y1 = int(round(x + dx)), int(round(y + dy))
            X2, Y2 = int(round(x + dx * 2)), int(round(y + dy * 2))
            if not (0 <= X1 < W and 0 <= Y1 < H and 0 <= X2 < W and 0 <= Y2 < H):
                continue
            edge = (src[Y1][X1] == '.') or (src[Y1][X1] == '#' and src[Y2][X2] == '.')
            if not edge:
                continue
            if d > reach * 0.55 and (x + y) % 2:
                continue
            c[y][x] = col if d < reach * 0.55 else 'A'
    return c


def spark(c, x, y, size=1, col='Y'):
    put(c, x, y, col)
    if size >= 2:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            if c[y + dy][x + dx] in '.':
                put(c, x + dx, y + dy, 'F')
    if size >= 3:
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            if c[y + dy][x + dx] in '.':
                put(c, x + dx, y + dy, 'A')
    return c
