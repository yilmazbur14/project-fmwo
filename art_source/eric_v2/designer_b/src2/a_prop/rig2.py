"""Eric v2 animation rig (75 px body, 1.25x greatsword, 256x192 frames). SHARED with designer B.

Import from any folder:
    import sys; sys.path.insert(0, r'C:/Users/theyi/AppData/Local/Temp/claude/C--Users-theyi-OneDrive-Documents-new-game-project/a7fc2846-afef-472d-979b-e17143793a0f/scratchpad/eric_redesign/prop')
    import rig2 as R

Frame contract: FW x FH = 256 x 192, Eric centred at x=128, feet on the bottom row (y=191).
    fr = R.Frame()                         # empty 256x192
    R.compose(fr, off={...}, skip=(...), extra={...}, hooks={...})   # body layers, same semantics as v1 rig
    R.idle_weapon(fr)                      # approved idle arm + sword + fist
    R.sword(fr, guard_xy, direction_xy, blade_len=110, grip_len=24)
    R.limb(fr, a, b, width, ramp='plate'|'chain'); R.cop(fr, c, rx, ry); R.fist(fr, x, y, horizontal=False)
    px = fr.rgba()
    R.base_idle() reproduces Assets/Characters/Eric/eric_redesign_v2.png exactly.

Body layer names (96-space, placed at the anchor): cape legs flap tassets belt torso buckle gorget paulL paulR
armR_front head. Offsets in `off` (all (dx, dy) ints):
    'upper'     -> belt torso buckle gorget paulL paulR armR_front head
    'shoulders' -> paulL paulR armR_front gorget head (added on top of upper)
    'headx'     -> head only (added on top)
    any layer name -> that layer only
Variants: R.cape_layer(sway, flare, lift), R.cape_kneel(flare), R.torso_layer(widen, drop),
          R.head_layer(None|'strain'|'tired'), R.split_layer(img, x_split, left)
Map a v1 (128x128) coordinate to v2 frame space: R.M(x, y)  (0.8 scale about feet centre).
"""
import os
import sys
import math

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import scaled as SC            # noqa: E402  (sets the toolkit path)
import lib                     # noqa: E402
from lib import PALC, BLACK, _DARKER, _LIGHTER, hexc  # noqa: E402
import parts                   # noqa: E402
import body_s                  # noqa: E402
import pose as P               # noqa: E402

FW, FH = 256, 192
ANCHOR = (128, 191)
T0 = (0, 0, 0, 0)
for _k, _v in {'d': 'd8f2ff', 'f': '7cc4f0', 'j': '3a78c0'}.items():   # sweat blues
    lib.PAL[_k] = _v
    PALC[_k] = hexc(_v)


def M(x, y):
    """v1 128x128 frame coordinate -> v2 frame coordinate"""
    return (128 + (x - 64) * 0.8, 192 + (y - 128) * 0.8)


class Frame(P.Big):
    def __init__(self):
        super().__init__(FW, FH)

    def put(self, img, dx=0, dy=0):
        """paste a frame-space RGBA image"""
        for y, row in enumerate(img):
            yy = y + dy
            if not 0 <= yy < self.H:
                continue
            for x, p in enumerate(row):
                if p[3]:
                    xx = x + dx
                    if 0 <= xx < self.W:
                        self.px[yy][xx] = p

    def setc(self, x, y, col):
        if 0 <= x < self.W and 0 <= y < self.H:
            self.px[y][x] = col


# ------------------------------------------------------------------ layers + variants
def layers():
    return body_s.layers()


_VCACHE = {}


def trim_spikes(img, passes=2):
    """remove 1px-wide outline spikes (black pixels with at most one opaque 8-neighbour)"""
    h, w = len(img), len(img[0])
    img = [row[:] for row in img]
    for _ in range(passes):
        kill = []
        for y in range(h):
            for x in range(w):
                p = img[y][x]
                if p[3] and p[:3] == (0, 0, 0):
                    n = sum(1 for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                            if (dx or dy) and 0 <= y + dy < h and 0 <= x + dx < w and img[y + dy][x + dx][3])
                    if n <= 1:
                        kill.append((x, y))
        for x, y in kill:
            img[y][x] = T0
    return img


def _cached(key, fn, trim=False):
    if key not in _VCACHE:
        img = body_s._layer(fn)
        _VCACHE[key] = trim_spikes(img) if trim else img
    return _VCACHE[key]


_CAPE = [(48, 40), (30, 39), (17, 45), (11.5, 56), (8.5, 68), (6.5, 80), (5, 90),
         (7, 94.5), (10, 90.5), (13.5, 95.5), (18, 90), (22, 94), (26, 91), (30, 95.5), (34, 92),
         (48, 92),
         (62, 92.5), (66, 95.5), (70, 91), (74.5, 94.5), (79, 89.5), (83, 95), (86.5, 90.5), (90, 93.5), (91.5, 88),
         (89.5, 78), (87.5, 67), (84.5, 56), (79, 45), (66, 39)]
_FOLDS = [((13, 62), (10, 86)), ((19, 70), (18, 89)), ((81, 64), (84, 86)), ((75, 72), (76, 88))]


def _cape_fn(pts, folds):
    def fn(cv):
        m = parts.poly(pts)
        cv.part(m, 'cape', ('sphere', 44, 56, 46, 46, 0.7), th=[9.0, 0.95, 0.80, 0.55, 0.2], bias=0)
        for q0, q1 in folds:
            ln = lib.inter(parts.seg_line(q0, q1), m)
            for y in range(96):
                for x in range(96):
                    if ln[y][x] and cv.px[y][x] != BLACK:
                        cv.px[y][x] = PALC['S']
    return fn


def cape_layer(sway=0.0, flare=0.0, lift=0.0):
    if not (sway or flare or lift):
        return layers()['cape']
    pts = []
    for x, y in _CAPE:
        t = max(0.0, (y - 50) / 45.0)
        pts.append((x + sway * t + (flare * t if x > 48 else -flare * t if x < 48 else 0), y - lift * t))
    folds = []
    for p0, p1 in _FOLDS:
        folds.append(((p0[0] + sway * max(0, (p0[1] - 50) / 45), p0[1]),
                      (p1[0] + sway * max(0, (p1[1] - 50) / 45), p1[1] - lift * max(0, (p1[1] - 50) / 45))))
    return _cached(('cape', sway, flare, lift), _cape_fn(pts, folds), trim=True)


def cape_kneel(flare=4.0):
    pts = []
    for x, y in _CAPE:
        t = max(0.0, (y - 50) / 45.0)
        ny = 40 + (y - 40) * 47.0 / 55.0 if y > 40 else y
        pts.append((x + (flare * t if x > 48 else -flare * t if x < 48 else 0), ny))
    folds = [((12, 60), (8, 84)), ((18, 66), (16, 84)), ((82, 62), (86, 82)), ((76, 68), (78, 84))]
    return _cached(('cape_kneel', flare), _cape_fn(pts, folds), trim=True)


_TORSO = [(48, 33), (39, 34), (31, 37), (26, 42), (22.5, 49), (21, 56), (21.3, 61.5), (23.2, 65.8),
          (27.3, 69.2), (34, 71.4), (41, 72.4), (48, 72.7)]


def torso_layer(widen=0.0, drop=0.0):
    if not (widen or drop):
        return layers()['torso']

    def fn(cv):
        half = []
        for x, y in _TORSO:
            if y > 44:
                k = min(1.0, (y - 44) / 14.0)
                x = x - widen * k
                y = y + drop * k
            half.append((x, y))
        m = parts.poly(lib.sym_pts(half))
        cv.part(m, 'plate', ('sphere', 46.5, 53, 28.5 + widen, 25.5, 0.05), th=lib.TH_METAL)
        parts.torso_details(cv, m)
    return _cached(('torso', widen, drop), fn)


# face variants on the redrawn head (96-space pixel stamps: x, y, chars)
FACE_STRAIN = [
    (41, 36, "kkkk"), (51, 36, "kkkk"),        # eyes squeezed shut under the glaring brows
    (41, 37, "tttt"), (51, 37, "tttt"),
    (45, 44, "eeeeee"), (45, 45, "kkkkkk"),    # bared, gritted teeth
]
FACE_TIRED = [
    (44, 35, "tt"), (50, 35, "tt"),            # brows no longer dipping (worn out)
    (42, 34, "nn"), (52, 34, "nn"),
    (41, 36, "kkbk"), (51, 36, "kbkk"),        # heavy half-closed lids
    (46, 44, "6666"), (46, 45, "k66k"),        # mouth hanging open, panting
]


def head_layer(kind=None):
    base = layers()['head']
    if not kind:
        return base
    key = ('head', kind)
    if key not in _VCACHE:
        img = [row[:] for row in base]
        for x0, y0, s in {'strain': FACE_STRAIN, 'tired': FACE_TIRED}[kind]:
            for i, ch in enumerate(s):
                if img[y0][x0 + i][3]:
                    img[y0][x0 + i] = PALC[ch]
        _VCACHE[key] = img
    return _VCACHE[key]


def split_layer(img, x_split, left=True):
    return [[(p if ((x < x_split) == left) else T0) for x, p in enumerate(row)] for row in img]


ORDER = ['cape', 'legs', 'flap', 'tassets', 'belt', 'torso', 'buckle', 'gorget', 'paulL', 'paulR', 'armR_front', 'head']
UPPER = {'belt', 'torso', 'buckle', 'gorget', 'paulL', 'paulR', 'armR_front', 'head'}
SHOULDERS = {'paulL', 'paulR', 'armR_front', 'gorget', 'head'}


def compose(fr, off=None, skip=(), extra=None, hooks=None):
    off = off or {}
    L = layers()
    up = off.get('upper', (0, 0))
    sh = off.get('shoulders', (0, 0))
    hx = off.get('headx', (0, 0))
    for name in ORDER:
        if hooks and name in hooks:
            hooks[name](fr)
        if name in skip:
            continue
        img = (extra or {}).get(name, L[name])
        dx, dy = off.get(name, (0, 0))
        if name in UPPER:
            dx += up[0]
            dy += up[1]
        if name in SHOULDERS:
            dx += sh[0]
            dy += sh[1]
        if name == 'head':
            dx += hx[0]
            dy += hx[1]
        fr.put96(img, dx, dy)


# ------------------------------------------------------------------ weapon / limbs (re-exports)
sword = P.sword
limb = P.limb
cop = P.cop
fist = P.fist
bar = P.bar
cast_shadow = P.cast_shadow
BLADE_LEN, GRIP_LEN = P.BLADE_LEN, P.GRIP_LEN

IDLE_UP = (-1.0, -5.0)
IDLE_FIST = (92, 163)


def _idle_parts():
    if 'idle_arm' not in _VCACHE:
        a = Frame()
        P.limb(a, (105, 162), (95, 163), 9)
        P.cop(a, (105, 162), 4.3, 4.1)
        _VCACHE['idle_arm'] = a.rgba()
        s = Frame()
        L = math.hypot(*IDLE_UP)
        u = (IDLE_UP[0] / L, IDLE_UP[1] / L)
        guard = (IDLE_FIST[0] + u[0] * 10, IDLE_FIST[1] + u[1] * 10)
        P.sword(s, guard, IDLE_UP)
        _VCACHE['idle_sword'] = s.rgba()
    return _VCACHE['idle_arm'], _VCACHE['idle_sword']


def idle_weapon(fr, dx=0, dy=0, fist_dx=None, fist_dy=None, arm_dx=None, arm_dy=None):
    """approved idle arm + sword + fist, each movable (defaults follow dx, dy)"""
    arm, sw = _idle_parts()
    fr.put(arm, dx if arm_dx is None else arm_dx, dy if arm_dy is None else arm_dy)
    fr.put(sw, dx, dy)
    P.fist(fr, IDLE_FIST[0] + (dx if fist_dx is None else fist_dx), IDLE_FIST[1] + (dy if fist_dy is None else fist_dy))


def base_idle():
    fr = Frame()
    compose(fr)
    idle_weapon(fr)
    return fr
