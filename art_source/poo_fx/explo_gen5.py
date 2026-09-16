"""POO EXPLOSION v5: unified gas masses (black silhouette outline, olive inner creases),
energetic F1, flat-bottom stink clouds, irregular chunks, strict 1px frame margin."""
import math
import sys
import fxpng
from explo_gen import W, H, FLOOR, PAL, LIGHT, Frame, disc, puff_tones, star_tones, to_px, bbox, snap
from explo_gen2 import capsule, lumpy_core, height_shade
from explo_gen3 import splat

N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
WOB_BIG = ((2, 0.07, 1.1), (3, 0.10, 0.4), (5, 0.08, 1.9), (7, 0.05, 3.1))


def gas_mass(f, circles, fade=False, silhouette=True):
    """Paint overlapping puffs back-to-front. Inner overlaps get a dark olive crease; the
    union silhouette gets the black (or, when fading, olive) outline."""
    inner = 'u' if fade else 's'
    outer = 't' if fade else 'K'
    union = set()
    for (x, y, r) in circles:
        tones = puff_tones(x, y, r, fade=fade)
        for p, ch in tones.items():
            if f.inside(*p):
                f.g[p[1]][p[0]] = ch
        for (px_, py_) in tones:
            for dx, dy in N4:
                q = (px_ + dx, py_ + dy)
                if q not in tones and q in union and f.inside(*q):
                    f.g[q[1]][q[0]] = inner
        union |= set(tones)
    if silhouette:
        for (px_, py_) in union:
            for dx, dy in N4:
                q = (px_ + dx, py_ + dy)
                if q not in union and f.inside(*q):
                    f.g[q[1]][q[0]] = outer
    return union


def flat_shade(m, hmax=1.7):
    return height_shade(m, hmax=hmax, bands=(0.80, 0.60, 0.36, 0.12), tones='edcba')


def gloss(t, pts):
    for p in pts:
        if p in t and t[p] in 'cde':
            t[p] = 'f' if t[p] in 'de' else 'e'


def lump(t, x, y, r=1.5):
    """Chunky bump inside a splat: lit cap, mid body, shadow crease on the lower right."""
    body = disc(x, y, r)
    for (px_, py_) in body:
        if (px_, py_) not in t:
            continue
        v = (px_ + 0.5 - x) * LIGHT[0] + (py_ + 0.5 - y) * LIGHT[1]
        t[(px_, py_)] = 'e' if v > 0.45 * r else 'd'
    for (px_, py_) in body:
        for dx, dy in ((1, 0), (0, 1), (1, 1)):
            q = (px_ + dx, py_ + dy)
            if q in t and q not in body:
                t[q] = 'b'


def chunk(f, x, y, r=1.5, ang=0.0):
    """Irregular poo chunk: two overlapping discs, lit from the upper left."""
    a = math.radians(ang)
    m = disc(x, y, r) | disc(x + math.cos(a) * 1.0, y + math.sin(a) * 1.0, r * 0.85)
    t = {}
    for (px_, py_) in m:
        v = (px_ + 0.5 - x) * LIGHT[0] + (py_ + 0.5 - y) * LIGHT[1]
        t[(px_, py_)] = 'e' if v > 0.55 * r else 'c' if v > -0.45 * r else 'b'
    f.paint(t)


def ring_pts(cx, cy, specs):
    """specs: [(angle_deg, dist, radius)] -> circles snapped to pixel centres."""
    out = []
    for ang, dist, r in specs:
        a = math.radians(ang)
        out.append((snap(cx + dist * math.cos(a)), snap(cy + dist * math.sin(a)), r))
    return out


# ------------------------------------------------------------------------ frames
def frame0():
    f = Frame()
    f.paint(star_tones(24.0, 24.0, 3.8, 10.4, 7.6, rot=0.0, core=2.4, mid=4.8))
    for ang, rad in ((22, 10.0), (112, 10.5), (158, 9.5), (205, 10.5), (292, 10.0), (338, 10.5)):
        a = math.radians(ang)
        chunk(f, snap(24 + rad * math.cos(a)), snap(24 + rad * math.sin(a)), 1.5, ang)
    return f


def frame1():
    f = Frame()
    back = [(23.5, 23.5, 7.5)] + ring_pts(24.0, 24.0, [
        (-90, 11.0, 5.5), (-45, 11.5, 4.5), (0, 11.0, 5.5), (45, 11.5, 4.5),
        (90, 11.0, 5.5), (135, 11.5, 4.5), (180, 11.0, 5.5), (225, 11.5, 4.5)])
    gas_mass(f, back)
    arms = [(-112, 7.0, 2.3, 0.9, 1.6), (-62, 3.0, 2.3, 1.2, 0), (-17, 6.0, 2.2, 0.9, 1.5),
            (35, 7.5, 2.3, 0.9, 1.7), (95, 3.5, 2.3, 1.2, 0), (140, 6.5, 2.2, 0.9, 1.5),
            (190, 3.0, 2.3, 1.2, 0), (230, 7.0, 2.3, 0.9, 1.6)]
    m = splat(24.0, 24.0, 6.5, arms, lumps=((-40, 2.5), (65, 2.5), (160, 2.5), (260, 2.0)), wob=WOB_BIG)
    t = flat_shade(m)
    # burst origin still glowing from the flash
    lump(t, 18.5, 27.5, 1.2)
    lump(t, 28.5, 20.5, 1.2)
    for p in disc(23.5, 23.5, 2.5):
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
    f = Frame()
    back = [(23.5, 23.5, 9.5)] + ring_pts(24.0, 24.0, [
        (-45, 8.5, 6.5), (45, 8.5, 6.5), (135, 8.5, 6.5), (225, 8.5, 6.5)]) + ring_pts(24.0, 24.0, [
        (-90, 15.0, 6.5), (-57, 15.5, 5.5), (-25, 15.0, 6.5), (8, 15.5, 5.5), (40, 15.0, 6.5),
        (73, 15.5, 5.5), (106, 15.0, 6.5), (139, 15.5, 5.5), (172, 15.0, 6.5), (205, 15.5, 5.5),
        (238, 15.0, 6.5)])
    gas_mass(f, back)
    arms = [(-105, 8.0, 2.8, 1.0, 2.0), (-58, 3.5, 2.8, 1.3, 0), (-20, 7.0, 2.6, 1.0, 1.7),
            (22, 4.0, 2.8, 1.3, 0), (62, 8.5, 2.8, 1.0, 2.0), (108, 4.5, 2.6, 1.2, 0),
            (150, 7.5, 2.8, 1.0, 1.8), (195, 3.5, 2.6, 1.3, 0), (232, 8.0, 2.8, 1.0, 1.9)]
    m = splat(24.0, 24.0, 8.5, arms, lumps=((-80, 3.0), (0, 3.0), (85, 3.0), (128, 2.5),
                                            (172, 3.0), (212, 2.5), (260, 2.5)), wob=WOB_BIG)
    t = flat_shade(m, hmax=1.8)
    for (lx, ly, lr) in ((27.5, 20.5, 2.2), (19.5, 27.5, 1.2), (29.5, 29.5, 1.2), (23.5, 32.5, 1.2), (15.5, 21.5, 1.2)):
        lump(t, lx, ly, lr)
    gloss(t, [(18, 19), (19, 18), (20, 18), (21, 17), (26, 19)])
    f.paint(t)
    gas_mass(f, [(16.5, 39.5, 4.5), (32.5, 40.5, 4.5)])
    for ang, dist in ((-128, 19.5), (-8, 20.0), (52, 19.5), (172, 20.0)):
        a = math.radians(ang)
        chunk(f, snap(24 + dist * math.cos(a)), snap(24 + dist * math.sin(a)), 1.5, ang + 180)
    return f


def puddle(f, cx, cy, r0, arms, lumps, glossy, bumps=()):
    m = splat(cx, cy, r0, arms, lumps=lumps, sy=0.5)
    t = height_shade(m, hmax=1.6, bands=(0.80, 0.60, 0.36, 0.12), tones='edcba')
    for (lx, ly, lr) in bumps:
        lump(t, lx, ly, lr)
    gloss(t, glossy)
    f.paint(t)


def frame3():
    f = Frame()
    puddle(f, 24.0, 30.0, 10.5,
           [(-10, 2.5, 2.4, 1.2, 0), (60, 1.5, 2.2, 1.2, 0), (160, 2.5, 2.4, 1.2, 0), (215, 2.0, 2.2, 1.2, 0)],
           ((20, 3.0), (110, 3.5), (190, 3.0), (250, 3.0), (300, 3.0)),
           [(17, 27), (18, 27), (19, 27)], bumps=((28.5, 30.5, 1.2), (21.5, 31.5, 1.2)))
    # the stink cloud breaking up into three flat-bottomed clouds drifting upward
    gas_mass(f, [(8.5, 18.5, 3.5), (12.5, 15.5, 4.5), (16.5, 18.5, 3.5)], fade=True)
    gas_mass(f, [(31.5, 17.5, 3.5), (35.5, 14.5, 4.5), (39.5, 17.5, 3.5)], fade=True)
    gas_mass(f, [(19.5, 9.5, 3.5), (23.5, 7.5, 4.5), (27.5, 9.5, 3.5)], fade=True)
    for (x, y, ang) in ((8.5, 34.5, 200), (40.5, 33.5, -20), (30.5, 39.5, 60)):
        chunk(f, x, y, 1.5, ang)
    return f


def frame4():
    f = Frame()
    puddle(f, 24.0, 30.0, 8.0,
           [(0, 1.5, 2.0, 1.2, 0), (185, 2.0, 2.0, 1.2, 0)],
           ((60, 2.5), (130, 2.5), (240, 2.5), (300, 2.5)),
           [(19, 28), (20, 28)], bumps=((26.5, 30.5, 1.2),))
    gas_mass(f, [(20.5, 15.5, 3.0), (24.5, 13.5, 3.5), (28.5, 15.5, 3.0)], fade=True)
    return f


FRAMES = [frame0, frame1, frame2, frame3, frame4]


def render(tag, grids):
    px = to_px(grids)
    fxpng.write_png('explo_%s.png' % tag, W * 5, H, px)
    a, b, o = fxpng.view(W * 5, H, px, 5, grid=(W, H))
    fxpng.write_png('explo_%s_5x.png' % tag, a, b, o)
    a, b, o = fxpng.view(W * 5, H, px, 3, bg=FLOOR, grid=(W, H), gridcol=(60, 90, 40, 255))
    fxpng.write_png('explo_%s_3x_floor.png' % tag, a, b, o)
    return px


if __name__ == '__main__':
    tag = sys.argv[1] if len(sys.argv) > 1 else 'e5'
    grids = [fn().g for fn in FRAMES]
    for i, g in enumerate(grids):
        bb = bbox(g)
        print('frame', i, 'bbox', bb, 'MARGIN OK' if bb[0] >= 1 and bb[2] >= 1 and bb[1] <= 46 and bb[3] <= 46 else 'TOUCHES EDGE')
    render(tag, grids)
    with open('explo_%s.txt' % tag, 'w') as fh:
        for i, g in enumerate(grids):
            fh.write('# frame %d\n' % i)
            for row in g:
                fh.write(''.join(row) + '\n')
