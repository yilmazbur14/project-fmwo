"""matt_mystic_spark.png: a Mystic bolt splashing off the ropes. 12 frames of 24x24 at 0.04 s, one strip:
  frames 0-5    off a TOP rope: the rope is above, the splash sprays down into the ring.
                flip_v for a bottom rope.
  frames 6-11   off a LEFT rope: the exact transpose of 0-5, the splash sprays right into the ring.
                flip_h for a right rope.
A bounce plays the first 4 frames of its set (0-3 or 6-9); the final fizzle plays all 6 (0-5 or 6-11).

The pivot is the frame centre (12, 12): put it on the bolt's position at the bounce. Bolts reflect off
ROPES.grow(-12), so the rope line itself is 12 px (4 texels) beyond the pivot, and the splash flattens
against it there (row 8 in frames 0-5, column 8 in 6-11). The pivot being the frame centre, a flip keeps it
in place and the Sprite2D needs no offset.

The same cyan as the bolt: a white-hot flash against the rope, a bright smear along it, a half-ring and a fan
of droplets spraying back into the ring and cooling as they fly, then (frames 4-5, the fizzle's tail) the
last droplets and motes going out in the far-wisp blue.
"""
import math

import mfx_pal as pal

W = H = 24
CX, CY = 12.0, 12.0          # the pivot (continuous)
WALL = 8                     # the rope's row in the top-rope frames

# Droplets: (angle in degrees from straight down, positive toward +x; speed factor; tail length).
DROPS = [(-82, 1.0, 2), (-55, 1.1, 2), (-28, 0.95, 1), (0, 1.15, 2), (26, 1.0, 1), (54, 1.08, 2),
         (80, 0.95, 2)]
# Distance flown per frame (texels from the splash centre), fast then slowing.
REACH = [0.0, 4.2, 6.6, 8.4, 9.8, 10.8]
# Colour of a droplet's head / tail by frame.
DROP_COL = [None, ('D', 'C'), ('C', 'B'), ('B', 'R'), ('R', None), ('F', None)]


def origin():
    """The splash's centre: just inside the rope, on the pivot's column."""
    return CX, WALL + 1.5


def drop_texels(f):
    out = {}
    if f == 0:
        return out                      # frame 0 is the flash alone
    ox, oy = origin()
    head_k, tail_k = DROP_COL[f]
    for i, (ang, spd, tail) in enumerate(DROPS):
        if f == 5 and i % 2:            # the last frame keeps every other droplet
            continue
        a = math.radians(ang)
        dx, dy = math.sin(a), math.cos(a)
        r = REACH[f] * spd
        hx, hy = ox + dx * r, oy + dy * r
        if hy < WALL + 0.5:              # never behind the rope
            hy = WALL + 0.5
        out[(int(math.floor(hx)), int(math.floor(hy)))] = head_k
        if tail_k:
            for t in range(1, (tail if f < 3 else 1) + 1):
                tx, ty = hx - dx * t, hy - dy * t
                k = (int(math.floor(tx)), int(math.floor(ty)))
                if k not in out and ty >= WALL + 0.5:
                    out[k] = tail_k
    return out


def ring_texels(f):
    """A thin flat half-ring bulging into the ring behind the droplets (frames 2-3), dashed as it cools."""
    radius = {2: 4.4, 3: 6.2}.get(f)
    if radius is None:
        return {}
    k = {2: 'B', 3: 'R'}[f]
    ox, oy = origin()
    out = {}
    steps = 90
    for i in range(steps + 1):
        a = math.pi * i / steps                     # 0..180 degrees, the lower half
        if f == 3 and (i // 8) % 2:
            continue
        x = ox + math.cos(a) * radius * 1.35
        y = oy + math.sin(a) * radius * 0.62
        if y >= WALL + 0.5:
            out[(int(math.floor(x)), int(math.floor(y)))] = k
    return out


def mirrored(rows_left, top):
    """Texels from left-half rows (x 0..11), mirrored about the pivot column line (x' = 23 - x)."""
    out = {}
    for j, r in enumerate(rows_left):
        for x, k in enumerate(r):
            if k != '.':
                out[(x, top + j)] = k
                out[(W - 1 - x, top + j)] = k
    return out


# The flash, drawn by hand as the left half of a starburst flattened against the rope (row 8).
FLASH = {
    0: ['.....BCCDDWW',
        '.......BCDWW',
        '........BCDW',
        '.......B..CD',
        '......B....C',
        '...........B'],
    1: ['..B..BCCDDDD',
        '........CDDW',
        '.........CCD',
        '..........BC',
        '...........B'],
    2: ['.B........BC',
        '..........BB'],
    3: ['............'],
}


def wall_texels(f):
    """The smear along the rope, spreading and breaking up after the flash."""
    spans = {2: [(3, 5, 'B'), (18, 20, 'B'), (7, 8, 'R'), (15, 16, 'R')],
             3: [(1, 2, 'R'), (21, 22, 'R')],
             4: [(0, 0, 'F'), (23, 23, 'F')]}.get(f, [])
    out = {}
    for x0, x1, k in spans:
        for x in range(x0, x1 + 1):
            out[(x, WALL)] = k
    return out


def flash_texels(f):
    return mirrored(FLASH[f], WALL) if f in FLASH else {}


def motes(f):
    """Two specks that outlast the droplets in the fizzle's tail, on the outer droplets' paths."""
    table = {4: [((4, 14), 'F'), ((20, 15), 'F')],
             5: [((2, 13), 'F'), ((22, 12), 'F'), ((12, 22), 'F')]}
    return dict((p, k) for p, k in table.get(f, []))


RANK = {'W': 6, 'D': 5, 'C': 4, 'B': 3, 'R': 2, 'F': 1, '.': 0}


def top_frame(f):
    g = pal.blank(W, H)
    layers = [motes(f), ring_texels(f), drop_texels(f), wall_texels(f), flash_texels(f)]
    for layer in layers:
        for (x, y), k in layer.items():
            if 0 <= x < W and 0 <= y < H and RANK[k] >= RANK[g[y][x]]:
                g[y][x] = k
    return pal.rows(g)


def frames():
    top = [top_frame(f) for f in range(6)]
    side = [pal.transpose(fr) for fr in top]
    return top + side


if __name__ == '__main__':
    for fr in frames()[:6]:
        print('\n'.join(fr))
        print()
