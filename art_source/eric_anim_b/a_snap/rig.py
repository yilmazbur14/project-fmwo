"""Eric animation rig. Body layers are rendered once with the approved part functions (96-space),
then composed in a 128x128 frame with per-layer offsets. Weapon/arms/FX are drawn per frame in 128-space."""
import os
import sys
import math

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import lib
from lib import PALC, BLACK, _DARKER, _LIGHTER, TH_SOFT, TH_METAL, RAMPS, hexc
import parts
from parts import (cape, flap, tassets, tasset_details, belt, torso, torso_details, belt_details,
                   gorget, pauldron, pauldron_details, ID)
from parts import mirror as mirror96
from legstamp import stamp_legs
from headrender import render_head
from headstrokes import STROKES
import weapons
from weapons import FIST_V, arm_right_back, arm_right_front, arm_left_back

FW = FH = 128
OX, OY = 16, 32
T = (0, 0, 0, 0)


def _layer(fn):
    lib.W = lib.H = 96
    cv = lib.Canvas()
    fn(cv)
    return cv.rgba()


def _torso_layer(cv):
    tm = torso(cv)
    torso_details(cv, tm)


def _paul(f):
    def go(cv):
        d, l1, l2 = pauldron(cv, f)
        pauldron_details(cv, f, d, l1, l2)
    return go


def _tass(cv):
    tassets(cv)
    tasset_details(cv)


LAYER_FNS = [
    ('cape', cape), ('legs', stamp_legs), ('flap', flap), ('tassets', _tass), ('belt', belt),
    ('torso', _torso_layer), ('buckle', belt_details), ('gorget', gorget), ('armR_back', arm_right_back),
    ('armL_back', arm_left_back), ('paulL', _paul(ID)), ('paulR', _paul(mirror96)), ('armR_front', arm_right_front),
    ('head', lambda cv: render_head(cv, STROKES)),
]

_CACHE = {}


def layers():
    if "head" not in _CACHE:
        for name, fn in LAYER_FNS:
            _CACHE[name] = _layer(fn)
    return _CACHE


def layer_from(name, fn):
    _CACHE[name] = _layer(fn)
    return _CACHE[name]


# ------------------------------------------------------------------ frame canvas (128)
class Frame:
    def __init__(self):
        self.px = [[None] * FW for _ in range(FH)]

    def put(self, img, dx=0, dy=0, ox=OX, oy=OY):
        h, w = len(img), len(img[0])
        for y in range(h):
            yy = y + oy + dy
            if not 0 <= yy < FH:
                continue
            row = img[y]
            for x in range(w):
                p = row[x]
                if p[3]:
                    xx = x + ox + dx
                    if 0 <= xx < FW:
                        self.px[yy][xx] = p

    def set(self, x, y, ch):
        if 0 <= x < FW and 0 <= y < FH:
            self.px[y][x] = None if ch == '_' else PALC[ch]

    def setc(self, x, y, col):
        if 0 <= x < FW and 0 <= y < FH:
            self.px[y][x] = col

    def get(self, x, y):
        if 0 <= x < FW and 0 <= y < FH:
            return self.px[y][x]
        return None

    def stamp(self, grid, x0, y0, over_only=False):
        rows = grid.strip('\n').split('\n')
        for dy, row in enumerate(rows):
            for dx, ch in enumerate(row):
                if ch in '. ':
                    continue
                x, y = x0 + dx, y0 + dy
                if not (0 <= x < FW and 0 <= y < FH):
                    continue
                cur = self.px[y][x]
                if over_only and cur is None:
                    continue
                if ch == '-':
                    if cur is not None:
                        self.px[y][x] = _DARKER.get(cur, cur)
                elif ch == '+':
                    if cur is not None:
                        self.px[y][x] = _LIGHTER.get(cur, cur)
                else:
                    self.set(x, y, ch)

    def as_canvas(self):
        """lib.Canvas view sharing pixels (lib.W must be 128)"""
        lib.W = lib.H = FW
        c = lib.Canvas()
        c.px = self.px
        return c

    def rgba(self):
        return [[(p if p is not None else T) for p in row] for row in self.px]


def stamp_mask(grid, x0, y0):
    rows = grid.strip('\n').split('\n')
    pts = []
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch not in '. ':
                pts.append((x0 + c, y0 + r))
    return pts


def cast_shadow_pts(fr, pts, dx, dy, steps=1):
    s = set(pts)
    tgt = set()
    for x, y in pts:
        q = (x + dx, y + dy)
        if q not in s:
            tgt.add(q)
    for x, y in tgt:
        c = fr.get(x, y)
        if c is not None and c != BLACK:
            for _ in range(steps):
                c = _DARKER.get(c, c)
            fr.px[y][x] = c


# ------------------------------------------------------------------ generic thick bar (blade / grip / guard)
def bar(fr, p0, p1, tones, point_rows=0, cap0=True, cap1=True, pattern=None, clip=None):
    """Draw a straight bar from p0 to p1 (centre line, 128 coords) as parallel runs.
    tones: string across the bar, lit side first (left for steep bars, top for flat bars).
    point_rows: taper length (in runs) at the p1 end. pattern(i_run, k_across, ch) -> ch lets callers add
    texture. Returns dict run_index -> (start, tones)."""
    x0, y0 = p0
    x1, y1 = p1
    steep = abs(y1 - y0) >= abs(x1 - x0)
    n = len(tones)
    if steep:
        ya, yb = int(round(y0)), int(round(y1))
        step = 1 if yb >= ya else -1
        idx = list(range(ya, yb + step, step))
    else:
        xa, xb = int(round(x0)), int(round(x1))
        step = 1 if xb >= xa else -1
        idx = list(range(xa, xb + step, step))
    L = len(idx)
    runs = {}
    prev_inset = 0
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
        k = n - li - ri
        if k < 3:
            continue
        run = list(tones[li:n - ri]) if (li or ri) else list(tones)
        run[0] = 'k'
        run[-1] = 'k'
        if li and len(run) > 4:
            run[1] = tones[1]
            run[2] = tones[2]
        if ri and len(run) > 4:
            run[-2] = tones[-2]
            run[-3] = tones[-3]
        if pattern:
            run = [pattern(i, j + li, ch) for j, ch in enumerate(run)]
        runs[i] = (m, start + li, run)
        for j, ch in enumerate(run):
            if steep:
                x, y = start + li + j, m
            else:
                x, y = m, start + li + j
            if clip and not clip(x, y):
                continue
            fr.set(x, y, ch)
    # caps
    for which, on in ((0, cap0), (L - 1, cap1)):
        if on and which in runs:
            m, s, run = runs[which]
            for j in range(len(run)):
                x, y = (s + j, m) if steep else (m, s + j)
                if clip and not clip(x, y):
                    continue
                fr.set(x, y, 'k')
    # close stair gaps between consecutive runs (edge jumps of 2+)
    keys = sorted(runs)
    for a, b in zip(keys, keys[1:]):
        ma, sa, ra = runs[a]
        mb, sb, rb = runs[b]
        ea, eb = sa + len(ra) - 1, sb + len(rb) - 1
        for lo, hi, m in ((min(sa, sb), max(sa, sb), ma if sa > sb else mb), (min(ea, eb), max(ea, eb), mb if ea > eb else ma)):
            if hi - lo >= 2:
                for q in range(lo + 1, hi):
                    x, y = (q, m) if steep else (m, q)
                    if not (clip and not clip(x, y)):
                        fr.set(x, y, 'k')
    return runs


BLADE_V = "kJIJKKKKKKKKKKKLNMMNk"      # steep blade, lit edge on the left
BLADE_H = "kJIJKKKKKKKKKKKLNMMNk"      # flat blade, lit edge on top (same scheme)
GRIP_T = "kmmnok"
GUARD_T = "kJKKLMk"


def pits(seed_pts):
    def f(i, j, ch):
        if ch == 'K' and (i, j) in seed_pts:
            return seed_pts[(i, j)]
        return ch
    return f


PIT_MAP = {(9, 6): 'L', (9, 7): 'L', (16, 11): 'L', (22, 5): 'L', (22, 6): 'L', (27, 9): 'L', (31, 12): 'L',
           (31, 13): 'L', (38, 6): 'L', (44, 10): 'L', (49, 5): 'L', (49, 6): 'L', (54, 11): 'L', (60, 8): 'L',
           (64, 12): 'L', (68, 7): 'L', (75, 10): 'L', (79, 6): 'L', (41, 12): 'L',
           (13, 5): 'J', (14, 5): 'J', (36, 9): 'J', (37, 9): 'J', (52, 8): 'J', (53, 8): 'J', (72, 6): 'J', (73, 6): 'J'}


def grip_pattern(i, j, ch):
    if ch in 'mno':
        wrap = ((i + j) // 2) % 2
        return {'m': 'l' if wrap else 'm', 'n': 'm' if wrap else 'n', 'o': 'o' if wrap else 'p'}[ch]
    return ch


def sword(fr, guard_c, tip, blade_len=None, grip_len=19, guard_half=13, smear=None):
    """Full greatsword from guard centre towards tip. Returns geometry dict."""
    gx, gy = guard_c
    dx, dy = tip[0] - gx, tip[1] - gy
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    steep = abs(dy) >= abs(dx)
    # blade (pits indexed from guard end -> reverse run index)
    runs_len = int(abs(round(tip[1]) - round(gy + uy * 4))) if steep else int(abs(round(tip[0]) - round(gx + ux * 4)))
    pm = {(runs_len - i, j): c for (i, j), c in PIT_MAP.items()}
    b0 = (gx + ux * 4, gy + uy * 4)
    bar(fr, b0, tip, BLADE_V, point_rows=10, cap0=False, pattern=pits(pm))
    # grip + pommel (behind the guard end)
    g1 = (gx - ux * 3.5, gy - uy * 3.5)
    g2 = (gx - ux * (3.5 + grip_len), gy - uy * (3.5 + grip_len))
    bar(fr, g1, g2, GRIP_T, pattern=grip_pattern)
    pc = (gx - ux * (grip_len + 6.5), gy - uy * (grip_len + 6.5))
    pommel(fr, pc, steep)
    # guard: perpendicular
    px_, py_ = -uy, ux
    q0 = (gx - px_ * guard_half, gy - py_ * guard_half)
    q1 = (gx + px_ * guard_half, gy + py_ * guard_half)
    bar(fr, q0, q1, GUARD_T if not steep else GUARD_T)
    return dict(u=(ux, uy), p=(px_, py_), guard=guard_c, tip=tip, grip_mid=((g1[0] + g2[0]) / 2, (g1[1] + g2[1]) / 2))


POMMEL = """
.kkkkk.
kIJJKLk
kJKKLMk
kKLLMNk
.kkkkk.
"""


def pommel(fr, c, steep=True):
    g = POMMEL if steep else '\n'.join(''.join(r) for r in zip(*POMMEL.strip('\n').split('\n')))
    rows = g.strip('\n').split('\n')
    fr.stamp(g, int(round(c[0])) - len(rows[0]) // 2, int(round(c[1])) - len(rows) // 2)


def transpose(grid):
    rows = grid.strip('\n').split('\n')
    w = max(len(r) for r in rows)
    rows = [r.ljust(w, '.') for r in rows]
    return '\n'.join(''.join(r[i] for r in rows) for i in range(w))


FIST_H = transpose(FIST_V)


def fist(fr, cx, cy, vertical=True, shadow=True):
    g = FIST_V if vertical else FIST_H
    rows = g.strip('\n').split('\n')
    x0, y0 = int(round(cx)) - len(rows[0]) // 2, int(round(cy)) - len(rows) // 2
    if shadow:
        cast_shadow_pts(fr, stamp_mask(g, x0, y0), 1, 2)
    fr.stamp(g, x0, y0)
    return x0, y0


def limb(fr, a, b, width, ramp='plate', cap=True):
    """tube from a to b (128 coords) shaded with lib cyl model"""
    cv = fr.as_canvas()
    ax, ay = a
    bx, by = b
    L = math.hypot(bx - ax, by - ay)
    nx, ny = -(by - ay) / L * width / 2, (bx - ax) / L * width / 2
    m = lib.poly([(ax + nx, ay + ny), (bx + nx, by + ny), (bx - nx, by - ny), (ax - nx, ay - ny)])
    cv.part(m, ramp, ('cyl', a, b, width / 2 + 0.5), th=TH_METAL if ramp == 'plate' else TH_SOFT)
    if ramp == 'chain':
        for y in range(FH):
            for x in range(FW):
                if m[y][x] and fr.px[y][x] not in (None, BLACK) and (x + y) % 2 == 0:
                    fr.px[y][x] = _DARKER.get(fr.px[y][x], fr.px[y][x])
    return m


def cop(fr, c, rx=4.8, ry=4.6):
    cv = fr.as_canvas()
    m = lib.ell(c[0], c[1], rx, ry)
    cv.part(m, 'plate', ('sphere', c[0] - 1, c[1] - 1.5, rx + 0.7, ry + 0.9), th=TH_METAL)
    return m


def compose_body(fr, off=None, skip=(), extra=None, hooks=None):
    """off: dict layer -> (dx, dy). groups: 'upper' applies to belt..head, 'head' adds to head."""
    off = off or {}
    L = layers()
    up = off.get('upper', (0, 0))
    order = ['cape', 'legs', 'flap', 'tassets', 'belt', 'torso', 'buckle', 'gorget', 'armR_back', 'armL_back',
             'paulL', 'paulR', 'armR_front', 'head']
    upper = {'belt', 'torso', 'buckle', 'gorget', 'armR_back', 'armL_back', 'paulL', 'paulR', 'armR_front', 'head'}
    for name in order:
        if hooks and name in hooks:
            hooks[name](fr)
        if name in skip:
            continue
        img = (extra or {}).get(name, L[name])
        dx, dy = off.get(name, (0, 0))
        if name in upper:
            dx += up[0]
            dy += up[1]
        if name in ('paulL', 'paulR', 'head', 'armR_back', 'armL_back', 'armR_front', 'gorget'):
            sx, sy = off.get('shoulders', (0, 0))
            dx += sx
            dy += sy
        if name == 'head':
            hx, hy = off.get('headx', (0, 0))
            dx += hx
            dy += hy
        fr.put(img, dx, dy)
