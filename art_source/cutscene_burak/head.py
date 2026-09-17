"""Hooded head block-in (procedural shapes, hand features added later as text)."""
import math, sys
from blib import *
from rig import HOOD, HOOD_TH, SKIN, SKIN_TH, rot

CX, CY = 31.5, 21.5


def hood_layer(tilt=0.2, open_dx=5.0, open_rx=5.8, open_ry=7.4):
    L = layer()
    cx, cy = CX, CY
    outer = ellipse_mask(cx, cy, 9.6, 9.2)
    # back peak of the hood
    pk = [rot(x, y, tilt * 0.5) for x, y in [(-9.0, 1.0), (-8.6, -5.5), (-5.0, -8.8), (-3.0, -4.0)]]
    peak = poly_mask([(cx + x, cy + y) for x, y in pk])
    # lower drape to shoulders
    drape = poly_mask([(cx - 8.8, cy + 3.5), (cx + 3.5, cy + 5.0), (cx + 6.5, cy + 11.5), (cx - 7.5, cy + 11.5)])
    hm = m_or(outer, peak, drape)
    paint_part(L, hm, shade_fn(lambda x, y: sphere_normal(x, y, cx - 1, cy + 1, 10.5, 11.5), HOOD, HOOD_TH))
    # opening (rotated ellipse)
    ocx, ocy = cx + open_dx, cy + 2.2
    om = empty_mask()
    rim = empty_mask()
    for y in range(H):
        for x in range(W):
            lx, ly = rot(x + .5 - ocx, y + .5 - ocy, -tilt)
            v = (lx / open_rx) ** 2 + (ly / open_ry) ** 2
            v2 = (lx / (open_rx + 1.6)) ** 2 + (ly / (open_ry + 1.4)) ** 2
            if v <= 1:
                om[y][x] = True
            elif v2 <= 1 and hm[y][x]:
                rim[y][x] = True
    for y in range(H):
        for x in range(W):
            if rim[y][x] and L[y][x] != '#':
                lx, ly = rot(x + .5 - ocx, y + .5 - ocy, -tilt)
                L[y][x] = 'A' if ly < -3 else ('B' if ly < 3 else 'C')
    paint_part(L, om, lambda x, y: 'F')
    return L, om


FACE_GLOOM = [(0.5, -4.0), (4.0, -5.0), (8.3, -3.6), (9.2, -1.2), (8.9, 0.2), (9.5, 1.2), (11.0, 2.8), (10.6, 3.6),
              (9.9, 3.8), (10.1, 4.6), (9.6, 5.3), (9.8, 6.0), (9.3, 7.4), (7.8, 8.4), (5.0, 8.0), (3.0, 9.0), (1.0, 6.0)]


def face_layer(poly, tilt=0.2, dx=0.0, dy=0.0):
    L = layer()
    pts = [(CX + dx + p[0], CY + dy + p[1]) for p in [rot(x, y, tilt) for x, y in poly]]
    m = poly_mask(pts)
    fcx, fcy = CX + dx + 6.0, CY + dy + 2.5

    def fn(x, y):
        n = sphere_normal(x, y, fcx, fcy, 6.5, 8.0)
        v = lambert_wrap(n, light=(0.2, -0.6, 0.9), wrap=0.2)
        # hood shadow over the top of the face
        lx, ly = rot(x + .5 - CX - dx, y + .5 - CY - dy, -tilt)
        if ly < -1.5:
            v *= 0.45
        elif ly < 0.5:
            v *= 0.7
        return quant(v, SKIN, SKIN_TH)
    paint_part(L, m, fn)
    return L, m


if __name__ == '__main__':
    hood, om = hood_layer()
    face, fm = face_layer(FACE_GLOOM)
    cv = compose([hood, face])
    preview(cv, 'head_8x.png', s=10)
    open('head_dump.txt', 'w').write(to_text(cv))
    for y, r in enumerate(cv[8:36]):
        print('%2d' % (y + 8), ''.join(r[16:52]))
