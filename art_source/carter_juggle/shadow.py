"""Carter's shadow on the mat while he is in the air.

Three frames of 64x16, the same piece Mason and Eric have: a solid ellipse centred in its frame, so a
centred sprite puts it under his feet point, with the code applying the alpha (their JUGGLE_SHADOW uses
0.35).  Frame 0 is him low, frame 2 is him high.

SIZED OFF HIM.  His three-quarter stance spans about 32-40 texels between the heels and his shoulders,
caps included, about 50; the low shadow is 44 wide, between the two.  Pure black #000000: his keyline is
pure black, and so are Mason's and Eric's shadows.
"""
W, H, FRAMES = 64, 16, 3
INK = (0, 0, 0, 255)
CLEAR = (0, 0, 0, 0)

# half-width, half-height per frame: low, middle, high
SIZES = ((22.0, 6.5), (16.5, 4.8), (11.0, 3.4))


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
