"""One rotated-card primitive, shared by the bomb card, the thrown card and the special cards.

Every card in the fight is the same object seen at a different angle, so they all come out of
this function: a rotated rounded rectangle with a cream face, a gold rim, a red spade pip and a
1px black outline.  `squash` narrows the card about its own long axis, which is what sells a
tumble - at squash ~0.1 the card is edge-on and reads as a bright sliver.
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fxlib import *

SPADE_PIP = [
    '.#.',
    '###',
    '.#.',
]
SPADE_PIP5 = [
    '..#..',
    '.###.',
    '#####',
    '#####',
    '#.#.#',
    '..#..',
]


def card_uv(c, cx, cy, hw, hh, ang):
    """Every covered pixel -> its (u, v) in card space, u across, v along."""
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    r = math.hypot(hw, hh) + 2
    out = {}
    for y in range(max(0, int(cy - r)), min(c.h, int(cy + r) + 1)):
        for x in range(max(0, int(cx - r)), min(c.w, int(cx + r) + 1)):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            u = dx * ca + dy * sa
            v = -dx * sa + dy * ca
            if abs(u) > hw or abs(v) > hh:
                continue
            # rounded corners, scaled so a squashed card doesn't lose its whole width
            rc = min(1.6, hw * 0.55)
            if abs(u) > hw - rc and abs(v) > hh - rc:
                if math.hypot(abs(u) - (hw - rc), abs(v) - (hh - rc)) > rc:
                    continue
            out[(x, y)] = (u / max(0.001, hw), v / max(0.001, hh))
    return out


def draw_card(c, cx, cy, hw, hh, ang, squash=1.0, back=False, pip='R',
              glow=0.0, dim=0.0, outline_col='#'):
    """Draw one card.  `back` paints Josh's red card back instead of a cream face.
    `glow` 0..1 adds a gold bloom hugging the card.  `dim` 0..1 darkens the whole face."""
    hw = max(0.6, hw * squash)
    uv = card_uv(c, cx, cy, hw, hh, ang)
    if not uv:
        return set()
    thin = hw < 2.2                                  # nearly edge-on: read it as a lit sliver
    cells = set(uv.keys())

    for (x, y), (u, v) in uv.items():
        au, av = abs(u), abs(v)
        edge = max(au, av * (hw / max(0.001, hh)) if hh > hw else av)
        if thin:
            ch = 'n' if u < 0.1 else 'N'
            if av > 0.86:
                ch = 'D'
            c.p[y][x] = ch
            continue
        # gold rim just inside the outline
        if au > 0.80 or av > 0.90:
            ch = 'D' if (u < 0.15 or v < -0.15) else 'A'
        elif back:
            # red back with a cream lattice
            lat = (abs((u * 3.1 + v * 4.3) % 1.0 - 0.5) + abs((u * 3.1 - v * 4.3) % 1.0 - 0.5)) > 0.62
            ch = 'u' if lat else ('Q' if (u * 0.6 + v * 0.4) < 0.25 else 'q')
        else:
            ch = 'n' if (u * 0.55 + v * 0.45) < 0.10 else 'N'
        if dim > 0:
            ch = {'n': 'N', 'N': 'u', 'u': 'U', 'D': 'A', 'A': 'K',
                  'Q': 'q', 'q': 'L'}.get(ch, ch) if dim > 0.5 else ch
        c.p[y][x] = ch

    # centre pip.  `pip` must be tested: without it a pip=None caller writes None into the
    # canvas, and Cv.set silently drops those, punching pip-shaped transparent holes in the
    # card - which is exactly what happened to the bomb's shrapnel.
    if pip and not thin and not back and hh >= 4:
        art = SPADE_PIP5 if hh >= 9 and hw >= 5.5 else SPADE_PIP
        ph, pw = len(art), len(art[0])
        a = math.radians(ang)
        ca, sa = math.cos(a), math.sin(a)
        for j in range(ph):
            for i in range(pw):
                if art[j][i] != '#':
                    continue
                u = (i - (pw - 1) / 2.0) * min(1.0, hw / (pw * 0.62))
                v = j - (ph - 1) / 2.0
                x = int(round(cx + u * ca - v * sa))
                y = int(round(cy + u * sa + v * ca))
                if (x, y) in cells:
                    c.p[y][x] = pip

    # outline FIRST, bloom after: the black keeps the card's shape crisp inside its own glow
    if outline_col:
        _outline_cells(c, cells, outline_col)
    if glow > 0.0:
        card_glow(c, cx, cy, hw + 1.0, hh + 1.0, ang, glow)
    return cells


def _outline_cells(c, cells, col):
    nb = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)]
    add = []
    for (x, y) in cells:
        for dx, dy in nb:
            nx, ny = x + dx, y + dy
            if (nx, ny) in cells or not c.inb(nx, ny):
                continue
            add.append((nx, ny))
    for x, y in add:
        c.p[y][x] = col


def card_glow(c, cx, cy, hw, hh, ang, amp=1.0, reach=3.6, ramp=('A', 'D', 'F', 'Y')):
    """Gold bloom that hugs the card rectangle, so the card's shape survives the glow."""
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    r = math.hypot(hw, hh) + reach + 2
    for y in range(max(0, int(cy - r)), min(c.h, int(cy + r) + 1)):
        for x in range(max(0, int(cx - r)), min(c.w, int(cx + r) + 1)):
            if c.p[y][x] != '.':
                continue
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            u = dx * ca + dy * sa
            v = -dx * sa + dy * ca
            d = math.hypot(max(0.0, abs(u) - hw), max(0.0, abs(v) - hh))
            val = amp * max(0.0, 1.0 - d / reach) ** 1.4
            if (x * 7 + y * 13) % 5 == 0:
                val *= 0.78
            i = int(val * len(ramp))
            if i <= 0:
                continue
            c.p[y][x] = ramp[min(i - 1, len(ramp) - 1)]
    return c


def flat_card(c, cx, cy, rx, ry, tone='n', shade='N', rim='D', pip='R', glowc=None):
    """A card lying flat on the ground: a squat ellipse-ish slab with a 1px stock edge, so the
    landed bomb reads as being ON the floor rather than floating."""
    cells = set()
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if not c.inb(x, y):
                continue
            u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            if abs(u) ** 5.0 + abs(v) ** 5.0 > 1.0:     # a rounded RECTANGLE, not an oval
                continue
            cells.add((x, y))
            if abs(u) > 0.84 or abs(v) > 0.74:
                c.p[y][x] = rim
            else:
                c.p[y][x] = tone if (u * 0.5 + v * 0.5) < 0.05 else shade
    # the stock's near edge, one row under the slab
    for x in range(int(cx - rx), int(cx + rx) + 1):
        col = [y for (xx, y) in cells if xx == x]
        if col:
            c.set(x, max(col) + 1, 'U')
            cells.add((x, max(col) + 1))
    if pip:
        for j, row in enumerate(SPADE_PIP):
            for i, s in enumerate(row):
                if s == '#':
                    c.set(int(cx) - 1 + i, int(cy) - 2 + j, pip)
    if glowc:
        for (x, y) in list(cells):
            pass
    _outline_cells(c, cells, '#')
    return cells
