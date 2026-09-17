"""Assemble 3/4-back frames."""
from blib import *
import rig, prod, back34_parts as BP
from back34 import shoe_back
from lace import draw_lace


def back_leg(hip, ankle, shade):
    LG, _ = rig.build_leg2(hip, ankle, shade=shade)
    S = shoe_back(ankle, dark=(shade == 'far'))
    dy = 63 - prod.lowest_row(S)
    if dy:
        LG, _ = rig.build_leg2(hip, (ankle[0], ankle[1] + dy), shade=shade)
        S = shoe_back((ankle[0], ankle[1] + dy), dark=(shade == 'far'))
    return LG, S


def build_b34(p):
    hx, hy = 30, 47
    up = p.get('up', 0)          # upper body raise (breath / startle)
    hip_up = p.get('hip_up', 0)
    if p.get('legs') == 'back':
        FL, FS = back_leg((hx + 1.5, hy - hip_up), (27, 59), 'far')
        NL, NS = back_leg((hx - 0.5, hy - hip_up), (33, 59), 'near')
        legs = [FL, FS, NL, NS]
    else:
        FL, FS = prod.grounded_leg((hx + 1.0, hy - hip_up), prod.foot('flat', 28), 'far')
        NL, NS = prod.grounded_leg((hx - 1.0, hy - hip_up), prod.foot('flat', 33), 'near')
        legs = [FL, FS, NL, NS]
    cv = compose(legs)
    # front glove peeking past the right side (behind the body)
    T = layer()
    x0, y0, r = BP.rows_of(BP.TORSO_B34)
    blk(T, x0, y0 - up, r)
    prod.cast_shadow(cv, T)
    cv = compose([cv, T])
    Hd = layer()
    hxo, hyo = p.get('head_at', (20, 13))
    blk(Hd, hxo, hyo - up - p.get('head_up', 0), p.get('head', blk_rows(BP.HEAD_B34)))
    prod.cast_shadow(cv, Hd)
    cv = compose([cv, Hd])
    gb = p.get('gb', (30, 33))
    GB = layer()
    blk(GB, gb[0], gb[1] - up, prod.glove(mirror=True))
    prod.cast_shadow(cv, GB)
    lt = p.get('lace_top', (38, 31))
    draw_lace(cv, [(gb[0] + 4, gb[1] - up + 1), (gb[0] + 5, gb[1] - up), (lt[0] - 2, lt[1] - up - 1), (lt[0], lt[1] - up),
                   (lt[0] + 3, lt[1] - up + 1)])
    cv = compose([cv, GB])
    blk(cv, gb[0], gb[1] - up, prod.glove(mirror=True)[:3])
    FX = layer()
    for f in p.get('fx', []):
        if f[0] == 'rows':
            prod.fx_rows(FX, f[1], f[2], f[3])
    cv = compose([cv, FX])
    return prod.cleanup(outer_outline(cv))


if __name__ == '__main__':
    a = build_b34(dict(legs='side'))
    b = build_b34(dict(legs='back'))
    c = build_b34(dict(legs='back', up=1))
    preview([a, b, c], 'out/b34_v2_8x.png', s=7)
    print('ok')
