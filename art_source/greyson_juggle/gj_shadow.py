"""Greyson's shadow on the mat while he is in the air: greyson_leap_shadow.

Three frames in one horizontal strip, the same piece the cast has (Mason's, Eric's, Computah's,
Carter's, Matt's): a solid ellipse centred in its frame, so a centred sprite puts it under his feet
point, with the code applying the alpha (their JUGGLE_SHADOW uses 0.35). Frame 0 is him low,
frame 2 him high.

SIZED OFF HIM. His boots stand about 40 texels apart outside to outside, his shoulders with the
delts span about 72, and he is the broadest of the cast, so his low shadow is 64 wide (Matt's is
64, Mason's 54); it narrows to 48 and 32 as he rises, each a quarter as deep as it is wide like the
others'. The frames are 80x20 to hold it (Matt's are 80x24). Pure black #000000: his keyline is pure
black, and so are Mason's, Eric's and Carter's shadows.
"""
W, H, FRAMES = 80, 20, 3
INK = (0, 0, 0, 255)
CLEAR = (0, 0, 0, 0)

# half-width, half-height per frame: low, middle, high
SIZES = ((32.0, 8.0), (24.0, 6.0), (16.0, 4.0))


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
    """-> (rows of RGBA tuples for the whole strip, [(width, height) of each ellipse])."""
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
