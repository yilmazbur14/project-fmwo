"""Assets/UI/key_shift.png - a wide SHIFT keycap in the exact style of key_q.png / key_w.png.

The cap is not redrawn: key_q's own pixels are reused. Its letter is wiped (222034 is only ever the glyph),
then the cap is widened by duplicating one middle column, so every bevel, highlight, skirt tone and rounded
corner is pixel-identical to the existing keys. Only the glyph is new: a shift arrow plus SHIFT in 222034.

32x32 keys sit in a 96x96 card slot (3x); this one is 64x32, so its card slot is 192x96 at the same 3x.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', 'le_src')))
from pngio import read_png, write_png

UI = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/UI'
FACE = (203, 219, 252, 255)      # cbdbfc
GLYPH = (34, 32, 52, 255)        # 222034
SPLICE_COL = 16                  # a column with no corner/bevel detail
EXTRA = 32                       # 32 -> 64 px wide

def arrow_glyph():
    """the exact up-arrow glyph the arrow keys use (key_arrows.png, top key)"""
    w, h, px = read_png(os.path.join(UI, 'key_arrows.png'))
    pts = [(x, y) for y in range(0, 32) for x in range(32, 64)
           if px[y][x][3] and tuple(px[y][x]) == GLYPH]
    x0 = min(p[0] for p in pts)
    y0 = min(p[1] for p in pts)
    return {(x - x0, y - y0) for (x, y) in pts}, max(p[0] for p in pts) - x0 + 1, max(p[1] for p in pts) - y0 + 1


FONT = {
    'S': [".####.", "##..##", "##....", ".####.", "....##", "##..##", ".####."],
    'H': ["##..##", "##..##", "##..##", "######", "##..##", "##..##", "##..##"],
    'I': ["####", ".##.", ".##.", ".##.", ".##.", ".##.", "####"],
    'F': ["#####", "##...", "##...", "####.", "##...", "##...", "##..."],
    'T': ["######", "..##..", "..##..", "..##..", "..##..", "..##..", "..##.."],
}


def blank_cap():
    w, h, px = read_png(os.path.join(UI, 'key_q.png'))
    rows = []
    for y in range(h):
        row = [tuple(p) for p in px[y]]
        row = [FACE if p == GLYPH else p for p in row]          # wipe the Q
        rows.append(row[:SPLICE_COL] + [row[SPLICE_COL]] * EXTRA + row[SPLICE_COL:])
    return w + EXTRA, h, rows


def stamp(rows, grid, x0, y0):
    for j, line in enumerate(grid.strip('\n').split('\n')):
        for i, ch in enumerate(line):
            if ch == '#':
                rows[y0 + j][x0 + i] = GLYPH


def text_width(s, spacing=1):
    return sum(len(FONT[c][0]) + spacing for c in s) - spacing


def draw_text(rows, s, x0, y0, spacing=1):
    cx = x0
    for ch in s:
        g = FONT[ch]
        for j, line in enumerate(g):
            for i, c in enumerate(line):
                if c == '#':
                    rows[y0 + j][cx + i] = GLYPH
        cx += len(g[0]) + spacing
    return cx - x0 - spacing


def build():
    w, h, rows = blank_cap()
    glyph, aw, ah = arrow_glyph()
    tw = text_width('SHIFT')
    gap = 4
    x0 = 5 + (54 - (aw + gap + tw)) // 2          # face runs cols 5..58
    ay = 2 + (22 - ah) // 2
    for (gx, gy) in glyph:
        rows[ay + gy][x0 + gx] = GLYPH
    draw_text(rows, 'SHIFT', x0 + aw + gap, ay + (ah - 7) // 2)
    return w, h, rows


if __name__ == '__main__':
    w, h, rows = build()
    out = os.path.join(UI, 'key_shift.png')
    write_png(out, w, h, rows)
    print(out, w, h)
