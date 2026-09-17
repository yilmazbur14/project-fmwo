"""Grounded contact shadows for beast Bixby: 192x48 per frame, solid black (alpha 255, code sets transparency),
same format as bixby_beast_shadow.png. Frame centre (96,25) sits ON the grounded feet anchor (96,151)
(the hover shadow sits 40 texels below the hover anchor; landing tweens that gap to 0).
  0 crouch / standing footprint  (land 1-2, takeoff 0-1, roar, defeat 0)
  1 exhausted footprint, wings flat on the floor (recover, hit, defeat 1-3)
  2 normal Bixby                 (defeat 4-7)
  3 normal Bixby + Liam          (defeat 8-9)"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from lib import *
from pal import BLACK
from parts import qbez

SW, SH = 192, 48
CX, CY = 96, 25


def wing_flat(side, span, droop=0):
    s = side
    root = (CX - 20 * s, CY - 4)
    tip = (CX - span * s, CY + 2 + droop)
    pts = [root, (CX - span * 0.5 * s, CY - 9), tip]
    fingers = [(CX - span * 0.92 * s, CY + 9 + droop), (CX - span * 0.7 * s, CY + 13), (CX - span * 0.45 * s, CY + 14), (CX - 28 * s, CY + 12)]
    prev = tip
    for f in fingers:
        mid = ((prev[0] + f[0]) / 2, (prev[1] + f[1]) / 2 - 2.5)
        pts += qbez(prev, mid, f, 6)[1:]
        prev = f
    pts.append((CX - 16 * s, CY + 8))
    return poly(pts)


def body_foot(rx=34, ry=11, paws=True, tail=True):
    m = ell(CX, CY, rx, ry)
    if paws:
        for dx in (-48, 48):
            m |= ell(CX + dx, CY + 4, 9, 5)
    if tail:
        m |= tube([(CX - 26, CY - 4), (CX - 44, CY - 8), (CX - 62, CY - 6), (CX - 76, CY - 1)], [3.4, 2.8, 2.0, 1.0])
    return m


def frame(k):
    lib.set_size(SW, SH)
    if k == 0:
        m = body_foot()
        m |= ell(CX - 50, CY - 2, 14, 7) | ell(CX + 50, CY - 2, 14, 7)      # folded wing tips at the sides
    elif k == 1:
        m = body_foot(rx=36, ry=12)
        m |= wing_flat(1, 94, 2) | wing_flat(-1, 94, 2)
    elif k == 2:
        m = ell(CX, CY - 1, 27, 6)
    else:
        m = ell(CX, CY - 1, 27, 6) | ell(CX + 61, CY - 2, 29, 5)
    m = erode(dilate(m, 1, diag=True), 1)
    cv = Canvas(SW, SH)
    cv.paint({q for q in m if 0 <= q[0] < SW and 0 <= q[1] < SH}, BLACK)
    return cv


def frames():
    return [frame(k) for k in range(4)]
