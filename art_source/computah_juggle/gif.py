"""python gif.py <out_dir>  - the juggle in context, for review.  Writes ONLY into
the folder it is given; reads the arena mat and the player's uppercut sheet.

Everything at game scale (3x): the arena mat, the player's own uppercut frames
(mirrored to face him), and Computah's juggle frames lifted along a parabola the
way PlayerFinisher lifts a boss -- hit, the tumble looping twice while he rises and
falls, the crash, then the lying loop -- with his leap shadow under him while he is
up.  The lift is scaled down to fit the picture, the way the finisher's own
lift_scale fits it to a boss's headroom.
"""
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import jrig as J          # noqa: E402
import poses              # noqa: E402
import shadow             # noqa: E402
import build              # noqa: E402
from PIL import Image     # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
MAT = os.path.join(ROOT, 'Assets', 'Environment', 'arena_mat.png')
PLAYER = os.path.join(ROOT, 'Assets', 'Characters', 'MainPlayer', 'player_uppercut.png')
S = 3
CANVAS = (768, 600)
GROUND = 560                 # screen row his feet (and the player's) stand on
BOSS_X = 300                 # screen column of his feet texel
PLAYER_FOOT_ROW = 60         # the player's lowest drawn row on his ground frames
APEX = 150                   # px the tumble peaks at over his ground line


def mat():
    m = Image.open(MAT).convert('RGBA')
    w, h = CANVAS[0] // S, CANVAS[1] // S
    x0, y0 = (m.width - w) // 2, m.height - h - 8
    return m.crop((x0, y0, x0 + w, y0 + h)).resize(CANVAS, Image.NEAREST)


def player_frames():
    p = Image.open(PLAYER).convert('RGBA')
    out = []
    for f in range(10):
        c = p.crop((f * 48, 0, f * 48 + 48, 64)).transpose(Image.FLIP_LEFT_RIGHT)
        out.append(c.resize((48 * S, 64 * S), Image.NEAREST))
    return out


def boss_frames():
    grids = [fn() for _, fn, _ in poses.FRAMES]
    return [build.to_image(g).resize((J.W * S, J.H * S), Image.NEAREST)
            for g in grids]


def shadow_frames():
    rows, _ = shadow.sheet()
    im = build.to_image(rows)
    out = []
    for f in range(shadow.FRAMES):
        c = im.crop((f * shadow.W, 0, (f + 1) * shadow.W, shadow.H))
        c = c.resize((shadow.W * S, shadow.H * S), Image.NEAREST)
        a = c.getchannel('A').point(lambda v: int(v * 0.35))
        c.putalpha(a)
        out.append(c)
    return out


def timeline():
    """(juggle frame, lift px, player frame, ms).  Durations are the sheet's own
    suggested holds; the lift follows one parabola across the two tumble loops."""
    hold = [t for _, _, t in poses.FRAMES]
    seq = [(0, 0.0, 5, hold[0]), (1, 26.0, 6, hold[1])]
    loop = [2, 3, 4, 5, 6] * 2
    T = sum(hold[i] for i in loop)
    t = 0.0
    pl = [7, 7, 8, 8, 9, 9, 9, 9, 9, 9]
    for n, i in enumerate(loop):
        mid = (t + hold[i] / 2.0) / T
        lift = 26.0 * (1 - mid) + 4 * (APEX - 13.0) * mid * (1 - mid)
        seq.append((i, lift, pl[n], hold[i]))
        t += hold[i]
    seq += [(7, 0.0, 9, hold[7]), (8, 0.0, 9, hold[8]), (9, 0.0, 9, hold[9])]
    seq += [(10, 0.0, 9, hold[10]), (11, 0.0, 9, hold[11])] * 3
    return seq


def main():
    out = sys.argv[1]
    bg = mat()
    pf, bf, sf = player_frames(), boss_frames(), shadow_frames()
    frames, times = [], []
    for (i, lift, p, t) in timeline():
        im = bg.copy()
        if lift > 0.5:
            s = sf[min(int(lift / 100.0), 2)]
            im.alpha_composite(s, (BOSS_X - s.width // 2, GROUND - s.height // 2))
        b = bf[i]
        ox = BOSS_X - J.FEET[0] * S - S // 2
        oy = GROUND - (J.FEET[1] + 1) * S - int(round(lift))
        im.alpha_composite(b, (ox, oy))
        pim = pf[p]
        px = BOSS_X + 118 - pim.width // 2
        py = GROUND - (PLAYER_FOOT_ROW + 1) * S
        im.alpha_composite(pim, (px, py))
        frames.append(im.convert('RGB'))
        times.append(int(round(t * 1000)))
    path = os.path.join(out, 'computah_juggle_ingame.gif')
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=times,
                   loop=0, disposal=1, optimize=False)
    # the same frames side by side, for reading the lift and scale off a still
    sheet = Image.new('RGB', (CANVAS[0] // 2 * 6, CANVAS[1] // 2 * 4), (20, 20, 20))
    for n, f in enumerate(frames[:24]):
        small = f.resize((CANVAS[0] // 2, CANVAS[1] // 2), Image.NEAREST)
        sheet.paste(small, ((n % 6) * CANVAS[0] // 2, (n // 6) * CANVAS[1] // 2))
    sheet.save(os.path.join(out, 'computah_juggle_ingame_frames.png'))
    print('wrote', path, len(frames), 'frames,', sum(times), 'ms')


if __name__ == '__main__':
    main()
