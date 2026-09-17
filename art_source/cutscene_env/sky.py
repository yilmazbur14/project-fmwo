"""street_sky.png (960x360): drizzly dusk sky + distant skyline with the arena far off. Opaque.

Visible through the street layer mostly at y < 110 (above rooftops) and through the vacant lot (y < 186).
"""
import math
import random
from lib import Canvas, bayer, hsh, vnoise

W, H = 960, 360
BASE = 250
ARENA_X = 700


def sky_gradient(c):
    stops = [(0, 'N'), (18, 'N'), (50, 'I'), (78, 'I'), (116, 'V')]
    for y in range(H):
        k = 'V'
        for (ya, ka), (yb, kb) in zip(stops, stops[1:]):
            if ya <= y < yb:
                t = (y - ya) / float(yb - ya)
                k = (ka, kb, t)
                break
        for x in range(W):
            if isinstance(k, tuple):
                ka, kb, t = k
                c.p[y][x] = kb if bayer(x, y) < t else ka
            else:
                c.p[y][x] = k


DARKER = {'I': 'N', 'V': 'I', 'N': 'N'}
LIGHTER = {'N': 'I', 'I': 'V', 'V': '8'}


def clouds(c):
    """Low overcast streaks: darker bodies, a broken city-glow underside."""
    bands = [(10, 7, 1, 0.40), (26, 6, 2, 0.45), (44, 7, 3, 0.42), (62, 5, 4, 0.50), (84, 4, 5, 0.55), (104, 3, 6, 0.6)]
    for (cy, thick, s, thr) in bands:
        for x in range(W):
            n = vnoise(x / 61.0, s) * 0.65 + vnoise(x / 19.0, s + 40) * 0.35
            if n < thr:
                continue
            t = min(1.0, (n - thr) / (1.0 - thr) * 1.6)
            half = max(1, int(round(thick * t)))
            off = int(round(6 * (vnoise(x / 97.0, s + 9) - 0.5)))
            top = cy + off - half
            bot = cy + off + half // 2
            for y in range(top, bot + 1):
                if 0 <= y < H:
                    if y == top and bayer(x, y) > 0.5:
                        continue
                    k = c.p[y][x]
                    c.p[y][x] = DARKER.get(k, k)
            y = bot + 1
            if 0 <= y < H and bayer(x, y) < 0.35 + 0.5 * t and y > 36:
                k = c.p[y][x]
                c.p[y][x] = LIGHTER.get(k, k)


def windows(c, x0, x1, top, rnd, cols, lit=0.25, sx=3, sy=4):
    """Office-grid windows lit in clusters (whole floors / columns), not noise."""
    floors = list(range(top + 4, BASE - 2, sy))
    col_on = [rnd.random() < 0.5 for _ in range(0, x1 - x0 + 1, sx)]
    for fi, y in enumerate(floors):
        floor_on = rnd.random() < lit
        for ci, x in enumerate(range(x0 + 2, x1 - 1, sx)):
            p = 0.0
            if floor_on:
                p = 0.7
            elif col_on[min(ci, len(col_on) - 1)]:
                p = lit * 0.25
            if rnd.random() < p:
                c.set(x, y, rnd.choice(cols))


def tower(c, x0, x1, top, col, rnd, rim=None, wcols=('A',), lit=0.2, crown=None):
    c.rect(x0, top, x1, BASE, col)
    if crown == 'step':
        w = x1 - x0
        c.rect(x0 + w // 5, top - 6, x1 - w // 5, top, col)
        c.rect(x0 + w // 3, top - 11, x1 - w // 3, top - 6, col)
        if rim:
            c.hline(x0 + w // 5, x1 - w // 5, top - 6, rim)
            c.hline(x0 + w // 3, x1 - w // 3, top - 11, rim)
    elif crown == 'spire':
        m = (x0 + x1) // 2
        for i in range(14):
            half = max(0, (14 - i) // 5)
            c.hline(m - half, m + half, top - 1 - i, col)
        c.vline(m, top - 22, top - 14, col)
        c.set(m, top - 23, 'R')
    elif crown == 'mast':
        m = x0 + (x1 - x0) * 2 // 3
        c.vline(m, top - 16, top, col)
        c.hline(m - 2, m + 2, top - 10, col)
        c.set(m, top - 17, 'R')
    elif crown == 'slant':
        for x in range(x0, x1 + 1):
            h = int((x - x0) * 0.4)
            c.vline(x, top - h, top, col)
        if rim:
            for x in range(x0, x1 + 1):
                c.set(x, top - int((x - x0) * 0.4), rim)
    elif crown == 'tank':
        tx = x0 + 4
        c.line(tx + 1, top - 1, tx + 3, top - 6, col)
        c.line(tx + 9, top - 1, tx + 7, top - 6, col)
        c.rect(tx + 1, top - 12, tx + 9, top - 6, col)
        c.hline(tx + 2, tx + 8, top - 13, col)
        c.hline(tx + 4, tx + 6, top - 14, col)
    if rim and crown not in ('slant',):
        c.hline(x0, x1, top, rim)
    windows(c, x0, x1, top, rnd, wcols, lit)


def far_tier(c):
    rnd = random.Random(21)
    x = -8
    while x < W:
        w = rnd.randint(16, 38)
        top = rnd.randint(40, 92)
        crown = rnd.choice([None, None, 'step', 'mast', 'spire', None])
        if ARENA_X - 70 < x + w // 2 < ARENA_X + 70:
            top = max(top, 70)
        tower(c, x, x + w, top, 'M', rnd, wcols=('V', 'A'), lit=0.12, crown=crown)
        x += w + rnd.randint(-6, 4)


def near_tier(c):
    rnd = random.Random(8)
    x = -6
    while x < W:
        w = rnd.randint(22, 56)
        top = rnd.randint(78, 132)
        crown = rnd.choice([None, None, 'tank', 'mast', 'slant', 'step'])
        if ARENA_X - 90 < x + w and x < ARENA_X + 90:
            x = ARENA_X + 90
            continue
        tower(c, x, x + w, top, 'N', rnd, rim='I', wcols=('d', 'A', 'A', '7'), lit=0.22, crown=crown)
        x += w + rnd.randint(3, 16)


def radio_tower(c, x, top):
    for y in range(top, BASE):
        half = (y - top) // 12
        c.set(x - half, y, 'N')
        c.set(x + half, y, 'N')
        if (y - top) % 8 == 0:
            c.hline(x - half, x + half, y, 'N')
            if y + 8 < BASE:
                c.line(x - half, y, x + (y + 8 - top) // 12, y + 8, 'N')
    c.vline(x, top - 12, top, 'N')
    c.set(x, top - 13, 'R')
    c.set(x, top - 14, 'R')


def arena(c, cx):
    """Distant domed arena: blurple light ring, two searchlights sweeping the cloud deck."""
    rx, ry = 54, 24
    ring = 102
    for (ang, side) in ((-64, 1), (-116, -1)):
        a = math.radians(ang)
        ox, oy = cx + side * 26, ring - 16
        L = 150
        for i in range(L):
            px = ox + math.cos(a) * i
            py = oy + math.sin(a) * i
            wdt = 1.2 + i * 0.05
            fade = 1.0 - i / float(L)
            for j in range(-int(wdt) - 1, int(wdt) + 2):
                qx, qy = int(round(px + j)), int(round(py))
                if not (0 <= qx < W and 0 <= qy < H):
                    continue
                core = abs(j) <= wdt * 0.35
                dens = (0.8 if core else 0.35) * fade
                if bayer(qx, qy) < dens:
                    k = c.p[qy][qx]
                    c.p[qy][qx] = {'N': 'I', 'I': 'U' if core and fade > 0.55 else 'V', 'V': 'U', 'M': 'V'}.get(k, k)
    # stands / drum
    c.rect(cx - rx - 4, ring - 2, cx + rx + 4, BASE, 'N')
    for y in range(ring - ry - 2, ring - 1):
        for x in range(cx - rx, cx + rx + 1):
            dx = (x + 0.5 - cx) / rx
            dy = (y + 0.5 - (ring - 2)) / ry
            if dx * dx + dy * dy <= 1.0:
                c.set(x, y, 'N')
    # glow catching the ribs
    for kk in (-2, -1, 0, 1, 2):
        for y in range(ring - ry - 2, ring - 2):
            dy = (y + 0.5 - (ring - 2)) / ry
            xr = math.sqrt(max(0.0, 1 - dy * dy)) * rx
            x = int(round(cx + xr * kk / 3.0))
            if c.get(x, y) == 'N' and (y % 2 == 0):
                c.set(x, y, 'I')
    # cap ring on the crown
    c.hline(cx - 6, cx + 6, ring - ry - 2, 'I')
    c.vline(cx, ring - ry - 12, ring - ry - 3, 'N')
    c.rect(cx + 1, ring - ry - 12, cx + 6, ring - ry - 9, 'N')
    c.set(cx, ring - ry - 13, 'R')
    # the blurple light ring
    for x in range(cx - rx - 4, cx + rx + 5):
        c.set(x, ring - 1, 'U' if (x // 3) % 2 == 0 else 'u')
        c.set(x, ring, 'I')
    # entrance lights under the ring
    for x in range(cx - rx + 2, cx + rx - 2, 9):
        c.rect(x, ring + 6, x + 3, ring + 9, 'A')


def build():
    c = Canvas(W, H)
    sky_gradient(c)
    clouds(c)
    far_tier(c)
    radio_tower(c, 250, 22)
    arena(c, ARENA_X)
    near_tier(c)
    c.rect(0, BASE, W - 1, H - 1, 'N')
    return c


if __name__ == '__main__':
    c = build()
    c.save('out/street_sky.png')
    c.save('view/sky_2x.png', 2)
