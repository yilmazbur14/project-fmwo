"""Carter "Satsui no Hado" sprite toolkit. 96x96 canvas of RGBA-or-None.
Parts = masks shaded with a volume model, outlined in black in z-order;
hand ASCII stamps add the detail."""
import math
from pngio import write_png, scale, read_png

W = H = 96
AX = 95  # mirror: x' = 95 - x


def hexc(s):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


BLACK = (0, 0, 0, 255)

# ramps: index 0 = brightest.  Carter "Satsui no Hado" palette.
RAMPS = {
    # skin: Carter's approved redesign tones, pushed one step deeper
    'skin':  ['fbd6b0', 'f0b98e', 'db976c', 'b86c4e', '84412f', '552619'],
    # same skin, reddened - used for the aura-lit underside
    'skinr': ['f7c9a4', 'e8a87e', 'cf8560', 'a85a44', '75362c', '4a2018'],
    # beard: Carter's orange, exact hues
    'hair':  ['ffb45e', 'f09040', 'd66c28', 'b05b21', '703414', '4a2210'],
    # gi jacket / pants, dark navy
    'gi':    ['4a6ed8', '2d4392', '1d2b60', '14204a', '0c1430', '060a1e'],
    'rope':  ['fff2d6', 'f0d8a4', 'd0ae74', 'a07e4c', '6e5230', '42301a'],
    'belt':  ['c8a46a', 'a07c46', '74562e', '50381c', '32210f', '1c1208'],
    'bead':  ['c08a58', '84542e', '58341c', '3a2010', '221208', '140a04'],
    # aura: hot red core
    'ember': ['ffe2c0', 'ff9a6a', 'ff4a3c', 'c01830', '780c28', '440618'],
    # aura: violet outer / dark haze
    'void':  ['e2a2f4', 'b45ae0', '7c2eb0', '4e1878', '2e0c4c', '19062a'],
    # glowing eye
    'glow':  ['ffffff', 'ffd2d8', 'ff5a62', 'e0203c', '90102a', '54061a'],
    'steel': ['e6ecf2', 'bed6ff', '9badb7', '6b7c8c', '44505c', '242c36'],
    'dark':  ['5a5a6a', '383845', '22222b', '111117', '000000', '000000'],
}
_GI_PURPLE = ['8a52d8', '5c30a0', '3f1f74', '2a1450', '1a0c34', '0e0620']

PAL = {
    'k': '000000', 'K': '111117', 'N': '22222b',
    # skin
    's': 'fbd6b0', 't': 'f0b98e', 'u': 'db976c', 'v': 'b86c4e', 'w': '84412f', 'W': '552619',
    # beard orange
    '1': 'ffb45e', '2': 'f09040', '3': 'd66c28', '4': 'b05b21', '5': '703414', '6': '4a2210',
    # gi navy
    'a': '4a6ed8', 'b': '2d4392', 'c': '1d2b60', 'd': '14204a', 'e': '0c1430', 'f': '060a1e',
    # gi violet
    'A': '8a52d8', 'B': '5c30a0', 'C': '3f1f74', 'D': '2a1450', 'E': '1a0c34', 'F': '0e0620',
    # rope wraps
    'g': 'fff2d6', 'h': 'f0d8a4', 'i': 'd0ae74', 'j': 'a07e4c', 'l': '6e5230', 'm': '42301a',
    # belt rope
    'n': 'c8a46a', 'o': 'a07c46', 'p': '74562e', 'q': '50381c', 'r': '32210f',
    # beads
    'G': 'c08a58', 'H': '84542e', 'I': '58341c', 'J': '3a2010', 'L': '221208',
    # ember
    'x': 'ffe2c0', 'X': 'ff9a6a', 'y': 'ff4a3c', 'Y': 'c01830', 'z': '780c28', 'Z': '440618',
    # void
    'P': 'e2a2f4', 'Q': 'b45ae0', 'R': '7c2eb0', 'S': '4e1878', 'T': '2e0c4c', 'U': '19062a',
    # glow eye
    'M': 'ffffff', 'O': 'ffd2d8', 'V': 'ff5a62', '7': 'e0203c', '8': '90102a', '9': '54061a',
    # steel (earring)
    '#': 'e6ecf2', '%': 'bed6ff', '&': '9badb7', '*': '6b7c8c',
    # neutrals
    '0': '5a5a6a', '=': '383845',
}
PALC = {k: hexc(v) for k, v in PAL.items()}

_DARKER, _LIGHTER = {}, {}
for rn, rr in RAMPS.items():
    cs = [hexc(c) for c in rr]
    for i, c in enumerate(cs):
        _DARKER.setdefault(c, cs[min(i + 1, len(cs) - 1)])
        _LIGHTER.setdefault(c, cs[max(i - 1, 0)])

# ------------------------------------------------------------------ masks

def empty():
    return [[False] * W for _ in range(H)]


def poly(pts):
    m = empty()
    n = len(pts)
    for y in range(H):
        cy = y + 0.5
        xs = []
        for i in range(n):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % n]
            if (y1 <= cy < y2) or (y2 <= cy < y1):
                xs.append(x1 + (cy - y1) * (x2 - x1) / (y2 - y1))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            for x in range(W):
                if xs[i] <= x + 0.5 <= xs[i + 1]:
                    m[y][x] = True
    return m


def ell(cx, cy, rx, ry, ang=0.0):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    m = empty()
    for y in range(H):
        for x in range(W):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            u = dx * ca + dy * sa
            v = -dx * sa + dy * ca
            if (u / rx) ** 2 + (v / ry) ** 2 <= 1.0:
                m[y][x] = True
    return m


def rrect(cx, cy, w, h, ang=0.0, ch=0.0):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    hw, hh = w / 2, h / 2
    if ch:
        base = [(-hw + ch, -hh), (hw - ch, -hh), (hw, -hh + ch), (hw, hh - ch),
                (hw - ch, hh), (-hw + ch, hh), (-hw, hh - ch), (-hw, -hh + ch)]
    else:
        base = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
    return poly([(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in base])


def mirror(m):
    return [row[::-1] for row in m]


def sym(m):
    return union(m, mirror(m))


def sym_pts(half):
    """half: points on the LEFT half top->bottom incl. axis points."""
    return half + [(96 - x, y) for x, y in reversed(half)]


def union(*ms):
    return [[any(m[y][x] for m in ms) for x in range(W)] for y in range(H)]


def inter(a, b):
    return [[a[y][x] and b[y][x] for x in range(W)] for y in range(H)]


def sub(a, b):
    return [[a[y][x] and not b[y][x] for x in range(W)] for y in range(H)]


def halfplane(p0, p1, side=1):
    """pixels on one side of the infinite line p0->p1"""
    m = empty()
    (x0, y0), (x1, y1) = p0, p1
    for y in range(H):
        for x in range(W):
            c = (x1 - x0) * (y + 0.5 - y0) - (y1 - y0) * (x + 0.5 - x0)
            if c * side > 0:
                m[y][x] = True
    return m


def count(m):
    return sum(sum(r) for r in m)

# ------------------------------------------------------------------ shading

LIGHT = (-0.45, -0.6, 1.1)
_l = math.sqrt(sum(c * c for c in LIGHT))
LIGHT = tuple(c / _l for c in LIGHT)


def _dist_height(mask, R):
    Rr = int(R) + 2
    hgt = [[0.0] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            if not mask[y][x]:
                continue
            best = Rr
            for dy in range(-Rr, Rr + 1):
                yy = y + dy
                for dx in range(-Rr, Rr + 1):
                    xx = x + dx
                    if not (0 <= yy < H and 0 <= xx < W) or not mask[yy][xx]:
                        d = math.sqrt(dx * dx + dy * dy) - 0.5
                        if d < best:
                            best = d
            t = min(best, R) / R
            hgt[y][x] = R * math.sqrt(max(0.0, 1 - (1 - t) ** 2))
    return hgt


def normals(mask, model):
    """returns grid of (nx,ny,nz) or None"""
    kind = model[0]
    out = [[None] * W for _ in range(H)]
    if kind == 'sphere':
        _, cx, cy, rx, ry = model[:5]
        flat = model[5] if len(model) > 5 else 0.0
        for y in range(H):
            for x in range(W):
                if mask[y][x]:
                    u = (x + 0.5 - cx) / rx
                    v = (y + 0.5 - cy) / ry
                    d = u * u + v * v
                    if d > 0.97:
                        s = math.sqrt(0.97 / d)
                        u, v, d = u * s, v * s, 0.97
                    nz = math.sqrt(1 - d) + flat
                    out[y][x] = (u, v, nz)
    elif kind == 'cyl':
        _, (x0, y0), (x1, y1), r = model[:4]
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy)
        px, py = -dy / L, dx / L  # perpendicular unit
        for y in range(H):
            for x in range(W):
                if mask[y][x]:
                    s = ((x + 0.5 - x0) * px + (y + 0.5 - y0) * py) / r
                    s = max(-0.985, min(0.985, s))
                    nz = math.sqrt(1 - s * s)
                    out[y][x] = (s * px, s * py, nz)
    elif kind == 'dist':
        R = model[1]
        hgt = _dist_height(mask, R)

        def g(xx, yy):
            if 0 <= xx < W and 0 <= yy < H and mask[yy][xx]:
                return hgt[yy][xx]
            return 0.0
        for y in range(H):
            for x in range(W):
                if mask[y][x]:
                    gx = (g(x + 1, y) - g(x - 1, y)) / 2
                    gy = (g(x, y + 1) - g(x, y - 1)) / 2
                    out[y][x] = (-gx, -gy, 1.0)
    elif kind == 'flat':
        nx, ny = model[1], model[2]
        for y in range(H):
            for x in range(W):
                if mask[y][x]:
                    out[y][x] = (nx, ny, 1.0)
    return out


def intensity(n):
    nx, ny, nz = n
    l = math.sqrt(nx * nx + ny * ny + nz * nz)
    return (nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]) / l


TH_METAL = [0.97, 0.87, 0.63, 0.38, 0.12]
TH_SOFT = [9.0, 0.88, 0.64, 0.38, 0.12]
TH_CLOTH = [9.0, 0.93, 0.72, 0.46, 0.18]
TH_HARD = [9.0, 0.90, 0.60, 0.22, -9.0]
TH_HARD2 = [9.0, 0.95, 0.68, 0.30, -9.0]


def shade_idx(mask, model, th, cleanup=True):
    ns = normals(mask, model)
    out = [[None] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            if ns[y][x] is None:
                continue
            I = intensity(ns[y][x])
            idx = len(th)
            for i, t in enumerate(th):
                if I >= t:
                    idx = i
                    break
            out[y][x] = idx
    if cleanup:
        for _ in range(2):
            chg = []
            for y in range(H):
                for x in range(W):
                    if out[y][x] is None:
                        continue
                    nb = []
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        xx, yy = x + dx, y + dy
                        if 0 <= xx < W and 0 <= yy < H and out[yy][xx] is not None:
                            nb.append(out[yy][xx])
                    if len(nb) >= 3 and out[y][x] not in nb:
                        chg.append((x, y, max(set(nb), key=nb.count)))
            for x, y, v in chg:
                out[y][x] = v
    return out

# ------------------------------------------------------------------ canvas


class Canvas:
    def __init__(self):
        self.px = [[None] * W for _ in range(H)]

    def part(self, mask, ramp, model, th=TH_METAL, outline=True, bias=0, clip=None):
        if clip is not None:
            mask = inter(mask, clip)
        idx = shade_idx(mask, model, th)
        rp = [hexc(c) for c in RAMPS[ramp]]
        for y in range(H):
            for x in range(W):
                if mask[y][x]:
                    i = max(0, min(idx[y][x] + bias, len(rp) - 1))
                    self.px[y][x] = rp[i]
        if outline:
            self.outline(mask)

    def outline(self, mask, color=BLACK, only_outer=False):
        pts = []
        for y in range(H):
            for x in range(W):
                if not mask[y][x]:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if not (0 <= xx < W and 0 <= yy < H) or not mask[yy][xx]:
                        pts.append((x, y))
                        break
        for x, y in pts:
            self.px[y][x] = color

    def recolor(self, mask, ramp, model, th=TH_SOFT, bias=0, keep_black=True):
        idx = shade_idx(mask, model, th)
        rp = [hexc(c) for c in RAMPS[ramp]]
        for y in range(H):
            for x in range(W):
                if mask[y][x] and self.px[y][x] is not None:
                    if keep_black and self.px[y][x] == BLACK:
                        continue
                    self.px[y][x] = rp[max(0, min(idx[y][x] + bias, len(rp) - 1))]

    def paint(self, mask, color):
        for y in range(H):
            for x in range(W):
                if mask[y][x]:
                    self.px[y][x] = color

    def line_on(self, mask, color=BLACK):
        """paint color on mask only where canvas is not empty"""
        for y in range(H):
            for x in range(W):
                if mask[y][x] and self.px[y][x] is not None:
                    self.px[y][x] = color

    def stamp(self, grid, x0, y0, flip=False, over_only=False):
        rows = grid.strip('\n').split('\n')
        wdt = max(len(r) for r in rows)
        for dy, row in enumerate(rows):
            for dx, ch in enumerate(row):
                if ch in '. ':
                    continue
                x = x0 + (wdt - 1 - dx if flip else dx)
                y = y0 + dy
                if not (0 <= x < W and 0 <= y < H):
                    continue
                cur = self.px[y][x]
                if over_only and cur is None:
                    continue
                if ch == '_':
                    self.px[y][x] = None
                elif ch == '-':
                    if cur is not None:
                        self.px[y][x] = _DARKER.get(cur, cur)
                elif ch == '+':
                    if cur is not None:
                        self.px[y][x] = _LIGHTER.get(cur, cur)
                else:
                    self.px[y][x] = PALC[ch]

    def set(self, x, y, ch):
        if 0 <= x < W and 0 <= y < H:
            self.px[y][x] = PALC[ch] if ch not in ('_',) else None

    def copy(self):
        c = Canvas()
        c.px = [row[:] for row in self.px]
        return c

    def rgba(self):
        return [[(p if p is not None else (0, 0, 0, 0)) for p in row] for row in self.px]

    def save(self, path, s=1, bg=None):
        px = self.rgba()
        if s == 1:
            write_png(path, W, H, px)
        else:
            write_png(path, W * s, H * s, scale(px, s, bg))
        return px

    def mask_of(self):
        return [[p is not None for p in row] for row in self.px]


def shave_corners(cv, passes=1):
    """remove black outline pixels that form an outward L-corner on the silhouette
    (both orthogonal outer neighbours empty, and two black orthogonal neighbours)."""
    for _ in range(passes):
        kill = []
        for y in range(H):
            for x in range(W):
                if cv.px[y][x] != BLACK:
                    continue
                def em(xx, yy):
                    return not (0 <= xx < W and 0 <= yy < H) or cv.px[yy][xx] is None
                def bk(xx, yy):
                    return 0 <= xx < W and 0 <= yy < H and cv.px[yy][xx] == BLACK
                for (ax, ay), (bx, by) in (((-1, 0), (0, -1)), ((1, 0), (0, -1)), ((-1, 0), (0, 1)), ((1, 0), (0, 1))):
                    if em(x + ax, y + ay) and em(x + bx, y + by) and bk(x - ax, y - ay) and bk(x - bx, y - by):
                        # the inner diagonal must be non-empty and non-black (so line stays closed)
                        dx, dy = -ax - bx, -ay - by
                        ip = cv.px[y + dy][x + dx] if 0 <= x + dx < W and 0 <= y + dy < H else None
                        if ip is not None and ip != BLACK:
                            kill.append((x, y))
                            break
        for x, y in kill:
            cv.px[y][x] = None


def to_grid(cv):
    """dump canvas to chars (reverse PAL lookup); unknown colours -> '?'"""
    rev = {v: k for k, v in PALC.items()}
    lines = []
    for row in cv.px:
        lines.append(''.join('.' if p is None else rev.get(p, '?') for p in row))
    return '\n'.join(lines)


def from_grid(text):
    cv = Canvas()
    rows = text.strip('\n').split('\n')
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch != '.':
                cv.px[y][x] = PALC[ch]
    return cv


# ---------------------------------------------------------------- gi gradient

def _lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3)) + (255,)


GI_RAMP = [hexc(c) for c in RAMPS['gi']]
GIP_RAMP = [hexc(c) for c in _GI_PURPLE]
# 4 quantised blend steps, index 0 = pure navy
GI_STEPS = [[_lerp(GI_RAMP[i], GIP_RAMP[i], t) for i in range(6)]
            for t in (0.0, 0.34, 0.67, 1.0)]


def gi_fade(cv, mask, y0, y1):
    """remap already-shaded navy pixels toward violet as y goes y0 -> y1"""
    idx_of = {c: i for i, c in enumerate(GI_RAMP)}
    for y in range(H):
        t = (y - y0) / max(1e-6, (y1 - y0))
        t = max(0.0, min(1.0, t))
        step = min(3, int(t * 3.999))
        for x in range(W):
            if not mask[y][x]:
                continue
            c = cv.px[y][x]
            if c in idx_of:
                cv.px[y][x] = GI_STEPS[step][idx_of[c]]


def dither(mask, phase=0, every=2):
    m = empty()
    for y in range(H):
        for x in range(W):
            if mask[y][x] and (x + y + phase) % every == 0:
                m[y][x] = True
    return m


def grow(mask, n=1):
    m = [row[:] for row in mask]
    for _ in range(n):
        nm = [row[:] for row in m]
        for y in range(H):
            for x in range(W):
                if m[y][x]:
                    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                        xx, yy = x+dx, y+dy
                        if 0 <= xx < W and 0 <= yy < H:
                            nm[yy][xx] = True
        m = nm
    return m


def ring(mask, n=1):
    return sub(grow(mask, n), mask)


def erode(mask, n=1):
    inv = [[not mask[y][x] for x in range(W)] for y in range(H)]
    # treat outside the canvas as empty so the border erodes too
    g = grow(inv, n)
    return [[mask[y][x] and not g[y][x] for x in range(W)] for y in range(H)]


def band(y0, y1):
    m = empty()
    for y in range(H):
        if y0 <= y + 0.5 <= y1:
            for x in range(W):
                m[y][x] = True
    return m


_BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def bayer(mask, level, off=0):
    """ordered-dither a mask: level 0..16, higher keeps more pixels."""
    m = empty()
    for y in range(H):
        for x in range(W):
            if mask[y][x] and _BAYER[(y + off) % 4][(x + off) % 4] < level:
                m[y][x] = True
    return m
