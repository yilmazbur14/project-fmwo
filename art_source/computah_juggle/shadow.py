"""Computah's shadow on the mat while he is in the air.

Three frames of 64x16, the same piece Mason and Eric have: a solid ellipse centred
in its frame, so a centred sprite puts it under his feet point, with the code
applying the alpha (their JUGGLE_SHADOW uses 0.35).  Frame 0 is him low, frame 2 is
him high.

SIZED OFF HIM.  His boots span 41 texels (27.5-68 on his sheets) and his shoulders
-- the pauldron on one side, the cannon's shoulder on the other -- 57, so the low
shadow is 50 wide: between the two, the way Mason's sits between his stance and his
belly.

DRAWN IN HIS KEYLINE, #0C111A, NOT PURE BLACK.  Nothing of his is pure black and
this keeps it that way; at the 0.35 alpha the code applies it is indistinguishable
from black on the mat.
"""
W, H, FRAMES = 64, 16, 3
INK = (0x0C, 0x11, 0x1A, 255)
CLEAR = (0, 0, 0, 0)

# half-width, half-height per frame: low, middle, high
SIZES = ((25.0, 7.0), (18.5, 5.0), (12.5, 3.5))


def frame(rx, ry):
    g = [[CLEAR] * W for _ in range(H)]
    cx, cy = W / 2.0, H / 2.0
    for y in range(H):
        for x in range(W):
            nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            if nx * nx + ny * ny <= 1.0:
                g[y][x] = INK
    return g


def sheet():
    """The strip as rows of RGBA tuples, and the drawn size of each ellipse."""
    grids = [frame(*s) for s in SIZES]
    out = [[CLEAR] * (W * FRAMES) for _ in range(H)]
    sizes = []
    for i, g in enumerate(grids):
        for y in range(H):
            for x in range(W):
                out[y][i * W + x] = g[y][x]
        xs = [x for y in range(H) for x in range(W) if g[y][x][3]]
        ys = [y for y in range(H) for x in range(W) if g[y][x][3]]
        sizes.append((max(xs) - min(xs) + 1, max(ys) - min(ys) + 1))
    return out, sizes
