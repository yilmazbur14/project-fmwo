"""Ground FIRE TRAIL patch left by beast Bixby's fire breath (displayed at 3x).
Frame 40x40 texels. Ground anchor (20, 31) = centre of the burning floor patch (Sprite2D offset (0, -11)).
Frames: 0-2 ignite, 3-6 burn loop, 7-9 burn-out. Optional scorch sheet: 2 frames of 40x40, same anchor.
Collision (solid barrier) rect: x 4..35, y 26..35 in frame texels = 32x10 centred on the anchor.

Style matches the approved breath (fire.py): flat colour bands on the beast fire ramp
W FFFFFF > L FFF7A0 > O FBF236 > o F58A38 > F DF7126 > Q AC3232 > r 6E1E22 (outer rim), no black outline,
single-pixel ember sparks. Smoke uses the beast smoke ramp (fx2). Alpha is 0/255 only.

Model: a burning bed on the floor (a rounded strip, superellipse 37x13 texels) + five flame tongues on a 6-texel
pitch. Placed 32 texels apart, neighbouring beds overlap by ~5 texels and the tongue pitch carries across the
seam; the bed's side tips have no dark rim, so a row reads as one continuous wall.
Flicker is periodic (noise scrolls one full period over the 4 burn frames) so the burn loop is seamless."""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lib
from lib import *
from pal import PALC, BLACK
import fx2 as FX

FW, FH = 40, 40
AX, AY = 20, 31                  # ground anchor (bed centre)
BED_RX, BED_RY = 18.5, 6.5       # bed spans x 2..38, y 25..37: a rounded strip, neighbours 32 apart overlap ~5 texels
BED_P = 4.0                       # superellipse exponent along x (flat-ish ends so neighbouring beds merge top to bottom)
BANDS = [(0.93, 'W'), (0.80, 'L'), (0.64, 'O'), (0.46, 'o'), (0.30, 'F'), (0.15, 'Q'), (0.0, 'r')]

# tongues: base x, base y (on the bed), half width, height above base, flicker phase, sway phase.
# Tongues sit on a 6-texel pitch; a neighbour 32 texels away continues the same pitch across the seam.
TONGUES = [
    (7.0, 32.0, 3.0, 14.0, 0.0, 1.1),
    (14.0, 30.5, 3.7, 20.0, 1.9, 2.6),
    (20.0, 31.5, 4.0, 23.5, 3.7, 0.4),
    (26.0, 30.5, 3.7, 18.5, 5.1, 3.9),
    (33.0, 32.0, 3.0, 15.0, 2.6, 5.2),
]


# ------------------------------------------------------------------ periodic value noise
def _hash(ix, iy, seed):
    h = (ix * 374761393 + iy * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def pnoise(x, y, seed, py):
    """value noise, periodic in y with period py lattice cells"""
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)
    a = _hash(ix, iy % py, seed)
    b = _hash(ix + 1, iy % py, seed)
    c = _hash(ix, (iy + 1) % py, seed)
    d = _hash(ix + 1, (iy + 1) % py, seed)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def flicker_noise(x, y, t, seed=7):
    """scrolls upward; one full period after 4 frames (t in frame units)"""
    return 0.65 * pnoise(x * 0.33, y * 0.22 + t * 0.75, seed, 3) + 0.35 * pnoise(x * 0.66, y * 0.44 + t * 1.5, seed + 3, 6)


# ------------------------------------------------------------------ fire field
def field(t, bed_scale=1.0, bed_heat=1.0, tongue_scale=1.0, heat=1.0, bed_rx=BED_RX, bed_ry=BED_RY, holes=0.0,
          wisp=True, seed=7):
    """intensity map {(x, y): I} for one frame. t = loop phase in frames (0..4)."""
    F = {}
    ph = 2 * math.pi * t / 4.0
    rx, ry = bed_rx * bed_scale, bed_ry * bed_scale
    for y in range(FH):
        for x in range(FW):
            px, py = x + 0.5, y + 0.5
            n = flicker_noise(px, py, t, seed) - 0.5
            best = 0.0
            # bed: glowing floor patch, hottest in the middle, ragged edge
            if rx > 0.5:
                d2 = abs((px - AX) / rx) ** BED_P + ((py - AY) / ry) ** 2
                if d2 <= 1.0 + n * 0.30:
                    b = (0.34 + 0.40 * (1 - min(1.0, d2))) * bed_heat
                    if holes and flicker_noise(px * 1.7, py * 1.7, 0.0, seed + 11) < holes:
                        b *= 0.45
                    best = max(best, b)
            # tongues: hottest at the base centre, cooling to a red tip
            for (bx, by, hw, h, fph, sph) in TONGUES:
                hh = h * tongue_scale * (1.0 + 0.13 * math.sin(ph + fph)) * (1.0 + 0.10 * n)
                if hh < 1.0:
                    continue
                u = (by - py) / hh
                if u < -0.3 or u > 1.0:
                    continue
                sway = 1.6 * math.sin(ph + sph) * max(0.0, u) ** 1.4
                cx = bx + sway
                if u >= 0:
                    w = hw * (1.0 - u) ** 0.62 * (1.0 + 0.22 * n)
                else:
                    w = hw * (1.0 + u * 1.5)
                if w <= 0.35:
                    continue
                dx = abs(px - cx) / w
                if dx >= 1.0:
                    continue
                v = 0.90 * (1.0 - max(0.0, u) * 0.86) * (1.0 - dx * dx * 0.62)
                best = max(best, v)
            # detached flame lick above a tall tongue at the top of its flicker
            if wisp and tongue_scale > 0.7:
                for (bx, by, hw, h, fph, sph) in TONGUES[1:4]:
                    s_ = math.sin(ph + fph)
                    if s_ > 0.6:
                        top = by - h * tongue_scale * (1.0 + 0.13 * s_)
                        wx = bx + 1.6 * math.sin(ph + sph) + 0.5
                        wy = max(4.2, top - 3.0)
                        dd = ((px - wx) / 1.7) ** 2 + ((py - wy) / 2.8) ** 2
                        if dd < 1.0:
                            best = max(best, 0.40 * (1 - dd) + 0.12)
            if best > 0:
                I = best * heat + n * 0.14
                if I > 0.05:
                    F[(x, y)] = I
    return F


def paint_field(F):
    lib.set_size(FW, FH)
    cv = Canvas(FW, FH)
    mask = set(F.keys())
    # remove isolated pixels / 1-px spurs
    for _ in range(2):
        kill = [q for q in mask if sum(((q[0] + dx, q[1] + dy) in mask) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) <= 1]
        for q in kill:
            mask.discard(q)
    for q in mask:
        I = F[q]
        for th, ch in BANDS:
            if I >= th:
                cv.put(q[0], q[1], PALC[ch])
                break
    # smooth single-pixel band islands (a pixel whose 4 neighbours all share another colour takes that colour)
    for _ in range(2):
        chg = []
        for (x, y) in mask:
            c = cv.get(x, y)
            nb = [cv.get(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            nb = [p for p in nb if p is not None]
            if len(nb) == 4 and c not in nb and nb.count(nb[0]) == 4:
                chg.append((x, y, nb[0]))
        for x, y, c in chg:
            cv.put(x, y, c)
    # dark red rim, except on the side-facing tips of the bed band (y >= 27): those are where a neighbouring patch
    # overlaps, so leaving them rimless makes a row of patches read as one unbroken bed of fire
    for (x, y) in edge(mask):
        if y >= 27:
            up = (x, y - 1) in mask
            down = (x, y + 1) in mask
            side_open = (x - 1, y) not in mask or (x + 1, y) not in mask
            if up and down and side_open:
                continue
        cv.put(x, y, PALC['r'])
    return cv, mask


def sparks(cv, pts):
    for (x, y, ch) in pts:
        if 0 <= x < FW and 0 <= y < FH and cv.get(x, y) is None:
            cv.put(x, y, PALC[ch])


# rising sparks for the burn loop: each spark climbs 4 texels per frame and wraps (loops over 4 frames)
LOOP_SPARKS = [(9, 20, 'O'), (18, 9, 'L'), (29, 14, 'o'), (24, 3, 'O'), (4, 15, 'o'), (35, 22, 'O')]


def loop_sparks(t):
    out = []
    for k, (x, y0, ch) in enumerate(LOOP_SPARKS):
        y = y0 - (t * 4 + k) % 16 + 4
        sway = int(round(math.sin((t + k) * 1.6)))
        out.append((x + sway, max(1, y), ch))
    return out


# ------------------------------------------------------------------ frames
def ignite(k):
    lib.set_size(FW, FH)
    smoke = Canvas(FW, FH)
    if k == 0:
        # embers land and catch: a bright flash on the floor, sparks scattered over the footprint
        F = field(0.0, bed_scale=0.42, bed_heat=1.12, tongue_scale=0.20, heat=1.08, wisp=False)
        cv, m = paint_field(F)
        sparks(cv, [(5, 30, 'O'), (35, 32, 'o'), (10, 36, 'F'), (30, 26, 'O'), (15, 24, 'L'), (26, 36, 'o'),
                    (20, 19, 'W'), (13, 21, 'O'), (27, 20, 'o'), (2, 33, 'F'), (37, 29, 'F')])
    elif k == 1:
        F = field(1.0, bed_scale=0.74, bed_heat=1.08, tongue_scale=0.48, heat=1.05, wisp=False)
        cv, m = paint_field(F)
        sparks(cv, [(3, 28, 'O'), (37, 30, 'O'), (11, 12, 'L'), (29, 10, 'O'), (20, 6, 'o'), (6, 18, 'o'), (34, 17, 'F')])
    else:
        F = field(2.0, bed_scale=0.94, bed_heat=1.05, tongue_scale=0.86, heat=1.06)
        cv, m = paint_field(F)
        sparks(cv, [(4, 14, 'O'), (36, 12, 'L'), (16, 3, 'O'), (27, 2, 'o'), (9, 7, 'o')])
    return cv, smoke


def burn(t):
    lib.set_size(FW, FH)
    F = field(float(t))
    cv, m = paint_field(F)
    sparks(cv, loop_sparks(t))
    return cv, Canvas(FW, FH)


def burnout(k):
    lib.set_size(FW, FH)
    smoke = Canvas(FW, FH)
    if k == 0:
        F = field(0.5, bed_scale=0.97, bed_heat=0.86, tongue_scale=0.55, heat=0.86, wisp=False)
        cv, m = paint_field(F)
        FX.puff(smoke, 17, 8, 2.2, seed=31)
        FX.puff(smoke, 25, 11, 1.8, seed=32)
        sparks(cv, [(8, 13, 'o'), (31, 15, 'F'), (21, 4, 'o')])
    elif k == 1:
        F = field(1.5, bed_scale=0.9, bed_heat=0.66, tongue_scale=0.24, heat=0.78, holes=0.42, wisp=False)
        cv, m = paint_field(F)
        FX.puff(smoke, 14, 13, 3.0, seed=41)
        FX.puff(smoke, 25, 8, 3.4, seed=42)
        FX.puff(smoke, 20, 19, 2.0, seed=43)
        sparks(cv, [(10, 18, 'F'), (30, 16, 'o'), (6, 24, 'F')])
    else:
        # nothing but a charred bed dotted with dying embers, smoke drifting off
        lib.set_size(FW, FH)
        cv = Canvas(FW, FH)
        bed = ell(AX, AY + 1, BED_RX * 0.86, BED_RY * 0.72)
        for (x, y) in bed:
            n = flicker_noise(x + 0.5, y + 0.5, 0.0, 19)
            cv.put(x, y, PALC['S'] if n > 0.45 else PALC['T'])
        for (x, y) in edge(bed):
            cv.put(x, y, PALC['r'])
        for (x, y, ch) in ((12, 31, 'F'), (13, 31, 'o'), (19, 33, 'F'), (24, 30, 'o'), (25, 30, 'F'), (29, 33, 'F'), (8, 33, 'Q'), (32, 31, 'Q')):
            cv.put(x, y, PALC[ch])
        FX.puff(smoke, 13, 10, 3.2, seed=51)
        FX.puff(smoke, 26, 5, 2.8, seed=52)
        FX.puff(smoke, 20, 18, 2.4, seed=53)
    return cv, smoke


def scorch(k):
    """charred floor mark left after burn-out (0: still smouldering, 1: cold). Same frame and anchor as the patch."""
    lib.set_size(FW, FH)
    cv = Canvas(FW, FH)
    rx, ry = BED_RX * 0.92, BED_RY * 0.9
    m = set()
    for y in range(FH):
        for x in range(FW):
            d = abs((x + 0.5 - AX) / rx) ** 3.0 + ((y + 0.5 - AY) / ry) ** 2
            n = flicker_noise(x * 1.6 + 0.5, y * 1.6 + 0.5, 0.0, 23) - 0.5
            if d <= 1.0 + n * 0.55:
                m.add((x, y))
    for _ in range(2):
        m = {q for q in m if sum(((q[0] + dx, q[1] + dy) in m) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) >= 2}
    # fill pinholes
    m |= {(x, y) for y in range(FH) for x in range(FW)
          if (x, y) not in m and sum(((x + dx, y + dy) in m) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) >= 3}
    for (x, y) in m:
        d = abs((x + 0.5 - AX) / rx) ** 3.0 + ((y + 0.5 - AY) / ry) ** 2
        n = flicker_noise(x * 2.3 + 0.5, y * 2.3 + 0.5, 0.0, 29)
        if d < 0.40:
            c = PALC['Z'] if n < 0.62 else PALC['J']
        elif d < 0.85:
            c = PALC['J'] if n < 0.58 else PALC['D']
        else:
            c = PALC['D'] if n < 0.66 else PALC['B']
        cv.put(x, y, c)
    # sparse ash specks just outside the mark (every other texel so they read as soot, not noise)
    for (x, y) in outer_edge(m):
        if (x + y) % 2 == 0 and flicker_noise(x * 3.1 + 0.5, y * 3.1 + 0.5, 0.0, 37) > 0.58:
            cv.put(x, y, PALC['D'])
    if k == 0:
        for (x, y, ch) in ((13, 31, 'F'), (14, 31, 'r'), (21, 33, 'o'), (26, 30, 'F'), (9, 32, 'r'), (30, 32, 'r'), (18, 29, 'r')):
            if (x, y) in m:
                cv.put(x, y, PALC[ch])
    return cv


FRAMES = [('ignite', 0), ('ignite', 1), ('ignite', 2), ('burn', 0), ('burn', 1), ('burn', 2), ('burn', 3),
          ('out', 0), ('out', 1), ('out', 2)]


def frame(kind, k):
    if kind == 'ignite':
        return ignite(k)
    if kind == 'burn':
        return burn(k)
    return burnout(k)


def all_frames():
    return [frame(kind, k) for kind, k in FRAMES]


if __name__ == '__main__':
    import anim_common as AC
    fr = all_frames()
    s = Canvas(FW * len(fr) + 4 * len(fr), FH)
    for i, (fire, smoke) in enumerate(fr):
        s.blit(fire, i * (FW + 4), 0)
        s.blit(smoke, i * (FW + 4), 0)
    AC.preview(s, 'trail_frames_6x.png', 6)
    print('ok')
