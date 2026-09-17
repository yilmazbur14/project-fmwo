"""Procedural hoodie sleeves with cuff + hand sprites."""
import math
from blib import *
import rig, parts

HOOD_R = 'EDCBA'


def sleeve(L, sh, el, wr, dark=False, r=(3.6, 3.1, 2.8), cuff=True):
    sx, sy = sh
    ex, ey = el
    wx, wy = wr
    r0, r1, r2 = r
    m = m_or(tcapsule_mask(sx, sy, ex, ey, r0, r1), tcapsule_mask(ex, ey, wx, wy, r1, r2))
    th = [0.16, 0.36, 0.60, 0.84] if not dark else [0.36, 0.60, 0.84, 0.99]
    flen = math.hypot(wx - ex, wy - ey) or 1
    ux, uy = (wx - ex) / flen, (wy - ey) / flen

    def nfn(x, y):
        d1 = seg_t(x + .5, y + .5, sx, sy, ex, ey)
        d2 = seg_t(x + .5, y + .5, ex, ey, wx, wy)
        e1 = math.hypot(x + .5 - d1[1], y + .5 - d1[2])
        e2 = math.hypot(x + .5 - d2[1], y + .5 - d2[2])
        if e1 <= e2:
            return tcapsule_normal(x, y, sx, sy, ex, ey, r0, r1)
        return tcapsule_normal(x, y, ex, ey, wx, wy, r1, r2)

    def fn(x, y):
        c = quant(lambert_wrap(nfn(x, y), wrap=0.35), HOOD_R, th)
        if cuff:
            al = (x + .5 - ex) * ux + (y + .5 - ey) * uy
            if al > flen - 1.6:
                c = {'A': 'C', 'B': 'C', 'C': 'D', 'D': 'E', 'E': 'E'}[c]
        return c
    paint_part(L, m, fn)
    return m


HANDS = {'fist': 'FIST6', 'fist_s': 'FIST', 'fist_big': 'FIST7', 'open': 'HAND_OPEN2'}


def hand(L, cx, cy, kind='fist', mirror=False, dark=False):
    rows = blk_rows(getattr(parts, HANDS[kind]))
    if mirror:
        rows = [s[::-1] for s in rows]
    if dark:
        mp = {'a': 's', 's': 'd', 'd': 'f', 'f': 'g'}
        rows = [''.join(mp.get(c, c) for c in s) for s in rows]
    w, h = len(rows[0]), len(rows)
    blk(L, int(round(cx - w / 2)), int(round(cy - h / 2)), rows)
