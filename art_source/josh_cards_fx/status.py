"""status_icons.png - 24x24 HUD badges for the two phase-2 debuffs, 2x2 grid (48x48).

  frame 0 (row 0, col 0)  stamina drain, dim     frame 1 (row 0, col 1)  stamina drain, lit
  frame 2 (row 1, col 0)  inverted controls, dim frame 3 (row 1, col 1)  inverted controls, lit

Brass bevel + dark navy well, straight out of Assets/UI: the same DB32 brass ramp as the stamina
and hype meters, so these sit in the existing HUD without looking bolted on.
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fxlib import *

S = 24
COLS, ROWS = 2, 2


def badge(c, ox, oy, lit):
    """The brass frame and its navy well.  Returns the set of interior cells."""
    inner = set()
    for y in range(S):
        for x in range(S):
            u, v = (x + 0.5 - S / 2.0) / (S / 2.0 - 2), (y + 0.5 - S / 2.0) / (S / 2.0 - 2)
            au, av = abs(u), abs(v)
            rc = 0.30
            if au > 1 - rc and av > 1 - rc:
                if math.hypot((au - (1 - rc)) / rc, (av - (1 - rc)) / rc) > 1.0:
                    continue
            if au > 1.0 or av > 1.0:
                continue
            l = (-u) * 0.5 + (-v) * 0.5
            if au > 0.82 or av > 0.82:                      # brass bevel
                if l > 0.42:
                    ch = 'T' if lit else 't'
                elif l > -0.05:
                    ch = 't' if lit else 'B'
                else:
                    ch = 'B' if lit else 'b'
            elif au > 0.70 or av > 0.70:                    # dark seat under the bevel
                ch = 'b'
            else:
                inner.add((ox + x, oy + y))
                ch = 'f' if (au > 0.56 or av > 0.56) else 'd'
            c.p[oy + y][ox + x] = ch
    # rivets in the corners, as on the meter frames
    for (rx, ry) in ((5, 5), (S - 6, 5), (5, S - 6), (S - 6, S - 6)):
        c.p[oy + ry][ox + rx] = 'T' if lit else 't'
    outline(c)
    return inner


def glyph_drain(c, inner, ox, oy, lit):
    """A fat down-arrow draining into a drip: 'your stamina is leaking'."""
    # Laid out against the navy well, which is x 5..19 / y 5..19 inside the 24x24 badge - the
    # glyph is sized to that box so nothing is clipped by the brass bevel.
    body = ['h', 'G', 'g'] if lit else ['G', 'g', 'J']
    cells = set()
    cx = ox + 12
    for y in range(oy + 5, oy + 10):                        # shaft
        for x in range(cx - 2, cx + 3):
            cells.add((x, y))
    for k, half in enumerate((5, 4, 3, 2, 1)):              # head
        for x in range(cx - half, cx + half + 1):
            cells.add((x, oy + 9 + k))
    for (x, y) in cells:
        if (x, y) in inner:
            l = (cx - x) * 0.13 + (oy + 12 - y) * 0.10
            c.p[y][x] = body[0] if l > 0.35 else (body[1] if l > -0.30 else body[2])
    # the drips that have already fallen clear of the arrow
    for (dx, dy, r) in ((1, 17, 1.8), (-4, 16, 0.6)):
        for yy in range(oy + dy - 2, oy + dy + 3):
            for xx in range(cx + dx - 2, cx + dx + 3):
                if (xx, yy) in inner and math.hypot(xx - (cx + dx), yy - (oy + dy)) <= r:
                    c.p[yy][xx] = body[1]
                    cells.add((xx, yy))
    _keyline(c, inner, cells)
    return c


def glyph_inverse(c, inner, ox, oy, lit):
    """Two opposing arrows - the same mark as the INVERSE CONTROLS card, shrunk to a badge."""
    hi, lo = ('w', 'P') if lit else ('o', 'p')
    cx, cy = ox + S // 2, oy + S // 2
    all_cells = set()
    for (sign, yoff) in ((-1, -4), (1, 4)):
        cells = set()
        for dx in range(-5, 6):
            for dy in range(-3, 4):
                if abs(dy) <= 1 and (dx * sign) <= 2:
                    cells.add((cx + dx, cy + yoff + dy))
                if (dx * sign) > 1 and abs(dy) <= 3 - ((dx * sign) - 2):
                    cells.add((cx + dx, cy + yoff + dy))
        for (x, y) in cells:
            if (x, y) in inner:
                c.p[y][x] = lo if (x, y + 1) not in cells else hi
        all_cells |= cells
    _keyline(c, inner, all_cells)
    return c


def _keyline(c, inner, cells):
    for (x, y) in cells:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            n = (x + dx, y + dy)
            if n not in cells and n in inner:
                c.p[n[1]][n[0]] = '#'


def build():
    s = Cv(S * COLS, S * ROWS)
    for col, lit in ((0, False), (1, True)):
        inner = badge(s, col * S, 0, lit)
        glyph_drain(s, inner, col * S, 0, lit)
    for col, lit in ((0, False), (1, True)):
        inner = badge(s, col * S, S, lit)
        glyph_inverse(s, inner, col * S, S, lit)
    return s


def cells():
    s = build()
    out = []
    for r in range(ROWS):
        for col in range(COLS):
            cc = Cv(S, S)
            for y in range(S):
                for x in range(S):
                    cc.p[y][x] = s.p[r * S + y][col * S + x]
            out.append(cc)
    return out
