"""Burak cutscene toolkit: palette, char-canvas ops, masks, outline, form shading, previews."""
import math
from pngio import read_png, write_png, scale, checker_bg

W = H = 64


def hx(s):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


PAL = {
    '#': hx('000000'),
    # skin (cast ramp: carter/josh)
    'a': hx('fbd6b0'), 's': hx('f0b98e'), 'd': hx('db976c'), 'f': hx('b86c4e'), 'g': hx('84412f'),
    # hair (near-black, cool-warm)
    'h': hx('17111a'), 'H': hx('2e2430'), 'r': hx('4a3c4a'),
    # hoodie charcoal (cool)
    'A': hx('8e93a8'), 'B': hx('6c7187'), 'C': hx('515569'), 'D': hx('3b3e50'), 'E': hx('292b39'), 'F': hx('181920'),
    # pants (dark indigo denim)
    'p': hx('6a76a6'), 'q': hx('4c5782'), 'Q': hx('373e60'), 'z': hx('252a42'),
    # shoes
    'o': hx('6a6470'), 'O': hx('3e3944'), 'x': hx('24212a'), 'e': hx('9a98a6'),
    # boxing gloves (player blue)
    'b': hx('8cc0ff'), 'c': hx('4a8ae6'), 'v': hx('2a62c4'), 'V': hx('1b3f8e'), 'Z': hx('112660'),
    # laces / drawstrings
    'L': hx('eef2f7'), 'l': hx('aab2c0'),
    # eyes / mouth
    'W': hx('ffffff'), 'w': hx('c9d2df'), 'k': hx('120c10'), 'i': hx('5a3524'), 'I': hx('8a5a3a'),
    'u': hx('6a2a2a'), 'U': hx('a04848'),
    # fx
    'y': hx('fff6b0'), 'Y': hx('ffd84a'), 'S': hx('d6ecff'), 'T': hx('7fb4ec'),
}
TRANSPARENT = (0, 0, 0, 0)

# ---------------------------------------------------------------- canvas
def layer():
    return [['.' for _ in range(W)] for _ in range(H)]


def copy(L):
    return [r[:] for r in L]


def composite(dst, src):
    for y in range(H):
        for x in range(W):
            if src[y][x] != '.':
                dst[y][x] = src[y][x]


def compose(layers):
    cv = layer()
    for l in layers:
        if l is not None:
            composite(cv, l)
    return cv


def shift(canvas, dx, dy):
    out = layer()
    for y in range(H):
        for x in range(W):
            X, Y = x + dx, y + dy
            if 0 <= X < W and 0 <= Y < H and canvas[y][x] != '.':
                out[Y][X] = canvas[y][x]
    return out


def blk(L, x0, y0, rows, skip='.', erase='_'):
    """Stamp an ASCII block. '.' = leave, '_' = erase to transparent."""
    wd = max(len(r) for r in rows)
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            X, Y = x0 + i, y0 + j
            if not (0 <= X < W and 0 <= Y < H) or ch in skip or ch == ' ':
                continue
            L[Y][X] = '.' if ch == erase else ch


def blk_rows(text):
    lines = text.split('\n')
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def to_text(c):
    return '\n'.join(''.join(r) for r in c)


def from_text(t):
    lines = [ln for ln in t.strip('\n').split('\n')]
    assert len(lines) == H, len(lines)
    return [list(ln.ljust(W, '.')) for ln in lines]


def to_rgba(c):
    return [[(PAL[ch] if ch != '.' else TRANSPARENT) for ch in row] for row in c]


def mask_of(c):
    return [[c[y][x] != '.' for x in range(W)] for y in range(H)]

# ---------------------------------------------------------------- masks
def empty_mask():
    return [[False] * W for _ in range(H)]


def poly_mask(pts):
    m = empty_mask()
    n = len(pts)
    for y in range(H):
        yc = y + 0.5
        xs = []
        for i in range(n):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % n]
            if (y1 <= yc < y2) or (y2 <= yc < y1):
                xs.append(x1 + (yc - y1) * (x2 - x1) / (y2 - y1))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            xa, xb = xs[k], xs[k + 1]
            for x in range(W):
                if xa <= x + 0.5 <= xb:
                    m[y][x] = True
    return m


def ellipse_mask(cx, cy, rx, ry):
    m = empty_mask()
    for y in range(H):
        for x in range(W):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0:
                m[y][x] = True
    return m


def seg_t(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
    return t, ax + t * dx, ay + t * dy


def tcapsule_mask(ax, ay, bx, by, r0, r1):
    m = empty_mask()
    for y in range(max(0, int(min(ay, by) - 8)), min(H, int(max(ay, by) + 9))):
        for x in range(max(0, int(min(ax, bx) - 8)), min(W, int(max(ax, bx) + 9))):
            px, py = x + 0.5, y + 0.5
            t, qx, qy = seg_t(px, py, ax, ay, bx, by)
            if math.hypot(px - qx, py - qy) <= r0 + (r1 - r0) * t:
                m[y][x] = True
    return m


def tcapsule_normal(x, y, ax, ay, bx, by, r0, r1):
    px, py = x + 0.5, y + 0.5
    t, qx, qy = seg_t(px, py, ax, ay, bx, by)
    r = r0 + (r1 - r0) * t
    nx, ny = (px - qx) / r, (py - qy) / r
    d2 = nx * nx + ny * ny
    if d2 >= 1:
        l = math.sqrt(d2)
        return (nx / l, ny / l, 0.0)
    return (nx, ny, math.sqrt(1 - d2))


def sphere_normal(x, y, cx, cy, rx, ry):
    nx = (x + 0.5 - cx) / rx
    ny = (y + 0.5 - cy) / ry
    d2 = nx * nx + ny * ny
    if d2 >= 1.0:
        l = math.sqrt(d2)
        return (nx / l, ny / l, 0.0)
    return (nx, ny, math.sqrt(1 - d2))


def m_or(*ms):
    return [[any(m[y][x] for m in ms) for x in range(W)] for y in range(H)]


def m_and(a, b):
    return [[a[y][x] and b[y][x] for x in range(W)] for y in range(H)]


def m_sub(a, b):
    return [[a[y][x] and not b[y][x] for x in range(W)] for y in range(H)]


def m_count(m):
    return sum(sum(r) for r in m)

# ---------------------------------------------------------------- outline
def outline_pixels(mask, prune=True):
    def inside(x, y):
        return 0 <= x < W and 0 <= y < H and mask[y][x]
    ol = [[False] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            if mask[y][x] and not (inside(x - 1, y) and inside(x + 1, y) and inside(x, y - 1) and inside(x, y + 1)):
                ol[y][x] = True
    pruned = []
    if prune:
        def o(x, y):
            return 0 <= x < W and 0 <= y < H and ol[y][x]
        changed = True
        while changed:
            changed = False
            for y in range(H):
                for x in range(W):
                    if not ol[y][x]:
                        continue
                    for (ax_, ay_), (bx_, by_) in (((-1, 0), (0, -1)), ((1, 0), (0, -1)), ((-1, 0), (0, 1)), ((1, 0), (0, 1))):
                        if o(x + ax_, y + ay_) and o(x + bx_, y + by_) and not o(x - ax_, y - ay_) and not o(x - bx_, y - by_):
                            outs = [(ddx, ddy) for ddx, ddy in ((-1, 0), (1, 0), (0, -1), (0, 1)) if not inside(x + ddx, y + ddy)]
                            if outs and all(d in ((-ax_, -ay_), (-bx_, -by_)) for d in outs):
                                ol[y][x] = False
                                pruned.append((x, y))
                                changed = True
                                break
    return ol, pruned


def paint_part(canvas, mask, fn, outline=True, prune=True):
    """Fill mask via fn(x,y)->char, outline it. Pruned corners restore what was under."""
    under = copy(canvas)
    for y in range(H):
        for x in range(W):
            if mask[y][x]:
                c = fn(x, y)
                if c is not None:
                    canvas[y][x] = c
    if outline:
        ol, pruned = outline_pixels(mask, prune)
        for y in range(H):
            for x in range(W):
                if ol[y][x]:
                    canvas[y][x] = '#'
        for (x, y) in pruned:
            canvas[y][x] = under[y][x]


def outer_outline(canvas):
    """Ensure a 1px black ring OUTSIDE any non-black pixel that touches transparency (4-neighbour)."""
    out = copy(canvas)
    for y in range(H):
        for x in range(W):
            if canvas[y][x] != '.':
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                X, Y = x + dx, y + dy
                if 0 <= X < W and 0 <= Y < H and canvas[Y][X] not in '.#':
                    out[y][x] = '#'
                    break
    return out

# ---------------------------------------------------------------- shading
LIGHT = (-0.55, -0.8, 0.85)


def _norm(v):
    l = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / l for c in v)


def lambert_wrap(n, light=LIGHT, wrap=0.25):
    L = _norm(light)
    raw = n[0] * L[0] + n[1] * L[1] + n[2] * L[2]
    return max(0.0, (raw + wrap) / (1 + wrap))


def quant(v, ramp, th):
    i = 0
    while i < len(th) and v >= th[i]:
        i += 1
    return ramp[i]


def shade_fn(normal_fn, ramp, th, light=LIGHT, wrap=0.25):
    def f(x, y):
        return quant(lambert_wrap(normal_fn(x, y), light, wrap), ramp, th)
    return f

# ---------------------------------------------------------------- previews
DIGITS = {
    '0': ['111', '101', '101', '101', '111'], '1': ['010', '110', '010', '010', '111'],
    '2': ['111', '001', '111', '100', '111'], '3': ['111', '001', '111', '001', '111'],
    '4': ['101', '101', '111', '001', '001'], '5': ['111', '100', '111', '001', '111'],
    '6': ['111', '100', '111', '101', '111'], '7': ['111', '001', '001', '001', '001'],
    '8': ['111', '101', '111', '101', '111'], '9': ['111', '101', '111', '001', '111'],
}


def draw_text(img, x, y, s, col, sc=2):
    for k, ch in enumerate(s):
        g = DIGITS[ch]
        for j in range(5):
            for i in range(3):
                if g[j][i] == '1':
                    for yy in range(sc):
                        for xx in range(sc):
                            X, Y = x + (k * 4 + i) * sc + xx, y + j * sc + yy
                            if 0 <= X < len(img[0]) and 0 <= Y < len(img):
                                img[Y][X] = col


def rgba_strip(canvases, gap=0):
    n = len(canvases)
    w = n * W + (n - 1) * gap
    img = [[TRANSPARENT] * w for _ in range(H)]
    for i, c in enumerate(canvases):
        rg = to_rgba(c)
        ox = i * (W + gap)
        for y in range(H):
            img[y][ox:ox + W] = rg[y]
    return w, H, img


def preview(canvases, path, s=8, grid=True, bg='checker', rulers=True):
    if not isinstance(canvases[0][0], list):
        canvases = [canvases]
    w, h, rgba = rgba_strip(canvases, gap=0)
    if bg == 'checker':
        rgba = checker_bg(w, h, rgba, cell=4, c1=(190, 196, 204, 255), c2=(165, 172, 182, 255))
    elif bg is not None:
        rgba = [[p if p[3] == 255 else bg for p in row] for row in rgba]
    _, _, big = scale(w, h, rgba, s)
    if grid:
        for y in range(h * s):
            for x in range(w * s):
                if (x % s == 0 and (x // s) % 8 == 0) or (y % s == 0 and (y // s) % 8 == 0):
                    p = big[y][x]
                    big[y][x] = tuple((p[i] * 3 + (255 if i == 0 else 60)) // 4 for i in range(3)) + (255,)
                if x % (W * s) == 0:
                    big[y][x] = (255, 0, 255, 255)
    if not rulers:
        write_png(path, w * s, h * s, big)
        return
    M = 16
    TW, TH = w * s + M, h * s + M
    img = [[(40, 40, 48, 255)] * TW for _ in range(TH)]
    for y in range(h * s):
        img[y + M][M:] = big[y]
    for i in range(0, max(w, h), 8):
        if i < w:
            draw_text(img, M + (i % W) * s + 1, 3, str(i % W), (255, 230, 120, 255), sc=2)
        if i < h:
            draw_text(img, 0, M + i * s + 1, str(i), (255, 230, 120, 255), sc=2)
    write_png(path, TW, TH, img)
