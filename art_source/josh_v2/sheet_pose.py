"""Shared pose helpers for the new sheet frames (telegraph / recover / hit / defeated)."""
from jlib import *
import idle as I
import parts as P
import head as HD

TH_LIMB = [0.0, 0.35, 0.6, 0.85, 0.98]
SK = I.SKIN


def offset_pts(pts, dx, dy):
    return [(x + dx, y + dy) for (x, y) in pts]


def limb(c, poly, a, b, r0, r1, th=TH_LIMB):
    I.hf_shade(c, poly_mask(poly), lambda px, py: I.hcap(px, py, a[0], a[1], b[0], b[1], r0, r1), SK, th)


def limb_bulge(c, poly, a, b, r0, r1, dome, th=TH_LIMB):
    cx, cy, rx, ry, amp = dome
    I.hf_shade(c, poly_mask(poly), lambda px, py: max(I.hcap(px, py, a[0], a[1], b[0], b[1], r0, r1),
                                                      I.hdome(px, py, cx, cy, rx, ry, amp)), SK, th)


def torso(c, dx=0, dy=0, poly=None, hfn=None, th=(0.05, 0.4, 0.66, 0.88, 0.985)):
    poly = poly or offset_pts(I.G['body'], dx, dy)
    hfn = hfn or (lambda px, py: I.torso_h(px - dx, py - dy))
    m = poly_mask(poly)
    I.hf_shade(c, m, hfn, SK, list(th), crease=3, crease_th=1.1, zscale=0.9)
    despeckle(c, region=m)
    return m


def boots(c, dxn=0, dxf=0, dy=0):
    I.draw_boot(c, offset_pts(I.G['n_boot'], dxn, dy), shaft=(16 + dxn, 29 + dxn), toe=(14 + dxn, 61 + dy))
    I.draw_boot(c, offset_pts(I.G['f_boot'], dxf, dy), shaft=(38 + dxf, 50 + dxf), toe=(52 + dxf, 61 + dy))


def speedo(c, dx=0, dy=0):
    x, y, rows = P.SPEEDO
    block(c, x + dx, y + dy, rows)


def head(c, eyes, mouth, dx=0, dy=0, extra=None):
    hc = blank()
    HD.build_head(hc, eyes, mouth)
    if extra:
        extra(hc)
    composite(c, shift_canvas(hc, dx, dy))


def finish(c):
    """Pre-shift canvases are drawn one row high like the idle: drop 1 so boots land on row 63."""
    assert all(ch == '.' for ch in c[63]), 'row 63 not empty before shift'
    return [['.'] * W] + c[:63]
