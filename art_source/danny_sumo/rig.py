"""Shared sprite engine for Danny's sumo transformation.

Generalised from art_source/danny/danny.py so both the 64x64 small form and
the 160x144 sumo form can use it.

Pipeline: polygon / capsule silhouettes -> z-composite -> directional bevel
shading (light from upper-left) -> auto 1px black outline -> letter grid ->
hand-authored stamps -> PNG.
Palette stays inside the cast's DawnBringer-32 range.
"""
import math

# ---------------------------------------------------------------- PALETTE
PAL = {
    'K': '#000000',
    # beanie (light-blue / blue knit, from portrait.png)
    'W': '#ffffff', 'C': '#cbdbfc', 'G': '#9badb7', 'g': '#847e87', 'q': '#696a6a',
    # skin
    'S': '#eec39a', 's': '#d9a066', 'd': '#8f563b', 'D': '#663931',
    # red shirt / rags
    'R': '#d95763', 'r': '#ac3232', 'M': '#45283c',
    # gold chain
    'Y': '#fbf236', 'y': '#df7126', 'o': '#8a6f30',
    # boots / dark
    'B': '#595652', 'b': '#323c39', 'k': '#222034',
    # mawashi (indigo-navy cloth belt)
    'N': '#639bff', 'n': '#5b6ee1', 'm': '#3f3f74', 'p': '#306082',
    # topknot hair
    'H': '#696a6a', 'h': '#45283c', 'j': '#222034',
    # misc
    'E': '#ffffff', 'v': '#8f974a', 'V': '#d9a066',
}

LEVEL_LETTERS = {
    'skin':   ['S', 'S', 's', 'd'],
    'belly':  ['S', 'S', 's', 'd'],
    'shirt':  ['R', 'r', 'D', 'M'],
    'shorts': ['R', 'r', 'D', 'M'],
    'bw':     ['W', 'W', 'C', 'G'],
    'bg':     ['G', 'G', 'g', 'q'],
    'boot':   ['B', 'b', 'k', 'k'],
    'mawashi': ['N', 'n', 'm', 'k'],
    'hair':   ['H', 'h', 'j', 'j'],
    'rope':   ['W', 'G', 'g', 'q'],
}

# per material: (t0, t1, t2, rim_amount, rim_radius)
BANDS = {
    'shirt':   (0.14, 0.80, 1.02, 0.45, 2.5),
    'shorts':  (0.04, 0.60, 0.97, 0.35, 2.5),
    'skin':    (-9.0, 0.62, 0.90, 0.42, 2.5),
    'belly':   (-9.0, 0.50, 0.82, 0.50, 3.0),
    'boot':    (0.08, 0.40, 0.62, 0.40, 2.5),
    'beanie':  (0.34, 0.62, 0.86, 0.30, 3.0),
    'mawashi': (0.10, 0.55, 0.88, 0.40, 2.5),
    'hair':    (0.20, 0.55, 0.85, 0.35, 2.5),
    'bw':      (0.34, 0.62, 0.86, 0.30, 3.0),
    'bg':      (0.34, 0.62, 0.86, 0.30, 3.0),
    'rope':    (0.18, 0.52, 0.84, 0.35, 2.5),
}

U = (0.62, 0.78)   # direction toward shadow (light from upper-left)
_UN = math.hypot(*U)
U = (U[0] / _UN, U[1] / _UN)


def hexc(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def inside(px, py, poly):
    c = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > py) != (yj > py):
            if px < xi + (py - yi) * (xj - xi) / (yj - yi):
                c = not c
        j = i
    return c


def seg_dist(px, py, x0, y0, x1, y1):
    vx, vy = x1 - x0, y1 - y0
    L2 = vx * vx + vy * vy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - x0) * vx + (py - y0) * vy) / L2))
    return math.hypot(px - (x0 + t * vx), py - (y0 + t * vy))


class Rig:
    """One sprite frame: collect regions, then build_letters()."""

    def __init__(self, W, H, AX, DX=0):
        self.W, self.H, self.AX, self.DX = W, H, AX, DX
        self.regions = []
        self.head_skin = None      # callable(x,y)->'beanie'|'hair'|None

    # ---------------------------------------------------------- geometry
    def mirror(self, left):
        return left + [(2 * self.AX - x, y) for (x, y) in reversed(left)]

    def mx(self, pts):
        return [(2 * self.AX - x, y) for (x, y) in reversed(pts)]

    def region(self, name, shape, z, group, mat, clip=None, sym=False,
               mirror_of=None):
        """sym       force the raster mask to be symmetric about the axis
        mirror_of    take this region's mask as the exact mirror of another,
                     so a left/right pair can never differ by a pixel"""
        self.regions.append(dict(name=name, shape=shape, z=z, group=group,
                                 mat=mat, clip=clip, sym=sym,
                                 mirror_of=mirror_of))

    # ------------------------------------------------------------ raster
    def raster(self, shape):
        W, H, DX = self.W, self.H, self.DX
        if isinstance(shape, list):
            shape = dict(polys=[shape])
        polys = shape.get('polys', [])
        caps = shape.get('caps', [])
        # cheap bbox so 160x144 frames stay fast
        xs, ys = [], []
        for p in polys:
            xs += [q[0] for q in p]
            ys += [q[1] for q in p]
        for c in caps:
            xs += [c[0] - c[4], c[2] + c[4]]
            ys += [c[1] - c[4], c[3] + c[4]]
        if not xs:
            return [[False] * W for _ in range(H)]
        bx0 = max(0, int(min(xs) + DX) - 2)
        bx1 = min(W - 1, int(max(xs) + DX) + 2)
        by0 = max(0, int(min(ys)) - 2)
        by1 = min(H - 1, int(max(ys)) + 2)
        m = [[False] * W for _ in range(H)]
        for y in range(by0, by1 + 1):
            for x in range(bx0, bx1 + 1):
                px, py = x + 0.5 - DX, y + 0.5
                hit = any(inside(px, py, p) for p in polys)
                if not hit:
                    hit = any(seg_dist(px, py, *c[:4]) <= c[4] for c in caps)
                m[y][x] = hit
        return m

    def composite(self):
        W, H, DX = self.W, self.H, self.DX
        idm = [[None] * W for _ in range(H)]
        ax = int(2 * self.AX)
        by_name = {r['name']: r for r in self.regions}
        for r in sorted(self.regions, key=lambda r: r['z']):
            if r.get('mirror_of'):
                src = by_name[r['mirror_of']]
                if 'mask' not in src:
                    src['mask'] = self.raster(src['shape'])
                    if src.get('sym'):
                        src['mask'] = self._symmetrise(src['mask'], ax)
                r['mask'] = [[src['mask'][y][ax - x] if 0 <= ax - x < W else False
                              for x in range(W)] for y in range(H)]
            elif 'mask' not in r:
                r['mask'] = self.raster(r['shape'])
                if r.get('sym'):
                    r['mask'] = self._symmetrise(r['mask'], ax)
            if r['clip']:
                for y in range(H):
                    for x in range(W):
                        if r['mask'][y][x] and not r['clip'](x - DX, y):
                            r['mask'][y][x] = False
            for y in range(H):
                row = r['mask'][y]
                for x in range(W):
                    if row[x]:
                        idm[y][x] = r
        return idm

    def _symmetrise(self, mask, ax):
        W, H = self.W, self.H
        return [[mask[y][x] or (mask[y][ax - x] if 0 <= ax - x < W else False)
                 for x in range(W)] for y in range(H)]

    def outline_pass(self, idm):
        W, H = self.W, self.H
        out = [[False] * W for _ in range(H)]
        for y in range(H):
            for x in range(W):
                a = idm[y][x]
                if a is None:
                    continue
                for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + ddx, y + ddy
                    b = idm[ny][nx] if (0 <= nx < W and 0 <= ny < H) else None
                    if b is None or (b['group'] != a['group'] and b['z'] < a['z']):
                        out[y][x] = True
                        break
        return out

    # ------------------------------------------------------------ shading
    def dist_map(self, mask):
        W, H = self.W, self.H
        pts = [(x, y) for y in range(H) for x in range(W) if mask[y][x]]
        if not pts:
            return {}
        # two-pass chamfer distance to the nearest empty pixel (fast enough,
        # and visually identical to the exact euclidean map at this scale)
        INF = 1e9
        d = [[0.0 if not mask[y][x] else INF for x in range(W)] for y in range(H)]
        for y in range(H):
            for x in range(W):
                if d[y][x] == 0.0:
                    continue
                best = INF
                for dx, dy, w in ((-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0),
                                  (-1, -1, 1.41421), (1, -1, 1.41421)):
                    nx, ny = x + dx, y + dy
                    v = d[ny][nx] + w if (0 <= nx < W and 0 <= ny < H) else w
                    best = min(best, v)
                d[y][x] = best
        for y in range(H - 1, -1, -1):
            for x in range(W - 1, -1, -1):
                if not mask[y][x]:
                    continue
                best = d[y][x]
                for dx, dy, w in ((1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0),
                                  (1, 1, 1.41421), (-1, 1, 1.41421)):
                    nx, ny = x + dx, y + dy
                    v = d[ny][nx] + w if (0 <= nx < W and 0 <= ny < H) else w
                    best = min(best, v)
                d[y][x] = best
        return {(x, y): d[y][x] for (x, y) in pts}

    def shade_region(self, r, idm):
        W, H = self.W, self.H
        d = self.dist_map(r['mask'])
        pts = list(d.keys())
        if not pts:
            r['lev'], r['t'] = {}, {}
            return
        proj = {p: p[0] * U[0] + p[1] * U[1] for p in pts}
        lo, hi = min(proj.values()), max(proj.values())
        span = max(hi - lo, 1e-6)
        t0, t1, t2, amt, Rr = BANDS[r['mat']]
        lev, tval = {}, {}
        for (x, y) in pts:
            p = (proj[(x, y)] - lo) / span
            gx = d.get((x + 1, y), 0.0) - d.get((x - 1, y), 0.0)
            gy = d.get((x, y + 1), 0.0) - d.get((x, y - 1), 0.0)
            gn = math.hypot(gx, gy)
            s = 0.0 if gn == 0 else -(gx * U[0] + gy * U[1]) / gn
            rim = max(0.0, 1.0 - (d[(x, y)] - 1.0) / Rr)
            t = p + amt * rim * s
            for step in (1, 2):
                cx = int(round(x - U[0] * step))
                cy = int(round(y - U[1] * step))
                if 0 <= cx < W and 0 <= cy < H:
                    o = idm[cy][cx]
                    if o is not None and o['z'] > r['z'] and o['group'] != r['group']:
                        t += 0.30 if step == 1 else 0.18
                        break
            tval[(x, y)] = t
            lev[(x, y)] = 0 if t < t0 else 1 if t < t1 else 2 if t < t2 else 3
        r['lev'], r['t'] = lev, tval

    # ------------------------------------------------------------- build
    def build_letters(self):
        W, H = self.W, self.H
        idm = self.composite()
        self.idm = idm
        for r in self.regions:
            self.shade_region(r, idm)
        ol = self.outline_pass(idm)
        g = [[' '] * W for _ in range(H)]
        for y in range(H):
            for x in range(W):
                r = idm[y][x]
                if r is None:
                    continue
                if ol[y][x]:
                    g[y][x] = 'K'
                    continue
                lv = r['lev'][(x, y)]
                mat = r['mat']
                if r['name'] == 'head' and self.head_skin:
                    kind = self.head_skin(x, y)
                    if kind in ('bw', 'bg'):
                        t = r['t'][(x, y)]
                        b0, b1, b2 = BANDS['beanie'][:3]
                        lv = 0 if t < b0 else 1 if t < b1 else 2 if t < b2 else 3
                        mat = kind
                    elif kind == 'hair':
                        t = r['t'][(x, y)]
                        b0, b1, b2 = BANDS['hair'][:3]
                        lv = 0 if t < b0 else 1 if t < b1 else 2 if t < b2 else 3
                        mat = 'hair'
                    elif kind == 'face':
                        lv = 1
                g[y][x] = LEVEL_LETTERS[mat][lv]
        return g


# ------------------------------------------------------------------ STAMPS
def stamp(g, x0, y0, block):
    """block: multi-line string. ' ' or '.' keep, '_' clear, other = letter."""
    H = len(g)
    W = len(g[0])
    for j, line in enumerate(block.strip('\n').split('\n')):
        for i, ch in enumerate(line):
            if ch in ' .':
                continue
            x, y = x0 + i, y0 + j
            if 0 <= x < W and 0 <= y < H:
                g[y][x] = ' ' if ch == '_' else ch


def S(x0, y0, rows, width=None):
    """Rows are right-padded with '.' (a no-op) so ragged authoring is fine;
    a row LONGER than the declared width is still an error."""
    width = max([len(r) for r in rows] + ([width] if width else [0]))
    for i, r in enumerate(rows):
        assert len(r) <= width, 'stamp @(%d,%d) row %d len %d > %d: %r' % (
            x0, y0, i, len(r), width, r)
    return (x0, y0, '\n'.join(r.ljust(width, '.') for r in rows))


def SM(axis, y0, halfrows):
    """Symmetric stamp: author the LEFT half only and get the mirror about
    pixel `axis` for free.  halfrows is [(x0, 'row'), ...] and each row may
    carry its OWN x0; rows are aligned to the smallest one."""
    x0 = min(h[0] for h in halfrows)
    body = [('.' * (hx - x0)) + r for (hx, r) in halfrows]
    width = max(len(r) for r in body)
    # Anything past the axis would be overwritten by the mirror anyway, so
    # clip the half there; the result is symmetric by construction.
    half = axis // 2
    if x0 + width - 1 > half:
        width = half - x0 + 1
        body = [r[:width] for r in body]
    body = [r.ljust(width, '.')[:width] for r in body]
    mir = [''.join(reversed(r)) for r in body]
    return [(x0, y0, '\n'.join(body)),
            (int(axis) - x0 - width + 1, y0, '\n'.join(mir))]


def stamp_mirror(g, x0, y0, block, axis):
    """Apply a stamp and its mirror about pixel axis (x' = axis - x)."""
    stamp(g, x0, y0, block)
    lines = block.strip('\n').split('\n')
    w = len(lines[0])
    mirrored = '\n'.join(''.join(reversed(ln)) for ln in lines)
    stamp(g, int(axis) - x0 - w + 1, y0, mirrored)


# --------------------------------------------------------- CURVE PAINTING
def _catmull(pts, n=None):
    """Sample a Catmull-Rom spline through pts; returns a dense point list."""
    if len(pts) < 2:
        return list(pts)
    p = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(len(p) - 3):
        p0, p1, p2, p3 = p[i], p[i + 1], p[i + 2], p[i + 3]
        seg = n or max(6, int(math.hypot(p2[0] - p1[0], p2[1] - p1[1]) * 2))
        for k in range(seg):
            t = k / float(seg)
            t2, t3 = t * t, t * t * t
            out.append((
                0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t
                       + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
                0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t
                       + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)))
    out.append(tuple(pts[-1]))
    return out


def curve(g, pts, ch, thick=1, over=None, mirror_axis=None, dy=0):
    """Paint a smooth curve of letter `ch` through `pts`.

    thick  vertical thickness in pixels (grows downward)
    over   only paint where the existing letter is in this set (keeps creases
           on the body instead of spilling into the outline or the background)
    """
    H, W = len(g), len(g[0])
    runs = [pts]
    if mirror_axis is not None:
        runs.append([(mirror_axis - x, y) for (x, y) in pts])
    for run in runs:
        for (fx, fy) in _catmull(run):
            x = int(round(fx))
            for k in range(thick):
                y = int(round(fy)) + k + dy
                if 0 <= x < W and 0 <= y < H:
                    if over is None or g[y][x] in over:
                        g[y][x] = ch


def region_mask(R, name):
    return next(r for r in R.regions if r['name'] == name)['mask']


def visible_mask(R, name):
    """Pixels where this region is the TOP one after compositing.  Painting
    passes must use this, never the raw raster mask, or they repaint pixels
    that something in front of them owns."""
    idm = R.idm
    H, W = len(idm), len(idm[0])
    return [[(idm[y][x] is not None and idm[y][x]['name'] == name)
             for x in range(W)] for y in range(H)]


def visible_bottom(R, names, x):
    """Lowest row in column x owned by any of `names`, or None."""
    idm = R.idm
    for y in range(len(idm) - 1, -1, -1):
        r = idm[y][x]
        if r is not None and r['name'] in names:
            return y
    return None


def mask_bounds_col(mask, x):
    """(top, bottom) row of a mask in column x, or None."""
    ys = [y for y in range(len(mask)) if mask[y][x]]
    return (ys[0], ys[-1]) if ys else None


def to_pix(g, pal=PAL):
    H, W = len(g), len(g[0])
    pix = [[(0, 0, 0, 0)] * W for _ in range(H)]
    for y in range(H):
        row = [(0, 0, 0, 0)] * W
        for x in range(W):
            c = g[y][x]
            if c != ' ':
                row[x] = hexc(pal[c])
        pix[y] = row
    return pix


def dump(g, path=None):
    H, W = len(g), len(g[0])
    lines = ['    ' + ''.join(str((x // 10) % 10) for x in range(W)),
             '    ' + ''.join(str(x % 10) for x in range(W))]
    for y in range(H):
        lines.append('%3d ' % y + ''.join(g[y]))
    s = '\n'.join(lines)
    if path:
        open(path, 'w').write(s)
    return s


def blank(W, H):
    return [[' '] * W for _ in range(H)]


def paste_grid(dst, src, x0, y0):
    H, W = len(dst), len(dst[0])
    for j, row in enumerate(src):
        for i, ch in enumerate(row):
            if ch == ' ':
                continue
            x, y = x0 + i, y0 + j
            if 0 <= x < W and 0 <= y < H:
                dst[y][x] = ch


def check_symmetry(g, axis, name='frame', outline_only=True):
    """Report mirrored pairs whose COVERAGE disagrees (axis: x' = axis - x).
    Shading is lit from the upper-left so colour is asymmetric on purpose;
    what must match is the silhouette, and (optionally) where the black
    outline falls."""
    H, W = len(g), len(g[0])
    bad = []
    for y in range(H):
        for x in range(W):
            mxp = int(axis) - x
            if not (0 <= mxp < W) or mxp <= x:
                continue
            a, b = g[y][x], g[y][mxp]
            if (a == ' ') != (b == ' '):
                bad.append((x, y, a, b))
            elif outline_only and (a == 'K') != (b == 'K'):
                bad.append((x, y, a, b))
    if bad:
        print('  %s: %d asymmetric pairs (first 12) %s' % (name, len(bad), bad[:12]))
    else:
        print('  %s: silhouette symmetric' % name)
    return bad
