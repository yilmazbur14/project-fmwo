"""POO EXPLOSION - final generator. 5 frames x 48x48 -> 240x48.
Builds on the v5 techniques (unified gas masses, flat liquid splats, irregular chunks) with
the review fixes: comic pop burst, smoother arms, arc lumps, no cat-ear puddle."""
import math
import sys
import fxpng
from explo_gen import W, H, FLOOR, PAL, LIGHT, Frame, disc, to_px, bbox, snap
from explo_gen5 import gas_mass, flat_shade, gloss, chunk, ring_pts, WOB_BIG
from explo_gen3 import splat
from explo_gen2 import height_shade


def burst_tones(cx, cy, n, r_in, r_long, r_short, rot=0.0, core=2.8, mid=5.2):
    out = {}
    sector = 360.0 / n
    reach = int(r_long) + 2
    for y in range(int(cy) - reach, int(cy) + reach + 1):
        for x in range(int(cx) - reach, int(cx) + reach + 1):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(dx, dy)
            th = (math.degrees(math.atan2(dy, dx)) - rot) % 360.0
            k = int(round(th / sector))
            off = abs(th - k * sector) / (sector / 2.0)
            tip = r_long if k % 2 == 0 else r_short
            R = r_in + (tip - r_in) * max(0.0, 1.0 - off) ** 1.25
            if d <= R:
                out[(x, y)] = 'W' if d <= core else 'w' if d <= mid else 'v'
    return out


def arc_lump(t, x, y):
    """Glossy lump: light arc over a dark crease (5x3)."""
    ix, iy = int(x), int(y)
    for p, ch in (((ix - 1, iy), 'd'), ((ix, iy - 1), 'e'), ((ix + 1, iy - 1), 'd'),
                  ((ix - 1, iy + 1), 'b'), ((ix, iy + 1), 'b'), ((ix + 1, iy + 1), 'b'), ((ix + 2, iy), 'b')):
        if p in t and t[p] in 'cdb':
            t[p] = ch


# ------------------------------------------------------------------------------ frames
def frame0():
    """POP: small bright burst + first flecks of the shell."""
    f = Frame()
    f.paint(burst_tones(24.0, 24.0, 12, 4.6, 10.6, 7.0, rot=0.0, core=2.6, mid=5.0))
    for ang, rad in ((32, 12.0), (88, 12.5), (148, 12.0), (212, 12.5), (268, 12.0), (328, 12.5)):
        a = math.radians(ang)
        chunk(f, snap(24 + rad * math.cos(a)), snap(24 + rad * math.sin(a)), 1.5, ang)
    return f


def frame1():
    """EXPANDING: splat bursting out through the first gas, chunks flying."""
    f = Frame()
    back = [(23.5, 23.5, 7.5)] + ring_pts(24.0, 24.0, [
        (-90, 11.0, 5.5), (-45, 11.5, 4.5), (0, 11.0, 5.5), (45, 11.5, 4.5),
        (90, 11.0, 5.5), (135, 11.5, 4.5), (180, 11.0, 5.5), (225, 11.5, 4.5)])
    gas_mass(f, back)
    arms = [(-112, 6.5, 2.6, 1.2, 1.7), (-62, 3.0, 2.6, 1.4, 0), (-17, 5.5, 2.5, 1.2, 1.5),
            (35, 7.0, 2.6, 1.2, 1.7), (95, 3.5, 2.6, 1.4, 0), (140, 6.0, 2.5, 1.2, 1.5),
            (190, 3.0, 2.6, 1.4, 0), (230, 6.5, 2.6, 1.2, 1.6)]
    m = splat(24.0, 24.0, 6.5, arms, lumps=((-40, 2.5), (65, 2.5), (160, 2.5), (260, 2.0)), wob=WOB_BIG)
    t = flat_shade(m)
    arc_lump(t, 19.5, 28.5)
    arc_lump(t, 28.5, 21.5)
    for p in disc(23.5, 23.5, 2.5):          # burst origin still glowing from the flash
        if p in t:
            t[p] = 'f'
    for p in disc(23.5, 23.5, 1.5):
        if p in t:
            t[p] = 'W'
    f.paint(t)
    for ang, dist in ((-142, 18.5), (-28, 19.0), (68, 18.5), (160, 19.0)):
        a = math.radians(ang)
        chunk(f, snap(24 + dist * math.cos(a)), snap(24 + dist * math.sin(a)), 1.5, ang + 180)
    return f


def frame2():
    """PEAK: biggest, full stink ring = the clearest damage footprint."""
    f = Frame()
    back = [(23.5, 23.5, 9.5)] + ring_pts(24.0, 24.0, [
        (-45, 8.5, 6.5), (45, 8.5, 6.5), (135, 8.5, 6.5), (225, 8.5, 6.5)]) + ring_pts(24.0, 24.0, [
        (-90, 15.0, 6.5), (-57, 15.5, 5.5), (-25, 15.0, 6.5), (8, 15.5, 5.5), (40, 15.0, 6.5),
        (73, 15.5, 5.5), (106, 15.0, 6.5), (139, 15.5, 5.5), (172, 15.0, 6.5), (205, 15.5, 5.5),
        (238, 15.0, 6.5)])
    gas_mass(f, back)
    arms = [(-105, 7.5, 3.0, 1.3, 2.0), (-58, 3.5, 3.0, 1.5, 0), (-20, 6.5, 2.8, 1.3, 1.7),
            (22, 4.0, 3.0, 1.5, 0), (62, 8.0, 3.0, 1.3, 2.0), (108, 4.5, 2.8, 1.4, 0),
            (150, 7.0, 3.0, 1.3, 1.8), (195, 3.5, 2.8, 1.5, 0), (232, 7.5, 3.0, 1.3, 1.9)]
    m = splat(24.0, 24.0, 8.5, arms, lumps=((-80, 3.0), (0, 3.0), (85, 3.0), (128, 2.5),
                                            (172, 3.0), (212, 2.5), (260, 2.5)), wob=WOB_BIG)
    t = flat_shade(m, hmax=1.8)
    for (lx, ly) in ((27.5, 21.5), (19.5, 28.5), (28.5, 30.5)):
        arc_lump(t, lx, ly)
    gloss(t, [(18, 19), (19, 18), (20, 18), (21, 17)])
    f.paint(t)
    gas_mass(f, [(16.5, 39.5, 4.5), (32.5, 40.5, 4.5)])
    for ang, dist in ((-128, 19.5), (-8, 20.0), (52, 19.5), (172, 20.0)):
        a = math.radians(ang)
        chunk(f, snap(24 + dist * math.cos(a)), snap(24 + dist * math.sin(a)), 1.5, ang + 180)
    return f


def puddle(f, cx, cy, r0, arms, lumps, glossy, bumps=(), wob=WOB_BIG, hmax=1.6):
    m = splat(cx, cy, r0, arms, lumps=lumps, sy=0.5, wob=wob)
    t = height_shade(m, hmax=hmax, bands=(0.80, 0.60, 0.36, 0.12), tones='edcba')
    for (lx, ly) in bumps:
        arc_lump(t, lx, ly)
    gloss(t, glossy)
    f.paint(t)


def frame3():
    """DISSIPATING: splat lands, the stink breaks into clouds drifting up."""
    f = Frame()
    puddle(f, 24.0, 30.0, 10.5,
           [(-10, 2.5, 2.4, 1.3, 0), (60, 1.5, 2.2, 1.3, 0), (160, 2.5, 2.4, 1.3, 0), (215, 2.0, 2.2, 1.3, 0)],
           ((20, 3.0), (110, 3.5), (190, 3.0), (250, 3.0), (300, 3.0)),
           [(17, 27), (18, 27), (19, 27)], bumps=((28.5, 30.5), (21.5, 31.5)))
    gas_mass(f, [(8.5, 18.5, 3.5), (12.5, 15.5, 4.5), (16.5, 18.5, 3.5)], fade=True)
    gas_mass(f, [(31.5, 17.5, 3.5), (35.5, 14.5, 4.5), (39.5, 17.5, 3.5)], fade=True)
    gas_mass(f, [(19.5, 9.5, 3.5), (23.5, 7.5, 4.5), (27.5, 9.5, 3.5)], fade=True)
    for (x, y, ang) in ((8.5, 34.5, 200), (40.5, 33.5, -20), (31.5, 40.5, 60)):
        chunk(f, x, y, 1.5, ang)
    return f


def frame4():
    """WHIFF: small splat left behind + last puff of stink."""
    f = Frame()
    puddle(f, 24.0, 30.0, 8.0,
           [(-8, 1.5, 2.0, 1.3, 0), (188, 2.0, 2.0, 1.3, 0)],
           ((25, 2.5), (85, 2.5), (150, 2.5), (218, 2.0), (322, 2.0)),
           [(19, 28), (20, 28)], bumps=((26.5, 30.5),),
           wob=((2, 0.05, 0.3), (3, 0.08, 1.2), (5, 0.06, 2.5)), hmax=0.9)
    gas_mass(f, [(20.5, 15.5, 3.0), (24.5, 13.5, 3.5), (28.5, 15.5, 3.0)], fade=True)
    return f


FRAMES = [frame0, frame1, frame2, frame3, frame4]


def build():
    return [fn().g for fn in FRAMES]


if __name__ == '__main__':
    tag = sys.argv[1] if len(sys.argv) > 1 else 'ef1'
    grids = build()
    for i, g in enumerate(grids):
        bb = bbox(g)
        ok = bb[0] >= 1 and bb[2] >= 1 and bb[1] <= 46 and bb[3] <= 46
        print('frame', i, 'bbox', bb, 'MARGIN OK' if ok else 'TOUCHES EDGE')
    px = to_px(grids)
    fxpng.write_png('explo_%s.png' % tag, W * 5, H, px)
    top = [row[0:144] for row in px]
    bot = [row[144:240] + [(0, 0, 0, 0)] * 48 for row in px]
    a, b, o = fxpng.view(144, 96, top + bot, 6, grid=(48, 48))
    fxpng.write_png('explo_%s_6x_grid.png' % tag, a, b, o)
    with open('explo_%s.txt' % tag, 'w') as fh:
        for i, g in enumerate(grids):
            fh.write('# frame %d\n' % i)
            for row in g:
                fh.write(''.join(row) + '\n')
