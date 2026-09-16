"""Final keycap icons: key_q.png (32x32), key_w.png (32x32), key_arrows.png (96x64)."""
import os
from common import Canvas, write_png, validate_png
from keys import COL, orient, sheet, composite_on
from cmp2 import body_variant
from glyphs2 import BOLD

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')

BODY = 3
Q = BOLD['Q_bold1']   # ring 14 wide, tail breaks out bottom-right
W = BOLD['W_bold1']
ARROW = BOLD['A_bold1']


def key(glyph, body_w=None):
    c = Canvas(32, 32)
    c.grid(0, 0, [''.join(r) for r in body_variant(BODY)], COL)
    gh, gw = len(glyph), len(glyph[0])
    bw = body_w or gw
    x0 = int(round(15.5 - bw / 2 + 0.5))
    y0 = int(round(12.5 - gh / 2 + 0.5))
    for j, row in enumerate(glyph):
        for i, ch in enumerate(row):
            if ch == 'X':
                c.set(x0 + i, y0 + j, COL['g'])
    return c


def build():
    kq = key(Q, body_w=14)
    kw = key(W)
    arrows = Canvas(96, 64)
    arrows.blit(key(orient(ARROW, 'up')), 32, 0)
    arrows.blit(key(orient(ARROW, 'left')), 0, 32)
    arrows.blit(key(orient(ARROW, 'down')), 32, 32)
    arrows.blit(key(orient(ARROW, 'right')), 64, 32)
    return kq, kw, arrows


if __name__ == '__main__':
    kq, kw, arrows = build()
    kq.save(os.path.join(OUT, 'key_q.png'))
    kw.save(os.path.join(OUT, 'key_w.png'))
    arrows.save(os.path.join(OUT, 'key_arrows.png'))
    # symmetry checks on the body (mirror about x=15.5 for silhouette/outline)
    body = body_variant(BODY)
    for y in range(32):
        for x in range(32):
            a = body[y][x] == ' '
            b = body[y][31 - x] == ' '
            assert a == b, ('silhouette asymmetry', x, y)
            assert (body[y][x] == '#') == (body[y][31 - x] == '#'), ('outline asymmetry', x, y)
    # glyph checks: up/down arrows mirror-symmetric, left = mirror of right
    up = orient(ARROW, 'up')
    assert all(r == r[::-1] for r in up), 'up arrow not symmetric'
    assert orient(ARROW, 'left') == [r[::-1] for r in orient(ARROW, 'right')]
    assert orient(ARROW, 'down') == list(reversed(up))
    assert all(r == r[::-1] for r in W), 'W not symmetric'
    print('saved + checks passed')
