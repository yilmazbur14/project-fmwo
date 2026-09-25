"""Text-grid sprites: one character per texel, mapped through a legend.

    stamp(im, GRID, LEGEND, at)     '.' leaves the canvas alone, ' ' clears it
"""
from PIL import Image


def rgba(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def rows(grid):
    lines = [ln for ln in grid.strip("\n").split("\n")]
    w = max(len(ln) for ln in lines)
    return [ln.ljust(w, ".") for ln in lines]


def stamp(im, grid, legend, at):
    px = im.load()
    ox, oy = at
    for y, ln in enumerate(rows(grid)):
        for x, ch in enumerate(ln):
            if ch == ".":
                continue
            X, Y = ox + x, oy + y
            if 0 <= X < im.width and 0 <= Y < im.height:
                px[X, Y] = (0, 0, 0, 0) if ch == " " else rgba(legend[ch])
    return im


def check(grid, name="grid"):
    """Every row the same width - a ragged row is the classic grid typo."""
    lines = grid.strip("\n").split("\n")
    widths = {len(ln) for ln in lines}
    if len(widths) != 1:
        bad = [(i, len(ln)) for i, ln in enumerate(lines) if len(ln) != max(widths)]
        raise ValueError("%s: ragged rows %s" % (name, bad[:6]))
    return len(lines[0]), len(lines)
