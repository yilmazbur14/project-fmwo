"""Previews for Captain Burak's juggle. Writes ONLY to the folder given (the session scratchpad),
never into Assets/:

    python jpreviews.py <out_dir>

  strip_4x.png    all 12 frames at 4x, two rows of six, labelled with their holds
  juggle_3x.gif   the whole sequence at game scale (3x) over the arena mat, the player beside him for
                  scale: the hit, the tumble looping twice while he rises and falls (his mat shadow
                  under him, picked by height the way the juggle state picks it), the crash, the
                  lying loop
"""
import math
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jexport  # noqa: E402
import jkit as J  # noqa: E402
import jposes  # noqa: E402
import jshadow  # noqa: E402
import kit  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))


def asset(*parts):
    return Image.open(os.path.join(ROOT, 'Assets', *parts)).convert('RGBA')


def strip_4x(frames):
    ims = [kit.label(kit.up(f, 4), '%d %s  %.2fs' % (i, jposes.FRAMES[i][0], jposes.FRAMES[i][2]))
           for i, f in enumerate(frames)]
    top, bot = kit.row(ims[:6], gap=8), kit.row(ims[6:], gap=8)
    out = Image.new('RGBA', (max(top.width, bot.width), top.height + bot.height + 8), (10, 10, 12, 255))
    out.paste(top, (0, 0))
    out.paste(bot, (0, top.height + 8))
    return out


# the juggle's shadow spec, as Mason's and Eric's layouts give it
SHADOW_ALPHA, SHADOW_STEP, SCALE = 0.35, 100.0, 3


def sequence():
    """(frame index, hold s, lift in art px): contact, lift, the loop twice rising and falling, the
    crash, the lying loop three times."""
    seq = [(0, None, 0.0)]
    air = [1] + [2, 3, 4, 5, 6] * 2
    n = len(air)
    for k, fi in enumerate(air):
        t = (k + 1) / (n + 1.0)
        seq.append((fi, None, 58.0 * 4 * t * (1 - t)))      # up and back down, peak ~58px (174 on screen)
    for fi in (7, 8, 9):
        seq.append((fi, None, 0.0))
    for _ in range(3):
        seq += [(10, None, 0.0), (11, None, 0.0)]
    return [(fi, jposes.FRAMES[fi][2], lift) for (fi, _, lift) in seq]


def juggle_gif(frames, path):
    mat = asset('Environment', 'arena_mat.png')
    player = asset('Characters', 'MainPlayer', 'player_4dir_sheet.png').crop((0, 64, 32, 96))   # facing left, toward him
    shadow = kit.image(jshadow.sheet_px(), jshadow.W * jshadow.FRAMES, jshadow.H)
    w, h = 300, 210
    base = mat.crop((110, 40, 110 + w, 40 + h)).copy()
    ground = (118, 196)                                   # the mat point his feet texel stands on
    base.alpha_composite(player, (226, ground[1] - 30))   # the player, to his right, for scale
    out, durations = [], []
    for fi, hold, lift in sequence():
        scene = base.copy()
        if lift > 0:
            sf = max(0, min(jshadow.FRAMES - 1, int(lift * SCALE / SHADOW_STEP)))
            sh = shadow.crop((sf * jshadow.W, 0, (sf + 1) * jshadow.W, jshadow.H))
            a = sh.getchannel('A').point(lambda v: int(v * SHADOW_ALPHA))
            sh.putalpha(a)
            scene.alpha_composite(sh, (ground[0] - jshadow.W // 2, ground[1] - jshadow.H // 2))
        top_left = (ground[0] - J.FEET[0], ground[1] - J.FEET[1] - int(round(lift)))
        scene.alpha_composite(frames[fi], top_left)
        big = scene.resize((w * SCALE, h * SCALE), Image.NEAREST)
        out.append(big.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=255, dither=Image.NONE))
        durations.append(int(round(hold * 1000)))
    out[0].save(path, save_all=True, append_images=out[1:], duration=durations, loop=0, disposal=2, optimize=False)
    return sum(durations) / 1000.0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    od = sys.argv[1]
    os.makedirs(od, exist_ok=True)
    fr = jexport.frames_with_owners()
    frames = [kit.image(px, J.FW, J.FH) for (name, px, own, hold) in fr]
    strip_4x(frames).save(os.path.join(od, 'strip_4x.png'))
    secs = juggle_gif(frames, os.path.join(od, 'juggle_3x.gif'))
    print('previews written to', od, '(gif %.2fs a loop)' % secs)
