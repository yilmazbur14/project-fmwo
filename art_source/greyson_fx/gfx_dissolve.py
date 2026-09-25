"""The player disintegrating in the spirit bomb's explosion: a dissolve SHEET built from his own sprite, so it is
texel-true to him. 4 rows (his four facings, from player_4dir_sheet's first frame of each row: down, up, left,
right) x 12 frames of 48x48, at 0.08 s, once (0.96 s), over the explosion layer.
  f0      the blast's light catches him: a cyan rim of light round his silhouette
  f1-9    he comes apart from the top down (the blast is on him): the texels at the dissolving front burn
          white-hot and cyan, then fly off as motes, drifting up and away and thinning in stepped alpha
  f10-11  the last motes thinning out; nothing is left
PIVOT: the frame's centre (24, 24), which is his own frame's centre (16, 16): put it on the player's node with his
sprite's own offset, and hide his sprite on f1.
Built from his sprite's colours plus the crowd's energy ramp (W C A c) for the burning front and the motes.

Proposal: this sheet rather than a shader. It is texel-true (a shader dissolving the sprite at screen res
would cut through texels unless it snaps to the 3x grid), matches the rest of the FX (stepped, no dither),
needs no particle system, and costs 4 x 12 small frames. A shader is the better choice only if the player can
be in any animation frame when it plays; this cutscene can set him to his standing frame first.
"""
import math
import random
import os

from PIL import Image

PLAYER = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'Assets', 'Characters',
                                       'MainPlayer', 'player_4dir_sheet.png'))
W = H = 48
OFF = 8                          # his 32x32 frame sits 8 texels in
FRAMES = 12
ENERGY = {'W': (255, 255, 255), 'C': (230, 247, 255), 'A': (95, 225, 255), 'c': (180, 220, 255)}


def player_frame(row):
    sh = Image.open(PLAYER).convert('RGBA')
    return sh.crop((0, row * 32, 32, row * 32 + 32))


def dissolve_frames(row):
    src = player_frame(row)
    px = src.load()
    texels = [(x, y, px[x, y]) for y in range(32) for x in range(32) if px[x, y][3] > 0]
    ys = [t[1] for t in texels]
    top, bottom = min(ys), max(ys)
    rnd = random.Random(row * 13 + 1)
    # each texel's moment to go: from the top down, with a ragged front
    when = {}
    for (x, y, c) in texels:
        when[(x, y)] = 0.08 + 0.72 * (y - top) / max(1, bottom - top) + rnd.uniform(-0.1, 0.1)
    drift = {(x, y): (rnd.uniform(-10, 18), rnd.uniform(-38, -18)) for (x, y, c) in texels}
    out = []
    for f in range(FRAMES):
        u = f / (FRAMES - 1.0)
        im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        q = im.load()
        solid = set()
        for (x, y, c) in texels:
            t = when[(x, y)]
            if f == 0 or u < t - 0.06:
                q[x + OFF, y + OFF] = c                     # still whole
                solid.add((x + OFF, y + OFF))
            elif u < t:
                q[x + OFF, y + OFF] = ENERGY['W' if (t - u) < 0.03 else 'C'] + (255,)   # the burning front, in bands
                solid.add((x + OFF, y + OFF))
            else:
                age = u - t
                if age > 0.45 or (x * 7 + y * 3) % 3 == 0:
                    continue                                 # a third never become motes; the rest burn out
                dx, dy = drift[(x, y)]
                mx, my = int(x + OFF + dx * age), int(y + OFF + dy * age)
                if 1 <= mx < W - 1 and 1 <= my < H - 1:          # a mote at the edge has gone
                    a = 255 if age < 0.15 else (176 if age < 0.3 else 96)
                    col = ENERGY['A' if age > 0.2 else 'C']
                    q[mx, my] = col + (a,)
        if f == 0:
            # the blast's light: a cyan rim round his silhouette
            for (sx, sy) in list(solid):
                for (ax, ay) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    n = (sx + ax, sy + ay)
                    if n not in solid and 0 <= n[0] < W and 0 <= n[1] < H and q[n][3] == 0:
                        q[n] = ENERGY['A'] + (176,)
        out.append(im)
    return out


def sheet():
    rows = [dissolve_frames(r) for r in range(4)]
    im = Image.new('RGBA', (W * FRAMES, H * 4), (0, 0, 0, 0))
    for r, frames in enumerate(rows):
        for f, fr in enumerate(frames):
            im.paste(fr, (f * W, r * H))
    return im
