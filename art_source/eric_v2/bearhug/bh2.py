"""Eric bear hug v2 helpers: 256x192 frames on designer A's rig2 (75 px body, 1.25x sword)."""
import os
import sys
import math
import random

HERE = os.path.dirname(os.path.abspath(__file__))
# designer A's shared v2 rig: the scratch working copy while it exists, otherwise the archived copy next to this
# folder (art_source/eric_v2/prop). Override with BH2_RIG=<folder>.
LIVE = 'C:/Users/theyi/AppData/Local/Temp/claude/C--Users-theyi-OneDrive-Documents-new-game-project/a7fc2846-afef-472d-979b-e17143793a0f/scratchpad/eric_redesign/prop'
LOCAL = os.path.join(os.path.dirname(HERE), 'prop')
RIG_DIR = os.environ.get('BH2_RIG') or (LIVE if os.path.isdir(LIVE) else LOCAL)
sys.path.insert(0, HERE)
sys.path.insert(0, RIG_DIR)
import rig2 as R
import fx2 as FX
import lib
import pose as PZ
from lib import PALC, BLACK, _DARKER, _LIGHTER, hexc, TH_METAL, TH_SOFT
import scaled as SC

FW, FH = R.FW, R.FH

for k, v in {'Z': 'fff7d6'}.items():            # aura hot core
    lib.PAL[k] = v
    PALC[k] = hexc(v)


def M(x, y):
    return R.M(x, y)


def mi(p):
    x, y = R.M(*p)
    return (round(x, 1), round(y, 1))


def s8(v):
    """scale a v1 pixel offset by 0.8 (rounded half away from zero)"""
    return int(math.copysign(math.floor(abs(v) * 0.8 + 0.5), v))


def off8(p):
    return (s8(p[0]), s8(p[1]))


# ---------------------------------------------------------------- body
def body(fr, upper=(0, 0), shoulders=(0, 0), headx=(0, 0), cape=None, torso=None, skip=(), under_pauldrons=None,
         legs=None, tassets=None, head=None):
    L = R.layers()
    extra = {}
    if cape is not None:
        extra['cape'] = R.cape_layer(*cape)
    if torso is not None:
        extra['torso'] = R.torso_layer(*torso)
    if head is not None:
        extra['head'] = head
    hooks = {}
    if under_pauldrons:
        hooks['paulL'] = under_pauldrons
    sk = set(skip)
    if legs is not None:
        sk.add('legs')
        (ldx, ldy), (rdx, rdy) = legs

        def put_legs(f, _l=L['legs']):
            f.put96(R.split_layer(_l, 48, True), ldx, ldy)
            f.put96(R.split_layer(_l, 48, False), rdx, rdy)
        hooks['flap'] = put_legs
    if tassets is not None:
        sk.add('tassets')
        (ldx, ldy), (rdx, rdy) = tassets

        def put_tass(f, _l=L['tassets']):
            f.put96(R.split_layer(_l, 48, True), ldx, ldy)
            f.put96(R.split_layer(_l, 48, False), rdx, rdy)
        hooks['belt'] = put_tass
    R.compose(fr, {'upper': upper, 'shoulders': shoulders, 'headx': headx}, skip=tuple(sk), extra=extra, hooks=hooks)


# face variants on the v2 head (96-space stamps: x, y, chars). Eyes: left x41-43, right x52-54, row 36; lids row 35;
# brows rows 34-35; mouth line row 44 x45-50 under the moustache.
FACES = {
    'roar': [
        (40, 34, "5555"), (52, 34, "5555"),
        (44, 43, "kkkkkk"),
        (43, 44, "keeeeeek"), (43, 45, "k6YYYY6k"), (44, 46, "k6YY6k"), (45, 47, "keek"), (45, 48, "kkkk"),
    ],
    'strain': [
        (41, 35, "kkt"), (52, 35, "tkk"),
        (41, 36, "tkk"), (52, 36, "kkt"),
        (41, 37, "kkt"), (52, 37, "tkk"),
        (44, 44, "keeeeeek"), (44, 45, "kkkkkkkk"), (45, 46, "keeeek"), (46, 47, "kkkk"),
    ],
    'grin': [
        (41, 37, "kkk"), (52, 37, "kkk"),
        (43, 43, "k"), (52, 43, "k"),
        (43, 44, "keeeeeek"), (44, 45, "kkkkkk"),
    ],
    'crush': [
        (41, 35, "kkt"), (52, 35, "tkk"),
        (41, 36, "tkk"), (52, 36, "kkt"),
        (41, 37, "kkt"), (52, 37, "tkk"),
        (49, 30, "y.y"), (49, 31, ".X."), (49, 32, "y.y"),
        (42, 43, "k"), (53, 43, "k"),
        (43, 44, "keeeeeeek"), (43, 45, "kkkkkkkkk"), (44, 46, "keeeeek"), (45, 47, "kkkkk"),
    ],
    'shock': [
        (40, 33, "ttttt"), (51, 33, "ttttt"),
        (40, 34, "ttttt"), (51, 34, "ttttt"),
        (41, 32, "555"), (52, 32, "555"),
        (41, 34, "kkk"), (52, 34, "kkk"),
        (40, 35, "keeek"), (51, 35, "keeek"),
        (40, 36, "kebek"), (51, 36, "kebek"),
        (40, 37, "keeek"), (51, 37, "keeek"),
        (41, 38, "kkk"), (52, 38, "kkk"),
        (46, 44, "k66k"), (46, 45, "k66k"), (47, 46, "kk"),
    ],
    'wobble': [
        (40, 33, "ttttt"), (51, 33, "ttttt"),
        (40, 34, "ttttt"), (51, 34, "ttttt"),
        (41, 33, "555"), (52, 33, "555"),
        (41, 34, "kkk"), (52, 34, "kkk"),
        (40, 35, "keeek"), (51, 35, "keeek"),
        (40, 36, "kbeek"), (51, 36, "kbeek"),
        (40, 37, "keeek"), (51, 37, "keeek"),
        (41, 38, "kkk"), (52, 38, "kkk"),
        (44, 44, "6k66k66k"), (44, 45, "k6kk6kk6"),
    ],
    'exhale': [
        (41, 35, "ttt"), (52, 35, "ttt"),
        (41, 36, "ktk"), (52, 36, "ktk"),
        (41, 37, "tkt"), (52, 37, "tkt"),
        (46, 44, "k66k"), (46, 45, "k66k"), (47, 46, "kk"),
    ],
    'look': [
        (41, 36, "bbe"), (52, 36, "bbe"),
    ],
}

_HCACHE = {}


def head_variant(kind):
    if kind in _HCACHE:
        return _HCACHE[kind]
    img = [row[:] for row in R.layers()['head']]
    for x0, y0, s in FACES[kind]:
        for i, ch in enumerate(s):
            if ch != '.' and img[y0][x0 + i][3]:
                img[y0][x0 + i] = PALC[ch]
    _HCACHE[kind] = img
    return img


# ---------------------------------------------------------------- arms and hands
def upper_arm(fr, s, e, w=9):
    R.limb(fr, s, e, w, ramp='chain')


def fore_arm(fr, e, w_, w=9, cop=True):
    R.limb(fr, e, w_, w, ramp='plate')
    if cop:
        R.cop(fr, e, 4.6, 4.4)


OPEN_S = """
...kk.kk.kk.....
..kIJkIJkJKk....
..kIJkIJkJKk.kk.
..kIJkJJkJKkkJKk
k.kJJkJKkKKkJKk.
kkkJJJJKKKKkKk..
kIkJJJJKKKKLk...
kIJkJJKKKKLLk...
.kJJJJKKKLLMk...
..kJJKKKLLMk....
...kKKKLLMk.....
....kkkkkk......
"""


def rows_of(grid):
    rows = grid.strip('\n').split('\n')
    w = max(len(r) for r in rows)
    return [r.ljust(w, '.') for r in rows]


def join(rows):
    return '\n'.join(rows)


def T_(grid):
    rows = rows_of(grid)
    return join(''.join(r[i] for r in rows) for i in range(len(rows[0])))


def FXg(grid):
    return join(r[::-1] for r in rows_of(grid))


def FYg(grid):
    return join(rows_of(grid)[::-1])


def reshade(grid, ramp='IJKLMN'):
    rows = [list(r) for r in rows_of(grid)]
    H, W = len(rows), len(rows[0])
    metal = set('IJKLMN')

    def solid(x, y):
        return 0 <= x < W and 0 <= y < H and rows[y][x] in metal
    out = [r[:] for r in rows]
    for y in range(H):
        for x in range(W):
            if rows[y][x] not in metal:
                continue
            t = (x / max(1, W - 1)) * 0.55 + (y / max(1, H - 1)) * 0.75
            base = 1 if t < 0.45 else 2 if t < 0.8 else 3
            if not solid(x - 1, y) or not solid(x, y - 1):
                base -= 1
            if not solid(x + 1, y) or not solid(x, y + 1):
                base += 1
            out[y][x] = ramp[max(0, min(len(ramp) - 1, base))]
    return join(''.join(r) for r in out)


def hand(kind):
    g = OPEN_S
    return reshade({'up': g, 'up_l': FXg(g), 'out_r': FYg(FXg(T_(g))), 'out_l': FYg(T_(g)),
                    'down': FYg(g), 'down_l': FYg(FXg(g))}[kind])


def stamp(fr, grid, cx, cy, shadow=True):
    rows = rows_of(grid)
    h, w = len(rows), len(rows[0])
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    pts = [(x0 + c, y0 + r, ch) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch not in '. ']
    if shadow:
        R.cast_shadow(fr, [(x, y) for x, y, _ in pts], 1, 2)
    for x, y, ch in pts:
        fr.set(x, y, ch)
    return pts


CLASP = """
.kkkkk.............kkkkk.
kIJJJJkkkkkkkkkkkkkkJJKKk
kJJKKKkIJJJKkkJKKLkKKKLLk
kJKKLLkkkkkkkkkkkkkkKLLMk
.kkkkk.............kkkkk.
"""


def clasp(width):
    r = rows_of(CLASP)
    W = len(r[0])
    d = width - W
    out = []
    for row in r:
        left, centre, right = row[:6], row[6:W - 6], row[W - 6:]
        h = len(centre) // 2
        if d >= 0:
            c = centre[:h] + centre[h] * d + centre[h:]
        else:
            k = -d
            c = centre[:h - k // 2 - k % 2] + centre[h + k // 2:]
        out.append(left + c + right)
    return join(out)


# ---------------------------------------------------------------- planted greatsword (beside him, viewer-left)
SWX = 63            # blade centre column
GUARD_Y = 130       # crossguard centre row
GROUND_Y = 186      # row where the blade enters the ground


def sword_upright(fr, lift=0):
    tmp = R.Frame()
    R.sword(tmp, (SWX, GUARD_Y - lift), (0, 1))
    for y in range(FH):
        if y > GROUND_Y:
            break
        for x in range(FW):
            p = tmp.px[y][x]
            if p is not None:
                fr.px[y][x] = p


MOUND = [
    "..kk.k" + "k" * 22 + "k.kk..",
    ".knkkm" + "n" * 22 + "mkknk.",
    "kmnnmn" + "o" * 22 + "nmnnmk",
    ".kkoop" + "p" * 22 + "pookk.",
    "...kkk" + "k" * 22 + "kkk...",
]


def ground_lip(fr, cracks=True):
    w = len(MOUND[0])
    x0 = SWX - w // 2
    for r, row in enumerate(MOUND):
        for c, ch in enumerate(row):
            if ch not in '. ':
                fr.set(x0 + c, GROUND_Y - 1 + r, ch)
    if cracks:
        g = GROUND_Y
        FX.crack(fr, [(x0 - 1, g + 2), (x0 - 5, g + 1), (x0 - 8, g + 3), (x0 - 11, g + 2)])
        FX.crack(fr, [(x0 + w, g + 2), (x0 + w + 4, g + 4), (x0 + w + 7, g + 3)])
        FX.crack(fr, [(SWX - 4, g + 4), (SWX - 7, g + 5)])
        FX.crack(fr, [(SWX + 6, g + 4), (SWX + 9, g + 5)])


def planted_sword(fr, lift=0, cracks=True):
    sword_upright(fr, lift=lift)
    ground_lip(fr, cracks=cracks)


# ---------------------------------------------------------------- aura
def dist_field(mask):
    INF = 999.0
    d = [[0.0 if mask[y][x] else INF for x in range(FW)] for y in range(FH)]
    a, b = 1.0, 1.4142
    for y in range(FH):
        for x in range(FW):
            v = d[y][x]
            if v == 0:
                continue
            if x > 0: v = min(v, d[y][x - 1] + a)
            if y > 0:
                v = min(v, d[y - 1][x] + a)
                if x > 0: v = min(v, d[y - 1][x - 1] + b)
                if x < FW - 1: v = min(v, d[y - 1][x + 1] + b)
            d[y][x] = v
    for y in range(FH - 1, -1, -1):
        for x in range(FW - 1, -1, -1):
            v = d[y][x]
            if v == 0:
                continue
            if x < FW - 1: v = min(v, d[y][x + 1] + a)
            if y < FH - 1:
                v = min(v, d[y + 1][x] + a)
                if x < FW - 1: v = min(v, d[y + 1][x + 1] + b)
                if x > 0: v = min(v, d[y + 1][x - 1] + b)
            d[y][x] = v
    return d


def aura(fr, phase=0, thick=4.0, tongues=10.0, bands='ZgGh', floor=None):
    m = [[p is not None for p in row] for row in fr.px]
    d = dist_field(m)
    col_top = [FH] * FW
    for x in range(FW):
        for y in range(FH):
            if m[y][x]:
                col_top[x] = y
                break
    floor = GROUND_Y - 6 if floor is None else floor
    out = []
    for y in range(FH):
        for x in range(FW):
            if m[y][x]:
                continue
            dd = d[y][x]
            if dd > thick + tongues + 2:
                continue
            above = 1.0 if y < col_top[x] else 0.35
            X = x * 1.25                       # keep the v1 tongue spacing relative to the body
            wave = 0.5 + 0.5 * math.sin((X * 0.42) + phase * 2.1) * math.cos((X * 0.17) - phase * 1.3)
            r = thick + tongues * above * wave ** 2
            edge = min(x, FW - 1 - x, y)
            r = min(r, max(0.0, edge * 0.8 - 0.5))
            if y > floor:
                r = 0.0
            if dd <= r:
                t = dd / max(r, 1e-6)
                out.append((x, y, bands[0] if t < 0.3 else bands[1] if t < 0.62 else bands[2] if t < 0.88 else bands[3]))
    return out


def spark(fr, x, y, size=1, ch='W', edge='g'):
    fr.set(x, y, ch)
    for k in range(1, size + 1):
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            fr.set(x + dx, y + dy, ch if k < size else edge)


def line(fr, p0, p1, ch):
    x0, y0 = p0
    x1, y1 = p1
    n = int(max(abs(x1 - x0), abs(y1 - y0), 1))
    for i in range(n + 1):
        fr.set(int(round(x0 + (x1 - x0) * i / n)), int(round(y0 + (y1 - y0) * i / n)), ch)


def energy_streaks(fr, phase, xs, top, bottom):
    for i, x in enumerate(xs):
        L = 7 + ((i * 7 + phase * 5) % 8)
        y0 = top + ((i * 13 + phase * 17) % (bottom - top - L))
        for y in range(y0, y0 + L):
            if fr.get(x, y) is None:
                fr.set(x, y, 'Z' if y < y0 + 2 else ('g' if y < y0 + L - 2 else 'G'))


PEBBLE = """
.kk.
kKLk
kLMk
.kk.
"""
PEBBLE_S = """
kk
kk
"""
CLOD = FX.CLOD


# ---------------------------------------------------------------- flying cape (v1 polygon mapped through M)
def cape_fly(fr, rise=0.0, spread=0.0, flutter=0, sway=0.0):
    cv = fr.canvas()
    r, sp = rise, spread
    half = [(64, 70), (52, 64 - r * 0.3), (40, 58 - r * 0.6), (28, 52 - r * 0.85), (17, 48 - r), (9 - sp * 0.5, 49 - r),
            (4 - sp, 54 - r * 0.9 + flutter), (8 - sp * 0.6, 59 - r * 0.8), (2 - sp, 65 - r * 0.6 - flutter),
            (9 - sp * 0.5, 70 - r * 0.5), (4 - sp, 78 - r * 0.3 + flutter), (13 - sp * 0.3, 81 - r * 0.2),
            (9 - sp * 0.3, 89 - flutter), (19, 90), (16, 98 + flutter), (26, 96), (29, 104), (40, 99), (48, 102)]
    pts = [(x + sway * (1 - y / 128), y) for x, y in half]
    right = [(127 - x + sway * (1 - y / 128) * 2, y) for x, y in reversed(half)]
    poly = [M(*p) for p in pts + [(64, 102)] + right]
    m = lib.poly(poly)
    c = M(60, 64)
    cv.part(m, 'cape', ('sphere', c[0], c[1], 70 * 0.8, 48 * 0.8, 0.4), th=[9.0, 0.95, 0.80, 0.55, 0.2])
    for p0, p1 in [((40, 76), (14, 60 - r)), ((44, 86), (16, 76)), ((87, 76), (113, 60 - r)), ((83, 86), (111, 76))]:
        q0, q1 = M(*p0), M(*p1)
        n = 30
        for i in range(n + 1):
            x = int(round(q0[0] + (q1[0] - q0[0]) * i / n))
            y = int(round(q0[1] + (q1[1] - q0[1]) * i / n))
            if 0 <= x < FW and 0 <= y < FH and m[y][x] and fr.px[y][x] not in (None, BLACK):
                fr.set(x, y, 'S')
    return m


def speed_burst(fr, c, r0, r1, n=28, seed=1, ch='W', ch2='B'):
    rnd = random.Random(seed)
    cx, cy = c
    for i in range(n):
        a = (i / n) * 2 * math.pi + rnd.uniform(-0.08, 0.08)
        ra = r0 + rnd.uniform(0, 8)
        rb = min(r1, ra + rnd.uniform(6, 18))
        steps = int((rb - ra) * 1.5) + 1
        for k in range(steps):
            rr = ra + (rb - ra) * k / steps
            x = int(round(cx + math.cos(a) * rr))
            y = int(round(cy + math.sin(a) * rr * 0.9))
            if 0 <= x < FW and 0 <= y < FH and y <= 190 and fr.px[y][x] is None:
                fr.set(x, y, ch if k > steps * 0.35 else ch2)


def ghost(fr, src, dy, ch):
    for y in range(FH):
        yy = y + dy
        if not 0 <= yy < FH or yy % 2 == 0:
            continue
        for x in range(FW):
            if src.px[y][x] is not None and fr.get(x, yy) is None:
                fr.set(x, yy, ch)


def emphasis(fr, c, r0, r1, angs, ch='W'):
    for ang in angs:
        a = math.radians(ang)
        for k in range(int(r1 - r0) + 1):
            x = int(round(c[0] + math.cos(a) * (r0 + k)))
            y = int(round(c[1] + math.sin(a) * (r0 + k)))
            if fr.get(x, y) is None:
                fr.set(x, y, ch)


def pop_star(fr, x, y, big=True):
    g = ["..k..", ".kZk.", "kZZZk", ".kZk.", "..k.."] if big else [".k.", "kZk", ".k."]
    for r, row in enumerate(g):
        for q, ch in enumerate(row):
            if ch != '.':
                fr.set(x + q - len(row) // 2, y + r - len(g) // 2, ch)


def stars(fr, c, phase):
    cx, cy = c
    STAR = [".k.", "kGk", ".k."]
    for i in range(3):
        a = math.radians(phase * 50 + i * 120)
        x, y = int(round(cx + math.cos(a) * 7)), int(round(cy + math.sin(a) * 2))
        for r, row in enumerate(STAR):
            for q, ch in enumerate(row):
                if ch != '.':
                    fr.set(x + q - 1, y + r - 1, ch)


# ---------------------------------------------------------------- compositing + clean-up
def layered(back, body_fr, front=None):
    fr = R.Frame()
    back(fr)
    for y in range(FH):
        for x in range(FW):
            p = body_fr.px[y][x]
            if p is not None:
                fr.px[y][x] = p
    if front:
        front(fr)
    return fr


def seal(fr):
    fx_ok = set(PALC[c] for c in 'WABCZgGhdfj') | {BLACK}
    px = fr.px
    for y in range(FH):
        for x in range(FW):
            if px[y][x] is None:
                nb = [px[yy][xx] for xx, yy in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)) if 0 <= xx < FW and 0 <= yy < FH]
                if len(nb) == 4 and all(p is not None for p in nb):
                    px[y][x] = BLACK
    fix = []
    for y in range(FH):
        for x in range(FW):
            p = px[y][x]
            if p is None or p in fx_ok:
                continue
            for xx, yy in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= xx < FW and 0 <= yy < FH and px[yy][xx] is None:
                    fix.append((x, y))
                    break
    for x, y in fix:
        px[y][x] = BLACK
    return fr
