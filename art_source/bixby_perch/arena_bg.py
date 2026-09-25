"""A 1920x1080 still of the Liam fight's arena, built from its own textures with the layout in
Scenes/Core/ArenaScene.tscn (read, not changed), for placing the perch frames at game scale. It has no
boss in it, which no capture does.

Layers, back to front: black, ringside (3x from the origin), crowd frame 0 (3x, centred on (960, 60)),
mat (3x at (111, 114)), and the ropes. The top rope is two halves with the gate's doorway at x 852..1067
between them; the Liam fight never opens the gate, so the doorway is empty.
"""
import os

from PIL import Image

from common import ROOT

ENV = os.path.join(ROOT, 'Assets', 'Environment')
TOP_ROPE_Y = 100
DOOR = (852, 1068)          # the top rope's doorway, [start, end)
HUD_BAR = (720, 100, 1200, 154)
HUD_PLATE = (816, 3, 1104, 81)


def up(im, s):
    return im.resize((im.width * s, im.height * s), Image.NEAREST)


def rope_band(img, y_white, x0, x1):
    """Black 7 px, white 7 px, black 7 px, as measured on a capture."""
    px = img.load()
    for i in range(21):
        y = y_white - 7 + i
        col = (255, 255, 255, 255) if 7 <= i < 14 else (0, 0, 0, 255)
        for x in range(max(0, x0), min(img.width, x1)):
            px[x, y] = col


def arena(ropes=True):
    out = Image.new('RGBA', (1920, 1080), (0, 0, 0, 255))
    ring = Image.open(os.path.join(ENV, 'arena_ringside.png')).convert('RGBA')
    out.alpha_composite(up(ring, 3), (0, 0))
    crowd = Image.open(os.path.join(ENV, 'crowd_v2.png')).convert('RGBA')
    fw = crowd.width // 5
    c0 = up(crowd.crop((0, 0, fw, crowd.height)), 3)
    out.alpha_composite(c0, (960 - c0.width // 2, 60 - c0.height // 2))
    mat = Image.open(os.path.join(ENV, 'arena_mat.png')).convert('RGBA')
    out.alpha_composite(up(mat, 3), (111, 114))
    if ropes:
        top_ropes(out)
    return out


def top_ropes(img):
    rope_band(img, TOP_ROPE_Y, 109, DOOR[0])
    rope_band(img, TOP_ROPE_Y, DOOR[1], 1806)


if __name__ == '__main__':
    from common import SCRATCH
    a = arena()
    a.save(SCRATCH + 'arena_bg.png')
    # check against a real capture where no boss is drawn: the top right of the arena
    cap = os.path.join(os.path.dirname(SCRATCH.rstrip('/')), 'full2', 'red_fire.png')
    if os.path.exists(cap):
        c = Image.open(cap).convert('RGBA')
        box = (1260, 0, 1800, 560)
        side = Image.new('RGBA', (2 * (box[2] - box[0]) + 10, box[3] - box[1]), (255, 0, 255, 255))
        side.alpha_composite(a.crop(box), (0, 0))
        side.alpha_composite(c.crop(box), (box[2] - box[0] + 10, 0))
        side.save(SCRATCH + 'arena_bg_vs_capture.png')
        diff = sum(1 for p, q in zip(a.crop(box).getdata(), c.crop(box).getdata()) if p[:3] != q[:3])
        print('differing px in the check box:', diff, 'of', (box[2] - box[0]) * (box[3] - box[1]))
