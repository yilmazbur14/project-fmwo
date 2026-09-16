"""POO EXPLOSION v3: wedge splash arms + detached droplets, contrasty dome shading,
leg-free puddles, faded gas with olive outline, floating stink lines."""
import math, sys
import fxpng
from explo_gen import W, H, FLOOR, PAL, LIGHT, Frame, disc, puff_tones, chunk_tones, star_tones, to_px, bbox, snap
from explo_gen2 import capsule, lumpy_core, chamfer, height_shade, glint

def splat(cx, cy, r0, arms, lumps=(), sy=1.0, wob=((3, 0.08, 0.4), (5, 0.06, 1.9), (7, 0.04, 3.1))):
    """arms: [(angle, length_beyond_core, base_halfwidth, tip_halfwidth, bulb)]; lumps: [(angle, r)]"""
    m = lumpy_core(cx, cy, r0, sy, wob)
    for ang, ln, bw, tw, bulb in arms:
        a = math.radians(ang); ux, uy = math.cos(a), math.sin(a) * sy
        ex, ey = cx + ux * (r0 + ln), cy + uy * (r0 + ln)
        m |= capsule(cx + ux * r0 * 0.5, cy + uy * r0 * 0.5, ex, ey, bw, tw)
        if bulb:
            m |= disc(ex + ux * 0.5, ey + uy * 0.5, bulb)
    for ang, r in lumps:
        a = math.radians(ang)
        m |= disc(cx + math.cos(a) * r0 * 0.92, cy + math.sin(a) * r0 * 0.92 * sy, r)
    return m

def dome_shade(m, cx, cy, r0, sy=1.0, hmax=3.2):
    """height-field edges + a broad dome term so the core reads glossy and rounded."""
    t = height_shade(m, hmax=hmax, bands=(0.84, 0.64, 0.40, 0.14), tones='edcba')
    for (x, y) in m:
        dx, dy = (x + 0.5 - cx) / r0, (y + 0.5 - cy) / (r0 * sy)
        d = math.hypot(dx, dy)
        if d < 0.95:
            nz = math.sqrt(max(0.0, 1 - (0.8 * d) ** 2))
            v = (0.8 * dx) * LIGHT[0] + (0.8 * dy) * LIGHT[1] + nz * LIGHT[2]
            ch = 'e' if v > 0.86 else 'd' if v > 0.70 else 'c' if v > 0.45 else 'b'
            # keep the darker of the two so rim shadows survive
            order = 'fedcba'
            if order.index(ch) > order.index(t[(x, y)]) or (t[(x, y)] in 'de' and ch in 'de'):
                t[(x, y)] = ch
    return t

def droplet(f, x, y, r=1.5):
    f.paint(chunk_tones(x, y, r))

def gas(f, circles, fade=False):
    for (x, y, r) in circles:
        f.paint(puff_tones(x, y, r, fade=fade), outline_ch='t' if fade else 'K')

def stink_line(f, x0, top, bot, amp=1.2, wavelength=10.0, phase=0.0, ch='v', out='t'):
    pts = {}
    prev = None
    for y in range(bot, top - 1, -1):
        x = int(round(x0 + amp * math.sin(2 * math.pi * (y / wavelength) + phase)))
        pts[(x, y)] = ch
        if prev is not None and abs(prev - x) > 1:
            pts[((prev + x) // 2, y)] = ch
        prev = x
    f.paint(pts, outline_ch=out)

def frame0():
    f = Frame()
    f.paint(star_tones(24.0, 24.0, 3.8, 10.4, 7.6, rot=0.0, core=2.4, mid=4.8))
    for ang, rad, r in ((22, 9.5, 1.5), (112, 10.0, 1.5), (160, 9.0, 1.0), (205, 10.0, 1.5), (292, 9.5, 1.0), (338, 10.0, 1.5)):
        a = math.radians(ang)
        droplet(f, snap(24 + rad * math.cos(a)), snap(24 + rad * math.sin(a)), r)
    return f

def frame1():
    f = Frame()
    gas(f, [(15.5, 13.5, 5.5), (24.5, 10.5, 5.5), (33.5, 13.5, 5.5), (11.5, 23.5, 5.5),
            (37.5, 23.5, 5.5), (14.5, 33.5, 5.5), (34.5, 33.5, 5.5), (24.5, 37.5, 5.5)])
    arms = [(-100, 5.5, 2.6, 0.9, 1.6), (-35, 4.0, 2.4, 1.0, 0), (20, 6.0, 2.6, 0.9, 1.6),
            (75, 3.5, 2.2, 1.0, 0), (125, 5.5, 2.6, 0.9, 1.5), (180, 4.0, 2.4, 1.0, 0), (230, 6.0, 2.6, 0.9, 1.6)]
    m = splat(24.0, 24.0, 7.5, arms, lumps=((-65, 2.5), (50, 2.5), (150, 2.5), (205, 2.0)))
    t = dome_shade(m, 24.0, 24.0, 7.5)
    glint(t, 24, 24, [(20, 19), (21, 19), (19, 20)])
    f.paint(t)
    for (x, y, r) in ((5.5, 11.5, 1.5), (42.5, 17.5, 1.5), (8.5, 40.5, 1.5), (40.5, 41.5, 1.0), (27.5, 3.5, 1.0)):
        droplet(f, x, y, r)
    return f

def frame2():
    f = Frame()
    back = [(24.5, 8.5, 6.5), (34.5, 9.5, 6.5), (40.5, 18.5, 6.5), (40.5, 29.5, 6.5), (34.5, 38.5, 6.5),
            (14.5, 9.5, 6.5), (8.5, 18.5, 6.5), (7.5, 29.5, 6.5), (14.5, 38.5, 6.5),
            (24.5, 40.5, 6.5), (17.5, 17.5, 5.5), (31.5, 17.5, 5.5), (24.5, 30.5, 5.5)]
    gas(f, back)
    arms = [(-95, 7.0, 3.0, 1.0, 1.8), (-40, 5.0, 2.8, 1.1, 0), (5, 7.5, 3.0, 1.0, 1.8), (55, 5.0, 2.8, 1.1, 0),
            (100, 7.0, 3.0, 1.0, 1.8), (150, 5.5, 2.8, 1.0, 0), (200, 7.5, 3.0, 1.0, 1.8), (250, 4.5, 2.6, 1.1, 0)]
    m = splat(24.0, 24.0, 9.0, arms, lumps=((-70, 3.0), (30, 3.0), (125, 3.0), (175, 2.5), (228, 2.5)))
    t = dome_shade(m, 24.0, 24.0, 9.0)
    glint(t, 24, 24, [(19, 18), (20, 18), (18, 19)])
    f.paint(t)
    gas(f, [(15.5, 39.5, 4.5), (33.5, 40.5, 4.5)])
    for (x, y, r) in ((3.5, 6.5, 1.5), (44.5, 8.5, 1.5), (2.5, 41.5, 1.5), (44.5, 43.5, 1.5), (24.5, 2.5, 1.0)):
        droplet(f, x, y, r)
    return f

def frame3():
    f = Frame()
    m = splat(24.0, 29.0, 10.5, [(-10, 2.5, 2.4, 1.2, 0), (60, 1.5, 2.2, 1.2, 0), (160, 2.5, 2.4, 1.2, 0), (215, 2.0, 2.2, 1.2, 0)],
              lumps=((20, 3.0), (110, 3.5), (190, 3.0), (250, 3.0), (300, 3.0)), sy=0.5)
    t = dome_shade(m, 24.0, 29.0, 10.5, sy=0.5, hmax=2.0)
    glint(t, 24, 29, [(18, 26), (19, 26)])
    f.paint(t)
    gas(f, [(10.5, 19.5, 3.5), (14.5, 15.5, 4.5), (10.5, 12.5, 2.5)], fade=True)
    gas(f, [(37.5, 18.5, 3.5), (33.5, 14.5, 4.5), (37.5, 10.5, 2.5)], fade=True)
    gas(f, [(21.5, 7.5, 3.5), (26.5, 5.5, 3.5)], fade=True)
    for (x, y, r) in ((8.5, 33.5, 1.5), (40.5, 32.5, 1.5), (31.5, 38.5, 1.0), (15.5, 38.5, 1.0)):
        droplet(f, x, y, r)
    return f

def frame4():
    f = Frame()
    m = splat(24.0, 31.0, 8.0, [(0, 1.5, 2.0, 1.2, 0), (185, 2.0, 2.0, 1.2, 0)],
              lumps=((60, 2.5), (130, 2.5), (240, 2.5), (300, 2.5)), sy=0.5)
    t = dome_shade(m, 24.0, 31.0, 8.0, sy=0.5, hmax=1.8)
    glint(t, 24, 31, [(19, 29)])
    f.paint(t)
    gas(f, [(28.5, 16.5, 3.5), (24.5, 14.5, 2.5)], fade=True)
    stink_line(f, 18, 17, 24, amp=1.0, wavelength=9, phase=0.0)
    stink_line(f, 31, 18, 24, amp=1.0, wavelength=9, phase=3.0)
    return f

FRAMES = [frame0, frame1, frame2, frame3, frame4]

if __name__ == '__main__':
    tag = sys.argv[1] if len(sys.argv) > 1 else 'e3'
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
