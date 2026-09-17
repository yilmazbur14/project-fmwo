"""Comic FX: bold outlined lettering, impact starbursts, motion arcs, anger veins, sweat, shock marks."""
import math
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from pal import *

# bold 2px-stroke glyphs, 8 rows
_G = {
    'S': [".####.", "##..##", "##....", ".###..", "...##.", "....##", "##..##", ".####."],
    'M': ["##....##", "###..###", "########", "##.##.##", "##....##", "##....##", "##....##", "##....##"],
    'A': ["..##..", ".####.", "##..##", "##..##", "######", "##..##", "##..##", "##..##"],
    'C': [".####.", "##..##", "##....", "##....", "##....", "##....", "##..##", ".####."],
    'K': ["##..##", "##.##.", "####..", "###...", "####..", "##.##.", "##..##", "##..##"],
    'H': ["##..##", "##..##", "##..##", "######", "##..##", "##..##", "##..##", "##..##"],
    'O': [".####.", "##..##", "##..##", "##..##", "##..##", "##..##", "##..##", ".####."],
    'P': ["#####.", "##..##", "##..##", "#####.", "##....", "##....", "##....", "##...."],
    'G': [".####.", "##..##", "##....", "##.###", "##..##", "##..##", "##..##", ".####."],
    'U': ["##..##", "##..##", "##..##", "##..##", "##..##", "##..##", "##..##", ".####."],
    'L': ["##....", "##....", "##....", "##....", "##....", "##....", "######", "######"],
    'R': ["#####.", "##..##", "##..##", "#####.", "####..", "##.##.", "##..##", "##..##"],
    'W': ["##....##", "##....##", "##....##", "##.##.##", "##.##.##", "########", "###..###", "##....##"],
    '!': ["##", "##", "##", "##", "##", "..", "##", "##"],
    '?': [".####.", "##..##", "....##", "...##.", "..##..", "......", "..##..", "..##.."],
    ' ': ["...", "...", "...", "...", "...", "...", "...", "..."],
}


def lettering(cv, text, x, y, fill=(IMPACT[0], IMPACT[1], IMPACT[2]), shadow=IMPACT[5], bounce=(0, -1, 1, 0, -1, 1),
              spacing=1, scale=1):
    """draw bouncy comic lettering with a gradient fill, 1px black outline and a coloured drop shadow"""
    glyph_px = set()
    cx = x
    for i, ch in enumerate(text):
        g = _G[ch]
        dy = bounce[i % len(bounce)]
        for j, row in enumerate(g):
            for k, v in enumerate(row):
                if v == '#':
                    for sy in range(scale):
                        for sx in range(scale):
                            glyph_px.add((cx + k * scale + sx, y + dy + j * scale + sy))
        cx += (len(g[0]) + spacing) * scale
    outline = dilate(glyph_px, 1, diag=True) - glyph_px
    shadow_px = shift(dilate(glyph_px, 1, diag=True), 1, 2) - dilate(glyph_px, 1, diag=True)
    cv.fill(shadow_px, shadow)
    cv.fill(outline, BLACK)
    ys = [p[1] for p in glyph_px]
    y0, y1 = min(ys), max(ys)
    for (px, py) in glyph_px:
        t = (py - y0) / max(1, (y1 - y0))
        cv.put(px, py, fill[0] if t < 0.3 else (fill[1] if t < 0.65 else fill[2]))
    return cx - x


def text_width(text, spacing=1, scale=1):
    return sum((len(_G[c][0]) + spacing) * scale for c in text) - spacing * scale


def starburst(cv, cx, cy, r_out, r_in, n=10, seed=0, ramp=IMPACT, rot=0.0):
    """spiky impact star: white core, yellow, orange rim, black outline"""
    pts = []
    for i in range(n * 2):
        a = rot + math.pi * i / n
        jitter = 1.0 + 0.18 * math.sin(i * 12.9898 + seed * 78.233)
        r = (r_out * jitter) if i % 2 == 0 else r_in
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r * 0.85))
    m = poly(pts)
    cv.fill(m, ramp[3])
    inner = poly([(cx + (px - cx) * 0.68, cy + (py - cy) * 0.68) for px, py in pts])
    cv.fill(inner, ramp[2])
    core = poly([(cx + (px - cx) * 0.38, cy + (py - cy) * 0.38) for px, py in pts])
    cv.fill(core, ramp[0])
    cv.outline(m)
    return m


def motion_arc(cv, cx, cy, r, a0, a1, width=1, col=WHITE, dashed=False):
    steps = max(8, int(abs(a1 - a0) * r / 1.5))
    for i in range(steps + 1):
        if dashed and (i // 3) % 2:
            continue
        a = math.radians(a0 + (a1 - a0) * i / steps)
        for w in range(width):
            x = cx + math.cos(a) * (r - w)
            y = cy + math.sin(a) * (r - w)
            cv.put(int(round(x)), int(round(y)), col)


def speed_line(cv, x0, y0, x1, y1, col=WHITE):
    n = int(max(abs(x1 - x0), abs(y1 - y0)))
    for i in range(n + 1):
        t = i / max(1, n)
        cv.put(int(round(x0 + (x1 - x0) * t)), int(round(y0 + (y1 - y0) * t)), col)


VEIN = """
.kk.kk.
kPk.kPk
kPPkPPk
.kk.kk.
kPPkPPk
kPk.kPk
.kk.kk.
"""

SWEAT_DROP = """
.k.
kbk
kbk
kWBk
.kk.
"""

SHOCK = """
k...k...k
.k..k..k.
..k.k.k..
"""


def vein(cv, x, y, big=False):
    cm = {'k': BLACK, 'P': VEIN_C[1] if not big else VEIN_C[0]}
    cv.stamp(VEIN, x, y, cm)


VEIN_C = [hx('ff5a4a'), hx('e0524a')]


def sweat(cv, x, y):
    cv.stamp(SWEAT_DROP, x, y, {'k': BLACK, 'b': SWEAT[1], 'B': SWEAT[2], 'W': WHITE})


def shock(cv, x, y):
    cv.stamp(SHOCK, x, y, {'k': BLACK})
