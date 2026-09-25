"""Tile a flood loop the way BixbyInfernoFloodScript lays and plays it, over the real mat, for seam checks.

Tiles sit on a grid of 57x29-texel beds; each frame's 12 tongue rows rise over the tile above, and tiles
are added row by row, so the lower row draws over the upper one. Tile i of the grid shows loop frame
(step + i) % len(loop), as _show_tiles does.
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pal  # noqa: E402

MAT = r'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Environment/arena_mat.png'
FW, FH, BED = 57, 41, 29
RISE = FH - BED


def tiled(loop, cols, rows, step=0, scale=3, alpha=1.0, mat=True, stride=None):
    """Composite `rows` x `cols` tiles of the loop (frames as lists of strings). stride: offset per row
    (defaults to cols, the flood script's row-major index)."""
    stride = cols if stride is None else stride
    w, h = cols * FW, rows * BED + RISE
    base = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for r in range(rows):
        for c in range(cols):
            fr = loop[(step + r * stride + c) % len(loop)]
            base.alpha_composite(pal.to_image(fr), (c * FW, r * BED))
    if alpha < 1.0:
        a = base.getchannel('A').point(lambda v: int(v * alpha))
        base.putalpha(a)
    if mat:
        m = Image.open(MAT).convert('RGBA')
        bg = Image.new('RGBA', (w, h))
        for yy in range(0, h, m.height):
            for xx in range(0, w, m.width):
                bg.paste(m, (xx, yy))
        bg.alpha_composite(base)
        base = bg
    return base.resize((w * scale, h * scale), Image.NEAREST)


def seam_report(loop, name):
    """How often the colour jumps across a seam, against how often it jumps between two interior columns
    or rows. A seam that shows has a jump rate well above the interior's."""
    order = {k: i for i, k in enumerate(['.', 'q', 'r', 'n', 't', 'N', 'p', 'P', 'Y', 'W', 'a', 'b', 'c', 'd'])}

    def jump(a, b):
        return a != b

    n = len(loop)
    seam_h = seam_v = cnt_h = cnt_v = 0
    for a in range(n):
        for b in range(n):
            A, B = loop[a], loop[b]
            for y in range(12, FH):          # side seam: A's last column against B's first
                cnt_h += 1
                seam_h += jump(A[y][FW - 1], B[y][0])
            for x in range(FW):              # bed seam: A's bottom row against B's top bed row
                cnt_v += 1
                seam_v += jump(A[FH - 1][x], B[12][x])
    int_h = int_v = ci_h = ci_v = 0
    for A in loop:
        for y in range(12, FH):
            for x in range(FW - 1):
                ci_h += 1
                int_h += jump(A[y][x], A[y][x + 1])
        for y in range(12, FH - 1):
            for x in range(FW):
                ci_v += 1
                int_v += jump(A[y][x], A[y + 1][x])
    print('%-10s side seam jumps %5.1f%%  (interior %5.1f%%)   bed seam jumps %5.1f%%  (interior %5.1f%%)'
          % (name, 100.0 * seam_h / cnt_h, 100.0 * int_h / ci_h, 100.0 * seam_v / cnt_v, 100.0 * int_v / ci_v))
