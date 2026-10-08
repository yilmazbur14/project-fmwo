"""home_run.png: 6 frames of 128x40, pivot at the bottom centre (64, 40). Gold, the approved HOME RUN!
(homerun.py, the KNIGHT BREAKER! recipe) animated:

  0 squashed pop   the word squashed to 7 rows and stretched 15% wide, bright scheme, sparks out
  1 overshoot      stretched to 14 rows and 8% narrow, bright scheme, tall
  2 settle         the approved pop frame (11 rows, bright, up a texel)
  3 hold           the approved rest frame
  4 glint sweep    rest + a white diagonal glint across the left third
  5 glint sweep    rest + the glint across the right third, end sparkles lit

Every frame sits on the same baseline: the extrusion's lowest row is row 37 in every frame, so the
pivot at the bottom centre holds the word still while it squashes and stretches.
"""
import os
import sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault('DH_WORK', os.path.join(HERE, '_dh_work'))
from dh_common import Canvas, C   # noqa: E402
import lettering as LT             # noqa: E402
import homerun as HR               # noqa: E402

FW, FH = 128, 40
BASE = 37           # the row the extrusion's bottom sits on in every frame
WORD = HR.WORD


def scaled_glyphs(th, wf):
    out = {}
    for ch, g in HR.GLYPHS.items():
        w = len(g[0])
        nw = max(1, int(round(w * wf)))
        rows = []
        for j in range(th):
            src = g[min(10, int(j * 11 / th))]
            rows.append(''.join(src[min(w - 1, int(i / wf))] for i in range(nw)))
        out[ch] = rows
    return out


def scaled_slant(th):
    return [LT.SLANT[min(10, int(j * 11 / th))] for j in range(th)]


def bbox(c):
    xs = [x for y in range(c.h) for x in range(c.w) if c.p[y][x]]
    ys = [y for y in range(c.h) for x in range(c.w) if c.p[y][x]]
    return min(xs), min(ys), max(xs), max(ys)


def word(scheme, bright, glyphs=HR.GLYPHS, slant=LT.SLANT, gap=2):
    """render on a roomy canvas, then drop it into the frame centred with its bottom on BASE"""
    big = LT.word_canvas(WORD, scheme, bright, 200, 48, glyphs=glyphs, slant=slant, gap=gap, oy_rest=8)
    x0, y0, x1, y1 = bbox(big)
    f = Canvas(FW, FH)
    ox = (FW - (x1 - x0 + 1)) // 2 - x0
    oy = BASE - y1
    for y in range(big.h):
        for x in range(big.w):
            if big.p[y][x]:
                f.set(x + ox, y + oy, big.p[y][x])
    return f


def sparkle(c, x, y, size, core='W', tip='Y'):
    if c.get(x, y) is not None:
        return
    c.set(x, y, C[core])
    for k in range(1, size + 1):
        col = C[core] if k < size else C[tip]
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            if c.get(x + dx, y + dy) is None:
                c.set(x + dx, y + dy, col)




LIGHTER = {C['Y']: C['W'], C['O']: C['W'], C['E']: C['e'], C['r']: C['E']}


def glint(c, x_at, width=4, slope=1.0):
    """a white 45-degree band sweeping across the letters: gold and orange go white, the red extrusion
    goes a step lighter; the outline and empty pixels are never touched"""
    for y in range(c.h):
        for x in range(c.w):
            u = x - x_at + (y - BASE) * slope
            if 0 <= u < width and c.p[y][x] in LIGHTER:
                c.set(x, y, LIGHTER[c.p[y][x]])


def frames():
    rest, bright = HR.SCHEME
    f0 = word(bright, True, scaled_glyphs(7, 1.15), scaled_slant(7))
    x0, y0, x1, y1 = bbox(f0)
    for (x, y, s) in [(x0 - 4, y0 + 2, 1), (x1 + 4, y0 + 1, 1), (x0 + 10, y0 - 4, 0), (x1 - 12, y0 - 4, 0)]:
        sparkle(f0, x, y, s)
    f1 = word(bright, True, scaled_glyphs(14, 0.92), scaled_slant(14))
    x0, y0, x1, y1 = bbox(f1)
    for (x, y, s) in [(x0 - 3, y0 + 3, 2), (x1 + 3, y0 + 2, 2), ((x0 + x1) // 2, y0 - 3, 1)]:
        sparkle(f1, x, y, s)
    f2 = word(bright, True)
    x0, y0, x1, y1 = bbox(f2)
    for (x, y, s) in [(x0 - 3, y0 + 3, 1), (x1 + 3, y0 + 2, 1), ((x0 + x1) // 2, y0 - 2, 0)]:
        sparkle(f2, x, y, s)
    f3 = word(rest, False)
    x0, y0, x1, y1 = bbox(f3)
    for (x, y, s) in [(x0 - 3, y0 + 3, 0), (x1 + 3, y0 + 2, 0)]:
        sparkle(f3, x, y, s)
    f4 = word(rest, False)
    glint(f4, x0 + (x1 - x0) * 0.30)
    sparkle(f4, x0 - 3, y0 + 3, 1)
    f5 = word(rest, False)
    glint(f5, x0 + (x1 - x0) * 0.72)
    sparkle(f5, x1 + 3, y0 + 2, 1)
    return [f0, f1, f2, f3, f4, f5]


# --------------------------------------------------------------------------- pips
# 12x12 baseball pips for the streak: 0 empty (dark ball, faint stitches), 1 filled (white ball, red stitches)
PIP_EMPTY = [
    "....KKKK....",
    "..KKnnnnKK..",
    ".KnnqnnqnnK.",
    ".KnqnnnnqnK.",
    "KnnqnnnnqnnK",
    "KnqnnnnnnqnK",
    "KnqnnnnnnqnK",
    "KnnqnnnnqnnK",
    ".KnqnnnnqnK.",
    ".KnnqnnqnnK.",
    "..KKnnnnKK..",
    "....KKKK....",
]
PIP_FULL = [
    "....KKKK....",
    "..KKWWWWKK..",
    ".KWWEWWEWPK.",
    ".KWEWWWWEPK.",
    "KWWEWWWWEWPK",
    "KWEWWWWWWEPK",
    "KWEWWWWWWEsK",
    "KWWEWWWWEPsK",
    ".KWEPPPPEsK.",
    ".KPPEPPEssK.",
    "..KKsssskK..",
    "....KKKK....",
]
PIP_PAL = {'K': '000000', 'n': '222034', 'q': '45283c', 'W': 'ffffff', 'P': 'cbdbfc', 's': '9badb7',
           'E': 'ac3232', 'k': '000000'}


def pips():
    out = []
    for rows in (PIP_EMPTY, PIP_FULL):
        assert len(rows) == 12 and all(len(r) == 12 for r in rows), rows
        c = Canvas(12, 12)
        for y, r in enumerate(rows):
            for x, ch in enumerate(r):
                if ch != '.':
                    c.set(x, y, PIP_PAL[ch])
        out.append(c)
    return out
