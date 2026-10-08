"""Wave-2 effects: the roar's sound arcs, the spin's smear streaks, the tail's floor swoosh (16 angles),
and the 96x96 pink-gold puff. Same palette and language as wave 1 (kjr_fx)."""
import math
import os
import random
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kj_common as K  # noqa: E402
import kjr_fx as FX  # noqa: E402


def roar_arcs(mouth, direction, frame, existing):
    """Three broken sound arcs fanning out of the open mouth (ivory and white, no keyline); they step
    outward frame to frame. Only drawn where nothing else is."""
    ox, oy = mouth
    a0 = math.atan2(direction[1], direction[0])
    out = {}
    base = [7, 12, 17][frame % 3] if frame else 6
    for j, r in enumerate((base, base + 8, base + 16)):
        span = math.radians(28 + 4 * j)
        n = int(r * span * 2) + 2
        for i in range(n):
            a = a0 - span + 2 * span * i / max(1, n - 1)
            if (i // 3 + j) % 3 == 2:
                continue                                      # broken into dashes
            q = (int(round(ox + math.cos(a) * r)), int(round(oy + math.sin(a) * r)))
            if q not in existing:
                out[q] = 'W' if j == 0 else ('7' if j == 1 else '6')
    return out


def smear(px, direction, seed=3):
    """Motion streaks off the trailing side of a turning body: rows of hide tone running out of its
    silhouette and breaking up (no keyline)."""
    rnd = random.Random(seed)
    xs = [x for (x, y) in px]
    ys = [y for (x, y) in px]
    out = {}
    for y in range(min(ys) + 4, max(ys) - 2, 4):
        row = [x for (x, yy) in px if yy == y]
        if not row:
            continue
        edge = max(row) if direction > 0 else min(row)
        ln = rnd.randint(8, 20)
        for i in range(1, ln + 1):
            x = edge + i * direction
            t = i / float(ln)
            if t > 0.55 and (i % 2):
                continue
            k = '+' if t < 0.25 else ('@' if t < 0.5 else ('&' if t < 0.8 else '%'))
            out[(x, y)] = k
            if t < 0.4 and (x, y + 1) not in px:
                out[(x, y + 1)] = '&'
    return out


def tail_smear(feet, sc, direction, seed=5):
    """The tail whipping round in front of the feet: a dithered arc of hide tones on the mat."""
    cx, cy = feet
    out = {}
    a, b = 70 * sc / 1.45, 16 * sc / 1.45
    for i in range(160):
        t = i / 159.0
        ang = math.radians(20 + 140 * t) if direction > 0 else math.radians(160 - 140 * t)
        for w in range(-2, 3):
            x = int(round(cx + math.cos(ang) * a))
            y = int(round(cy + 6 + math.sin(ang) * b + w))
            k = '@' if abs(w) < 1 else ('&' if abs(w) < 2 else '%')
            if (x + y + i) % 3 == 0 and abs(w) == 2:
                continue
            out[(x, y)] = k
    return out


#THE TAIL'S FLOOR SWOOSH: 16 angles, 22.5 degrees apart

ARC_W, ARC_H = 176, 80
ARC_A, ARC_B = 520 / 3.0, 230 / 3.0       # the band's outer ellipse, texels round the kaiju's FEET
ARC_SPAN = 42.0


def tail_arc(k):
    """Frame k: the swoosh's leading edge at k * 22.5 degrees round the feet (0 = screen right, 90 =
    toward the camera, clockwise), its trail behind it. Gold and white, additive. Returns (pixels,
    pivot): the pivot is the ellipse centre (the kaiju's FEET) in this frame's texels."""
    th = k * 22.5
    pix = {}
    R = int(ARC_A) + 2
    for dy in range(-int(ARC_B) - 2, int(ARC_B) + 3):
        for dx in range(-R, R + 1):
            u, v = dx / ARC_A, dy / ARC_B
            r = math.hypot(u, v)
            if r > 1.0 or r < 0.22:
                continue
            phi = math.degrees(math.atan2(v, u)) % 360.0
            back = (th - phi) % 360.0                       # degrees behind the leading edge
            if back > ARC_SPAN:
                continue
            t = 1.0 - back / ARC_SPAN                       # 1 at the leading edge
            s = (r - 0.22) / 0.78                           # 1 at the outer rim
            s_in = 0.6 + 0.32 * (1.0 - t)                   # the band tapers toward its trail
            c = None
            if s >= s_in:
                mid, half = (s_in + 1.0) / 2.0, (1.0 - s_in) / 2.0
                head = 7.0                                  # a rounded leading edge, degrees
                if back < head and ((s - mid) / half) ** 2 + ((head - back) / head) ** 2 > 1.0:
                    c = None
                elif t > 0.88:
                    c = 'W' if abs(s - mid) < half * 0.55 else 'Y'
                elif t > 0.62:
                    c = 'Y' if abs(s - mid) < half * 0.45 else 'O'
                elif t > 0.32:
                    c = 'O' if (dx + dy) % 2 == 0 or t > 0.47 else None
                else:
                    c = 'o' if (dx + dy) % 2 == 0 and (dx // 2 + dy) % 3 else None
            else:                                           # the inner sweep: sparse streaks
                lane = int(s * 14) % 3 == 0
                c = ('O' if t > 0.6 else 'o') if lane and (dx + dy) % 2 == 0 and t > 0.25 else None
            if c:
                pix[(dx, dy)] = c
    xs = [x for (x, y) in pix]
    ys = [y for (x, y) in pix]
    cx, cy = (min(xs) + max(xs)) // 2, (min(ys) + max(ys)) // 2
    x0, y0 = cx - ARC_W // 2, cy - ARC_H // 2
    out = {(x - x0, y - y0): c for (x, y), c in pix.items() if 0 <= x - x0 < ARC_W and 0 <= y - y0 < ARC_H}
    lost = len(pix) - len(out)
    return out, (-x0, -y0), lost


#THE PUFF (96 x 96, the funko pop's language at the kaiju's scale)

PUFF = 96


def star_poly(cx, cy, r):
    pts = []
    for i in range(10):
        a = math.radians(-90 + i * 36)
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    shape = K.poly(pts)
    out = {}
    for (x, y) in shape:
        lam = -(x - cx) * 0.6 - (y - cy) * 0.8
        out[(x, y)] = 'Y' if lam > r * 0.25 else ('O' if lam > -r * 0.35 else 'o')
    for q in FX.ring_of(shape):
        out[q] = 'W'
    return out


def puff96(frame):
    c = PUFF / 2.0
    rnd = random.Random(90 + frame)
    out = {}
    if frame == 0:
        for (x, y) in FX.disc(c, c, 7):
            out[(x, y)] = 'W'
        for q in FX.ring_of(set(out)):
            out[q] = 'Q'
        circles = [(c + math.cos(a) * 11, c + math.sin(a) * 11, 4) for a in (0.4, 2.0, 3.6, 5.2)]
        cl = FX.puff_cloud(circles)
        for q, k in cl.items():
            out.setdefault(q, k)
        for d in ((-16, -14), (15, -16), (17, 12)):
            out.update(FX.sparkle(int(c + d[0]), int(c + d[1]), 2))
        return out
    ring, rmin, rmax, n, hole = {1: (14, 9, 12, 9, False), 2: (20, 10, 13, 11, False), 3: (27, 8, 10, 13, True),
                                 4: (33, 5, 7, 12, True), 5: (37, 3, 4, 10, True)}[frame]
    circles = []
    for i in range(n):
        a = 2 * math.pi * i / n + rnd.random() * 0.3
        circles.append((c + math.cos(a) * ring, c + 4 + math.sin(a) * ring * 0.9, rnd.uniform(rmin, rmax)))
    if not hole:
        circles.append((c, c + 4, ring * 0.9))
    out.update(FX.puff_cloud(circles))
    star_at = {1: (c, c - 4, 9), 2: (c, c - 22, 12), 3: (c, c - 30, 11), 4: (c, c - 36, 9), 5: (c, c - 39, 6)}[frame]
    out.update(star_poly(*star_at))
    for i in range({1: 3, 2: 4, 3: 6, 4: 7, 5: 6}[frame]):
        a = rnd.random() * 2 * math.pi
        rr = ring + rmax + 4 + rnd.random() * 6
        out.update(FX.sparkle(int(c + math.cos(a) * rr), int(c + 4 + math.sin(a) * rr * 0.9), 1 if frame == 5 else 2))
    out = {q: k for q, k in out.items() if 0 <= q[0] < PUFF and 0 <= q[1] < PUFF}
    for y in range(PUFF):                       # pinholes between puffs take the puffs' keyline
        for x in range(PUFF):
            if (x, y) not in out and all(q in out for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
                out[(x, y)] = 'k'
    return out
