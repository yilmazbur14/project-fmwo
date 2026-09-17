"""Josh v2 sprite toolkit: palette, masks, outlines, height-field muscle shading, previews.
Char canvas: 64x64 list of lists of palette chars ('.' = transparent)."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png, write_png, scale, checker_bg

W = H = 64
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
os.makedirs(OUT, exist_ok=True)


def hx(s):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


PAL = {
    '#': hx('000000'),
    # skin: fair, warm, rosy undertone (5-tone + spec)
    '1': hx('fff0dc'), 'a': hx('fbd6b0'), 's': hx('f0b98e'), 'd': hx('db976c'), 'f': hx('b86c4e'), 'g': hx('84412f'),
    # blush / lips
    'r': hx('f09c86'), 'R': hx('d27463'),
    # stubble tint
    't': hx('d9ab93'), 'T': hx('b58773'),
    # hair / facial hair: near-black brown with warm sheen
    'k': hx('130b09'), 'h': hx('24160f'), 'H': hx('3d261a'), 'j': hx('5f3c29'), 'J': hx('8a5b3d'),
    # eyes / teeth / mouth
    'e': hx('3a2014'), 'w': hx('ffffff'), 'W': hx('d3d9e4'), 'm': hx('6e1f2a'), 'M': hx('b0464c'),
    # sunglasses (blue lenses)
    'b': hx('173c8a'), 'B': hx('2a67c9'), 'c': hx('5fa8f0'), 'C': hx('c8ecff'),
    # speedo orange
    'o': hx('ffc36a'), 'O': hx('f8912c'), 'p': hx('dd6a1a'), 'P': hx('a94811'), 'q': hx('6e2d0b'),
    # boots black
    'x': hx('111117'), 'X': hx('22222b'), 'v': hx('383845'), 'V': hx('5a5a6a'), 'n': hx('8d8da0'),
    # fx
    'z': hx('ffffff'), 'Z': hx('d8e8e8'), 'y': hx('9fb4c4'),
    # dust (matches Assets/Characters/Mason/elbow_impact.png)
    'u': hx('fbf6e8'), 'U': hx('e6dcc2'), 'i': hx('c4b494'), 'I': hx('978769'), 'l': hx('5a4a3a'),
}
TRANSPARENT = (0, 0, 0, 0)
LIGHT = (-0.55, -0.75, 0.95)


def _norm(v):
    l = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / l for c in v)


LN = _norm(LIGHT)


# ------------------------------------------------------------------ canvas
def blank():
    return [['.' for _ in range(W)] for _ in range(H)]


def copy(c):
    return [r[:] for r in c]


def composite(dst, src):
    for y in range(H):
        for x in range(W):
            if src[y][x] != '.':
                dst[y][x] = src[y][x]


def compose(layers):
    cv = blank()
    for l in layers:
        composite(cv, l)
    return cv


def to_text(c):
    return '\n'.join(''.join(r) for r in c)


def from_text(t, w=W, h=H):
    lines = [ln for ln in t.strip('\n').split('\n')]
    assert len(lines) == h, len(lines)
    for i, ln in enumerate(lines):
        assert len(ln) == w, (i, len(ln), ln)
    return [list(ln) for ln in lines]


def to_rgba(c):
    return [[(PAL[ch] if ch != '.' else TRANSPARENT) for ch in row] for row in c]


def overlay(c, ox, oy, text, skip='. ', erase='_'):
    lines = text.strip('\n').split('\n')
    for j, line in enumerate(lines):
        for i, ch in enumerate(line):
            X, Y = ox + i, oy + j
            if 0 <= X < W and 0 <= Y < H and ch not in skip:
                c[Y][X] = '.' if ch == erase else ch


def block(c, x0, y0, rows, skip='. ', erase='_'):
    for r in rows:
        for ch in r:
            assert ch in PAL or ch in '._ ', 'bad char %r in %r' % (ch, r)
    for j, line in enumerate(rows):
        for i, ch in enumerate(line):
            X, Y = x0 + i, y0 + j
            if 0 <= X < W and 0 <= Y < H and ch not in skip:
                c[Y][X] = '.' if ch == erase else ch


def put(c, x, y, ch):
    if 0 <= x < W and 0 <= y < H:
        c[y][x] = ch


# ------------------------------------------------------------------ masks
def mask_empty():
    return [[False] * W for _ in range(H)]


def poly_mask(pts):
    m = mask_empty()
    n = len(pts)
    for y in range(H):
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
            for x in range(max(0, int(math.ceil(xa - 0.5))), min(W, int(math.floor(xb - 0.5)) + 1)):
                if xa <= x + 0.5 <= xb:
                    m[y][x] = True
    return m


def ellipse_mask(cx, cy, rx, ry):
    m = mask_empty()
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
    m = mask_empty()
    for y in range(H):
        for x in range(W):
            px, py = x + 0.5, y + 0.5
            t, qx, qy = seg_t(px, py, ax, ay, bx, by)
            if math.hypot(px - qx, py - qy) <= r0 + (r1 - r0) * t:
                m[y][x] = True
    return m


def m_or(*ms):
    return [[any(m[y][x] for m in ms) for x in range(W)] for y in range(H)]


def m_and(a, b):
    return [[a[y][x] and b[y][x] for x in range(W)] for y in range(H)]


def m_sub(a, b):
    return [[a[y][x] and not b[y][x] for x in range(W)] for y in range(H)]


def m_count(m):
    return sum(sum(1 for v in r if v) for r in m)


def outline_pixels(mask, prune=True):
    """Inner 4-neighbour boundary with pixel-perfect L-corner pruning. Returns (ol, pruned)."""
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


def paint_mask(c, mask, fn):
    for y in range(H):
        for x in range(W):
            if mask[y][x]:
                v = fn(x, y)
                if v is not None:
                    c[y][x] = v


def paint_part(c, mask, fn, outline=True, prune=True, ch='#'):
    under = copy(c)
    paint_mask(c, mask, fn)
    if outline:
        ol, pruned = outline_pixels(mask, prune)
        for y in range(H):
            for x in range(W):
                if ol[y][x]:
                    c[y][x] = ch
        for (x, y) in pruned:
            c[y][x] = under[y][x]


# ------------------------------------------------------------------ shading
def lambert_n(n, light=LN):
    return n[0] * light[0] + n[1] * light[1] + n[2] * light[2]


def quant(v, ramp, th):
    i = 0
    while i < len(th) and v >= th[i]:
        i += 1
    return ramp[i]


def sphere_normal(x, y, cx, cy, rx, ry):
    nx = (x + 0.5 - cx) / rx
    ny = (y + 0.5 - cy) / ry
    d2 = nx * nx + ny * ny
    if d2 >= 1.0:
        l = math.sqrt(d2)
        return (nx / l, ny / l, 0.0)
    return (nx, ny, math.sqrt(1 - d2))


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


def shade_normal(normal_fn, ramp, th, wrap=0.0):
    def f(x, y):
        raw = lambert_n(normal_fn(x, y))
        v = max(0.0, (raw + wrap) / (1 + wrap))
        return quant(v, ramp, th)
    return f


# height-field shading ------------------------------------------------
def dome(px, py, cx, cy, rx, ry, amp, power=1.0):
    d2 = ((px - cx) / rx) ** 2 + ((py - cy) / ry) ** 2
    if d2 >= 1:
        return 0.0
    return amp * (1 - d2) ** power


def dome4(px, py, cx, cy, rl, rr, rt, rb, amp, power=1.0):
    """Asymmetric dome: separate radii left/right/top/bottom."""
    rx = rl if px < cx else rr
    ry = rt if py < cy else rb
    return dome(px, py, cx, cy, rx, ry, amp, power)


def hf_values(mask, hfn, eps=0.5, zscale=1.0):
    """Returns dict (x,y) -> (lambert, laplacian) for pixels in mask."""
    out = {}
    for y in range(H):
        for x in range(W):
            if not mask[y][x]:
                continue
            px, py = x + 0.5, y + 0.5
            h0 = hfn(px, py)
            hxp = hfn(px + eps, py); hxm = hfn(px - eps, py)
            hyp = hfn(px, py + eps); hym = hfn(px, py - eps)
            gx = (hxp - hxm) / (2 * eps) * zscale
            gy = (hyp - hym) / (2 * eps) * zscale
            n = _norm((-gx, -gy, 1.0))
            lap = (hxp + hxm + hyp + hym - 4 * h0) / (eps * eps)
            out[(x, y)] = (lambert_n(n), lap, h0)
    return out


# ------------------------------------------------------------------ previews
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


def rgba_checker(rgba, w, h, cell=4):
    return checker_bg(w, h, rgba, cell=cell, c1=(190, 196, 204, 255), c2=(160, 168, 178, 255))


def preview(c, path, s=8, rulers=True, grid=True, w=W, h=H, rgba=None, bg='checker'):
    rgba = rgba if rgba is not None else to_rgba(c)
    if bg == 'checker':
        rgba = rgba_checker(rgba, w, h)
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


def save_png(c, path):
    write_png(path, W, H, to_rgba(c))


def load_block(path):
    """Text block file: first line '@x,y', optional ruler line of digits, then rows."""
    lines = [ln.rstrip('\n') for ln in open(path).read().split('\n')]
    lines = [ln for ln in lines if ln != '']
    assert lines[0].startswith('@'), path
    x0, y0 = map(int, lines[0][1:].split(','))
    rows = lines[1:]
    if rows and all(ch.isdigit() for ch in rows[0]):
        rows = rows[1:]
    wd = len(rows[0])
    for i, r in enumerate(rows):
        assert len(r) == wd, '%s row %d (y=%d) len %d != %d: %r' % (path, i, y0 + i, len(r), wd, r)
        for ch in r:
            assert ch in PAL or ch in '._', '%s row %d bad char %r' % (path, i, ch)
    return x0, y0, rows


def despeckle(c, chars='gfdsa1', region=None, passes=2, protect=None):
    """Replace pixels of `chars` that have no 4-neighbour of the same char with the most common
    4-neighbour char from `chars` (needs >= 2 votes). region: optional mask limiting edits."""
    changed_total = 0
    for _ in range(passes):
        src = copy(c)
        changed = 0
        for y in range(H):
            for x in range(W):
                ch = src[y][x]
                if ch not in chars:
                    continue
                if region is not None and not region[y][x]:
                    continue
                if protect is not None and protect[y][x]:
                    continue
                nb = []
                for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    X, Y = x + dx, y + dy
                    if 0 <= X < W and 0 <= Y < H:
                        nb.append(src[Y][X])
                if ch in nb:
                    continue
                votes = {}
                for n in nb:
                    if n in chars:
                        votes[n] = votes.get(n, 0) + 1
                if not votes:
                    continue
                best = max(votes.items(), key=lambda kv: (kv[1], -abs(chars.index(kv[0]) - chars.index(ch))))
                if best[1] >= 2:
                    c[y][x] = best[0]
                    changed += 1
        changed_total += changed
        if not changed:
            break
    return changed_total


def shift_canvas(c, dx, dy):
    out = blank()
    for y in range(H):
        for x in range(W):
            if c[y][x] != '.':
                X, Y = x + dx, y + dy
                if 0 <= X < W and 0 <= Y < H:
                    out[Y][X] = c[y][x]
    return out


def merge_small_regions(c, region, chars='gfdsa1', max_size=2, passes=3):
    """Merge 4-connected same-tone islands of <= max_size pixels (inside region) into the most common
    bordering tone from `chars`. Keeps highlights '1' untouched."""
    total = 0
    for _ in range(passes):
        seen = [[False] * W for _ in range(H)]
        changed = 0
        for y in range(H):
            for x in range(W):
                if seen[y][x] or not region[y][x] or c[y][x] not in chars or c[y][x] == '1':
                    continue
                ch = c[y][x]
                comp, stack = [], [(x, y)]
                seen[y][x] = True
                while stack:
                    px, py = stack.pop()
                    comp.append((px, py))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        X, Y = px + dx, py + dy
                        if 0 <= X < W and 0 <= Y < H and not seen[Y][X] and region[Y][X] and c[Y][X] == ch:
                            seen[Y][X] = True
                            stack.append((X, Y))
                if len(comp) > max_size:
                    continue
                votes = {}
                cs = set(comp)
                for (px, py) in comp:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        X, Y = px + dx, py + dy
                        if (X, Y) in cs or not (0 <= X < W and 0 <= Y < H):
                            continue
                        n = c[Y][X]
                        if n in chars and n != '1':
                            votes[n] = votes.get(n, 0) + 1
                if not votes:
                    continue
                best = max(votes.items(), key=lambda kv: (kv[1], -abs(chars.index(kv[0]) - chars.index(ch))))[0]
                for (px, py) in comp:
                    c[py][px] = best
                changed += 1
        total += changed
        if not changed:
            break
    return total
