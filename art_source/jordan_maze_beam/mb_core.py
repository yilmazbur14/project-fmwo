"""The maze beam's toolkit: palettes, periodic noise, drawing on index grids, and PNG assembly.

Every sheet is built as numpy grids of palette indices (0 = transparent), one grid per frame, then
turned into RGBA with no semi-alpha. Texel scale in game: 3 world px, which the god fight's 2/3 view
shows as 2 screen px.

Nothing here writes a file: the build script (mb_build.py) does, and only into approval/.
"""
import math

import numpy as np
from PIL import Image


def hexrgb(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# ----------------------------------------------------------------------------------------------- palettes
# Take A, HELLBOLT: the undead puppets' crimson ramp (measured from Assets/Characters/Jordan/Puppets/
# greyson/*.png: #36091C #661127 #9F1C2E #D2403A, and the void black #17111D) carried up past the
# puppets' own highlight into a searing white core, hue-shifting warm as it brightens.
PAL_A = {
    'k': '#000000',   # black lightning
    'v': '#17111D',   # puppet void black
    'm': '#36091C',   # puppet maroon (h334)
    'd': '#661127',   # puppet deep crimson (h344)
    'c': '#9F1C2E',   # puppet crimson (h351)
    'r': '#D2403A',   # puppet red highlight (h2)
    's': '#FF4A57',   # NEW red-hot (h356): past the puppets' highlight, shifting to pink, not to fire
    'p': '#FF9EA0',   # NEW pale red-hot (h359)
    'h': '#FFE4E4',   # NEW pink-white
    'w': '#FFFFFF',   # white-hot core
}
# The intensity ramp of take A, dark to hot.
RAMP_A = ['m', 'd', 'c', 'r', 's', 'p', 'h', 'w']

# Take B, SOUL TORRENT: the puppets' own bone and ash ramp (cool purple shadows #17111D #2C2434
# #4A4356 #6E6A80 #9893A5 warming into bone #CFC6B2 #F1EAD4) as ghost fire, black smoke, and their
# red for the eyes. Every colour but white is measured off the puppet sheets.
PAL_B = {
    'k': '#000000',   # smoke black, eye holes
    'v': '#17111D',   # puppet void black (h270)
    'u': '#2C2434',   # puppet dusk (h270)
    'a': '#4A4356',   # puppet ash (h262)
    'g': '#6E6A80',   # puppet grey (h250)
    'l': '#9893A5',   # puppet pale grey (h256)
    'b': '#CFC6B2',   # puppet bone (h41)
    'e': '#F1EAD4',   # puppet bone light (h45)
    'w': '#FFFFFF',   # white
    'r': '#D2403A',   # puppet red: eye glints
    'c': '#9F1C2E',   # puppet crimson: eye glow edge
    'd': '#661127',   # puppet deep crimson
}
RAMP_B = ['u', 'a', 'g', 'l', 'b', 'e', 'w']

# Additive glow sheets: opaque dark tones added over the scene (the house glow sheets are opaque,
# 3 tones, e.g. jordan_god_*_aura.png). Three steps each, faint to strong.
GLOW_A = {'1': '#1E050E', '2': '#3A0A19', '3': '#5E1126'}
GLOW_B = {'1': '#15121A', '2': '#2A2531', '3': '#46404F'}


class Pal:
    """A palette: letter keys to RGB, and the index each letter has in the frame grids."""

    def __init__(self, table):
        self.keys = list(table.keys())
        self.rgb = [None] + [hexrgb(table[k]) for k in self.keys]
        self.idx = {k: i + 1 for i, k in enumerate(self.keys)}

    def __getitem__(self, key):
        return self.idx[key]

    def image(self, grid):
        h, w = grid.shape
        out = np.zeros((h, w, 4), np.uint8)
        for i, c in enumerate(self.rgb):
            if c is None:
                continue
            m = grid == i
            out[m, 0], out[m, 1], out[m, 2], out[m, 3] = c[0], c[1], c[2], 255
        return Image.fromarray(out, 'RGBA')

    def hexes(self):
        return ['#%02X%02X%02X' % c for c in self.rgb[1:]]


# ----------------------------------------------------------------------------------------------- noise

def value_noise_periodic(w, h, cell_x, cell_y, seed, period_x=None):
    """Smooth value noise in [0, 1], periodic in x with period `period_x` (default w; must be a
    multiple of cell_x). Rolling it by any whole number of texels keeps it seamless."""
    px = period_x or w
    assert px % cell_x == 0, (px, cell_x)
    nx = px // cell_x
    ny = int(math.ceil(h / cell_y)) + 2
    rng = np.random.default_rng(seed)
    lat = rng.random((ny + 1, nx))
    xs = np.arange(w) / cell_x
    ys = np.arange(h) / cell_y
    x0 = np.floor(xs).astype(int)
    y0 = np.floor(ys).astype(int)
    fx = xs - x0
    fy = ys - y0
    sx = fx * fx * (3 - 2 * fx)
    sy = fy * fy * (3 - 2 * fy)
    xa, xb = x0 % nx, (x0 + 1) % nx
    ya, yb = y0, y0 + 1
    v00 = lat[np.ix_(ya, xa)]
    v01 = lat[np.ix_(ya, xb)]
    v10 = lat[np.ix_(yb, xa)]
    v11 = lat[np.ix_(yb, xb)]
    top = v00 + (v01 - v00) * sx[None, :]
    bot = v10 + (v11 - v10) * sx[None, :]
    return top + (bot - top) * sy[:, None]


def fbm_periodic(w, h, cells, seed, period_x=None):
    """Sum of octaves of periodic value noise, normalised to [-1, 1]. `cells` is a list of
    (cell_x, cell_y, weight)."""
    acc = np.zeros((h, w))
    tot = 0.0
    for i, (cx, cy, wt) in enumerate(cells):
        acc += wt * (value_noise_periodic(w, h, cx, cy, seed * 131 + i * 17, period_x) * 2 - 1)
        tot += wt
    return acc / tot


def noise1_periodic(n, period, harmonics, seed):
    """1-D smooth periodic noise over n samples (period divides the harmonics' wavelengths)."""
    rng = np.random.default_rng(seed)
    x = np.arange(n)
    out = np.zeros(n)
    tot = 0
    for k in harmonics:
        a = 1.0 / k
        out += a * np.sin(2 * math.pi * k * x / period + rng.random() * 2 * math.pi)
        tot += a
    return out / tot


# ----------------------------------------------------------------------------------------------- drawing

def blank(w, h):
    return np.zeros((h, w), np.int16)


def put(g, x, y, c, wrap_x=False):
    h, w = g.shape
    x, y = int(round(x)), int(round(y))
    if wrap_x:
        x %= w
    if 0 <= x < w and 0 <= y < h:
        g[y, x] = c


def line_points(x0, y0, x1, y1):
    x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
    pts = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
    return pts


def draw_line(g, x0, y0, x1, y1, c, wrap_x=False):
    for x, y in line_points(x0, y0, x1, y1):
        put(g, x, y, c, wrap_x)


def polygon_mask(w, h, pts):
    """Boolean mask of the polygon (even-odd, sampled at texel centres)."""
    ys, xs = np.mgrid[0:h, 0:w]
    px = xs + 0.5
    py = ys + 0.5
    inside = np.zeros((h, w), bool)
    n = len(pts)
    for i in range(n):
        xa, ya = pts[i]
        xb, yb = pts[(i + 1) % n]
        cond = ((ya > py) != (yb > py))
        with np.errstate(divide='ignore', invalid='ignore'):
            xint = xa + (py - ya) * (xb - xa) / (yb - ya)
        inside ^= cond & (px < xint)
    return inside


def disc_mask(w, h, cx, cy, rx, ry=None):
    ry = rx if ry is None else ry
    ys, xs = np.mgrid[0:h, 0:w]
    return ((xs + 0.5 - cx) / max(rx, 1e-6)) ** 2 + ((ys + 0.5 - cy) / max(ry, 1e-6)) ** 2 <= 1.0


def dilate(mask, r=1, diag=False):
    out = mask.copy()
    for _ in range(r):
        m = out.copy()
        m[1:, :] |= out[:-1, :]
        m[:-1, :] |= out[1:, :]
        m[:, 1:] |= out[:, :-1]
        m[:, :-1] |= out[:, 1:]
        if diag:
            m[1:, 1:] |= out[:-1, :-1]
            m[1:, :-1] |= out[:-1, 1:]
            m[:-1, 1:] |= out[1:, :-1]
            m[:-1, :-1] |= out[1:, 1:]
        out = m
    return out


def dilate_wrap(mask, r=1, diag=False):
    """Dilate with x wrapping (for tileable strips)."""
    out = mask.copy()
    for _ in range(r):
        m = out.copy()
        m[1:, :] |= out[:-1, :]
        m[:-1, :] |= out[1:, :]
        m |= np.roll(out, 1, axis=1)
        m |= np.roll(out, -1, axis=1)
        if diag:
            up = np.zeros_like(out)
            up[1:, :] = out[:-1, :]
            dn = np.zeros_like(out)
            dn[:-1, :] = out[1:, :]
            m |= np.roll(up, 1, axis=1) | np.roll(up, -1, axis=1) | np.roll(dn, 1, axis=1) | np.roll(dn, -1, axis=1)
        out = m
    return out


def neighbours4(mask, wrap_x=False):
    """Count of 4-neighbours set."""
    m = mask.astype(np.int16)
    c = np.zeros_like(m)
    c[1:, :] += m[:-1, :]
    c[:-1, :] += m[1:, :]
    if wrap_x:
        c += np.roll(m, 1, axis=1) + np.roll(m, -1, axis=1)
    else:
        c[:, 1:] += m[:, :-1]
        c[:, :-1] += m[:, 1:]
    return c


def despeckle(g, wrap_x=False, passes=2):
    """Pixel-art cleanup: a lone texel whose 4 neighbours all share one other value takes it."""
    h, w = g.shape
    for _ in range(passes):
        if wrap_x:
            up = np.vstack([g[:1], g[:-1]])
            dn = np.vstack([g[1:], g[-1:]])
            lf = np.roll(g, 1, axis=1)
            rt = np.roll(g, -1, axis=1)
        else:
            up = np.vstack([g[:1], g[:-1]])
            dn = np.vstack([g[1:], g[-1:]])
            lf = np.hstack([g[:, :1], g[:, :-1]])
            rt = np.hstack([g[:, 1:], g[:, -1:]])
        same = (up == dn) & (dn == lf) & (lf == rt) & (up != g)
        g = np.where(same, up, g)
    return g


def rng_for(*keys):
    s = 0
    for k in keys:
        s = (s * 1000003 + (hash(k) & 0xFFFFFFF if isinstance(k, str) else int(k))) & 0x7FFFFFFF
    return np.random.default_rng(s)


def stable_seed(text):
    """A seed that is the same on every run (str hash is salted per process)."""
    h = 2166136261
    for ch in text.encode('utf-8'):
        h = ((h ^ ch) * 16777619) & 0xFFFFFFFF
    return h


def rng(text):
    return np.random.default_rng(stable_seed(text))


# ----------------------------------------------------------------------------------------------- assembly

def strip(pal, frames):
    """A horizontal strip PNG (frame 0 leftmost) from index grids of one size."""
    h, w = frames[0].shape
    out = Image.new('RGBA', (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        assert f.shape == (h, w), (f.shape, (h, w))
        out.paste(pal.image(f), (i * w, 0))
    return out


def upscale(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)
