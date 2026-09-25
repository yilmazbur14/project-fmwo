"""matt_trueshot_glow.png: the gold glow gathering at Matt's mouth during a Trueshot charge. 6 frames of
32x32, one strip:
  frames 0-3   the glow growing over the 0.55 s before the lock (about 0.14 s each)
  frame 4      the lock flash: white-hot
  frames 4-5   alternate at 0.06 s from the lock until the release (5 is the gold beat of the strobe)
The pivot is the frame centre (16, 16): put it on the mouth texel. It is symmetric, so it never flips.

In the Trueshot gold (the wave's ramp): a white-hot core, #FFF3A8 and #FFCB3C rings and an #F2A51E rim,
with 1-texel rays that turn a sixteenth of a circle per frame and grow with the ball, so it reads as
light gathering rather than a static coin. The lock flash is the same ball blown out to white with long
white rays and a thin ring; frame 5 is its gold counterpart at the same size, so the strobe pulses in
place. No keyline, no partial alpha.
"""
import math

import mfx_pal as pal

W = H = 32
CX = CY = 16.0
FRAME_SIZE = (32, 32)
NOTE = '6 frames: f0-3 grow over 0.55 s, f4 lock flash, then f4/f5 alternate at 0.06 s'

# Per frame: ball radius, core/ring/rim keys by fraction of the radius, ray count, ray length, ray keys,
# ray rotation (degrees), outer ring (radius, key) or None.
SPEC = [
    dict(r=2.6, bands=[(0.45, 'H'), (0.8, 'Y'), (9, 'G')], rays=4, ray=4.6, ray_keys='GO', rot=45.0,
         ring=None),
    dict(r=3.7, bands=[(0.4, 'H'), (0.68, 'Y'), (0.9, 'G'), (9, 'O')], rays=4, ray=6.8, ray_keys='YGO',
         rot=0.0, ring=None),
    dict(r=4.8, bands=[(0.38, 'H'), (0.62, 'Y'), (0.84, 'G'), (9, 'O')], rays=8, ray=8.6, ray_keys='YGO',
         rot=22.5, ring=None),
    dict(r=5.9, bands=[(0.36, 'H'), (0.6, 'Y'), (0.82, 'G'), (9, 'O')], rays=8, ray=10.8, ray_keys='YGGO',
         rot=0.0, ring=None),
    # the lock flash: blown out to white, long white rays through a thin ring, a reticle
    dict(r=6.6, bands=[(0.62, 'H'), (0.86, 'Y'), (9, 'G')], rays=8, ray=14.0, ray_keys='HHYYG', rot=0.0,
         ring=(10.5, 'Y')),
    # the strobe's gold beat, rays turned a sixteenth so the pair twinkles in place
    dict(r=6.6, bands=[(0.34, 'H'), (0.58, 'Y'), (0.82, 'G'), (9, 'O')], rays=8, ray=13.0,
         ray_keys='YGGOA', rot=22.5, ring=(10.5, 'O')),
]


def ball(g, spec):
    r = spec['r']
    for y in range(H):
        for x in range(W):
            d = math.hypot(x + 0.5 - CX, y + 0.5 - CY)
            if d <= r:
                q = d / r
                for edge, k in spec['bands']:
                    if q <= edge:
                        g[y][x] = k
                        break


def line_texels(a_deg, r0, r1):
    """Texels along a ray from radius r0 to r1 at angle a, one per step, with L-corners removed."""
    a = math.radians(a_deg)
    pts = []
    s = r0
    while s <= r1:
        p = (int(math.floor(CX + math.cos(a) * s)), int(math.floor(CY + math.sin(a) * s)))
        if not pts or pts[-1][0] != p:
            pts.append((p, s))
        s += 0.1
    out = list(pts)
    i = 1
    while i < len(out) - 1:
        (ax, ay), (bx, by), (cx, cy) = out[i - 1][0], out[i][0], out[i + 1][0]
        if abs(ax - cx) == 1 and abs(ay - cy) == 1 and (ax == bx or ay == by):
            del out[i]
        else:
            i += 1
    return out


def rays(g, spec):
    n = spec['rays']
    keys = spec['ray_keys']
    for i in range(n):
        a = spec['rot'] + 360.0 * i / n
        length = spec['ray'] * (1.0 if i % 2 == 0 or n == 4 else 0.72)     # alternate long and short
        for (x, y), s in line_texels(a, spec['r'] - 0.5, length):
            if g[y][x] != '.':
                continue
            t = (s - spec['r']) / max(0.5, length - spec['r'])
            k = keys[min(len(keys) - 1, int(t * len(keys)))]
            pal.put(g, x, y, k)


def circle_texels(rr):
    """A clean 1-texel ring of radius rr round the frame centre (a texel corner): for each column offset
    up to the 45 degree point, the row whose centre is nearest the circle, mirrored 8 ways."""
    pts = set()
    dx = 0.5
    while dx <= rr / math.sqrt(2) + 0.5:
        dy = math.floor(math.sqrt(max(0.0, rr * rr - dx * dx))) + 0.5
        if dy < dx:
            break
        for sx, sy in ((dx, dy), (dy, dx)):
            for mx in (1, -1):
                for my in (1, -1):
                    pts.add((int(math.floor(CX + mx * sx)), int(math.floor(CY + my * sy))))
        dx += 1.0
    return pts


def ring(g, spec):
    if not spec['ring']:
        return
    rr, k = spec['ring']
    for (x, y) in circle_texels(rr):
        if 0 <= x < W and 0 <= y < H and g[y][x] == '.':
            g[y][x] = k


def frame(i):
    spec = SPEC[i]
    g = pal.blank(W, H)
    ball(g, spec)
    rays(g, spec)
    ring(g, spec)
    return pal.rows(g)


def frames():
    return [frame(i) for i in range(6)]
