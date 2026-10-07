"""Liam elements-phase rig: a numpy port of the approved liam_v2 toolkit (art_source/liam_v2/lib.py,
build.py, anim.py, frames.py), generalised to any canvas size, plus loaders for his approved layers.

Nothing here writes files. art_source/liam_v2/ is only ever READ (its layers/*.txt).

Canvases are numpy '<U1' arrays of palette keys, '.' = transparent. Coordinates are pixel indices;
geometry uses pixel centres (x + 0.5, y + 0.5) exactly like the liam_v2 rig, so arms built here shade
and outline the same way the approved sprite's arms do.
"""
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
ROOT = os.path.dirname(ART)
V2 = os.path.join(ART, 'liam_v2')


def hx(s):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


# ------------------------------------------------------------------ Liam's approved palette (liam_v2/lib.PAL)
PAL = {
    '#': hx('000000'),
    'a': hx('fadcb8'), 's': hx('eec39a'), 'd': hx('d9a066'), 'f': hx('b8794a'), 'g': hx('8a5236'),
    'k': hx('120a08'), 'h': hx('1b0f0d'), 'H': hx('36201a'), 'r': hx('56352a'), 'R': hx('7d4c36'),
    'i': hx('c3885a'), 'j': hx('a96b43'), 'J': hx('8f563b'), 'n': hx('663931'), 'N': hx('45283c'),
    'W': hx('ffffff'), 'w': hx('d6dee5'), 'v': hx('a3b1bc'),
    't': hx('c4d2da'), 'T': hx('9badb7'), 'y': hx('6e7d86'), 'Y': hx('4a5563'),
    'm': hx('eef4f7'), 'M': hx('b3c0c9'), 'e': hx('7b8893'), 'E': hx('4b555e'),
    'p': hx('6b6bb0'), 'q': hx('4c4c8c'), 'Q': hx('3a3a70'), 'z': hx('26264c'), 'Z': hx('181830'),
    'o': hx('6a4a3a'), 'O': hx('45302a'), 'x': hx('2a1b16'),
    'L': hx('ffffff'), 'l': hx('cbdbfc'), 'b': hx('8fb3e8'),
    'c': hx('fff6a8'), 'C': hx('fbf236'),
    'u': hx('5a1f22'), 'U': hx('9a3a3a'),
}
LIAM_KEYS = set(PAL)

# ------------------------------------------------------------------ additions for the elements phase
# Kept deliberately small: the staff's wood reuses nothing of the jacket (it must read against it), the
# gems add one hue per element, and the FX ramps live in their own sprites.
ADD = {
    # staff wood: pale ash, greener and cooler than his skin so a grip never merges into the shaft
    '1': hx('efe2b4'), '2': hx('cdb67e'), '3': hx('9a8150'), '4': hx('62502f'),
    # element gems (water / fire / earth); air uses his own whites (W w v)
    '5': hx('3d6fd6'),              # water deep (light = b 8fb3e8, glint = l)
    '6': hx('ff8a2a'), '7': hx('d8321f'),   # fire orange / fire red (core = C fbf236)
    '8': hx('7fd35a'), '9': hx('2f8a3c'),   # earth leaf / earth deep
    # slime (Bixby's stomach) for the mouth gag: the defeat sheet's slime greens
    'A': hx('c9f08a'), 'B': hx('8fcf5a'),
    # wind, water and dust for in-frame FX (no keyline)
    'P': hx('e6f7ff'), 'S': hx('a8dff5'), 'V': hx('6fb3dc'),     # air streaks
    'G': hx('d9c9a8'), 'K': hx('a8916c'),                        # dust puffs
}
PAL.update(ADD)
TRANSPARENT = (0, 0, 0, 0)


# ------------------------------------------------------------------ canvases
def blank(w, h):
    return np.full((h, w), '.', dtype='<U1')


def centres(w, h):
    ys, xs = np.mgrid[0:h, 0:w]
    return xs + 0.5, ys + 0.5


def composite(dst, src, ox=0, oy=0):
    """Paste src over dst at (ox, oy), skipping '.'; clipped to dst."""
    h, w = src.shape
    H, W = dst.shape
    x0, y0 = max(0, ox), max(0, oy)
    x1, y1 = min(W, ox + w), min(H, oy + h)
    if x1 <= x0 or y1 <= y0:
        return dst
    s = src[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
    d = dst[y0:y1, x0:x1]
    d[...] = np.where(s != '.', s, d)
    return dst


def compose(layers, w, h):
    out = blank(w, h)
    for L in layers:
        if L is None:
            continue
        if isinstance(L, tuple):
            composite(out, L[0], L[1], L[2])
        else:
            composite(out, L)
    return out


def shift(L, dx, dy):
    h, w = L.shape
    out = blank(w, h)
    composite(out, L, dx, dy)
    return out


def blk(L, x0, y0, rows, skip='. ', erase='_'):
    """Overlay an ASCII block. ' ' and '.' are transparent; '_' erases to transparent."""
    wd = len(rows[0])
    for i, r in enumerate(rows):
        assert len(r) == wd, 'row %d (y=%d) len %d != %d: %r' % (i, y0 + i, len(r), wd, r)
    H, W = L.shape
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            X, Y = x0 + i, y0 + j
            if 0 <= X < W and 0 <= Y < H and ch not in skip:
                L[Y, X] = '.' if ch == erase else ch
    return L


def put(L, x, y, s):
    H, W = L.shape
    for i, ch in enumerate(s):
        if 0 <= x + i < W and 0 <= y < H and ch != ' ':
            L[y, x + i] = '.' if ch == '_' else ch


def to_rgba(cv, pal=None):
    pal = pal or PAL
    h, w = cv.shape
    out = np.zeros((h, w, 4), dtype=np.uint8)
    for k in np.unique(cv):
        if k == '.':
            continue
        out[cv == k] = pal[k]
    return out


def to_text(cv):
    return '\n'.join(''.join(r) for r in cv)


def from_text(text):
    lines = [ln for ln in text.strip('\n').split('\n')]
    w = len(lines[0])
    for ln in lines:
        assert len(ln) == w, (len(ln), w)
    return np.array([list(ln) for ln in lines], dtype='<U1')


# ------------------------------------------------------------------ Liam's approved layers (read only)
LAYER_NAMES = ('tails', 'legs', 'torso', 'far', 'near', 'head')
BASE_ORDER = ('tails', 'legs', 'torso', 'far', 'near', 'head')


def load_v2_layers():
    out = {}
    for k in LAYER_NAMES:
        with open(os.path.join(V2, 'layers', k + '.txt')) as f:
            out[k] = from_text(f.read())
    return out


def pad(L64, w, h, ox, oy):
    out = blank(w, h)
    composite(out, L64, ox, oy)
    return out


# ------------------------------------------------------------------ masks
def poly_mask(pts, w, h):
    """Even-odd fill using pixel centres (liam_v2 lib.poly_mask)."""
    m = np.zeros((h, w), dtype=bool)
    n = len(pts)
    for y in range(h):
        yc = y + 0.5
        xs = []
        for i in range(n):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % n]
            x1 += 0.5; y1 += 0.5; x2 += 0.5; y2 += 0.5
            if (y1 <= yc < y2) or (y2 <= yc < y1):
                xs.append(x1 + (yc - y1) * (x2 - x1) / (y2 - y1))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            xa, xb = xs[k], xs[k + 1]
            for x in range(max(0, int(math.ceil(xa - 0.5))), min(w, int(math.floor(xb - 0.5)) + 1)):
                if xa <= x + 0.5 <= xb:
                    m[y, x] = True
    return m


def ellipse_mask(cx, cy, rx, ry, w, h):
    X, Y = centres(w, h)
    return ((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 <= 1.0


def seg_t_arr(X, Y, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 == 0:
        t = np.zeros_like(X)
    else:
        t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0, 1)
    return t, ax + t * dx, ay + t * dy


def tcapsule_mask(ax, ay, bx, by, r0, r1, w, h):
    X, Y = centres(w, h)
    t, qx, qy = seg_t_arr(X, Y, ax, ay, bx, by)
    return np.hypot(X - qx, Y - qy) <= r0 + (r1 - r0) * t


def polyline_mask(pts, r, w, h):
    m = np.zeros((h, w), dtype=bool)
    for i in range(len(pts) - 1):
        (ax, ay), (bx, by) = pts[i], pts[i + 1]
        m |= tcapsule_mask(ax, ay, bx, by, r, r, w, h)
    return m


def outline_pixels(mask, prune=True, return_pruned=False):
    """Inner 4-neighbour boundary with pixel-perfect L-corner pruning (liam_v2 lib.outline_pixels)."""
    h, w = mask.shape
    M = np.pad(mask, 1, constant_values=False)
    interior = M[1:-1, 1:-1] & M[:-2, 1:-1] & M[2:, 1:-1] & M[1:-1, :-2] & M[1:-1, 2:]
    ol = mask & ~interior
    pruned = []
    if prune:
        def o(x, y):
            return 0 <= x < w and 0 <= y < h and ol[y, x]

        def inside(x, y):
            return 0 <= x < w and 0 <= y < h and mask[y, x]
        changed = True
        while changed:
            changed = False
            ys, xs = np.nonzero(ol)
            for y, x in zip(ys.tolist(), xs.tolist()):
                if not ol[y, x]:
                    continue
                for (ax_, ay_), (bx_, by_) in (((-1, 0), (0, -1)), ((1, 0), (0, -1)), ((-1, 0), (0, 1)), ((1, 0), (0, 1))):
                    if o(x + ax_, y + ay_) and o(x + bx_, y + by_) and not o(x - ax_, y - ay_) and not o(x - bx_, y - by_):
                        outs = [(ddx, ddy) for ddx, ddy in ((-1, 0), (1, 0), (0, -1), (0, 1)) if not inside(x + ddx, y + ddy)]
                        if outs and all(d in ((-ax_, -ay_), (-bx_, -by_)) for d in outs):
                            ol[y, x] = False
                            pruned.append((x, y))
                            changed = True
                            break
    if return_pruned:
        return ol, pruned
    return ol


# ------------------------------------------------------------------ shading (liam_v2 LIGHT and ramps)
LIGHT = (-0.55, -0.75, 0.95)


def _norm(v):
    l = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / l for c in v)


def sphere_normal(X, Y, cx, cy, rx, ry):
    nx = (X - cx) / rx
    ny = (Y - cy) / ry
    d2 = nx * nx + ny * ny
    l = np.sqrt(np.maximum(d2, 1e-9))
    over = d2 >= 1.0
    nz = np.where(over, 0.0, np.sqrt(np.clip(1 - d2, 0, None)))
    nx = np.where(over, nx / l, nx)
    ny = np.where(over, ny / l, ny)
    return nx, ny, nz


def tcapsule_normal(X, Y, ax, ay, bx, by, r0, r1):
    t, qx, qy = seg_t_arr(X, Y, ax, ay, bx, by)
    r = r0 + (r1 - r0) * t
    nx, ny = (X - qx) / r, (Y - qy) / r
    d2 = nx * nx + ny * ny
    l = np.sqrt(np.maximum(d2, 1e-9))
    over = d2 >= 1
    nz = np.where(over, 0.0, np.sqrt(np.clip(1 - d2, 0, None)))
    return np.where(over, nx / l, nx), np.where(over, ny / l, ny), nz


def lambert(n, light=LIGHT, wrap=0.0):
    L = _norm(light)
    raw = n[0] * L[0] + n[1] * L[1] + n[2] * L[2]
    if wrap:
        return np.maximum(0.0, (raw + wrap) / (1 + wrap))
    return np.maximum(0.0, raw)


def quant(v, ramp, th):
    idx = np.zeros(v.shape, dtype=int)
    for t in th:
        idx += (v >= t)
    return np.array(list(ramp))[idx]


def paint(canvas, mask, chars):
    canvas[mask] = chars[mask] if isinstance(chars, np.ndarray) else chars


def paint_outline(canvas, mask, prune=True, ch='#', under=None):
    ol, pruned = outline_pixels(mask, prune, return_pruned=True)
    canvas[ol] = ch
    for (x, y) in pruned:
        canvas[y, x] = under[y, x] if under is not None else '.'


def paint_part(canvas, mask, chars, outline=True, prune=True):
    under = canvas.copy()
    paint(canvas, mask, chars)
    if outline:
        paint_outline(canvas, mask, prune, under=under)


JACKET = 'NnJji'
ARM_JTH = [0.25, 0.5, 0.78, 0.94]
SKIN = 'fdsa'
STH = [0.32, 0.62, 0.9]


# ------------------------------------------------------------------ arm builder (liam_v2 anim.arm_pose)
def arm_pose(w, h, delt, up, fore, cuff=(0.4, 2.3), wrap_dir=0.9, draw_up=True):
    """delt=(cx,cy,r); up=(ax,ay,bx,by,r0,r1) sleeve; fore=(ax,ay,bx,by,r0,r1) wrapped forearm (elbow->wrist).
    Sleeve (deltoid + upper arm) painted and outlined, then the forearm on top with its own outline."""
    L = blank(w, h)
    X, Y = centres(w, h)
    dcx, dcy, dr = delt
    m_delt = ellipse_mask(dcx, dcy, dr, dr, w, h)
    m_up = tcapsule_mask(*up, w, h)
    if draw_up:
        t, qx, qy = seg_t_arr(X, Y, up[0], up[1], up[2], up[3])
        du = np.hypot(X - qx, Y - qy) / up[4]
        dd = np.hypot(X - dcx, Y - dcy) / dr
        sn = sphere_normal(X, Y, dcx, dcy, dr, dr)
        cn = tcapsule_normal(X, Y, *up)
        use_s = dd < du
        n = tuple(np.where(use_s, a, b) for a, b in zip(sn, cn))
        v = lambert(n, wrap=0.3)
        paint_part(L, m_delt | m_up, quant(v, JACKET, ARM_JTH))
    ax, ay, bx, by, r0, r1 = fore
    flen = math.hypot(bx - ax, by - ay)
    ux, uy = (bx - ax) / flen, (by - ay) / flen
    m_fore = tcapsule_mask(*fore, w, h)
    c0, c1 = cuff
    px, py = X - ax, Y - ay
    al = px * ux + py * uy
    pe = -px * uy + py * ux
    v = lambert(tcapsule_normal(X, Y, *fore))
    ch = np.where(v > 0.62, 'W', np.where(v > 0.3, 'w', 'v'))
    stripe = (np.floor(al - c1 + pe * wrap_dir + 100).astype(int) % 3) == 2
    ch = np.where(stripe, np.where(v > 0.55, 'w', 'v'), ch)
    ch = np.where(al < c1, np.where(v > 0.8, 'i', np.where(v > 0.45, 'j', 'J')), ch)
    ch = np.where(al < c0, np.where(v > 0.5, 'J', 'n'), ch)
    paint_part(L, m_fore, ch)
    seam = m_fore & (L != '#') & (al >= c1 - 0.5) & (al < c1 + 0.5)
    L[seam] = '#'
    return L


# ------------------------------------------------------------------ ribbons (headband tails)
def ribbon(L, pts, r=1.6, ramp='yT'):
    h, w = L.shape
    m = polyline_mask(pts, r, w, h)
    X, Y = centres(w, h)
    best_d = np.full((h, w), 1e9)
    best_vx = np.zeros((h, w))
    best_vy = np.zeros((h, w))
    for i in range(len(pts) - 1):
        (ax, ay), (bx, by) = pts[i], pts[i + 1]
        t, qx, qy = seg_t_arr(X, Y, ax, ay, bx, by)
        d = np.hypot(X - qx, Y - qy)
        better = d < best_d
        best_d = np.where(better, d, best_d)
        best_vx = np.where(better, X - qx, best_vx)
        best_vy = np.where(better, Y - qy, best_vy)
    ch = np.where((best_vy < 0.2) & (best_vx < 0.8), ramp[1], ramp[0])
    paint_part(L, m, ch)
    return m


def tails_layer(w, h, lower, upper, ox=0, oy=0):
    """Headband tails: two ribbons given in 64-body coords, drawn into a (w,h) canvas offset by (ox,oy)."""
    L = blank(w, h)
    ribbon(L, [(x + ox, y + oy) for x, y in lower], r=1.7, ramp='Yy')
    ribbon(L, [(x + ox, y + oy) for x, y in upper], r=1.8, ramp='yT')
    return L


def line(L, x0, y0, x1, y1, ch='#'):
    H, W = L.shape
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        x = round(x0 + (x1 - x0) * i / n)
        y = round(y0 + (y1 - y0) * i / n)
        if 0 <= x < W and 0 <= y < H:
            L[y, x] = ch


def arc(L, pts, ch='#'):
    for i in range(len(pts) - 1):
        line(L, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], ch)


def star(L, cx, cy, arm, diag=0, core='W'):
    """liam_v2 4-point sparkle, outlined."""
    H, W = L.shape
    pts = {(cx, cy): core}
    for i in range(1, arm + 1):
        c = 'W' if i < arm else 'c'
        for dx, dy in ((i, 0), (-i, 0), (0, i), (0, -i)):
            pts[(cx + dx, cy + dy)] = c
    for i in range(1, diag + 1):
        for dx, dy in ((i, i), (-i, -i), (i, -i), (-i, i)):
            pts[(cx + dx, cy + dy)] = 'c'
    if arm >= 3:
        for dx, dy in ((1, 1), (-1, -1), (1, -1), (-1, 1)):
            pts[(cx + dx, cy + dy)] = 'W'
    ol = set()
    for (x, y) in pts:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in pts:
                ol.add(q)
    for (x, y) in ol:
        if 0 <= x < W and 0 <= y < H:
            L[y, x] = '#'
    for (x, y), c in pts.items():
        if 0 <= x < W and 0 <= y < H:
            L[y, x] = c
    return L


# ------------------------------------------------------------------ measurement
def numbers(cv, region=None):
    """(black ratio of opaque px, colour count, opaque px) - the liam.png audit numbers."""
    c = cv if region is None else cv[region]
    op = c != '.'
    n = int(op.sum())
    if n == 0:
        return 0.0, 0, 0
    keys = set(np.unique(c[op]).tolist())
    cols = set(PAL[k][:3] for k in keys)
    blk_ = int((c == '#').sum())
    return blk_ / n, len(cols), n
