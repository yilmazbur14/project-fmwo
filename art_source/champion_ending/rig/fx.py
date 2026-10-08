"""Trophy shine, sparkles and the lift's burst lines. Effects carry no keyline (house rule)."""
from PIL import Image
from common import PROP

UP = {'5': '3', '4': '2', '3': '1', '2': 'W', '1': 'W'}     # two steps toward the light


def shine(grid, phase, width=3, slope=1):
    """A diagonal glint band across the gold only: pixels with x + slope*y in
    [phase, phase + width) step two tones lighter. Returns a new grid (rows list)."""
    rows = [list(r) for r in grid.rows()]
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch in UP and phase <= x + slope * y < phase + width:
                r[x] = UP[ch]
    return [''.join(r) for r in rows]


SPARKS = {
    'dot': ['W'],
    'small': ['.W.', 'W1W', '.W.'],
    'mid': ['..W..', '..1..', 'W1W1W', '..1..', '..W..'],
    'big': ['...W...', '...1...', '...W...', 'W1WWW1W', '...W...', '...1...', '...W...'],
}
FX_PAL = dict(PROP)


def stamp(img, rows, cx, cy, pal=FX_PAL):
    """Stamp a pattern centred on (cx, cy)."""
    px = img.load()
    h, w = len(rows), max(len(r) for r in rows)
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch == '.':
                continue
            x, y = cx - w // 2 + i, cy - h // 2 + j
            if 0 <= x < img.width and 0 <= y < img.height:
                px[x, y] = pal[ch]


def spark(img, kind, cx, cy):
    stamp(img, SPARKS[kind], cx, cy)


def burst_lines(img, cx, cy, r0, r1, n=8, colour='1', skip=(), gap_every=0):
    """Anime impact lines radiating from (cx, cy): 1-px rays between radius r0 and r1."""
    import math
    px = img.load()
    for k in range(n):
        if k in skip:
            continue
        a = -math.pi / 2 + k * 2 * math.pi / n
        steps = int((r1 - r0) * 2) + 1
        last = None
        for s in range(steps):
            r = r0 + (r1 - r0) * s / max(1, steps - 1)
            x, y = round(cx + r * math.cos(a)), round(cy + r * math.sin(a) * 0.85)
            if (x, y) == last:
                continue
            last = (x, y)
            if 0 <= x < img.width and 0 <= y < img.height and px[x, y][3] == 0:
                px[x, y] = FX_PAL[colour]


def streaks(img, xs, y0, y1, colour='1', dash=(3, 1)):
    """Vertical speed streaks (the cup's path) at columns xs from y0 down to y1, dashed."""
    px = img.load()
    on, off = dash
    for i, x in enumerate(xs):
        y = y0 + (i % 2)
        n = 0
        while y <= y1:
            if n % (on + off) < on and 0 <= x < img.width and 0 <= y < img.height:
                px[x, y] = FX_PAL[colour if n < 6 else '2']
            y += 1
            n += 1
