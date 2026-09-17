"""POO EXPLOSION v4: flat liquid splat shading, irregular arms, radial droplet trails."""
import math, sys
import fxpng
from explo_gen import W, H, FLOOR, PAL, LIGHT, Frame, disc, puff_tones, chunk_tones, star_tones, to_px, bbox, snap
from explo_gen2 import capsule, lumpy_core, height_shade
from explo_gen3 import splat, droplet, gas, stink_line

def flat_shade(m, hmax=1.6):
    return height_shade(m, hmax=hmax, bands=(0.80, 0.60, 0.36, 0.12), tones='edcba')

def gloss(t, pts):
    for p in pts:
        if p in t and t[p] in 'dce':
            t[p] = 'f' if t[p] in 'de' else 'e'

def radial_drops(f, cx, cy, arms, r0, sy=1.0):
    for ang, ln, bw, tw, bulb in arms:
        if ln >= 6.5:
            a = math.radians(ang)
            d = r0 + ln + 4.2
            droplet(f, snap(cx + math.cos(a) * d), snap(cy + math.sin(a) * d * sy), 1.5)

WOB_BIG = ((2, 0.07, 1.1), (3, 0.10, 0.4), (5, 0.08, 1.9), (7, 0.05, 3.1))

def frame1():
    f = Frame()
    gas(f, [(15.5, 13.5, 5.5), (24.5, 10.5, 5.5), (33.5, 13.5, 5.5), (11.5, 23.5, 5.5),
            (37.5, 23.5, 5.5), (14.5, 33.5, 5.5), (34.5, 33.5, 5.5), (24.5, 37.5, 5.5)])
    arms = [(-112, 6.5, 2.4, 0.9, 1.7), (-62, 2.5, 2.4, 1.2, 0), (-18, 5.0, 2.2, 0.9, 1.4), (38, 7.0, 2.4, 0.9, 1.7),
            (95, 3.0, 2.4, 1.2, 0), (138, 6.0, 2.2, 0.9, 1.5), (188, 3.5, 2.4, 1.1, 0), (228, 6.5, 2.4, 0.9, 1.6)]
    m = splat(24.0, 24.0, 7.0, arms, lumps=((-40, 2.5), (68, 2.5), (160, 2.5), (205, 2.0), (255, 2.5)), wob=WOB_BIG)
    t = flat_shade(m)
    gloss(t, [(19, 20), (20, 19), (21, 19)])
    f.paint(t)
    radial_drops(f, 24.0, 24.0, arms, 7.0)
    return f

def frame2():
    f = Frame()
    back = [(24.5, 8.5, 6.5), (34.5, 10.5, 6.5), (39.5, 19.5, 6.5), (39.5, 29.5, 6.5), (33.5, 37.5, 6.5),
            (14.5, 10.5, 6.5), (9.5, 19.5, 6.5), (8.5, 29.5, 6.5), (15.5, 37.5, 6.5),
            (24.5, 39.5, 6.5), (17.5, 17.5, 5.5), (31.5, 17.5, 5.5), (24.5, 30.5, 5.5)]
    gas(f, back)
    arms = [(-105, 8.0, 2.8, 1.0, 2.0), (-58, 3.5, 2.8, 1.3, 0), (-20, 7.0, 2.6, 1.0, 1.7), (22, 4.0, 2.8, 1.3, 0),
            (62, 8.5, 2.8, 1.0, 2.0), (108, 4.5, 2.6, 1.2, 0), (150, 7.5, 2.8, 1.0, 1.8), (195, 3.5, 2.6, 1.3, 0),
            (232, 8.0, 2.8, 1.0, 1.9)]
    m = splat(24.0, 24.0, 8.5, arms, lumps=((-80, 3.0), (0, 3.0), (85, 3.0), (128, 2.5), (172, 3.0), (212, 2.5), (260, 2.5)), wob=WOB_BIG)
    t = flat_shade(m, hmax=1.8)
    gloss(t, [(18, 19), (19, 18), (20, 18), (21, 17)])
    f.paint(t)
    gas(f, [(15.5, 39.5, 4.5), (33.5, 40.5, 4.5)])
    radial_drops(f, 24.0, 24.0, [(a, l, b, tw, bb) for (a, l, b, tw, bb) in arms if a in (-20, 150)], 8.5)
    return f

if __name__ == '__main__':
    import explo_gen3 as g3
    tag = sys.argv[1] if len(sys.argv) > 1 else 'e4'
    frames = [g3.frame0, frame1, frame2, g3.frame3, g3.frame4]
    grids = [fn().g for fn in frames]
    for i, g in enumerate(grids):
        print('frame', i, 'bbox', bbox(g))
    px = to_px(grids)
    fxpng.write_png('explo_%s.png' % tag, W * 5, H, px)
    a, b, o = fxpng.view(W * 5, H, px, 5, grid=(W, H))
    fxpng.write_png('explo_%s_5x.png' % tag, a, b, o)
    # frames 1-2 only at 8x for detail
    sub = [row[48:144] for row in px]
    a, b, o = fxpng.view(96, 48, sub, 8, grid=(48, 48))
    fxpng.write_png('explo_%s_f12_8x.png' % tag, a, b, o)
