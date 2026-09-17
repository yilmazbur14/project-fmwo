"""Shared helpers for Carter v2: palette, grid IO, part rasterising, previews."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pngio import read_png, write_png

# ---------------------------------------------------------------- palette
# one char per colour. '.' = transparent.
PAL = {
    '.': (0, 0, 0, 0),
    '#': (0, 0, 0, 255),          # outline
    # skin ramp (matches Liam / Mason cast)
    'W': (255, 255, 255, 255),    # gloss / sclera
    'H': (251, 214, 176, 255),    # highlight  #fadcb8
    's': (240, 185, 142, 255),    # base       #eec39a
    'm': (219, 151, 108, 255),    # cel shadow #d9a066
    'd': (184, 108, 78, 255),     # deep shadow#b8794a
    'D': (132, 65, 47, 255),      # crevice    #8a5236
    # beard (orange, portrait #b05b21 sits in the shadow band)
    'O': (240, 144, 64, 255),     # beard highlight
    'o': (214, 108, 40, 255),     # beard base
    'r': (176, 91, 33, 255),      # beard shadow  #b05b21 (portrait)
    'R': (112, 52, 20, 255),      # beard deep / brows
    # eyes
    'i': (74, 44, 26, 255),       # iris dark brown
    # earring silver (portrait #9badb7)
    'c': (230, 236, 242, 255),    # silver light
    'C': (155, 173, 183, 255),    # silver base #9badb7
    'x': (94, 108, 120, 255),     # silver dark
    # speedo blue (old sheet ramp + deep)
    'B': (98, 150, 244, 255),     # blue highlight
    'b': (58, 111, 216, 255),     # blue base #3a6fd8
    'u': (40, 80, 168, 255),      # blue shadow #2850a8
    'U': (26, 50, 112, 255),      # blue deep
    # boots
    'g': (90, 90, 106, 255),    # boot shine
    'k': (34, 34, 43, 255),       # boot base
    'K': (17, 17, 23, 255),       # boot shadow
    'q': (56, 56, 69, 255),       # boot mid (Josh #383845)
    'n': (226, 210, 176, 255),    # dust light
    'N': (176, 156, 120, 255),    # dust dark
    # fx
    'f': (255, 255, 255, 255),    # speed line white (no outline required)
    'F': (190, 214, 255, 255),    # speed line pale blue
    'L': (120, 150, 200, 255),    # speed line mid
}
INV = {v: k for k, v in PAL.items() if k not in ('f',)}


def blank(w=64, h=64, ch='.'):
    return [[ch] * w for _ in range(h)]


def grid_to_pix(g):
    return [[PAL[c] for c in row] for row in g]


def load_grid(path):
    """Grid text: lines 'NN|<64 chars>|'. Lines not matching are ignored."""
    rows = {}
    with open(path) as f:
        for ln in f:
            ln = ln.rstrip('\n')
            if len(ln) > 3 and ln[2] == '|' and ln[:2].strip().isdigit():
                y = int(ln[:2])
                body = ln[3:]
                if body.endswith('|'):
                    body = body[:-1]
                rows[y] = body
    h = max(rows) + 1
    w = max(len(r) for r in rows.values())
    g = []
    for y in range(h):
        r = rows.get(y, '')
        if len(r) != w:
            raise ValueError('%s row %d has width %d (want %d)' % (path, y, len(r), w))
        for c in r:
            if c not in PAL:
                raise ValueError('%s row %d unknown char %r' % (path, y, c))
        g.append(list(r))
    return g


def save_grid(path, g):
    w = len(g[0])
    with open(path, 'w') as f:
        f.write('   ' + ''.join(str(x // 10) for x in range(w)) + '\n')
        f.write('   ' + ''.join(str(x % 10) for x in range(w)) + '\n')
        for y, row in enumerate(g):
            f.write('%02d|%s|\n' % (y, ''.join(row)))


def zoom(pix, s, bg='checker'):
    h = len(pix); w = len(pix[0])
    out = []
    for Y in range(h * s):
        y = Y // s
        row = []
        for X in range(w * s):
            p = pix[y][X // s]
            if p[3] == 0:
                if bg == 'checker':
                    c = 205 if ((X // (s * 4) + Y // (s * 4)) % 2 == 0) else 178
                    p = (c, c, c, 255)
                else:
                    p = bg
            row.append(p)
        out.append(row)
    return out


def hcat(imgs, gap=8, bg=(245, 245, 245, 255)):
    H = max(len(i) for i in imgs)
    W = sum(len(i[0]) for i in imgs) + gap * (len(imgs) + 1)
    out = [[bg] * W for _ in range(H + 2 * gap)]
    x0 = gap
    for im in imgs:
        for y, row in enumerate(im):
            out[y + gap][x0:x0 + len(row)] = row
        x0 += len(im[0]) + gap
    return out


def save(path, pix):
    write_png(path, len(pix[0]), len(pix), pix)


def crop_pix(pix, x, y, w, h):
    return [row[x:x + w] for row in pix[y:y + h]]


def mirror_x(x):
    return 63 - x
