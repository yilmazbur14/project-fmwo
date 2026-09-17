"""Liam v2 sprite toolkit: palette, masks, outlines, form shading, ASCII overlays, previews."""
import math
from pngio import *

W = H = 64

def hx(s):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)

PAL = {
    '#': hx('000000'),
    # skin (warm tan, cast ramp)
    'a': hx('fadcb8'), 's': hx('eec39a'), 'd': hx('d9a066'), 'f': hx('b8794a'), 'g': hx('8a5236'),
    # hair / beard (portrait near-black with warm lifts)
    'k': hx('120a08'), 'h': hx('1b0f0d'), 'H': hx('36201a'), 'r': hx('56352a'), 'R': hx('7d4c36'),
    # jacket brown (portrait base 8f563b / shadow 663931)
    'i': hx('c3885a'), 'j': hx('a96b43'), 'J': hx('8f563b'), 'n': hx('663931'), 'N': hx('45283c'),
    # white collar / bandage wraps
    'W': hx('ffffff'), 'w': hx('d6dee5'), 'v': hx('a3b1bc'),
    # grey-blue tie / headband cloth (portrait 9badb7)
    't': hx('c4d2da'), 'T': hx('9badb7'), 'y': hx('6e7d86'), 'Y': hx('4a5563'),
    # steel plates
    'm': hx('eef4f7'), 'M': hx('b3c0c9'), 'e': hx('7b8893'), 'E': hx('4b555e'),
    # navy trousers
    'p': hx('6b6bb0'), 'q': hx('4c4c8c'), 'Q': hx('3a3a70'), 'z': hx('26264c'), 'Z': hx('181830'),
    # shoes
    'o': hx('6a4a3a'), 'O': hx('45302a'), 'x': hx('2a1b16'),
    # lens / fx
    'L': hx('ffffff'), 'l': hx('cbdbfc'), 'b': hx('8fb3e8'),
    'c': hx('fff6a8'), 'C': hx('fbf236'),
    # mouth interior
    'u': hx('5a1f22'), 'U': hx('9a3a3a'),
}
TRANSPARENT = (0, 0, 0, 0)

def new_img(fill=None):
    return [[fill for _ in range(W)] for _ in range(H)]

# ---------------------------------------------------------------- masks
def poly_mask(pts, w=W, h=H):
    """Even-odd fill using pixel centres."""
    m = [[False] * w for _ in range(h)]
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
                    m[y][x] = True
    return m

def ellipse_mask(cx, cy, rx, ry):
    m = [[False] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0:
                m[y][x] = True
    return m

def capsule_mask(ax, ay, bx, by, r):
    m = [[False] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            if seg_dist(x + 0.5, y + 0.5, ax, ay, bx, by)[0] <= r:
                m[y][x] = True
    return m

def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
    qx, qy = ax + t * dx, ay + t * dy
    return math.hypot(px - qx, py - qy), (px - qx, py - qy)

def m_or(*ms):
    return [[any(m[y][x] for m in ms) for x in range(W)] for y in range(H)]

def m_and(a, b):
    return [[a[y][x] and b[y][x] for x in range(W)] for y in range(H)]

def m_sub(a, b):
    return [[a[y][x] and not b[y][x] for x in range(W)] for y in range(H)]

def outline_pixels(mask, prune=True, return_pruned=False):
    """Inner boundary (4-neighbour) with pixel-perfect L-corner pruning.
    Pruned corner pixels are returned separately so the caller can restore what was underneath."""
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
    if return_pruned:
        return ol, pruned
    return ol

# ---------------------------------------------------------------- shading
LIGHT = (-0.55, -0.75, 0.95)

def _norm(v):
    l = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / l for c in v)

def sphere_normal(x, y, cx, cy, rx, ry):
    nx = (x + 0.5 - cx) / rx
    ny = (y + 0.5 - cy) / ry
    d2 = nx * nx + ny * ny
    if d2 >= 1.0:
        l = math.sqrt(d2)
        return (nx / l, ny / l, 0.0)
    return (nx, ny, math.sqrt(1 - d2))

def capsule_normal(x, y, ax, ay, bx, by, r):
    d, (vx, vy) = seg_dist(x + 0.5, y + 0.5, ax, ay, bx, by)
    nx, ny = vx / r, vy / r
    d2 = nx * nx + ny * ny
    if d2 >= 1.0:
        l = math.sqrt(d2)
        return (nx / l, ny / l, 0.0)
    return (nx, ny, math.sqrt(1 - d2))

def lambert(n, light=LIGHT, amb=0.0):
    L = _norm(light)
    return max(0.0, n[0] * L[0] + n[1] * L[1] + n[2] * L[2]) + amb

def quant(v, ramp, th):
    """ramp: chars dark->light. th: ascending thresholds, len(ramp)-1."""
    i = 0
    while i < len(th) and v >= th[i]:
        i += 1
    return ramp[i]

# ---------------------------------------------------------------- canvas ops (char canvas)
def blank_chars():
    return [['.' for _ in range(W)] for _ in range(H)]

def paint_mask(canvas, mask, fn):
    for y in range(H):
        for x in range(W):
            if mask[y][x]:
                c = fn(x, y)
                if c is not None:
                    canvas[y][x] = c

def paint_outline(canvas, mask, prune=True, ch='#', under=None):
    ol, pruned = outline_pixels(mask, prune, return_pruned=True)
    for y in range(H):
        for x in range(W):
            if ol[y][x]:
                canvas[y][x] = ch
    for (x, y) in pruned:
        canvas[y][x] = under[y][x] if under is not None else '.'

def paint_part(canvas, mask, fn, outline=True, prune=True):
    """Fill mask with fn, outline it; pruned outline corners restore the previous canvas content."""
    under = [row[:] for row in canvas]
    paint_mask(canvas, mask, fn)
    if outline:
        paint_outline(canvas, mask, prune, under=under)

def overlay(canvas, ox, oy, text, skip='. ', erase='_'):
    lines = text.strip('\n').split('\n')
    for j, line in enumerate(lines):
        for i, ch in enumerate(line):
            X, Y = ox + i, oy + j
            if not (0 <= X < W and 0 <= Y < H):
                continue
            if ch in skip:
                continue
            canvas[Y][X] = '.' if ch == erase else ch

def put(canvas, x, y, s):
    for i, ch in enumerate(s):
        if 0 <= x + i < W and 0 <= y < H and ch != ' ':
            canvas[y][x + i] = '.' if ch == '_' else ch

def composite(dst, src):
    for y in range(H):
        for x in range(W):
            if src[y][x] != '.':
                dst[y][x] = src[y][x]

def shift(canvas, dx, dy):
    out = blank_chars()
    for y in range(H):
        for x in range(W):
            X, Y = x + dx, y + dy
            if 0 <= X < W and 0 <= Y < H and canvas[y][x] != '.':
                out[Y][X] = canvas[y][x]
    return out

def to_text(canvas):
    return '\n'.join(''.join(r) for r in canvas)

def from_text(text):
    lines = text.strip('\n').split('\n')
    assert len(lines) == H, len(lines)
    c = []
    for ln in lines:
        assert len(ln) == W, (len(ln), ln)
        c.append(list(ln))
    return c

def to_rgba(canvas):
    return [[(PAL[ch] if ch != '.' else TRANSPARENT) for ch in row] for row in canvas]

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

def preview(canvas_or_rgba, path, s=8, rulers=True, grid=True, bg='checker', is_rgba=False, w=W, h=H):
    rgba = canvas_or_rgba if is_rgba else to_rgba(canvas_or_rgba)
    if bg == 'checker':
        rgba = checker_bg(w, h, rgba, cell=4, c1=(190, 196, 204, 255), c2=(160, 168, 178, 255))
    elif bg is not None:
        rgba = [[p if p[3] == 255 else bg for p in row] for row in rgba]
    _, _, big = scale(w, h, rgba, s)
    if grid:
        for y in range(h * s):
            for x in range(w * s):
                if (x % s == 0 and (x // s) % 4 == 0) or (y % s == 0 and (y // s) % 4 == 0):
                    p = big[y][x]
                    big[y][x] = tuple((p[i] * 3 + (255 if i != 1 else 0)) // 4 for i in range(3)) + (255,)
    if not rulers:
        write_png(path, w * s, h * s, big)
        return
    M = 26
    TW, TH = w * s + M, h * s + M
    img = [[(40, 40, 48, 255)] * TW for _ in range(TH)]
    for y in range(h * s):
        img[y + M][M:] = big[y]
    for i in range(0, max(w, h), 4):
        if i < w:
            draw_text(img, M + i * s + 1, 4, str(i), (255, 230, 120, 255), sc=2)
        if i < h:
            draw_text(img, 1, M + i * s + 1, str(i), (255, 230, 120, 255), sc=2)
    write_png(path, TW, TH, img)
