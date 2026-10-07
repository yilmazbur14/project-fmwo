"""The void maze wall block (approval pass): demon-god Jordan's obsidian, edged in his rune light.

One 3/4-view floor block: a 32x20 top face (rows 0-19, row 19 its front edge) over a front face
of FH rows. The contract (take A) is FH = 16: 32x36 texels, anchor (16,35). Take B is the same
block with a lower front face. Eight frames in a horizontal strip: 0-3 rise out of the floor,
4 stands, 5-7 vanish.

Everything is a dict canvas {(x, y): key}; keys map to colours through PAL. The colours are the
god's own: his obsidian plate ramp (jordan_god/jg_lord_pal.py LORD '1'-'5') and the rune circle's
four blues (jordan_god/jg_runes.py RUNE_PAL). Nothing in this module writes a file.
"""
import sys

sys.dont_write_bytecode = True


def hx(s):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


W = 32
TOP = 20                      # top face rows 0-19 (row 19 is its front edge)
N = 8
RISE, STAND, VANISH = (0, 1, 2, 3), 4, (5, 6, 7)

PAL = {
    'k': hx('000000'),        # keyline: pure black (the god's, measured on Jordan's v2 sheet)
    # obsidian, dark -> light (the god's plate ramp)
    '1': hx('0D0B12'), '2': hx('19151F'), '3': hx('28222F'), '4': hx('3B3346'), '5': hx('564B63'),
    # rune light, dim -> hot (the rune circle's four blues, exactly)
    'd': hx('17385A'), 'e': hx('2B6C99'), 'f': hx('66C6EC'), 'g': hx('D2F6FF'),
}
OBSIDIAN = '12345'
RUNE = 'defg'
BRIGHTER = {'d': 'e', 'e': 'f', 'f': 'g', 'g': 'g'}
DIMMER = {'g': 'f', 'f': 'e', 'e': 'd', 'd': 'd'}


def size(fh):
    return (W, TOP + fh)


def anchor(fh):
    return (W // 2, TOP + fh - 1)


# ------------------------------------------------------------------ the standing block

# The top face (interior x 2..29, y 2..17): black glass. One broad sheen crosses it from the
# back-left as an exact 2:1 pixel diagonal (u = x + 2y is constant along it), with a crisp lit
# edge on the side toward the house light (upper-left) and one hot point of gloss.
# The front two rows sink a step darker so the lit lip in front of them carries the shape.
SHEEN = (9.0, 21.0)                 # the band, in u
SHEEN_EDGE = 1                      # the lit edge: its near 2 u-steps (one 2-px step per row)
GLOSS = (10, 3)                     # the hottest point, on the lit edge
MOTES = ((24, 5), (27, 9), (19, 13), (12, 12))  # the void's motes, reflected

# The front face (interior x 2..29, y 21..34), drawn for the full 16 rows; a lower take drops
# rows from its middle. Solid volcanic glass: a lit bevel under the lip with a glint by the lit
# corner, then plain glass sinking into shadow at the floor.
FRONT = [
    # x = 2..29
    '3344333333333333333333333333',  # 21 the bevel under the lip
    '2222222222222222222222222222',  # 22
    '2222222222222222222222222222',  # 23
    '2222222222222222222222222222',  # 24
    '2222222222222222222222222222',  # 25
    '2222222222222222222222222222',  # 26
    '2222222222222222222222222222',  # 27
    '2222222222222222222222222222',  # 28
    '2222222222222222222222222222',  # 29
    '2222222222222222222222222222',  # 30
    '1212121212121212121212121212',  # 31 the floor shadow, dithered in
    '1111111111111111111111111111',  # 32
    '1111111111111111111111111111',  # 33
    '1111111111111111111111111111',  # 34
]
DROP_FROM = 26                      # a lower take removes (cut - 1) rows from here, and one of the floor-shadow rows

DARKER = {'5': '4', '4': '3', '3': '2', '2': '1', '1': '1'}


def stand16(bleed=True):
    """The contract block, 32x36."""
    last = 35
    px = {}
    # --- top face interior (x 2..29, y 2..17)
    lo, hi = SHEEN
    for x in range(2, W - 2):
        for y in range(2, TOP - 2):
            u = (x - 2) + 2 * (y - 2)
            k = '2'
            if lo <= u <= hi:
                k = '4' if u <= lo + SHEEN_EDGE else '3'
            if y >= 16:
                k = DARKER[k]
            px[(x, y)] = k
    for p in MOTES:
        if px[p] == '2':
            px[p] = '3'
    px[GLOSS] = '5'
    # --- front face interior (x 2..29, y 21..34)
    for r, row in enumerate(FRONT):
        assert len(row) == 28, (r, len(row))
        for c, ch in enumerate(row):
            px[(2 + c, 21 + r)] = ch
    # --- rune light on the edges (inside the keyline, as on the god's armour)
    for x in range(1, W - 1):
        px[(x, 1)] = 'e'                     # back rim: mid (the corners stay dim, below)
        px[(x, TOP - 1)] = 'f'               # the top face's front edge: the brightest line
    for y in range(1, TOP - 1):              # side rims: dim at the back, brightening forward
        k = 'd' if y <= 9 else ('e' if y <= 15 else 'f')
        px[(1, y)] = k
        px[(W - 2, y)] = k
    px[(1, TOP - 1)] = px[(W - 2, TOP - 1)] = 'g'   # hot corners, like the circle's flecks
    for x in (4, 5, 6):                      # a hot run along the lip near the lit corner
        px[(x, TOP - 1)] = 'g'
    for x in range(2, W - 2):                # the lip's light spilling onto both faces
        if bleed:
            px[(x, TOP - 2)] = 'd'
            px[(x, TOP)] = 'd'
        else:
            px[(x, TOP - 2)] = '1'
            px[(x, TOP)] = '2'
    for y in range(TOP, last):               # front corners: dim, dying out toward the floor
        k = 'e' if y == TOP else ('d' if y <= 27 else '1')
        px[(1, y)] = k
        px[(W - 2, y)] = k
    # --- the keyline, all round
    for x in range(W):
        px[(x, 0)] = 'k'
        px[(x, last)] = 'k'
    for y in range(last + 1):
        px[(0, y)] = 'k'
        px[(W - 1, y)] = 'k'
    return px


def stand(fh=16, bleed=True):
    """The standing block with a front face of fh rows: the contract's, with 16 - fh rows taken
    out of the front face (from its middle, and one floor-shadow row), so a lower take is exactly
    the same block, shorter."""
    px = stand16(bleed)
    cut = 16 - fh
    if cut <= 0:
        return px
    drop = set(range(DROP_FROM, DROP_FROM + cut - 1)) | {33}
    out = {}
    for (x, y), k in px.items():
        if y in drop:
            continue
        out[(x, y - sum(1 for d in drop if d < y))] = k
    return out


# ------------------------------------------------------------------ the other frames

def recolour(px, table):
    return {p: table.get(k, k) for p, k in px.items()}


def rise(px, h, fh):
    """The block at height h (0..fh): the standing art pushed down fh-h rows and cut at the floor
    line, which is exactly what a block rising out of a floor-sized hole shows in 3/4. The cut is
    the hole's front lip, lit from below by the rune light."""
    Wd, Hd = size(fh)
    last = Hd - 1
    s = fh - h
    out = {}
    for (x, y), k in px.items():
        if y + s <= last:
            out[(x, y + s)] = k
    if s > 0:
        for x in range(W):
            out[(x, last)] = 'g' if 3 <= x <= W - 4 else 'f'
        for x in range(1, W - 1):
            if out.get((x, last - 1)) in OBSIDIAN:
                out[(x, last - 1)] = 'e'
            if out.get((x, last - 2)) in OBSIDIAN and x % 2 == 0:
                out[(x, last - 2)] = 'd'
    return out


def _hash(x, y, seed):
    """A fixed pseudo-random value in [0, 1) for a texel (deterministic, no RNG state)."""
    h = (x * 374761393 + y * 668265263 + seed * 2246822519) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65536.0


def chunk(x, y, seed):
    """The same value for every texel of a 2x2 chunk, so the glass breaks away in pieces (6x6 px
    at the game's scale) instead of a single-texel checker."""
    return _hash(x // 2, y // 2, seed)


# the sparks that lift off the breaking block (texel, key), by vanish frame
SPARKS = {
    6: [((9, 6), 'g'), ((22, 3), 'f'), ((15, 11), 'f'), ((27, 8), 'g')],
    7: [((8, 2), 'f'), ((21, 1), 'g'), ((14, 5), 'g'), ((26, 3), 'f'), ((4, 9), 'f')],
}


def vanish(s, frame):
    """Frames 5-7: the glass breaks away in chunks while its rune lines flicker and fail."""
    out = {}
    if frame == 5:       # the flicker: every line flares a step, the first chunks go
        for (x, y), k in s.items():
            if k in RUNE:
                out[(x, y)] = BRIGHTER[k]
            elif chunk(x, y, 1) >= 0.22:
                out[(x, y)] = k
    elif frame == 6:     # most of the glass gone, the lines back to rest and breaking up
        for (x, y), k in s.items():
            if k in RUNE:
                if _hash(x, y, 2) >= 0.22:
                    out[(x, y)] = k
            elif chunk(x, y, 1) >= 0.64:
                out[(x, y)] = k
    else:                # a ghost of the lines, dimmed and broken, and the last sparks
        for (x, y), k in s.items():
            if k in RUNE and _hash(x, y, 3) < 0.42:
                out[(x, y)] = DIMMER[k]
    for p, k in SPARKS.get(frame, ()):
        out[p] = k
    return out


def frames_heights(fh=16):
    """How high the block stands on rise frames 0-2 (it is fully up on frame 3): quick out of the
    floor, easing into place."""
    return [1, round(fh * 0.4), round(fh * 0.78)]


def frames(fh=16, bleed=True):
    s = stand(fh, bleed)
    out = [rise(s, h, fh) for h in frames_heights(fh)]
    out.append(recolour(s, BRIGHTER))        # 3: it locks in place and every rune line flares
    out.append(s)                            # 4: standing
    out += [vanish(s, f) for f in VANISH]    # 5-7
    return out


def dump(px, fh=16):
    Wd, Hd = size(fh)
    return '\n'.join('%2d ' % y + ''.join(px.get((x, y), '.') for x in range(Wd)) for y in range(Hd))


if __name__ == '__main__':
    print(dump(stand()))
