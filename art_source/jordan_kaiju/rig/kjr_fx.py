"""The kaiju's effects (wave 1): puffs and stars for the grow / shrink, the stomp mark, the stomp
impact, the breath (beam body tile, mouth flare, end splash, mouth charge), the burn line's flames
and their dying embers, and the ground shadow. Colours: the kaiju's 16 and Jordan's 40 only.

Effects carry no keyline, except the pink puffs, which wear one like the funko summon's pop they
echo (funko_spawn_pop.png). Every function returns {pixel: key}; nothing writes a file.
"""
import math
import os
import random
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kj_common as K  # noqa: E402


def disc(cx, cy, r):
    out = set()
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                out.add((x, y))
    return out


def ell(cx, cy, rx, ry):
    out = set()
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0:
                out.add((x, y))
    return out


def ring_of(pix):
    out = set()
    for (x, y) in pix:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in pix:
                out.add(q)
    return out


#PUFFS AND STARS (the funko summon's pop, in the palette's pinks and golds)

def puff_cloud(circles, outline=True):
    """Pink puffs: a union of circles, lit upper left (Q), base P, shaded q lower right, keylined."""
    shape = set()
    for (cx, cy, r) in circles:
        shape |= disc(cx, cy, r)
    out = {}
    for (x, y) in shape:
        best = None
        for (cx, cy, r) in circles:
            d = math.hypot(x - cx, y - cy)
            if d <= r + 0.5 and (best is None or d / max(r, 1) < best[0]):
                best = (d / max(r, 1), (x - cx) / max(r, 1), (y - cy) / max(r, 1))
        _, nx, ny = best or (0, 0, 0)
        lam = -0.6 * nx - 0.7 * ny
        out[(x, y)] = 'Q' if lam > 0.35 else ('P' if lam > -0.3 else 'q')
    if outline:
        for q in ring_of(shape):
            out[q] = 'k'
    return out


STAR5 = [".O.", "OYO", ".O."]
STAR7 = ["...Y...", "..YOY..", "YYOOOYY", ".YOOOY.", "..OOO..", ".OO.OO.", ".O...O."]


def star(cx, cy, big=True):
    """The summon's gold star with a white rim (no keyline)."""
    rows = STAR7 if big else STAR5
    out = {}
    h = len(rows)
    w = len(rows[0])
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch != '.':
                out[(cx + c - w // 2, cy + r - h // 2)] = ch
    if big:
        for q in ring_of(set(out)):
            out.setdefault(q, 'W')
        for q, k in list(out.items()):
            if k == 'O' and (q[0] + q[1]) % 5 == 0:
                out[q] = 'o'
    return out


def sparkle(cx, cy, size=1):
    out = {(cx, cy): 'W'}
    for i in range(1, size + 1):
        k = 'Q' if i == size else 'W'
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            out[(cx + dx * i, cy + dy * i)] = k
    return out


def puffs_round(body_px, amount, seed, rmin, rmax, cover=0.55, stars=1, sparks=4, out_by=0.0):
    """A ring of puffs round a body's silhouette: `amount` 0..1 sets how many sit on its edge (and how
    far they cover it), plus gold stars and sparkles. Returns (fx pixels, keys)."""
    rnd = random.Random(seed)
    xs = [x for (x, y) in body_px]
    ys = [y for (x, y) in body_px]
    cx, cy = (min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0
    rx, ry = (max(xs) - min(xs)) / 2.0 + 2, (max(ys) - min(ys)) / 2.0 + 2
    n = max(0, int(round(4 + 14 * amount)))
    circles = []
    for i in range(n):
        a = 2 * math.pi * (i + rnd.random() * 0.6) / max(1, n)
        r = rmin + (rmax - rmin) * rnd.random() * (0.5 + 0.5 * amount)
        k = 1.0 - cover * amount * rnd.random()
        circles.append((cx + math.cos(a) * (rx * k + out_by), cy + math.sin(a) * (ry * k + out_by), r))
    out = puff_cloud(circles) if circles else {}
    for i in range(stars):
        a = rnd.random() * 2 * math.pi
        out.update(star(int(cx + math.cos(a) * rx * 0.8), int(cy - abs(math.sin(a)) * ry * 0.9), big=rmax > 5))
    for i in range(sparks):
        a = rnd.random() * 2 * math.pi
        out.update(sparkle(int(cx + math.cos(a) * (rx + 6)), int(cy + math.sin(a) * (ry + 6)), 1 if rmax < 6 else 2))
    return out


#STOMP MARK (112 x 80, pivot (56, 40), rim the (50, 35) ellipse)

MARK_W, MARK_H = 112, 80
MARK_PIVOT = (56, 40)
MARK_R = (50, 35)


def foot_print(scale=1.0, cx=56, cy=40):
    """A toed foot's shadow seen from above, pointing right: a broad heel, three toes, claw points."""
    s = scale
    shape = ell(cx - 6 * s, cy, 26 * s, 18 * s)
    for (tx, ty, r) in ((20, -12, 8), (25, 0, 9), (20, 12, 8)):
        shape |= ell(cx + tx * s, cy + ty * s, r * s * 1.2, r * s)
    for (tx, ty) in ((31, -13), (37, 0), (31, 13)):
        shape |= set(K.poly([(cx + (tx - 2) * s, cy + (ty - 3) * s), (cx + (tx + 6) * s, cy + ty * s),
                             (cx + (tx - 2) * s, cy + (ty + 3) * s)]))
    return shape


def stomp_mark(frame):
    """f0-1 tracking flicker, f2 high, f3 mid, f4 low, f5 landed."""
    out = {}
    scale, dens = {0: (0.62, 2), 1: (0.62, 2), 2: (0.66, 2), 3: (0.8, 3), 4: (0.94, 4), 5: (1.0, 5)}[frame]
    fp = foot_print(scale)
    for (x, y) in fp:
        if dens == 5:
            k = 'k'
        elif dens == 4:
            k = 'k' if (x + y) % 2 == 0 or (x % 2 == 0 and y % 2 == 0) else None
        elif dens == 3:
            k = 'k' if (x + y) % 2 == 0 else None
        else:
            ph = frame % 2
            k = 'k' if (x + y + ph) % 2 == 0 and (x // 2 + y // 2 + ph) % 2 == 0 else None
            if dens == 2 and (x + y) % 2 == 0 and frame >= 2:
                k = 'k'
        if k:
            out[(x, y)] = k
    rim = ell(MARK_PIVOT[0], MARK_PIVOT[1], MARK_R[0], MARK_R[1])
    edge = ring_of(rim)
    inner = {q for q in rim if any(n not in rim for n in ((q[0] + 1, q[1]), (q[0] - 1, q[1]),
                                                          (q[0], q[1] + 1), (q[0], q[1] - 1)))}
    for q in inner:
        out[q] = 'R' if q[1] > MARK_PIVOT[1] - 18 else 'T'
    for q in edge:
        out[q] = 'V'
    if frame in (0, 1):
        for i, (dx, dy) in enumerate(((-36, -24), (34, 26), (40, -20), (-42, 18))):
            if (i + frame) % 2 == 0:
                out.update(sparkle(MARK_PIVOT[0] + dx, MARK_PIVOT[1] + dy, 1))
    if frame == 5:
        for q in edge:
            out[q] = 'k'
        for q in inner:
            out[q] = 'V'
    return {q: k for q, k in out.items() if 0 <= q[0] < MARK_W and 0 <= q[1] < MARK_H}


#STOMP IMPACT (160 x 96, pivot (80, 48) on FOOT_IMPACT)

IMP_W, IMP_H = 160, 96
IMP_PIVOT = (80, 48)


def dust_puff(cx, cy, r, fade=0):
    """An ivory dust puff, lit upper left; fade 0..2 shifts it down the bone ramp."""
    ramp = ['5', '6', '7', 'W']
    out = {}
    for (x, y) in disc(cx, cy, r):
        nx, ny = (x - cx) / max(r, 1), (y - cy) / max(r, 1)
        lam = -0.6 * nx - 0.75 * ny
        i = 3 if lam > 0.35 else (2 if lam > -0.2 else 1)
        if math.hypot(nx, ny) > 0.8:
            i = min(i, 1 if lam < 0 else 2)
        out[(x, y)] = ramp[max(0, i - fade)]
    return out


CRACKS = [[(0, 0), (-14, -3), (-26, -2), (-40, -8)], [(0, 0), (-10, 6), (-18, 14), (-30, 16)],
          [(0, 0), (12, -5), (24, -6), (38, -12)], [(0, 0), (14, 6), (26, 9), (40, 8), (48, 14)],
          [(0, 0), (-3, 10), (-6, 22)], [(0, 0), (4, -9), (10, -16)], [(-26, -2), (-30, 6)],
          [(24, -6), (30, 0)], [(26, 9), (30, 18)]]


def cracks(cx, cy, grow=1.0):
    out = {}
    for path in CRACKS:
        pts = [(int(round(cx + x * grow)), int(round(cy + y * grow * 0.7))) for (x, y) in path]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            for q in K.line(x0, y0, x1, y1):
                out[q] = 'k'
                out.setdefault((q[0], q[1] + 1), '#')
    return out


def stomp_impact(frame):
    cx, cy = IMP_PIVOT
    out = {}
    if frame == 0:
        for (x, y) in ell(cx, cy, 34, 16):
            d = ((x - cx) / 34.0) ** 2 + ((y - cy) / 16.0) ** 2
            out[(x, y)] = 'X' if d < 0.3 else ('7' if d < 0.65 else '6')
        for a in range(0, 360, 30):
            r0, r1 = 20, 44 if a % 60 == 0 else 34
            p0 = (cx + math.cos(math.radians(a)) * r0, cy + math.sin(math.radians(a)) * r0 * 0.5)
            p1 = (cx + math.cos(math.radians(a)) * r1, cy + math.sin(math.radians(a)) * r1 * 0.5)
            for q in K.line(int(p0[0]), int(p0[1]), int(p1[0]), int(p1[1])):
                out.setdefault(q, '7')
        return clip(out, IMP_W, IMP_H)
    grow = {1: 0.55, 2: 0.8, 3: 0.95, 4: 1.0, 5: 1.0}[frame]
    out.update(cracks(cx, cy + 6, grow))
    if frame <= 4:
        rad = {1: (42, 20), 2: (58, 28), 3: (68, 34), 4: (74, 38)}[frame]
        size = {1: 9, 2: 9, 3: 8, 4: 6}[frame]
        fade = {1: 0, 2: 0, 3: 1, 4: 2}[frame]
        n = 16
        for i in range(n):
            a = 2 * math.pi * (i + 0.5 * (i % 2)) / n
            px_ = cx + math.cos(a) * rad[0]
            py_ = cy + 6 + math.sin(a) * rad[1]
            r = size - (i % 3)
            if frame == 4 and i % 2:
                continue
            for q, k in dust_puff(px_, py_ - r * 0.4, r, fade).items():
                out[q] = k
        if frame == 1:
            for (x, y) in ell(cx, cy + 4, 20, 9):
                out.setdefault((x, y), '7')
    return clip(out, IMP_W, IMP_H)


def clip(px, w, h):
    return {q: k for q, k in px.items() if 0 <= q[0] < w and 0 <= q[1] < h}


#THE BREATH

BEAM = 32


def beam_body(frame):
    """A 32x32 horizontal segment that tiles left-right; its waves and streaks scroll 8 px a frame."""
    out = {}
    sh = frame * 8
    for x in range(BEAM):
        u = (x - sh) % BEAM
        wob = math.sin(2 * math.pi * u / BEAM) * 1.4 + math.sin(4 * math.pi * u / BEAM + 1.0) * 0.6
        top, bot = 2.5 + wob, 29.5 - wob
        for y in range(BEAM):
            if y < top or y > bot:
                continue
            d = min(y - top, bot - y)
            if d < 1.2:
                k = '8' if (u + y) % 3 == 0 else 'I'
            elif d < 3.4:
                k = 'I' if d < 2.2 else 'J'
            elif d < 7.6:
                k = 'J' if d < 5.2 else 'K'
            elif d < 10.5:
                k = 'K'
            else:
                k = 'X'
            out[(x, y)] = k
        # streaks flowing along the core
        for (sy, ln, ph) in ((10, 6, 0), (21, 5, 13), (14, 4, 22)):
            if (u - ph) % BEAM < ln:
                q = (x, sy)
                if out.get(q) in ('K', 'J'):
                    out[q] = 'X'
            if (u - ph - 16) % BEAM < 3:
                q = (x, sy + 1)
                if out.get(q) == 'X':
                    out[q] = 'K'
    return out


FLARE = 48


def beam_mouth(frame):
    """The flare on the mouth, over the beam's root: a white-hot ball, rings, short rays; it pulses."""
    c = FLARE / 2.0 - 0.5
    out = {}
    pulse = [0, 1.5, 2.5, 1.0][frame]
    r_core, r1, r2, r3 = 6 + pulse * 0.5, 9 + pulse, 12 + pulse, 15 + pulse
    for y in range(FLARE):
        for x in range(FLARE):
            d = math.hypot(x - c, (y - c) * 1.08)
            if d <= r_core:
                k = 'X'
            elif d <= r1:
                k = 'K'
            elif d <= r2:
                k = 'J'
            elif d <= r3 and (x + y + frame) % 2 == 0:
                k = 'I'
            else:
                continue
            out[(x, y)] = k
    for i in range(8):
        a = math.radians(i * 45 + frame * 11)
        ln = (22 if i % 2 == 0 else 17) + pulse
        for t in range(int(r2), int(ln)):
            q = (int(round(c + math.cos(a) * t)), int(round(c + math.sin(a) * t)))
            out.setdefault(q, 'K' if t < ln - 4 else 'J')
    return clip(out, FLARE, FLARE)


def beam_end(frame):
    """Where the beam meets the rope: a splash fanning back toward the mouth, droplets thrown off."""
    c = FLARE / 2.0 - 0.5
    rnd = random.Random(31 + frame)
    out = {}
    pulse = [0, 1, 2, 1][frame]
    for y in range(FLARE):
        for x in range(FLARE):
            dx, dy = x - c - 4, (y - c)
            d = math.hypot(dx * 1.35, dy)
            if dx > 6:
                continue
            if d <= 7 + pulse:
                k = 'X'
            elif d <= 11 + pulse:
                k = 'K'
            elif d <= 15 + pulse:
                k = 'J'
            elif d <= 18 + pulse and (x + y) % 2 == 0:
                k = 'I'
            else:
                continue
            out[(x, y)] = k
    for i in range(10):
        a = math.radians(rnd.uniform(110, 250))
        t = rnd.uniform(16, 23)
        x, y = int(round(c + 4 + math.cos(a) * t)), int(round(c + math.sin(a) * t))
        out[(x, y)] = 'K'
        out[(x + 1, y)] = 'J'
    return clip(out, FLARE, FLARE)


CHG = 32


def mouth_charge(frame):
    """Light gathering on the mouth: motes drawn in from a ring, a ball growing at the centre."""
    c = CHG / 2.0 - 0.5
    out = {}
    ball = [0, 1.5, 3, 4.5, 6, 7.5][frame]
    rr = [15, 13, 11, 9, 8, 0][frame]
    for (x, y) in disc(c, c, ball):
        d = math.hypot(x - c, y - c)
        out[(x, y)] = 'X' if d < ball * 0.55 else ('K' if d < ball * 0.85 else 'J')
    if ball:
        for q in ring_of(set(out)):
            out.setdefault(q, 'I')
    if rr:
        for i in range(10):
            a = math.radians(i * 36 + frame * 14)
            r = rr + (i % 3) - 1
            q = (int(round(c + math.cos(a) * r)), int(round(c + math.sin(a) * r)))
            out[q] = 'K' if i % 2 else 'J'
            tail = (int(round(c + math.cos(a) * (r + 2))), int(round(c + math.sin(a) * (r + 2))))
            out.setdefault(tail, 'I')
    if frame == 5:
        for i in range(4):
            a = math.radians(45 + i * 90)
            for t in range(9, 14):
                out.setdefault((int(round(c + math.cos(a) * t)), int(round(c + math.sin(a) * t))), 'J')
    return clip(out, CHG, CHG)


FL_W, FL_H = 16, 24


def flame_shape(frame, height=1.0):
    """An upright blue flame, pivot bottom-centre; the tip sways with the frame."""
    out = {}
    sway = math.sin(frame * math.pi / 3.0) * 1.6
    H = 21 * height
    for y in range(FL_H):
        t = (FL_H - 1 - y) / max(1.0, H)              # 0 at the base, 1 at the tip
        if t > 1.0:
            continue
        w = 5.6 * math.sin(math.pi * min(1.0, 0.18 + t * 0.95)) * (1.0 - t * 0.55)
        cx = 7.5 + sway * t * t
        for x in range(FL_W):
            d = abs(x - cx)
            if d > w:
                continue
            rel = d / max(0.8, w)
            if t < 0.45 and rel < 0.45:
                k = 'X' if t < 0.3 else 'K'
            elif rel < 0.6 and t < 0.75:
                k = 'K' if t < 0.55 else 'J'
            elif rel < 0.85:
                k = 'J'
            else:
                k = 'I'
            if t > 0.85:
                k = 'I'
            out[(x, y)] = k
    # a lick that breaks off the tip every other frame
    if frame % 2 == 0 and height >= 0.8:
        lx = int(round(7.5 + sway * 1.3))
        out[(lx, FL_H - 1 - int(H) - 2)] = 'J'
        out[(lx, FL_H - 1 - int(H) - 3)] = 'I'
    return clip(out, FL_W, FL_H)


def burn_flame(frame):
    h = [1.0, 0.92, 0.86, 0.95, 1.0, 0.9][frame]
    return flame_shape(frame, h)


def burn_out(frame):
    if frame == 0:
        return flame_shape(1, 0.6)
    if frame == 1:
        return flame_shape(2, 0.35)
    if frame == 2:
        out = {}
        for (x, y) in ell(7.5, 21.5, 3.2, 1.8):
            out[(x, y)] = 'J'
        out[(7, 21)] = 'K'
        out[(8, 21)] = 'K'
        out[(7, 18)] = 'I'
        out[(8, 16)] = '8'
        return clip(out, FL_W, FL_H)
    out = {(7, 22): 'I', (8, 22): '8', (6, 22): '8', (8, 14): '8', (7, 11): '8'}
    return clip(out, FL_W, FL_H)


#GROUND SHADOW

SH_W, SH_H = 168, 32
SH_PIVOT = (84, 14)          # sits on the kaiju's FEET


def shadow():
    """The ground shadow under its feet and tail curl: solid black (the game sets its alpha)."""
    out = {}
    for q in ell(SH_PIVOT[0] + 2, SH_PIVOT[1] + 3, 74, 12.5):
        out[q] = 'k'
    return clip(out, SH_W, SH_H)
