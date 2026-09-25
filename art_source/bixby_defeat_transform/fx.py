"""Effects for the defeat and the transformation. A layer is a dict {(x, y): key-or-RGBA}; palette keys
are the redesign's (common.PAL). Alpha is 0/255 only.

Fire uses the beast's own ramp (u v p P Y, N n), light uses bone/steel whites, and the smoke keeps the
old defeat cloud's colours (normal Bixby's whites and slate) so it matches the puffs left over in the
kept frames 4-9.
"""
import math

import common as C
from common import Rng
from pal import ellipse, line, poly

# the old defeat's smoke (bixby.png colours): outline, shadow, body, highlight
SMOKE = dict(o=(94, 102, 116, 255), s=(168, 176, 190, 255), b=(232, 236, 242, 255), h=(255, 255, 255, 255))
# the old defeat's dizzy stars (kept frames 4, 5 and 9 use the same two sprites)
STAR_Y = (251, 242, 54, 255)
STAR_T = (217, 160, 102, 255)
STAR_D = (138, 111, 48, 255)
WHITE = (255, 255, 255, 255)
STAR_BIG = [
    "....k....",
    "...kYk...",
    "kkkkYkkkk",
    "kYYWYYTTk",
    ".kYYYTTk.",
    "..kYYTk..",
    ".kYYkYTk.",
    ".kYk.kTk.",
    ".kk...kk.",
]
STAR_SMALL = [
    "...k...",
    "..kTk..",
    "kkkTkkk",
    "kTTTDDk",
    ".kTTDk.",
    ".kTkTk.",
    ".kk.kk.",
]
STAR_KEYS = {'k': C.BLACK, 'Y': STAR_Y, 'T': STAR_T, 'D': STAR_D, 'W': WHITE}


def put(layer, x, y, k, keep=False):
    x, y = int(round(x)), int(round(y))
    if keep and (x, y) in layer:
        return
    layer[(x, y)] = k


def star(layer, x, y, big=True):
    rows = STAR_BIG if big else STAR_SMALL
    h = len(rows)
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch != '.':
                layer[(x - len(row) // 2 + c, y - h // 2 + r)] = STAR_KEYS[ch]


#FIRE AND LIGHT

FIRE_HOT_TO_COOL = ['Y', 'P', 'p', 'v', 'u']


def ember(layer, x, y, size=1, hot=True, keep=True):
    """A spark: 1px, a 3px plus, or a 5px diamond; hot = yellow core."""
    core = 'Y' if hot else 'v'
    rim = 'P' if hot else 'u'
    put(layer, x, y, core, keep)
    if size >= 2:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            put(layer, x + dx, y + dy, rim, keep)
    if size >= 3:
        for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            put(layer, x + dx, y + dy, 'u', keep)


def embers(layer, box, n, seed, hot_ratio=0.5, sizes=(1, 1, 2)):
    R = Rng(seed)
    x0, y0, x1, y1 = box
    for i in range(n):
        x = R.range(x0, x1)
        y = R.range(y0, y1)
        ember(layer, x, y, sizes[int(R() * len(sizes)) % len(sizes)], R() < hot_ratio)


def streak(layer, p0, p1, keys):
    """A line whose colour runs through `keys` from p0 to p1."""
    pts = line(int(round(p0[0])), int(round(p0[1])), int(round(p1[0])), int(round(p1[1])))
    n = len(pts)
    for i, (x, y) in enumerate(pts):
        layer[(x, y)] = keys[min(len(keys) - 1, int(len(keys) * i / max(1, n)))]


def impact_lines(layer, cx, cy, n, r0, r1, seed, keys=('W', 'w'), skip=()):
    """Radial speed lines around a hit: white, with a few longer ones."""
    R = Rng(seed)
    for i in range(n):
        a = (i + 0.5 * R()) * 2 * math.pi / n
        if any(lo <= math.degrees(a) % 360 <= hi for lo, hi in skip):
            continue
        ra = r0 + R.range(-3, 3)
        rb = r1 + R.range(-4, 8)
        p0 = (cx + ra * math.cos(a), cy + ra * math.sin(a) * 0.8)
        p1 = (cx + rb * math.cos(a), cy + rb * math.sin(a) * 0.8)
        streak(layer, p0, p1, list(keys))


def hit_chip(layer, x, y, k='w'):
    """A small white chip knocked loose: a 2x2 with a dark corner."""
    for dx, dy in ((0, 0), (1, 0), (0, 1)):
        put(layer, x + dx, y + dy, k)
    put(layer, x + 1, y + 1, 'y')


#SMOKE (stamped puffs, back to front, each keylined in slate so the puffs overlap like cotton)

def puff_cloud(layer, puffs, squash=0.82):
    """puffs: [(cx, cy, r)] back to front. Each puff is outlined in slate, lit from the upper left: a
    white rim, a pale body, and a hard diagonal into shadow on its lower right (as the old cloud)."""
    for (cx, cy, r) in puffs:
        body = ellipse(cx, cy, r, r * squash)
        for p in C.outer_edge(body):
            layer[p] = SMOKE['o']
        for (x, y) in body:
            t = ((x - cx) + (y - cy) / squash) / r          # diagonal: -1.4 upper left .. 1.4 lower right
            if t > 0.42:
                k = SMOKE['s']
            elif t < -0.5:
                k = SMOKE['h']
            else:
                k = SMOKE['b']
            layer[(x, y)] = k


def big_cloud(cx, cy, w, h, seed, r0=14, r1=20, squash=0.82):
    """Overlapping rows of big puffs filling a w x h ellipse: back rows higher and smaller, front rows
    lower and bigger, drawn back to front."""
    R = Rng(seed)
    puffs = []
    step_y = r0 * squash * 1.05
    rows = max(2, int((h - 2 * r1 * squash) / step_y) + 1)
    for row in range(rows):
        v = row / max(1, rows - 1)                           # 0 back .. 1 front
        y = cy - h / 2 + r1 * squash + v * (h - 2 * r1 * squash)
        e = (y - cy) / (h / 2)
        half = max(r1, (w / 2 - r1 * 0.8) * math.sqrt(max(0.0, 1 - e * e * 0.8)))
        step_x = r0 * 1.15
        n = max(2, int(2 * half / step_x) + 1)
        for i in range(n):
            x = cx - half + 2 * half * i / (n - 1)
            r = R.range(r0, r1) * (0.8 + 0.2 * v)
            puffs.append((x + R.range(-3, 3), y + R.range(-3, 3), r))
    puffs.sort(key=lambda p: p[1])
    return puffs


def twinkle(layer, x, y):
    """A white four-point glint with a black edge (the old defeat's twinkles)."""
    plus = [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)]
    for dx, dy in plus:
        for ex, ey in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx + ex, y + dy + ey)
            if (q[0] - x, q[1] - y) not in plus:
                layer[q] = C.BLACK
    for dx, dy in plus:
        layer[(x + dx, y + dy)] = WHITE


def dust(layer, x, y, r, seed):
    """A small dust puff kicked up at the floor: two or three little puffs."""
    R = Rng(seed)
    puffs = [(x, y, r), (x + r * R.range(0.8, 1.2), y + 1, r * 0.7), (x - r * R.range(0.8, 1.1), y + 1, r * 0.6)]
    puffs.sort(key=lambda p: p[1])
    puff_cloud(layer, puffs)


def wisp(layer, x, y, h, seed, lean=1):
    """A thin curl of smoke rising from a doused ember: slate with a pale core, thinning upward."""
    R = Rng(seed)
    ph = R.range(0, 6.28)
    for k in range(h):
        u = k / max(1, h - 1)
        xx = x + lean * 2.2 * math.sin(ph + k * 0.55) * (0.3 + u)
        yy = y - k
        if u < 0.55:
            put(layer, xx, yy, SMOKE['s'])
            put(layer, xx + 1, yy, SMOKE['o'] if u > 0.3 else SMOKE['b'])
        elif R() < 0.75:
            put(layer, xx, yy, SMOKE['s'] if u < 0.8 else SMOKE['o'])
