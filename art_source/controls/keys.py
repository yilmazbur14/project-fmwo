"""Keycap icons for the controls screen. 32x32 per key, DB32 only."""
from common import Canvas, zoom, write_png, read_png, upscale, DB32
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
os.makedirs(OUT, exist_ok=True)

# keycap ramp (cool greys, light from top-left like the cast sprites)
COL = {
    '#': '000000',  # outline
    'W': 'ffffff',  # top-face rim highlight
    'L': 'cbdbfc',  # top face
    'M': '9badb7',  # top-face shade rim / lit left skirt
    'D': '847e87',  # front skirt
    'S': '696a6a',  # shadowed skirt
    'X': '595652',  # deepest skirt corner
    'g': '222034',  # legend
}


def inside(x, y):
    if not (1 <= x <= 30 and 1 <= y <= 30):
        return False
    for cx, cy, dx, dy in [(1, 1, 1, 1), (30, 1, -1, 1), (1, 30, 1, -1), (30, 30, -1, -1)]:
        if (x - cx) * dx + (y - cy) * dy < 2:
            return False
    return True


def keycap_grid():
    g = [[' '] * 32 for _ in range(32)]
    for y in range(32):
        for x in range(32):
            if not inside(x, y):
                continue
            edge = any(not inside(x + a, y + b) for a, b in [(1, 0), (-1, 0), (0, 1), (0, -1)])
            if edge:
                g[y][x] = '#'
                continue
            # --- top face: x 4..27, y 2..23
            if 4 <= x <= 27 and 2 <= y <= 23:
                if (x, y) in [(4, 23), (27, 23), (27, 2)]:
                    c = 'M'
                elif (x, y) == (4, 2):
                    c = 'W'
                elif y == 2 or x == 4:
                    c = 'W'
                elif x == 27 or y == 23:
                    c = 'M'
                else:
                    c = 'L'
                g[y][x] = c
                continue
            # --- side / front skirts
            if y <= 23:
                g[y][x] = 'M' if x < 4 else 'S'
                continue
            # below the top face: diagonal joins from face corners to base corners
            t = (y - 23) / 6.0  # 0 at face bottom, 1 at base
            left_join = 4 - 2 * t
            right_join = 27 + 2 * t
            if x < left_join - 0.01:
                g[y][x] = 'M'
            elif x > right_join + 0.01:
                g[y][x] = 'X'
            else:
                g[y][x] = 'D' if y <= 26 else 'S'
    # darken the right end of the front skirt a touch for roundness
    for y in range(24, 30):
        for x in range(25, 30):
            if g[y][x] == 'D':
                g[y][x] = 'S'
            elif g[y][x] == 'S' and x >= 27:
                g[y][x] = 'X'
    return g


GLYPHS = {
    'Q_a': [
        "..XXXXXXXX...",
        ".XXXXXXXXXX..",
        "XXX......XXX.",
        "XX........XX.",
        "XX........XX.",
        "XX........XX.",
        "XX........XX.",
        "XX...XX...XX.",
        "XX....XX..XX.",
        "XXX....XXXXX.",
        ".XXXXXXXXXX..",
        "..XXXXXXXXXX.",
        "..........XXX",
    ],
    'Q_b': [
        "..XXXXXXXX..",
        ".XXXXXXXXXX.",
        "XXX......XXX",
        "XX........XX",
        "XX........XX",
        "XX........XX",
        "XX........XX",
        "XX....XX..XX",
        "XXX....XXXXX",
        ".XXXXXXXXXX.",
        "..XXXXXXXXXX",
        "..........XX",
    ],
    'Q_c': [
        "..XXXXXXX...",
        ".XXXXXXXXX..",
        "XXX.....XXX.",
        "XX.......XX.",
        "XX.......XX.",
        "XX.......XX.",
        "XX.......XX.",
        "XX...XX..XX.",
        "XXX...XXXXX.",
        ".XXXXXXXXX..",
        "..XXXXXXXXX.",
        ".........XXX",
    ],
    'W_a': [
        "XX........XX",
        "XX........XX",
        "XX........XX",
        "XX........XX",
        "XX........XX",
        "XX...XX...XX",
        "XX...XX...XX",
        "XX..XXXX..XX",
        "XX.XX..XX.XX",
        "XXXX....XXXX",
        "XXX......XXX",
        "XX........XX",
    ],
    'W_b': [
        "XX........XX",
        "XX........XX",
        "XX........XX",
        "XX........XX",
        "XX...XX...XX",
        "XX...XX...XX",
        "XX...XX...XX",
        "XX...XX...XX",
        "XX...XX...XX",
        "XXX.XXXX.XXX",
        ".XXXX..XXXX.",
        "..XX....XX..",
    ],
    'W_c': [
        "XX........XX",
        "XX........XX",
        "XX........XX",
        "XX........XX",
        "XX...XX...XX",
        "XX...XX...XX",
        ".XX.XXXX.XX.",
        ".XX.XXXX.XX.",
        ".XXXX..XXXX.",
        "..XXX..XXX..",
        "..XX....XX..",
        "..XX....XX..",
    ],
    'A_a': [
        ".....XX.....",
        "....XXXX....",
        "...XXXXXX...",
        "..XXXXXXXX..",
        ".XXXXXXXXXX.",
        "XXXXXXXXXXXX",
        "....XXXX....",
        "....XXXX....",
        "....XXXX....",
        "....XXXX....",
        "....XXXX....",
        "....XXXX....",
    ],
    'A_b': [
        ".....XX.....",
        "....XXXX....",
        "...XXXXXX...",
        "..XXXXXXXX..",
        ".XXXXXXXXXX.",
        "XXXXXXXXXXXX",
        ".....XX.....",
        ".....XX.....",
        ".....XX.....",
        ".....XX.....",
        ".....XX.....",
        ".....XX.....",
    ],
    'A_c': [
        "....XX....",
        "...XXXX...",
        "..XXXXXX..",
        ".XXXXXXXX.",
        "XXXXXXXXXX",
        "...XXXX...",
        "...XXXX...",
        "...XXXX...",
        "...XXXX...",
        "...XXXX...",
    ],
}


def rot_cw(rows):
    """rotate glyph 90 degrees clockwise"""
    h, w = len(rows), len(rows[0])
    return [''.join(rows[h - 1 - j][i] for j in range(h)) for i in range(w)]


def flip_v(rows):
    return list(reversed(rows))


def orient(rows, d):
    if d == 'up':
        return rows
    if d == 'right':
        return rot_cw(rows)
    if d == 'down':
        return flip_v(rows)
    if d == 'left':
        return [r[::-1] for r in rot_cw(rows)]
    raise ValueError(d)


def make_key(glyph_rows, dx=0, dy=0, legend='g', body_w=None):
    c = Canvas(32, 32)
    g = keycap_grid()
    c.grid(0, 0, [''.join(r) for r in g], COL)
    gh, gw = len(glyph_rows), len(glyph_rows[0])
    bw = body_w if body_w is not None else gw
    # legend area x 5..26, y 3..22  -> centre (15.5, 12.5)
    x0 = int(round(15.5 - bw / 2 + 0.5)) + dx
    y0 = int(round(12.5 - gh / 2 + 0.5)) + dy
    for j, row in enumerate(glyph_rows):
        for i, ch in enumerate(row):
            if ch == 'X':
                c.set(x0 + i, y0 + j, COL[legend])
    return c


def sheet(items, cols, cell=32, pad=0):
    rows = (len(items) + cols - 1) // cols
    s = Canvas(cols * cell + pad * (cols + 1), rows * cell + pad * (rows + 1))
    for k, it in enumerate(items):
        r, cc = divmod(k, cols)
        s.blit(it, pad + cc * (cell + pad), pad + r * (cell + pad))
    return s


def composite_on(canvas, bg_rgb, scale):
    """render canvas at scale over a solid colour -> (W,H,rows)"""
    rgba = canvas.to_rgba()
    W, H = canvas.w * scale, canvas.h * scale
    out = []
    for Y in range(H):
        row = []
        src = rgba[Y // scale]
        for X in range(W):
            p = src[X // scale]
            row.append(p if p[3] else bg_rgb + (255,))
        out.append(row)
    return W, H, out


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'variants'
    if mode == 'variants':
        items = []
        for name in ['Q_a', 'Q_b', 'Q_c', 'W_a', 'W_b', 'W_c']:
            body = 12 if name.startswith('Q') else None
            items.append(make_key(GLYPHS[name], body_w=body))
        for name in ['A_a', 'A_b', 'A_c']:
            items.append(make_key(GLYPHS[name]))
        s = sheet(items, 3, pad=4)
        W, H, px = composite_on(s, (34, 32, 52), 8)
        write_png(os.path.join(OUT, 'variants_8x.png'), W, H, px)
        print('ok', s.w, s.h)
