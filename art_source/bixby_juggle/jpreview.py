"""Previews, into the scratchpad only (jcommon.SCRATCH):

  bixby_juggle_4x.png        the 12 frames in one strip at 4x (and a 4x grid, easier to view)
  bixby_juggle_game.gif      the whole sequence at game scale (3 px a texel) over the arena mat, the
                             player for scale: the hit, the tumble looping twice while he rises and falls
                             on a ballistic arc (the finisher's gravity), the crash, then the lying loop
  bixby_juggle_game_*.png    stills from the GIF

The arena is built from its own textures the way Scenes/Core/ArenaScene.tscn lays them out (black,
ringside 3x, crowd frame 0, mat 3x at (111, 114)), read-only.
"""
import os

from PIL import Image

import jcommon as C
import jrot
import jshadow

ENV = os.path.join(C.ROOT, 'Assets', 'Environment')
PLAYER = os.path.join(C.ROOT, 'Assets', 'Characters', 'MainPlayer')
S = 3
FEET_AT = (960, 780)            # his feet on screen
SHADOW_ALPHA = 0.38             # BixbyBeastArtLayout.SHADOW_ALPHA
SHADOW_STEP = 70.0              # px of lift per shadow frame (a suggestion for the coder)
WINDOW = (960 - 450, 90, 960 + 450, 990)


def up(im, s):
    return im.resize((im.width * s, im.height * s), Image.NEAREST)


def arena():
    out = Image.new('RGBA', (1920, 1080), (0, 0, 0, 255))
    ring = Image.open(os.path.join(ENV, 'arena_ringside.png')).convert('RGBA')
    out.alpha_composite(up(ring, 3), (0, 0))
    crowd = Image.open(os.path.join(ENV, 'crowd_v2.png')).convert('RGBA')
    fw = crowd.width // 5
    c0 = up(crowd.crop((0, 0, fw, crowd.height)), 3)
    out.alpha_composite(c0, (960 - c0.width // 2, 60 - c0.height // 2))
    mat = Image.open(os.path.join(ENV, 'arena_mat.png')).convert('RGBA')
    out.alpha_composite(up(mat, 3), (111, 114))
    return out


def player_frames():
    upc = Image.open(os.path.join(PLAYER, 'player_uppercut.png')).convert('RGBA')
    ups = [up(upc.crop((i * 48, 0, i * 48 + 48, 64)), 3) for i in range(10)]
    four = Image.open(os.path.join(PLAYER, 'player_4dir_sheet.png')).convert('RGBA')
    idle_back = up(four.crop((0, 32, 32, 64)), 3)
    return ups, idle_back


def shadow_img(lift):
    i = max(0, min(2, int(lift / SHADOW_STEP)))
    f = jshadow.frames()[i]
    a = f.split()[3].point(lambda v: int(v * SHADOW_ALPHA))
    g = Image.new('RGBA', f.size, (0, 0, 0, 0))
    g.putalpha(a)
    return up(g, S)


def compose(bg, frame_img, lift, show_shadow, player=None, player_at=None):
    im = bg.copy()
    if show_shadow:
        sh = shadow_img(lift)
        im.alpha_composite(sh, (FEET_AT[0] - jshadow.CX * S, FEET_AT[1] - jshadow.CY * S))
    big = up(frame_img, S)
    tl = (FEET_AT[0] - C.FEET[0] * S, int(round(FEET_AT[1] - C.FEET[1] * S - lift)))
    # the player stands in front of him (lower on screen), so he is drawn after
    im.alpha_composite(big, (tl[0], max(0, tl[1])), (0, max(0, -tl[1])))
    if player is not None:
        im.alpha_composite(player, player_at)
    return im.crop(WINDOW)


def timeline(frames, holds):
    """[(frame index, seconds, lift px, shadow?, player)] for the GIF: the air phase cut into equal steps
    of about 35 ms (never under 20: GIF players clamp shorter delays) so the arc reads smoothly while
    each drawing is held its own time."""
    T_AIR = holds[1] + 2 * sum(holds[2:7])
    apex = 190.0
    g = 8 * apex / (T_AIR ** 2)
    v0 = 4 * apex / T_AIR
    seq = [(0, holds[0], 0.0, False, 'hit')]
    t = 0.0
    air = [1] + [2, 3, 4, 5, 6] * 2
    for fi in air:
        n = max(1, int(round(holds[fi] / 0.035)))
        dt = holds[fi] / n
        for _ in range(n):
            lift = max(0.0, v0 * t - 0.5 * g * t * t)
            seq.append((fi, dt, lift, lift > 0.5, 'lift' if fi == 1 else 'idle'))
            t += dt
    for fi in (7, 8, 9):
        seq.append((fi, holds[fi], 0.0, False, 'idle'))
    for _ in range(3):
        seq.append((10, holds[10], 0.0, False, 'idle'))
        seq.append((11, holds[11], 0.0, False, 'idle'))
    return seq


def gif(frames, holds, path):
    bg = arena()
    ups, idle = player_frames()
    imgs = [jrot.to_img(a) for a in frames]
    # where the player stands for the uppercut: in front of him, under his chest
    px_up = (FEET_AT[0] - 110, FEET_AT[1] - 150)
    px_idle = (FEET_AT[0] - 150, FEET_AT[1] + 34)
    out, durs = [], []
    for fi, dt, lift, sh, who in timeline(frames, holds):
        if who == 'hit':
            p, at = ups[5], px_up
        elif who == 'lift':
            p, at = ups[7], (px_up[0], px_up[1] - 20)
        else:
            p, at = idle, px_idle
        out.append(compose(bg, imgs[fi], lift, sh, p, at).convert('RGB'))
        durs.append(int(round(dt * 1000)))
    out[0].save(path, save_all=True, append_images=out[1:], duration=durs, loop=0, optimize=True)
    return out


def strip(frames, s=4):
    W = C.W * len(frames)
    im = Image.new('RGBA', (W, C.H), (0, 0, 0, 0))
    for i, a in enumerate(frames):
        im.alpha_composite(jrot.to_img(a), (i * C.W, 0))
    return jrot.upscale(im, s)


def grid(frames, s=4, cols=4, names=None):
    from PIL import ImageDraw
    rows = (len(frames) + cols - 1) // cols
    cell = C.W * s
    out = Image.new('RGBA', (cols * (cell + 8), rows * (cell + 8 + 16)), (22, 22, 28, 255))
    d = ImageDraw.Draw(out)
    for i, a in enumerate(frames):
        x = (i % cols) * (cell + 8)
        y = (i // cols) * (cell + 8 + 16)
        if names:
            d.text((x + 4, y + 2), names[i], fill=(230, 230, 230, 255))
        out.alpha_composite(jrot.upscale(jrot.to_img(a), s), (x, y + 16))
    return out


def run(frames, holds, names, out_dir=None):
    out_dir = out_dir or C.SCRATCH
    os.makedirs(out_dir, exist_ok=True)
    strip(frames, 4).save(os.path.join(out_dir, 'bixby_juggle_4x.png'))
    grid(frames, 4, 4, names).save(os.path.join(out_dir, 'bixby_juggle_grid_4x.png'))
    ims = gif(frames, holds, os.path.join(out_dir, 'bixby_juggle_game.gif'))
    for i in (0, 4, 12, 30, len(ims) - 1):
        ims[min(i, len(ims) - 1)].save(os.path.join(out_dir, 'bixby_juggle_game_%02d.png' % i))
    return out_dir


if __name__ == '__main__':
    import jposes
    frames = [fn() for _, fn, _ in jposes.FRAMES]
    holds = [h for _, _, h in jposes.FRAMES]
    names = ['%d %s' % (i, n) for i, (n, _, _) in enumerate(jposes.FRAMES)]
    print('previews in', run(frames, holds, names, os.path.join(C.SCRATCH, 'work')))
