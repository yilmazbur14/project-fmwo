"""python -B gj_gif.py <out_dir>  - the juggle in context, for review. Writes ONLY into the folder it
is given (a folder under Assets is refused); reads the arena mat and the player's uppercut sheet.

Everything at game scale: the arena mat and Greyson at 3x (his Sprite2D's scale), the player's own
uppercut frames at 2x (MainPlayer's body scale; FinisherArtLayout lines the 48x64 frames up with
his 32x32 ones), mirrored to face him, and Greyson's juggle frames lifted along a parabola the way PlayerFinisher lifts a boss -- the
hit, the tumble looping twice while he rises and falls, the crash, then the lying loop -- with his
leap shadow under him while he is up. The lift is scaled down to fit the picture, the way the
finisher's own lift_scale fits it to a boss's headroom.
"""
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import gj_rig as R        # noqa: E402
import gj_poses as P      # noqa: E402
import gj_shadow as S     # noqa: E402
import gj_build as B      # noqa: E402
from PIL import Image     # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
MAT = os.path.join(ROOT, 'Assets', 'Environment', 'arena_mat.png')
PLAYER = os.path.join(ROOT, 'Assets', 'Characters', 'MainPlayer', 'player_uppercut.png')
SC = 3
SC_PLAYER = 2
CANVAS = (900, 640)
GROUND = 600                 # screen row his feet (and the player's) stand on
BOSS_X = 330                 # screen column of his feet texel
PLAYER_FOOT_ROW = 60         # the player's lowest drawn row on his ground frames
PLAYER_DX = 130              # the player's feet, right of his
APEX = 170                   # px the tumble peaks at over his ground line
SHADOW_ALPHA = 0.35


def mat():
    m = Image.open(MAT).convert('RGBA')
    w, h = CANVAS[0] // SC, CANVAS[1] // SC
    x0, y0 = max(0, (m.width - w) // 2), max(0, m.height - h - 8)
    c = m.crop((x0, y0, x0 + w, y0 + h))
    return c.resize((c.width * SC, c.height * SC), Image.NEAREST)


def player_frames():
    p = Image.open(PLAYER).convert('RGBA')
    out = []
    for f in range(p.width // 48):
        c = p.crop((f * 48, 0, f * 48 + 48, 64)).transpose(Image.FLIP_LEFT_RIGHT)
        out.append(c.resize((48 * SC_PLAYER, 64 * SC_PLAYER), Image.NEAREST))
    return out


def boss_frames():
    return [f.resize((R.W * SC, R.H * SC), Image.NEAREST) for f in B.render()]


def shadow_frames():
    rows, _ = S.sheet()
    im = B.to_image(rows)
    out = []
    for f in range(S.FRAMES):
        c = im.crop((f * S.W, 0, (f + 1) * S.W, S.H)).resize((S.W * SC, S.H * SC), Image.NEAREST)
        c.putalpha(c.getchannel('A').point(lambda v: int(v * SHADOW_ALPHA)))
        out.append(c)
    return out


def timeline():
    """(juggle frame, lift px, player frame, seconds): the sheet's own suggested holds; the lift
    follows one parabola across the two tumble loops."""
    hold = [t for _, _, t in P.FRAMES]
    seq = [(0, 0.0, 5, hold[0]), (1, 20.0, 6, hold[1])]
    loop = [2, 3, 4, 5, 6] * 2
    total = sum(hold[i] for i in loop)
    t = 0.0
    pl = [7, 7, 8, 8, 9, 9, 9, 9, 9, 9]
    for n, i in enumerate(loop):
        mid = (t + hold[i] / 2.0) / total
        lift = 20.0 * (1 - mid) + 4 * (APEX - 10.0) * mid * (1 - mid)
        seq.append((i, lift, pl[n], hold[i]))
        t += hold[i]
    seq += [(7, 0.0, 9, hold[7]), (8, 0.0, 9, hold[8]), (9, 0.0, 9, hold[9])]
    seq += [(10, 0.0, 9, hold[10]), (11, 0.0, 9, hold[11])] * 3
    return seq


def main():
    out = sys.argv[1]
    if B._under(out, B.ASSETS):
        print('REFUSING: %s is under Assets' % out)
        return 1
    os.makedirs(out, exist_ok=True)
    bg = mat()
    pf, bf, sf = player_frames(), boss_frames(), shadow_frames()
    frames, times = [], []
    for (i, lift, p, t) in timeline():
        im = Image.new('RGBA', CANVAS, (0, 0, 0, 255))
        im.alpha_composite(bg, (0, 0))
        if lift > 0.5:
            s = sf[min(int(lift / 100.0), 2)]
            im.alpha_composite(s, (BOSS_X - s.width // 2, GROUND - s.height // 2))
        b = bf[i]
        ox = BOSS_X - R.FEET[0] * SC - SC // 2
        oy = GROUND - (R.FEET[1] + 1) * SC - int(round(lift))
        im.alpha_composite(b, (ox, oy))
        pim = pf[min(p, len(pf) - 1)]
        im.alpha_composite(pim, (BOSS_X + PLAYER_DX - pim.width // 2,
                                 GROUND - (PLAYER_FOOT_ROW + 1) * SC_PLAYER))
        frames.append(im.convert('RGB'))
        times.append(int(round(t * 1000)))
    path = os.path.join(out, 'greyson_juggle_ingame.gif')
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=times, loop=0,
                   disposal=1, optimize=False)
    # the same frames side by side, for reading the lift and scale off a still
    cols = 6
    small = [f.resize((CANVAS[0] // 2, CANVAS[1] // 2), Image.NEAREST) for f in frames[:24]]
    sheet = Image.new('RGB', (CANVAS[0] // 2 * cols, CANVAS[1] // 2 * ((len(small) + cols - 1) // cols)),
                      (20, 20, 20))
    for n, f in enumerate(small):
        sheet.paste(f, ((n % cols) * CANVAS[0] // 2, (n // cols) * CANVAS[1] // 2))
    sheet.save(os.path.join(out, 'greyson_juggle_ingame_frames.png'))
    print('wrote', path, len(frames), 'frames,', sum(times), 'ms')
    return 0


if __name__ == '__main__':
    sys.exit(main())
