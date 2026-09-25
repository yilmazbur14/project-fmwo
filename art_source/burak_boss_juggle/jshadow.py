"""Captain Burak's mat shadow while he is in the air: burak_boss_leap_shadow.png.

Three frames of 64x16, the same piece Mason and Eric have: a solid pure-black ellipse centred in its
frame so it sits under the feet point, the code applying the alpha (their JUGGLE_SHADOW uses 0.35).
Frame 0 is him low, frame 2 is him high.

Sized off Burak: his boots stand 33 texels wide but his greatcoat's hem is 41, so the low frame is
46px, a touch wider than the coat, like Eric's is a touch wider than his stance.
"""
import os
import sys

sys.dont_write_bytecode = True

W, H, FRAMES = 64, 16, 3
SIZES = ((23.0, 7.0), (17.0, 5.5), (11.5, 4.0))      # half-width, half-height: low, middle, high


def frames():
    out = []
    for (rx, ry) in SIZES:
        px = {}
        cx, cy = W / 2.0, H / 2.0
        for y in range(H):
            for x in range(W):
                nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
                if nx * nx + ny * ny <= 1.0:
                    px[(x, y)] = 'k'
        out.append(px)
    return out


def sheet_px():
    px = {}
    for i, f in enumerate(frames()):
        for (x, y), k in f.items():
            px[(i * W + x, y)] = k
    return px
