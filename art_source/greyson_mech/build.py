"""Greyson Mech (phase 2) sprite builder. 96x96.
Parts are masks (polygons/ellipses), shaded with a top-left light over a
rounded height field, outlined in black in z-order, then ASCII stamps are
applied for hand-drawn detail."""
import math, sys
from pngio import write_png, scale

W = H = 96
AX = 95  # mirror: x' = 95 - x

def hexc(s):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)

BLACK = hexc('000000')
RAMPS = {
    # index 0 = specular/brightest ... last = deepest
    'metal':  ['eef3f6', 'c4d2da', '9badb7', '7b8893', '5a6570', '3c4450'],
    'dark':   ['b0aab4', '8d8791', '6e6873', '514c57', '37333d', '24212a'],
    'purple': ['c0a8ec', 'a07fd6', '8060b0', '604090', '46287a', '2e1656'],
    'white':  ['ffffff', 'f0f4f8', 'd6dee5', 'aab6c2', '808c9a', '5e6874'],
    'shoe':   ['6a6474', '4e4a58', '3a3542', '2a2630', '1c1a22', '121016'],
    'skin':   ['f8e0a0', 'f0d080', 'd0b060', 'a09050', '806c34', '605020'],
    'hair':   ['fffa9a', 'f4ec50', 'd4cc2e', 'a8a024', '726e17', '4e4a10'],
    'yellow': ['fffde0', 'fff566', 'fbf236', 'd4cc2e', 'a8a024', '726e17'],
    'red':    ['ffe8ec', 'ff9aa8', 'e8566a', 'ac3232', '6e1e22', '4a1216'],
}

# single-char palette for stamps
PAL = {
    'k': '000000',
    # metal
    'Q': 'eef3f6', 'q': 'c4d2da', 'm': '9badb7', 'n': '7b8893', 'o': '5a6570', 'p': '3c4450',
    # dark metal
    'D': 'b0aab4', 'd': '8d8791', 'e': '6e6873', 'f': '514c57', 'g': '37333d', 'h': '24212a',
    # purple
    'U': 'c0a8ec', 'u': 'a07fd6', 'v': '8060b0', 'w': '604090', 'x': '46287a', 'z': '2e1656',
    # white
    'W': 'ffffff', 'i': 'd6dee5', 'j': 'aab6c2',
    # skin
    'S': 'fadcb8', 's': 'eec39a', 't': 'e3b27f', 'c': 'd9a066', 'b': 'b8794a', 'a': '8a5236',
    # hair
    'H': 'fff7a0', 'l': 'ece45a', 'y': 'd4cc2e', 'Y': '908a17', 'Z': '5e5a10',
    # emblem yellow
    'G': 'fff566', 'F': 'fbf236',
    # red / glow
    'P': 'ffe8ec', 'r': 'ff9aa8', 'R': 'e8566a', 'X': 'ac3232', 'V': '6e1e22',
    # eyes
    'B': '639bff', 'A': '3a64c0',
    # triangle mark
    'T': 'd95763',
    # mouth interior
    'M': '4a1a1a',
}
PALC = {k: hexc(v) for k, v in PAL.items()}

# ---------------------------------------------------------------- geometry

def poly_mask(pts):
    m = [[False] * W for _ in range(H)]
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
                if xs[i] - 1e-6 <= x + 0.5 <= xs[i + 1] + 1e-6:
                    m[y][x] = True
    return m

def ell_mask(cx, cy, rx, ry):
    m = [[False] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0:
                m[y][x] = True
    return m

def mirror_pts(pts):
    return [(AX + 1 - x, y) for x, y in pts]  # pts are in continuous coords (edges)

def mirror_mask(m):
    return [row[::-1] for row in m]

def union(*ms):
    return [[any(m[y][x] for m in ms) for x in range(W)] for y in range(H)]

def sub(a, b):
    return [[a[y][x] and not b[y][x] for x in range(W)] for y in range(H)]

def sym_poly(half):
    """half: list of (x,y) points on the LEFT side going top->bottom, including
    points on the axis. Returns full symmetric polygon."""
    right = [(AX + 1 - x, y) for x, y in reversed(half)]
    return half + right

# ---------------------------------------------------------------- shading

LIGHT = (-0.55, -0.75, 0.9)
_l = math.sqrt(sum(c * c for c in LIGHT))
LIGHT = tuple(c / _l for c in LIGHT)

def shade_part(mask, R, thresholds, vbias=0.0):
    """Return grid of ramp indices (or None) for mask."""
    ys = [y for y in range(H) for x in range(W) if mask[y][x]]
    if not ys:
        return [[None] * W for _ in range(H)]
    y0, y1 = min(ys), max(ys)
    # distance to outside (brute force within R+1)
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
                    outside = not (0 <= yy < H and 0 <= xx < W) or not mask[yy][xx]
                    if outside:
                        d = math.sqrt(dx * dx + dy * dy) - 0.5
                        if d < best:
                            best = d
            t = min(best, R) / R
            hgt[y][x] = R * math.sqrt(max(0.0, 1 - (1 - t) ** 2))
    out = [[None] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            if not mask[y][x]:
                continue
            def g(xx, yy):
                if 0 <= xx < W and 0 <= yy < H and mask[yy][xx]:
                    return hgt[yy][xx]
                return 0.0
            gx = (g(x + 1, y) - g(x - 1, y)) / 2
            gy = (g(x, y + 1) - g(x, y - 1)) / 2
            nx, ny, nz = -gx, -gy, 1.0
            nl = math.sqrt(nx * nx + ny * ny + nz * nz)
            I = (nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]) / nl
            if y1 > y0:
                I += vbias * (0.5 - (y - y0) / (y1 - y0))
            idx = len(thresholds)
            for i, th in enumerate(thresholds):
                if I >= th:
                    idx = i
                    break
            out[y][x] = idx
    # cleanup: remove isolated tone pixels (2 passes)
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
                elif len(nb) == 4 and nb.count(out[y][x]) == 1:
                    best = max(set(nb), key=nb.count)
                    if nb.count(best) >= 3:
                        chg.append((x, y, best))
        for x, y, v in chg:
            out[y][x] = v
    return out

# default thresholds -> ramp index 0..5
TH_METAL = [0.985, 0.91, 0.73, 0.54, 0.35]
TH_SOFT = [9.0, 0.93, 0.72, 0.52, 0.34]   # no specular tone

# ---------------------------------------------------------------- canvas ops

canvas = [[None] * W for _ in range(H)]  # RGBA or None
owner = [[None] * W for _ in range(H)]   # part name

def render_part(name, mask, ramp, R=5, th=TH_METAL, vbias=0.15, outline=True,
                shadow_below=0):
    idx = shade_part(mask, R, th, vbias)
    rp = [hexc(c) for c in RAMPS[ramp]]
    # cast shadow onto what is already there, below/right of this part
    if shadow_below:
        for y in range(H):
            for x in range(W):
                if mask[y][x]:
                    continue
                cast = False
                for k in range(1, shadow_below + 1):
                    yy = y - k
                    if 0 <= yy < H and mask[yy][x]:
                        cast = True
                        break
                if cast and canvas[y][x] is not None and canvas[y][x] != BLACK:
                    canvas[y][x] = darken(canvas[y][x])
    for y in range(H):
        for x in range(W):
            if mask[y][x]:
                i = min(idx[y][x], len(rp) - 1)
                canvas[y][x] = rp[i]
                owner[y][x] = name
    if outline:
        for y in range(H):
            for x in range(W):
                if not mask[y][x]:
                    continue
                edge = False
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if not (0 <= xx < W and 0 <= yy < H) or not mask[yy][xx]:
                        edge = True
                        break
                if edge:
                    canvas[y][x] = BLACK

# map every ramp colour to next darker in its ramp
_DARKER = {}
for rn, rr in RAMPS.items():
    cs = [hexc(c) for c in rr]
    for i, c in enumerate(cs):
        _DARKER.setdefault(c, cs[min(i + 1, len(cs) - 1)])
_LIGHTER = {}
for rn, rr in RAMPS.items():
    cs = [hexc(c) for c in rr]
    for i, c in enumerate(cs):
        _LIGHTER.setdefault(c, cs[max(i - 1, 0)])

def darken(c):
    return _DARKER.get(c, c)

def stamp(grid, x0, y0, mirror=False):
    rows = [r for r in grid.strip('\n').split('\n')]
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch in '. ':
                continue
            x = x0 + dx
            if mirror:
                x = AX - x
            y = y0 + dy
            if not (0 <= x < W and 0 <= y < H):
                continue
            if ch == '_':
                canvas[y][x] = None
            elif ch == '-':
                if canvas[y][x] is not None:
                    canvas[y][x] = darken(canvas[y][x])
            elif ch == '+':
                if canvas[y][x] is not None:
                    canvas[y][x] = _LIGHTER.get(canvas[y][x], canvas[y][x])
            else:
                canvas[y][x] = PALC[ch]

def stamp_sym(grid, x0, y0):
    """stamp grid and its horizontal mirror (grid given for left side)."""
    stamp(grid, x0, y0)
    stamp(grid, x0, y0, mirror=True)

def save(path, s=1, bg=None):
    px = [[(canvas[y][x] if canvas[y][x] is not None else (0, 0, 0, 0)) for x in range(W)] for y in range(H)]
    if s == 1:
        write_png(path, W, H, px)
    else:
        write_png(path, W * s, H * s, scale(px, s, bg))
    return px

def rot_rect(cx, cy, w, h, ang_deg, ch=0):
    a = math.radians(ang_deg)
    ca, sa = math.cos(a), math.sin(a)
    hw, hh = w / 2, h / 2
    if ch:
        base = [(-hw + ch, -hh), (hw - ch, -hh), (hw, -hh + ch), (hw, hh - ch),
                (hw - ch, hh), (-hw + ch, hh), (-hw, hh - ch), (-hw, -hh + ch)]
    else:
        base = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
    return [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in base]

def rot_ell_mask(cx, cy, rx, ry, ang_deg):
    a = math.radians(ang_deg)
    ca, sa = math.cos(a), math.sin(a)
    m = [[False] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            u = dx * ca + dy * sa
            v = -dx * sa + dy * ca
            if (u / rx) ** 2 + (v / ry) ** 2 <= 1.0:
                m[y][x] = True
    return m


def recolor_region(region, ramp, R=3, th=None, line_mask=None):
    """Shade `region` (mask) with ramp; draw black on line_mask pixels.
    Does not touch pixels that are black already (keeps outlines)."""
    th = th or TH_SOFT
    idx = shade_part(region, R, th, 0.1)
    rp = [hexc(c) for c in RAMPS[ramp]]
    for y in range(H):
        for x in range(W):
            if region[y][x] and canvas[y][x] is not None and canvas[y][x] != BLACK:
                canvas[y][x] = rp[min(idx[y][x], len(rp) - 1)]
    if line_mask:
        for y in range(H):
            for x in range(W):
                if line_mask[y][x] and canvas[y][x] is not None:
                    canvas[y][x] = BLACK

def bottom_band(mask, depth):
    """pixels of mask within `depth` rows of the mask's lower edge; plus the
    line just above the band."""
    band = [[False] * W for _ in range(H)]
    line = [[False] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            if not mask[y][x]:
                continue
            below_out = any(not (y + k < H and mask[y + k][x]) for k in range(1, depth + 1))
            if below_out:
                band[y][x] = True
    for y in range(H):
        for x in range(W):
            if mask[y][x] and not band[y][x] and y + 1 < H and band[y + 1][x]:
                line[y][x] = True
    return band, line

def ring_mask(mask, cx, cy, r0, r1):
    m = [[False] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            if mask[y][x]:
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                if r0 <= d < r1:
                    m[y][x] = True
    return m
