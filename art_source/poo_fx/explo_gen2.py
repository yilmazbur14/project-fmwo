"""POO EXPLOSION v2: organic splats (lumpy core + tapered tendrils + bulb droplets) with
height-field directional shading, cloud clusters with crescent shading, smooth stink lines."""
import math
import sys
import fxpng
from explo_gen import (W, H, FLOOR, PAL, LIGHT, Frame, disc, puff_tones, chunk_tones, star_tones,
                       to_px, bbox, snap)


# ------------------------------------------------------------------ shape helpers
def capsule(x0, y0, x1, y1, r0, r1):
    """Tapered capsule from (x0,y0) radius r0 to (x1,y1) radius r1."""
    pts = set()
    L = math.hypot(x1 - x0, y1 - y0)
    steps = max(2, int(L * 3))
    for i in range(steps + 1):
        t = i / steps
        pts |= disc(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, r0 + (r1 - r0) * t)
    return pts


def lumpy_core(cx, cy, r0, sy=1.0, wob=((3, 0.10, 0.4), (5, 0.07, 1.9), (7, 0.05, 3.1))):
    pts = set()
    reach = r0 * 1.4 + 2
    for y in range(int(cy - reach) - 1, int(cy + reach) + 2):
        for x in range(int(cx - reach) - 1, int(cx + reach) + 2):
            dx, dy = x + 0.5 - cx, (y + 0.5 - cy) / sy
            th = math.atan2(dy, dx)
            R = r0 * (1 + sum(a * math.sin(k * th + p) for k, a, p in wob))
            if math.hypot(dx, dy) <= R:
                pts.add((x, y))
    return pts


def splash(cx, cy, r0, tendrils, sy=1.0, wob=None):
    """tendrils: [(angle_deg, length_beyond_core, base_width, bulb_radius)]"""
    m = lumpy_core(cx, cy, r0, sy) if wob is None else lumpy_core(cx, cy, r0, sy, wob)
    for ang, ln, bw, bulb in tendrils:
        a = math.radians(ang)
        ux, uy = math.cos(a), math.sin(a) * sy
        sx, sy_ = cx + ux * r0 * 0.7, cy + uy * r0 * 0.7
        ex, ey = cx + ux * (r0 + ln), cy + uy * (r0 + ln)
        m |= capsule(sx, sy_, ex, ey, bw, max(0.6, bw * 0.4))
        if bulb > 0:
            m |= disc(ex + ux * bulb * 0.6, ey + uy * bulb * 0.6, bulb)
    return m


def chamfer(mask):
    """Two-pass 3-4 chamfer distance to the outside (in ~pixels)."""
    INF = 10 ** 9
    xs = [p[0] for p in mask]
    ys = [p[1] for p in mask]
    x0, x1, y0, y1 = min(xs) - 1, max(xs) + 1, min(ys) - 1, max(ys) + 1
    d = {}
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            d[(x, y)] = INF if (x, y) in mask else 0
    fw = ((-1, 0, 3), (0, -1, 3), (-1, -1, 4), (1, -1, 4))
    bw = ((1, 0, 3), (0, 1, 3), (1, 1, 4), (-1, 1, 4))
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if d[(x, y)]:
                d[(x, y)] = min([d[(x, y)]] + [d.get((x + dx, y + dy), 0) + w for dx, dy, w in fw])
    for y in range(y1, y0 - 1, -1):
        for x in range(x1, x0 - 1, -1):
            if d[(x, y)]:
                d[(x, y)] = min([d[(x, y)]] + [d.get((x + dx, y + dy), 0) + w for dx, dy, w in bw])
    return {p: v / 3.0 for p, v in d.items() if p in mask}


def height_shade(mask, hmax=3.0, bands=(0.86, 0.66, 0.36, 0.06), tones='edcba', flat_bias=0.0):
    dist = chamfer(mask)

    def h(p):
        if p not in dist:
            return 0.0
        t = min(dist[p], hmax) / hmax
        return hmax * (1 - (1 - t) ** 2)

    out = {}
    for (x, y) in mask:
        gx = (h((x + 1, y)) - h((x - 1, y))) / 2.0
        gy = (h((x, y + 1)) - h((x, y - 1))) / 2.0
        nx, ny, nz = -gx, -gy, 1.0 + flat_bias
        n = math.sqrt(nx * nx + ny * ny + nz * nz)
        v = (nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]) / n
        ch = tones[-1]
        for b, t in zip(bands, tones):
            if v > b:
                ch = t
                break
        out[(x, y)] = ch
    return out


def glint(tones, cx, cy, pts):
    for p in pts:
        if p in tones and tones[p] in 'ed':
            tones[p] = 'f'


def cloud(f, circles, fade=False):
    """circles drawn in the given order (put back ones first)."""
    for (x, y, r) in circles:
        f.paint(puff_tones(x, y, r, fade=fade))


def droplet(f, x, y, r=1.5):
    f.paint(chunk_tones(x, y, r))


def stink_line(f, x0, top, bot, amp=1.6, wavelength=11.0, phase=0.0):
    pts = {}
    prev = None
    for y in range(bot, top - 1, -1):
        x = int(round(x0 + amp * math.sin(2 * math.pi * (y / wavelength) + phase)))
        pts[(x, y)] = 'v' if y < (top + bot) / 2 else 'u'
        if prev is not None and abs(prev - x) > 1:
            pts[((prev + x) // 2, y)] = pts[(x, y)]
        prev = x
    f.paint(pts)


# ------------------------------------------------------------------ frames
def frame0():
    f = Frame()
    f.paint(star_tones(24.0, 24.0, 3.6, 10.4, 7.4, rot=0.0, core=2.4, mid=4.6))
    for ang, rad in ((22, 9.0), (112, 9.5), (158, 8.5), (205, 9.5), (292, 9.0), (338, 9.5)):
        a = math.radians(ang)
        droplet(f, snap(24 + rad * math.cos(a)), snap(24 + rad * math.sin(a)), 1.5)
    return f


def frame1():
    f = Frame()
    cloud(f, [(15.5, 13.5, 5.5), (24.5, 10.5, 5.5), (33.5, 13.5, 5.5), (12.5, 24.5, 5.5),
              (36.5, 23.5, 5.5), (15.5, 33.5, 5.5), (33.5, 33.5, 5.5), (24.5, 36.5, 5.5)])
    tend = [(-100, 7, 1.8, 2.2), (-40, 5, 1.6, 1.8), (15, 8, 1.8, 2.2), (70, 5, 1.6, 1.8),
            (120, 7.5, 1.8, 2.0), (175, 5.5, 1.6, 1.8), (225, 8, 1.8, 2.2)]
    m = splash(24.0, 24.0, 7.0, tend)
    t = height_shade(m, hmax=3.0)
    glint(t, 24, 24, [(20, 19), (21, 19), (19, 20)])
    f.paint(t)
    # hot core remnant of the flash
    f.paint({p: 'W' for p in disc(23.5, 23.5, 1.5)}, outline=False)
    for (x, y) in ((6.5, 12.5), (41.5, 16.5), (9.5, 39.5), (39.5, 40.5)):
        droplet(f, x, y, 1.5)
    return f


def frame2():
    f = Frame()
    back = [(24.5, 6.5, 6.5), (34.5, 8.5, 6.5), (40.5, 16.5, 6.5), (41.5, 27.5, 6.5), (36.5, 37.5, 6.5),
            (13.5, 8.5, 6.5), (7.5, 16.5, 6.5), (6.5, 27.5, 6.5), (11.5, 37.5, 6.5),
            (24.5, 40.5, 6.5), (17.5, 17.5, 5.5), (31.5, 17.5, 5.5), (24.5, 30.5, 5.5)]
    cloud(f, back)
    tend = [(-95, 9, 2.2, 2.6), (-45, 7, 2.0, 2.2), (0, 9.5, 2.2, 2.6), (50, 7, 2.0, 2.2),
            (100, 9, 2.2, 2.4), (150, 7.5, 2.0, 2.4), (200, 9, 2.2, 2.6), (245, 6.5, 1.8, 2.0)]
    m = splash(24.0, 24.0, 8.5, tend)
    t = height_shade(m, hmax=3.2)
    glint(t, 24, 24, [(19, 18), (20, 18), (18, 19)])
    f.paint(t)
    # a couple of front puffs over the lower splash so the gas wraps around it
    cloud(f, [(15.5, 38.5, 4.5), (33.5, 39.5, 4.5)])
    for (x, y, r) in ((3.5, 7.5, 1.5), (44.5, 9.5, 1.5), (2.5, 40.5, 1.5), (44.5, 42.5, 1.5)):
        droplet(f, x, y, r)
    return f


def frame3():
    f = Frame()
    tend = [(-5, 4, 1.6, 1.8), (40, 3, 1.4, 1.5), (95, 2.5, 1.4, 1.4), (150, 3.5, 1.6, 1.8),
            (195, 4.5, 1.6, 1.8), (240, 2.5, 1.2, 1.2), (300, 3, 1.4, 1.4)]
    m = splash(24.0, 28.0, 10.0, tend, sy=0.55)
    t = height_shade(m, hmax=2.2)
    glint(t, 24, 28, [(18, 25), (19, 25)])
    f.paint(t)
    cloud(f, [(9.5, 18.5, 3.5), (13.5, 15.5, 4.5), (10.5, 13.5, 2.5)], fade=True)
    cloud(f, [(38.5, 17.5, 3.5), (34.5, 14.5, 4.5), (37.5, 11.5, 2.5)], fade=True)
    cloud(f, [(22.5, 8.5, 3.5), (27.5, 6.5, 3.5)], fade=True)
    for (x, y) in ((7.5, 33.5), (41.5, 32.5), (30.5, 38.5)):
        droplet(f, x, y, 1.5)
    return f


def frame4():
    f = Frame()
    tend = [(0, 2.5, 1.4, 1.4), (70, 1.5, 1.2, 1.0), (140, 2.5, 1.4, 1.4), (185, 3, 1.4, 1.5), (300, 2, 1.2, 1.2)]
    m = splash(24.0, 30.0, 7.5, tend, sy=0.55)
    t = height_shade(m, hmax=2.0)
    glint(t, 24, 30, [(19, 28)])
    f.paint(t)
    stink_line(f, 17, 12, 25, amp=1.5, wavelength=12, phase=0.0)
    stink_line(f, 24, 7, 24, amp=1.5, wavelength=12, phase=2.4)
    stink_line(f, 31, 12, 25, amp=1.5, wavelength=12, phase=4.8)
    return f


FRAMES = [frame0, frame1, frame2, frame3, frame4]

if __name__ == '__main__':
    tag = sys.argv[1] if len(sys.argv) > 1 else 'e2'
    grids = [fn().g for fn in FRAMES]
    for i, g in enumerate(grids):
        print('frame', i, 'bbox', bbox(g))
    px = to_px(grids)
    fxpng.write_png('explo_%s.png' % tag, W * 5, H, px)
    a, b, o = fxpng.view(W * 5, H, px, 5, grid=(W, H))
    fxpng.write_png('explo_%s_5x.png' % tag, a, b, o)
    a, b, o = fxpng.view(W * 5, H, px, 3, bg=FLOOR, grid=(W, H), gridcol=(60, 90, 40, 255))
    fxpng.write_png('explo_%s_3x_floor.png' % tag, a, b, o)
    with open('explo_%s.txt' % tag, 'w') as fh:
        for i, g in enumerate(grids):
            fh.write('# frame %d\n' % i)
            for row in g:
                fh.write(''.join(row) + '\n')
