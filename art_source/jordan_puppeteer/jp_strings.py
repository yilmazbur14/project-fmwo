"""The puppet strings: two colour takes, drawn on the game's texel grid.

A string is 1 texel wide (3 px on screen) in its CORE colour, with a 1-texel GLOW on each side
that is ADDED (the aura's blending, never semi-alpha), so it lifts the void and his armour a
little without a hard edge. Where several strings run side by side their glows join into one
band instead of stacking brighter. The fingertip gets a small additive KNOT glow and a HOT texel.

  red   blood red, the puppets' red/black family (the lava's own blood red)
  blue  the rune circle's cold light: the approved hot-red-on-cold-blue contrast

For the engine (the strings are live): a string is a curve from a fingertip texel to the puppet's
back hook with a sag set by its tension (0 slack .. 1 taut; see jordan_puppeteer_fingertips.json).
To match the art, plot it on the 640x360 texel grid (3x3 px per texel) rather than as a smooth
3 px Line2D; string_tile() is a Line2D texture for either way (rows: glow, core, glow; one hot
bead per 16 texels that runs down the string when its UV scrolls, e.g. on the yank).

Nothing here writes a file.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import jp_rig as R  # noqa: E402,F401  (puts art_source/jordan_god on the path)
import jg_base as B  # noqa: E402
from PIL import Image, ImageChops  # noqa: E402

TAKES = {
    'red': {
        # blood red, one step up Jordan's own red ramp: the lava's 'R' (C9293F) is the exact red of
        # his wing veins and vanished wherever a string crossed a wing
        'core': B.hx('EC5A5B'),      # v2 'T'
        'hot': B.hx('FFF3B0'),       # the knot's centre and the travelling bead: the lava's white-hot
        'bright': B.hx('FF9C8C'),    # the bead's shoulders (v2 'U')
        'glow': B.hx('4C0D1A'),      # ADDED either side (v2 'v', the darkest red)
        'knot': B.hx('8C1B2D'),      # ADDED round the fingertip (v2 'V')
    },
    'blue': {
        'core': B.hx('66C6EC'),      # the rune circle's bright line ('f')
        'hot': B.hx('D2F6FF'),       # the runes' hot fleck ('g')
        'bright': B.hx('9ADCF4'),    # between f and g, for the bead
        'glow': B.hx('17385A'),      # ADDED either side (the runes' dim 'd')
        'knot': B.hx('2B6C99'),      # ADDED round the fingertip (the runes' mid 'e')
    },
}


def curve(p0, p1, tension, bow=0.0, wave=0.0, phase=0.0, n=None):
    """Points of a hanging string from p0 (fingertip) to p1 (hook), texel coordinates (floats).
    A quadratic whose middle sags down by (1 - tension) of 12% of the span, plus `bow` texels
    sideways (a slack string drifts) and a `wave` of that many texels across it, zero at both
    ends (a string gone limp)."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    span = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / span, dx / span
    sag = (1.0 - tension) * 0.12 * span
    c = ((p0[0] + p1[0]) / 2.0 + bow, (p0[1] + p1[1]) / 2.0 + sag)
    n = n or max(8, int(span / 2))
    out = []
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * p1[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * p1[1]
        if wave:
            w = wave * math.sin(math.pi * t) * math.sin(3.0 * math.pi * t + phase)
            x, y = x + nx * w, y + ny * w
        out.append((x, y))
    return out


def raster(pts):
    """The 1-texel line through the points: 8-connected, no doubled corners."""
    ipts = [(int(math.floor(x + 0.5)), int(math.floor(y + 0.5))) for x, y in pts]
    line = B.polyline(ipts)
    # drop L-corners (a texel whose two neighbours along the line are diagonal to each other)
    out = []
    for i, p in enumerate(line):
        if 0 < i < len(line) - 1:
            a, b = line[i - 1], line[i + 1]
            if abs(a[0] - b[0]) == 1 and abs(a[1] - b[1]) == 1 and (a[0] == p[0] or a[1] == p[1]):
                continue
        out.append(p)
    return out


def string_texels(strings):
    """strings: [(points, ...)] -> (core set, glow set). The glow is the ring round the cores,
    one texel wide, minus the cores, unioned over every string - except a texel lying between two
    different strings, which stays dark so neighbouring strings read apart instead of fusing
    into one bar."""
    cores = [set(raster(pts)) for pts in strings]
    core = set().union(*cores) if cores else set()
    owner = {}
    for i, c in enumerate(cores):
        for p in c:
            owner.setdefault(p, set()).add(i)
    glow = set()
    for (x, y) in core:
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if q in core:
                continue
            near = set()
            for r in ((q[0] + 1, q[1]), (q[0] - 1, q[1]), (q[0], q[1] + 1), (q[0], q[1] - 1)):
                near |= owner.get(r, set())
            if len(near) < 2:
                glow.add(q)
    return core, glow


def draw(native, strings, take, knots=(), beads=(), clip=None):
    """Draw strings onto an RGBA image in place: glow added, core opaque. knots: fingertip texels
    (each gets the hot texel and an added 3x3 knot glow). beads: texels on the strings where a
    pulse is (the damage running up them): a hot texel, bright neighbours and a knot glow.
    clip(x, y) -> False skips a texel (e.g. behind a puppet)."""
    T = TAKES[take]
    core, glow = string_texels(strings)
    kglow = set()
    for (x, y) in list(knots) + list(beads):
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                kglow.add((x + dx, y + dy))
    W, H = native.size
    add = Image.new('RGB', (W, H), (0, 0, 0))
    ap = add.load()
    for (x, y) in glow | kglow:
        if 0 <= x < W and 0 <= y < H and (clip is None or clip(x, y)):
            c = T['knot'] if (x, y) in kglow else T['glow']
            ap[x, y] = c[:3]
    base = native.convert('RGB')
    base = ImageChops.add(base, add)
    out = base.convert('RGBA')
    op = out.load()
    for (x, y) in core:
        if 0 <= x < W and 0 <= y < H and (clip is None or clip(x, y)):
            op[x, y] = T['core']
    for (x, y) in beads:
        for q in ((x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)):
            if q in core and 0 <= q[0] < W and 0 <= q[1] < H:
                op[q[0], q[1]] = T['bright']
    for (x, y) in list(knots) + list(beads):
        if 0 <= x < W and 0 <= y < H:
            op[x, y] = T['hot']
    native.paste(out)


# ------------------------------------------------------------------ engine textures

def string_tile(take, length=16):
    """A Line2D tile, `length` texels along x, 3 across (glow / core / glow), with one hot bead.
    Opaque; the glow rows are meant to be ADDED, so draw the tile's glow and core as two lines
    (or add the whole line: the core then reads a touch brighter over lit armour)."""
    T = TAKES[take]
    im = Image.new('RGBA', (length, 3), (0, 0, 0, 0))
    px = im.load()
    for x in range(length):
        px[x, 0] = T['glow']
        px[x, 2] = T['glow']
        px[x, 1] = T['core']
    px[length - 3, 1] = T['bright']
    px[length - 2, 1] = T['hot']
    px[length - 1, 1] = T['bright']
    px[length - 2, 0] = T['knot']
    px[length - 2, 2] = T['knot']
    return im


def knot_sprite(take):
    """5x5, additive, centred on (2, 2): the fingertip's glow (the hot texel is its centre)."""
    T = TAKES[take]
    im = Image.new('RGBA', (5, 5), (0, 0, 0, 0))
    px = im.load()
    for y in range(5):
        for x in range(5):
            d = abs(x - 2) + abs(y - 2)
            if d == 0:
                px[x, y] = T['hot']
            elif d == 1:
                px[x, y] = T['knot']
            elif d == 2:
                px[x, y] = T['glow']
    return im
