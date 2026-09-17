"""Big-frame composition helpers for the re-proportioned Eric (frame W x H, feet on bottom edge)."""
import math
import scaled as SC  # sets sys.path to the shared toolkit first
import lib
from lib import PALC, BLACK, _DARKER, _LIGHTER, TH_METAL, TH_SOFT
import body_s
import scaled as SC

T0 = (0, 0, 0, 0)


class Big:
    def __init__(self, W, H):
        self.W, self.H = W, H
        self.px = [[None] * W for _ in range(H)]
        self.ox, self.oy = W // 2 - 48, H - 96     # 96-space body -> frame

    def put96(self, img, dx=0, dy=0):
        for y in range(96):
            yy = y + self.oy + dy
            if not 0 <= yy < self.H:
                continue
            for x in range(96):
                p = img[y][x]
                if p[3]:
                    xx = x + self.ox + dx
                    if 0 <= xx < self.W:
                        self.px[yy][xx] = p

    def set(self, x, y, ch):
        if 0 <= x < self.W and 0 <= y < self.H:
            self.px[y][x] = PALC[ch]

    def get(self, x, y):
        return self.px[y][x] if 0 <= x < self.W and 0 <= y < self.H else None

    def stamp(self, grid, x0, y0):
        for dy, row in enumerate(grid.strip('\n').split('\n')):
            for dx, ch in enumerate(row):
                if ch in '. ':
                    continue
                self.set(x0 + dx, y0 + dy, ch)

    def canvas(self):
        lib.W, lib.H = self.W, self.H
        c = lib.Canvas()
        c.px = self.px
        return c

    def rgba(self):
        return [[(p if p is not None else T0) for p in row] for row in self.px]


def body(fr, skip=(), extra_first=None):
    L = body_s.layers()
    for n in body_s.ORDER:
        if extra_first and n in extra_first:
            fr.put96(extra_first[n])
        if n not in skip:
            fr.put96(L[n])


def bar(fr, p0, p1, tones, point_rows=0, cap0=True, cap1=True, pattern=None):
    x0, y0 = p0
    x1, y1 = p1
    steep = abs(y1 - y0) >= abs(x1 - x0)
    n = len(tones)
    a, b = (int(round(y0)), int(round(y1))) if steep else (int(round(x0)), int(round(x1)))
    step = 1 if b >= a else -1
    idx = list(range(a, b + step, step))
    L = len(idx)
    runs = {}
    for i, m in enumerate(idx):
        t = i / max(1, L - 1)
        c = (x0 + (x1 - x0) * t) if steep else (y0 + (y1 - y0) * t)
        start = int(math.floor(c - n / 2 + 0.5))
        inset = 0
        if point_rows:
            d = L - 1 - i
            if d < point_rows:
                inset = int(math.ceil((point_rows - d) * (n / 2 - 1.5) / point_rows))
        li = ri = inset
        if n - li - ri < 3:
            continue
        run = list(tones[li:n - ri]) if inset else list(tones)
        run[0] = run[-1] = 'k'
        if inset and len(run) > 4:
            run[1], run[2] = tones[1], tones[2]
            run[-2], run[-3] = tones[-2], tones[-3]
        if pattern:
            run = [pattern(i, j + li, ch) for j, ch in enumerate(run)]
        runs[i] = (m, start + li, run)
        for j, ch in enumerate(run):
            x, y = (start + li + j, m) if steep else (m, start + li + j)
            fr.set(x, y, ch)
    kept = sorted(runs)
    for which, on in ((kept[0] if kept else None, cap0), (kept[-1] if kept else None, cap1)):
        if on and which in runs:
            m, s, run = runs[which]
            for j in range(len(run)):
                fr.set(*((s + j, m) if steep else (m, s + j)), 'k')
    keys = sorted(runs)
    for ka, kb in zip(keys, keys[1:]):
        ma, sa, ra = runs[ka]
        mb, sb, rb = runs[kb]
        ea, eb = sa + len(ra) - 1, sb + len(rb) - 1
        for lo, hi, m in ((min(sa, sb), max(sa, sb), ma if sa > sb else mb),
                          (min(ea, eb), max(ea, eb), mb if ea > eb else ma)):
            for q in range(lo + 1, hi):
                fr.set(*((q, m) if steep else (m, q)), 'k')
    return runs


# ---- the 1.25x greatsword
BLADE = "kJIJ" + "K" * 14 + "LLNMMMNk"      # 26 wide
GRIP = "kmmnnok"                             # 7 wide
GUARD = "kJIKKLMNk"                          # 9 thick
BLADE_LEN, POINT, GRIP_LEN, GUARD_HALF = 110, 13, 24, 16.5
PITS = {(11, 7): 'L', (11, 8): 'L', (20, 14): 'L', (27, 6): 'L', (27, 7): 'L', (34, 11): 'L', (39, 15): 'L',
        (39, 16): 'L', (47, 7): 'L', (55, 12): 'L', (61, 6): 'L', (61, 7): 'L', (67, 14): 'L', (75, 10): 'L',
        (80, 15): 'L', (85, 8): 'L', (93, 12): 'L', (98, 7): 'L', (51, 15): 'L', (30, 18): 'L', (72, 19): 'L',
        (16, 6): 'J', (17, 6): 'J', (45, 11): 'J', (46, 11): 'J', (65, 10): 'J', (66, 10): 'J', (90, 7): 'J',
        (91, 7): 'J'}


def grip_pattern(i, j, ch):
    if ch in 'mno':
        w = ((i + j) // 2) % 2
        return {'m': 'l' if w else 'm', 'n': 'm' if w else 'n', 'o': 'o' if w else 'p'}[ch]
    return ch


POMMEL = """
.kkkkkkk.
kIJJJKKLk
kJKKKKLMk
kKLLLLMNk
kLMMMMNNk
.kkkkkkk.
"""


def _transpose(grid):
    rows = grid.strip('\n').split('\n')
    return '\n'.join(''.join(r[i] for r in rows) for i in range(len(rows[0])))


def sword(fr, guard_c, direction, blade_len=BLADE_LEN, grip_len=GRIP_LEN):
    gx, gy = guard_c
    ux, uy = direction
    L = math.hypot(ux, uy)
    ux, uy = ux / L, uy / L
    steep = abs(uy) >= abs(ux)
    axis_aligned = abs(ux) < 1e-9 or abs(uy) < 1e-9
    if axis_aligned:
        # Exactly vertical/horizontal: the .5 offsets below round half-to-even and could leave a 1 px
        # transparent seam at the guard/blade and grip/pommel joints. Snap every piece to whole
        # pixels flush against its neighbour instead. (Diagonal swords keep the original offsets, so
        # the approved idle is unchanged.)
        gx, gy = int(round(gx)), int(round(gy))
        ux, uy = int(round(ux)), int(round(uy))
        b0 = (gx + ux * 5, gy + uy * 5)                  # first blade run touches the 9-thick guard
        tip = (gx + ux * (5 + blade_len), gy + uy * (5 + blade_len))
        g1 = (gx - ux * 5, gy - uy * 5)                  # grip starts just outside the guard
        g2 = (gx - ux * (5 + grip_len - 1), gy - uy * (5 + grip_len - 1))
        pc = (gx - ux * (5 + grip_len + 3), gy - uy * (5 + grip_len + 3))   # 6-deep pommel flush with grip end
    else:
        b0 = (gx + ux * 5.5, gy + uy * 5.5)
        tip = (gx + ux * (5.5 + blade_len), gy + uy * (5.5 + blade_len))
        g1 = (gx - ux * 4.5, gy - uy * 4.5)
        g2 = (gx - ux * (4.5 + grip_len), gy - uy * (4.5 + grip_len))
        pc = (gx - ux * (grip_len + 8), gy - uy * (grip_len + 8))
    runs_len = int(abs(round(tip[1]) - round(b0[1]))) if steep else int(abs(round(tip[0]) - round(b0[0])))
    pm = {(runs_len - i, j): c for (i, j), c in PITS.items()}
    bar(fr, b0, tip, BLADE, point_rows=POINT, cap0=True,
        pattern=lambda i, j, ch: pm.get((i, j), ch) if ch == 'K' else ch)
    bar(fr, g1, g2, GRIP, pattern=grip_pattern)
    grid = POMMEL if steep else _transpose(POMMEL)
    gr = grid.strip('\n').split('\n')
    if axis_aligned:
        # place the pommel so its near edge sits on the row/column right after the grip end
        if steep:
            px0 = gx - len(gr[0]) // 2
            py0 = (g2[1] - uy * len(gr)) if uy > 0 else (g2[1] + 1)
        else:
            py0 = gy - len(gr) // 2
            px0 = (g2[0] - ux * len(gr[0])) if ux > 0 else (g2[0] + 1)
        fr.stamp(grid, int(px0), int(py0))
    else:
        fr.stamp(grid, int(round(pc[0])) - len(gr[0]) // 2, int(round(pc[1])) - len(gr) // 2)
    px_, py_ = -uy, ux
    bar(fr, (gx - px_ * GUARD_HALF, gy - py_ * GUARD_HALF), (gx + px_ * GUARD_HALF, gy + py_ * GUARD_HALF), GUARD)
    return dict(tip=tip, pommel=pc, guard=guard_c)


def limb(fr, a, b, width, ramp='plate'):
    cv = fr.canvas()
    ax, ay = a
    bx, by = b
    L = math.hypot(bx - ax, by - ay)
    nx, ny = -(by - ay) / L * width / 2, (bx - ax) / L * width / 2
    m = lib.poly([(ax + nx, ay + ny), (bx + nx, by + ny), (bx - nx, by - ny), (ax - nx, ay - ny)])
    cv.part(m, ramp, ('cyl', a, b, width / 2 + 0.5), th=TH_METAL if ramp == 'plate' else TH_SOFT)
    if ramp == 'chain':
        for y in range(fr.H):
            for x in range(fr.W):
                if m[y][x] and fr.px[y][x] not in (None, BLACK) and (x + y) % 2 == 0:
                    fr.px[y][x] = _DARKER.get(fr.px[y][x], fr.px[y][x])


def cop(fr, c, rx, ry):
    cv = fr.canvas()
    m = lib.ell(c[0], c[1], rx, ry)
    cv.part(m, 'plate', ('sphere', c[0] - 1, c[1] - 1.2, rx + 0.6, ry + 0.8), th=TH_METAL)


def cast_shadow(fr, pts, dx=1, dy=2):
    s = set(pts)
    for x, y in {(x + dx, y + dy) for x, y in pts} - s:
        c = fr.get(x, y)
        if c is not None and c != BLACK:
            fr.px[y][x] = _DARKER.get(c, c)


def fist(fr, cx, cy, horizontal=False, shadow=True):
    g = SC.FIST_V_S if not horizontal else _transpose(SC.FIST_V_S)
    rows = g.strip('\n').split('\n')
    x0, y0 = int(round(cx)) - len(rows[0]) // 2, int(round(cy)) - len(rows) // 2
    if shadow:
        cast_shadow(fr, [(x0 + c, y0 + r) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch != '.'])
    fr.stamp(g, x0, y0)


def to_bg(px, bg=(136, 180, 99, 255)):
    return [[(p if p[3] else bg) for p in row] for row in px]
