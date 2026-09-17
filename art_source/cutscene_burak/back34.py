"""3/4-back view parts: Burak turned toward the poster (up-right, away from camera)."""
import math
from blib import *
import rig

HOOD_R = 'EDCBA'

# hood from behind, head tilted up toward the poster; a sliver of cheek/nose past the rim on the right
HEAD_B34 = """
.......#######........
.....##AAABBBB##......
...##AAAABBBBBBC##....
..#AAAAACBBBBBBCCC#...
.#AAAAAACBBBBBBCCCB#..
.#AAAAABCBBBBBBCCCBB#.
#AAAAABBCBBBBBCCCDB#h#
#AAAABBBCBBBBBCCCDB#s#
#AAAABBBCBBBBCCCDDB#s#
#BBBBBBBCBBBBCCCDDB#d#
#BBBBBBCCBBBCCCDDDB#f#
#BBBBBBCBBBBCCCDDB#f#.
#CBBBBBCBBBCCCDDDB##..
.#CBBBBCBBBCCCDDDB#...
.#CCBBBCBBCCCDDDDB#...
..#CCBCCBCCCDDDDD#....
..#DCCCCCCCCDDDDDE#...
.#DDDCCCCCCCDDDDEEE#..
#EDDDDDDDDDDDDDEEEEE#.
"""


def torso_b34(L, dy=0):
    """Back of the hoodie with both hands in the front pocket (elbows out)."""
    back = [(23, 31), (38, 31), (41.5, 33.5), (40.5, 40), (39.5, 46), (39.5, 49.5), (22, 49.5), (21.5, 46), (20.5, 40),
            (19.5, 33.5)]
    back = [(x, y + dy) for x, y in back]
    # far (left) arm first, behind the back
    FA = layer()
    m = m_or(tcapsule_mask(21.5, 34.5 + dy, 18.8, 41.5 + dy, 3.3, 2.9), tcapsule_mask(18.8, 41.5 + dy, 23.5, 45.5 + dy, 2.9, 2.6))

    def nf(x, y):
        return tcapsule_normal(x, y, 21.5, 34.5 + dy, 18.8, 41.5 + dy, 3.3, 2.9)
    paint_part(FA, m, lambda x, y: quant(lambert_wrap(nf(x, y), wrap=0.35), HOOD_R, [0.3, 0.5, 0.72, 0.9]))
    B = layer()
    bm = poly_mask(back)
    cx = 30.0

    def fn(x, y):
        nx = max(-0.95, min(0.95, (x + 0.5 - cx) / 11.5))
        n = (nx, -0.2, math.sqrt(1 - nx * nx))
        return quant(lambert_wrap(n, wrap=0.25), HOOD_R, [0.16, 0.36, 0.62, 0.86])
    paint_part(B, bm, fn)
    # hem rib band
    for x in range(W):
        for y in (47 + dy, 48 + dy):
            if 0 <= y < H and bm[y][x] and B[y][x] != '#':
                B[y][x] = 'E' if y == 47 + dy else ('C' if B[y][x] in 'AB' else 'D')
    # near (right) arm on top
    NA = layer()
    m2 = m_or(tcapsule_mask(39.5, 34.5 + dy, 42.2, 41.5 + dy, 3.4, 3.0), tcapsule_mask(42.2, 41.5 + dy, 38.5, 45.5 + dy, 3.0, 2.7))

    def nn(x, y):
        return tcapsule_normal(x, y, 39.5, 34.5 + dy, 42.2, 41.5 + dy, 3.4, 3.0)
    paint_part(NA, m2, lambda x, y: quant(lambert_wrap(nn(x, y), wrap=0.35), HOOD_R, [0.2, 0.42, 0.66, 0.88]))
    composite(L, FA)
    composite(L, B)
    composite(L, NA)
    return L


def shoe_back(ankle, dark=False):
    """Foreshortened shoe seen from behind-left, toe pointing up-right into the scene."""
    ax, ay = ankle
    pts = [(ax - 2.6, ay - 1.2), (ax + 2.0, ay - 1.6), (ax + 4.4, ay + 0.4), (ax + 4.6, ay + 3.0), (ax + 3.6, ay + 5.0),
           (ax - 2.4, ay + 5.0), (ax - 3.2, ay + 3.2)]
    m = rig.ss_poly_mask(pts)
    L = layer()
    body, hi, sole = ('x', 'O', 'O') if dark else ('O', 'o', 'e')

    def fn(x, y):
        if y + 0.5 > ay + 3.4:
            return sole
        if x + 0.5 < ax - 0.5 and y + 0.5 < ay + 2.0:
            return hi
        return body
    paint_part(L, m, fn)
    return L


if __name__ == '__main__':
    from heads import rows
    import prod
    cv = layer()
    torso_b34(cv)
    Hd = layer()
    blk(Hd, 20, 13, rows(HEAD_B34))
    fl, fs = prod.grounded_leg((31.0, 47), ((33, 59), 0.0, 0), 'far')
    nl, ns = prod.grounded_leg((29.0, 47), ((28, 59), 0.0, 0), 'near')
    out = compose([fl, fs, nl, ns, cv, Hd])
    preview(outer_outline(out), 'out/b34_test_8x.png', s=8)
    print('ok')
