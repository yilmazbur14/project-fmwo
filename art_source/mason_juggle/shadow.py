"""Mason's mat shadow while he is in the air.

Three frames of 64x16, the same piece Eric has: a solid pure-black ellipse,
centred in its frame so it sits under the feet point, with the code applying the
alpha (Eric's JUGGLE_SHADOW uses 0.35).  Frame 0 is him low, frame 2 is him high.

Sized off Mason rather than off Eric.  Eric's frames are 48x16 and his widest
ellipse is 44px, a touch wider than his 44-texel stance.  Mason's stance is only
40 texels but his belly overhangs it to 58, so his low frame is 54px -- a wider,
flatter ellipse than the knight's, which is the point: the shadow should say
"something heavy is up there" before you look up.
"""
import os

from zoom import write_png

W, H, FRAMES = 64, 16, 3
BLACK = (0, 0, 0, 255)
CLEAR = (0, 0, 0, 0)

# half-width, half-height per frame: low, middle, high
SIZES = ((27.0, 7.5), (20.0, 5.5), (13.5, 4.0))


def frame(rx, ry):
    g = [[CLEAR] * W for _ in range(H)]
    cx, cy = W / 2.0, H / 2.0
    for y in range(H):
        for x in range(W):
            nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            if nx * nx + ny * ny <= 1.0:
                g[y][x] = BLACK
    return g


def build(out_dir):
    grids = [frame(*s) for s in SIZES]
    out = [[CLEAR] * (W * FRAMES) for _ in range(H)]
    for i, g in enumerate(grids):
        for y in range(H):
            for x in range(W):
                out[y][i * W + x] = g[y][x]
    path = os.path.join(out_dir, 'mason_leap_shadow.png')
    write_png(path, W * FRAMES, H, out)
    sizes = []
    for g in grids:
        xs = [x for y in range(H) for x in range(W) if g[y][x][3]]
        ys = [y for y in range(H) for x in range(W) if g[y][x][3]]
        sizes.append('%dx%d' % (max(xs) - min(xs) + 1, max(ys) - min(ys) + 1))
    print('wrote mason_leap_shadow.png %dx%d (%d frames of %dx%d, ellipses %s)'
          % (W * FRAMES, H, FRAMES, W, H, ' '.join(sizes)))
    return path
