"""Char-grid canvas helpers for Bixby. One char per pixel, '.' = transparent."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import write_png, upscale

W = H = 64


def blank(w=W, h=H):
    return [['.'] * w for _ in range(h)]


def mask_poly(points, w=W, h=H):
    """Even-odd scanline fill sampled at pixel centres. Returns set of (x,y)."""
    m = set()
    n = len(points)
    for y in range(h):
        cy = y + 0.5
        xs = []
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            if (y0 <= cy < y1) or (y1 <= cy < y0):
                xs.append(x0 + (cy - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            a, b = xs[i], xs[i + 1]
            for x in range(w):
                cx = x + 0.5
                if a <= cx < b:
                    m.add((x, y))
    return m


def mask_ellipse(cx, cy, rx, ry, w=W, h=H):
    m = set()
    for y in range(h):
        for x in range(w):
            dx = (x + 0.5 - cx) / rx
            dy = (y + 0.5 - cy) / ry
            if dx * dx + dy * dy <= 1.0:
                m.add((x, y))
    return m


def mask_tube(path, widths, w=W, h=H, samples=200):
    """Thick polyline: union of discs along a path with interpolated radius."""
    import math
    m = set()
    segs = []
    total = 0
    for i in range(len(path) - 1):
        (x0, y0), (x1, y1) = path[i], path[i + 1]
        L = math.hypot(x1 - x0, y1 - y0)
        segs.append((x0, y0, x1, y1, L))
        total += L
    acc = 0
    for (x0, y0, x1, y1, L) in segs:
        steps = max(2, int(samples * L / total))
        for s in range(steps + 1):
            t = s / steps
            px, py = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            u = (acc + L * t) / total
            r = widths[0] + (widths[1] - widths[0]) * u
            for yy in range(int(py - r - 1), int(py + r + 2)):
                for xx in range(int(px - r - 1), int(px + r + 2)):
                    if 0 <= xx < w and 0 <= yy < h:
                        if (xx + 0.5 - px) ** 2 + (yy + 0.5 - py) ** 2 <= r * r:
                            m.add((xx, yy))
        acc += L
    return m


def paint_part(grid, mask, fill, outline='K'):
    """Paint a part with its own 1px outline (boundary pixels of the mask)."""
    h = len(grid)
    w = len(grid[0])
    for (x, y) in mask:
        edge = False
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in mask:
                edge = True
                break
        if 0 <= x < w and 0 <= y < h:
            grid[y][x] = outline if edge else fill


def stamp(grid, rows, ox, oy, transparent='.'):
    for j, row in enumerate(rows):
        for i, c in enumerate(row):
            if c == transparent:
                continue
            x, y = ox + i, oy + j
            if 0 <= x < len(grid[0]) and 0 <= y < len(grid):
                grid[y][x] = c


def mirror_rows(rows, swap=None):
    swap = swap or {}
    return [''.join(swap.get(c, c) for c in reversed(r)) for r in rows]


def load_rows(path):
    """Read a stamp file. Lines look like 'NN |....|' or just raw rows.
    Lines starting with '#' are comments."""
    rows = []
    with open(path) as f:
        for line in f:
            line = line.rstrip('\n')
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            if '|' in line:
                a = line.index('|')
                b = line.rindex('|')
                rows.append(line[a + 1:b])
            else:
                rows.append(line)
    widths = {len(r) for r in rows}
    assert len(widths) == 1, 'ragged stamp %s: %s' % (path, sorted(widths))
    return rows


def save_rows(path, rows):
    with open(path, 'w') as f:
        for y, r in enumerate(rows):
            f.write('%02d |%s|\n' % (y, ''.join(r)))


def to_pix(grid, pal):
    out = []
    for row in grid:
        line = []
        for c in row:
            if c == '.':
                line.append((0, 0, 0, 0))
            else:
                hx = pal[c].lstrip('#')
                line.append((int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16), 255))
        out.append(line)
    return out


def save_png(path, grid, pal, scale=1, bg=None):
    pix = to_pix(grid, pal)
    h, w = len(pix), len(pix[0])
    if scale == 1 and bg is None:
        write_png(path, w, h, pix)
    else:
        W2, H2, big = upscale(w, h, pix, scale, bg=bg)
        write_png(path, W2, H2, big)


def hstack(images, gap=8, bg=(60, 60, 70, 255)):
    """images: list of (w,h,pix). Returns (w,h,pix) side by side, bottom-aligned."""
    H2 = max(im[1] for im in images)
    W2 = sum(im[0] for im in images) + gap * (len(images) + 1)
    out = [[bg] * W2 for _ in range(H2 + 2 * gap)]
    x = gap
    for (w, h, pix) in images:
        top = gap + (H2 - h)
        for y in range(h):
            for i in range(w):
                p = pix[y][i]
                if p[3] > 0:
                    out[top + y][x + i] = p
        x += w + gap
    return W2, H2 + 2 * gap, out
