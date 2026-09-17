"""Extra layers for the SUPERCHARGED uppercut contact, drawn on top of uppercut_impact_super.
  super_impact_rays : 5 frames of 640x360, centre (320, 180) - radial speed lines sweeping outward,
                      gold into magenta. Screen-space overlay, drawn at 3x (fills 1920x1080).
  super_impact_ring : 6 frames of 192x96, pivot (96, 48) - a flattened blast ring rolling out along
                      the floor, white-hot edge into gold and magenta.
DB32 only, alpha 0/255. Both are authored for NORMAL blending (they carry their own colour ramp)."""
import sys
sys.dont_write_bytecode = True
import math
from dh_common import *

# ------------------------------------------------------------------ radial speed lines (640x360)
RW, RH = 640, 360
RCX, RCY = 320, 180
RAY_DURATIONS_MS = [30, 40, 50, 60, 70]

# (angle, half width at the inner end, half width at the outer end, kind) - jittered so it never
# reads as a mechanical fan; 'big' lines carry the colour, 'thin' ones fill the gaps
RAYS = []
_seed = 12345


def _rnd():
    global _seed
    _seed = (1103515245 * _seed + 12345) % 2147483648
    return _seed / 2147483648.0


for _k in range(12):
    _a = _k * (360.0 / 12) + (_rnd() - 0.5) * 14.0
    RAYS.append((_a, 1.1 + _rnd() * 1.1, 2.4 + _rnd() * 2.6, 'big'))
for _k in range(10):
    _a = _k * (360.0 / 10) + 16.0 + (_rnd() - 0.5) * 12.0
    RAYS.append((_a, 0.6, 1.1 + _rnd() * 1.0, 'thin'))

# colour ramp along a line, from its inner end outward
RAMP_BIG = [['W', 'W', 'Y', 'O', 'm', 'V'],
            ['W', 'Y', 'O', 'm', 'V', 'p'],
            ['Y', 'O', 'm', 'm', 'V', 'p'],
            ['O', 'm', 'V', 'V', 'p', 'p'],
            ['m', 'V', 'V', 'p', 'p', 'p']]
RAMP_THIN = [['Y', 'O', 'm'], ['Y', 'm', 'V'], ['O', 'm', 'V'], ['m', 'V', 'V'], ['V', 'V', 'p']]
R0 = [58, 112, 168, 224, 282]         # inner radius per frame: the lines fly outward,
                                      # leaving the burst and the fighters clear in the middle
WIDTH_SCALE = [1.0, 0.8, 0.6, 0.45, 0.3]
KEEP = [1.0, 0.9, 0.7, 0.5, 0.35]     # fraction of lines still alive


def ray_frame(f):
    c = Canvas(RW, RH)
    r0 = R0[f]
    r1 = 430.0                                     # past the corner (367) so lines never end on screen
    for i, (ang, hw0, hw1, kind) in enumerate(RAYS):
        if (i * 0.37) % 1.0 > KEEP[f]:
            continue
        ramp = (RAMP_BIG if kind == 'big' else RAMP_THIN)[f]
        a = math.radians(ang)
        ux, uy = math.cos(a), math.sin(a)
        vx, vy = -uy, ux
        w0 = hw0 * WIDTH_SCALE[f]
        w1 = hw1 * WIDTH_SCALE[f]
        steps = int(r1 - r0)
        for s in range(steps):
            r = r0 + s
            t = s / float(steps)
            hw = w0 + (w1 - w0) * t
            fb = t * (len(ramp) - 1)
            b = int(fb)
            frac = fb - b
            px, py = RCX + ux * r, RCY + uy * r
            if px < -8 or px > RW + 8 or py < -8 or py > RH + 8:
                break
            n = int(hw) + 1
            for k in range(-n, n + 1):
                if abs(k) > hw:
                    continue
                x, y = int(round(px + vx * k)), int(round(py + vy * k))
                # checker dither across each band boundary so the ramp reads smooth, not striped
                bb = b + 1 if (frac > 0.5 and (x + y) % 2 == 0) or frac > 0.85 else b
                col = ramp[min(len(ramp) - 1, bb)]
                if hw >= 2.2 and abs(k) > hw - 1.0 and col in ('W', 'Y', 'O'):
                    col = {'W': 'Y', 'Y': 'O', 'O': 'm'}[col]      # warm edge instead of a hard outline
                c.set(x, y, C[col])
    return c


def super_impact_rays():
    return [ray_frame(f) for f in range(5)]


# ------------------------------------------------------------------ flattened blast ring (192x96)
GW, GH = 192, 96
GCX, GCY = 96, 48
RING_DURATIONS_MS = [40, 50, 60, 70, 80, 90]
# (rx, ry, band thickness in px, colours from the inner edge outward, gap angles)
RING_STEPS = [
    (22, 11, 4.5, ['W', 'W', 'Y', 'O'], []),
    (42, 21, 4.5, ['W', 'Y', 'O', 'm'], []),
    (60, 30, 4.0, ['W', 'Y', 'm', 'V'], [(84, 96), (264, 276)]),
    (76, 38, 3.0, ['Y', 'O', 'm', 'V'], [(80, 100), (260, 280)]),
    (88, 44, 2.0, ['O', 'm', 'V'], [(72, 108), (252, 288), (350, 10)]),
    (95, 47, 1.0, ['m', 'V'], [(60, 120), (240, 300), (340, 20), (160, 200)]),
]


def ring_frame(f):
    rx, ry, th, cols, gaps = RING_STEPS[f]
    c = Canvas(GW, GH)
    for y in range(GH):
        for x in range(GW):
            dx, dy = x - GCX + 0.5, y - GCY + 0.5
            e = math.hypot(dx / rx, dy / ry)
            if e > 1.0 or e < 1e-6:
                continue
            # perpendicular distance inside the outer edge, in px (keeps the band an even thickness
            # all the way round the ellipse)
            g = math.hypot(dx / (rx * rx), dy / (ry * ry)) / e
            d = (1.0 - e) / max(g, 1e-6)
            if d > th:
                continue
            a = math.degrees(math.atan2(dy, dx)) % 360
            if any((a0 <= a <= a1) if a0 <= a1 else (a >= a0 or a <= a1) for a0, a1 in gaps):
                continue
            k = int(d / th * len(cols))
            c.set(x, y, C[cols[min(len(cols) - 1, k)]])
    # sparks riding the front edge
    if f in (1, 2, 3):
        for ang in (-150, -30, 20, 200, 160, 340):
            a = math.radians(ang)
            x = int(round(GCX + rx * math.cos(a)))
            y = int(round(GCY + ry * math.sin(a)))
            c.set(x, y, C['W'])
            c.set(x, y - 1, C['Y' if f < 3 else 'm'])
    return c


def super_impact_ring():
    return [ring_frame(f) for f in range(6)]


def build():
    return {'super_impact_rays': super_impact_rays(), 'super_impact_ring': super_impact_ring()}


if __name__ == '__main__':
    A = build()
    for name, frames in A.items():
        s = strip(frames)
        cover = [sum(1 for row in f.p for v in row if v) * 100.0 / (f.w * f.h) for f in frames]
        print(name, s.w, s.h, 'non-DB32', s.colours() - DB32, 'coverage %', [round(c, 1) for c in cover])
    save_zoom(strip(A['super_impact_ring']), work('super_impact_ring_3x.png'), 3, bg=(136, 180, 99), grid=(GW, GH))
    for i, f in enumerate(A['super_impact_rays']):
        save_zoom(f, work('rays_f%d.png' % i), 1, bg=(136, 180, 99))
