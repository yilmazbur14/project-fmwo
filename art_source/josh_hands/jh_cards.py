"""Cards: Josh's trading cards (a hard black edge, an inset border, a suit pip) as any quad, so a card
can be a facet of the paper-craft hand (a fan wedge, a tapering phalanx) or a plain card in flight, at
any of four tones so a hand built of them carries a real light ramp (lit from the upper left).
"""
import math

import jh_lib as H

FACE = ['0', '9', '8', '7']              # cream: F6EFDC E6DBBE C8B994 9E8D68
GILT = ['O', 'o', 'G', 'g']              # gold:  F5D94E E0AB35 B07D22 7A5216
CREAM_EDGE = ['9', '8', '7', '6']
BACK_FIELD = ['z', 'y', 'x', 'w']        # wine:  A63B4B 7A2032 4D1420 2B0A12
BACK_LINE = ['y', 'x', 'w', 'w']
RED = ['R', 'R', 'V', 'V']
LIT = {'O': 'Y', 'o': 'O', 'G': 'o', 'g': 'G', '9': '0', '8': '9', '7': '8', '6': '7'}

PIPS3 = {
    'spade': ['.k.', 'kkk', 'k.k'],
    'heart': ['r.r', 'rrr', '.r.'],
    'diamond': ['.r.', 'rrr', '.r.'],
    'club': ['.k.', 'kkk', '.k.'],
}
PIPS5 = {
    'spade': ['..k..', '.kkk.', 'kkkkk', 'kk.kk', '..k..'],
    'heart': ['.r.r.', 'rrrrr', 'rrrrr', '.rrr.', '..r..'],
    'diamond': ['..r..', '.rrr.', 'rrrrr', '.rrr.', '..r..'],
    'club': ['..k..', '.kkk.', 'kkkkk', 'kkkkk', '..k..'],
}
SUITS = ['spade', 'heart', 'club', 'diamond']


# ------------------------------------------------------------------ cards as any quad
# For the hand: a card is a facet of the paper-craft, so it can be a trapezoid (foreshortened, or
# tapering along a finger). corners: four (x, y) points in order round the card.

def quad(corners_, tone=0, side='face', pip=None, gilt=True, pip_big=None, keyed=True, lit_sides=True,
         mark=True):
    body = H.JL.poly([(float(x), float(y)) for x, y in corners_])
    if not body:
        return {}
    tone = max(0, min(3, tone))
    part = {}
    inner = set()
    edge_k = (GILT if gilt else CREAM_EDGE)[tone]
    for (x, y) in body:
        n4 = [(x + 1, y) in body, (x - 1, y) in body, (x, y + 1) in body, (x, y - 1) in body]
        if not all(n4):
            k = edge_k
            if lit_sides and (not n4[1] or not n4[3]) and n4[0] and n4[2]:
                k = LIT.get(edge_k, edge_k)
        elif side == 'face':
            k = FACE[tone]
            inner.add((x, y))
        else:
            k = BACK_FIELD[tone]
            if (x + y) % 4 == 0 or (x - y) % 4 == 0:
                k = BACK_LINE[tone]
            inner.add((x, y))
        part[(x, y)] = k
    mx = sum(c[0] for c in corners_) / 4.0
    my = sum(c[1] for c in corners_) / 4.0
    if side == 'face' and pip:
        xs = [x for x, y in body]
        ys = [y for x, y in body]
        big = pip_big if pip_big is not None else (min(max(xs) - min(xs), max(ys) - min(ys)) >= 10)
        rows = (PIPS5 if big else PIPS3)[pip]
        pw, ph = len(rows[0]), len(rows)
        ox, oy = int(round(mx - (pw - 1) / 2.0)), int(round(my - (ph - 1) / 2.0))
        red = RED[tone]
        for r, row in enumerate(rows):
            for c, ch in enumerate(row):
                q = (ox + c, oy + r)
                if ch != '.' and q in inner:
                    part[q] = red if ch == 'r' else 'k'
    elif side == 'back':
        xs = [x for x, y in body]
        ys = [y for x, y in body]
        if min(max(xs) - min(xs), max(ys) - min(ys)) >= 7:
            ox, oy = int(round(mx - 1)), int(round(my - 1))
            for r, row in enumerate(PIPS3['spade']):
                for c, ch in enumerate(row):
                    q = (ox + c, oy + r)
                    if ch != '.' and q in inner:
                        part[q] = GILT[min(tone, 2)]
    return H.keyline(part) if keyed else part


def seg(p0, p1, w0, w1, back=0.0, fwd=0.0):
    """A trapezoid along p0 -> p1, w0 wide at p0 and w1 at p1, extended `back` before p0 and `fwd`
    past p1 along the axis. Corners in order."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    a = (p0[0] - ux * back, p0[1] - uy * back)
    b = (p1[0] + ux * fwd, p1[1] + uy * fwd)
    return [(a[0] + nx * w0 / 2.0, a[1] + ny * w0 / 2.0), (b[0] + nx * w1 / 2.0, b[1] + ny * w1 / 2.0),
            (b[0] - nx * w1 / 2.0, b[1] - ny * w1 / 2.0), (a[0] - nx * w0 / 2.0, a[1] - ny * w0 / 2.0)]


def quad_uv(corners_, tone=0, side='face', pip=None, gilt=True, pip_uv=None, keyed=True):
    """quad(), with the pip at (u, v) of the card: v along from the corner-0 end (0..1), u across from
    the corner-0 side (0..1). None puts it at the centre. A pip off-centre is the small corner index;
    a centred one on a big card is the big pip."""
    if pip_uv is None or side != 'face' or not pip:
        return quad(corners_, tone, side, pip, gilt, keyed=keyed)
    a, b, c, d = corners_
    u, v = pip_uv
    p0 = (a[0] + (b[0] - a[0]) * v, a[1] + (b[1] - a[1]) * v)
    p1 = (d[0] + (c[0] - d[0]) * v, d[1] + (c[1] - d[1]) * v)
    px_, py_ = p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u
    part = quad(corners_, tone, side, None, gilt, keyed=False)
    if not part:
        return {}
    inner = {q for q in part if all((q[0] + dx, q[1] + dy) in part for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    xs = [x for x, y in part]
    ys = [y for x, y in part]
    big = u == 0.5 and min(max(xs) - min(xs), max(ys) - min(ys)) >= 12
    rows = (PIPS5 if big else PIPS3)[pip]
    pw, ph = len(rows[0]), len(rows)
    ox, oy = int(round(px_ - (pw - 1) / 2.0)), int(round(py_ - (ph - 1) / 2.0))
    red = RED[max(0, min(3, tone))]
    for r, row in enumerate(rows):
        for cc, ch in enumerate(row):
            q = (ox + cc, oy + r)
            if ch != '.' and q in inner:
                part[q] = red if ch == 'r' else 'k'
    return H.keyline(part) if keyed else part
