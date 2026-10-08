"""void_bg: the void Jordan ascends into (the contract: 640x360, opaque, full screen, no floor line
or ropes; the fight uses the whole screen). Drawn for the approval mocks; static, so nothing in
it flickers.

Deep indigo with depth: a dim violet swell behind where he hovers, darkening to near-black at the
edges in dithered steps, a few faint drifting wisps, and motes at three depths."""
import math
import os
import random
import sys

sys.dont_write_bytecode = True
from PIL import Image  # noqa: E402

W, H = 640, 360

STEPS = [(4, 3, 10), (8, 6, 17), (13, 9, 26), (19, 13, 36), (26, 17, 47)]   # dark -> light
WISP = (34, 22, 58)
MOTES = [(46, 34, 84), (86, 70, 150), (170, 154, 236)]                        # far, mid, near

# where the swell of light sits (native texels): behind his chest, where the core burns
GLOW = (320, 110)


def backdrop(seed=4):
    im = Image.new('RGBA', (W, H), STEPS[0] + (255,))
    px = im.load()
    for y in range(H):
        for x in range(W):
            # an elliptical falloff from the glow, wider than tall
            d = math.hypot((x - GLOW[0]) / 330.0, (y - GLOW[1]) / 250.0)
            f = max(0.0, 1.0 - d) * (len(STEPS) - 1) * 1.08
            i = int(f)
            frac = f - i
            # ordered dither across each band edge (2x2 Bayer)
            bayer = ((0, 2), (3, 1))[y % 2][x % 2] / 4.0 + 0.125
            j = min(len(STEPS) - 1, i + (1 if frac > bayer and frac > 0.35 and frac < 0.65 or frac >= 0.65 else 0))
            px[x, y] = STEPS[j] + (255,)
    rnd = random.Random(seed)
    # faint wisps: long thin drifting curves
    for w in range(9):
        cx = rnd.uniform(40, W - 40)
        cy = rnd.uniform(30, H - 30)
        ln = rnd.uniform(60, 150)
        amp = rnd.uniform(3, 9)
        ph = rnd.uniform(0, 6.28)
        for t in range(int(ln)):
            x = int(cx - ln / 2 + t)
            y = int(cy + amp * math.sin(t / 18.0 + ph))
            if 0 <= x < W and 0 <= y < H and (t % 5) != 0:
                c = px[x, y][:3]
                if c in (STEPS[1], STEPS[2], STEPS[3]):
                    px[x, y] = WISP + (255,)
    # motes at three depths: many dim far ones, fewer mid, a handful of near 2px ones
    for i in range(520):
        x, y = rnd.randrange(W), rnd.randrange(H)
        r = rnd.random()
        if r < 0.72:
            px[x, y] = MOTES[0] + (255,)
        elif r < 0.95:
            px[x, y] = MOTES[1] + (255,)
        else:
            px[x, y] = MOTES[2] + (255,)
            if x + 1 < W:
                px[x + 1, y] = MOTES[1] + (255,)
            if y + 1 < H:
                px[x, y + 1] = MOTES[1] + (255,)
    return im


if __name__ == '__main__':
    out = sys.argv[1]
    im = backdrop()
    im.save(os.path.join(out, 'void_bg_1x.png'))
    im.resize((1920, 1080), Image.NEAREST).save(os.path.join(out, 'void_bg_3x.png'))
