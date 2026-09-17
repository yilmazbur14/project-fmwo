"""Auto cel-shading for part-based block-ins, plus grid helpers used by the sheet frames."""
from shapes import *

RAMPS = {
    'skin': ['H', 's', 'm', 'd', 'D'],
    'blue': ['B', 'b', 'u', 'U', 'U'],
    'boot': ['g', 'q', 'k', 'K', 'K'],
    'beard': ['O', 'o', 'r', 'R', 'R'],
}
FX = set('fFL')


class Part:
    def __init__(self, name, z, mat, pix, rim=True, base=1, outline=True):
        self.name, self.z, self.mat, self.pix, self.rim, self.base, self.outline = name, z, mat, set(pix), rim, base, outline


def shade(parts, term_x=39, term_shift=1, w=64, h=64):
    """parts: list of Part. Returns (grid, label). Outline on the front part side of every edge."""
    label = [[None] * w for _ in range(h)]
    zmap = [[-1] * w for _ in range(h)]
    by = {}
    for p in sorted(parts, key=lambda p: p.z):
        by[p.name] = p
        for (x, y) in p.pix:
            if 0 <= x < w and 0 <= y < h and p.z >= zmap[y][x]:
                label[y][x] = p.name; zmap[y][x] = p.z
    g = blank(w, h)

    def inside(x, y, name):
        return 0 <= x < w and 0 <= y < h and label[y][x] == name

    for y in range(h):
        for x in range(w):
            L = label[y][x]
            if L is None:
                continue
            P = by[L]
            edge = False
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < w and 0 <= ny < h):
                    if ny >= h:
                        edge = True
                    continue
                M = label[ny][nx]
                if M is None or (M != L and zmap[ny][nx] < zmap[y][x]):
                    edge = True
                    break
            if edge and P.outline:
                g[y][x] = '#'
                continue
            ramp = RAMPS[P.mat]
            # distance to own boundary toward light (up / left) and away (down / right)
            ld = min(next((k for k in range(1, 20) if not inside(x - k, y, L)), 20),
                     next((k for k in range(1, 20) if not inside(x, y - k, L)), 20))
            sd = min(next((k for k in range(1, 20) if not inside(x + k, y, L)), 20),
                     next((k for k in range(1, 20) if not inside(x, y + k, L)), 20))
            t = P.base
            if P.rim and ld <= 2:
                t = 0
            if sd <= 2:
                t = 3
            elif sd <= 4:
                t = 2
            if x >= term_x:
                t += term_shift
            # occlusion: a front part directly above / left casts a shadow
            for dx, dy in ((-1, 0), (0, -1), (-1, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and label[ny][nx] is not None and zmap[ny][nx] > zmap[y][x]:
                    t = max(t, 3)
            g[y][x] = ramp[max(0, min(4, t))]
    return g, label


def paste(dst, src, dx=0, dy=0, skip='.'):
    for y in range(len(src)):
        for x in range(len(src[0])):
            c = src[y][x]
            if c == skip:
                continue
            X, Y = x + dx, y + dy
            if 0 <= X < len(dst[0]) and 0 <= Y < len(dst):
                dst[Y][X] = c
    return dst


def segs(dst, rows):
    """rows: {y: [(x, chars)]}; '.' skips."""
    for y, ss in rows.items():
        for x0, s in ss:
            for i, c in enumerate(s):
                if c != '.' and 0 <= x0 + i < 64:
                    dst[y][x0 + i] = c
    return dst


def mask_grid(g, pred):
    out = blank()
    for y in range(64):
        for x in range(64):
            if pred(x, y, g[y][x]):
                out[y][x] = g[y][x]
    return out


def erase(g, other):
    """remove pixels that are set in other."""
    for y in range(64):
        for x in range(64):
            if other[y][x] != '.':
                g[y][x] = '.'
    return g


def copyg(g):
    return [r[:] for r in g]


def fliph(g):
    return [list(reversed(r)) for r in g]


def outline_pass(g):
    """Safety: any opaque non-FX pixel touching transparency becomes outline."""
    out = copyg(g)
    for y in range(64):
        for x in range(64):
            c = g[y][x]
            if c in ('.', '#') or c in FX:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < 64 and 0 <= ny < 64 and g[ny][nx] == '.':
                    out[y][x] = '#'
                    break
    return out


def _px(g, lab, name):
    return [(x, y) for y in range(64) for x in range(64) if lab[y][x] == name and g[y][x] not in ('#', '.')]


def repaint_speedo(g, lab, name='speedo', cx=32):
    px = _px(g, lab, name)
    if not px:
        return g
    top = min(y for x, y in px); bot = max(y for x, y in px)
    for x, y in px:
        if y == top:
            c = 'B' if x < cx else 'b'
        elif y == top + 1:
            c = 'u'
        elif y == bot:
            c = 'U' if x >= cx - 3 else 'u'
        else:
            c = 'B' if (x < cx - 6 and y == top + 2) else ('b' if x < cx + 3 else 'u')
        g[y][x] = c
    return g


def repaint_abs(g, lab, y0, y1, cx=32, name='torso', half=7):
    """Front ab grid between y0..y1 around centre cx (groove at cx-1/cx), rows of 2 + groove."""
    for x, y in _px(g, lab, name):
        if not (y0 <= y <= y1 and abs(x - cx + 0.5) <= half + 3):
            continue
        rel = (y - y0) % 3
        if x == cx - 1:
            c = 'd'
        elif x == cx:
            c = 'D'
        elif abs(x - cx + 0.5) > half:
            c = 'm' if x < cx else 'd'          # obliques
        elif rel == 2:
            c = 'm' if x < cx else 'd'          # transverse groove
        elif rel == 0 and x in (cx - half, cx + 1):
            c = 'H'
        else:
            c = 's' if x < cx + half - 2 else 'm'
        g[y][x] = c
    return g


def line(g, lab, pts, c, names=('torso',)):
    for (x, y) in pts:
        if 0 <= x < 64 and 0 <= y < 64 and lab[y][x] in names and g[y][x] not in ('#', '.'):
            g[y][x] = c
    return g
