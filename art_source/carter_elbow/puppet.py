"""Tiny 2.5D puppet renderer for pixel sprites.
Parts are ellipses / tapered capsules / polygons with a material. Rendered painter-order,
shaded with a top-left light using analytic normals, quantised to Carter's exact ramps,
then auto-outlined (outer 4-neighbour outline + internal outline between groups).
Output is a char grid (one char per pixel) that can be hand-patched and written to PNG."""
import math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import write_png, read_png

# Carter's exact palette (from carter.png) + effect colours added elsewhere
PAL = {
    '.': (0, 0, 0, 0),
    'K': (0, 0, 0, 255),
    'h': (0xf0, 0xc0, 0x88, 255),
    's': (0xd9, 0xa0, 0x66, 255),
    'm': (0xb8, 0x79, 0x4a, 255),
    'd': (0xa0, 0x6b, 0x3e, 255),
    'D': (0x8c, 0x5a, 0x34, 255),
    'L': (0x5a, 0x8f, 0xf0, 255),
    'B': (0x3a, 0x6f, 0xd8, 255),
    'b': (0x28, 0x50, 0xa8, 255),
    'k': (0x1a, 0x1a, 0x1a, 255),
    'O': (0xc2, 0x66, 0x2b, 255),
    'o': (0xa8, 0x5a, 0x24, 255),
    'r': (0x8f, 0x4a, 0x1e, 255),
    'n': (0x5a, 0x2e, 0x12, 255),
    'e': (0x1a, 0x10, 0x08, 255),
    'w': (0xff, 0xff, 0xff, 255),
    'G': (0xe8, 0xc6, 0x4a, 255),
    'g': (0xa8, 0x86, 0x2a, 255),
}
REV = {v: k for k, v in PAL.items()}

LIGHT = (-0.55, -0.75, 1.0)
_l = math.sqrt(sum(c * c for c in LIGHT))
LIGHT = tuple(c / _l for c in LIGHT)

RAMPS = {
    # (threshold, char) checked in order, first match wins
    'skin': [(0.93, 'h'), (0.18, 's'), (-0.38, 'm'), (-0.75, 'd'), (-9, 'D')],
    'trunks': [(0.90, 'L'), (-0.05, 'B'), (-9, 'b')],
    'boot': [(-9, 'k')],
    'beard': [(0.55, 'O'), (-0.25, 'o'), (-9, 'r')],
    'flat_s': [(-9, 's')],
}


class Part:
    def __init__(self, kind, geom, mat='skin', group=None, bias=0.0, sep='K', flat=None):
        self.kind, self.geom, self.mat = kind, geom, mat
        self.group = group
        self.bias = bias
        self.sep = sep      # char used for internal outline drawn on parts BEHIND this one (None = no line)
        self.flat = flat    # if set, force this char everywhere

    def sample(self, px, py):
        """returns normal (nx,ny,nz) or None"""
        g = self.geom
        if self.kind == 'ell':
            cx, cy, rx, ry, ang = g
            a = math.radians(ang)
            dx, dy = px - cx, py - cy
            u = (dx * math.cos(a) + dy * math.sin(a)) / rx
            v = (-dx * math.sin(a) + dy * math.cos(a)) / ry
            rr = u * u + v * v
            if rr > 1.0:
                return None
            nz = math.sqrt(1 - rr)
            nx = u * math.cos(a) - v * math.sin(a)
            ny = u * math.sin(a) + v * math.cos(a)
            return (nx, ny, nz)
        if self.kind == 'cap':
            ax, ay, bx, by, ra, rb = g
            vx, vy = bx - ax, by - ay
            L2 = vx * vx + vy * vy
            t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / L2))
            qx, qy = ax + t * vx, ay + t * vy
            r = ra + (rb - ra) * t
            dx, dy = px - qx, py - qy
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > r:
                return None
            nz = math.sqrt(max(0.0, 1 - (dist / r) ** 2))
            return (dx / r, dy / r, nz)
        if self.kind == 'poly':
            pts, rad = g
            if not _pip(px, py, pts):
                return None
            # distance to edge + direction for a rounded normal
            best, bdx, bdy = 1e9, 0, 0
            n = len(pts)
            for i in range(n):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % n]
                ex, ey = x2 - x1, y2 - y1
                l2 = ex * ex + ey * ey
                t = 0 if l2 == 0 else max(0, min(1, ((px - x1) * ex + (py - y1) * ey) / l2))
                qx, qy = x1 + t * ex, y1 + t * ey
                d = math.hypot(px - qx, py - qy)
                if d < best:
                    best, bdx, bdy = d, px - qx, py - qy
            k = min(best / rad, 1.0)
            # outward direction is -(bdx,bdy)
            if best > 1e-6:
                ox, oy = -bdx / best, -bdy / best
            else:
                ox, oy = 0, 0
            s = 1 - k
            nz = math.sqrt(max(0, 1 - s * s))
            return (ox * s, oy * s, nz)
        raise ValueError(self.kind)


def _pip(x, y, pts):
    inside = False
    n = len(pts)
    j = n - 1
    for i in range(n):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi):
            inside = not inside
        j = i
    return inside


def ell(cx, cy, rx, ry, ang=0, **kw):
    return Part('ell', (cx, cy, rx, ry, ang), **kw)


def cap(ax, ay, bx, by, ra, rb=None, **kw):
    return Part('cap', (ax, ay, bx, by, ra, ra if rb is None else rb), **kw)


def poly(pts, rad=3.0, **kw):
    return Part('poly', (pts, rad), **kw)


def render(parts, W=64, H=64, outline=True):
    lab = [[-1] * W for _ in range(H)]
    grid = [['.'] * W for _ in range(H)]
    for idx, p in enumerate(parts):
        for y in range(H):
            for x in range(W):
                n = p.sample(x + 0.5, y + 0.5)
                if n is None:
                    continue
                lab[y][x] = idx
                if p.flat:
                    grid[y][x] = p.flat
                    continue
                I = n[0] * LIGHT[0] + n[1] * LIGHT[1] + n[2] * LIGHT[2] + p.bias
                for th, ch in RAMPS[p.mat]:
                    if I >= th:
                        grid[y][x] = ch
                        break
    if outline:
        out = [row[:] for row in grid]
        for y in range(H):
            for x in range(W):
                a = lab[y][x]
                if a < 0:
                    # outer outline
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        xx, yy = x + dx, y + dy
                        if 0 <= xx < W and 0 <= yy < H and lab[yy][xx] >= 0:
                            out[y][x] = 'K'
                            break
                    continue
                pa = parts[a]
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < W and 0 <= yy < H:
                        b = lab[yy][xx]
                        if b > a and parts[b].group != pa.group and parts[b].sep:
                            out[y][x] = parts[b].sep
                            break
        grid = out
    return grid, lab


def stamp(grid, ox, oy, lines, skip=' '):
    for j, line in enumerate(lines):
        for i, ch in enumerate(line):
            if ch == skip:
                continue
            x, y = ox + i, oy + j
            if 0 <= y < len(grid) and 0 <= x < len(grid[0]):
                grid[y][x] = ch


def setpx(grid, pts, ch):
    for x, y in pts:
        grid[y][x] = ch


def grid_to_text(grid):
    W = len(grid[0])
    head = '    ' + ''.join(str((x // 10) % 10) for x in range(W)) + '\n' + '    ' + ''.join(str(x % 10) for x in range(W)) + '\n'
    return head + '\n'.join('%3d %s' % (y, ''.join(r)) for y, r in enumerate(grid)) + '\n'


def text_to_grid(txt):
    rows = []
    for line in txt.splitlines():
        if len(line) > 4 and line[:3].strip().isdigit():
            rows.append(list(line[4:]))
    return rows


def grid_pixels(grid, pal=None):
    pal = pal or PAL
    return [[pal[ch] for ch in row] for row in grid]


def load_grid_from_png(path, fw, frame, pal=None):
    pal = pal or PAL
    rev = {v: k for k, v in pal.items()}
    w, h, pix = read_png(path)
    g = []
    for y in range(h):
        row = []
        for x in range(fw):
            p = pix[y][frame * fw + x]
            if p[3] == 0:
                p = (0, 0, 0, 0)
            row.append(rev.get(p, '?'))
        g.append(row)
    return g


def write_strip(path, grids, pal=None):
    pal = pal or PAL
    fh = len(grids[0])
    fw = len(grids[0][0])
    W = fw * len(grids)
    img = [[(0, 0, 0, 0)] * W for _ in range(fh)]
    for f, g in enumerate(grids):
        assert len(g) == fh and all(len(r) == fw for r in g), 'frame %d bad size' % f
        for y in range(fh):
            for x in range(fw):
                img[y][f * fw + x] = pal[g[y][x]]
    write_png(path, W, fh, img)
