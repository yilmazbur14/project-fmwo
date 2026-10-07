"""FX v2 (2026-09-29): shared helpers for the redrawn elemental FX of Liam's attacks 1-2.

Imports the approved rig modules (le_rig, le_water, le_ice, le_air, le_earth) READ-ONLY, for their palette keys and
geometry helpers only; nothing here writes a file. Canvases are numpy '<U1' arrays of palette keys ('.' transparent),
exactly the rig's convention, so every pixel is a known, approved colour.
"""
import math
import os
import sys

sys.dont_write_bytecode = True

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LE = os.path.dirname(HERE)                               # art_source/liam_elements
ART = os.path.dirname(LE)                                # art_source
ROOT = os.path.dirname(ART)                              # the project
APPROVAL = os.path.join(LE, 'approval')                  # the shipped sheets (sha256-identical to Assets)
APPROVAL_FULL = os.path.join(APPROVAL, 'full')
for p in (LE, ART):
    if p not in sys.path:
        sys.path.insert(0, p)

import le_rig as R          # noqa: E402  (read only)
import le_water  # noqa: E402,F401  (registers the water ramp: 0 % = + ~)
import le_ice    # noqa: E402,F401  (registers the floor keys: < > ^ " ( ) [ ] { })
import le_air    # noqa: E402,F401
import le_earth  # noqa: E402,F401

PAL = R.PAL
SCALE = 3

# Every colour a v2 sheet may use, per piece: its own shipped colours plus, where noted, a sibling element's approved
# colours. Nothing outside the approved sheets' colour sets is used (checked by fx_build before anything is written).
ALLOWED = {
    'water': set('0%=+~lWb'),                       # the wave ramp, his spray blue (b)
    'floor': set('<>^"()[]{}'),                     # flood + ice floor keys (semi-transparent)
    'air': set('Wlwv~b'),                           # the gust/breath whites + the frost aqua and spray blue
    'air_debris': set('Wlwv~btTyY'),                # + the slate chips of the pillar/ridges for debris in the flow
    'earth': set('tTyYZ8Wwv(]'),                    # the ridge's slate, crevice, earth green, dust and ice plates
    'dust': set('wvTtyY'),                          # pillar dust + slate pebbles
}


# ------------------------------------------------------------------ canvases
def blank(w, h):
    return np.full((h, w), '.', dtype='<U1')


def rgba(cv):
    return R.to_rgba(cv, PAL)


def inverse_palette():
    inv = {}
    for k, v in PAL.items():
        if len(k) == 1:
            inv.setdefault(tuple(int(c) for c in v), k)
    return inv


def from_rgba(a):
    """An RGBA array back to a key canvas (every colour must be a palette colour)."""
    inv = inverse_palette()
    h, w = a.shape[:2]
    cv = blank(w, h)
    op = a[..., 3] > 0
    for y, x in zip(*np.nonzero(op)):
        cv[y, x] = inv[tuple(int(c) for c in a[y, x])]
    return cv


def load_strip(path, fw):
    """A shipped strip as a list of key canvases."""
    from PIL import Image
    a = np.array(Image.open(path).convert('RGBA'))
    n = a.shape[1] // fw
    return [from_rgba(a[:, i * fw:(i + 1) * fw]) for i in range(n)]


def shipped(name, fw):
    return load_strip(os.path.join(APPROVAL, name + '.png'), fw)


# ------------------------------------------------------------------ periodic value noise
def _smooth(t):
    return t * t * (3 - 2 * t)


def vnoise(shape, cells, seed, periodic=None):
    """Value noise on a grid of `shape` (any number of axes) with `cells` lattice cells along each axis. A periodic
    axis wraps exactly (its last sample runs on into its first), so tiles stay seamless and loops loop."""
    shape = tuple(shape)
    cells = tuple(cells)
    nd = len(shape)
    periodic = tuple(periodic) if periodic is not None else (True,) * nd
    rnd = np.random.RandomState(seed)
    lat = rnd.rand(*[c if p else c + 1 for c, p in zip(cells, periodic)])
    grids = np.meshgrid(*[np.arange(n) for n in shape], indexing='ij')
    idx0, idx1, ts = [], [], []
    for ax in range(nd):
        f = grids[ax] * cells[ax] / float(shape[ax])
        i0 = np.floor(f).astype(int)
        t = _smooth(f - i0)
        if periodic[ax]:
            i1 = (i0 + 1) % cells[ax]
            i0 = i0 % cells[ax]
        else:
            i1 = np.minimum(i0 + 1, cells[ax])
        idx0.append(i0)
        idx1.append(i1)
        ts.append(t)
    out = np.zeros(shape)
    for corner in range(1 << nd):
        w = np.ones(shape)
        ix = []
        for ax in range(nd):
            if corner >> ax & 1:
                w = w * ts[ax]
                ix.append(idx1[ax])
            else:
                w = w * (1 - ts[ax])
                ix.append(idx0[ax])
        out += w * lat[tuple(ix)]
    return out


def fbm(shape, cells, seed, octaves=2, periodic=None):
    total, amp, norm = 0.0, 1.0, 0.0
    for o in range(octaves):
        c = tuple(max(1, int(round(ci * (2 ** o)))) for ci in cells)
        total = total + amp * vnoise(shape, c, seed + 17 * o, periodic)
        norm += amp
        amp *= 0.5
    return total / norm


BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0


def dquant(v, ramp, strength=0.9, ox=0, oy=0):
    """Quantise 0..1 to a ramp with a 4x4 ordered dither (the rig's pixel-art gradients)."""
    h, w = v.shape
    t = np.tile(BAYER4, (h // 4 + 2, w // 4 + 2))[oy % 4:oy % 4 + h, ox % 4:ox % 4 + w]
    f = v * (len(ramp) - 1)
    i = np.clip(np.floor(f + (t - 0.5) * strength + 0.5).astype(int), 0, len(ramp) - 1)
    return np.array(list(ramp))[i]


# ------------------------------------------------------------------ plotting
def plot(cv, x, y, ch, wrap_x=False, wrap_y=False, under=None):
    """One texel at (x, y) (rounded). wrap_x/y wrap it round a tile; `under` limits it to texels holding those keys."""
    h, w = cv.shape
    xi, yi = int(math.floor(x + 0.5)), int(math.floor(y + 0.5))
    if wrap_x:
        xi %= w
    if wrap_y:
        yi %= h
    if 0 <= xi < w and 0 <= yi < h:
        if under is None or cv[yi, xi] in under:
            cv[yi, xi] = ch
            return True
    return False


def line(cv, x0, y0, x1, y1, ch, wrap_x=False, wrap_y=False, chars=None):
    """A 1-texel line; `chars` (a function of 0..1 along it) picks each texel's key instead of `ch`."""
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(n + 1):
        u = i / max(1, n)
        plot(cv, x0 + (x1 - x0) * u, y0 + (y1 - y0) * u, chars(u) if chars else ch, wrap_x, wrap_y)


def polyline(cv, pts, ch, wrap_x=False, wrap_y=False, chars=None):
    total = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])) or 1.0
    run = 0.0
    for a, b in zip(pts, pts[1:]):
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        n = int(seg) + 1
        for i in range(n + 1):
            u = i / max(1, n)
            along = (run + seg * u) / total
            plot(cv, a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, chars(along) if chars else ch,
                 wrap_x, wrap_y)
        run += seg


def arc(cv, cx, cy, rx, ry, a0, a1, ch, wrap_x=False, wrap_y=False, chars=None, gaps=None):
    """An elliptical arc from angle a0 to a1 (degrees, 0 = +x, 90 = +y, i.e. down on screen)."""
    n = max(8, int(abs(a1 - a0) / 360.0 * 2 * math.pi * max(rx, ry) * 1.6) + 2)
    for i in range(n + 1):
        u = i / n
        if gaps and gaps(u):
            continue
        a = math.radians(a0 + (a1 - a0) * u)
        plot(cv, cx + rx * math.cos(a), cy + ry * math.sin(a), chars(u) if chars else ch, wrap_x, wrap_y)


def spiral(cv, cx, cy, r, turns, rot, ch_in, ch_out, squash=1.0, wrap_x=False, wrap_y=False, direction=1):
    """A curling eddy: a spiral from its centre out to radius r."""
    n = max(20, int(turns * 2 * math.pi * r * 1.5))
    for i in range(n):
        u = i / (n - 1)
        a = rot + direction * 2 * math.pi * turns * u
        rr = 0.6 + r * u
        plot(cv, cx + rr * math.cos(a), cy + rr * squash * math.sin(a), ch_in if u < 0.5 else ch_out, wrap_x, wrap_y)


def ellipse_mask(w, h, cx, cy, rx, ry):
    X, Y = R.centres(w, h)
    return ((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 <= 1


def puff(cv, cx, cy, r, ramp=('w', 'v', 'T'), squash=0.72, holes=None):
    """A lit dust/mist ball (the pillar dust's lambert puff): ramp = (lit, mid, shade)."""
    h, w = cv.shape
    X, Y = R.centres(w, h)
    m = ((X - cx) / r) ** 2 + ((Y - cy) / (r * squash)) ** 2 <= 1
    if holes is not None:
        m &= holes
    v = R.lambert(R.sphere_normal(X, Y, cx, cy, r, r * squash))
    ch = np.where(v > 0.72, ramp[0], np.where(v > 0.38, ramp[1], ramp[2]))
    cv[m] = ch[m]
    return m


def chip(cv, x, y, size=2, keys=('t', 'T', 'y', 'Y')):
    """A rock chip: a lit 1x1, 2x2 or 3x2 pebble."""
    x, y = int(round(x)), int(round(y))
    if size <= 1:
        plot(cv, x, y, keys[1])
        return
    if size == 2:
        pts = ((0, 0, keys[0]), (1, 0, keys[1]), (0, 1, keys[2]), (1, 1, keys[3]))
    else:
        pts = ((0, 0, keys[0]), (1, 0, keys[0]), (2, 0, keys[1]), (0, 1, keys[2]), (1, 1, keys[2]), (2, 1, keys[3]))
    for dx, dy, ch in pts:
        plot(cv, x + dx, y + dy, ch)


def stamp(cv, x0, y0, rows, wrap_x=False, wrap_y=False):
    """An ASCII stamp; ' ' and '.' transparent."""
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch not in ' .':
                plot(cv, x0 + i, y0 + j, ch, wrap_x, wrap_y)


def spark(cv, x, y, arm=1, core='W', edge='l', wrap_x=False, wrap_y=False):
    """A 4-point glint."""
    plot(cv, x, y, core, wrap_x, wrap_y)
    for k in range(1, arm + 1):
        ch = core if k < arm else edge
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            plot(cv, x + dx, y + dy, ch, wrap_x, wrap_y)


def colours(cv):
    return set(np.unique(cv)) - {'.'}
