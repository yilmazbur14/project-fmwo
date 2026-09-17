"""Eric sword-leap draft: char-grid helpers. Palette sampled from EricTopDownRevised.png."""
import pickle, os
from pngio import *

HERE = os.path.dirname(os.path.abspath(__file__))
SHEET = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Eric/EricTopDownRevised.png'
FS = 128

PAL = {
    'k': (0, 0, 0), 'w': (255, 255, 255), 'L': (197, 205, 209), 'M': (155, 173, 183), 'l': (176, 188, 195),
    's': (132, 126, 135), 'g': (147, 143, 149), 'd': (86, 87, 87), 'D': (105, 106, 106), 'G': (125, 125, 125),
    'e': (81, 81, 81), 'b': (102, 57, 49), 'B': (117, 76, 69), 'o': (223, 113, 38), 't': (238, 195, 154),
    'T': (217, 160, 102), 'p': (236, 208, 181),
}
INV = {v: k for k, v in PAL.items()}


def ref_frames():
    p = os.path.join(HERE, 'eric_frames.pkl')
    return pickle.load(open(p, 'rb'))


def to_chars(fr):
    """RGBA frame -> char grid. Semi-transparent pixels become '~' (effects in the original)."""
    g = []
    for row in fr:
        r = []
        for p in row:
            if p[3] == 0:
                r.append('.')
            elif p[3] < 255:
                r.append('~')
            else:
                r.append(INV.get(p[:3], '?'))
        g.append(r)
    return g


def blank(w=FS, h=FS):
    return [['.'] * w for _ in range(h)]


def load_txt(path):
    """File format: first line '@ x0 y0', then rows of chars. '.' = transparent, '_' = erase."""
    lines = open(path).read().split('\n')
    hdr = lines[0].split()
    assert hdr[0] == '@', path
    x0, y0 = int(hdr[1]), int(hdr[2])
    rows = [l.rstrip('\r') for l in lines[1:]]
    while rows and rows[-1] == '':
        rows.pop()
    # optional ruler rows start with '#'
    rows = [r for r in rows if not r.startswith('#')]
    # strip optional "NNN|" prefix and trailing '|'
    out = []
    for r in rows:
        if len(r) > 4 and r[3] == '|':
            r = r[4:]
            if r.endswith('|'):
                r = r[:-1]
        out.append(r)
    widths = {len(r) for r in out}
    assert len(widths) == 1, '%s: ragged rows %s' % (path, sorted(widths))
    bad = {c for r in out for c in r if c not in PAL and c not in '._'}
    assert not bad, '%s: unknown chars %s' % (path, bad)
    return x0, y0, out


def save_txt(path, g, x0, y0, x1, y1):
    with open(path, 'w') as f:
        f.write('@ %d %d\n' % (x0, y0))
        f.write('#   ' + ''.join(str((x // 100) % 10) for x in range(x0, x1)) + '\n')
        f.write('#   ' + ''.join(str((x // 10) % 10) for x in range(x0, x1)) + '\n')
        f.write('#   ' + ''.join(str(x % 10) for x in range(x0, x1)) + '\n')
        for y in range(y0, y1):
            f.write('%3d|' % y + ''.join(g[y][x0:x1]) + '|\n')


def stamp(g, rows, x0, y0, dx=0, dy=0):
    for j, r in enumerate(rows):
        for i, c in enumerate(r):
            if c == '.':
                continue
            x, y = x0 + i + dx, y0 + j + dy
            if 0 <= x < len(g[0]) and 0 <= y < len(g):
                g[y][x] = '.' if c == '_' else c


def stamp_file(g, path, dx=0, dy=0):
    x0, y0, rows = load_txt(path)
    stamp(g, rows, x0, y0, dx, dy)


def copy_region(dst, src, x0, y0, x1, y1, dx=0, dy=0, keep=None):
    for y in range(y0, y1):
        for x in range(x0, x1):
            c = src[y][x]
            if c in '.~':
                continue
            if keep is not None and not keep(x, y, c):
                continue
            X, Y = x + dx, y + dy
            if 0 <= X < len(dst[0]) and 0 <= Y < len(dst):
                dst[Y][X] = c


def render(g):
    return [[(PAL[c] + (255,)) if c in PAL else (0, 0, 0, 0) for c in row] for row in g]


def crop_g(g, x0, y0, x1, y1):
    return [row[x0:x1] for row in g[y0:y1]]


def load_seg(path, g=None):
    """Segment format, one row per line:  'Y  X:chars  X:chars ...'  ('.' skip, '_' erase). '#' comments."""
    if g is None:
        g = blank()
    for ln in open(path):
        ln = ln.split('#', 1)[0].strip()
        if not ln:
            continue
        if ln.startswith('@inc'):
            # @inc file dx dy [ymin ymax xmin xmax]  -- include another seg, offset, optionally clipped (source coords)
            p = ln.split()
            sub = load_seg(os.path.join(os.path.dirname(path), p[1]))
            dx, dy = int(p[2]), int(p[3])
            ymin, ymax, xmin, xmax = (int(v) for v in p[4:8]) if len(p) >= 8 else (0, FS - 1, 0, FS - 1)
            for yy in range(ymin, ymax + 1):
                for xx in range(xmin, xmax + 1):
                    c = sub[yy][xx]
                    if c != '.' and 0 <= xx + dx < FS and 0 <= yy + dy < FS:
                        g[yy + dy][xx + dx] = c
            continue
        parts = ln.split()
        y = int(parts[0])
        for seg in parts[1:]:
            xs, s = seg.split(':', 1)
            bad = {c for c in s if c not in PAL and c not in '._'}
            assert not bad, '%s row %d: bad chars %s' % (path, y, bad)
            stamp(g, [s], int(xs), y)
    return g


def grid_to_seg(g, y0=0, y1=FS):
    out = []
    for y in range(y0, y1):
        row = g[y]
        segs = []
        x = 0
        while x < len(row):
            if row[x] == '.':
                x += 1
                continue
            s = x
            while x < len(row) and row[x] != '.':
                x += 1
            segs.append('%d:%s' % (s, ''.join(row[s:x])))
        if segs:
            out.append('%3d  ' % y + '  '.join(segs))
    return '\n'.join(out) + '\n'
