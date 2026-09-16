"""Shared helpers for the FMWO UI kit: DB32 palette, grid -> pixels, 9-slice
validation and compositing. Pure python (no PIL available)."""
from pngio import read_png, write_png, upscale

DB32 = """000000 222034 45283c 663931 8f563b df7126 d9a066 eec39a fbf236 99e550
6abe30 37946e 4b692f 524b24 323c39 3f3f74 306082 5b6ee1 639bff 5fcde4 cbdbfc
ffffff 9badb7 847e87 696a6a 595652 76428a ac3232 d95763 d77bba 8f974a 8a6f30""".split()
DB32_SET = set(DB32)
assert len(DB32) == 32


def hex2rgba(h):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


TRANSPARENT = (0, 0, 0, 0)


def grid_to_pix(grid, pal):
    """grid: list of equal-length strings. pal: role char -> hex (no #).
    '.' is transparent."""
    h = len(grid)
    w = len(grid[0])
    pix = []
    for y, row in enumerate(grid):
        assert len(row) == w, f"row {y} has len {len(row)} != {w}: {row!r}"
        out = []
        for x, ch in enumerate(row):
            if ch == '.':
                out.append(TRANSPARENT)
            else:
                assert ch in pal, f"role {ch!r} at ({x},{y}) not in palette"
                hx = pal[ch].lower()
                assert hx in DB32_SET, f"role {ch!r} -> {hx} is not DB32"
                out.append(hex2rgba(hx))
        pix.append(out)
    return w, h, pix


def check_db32(w, h, pix, name=""):
    bad = set()
    for row in pix:
        for p in row:
            if p[3] == 0:
                continue
            if p[3] != 255:
                bad.add(('alpha', p))
                continue
            hx = '%02x%02x%02x' % p[:3]
            if hx not in DB32_SET:
                bad.add(hx)
    return bad


def check_nine_slice(w, h, pix, m):
    """Checks that a 9-slice texture with uniform margin m stretches cleanly:
    - top/bottom edge regions constant along x
    - left/right edge regions constant along y
    - centre is a single flat colour
    - bleed safety: the corner column/row adjacent to an edge equals the edge
      profile, and the edge row/col adjacent to the centre equals the centre
      colour is NOT required (bevel lines may sit there), but reported.
    Returns list of problems (empty == OK)."""
    probs = []
    x0, x1 = m, w - m          # edge span [x0, x1)
    y0, y1 = m, h - m
    # top & bottom edges: each row constant across x in [x0,x1)
    for y in list(range(0, m)) + list(range(h - m, h)):
        ref = pix[y][x0]
        for x in range(x0, x1):
            if pix[y][x] != ref:
                probs.append(f"horizontal edge row y={y} not constant at x={x}")
                break
    # left & right edges: each column constant across y in [y0,y1)
    for x in list(range(0, m)) + list(range(w - m, w)):
        ref = pix[y0][x]
        for y in range(y0, y1):
            if pix[y][x] != ref:
                probs.append(f"vertical edge col x={x} not constant at y={y}")
                break
    # centre flat
    ref = pix[y0][x0]
    flat = all(pix[y][x] == ref for y in range(y0, y1) for x in range(x0, x1))
    if not flat:
        probs.append("centre is not a single flat colour")
    # bleed safety: corner columns adjacent to the top/bottom edge span
    for y in list(range(0, m)) + list(range(h - m, h)):
        if pix[y][x0 - 1] != pix[y][x0]:
            probs.append(f"bleed: corner col x={x0-1} differs from edge at y={y}")
        if pix[y][x1] != pix[y][x1 - 1]:
            probs.append(f"bleed: corner col x={x1} differs from edge at y={y}")
    for x in list(range(0, m)) + list(range(w - m, w)):
        if pix[y0 - 1][x] != pix[y0][x]:
            probs.append(f"bleed: corner row y={y0-1} differs from edge at x={x}")
        if pix[y1][x] != pix[y1 - 1][x]:
            probs.append(f"bleed: corner row y={y1} differs from edge at x={x}")
    return probs


def nine_slice(w, h, pix, m, W, H):
    """Proper 9-slice with uniform margin m: corners copied 1:1, edges and
    centre stretched with nearest-neighbour sampling. Returns W x H pixels."""
    cw, ch = w - 2 * m, h - 2 * m          # source centre size
    CW, CH = W - 2 * m, H - 2 * m          # dest centre size
    assert CW > 0 and CH > 0

    def mapc(D, dst_c, src_c):
        # map a destination coordinate to a source coordinate on one axis
        if D < m:
            return D
        if D >= m + dst_c:
            return D - (m + dst_c) + (m + src_c)
        return m + min(src_c - 1, int((D - m) * src_c / dst_c))

    xs = [mapc(X, CW, cw) for X in range(W)]
    ys = [mapc(Y, CH, ch) for Y in range(H)]
    return [[pix[ys[Y]][xs[X]] for X in range(W)] for Y in range(H)]


def scale_nn(w, h, pix, s):
    return w * s, h * s, [[pix[Y // s][X // s] for X in range(w * s)] for Y in range(h * s)]


def blit(dst, src, ox, oy):
    """alpha-over blit (binary alpha is all we use)."""
    for y, row in enumerate(src):
        Y = oy + y
        if Y < 0 or Y >= len(dst):
            continue
        drow = dst[Y]
        for x, p in enumerate(row):
            X = ox + x
            if X < 0 or X >= len(drow):
                continue
            if p[3] == 255:
                drow[X] = p
            elif p[3] > 0:
                a = p[3] / 255.0
                q = drow[X]
                drow[X] = tuple(int(p[i] * a + q[i] * (1 - a)) for i in range(3)) + (255,)


def solid(W, H, c):
    return [[c for _ in range(W)] for _ in range(H)]


def crop(pix, x, y, w, h):
    return [row[x:x + w] for row in pix[y:y + h]]
