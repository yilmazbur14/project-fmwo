"""Hover ground shadow for beast Bixby: 192x48 per frame, solid black (alpha 255); code sets transparency.
Top-down winged silhouette: body ellipse, three head bumps toward the player (bottom), scalloped wings whose
span follows the flap cycle, and a thin tail with a spade tip trailing behind (up-left)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from lib import *
from pal import BLACK
from parts import qbez
import view

SW, SH = 192, 48
CX, CY = 96, 24

# wing span factor per hover frame (F0 wings raised, F1 sweeping down, F2 down/out, F3 recovering)
SPANS = [0.84, 0.97, 1.0, 0.93]


def wing_poly(side, k):
    half = 86 * k
    s = side
    root_top = (CX - 16 * s, CY - 7)
    tip = (CX - half * s, CY - 9)
    pts = [root_top, (CX - half * 0.55 * s, CY - 12), tip]
    # trailing edge: fingertips with scallops between them, back toward the body
    fingers = [(CX - half * 0.93 * s, CY + 3), (CX - half * 0.68 * s, CY + 9), (CX - half * 0.43 * s, CY + 12), (CX - 26 * s, CY + 11)]
    prev = tip
    for f in fingers:
        mid = ((prev[0] + f[0]) / 2, (prev[1] + f[1]) / 2 - 3.2)
        pts += qbez(prev, mid, f, 6)[1:]
        prev = f
    pts.append((CX - 14 * s, CY + 6))
    return poly(pts)


def frame(k):
    lib.set_size(SW, SH)
    m = set()
    m |= wing_poly(1, k) | wing_poly(-1, k)
    m |= ell(CX, CY + 1, 28, 12.5)
    for dx, r in ((-19, 6.5), (0, 8), (19, 6.5)):
        m |= ell(CX + dx, CY + 9, r, 5.5)
    # tail trailing behind (upward) and to the left, with a spade tip
    m |= tube([(CX - 6, CY - 8), (CX - 20, CY - 15), (CX - 34, CY - 17), (CX - 44, CY - 15)], [3.2, 2.5, 1.6, 0.6])
    m = erode(dilate(m, 1, diag=True), 1)
    cv = Canvas(SW, SH)
    cv.paint(m, BLACK)
    return cv


if __name__ == '__main__':
    tag = sys.argv[1]
    strip = Canvas(SW * 4, SH)
    for i, k in enumerate(SPANS):
        strip.blit(frame(k), SW * i, 0)
    strip.save(os.path.join(view.PREV, '%s_shadow_strip.png' % tag))
    view.zoom_canvas(strip, 2, '%s_shadow_2x.png' % tag, bg=(136, 180, 99, 255))
    print('ok')
