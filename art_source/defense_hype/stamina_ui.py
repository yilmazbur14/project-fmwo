"""Stamina bar (brass kit). Sits under the hearts, bottom-left.
  stamina_bar_frame  : 88x15, 9-slice margins L7 T6 R8 B6 (horizontal stretch keeps rivet plates intact)
  stamina_bar_fill   : 74x5 green -> lime gradient, revealed left to right, drawn at (7, 5) in the frame
  stamina_bar_low    : 2 frames of 74x5, red / orange flash, same placement as the fill
  stamina_bar_broken : 2 frames of 88x15, whole-bar overlay for GUARD BREAK (cracked + red flash)
"""
import sys
sys.dont_write_bytecode = True
from dh_common import *

FW, FH = 88, 15
ML, MT, MR, MB = 7, 6, 8, 6
FILL_X, FILL_Y, FILL_W, FILL_H = 7, 5, 74, 5

PLATE = ["KKKKKK",
         "KYYYSK",
         "KYWYDK",
         "KYRpDK",
         "KSDDoK",
         "KKKKKK"]


def frame_canvas(pal_over=None):
    P = dict(C)
    if pal_over:
        P.update(pal_over)
    c = Canvas(FW, FH)
    # tube cross-section (x in the stretchable middle): rows 0..14
    mid = ['K', 'Y', 'T', 'D', 'K', 'n', 'n', 'n', 'n', 'I', 'K', 'T', 'D', 'o', 'K']
    for x in range(FW):
        for y in range(FH):
            c.p[y][x] = P[mid[y]]
    # left end: plates rows 0-5 / 9-14 in cols 0-5, cap bar rows 6-8, ring col 6
    for y in range(FH):
        c.p[y][6] = P['K'] if 4 <= y <= 10 else P[mid[y]]
    for y in range(6, 9):
        for x, ch in enumerate('KYSTTD'):
            c.p[y][x] = P[ch]
    # right end: I (reflected light) col 80 inside the ring, ring col 81, cap bar cols 82-87
    for y in range(5, 10):
        c.p[y][80] = P['I']
    for y in range(FH):
        c.p[y][81] = P['K'] if 4 <= y <= 10 else P[mid[y]]
    for y in range(6, 9):
        for i, ch in enumerate('STTDoK'):
            c.p[y][82 + i] = P[ch]
    # rivet plates (identical at both ends: light from the top-left)
    for (x0, y0) in [(0, 0), (FW - 6, 0), (0, FH - 6), (FW - 6, FH - 6)]:
        for j, row in enumerate(PLATE):
            for i, ch in enumerate(row):
                c.p[y0 + j][x0 + i] = P[ch]
    # the top rim runs into the plates' outline, the ring meets the plate outline
    for (x, y) in [(0, 0), (FW - 1, 0), (0, FH - 1), (FW - 1, FH - 1)]:
        c.p[y][x] = None
    return c


def fill_canvas(ramps, edges, w=FILL_W, h=FILL_H):
    """ramps: list of (highlight, base, shade); edges: x where band k+1 starts. 2-column checker dither
    before each edge. Row 0 highlight, rows 1..h-2 base, last row shade."""
    c = Canvas(w, h)
    for x in range(w):
        band = sum(1 for e in edges if x >= e)
        nb = band + 1 if (band < len(edges) and x in (edges[band] - 2, edges[band] - 1)) else band
        for y in range(h):
            b = nb if (nb != band and (x + y) % 2 == 0) else band
            hi, base, sh = ramps[b]
            col = hi if y == 0 else (sh if y == h - 1 else base)
            c.p[y][x] = C[col]
    return c


def stamina_fill():
    ramps = [('l', 'g', 'G'),      # vivid green
             ('Y', 'l', 'g'),      # lime, yellow glint on top
             ('W', 'l', 'g')]      # the last stretch catches a white glint
    return fill_canvas(ramps, [30, 62])


def stamina_low():
    f0 = fill_canvas([('e', 'E', 'r')], [])            # dim red
    f1 = fill_canvas([('Y', 'O', 'E')], [])            # hot orange
    return [f0, f1]


# guard-break cracks: '.' keep, '_' where the split meets the outline (kept black), 'K' black split edge,
# 'g' split core (black / white-hot), 's' chipped edge catching light (grey / orange), 'h' hairline (black / gold)
CRACK_MAIN = [
    "......_.....",
    "......K.....",
    ".....K......",
    ".....K......",
    "....KK......",
    "...sKgK.....",
    "..h.KgK.....",
    ".h..sKgK....",
    ".....sKgK...",
    "......KgKs..",
    ".......KK...",
    ".......K....",
    "......K.....",
    "......K.....",
    "......_.....",
]
CRACK_SMALL = [
    ".....",
    ".....",
    ".....",
    ".....",
    ".....",
    "...h.",
    "..h..",
    "..h..",
    ".h...",
    ".h...",
    ".....",
    ".....",
    ".....",
    ".....",
    ".....",
]


def _apply_crack(f, rows, x0, glow):
    for y, row in enumerate(rows):
        for i, ch in enumerate(row):
            x = x0 + i
            if ch == '.':
                continue
            if ch == '_':
                f.p[y][x] = C['K']          # the overlay draws over the normal frame: stay opaque
            elif ch == 'K':
                f.p[y][x] = C['K']
            elif ch == 'g':
                f.p[y][x] = C['K'] if not glow else (C['W'] if y in (6, 7, 8) else C['Y'])
            elif ch == 's':
                f.p[y][x] = C['s'] if not glow else C['O']
            elif ch == 'h':
                f.p[y][x] = C['K'] if not glow else C['Y']


def stamina_broken():
    # frame 0: drained brass, empty scorched tube, a wide jagged split through tube and rims
    f0 = frame_canvas()
    for y in range(5, 10):
        for x in range(7, 81):
            f0.p[y][x] = C['p'] if y < 9 else C['r']
    # frame 1: the whole bar flashes red and the splits glow white-hot
    red = {'Y': C['e'], 'S': C['e'], 'W': C['S'], 'T': C['E'], 'D': C['r'], 'o': C['p'], 'I': C['E'],
           'n': C['E'], 'R': C['p'], 'p': C['n']}
    f1 = frame_canvas(red)
    for y in range(5, 10):
        for x in range(7, 81):
            f1.p[y][x] = C['E'] if y < 9 else C['e']
    for f, glow in ((f0, False), (f1, True)):
        _apply_crack(f, CRACK_MAIN, 24, glow)
        _apply_crack(f, CRACK_SMALL, 58, glow)
    return [f0, f1]


def build():
    return {
        'stamina_bar_frame': [frame_canvas()],
        'stamina_bar_fill': [stamina_fill()],
        'stamina_bar_low': stamina_low(),
        'stamina_bar_broken': stamina_broken(),
    }


if __name__ == '__main__':
    A = build()
    print('9-slice problems:', nine_slice_problems(A['stamina_bar_frame'][0], ML, MT, MR, MB))
    for name, frames in A.items():
        s = strip(frames)
        save_zoom(s, work('%s_8x.png' % name), 8, bg=(70, 70, 90), grid=(frames[0].w, frames[0].h))
        print(name, s.w, s.h, 'non-DB32', s.colours() - DB32)
    # composite: frame + fill at 50% / low / broken
    comp = []
    fr = A['stamina_bar_frame'][0]
    for kind in ('full', 'half', 'low0', 'low1', 'broken0', 'broken1', 'empty'):
        c = fr.copy()
        if kind in ('full', 'half'):
            f = A['stamina_bar_fill'][0]
            n = FILL_W if kind == 'full' else FILL_W // 2
            c.blit(crop(f, 0, 0, n, FILL_H), FILL_X, FILL_Y)
        elif kind.startswith('low'):
            f = A['stamina_bar_low'][int(kind[-1])]
            c.blit(crop(f, 0, 0, 18, FILL_H), FILL_X, FILL_Y)
        elif kind.startswith('broken'):
            c = A['stamina_bar_broken'][int(kind[-1])].copy()
        comp.append(c)
    stack = Canvas(FW, FH * len(comp) + 2 * (len(comp) - 1))
    for i, c in enumerate(comp):
        stack.blit(c, 0, i * (FH + 2))
    save_zoom(stack, work('stamina_states_8x.png'), 8, bg=(70, 70, 90))
