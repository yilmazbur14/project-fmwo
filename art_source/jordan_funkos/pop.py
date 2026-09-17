"""Spawn pop: 4 frames x 32x32 (shown at 3x). Pink puff ring (Jordan's shirt ramp), sparkle rays and a
gold collectible-sticker star that pops up above the figure. Centre (16,16) = figure body centre."""
import math
import random
from explosion import Frame, disc, mass, N4, C as EC
from lib import *

W = H = 32
CX, CY = 16.0, 17.0

P = {
    'K': hx('000000'),
    # Jordan pink puff ramp
    'a': hx('fff0f8'), 'b': hx('f7c8e6'), 'c': hx('e49acd'), 'd': hx('b05e97'), 'e': hx('8a4574'),
    # sticker star
    'W': hx('ffffff'), 'Y': hx('fff27a'), 'G': hx('fbd23a'), 'g': hx('e0961e'),
    # sparkle
    's': hx('ffffff'), 'S': hx('fff6a0'), 't': hx('ffc2e8'),
}
PINK = ('a', 'b', 'c', 'd', 'e')


class PFrame(Frame):
    def inside(self, x, y):
        return 0 <= x < W and 0 <= y < H

    def to_px(self):
        px = blank(W, H)
        for (x, y), ch in self.g.items():
            px[y][x] = P[ch]
        return px


def star_mask(cx, cy, R, r, rot=-90.0):
    verts = []
    for i in range(10):
        a = math.radians(rot + i * 36.0)
        rr = R if i % 2 == 0 else r
        verts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    m = set()
    for y in range(int(cy - R - 2), int(cy + R + 3)):
        for x in range(int(cx - R - 2), int(cx + R + 3)):
            px_, py_ = x + 0.5, y + 0.5
            inside = False
            j = len(verts) - 1
            for i in range(len(verts)):
                xi, yi = verts[i]
                xj, yj = verts[j]
                if (yi > py_) != (yj > py_) and px_ < (xj - xi) * (py_ - yi) / (yj - yi + 1e-9) + xi:
                    inside = not inside
                j = i
            if inside:
                m.add((x, y))
    return m


def sticker(f, cx, cy, R, rim=True):
    m = star_mask(cx, cy, R, R * 0.48)
    for (x, y) in m:
        for dx, dy in N4:
            q = (x + dx, y + dy)
            if q not in m:
                f.set(q[0], q[1], 'K')
    edge = {p for p in m if any((p[0] + dx, p[1] + dy) not in m for dx, dy in N4)}
    for (x, y) in m:
        if rim and (x, y) in edge:
            ch = 'W'
        else:
            v = (x + 0.5 - cx) * -0.6 + (y + 0.5 - cy) * -0.8
            ch = 'Y' if v > 0.8 else ('G' if v > -1.2 else 'g')
        f.set(x, y, ch)


def sparkle(f, x, y, size, ch_core='s', ch_arm='S'):
    f.set(x, y, ch_core)
    for k in range(1, size + 1):
        c = ch_arm if k < size else 't'
        for dx, dy in N4:
            f.set(x + dx * k, y + dy * k, c)


def puff_ring(n, R, r, rot, seed, sy=0.85, rs=(1.0, 0.8)):
    rnd = random.Random(seed)
    pts = []
    for i in range(n):
        a = math.radians(rot + 360.0 * i / n + rnd.uniform(-8, 8))
        pts.append((CX + R * math.cos(a), CY + R * math.sin(a) * sy, r * rs[i % len(rs)]))
    pts.sort(key=lambda p: p[1])
    return pts


def f0():
    f = PFrame()
    # tight hot flash + 4 tiny puffs
    for p in puff_ring(5, 4.0, 2.6, rot=-90, seed=1):
        mass(f, [p], PINK, 'd')
    for p in disc(CX, CY, 3.0):
        f.set(p[0], p[1], 's')
    sparkle(f, int(CX), int(CY), 5)
    return f


def f1():
    f = PFrame()
    mass(f, puff_ring(11, 8.2, 3.5, rot=-90, seed=2, rs=(1.0, 0.85, 0.95)), PINK, 'd')
    for ang in (45, 135, 225, 315):
        a = math.radians(ang)
        for k in (12, 13):
            f.set(int(round(CX + k * math.cos(a))), int(round(CY + k * math.sin(a))), 'S' if k == 12 else 't')
    sticker(f, CX, CY - 3, 6.2)
    return f


def f2():
    f = PFrame()
    mass(f, puff_ring(15, 10.8, 2.7, rot=-80, seed=3, rs=(1.0, 0.7, 0.9)), PINK, 'd')
    sticker(f, CX, CY - 9, 6.4)
    sparkle(f, int(CX - 12), int(CY - 9), 2)
    sparkle(f, int(CX + 12), int(CY - 4), 1)
    sparkle(f, int(CX + 9), int(CY + 11), 1)
    return f


def f3():
    f = PFrame()
    rnd = random.Random(4)
    for i in range(9):
        a = math.radians(-70 + i * 40 + rnd.uniform(-8, 8))
        R = 13.0
        x, y = CX + R * math.cos(a), CY + R * math.sin(a) * 0.85
        mass(f, [(x, y, 1.7), (x + 1.2 * math.cos(a + 1.6), y + 1.0 * math.sin(a + 1.6), 1.1)],
             ('a', 'a', 'b', 'b', 'c'), 'b', outline='d')
    sticker(f, CX, CY - 12, 3.6, rim=True)
    sparkle(f, int(CX - 9), int(CY - 13), 1)
    sparkle(f, int(CX + 12), int(CY - 3), 1)
    f.set(int(CX - 14), int(CY + 4), 'S')
    f.set(int(CX + 6), int(CY + 13), 'S')
    return f


def pop_frames():
    return [fn().to_px() for fn in (f0, f1, f2, f3)]


if __name__ == '__main__':
    fr = pop_frames()
    for i, f in enumerate(fr):
        audit(f, 'pop %d' % i)
    save(hstack([zoom(f, 10, ARENA_GREEN, True) for f in fr], gap=10), WIP + 'pop_sheet.png')
    print('ok')
