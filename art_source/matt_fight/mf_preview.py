"""Previews of the fight body set, written only to the session scratchpad (never to Assets):

    contact_4x.png     every frame of every sheet at 4x, labelled
    game_scale.png     every sheet at 3x on the arena mat
    <sheet>.gif        each animation at 4x with its timing (recover, hit, yell_tell->roar,
                       mystic_cast, trueshot charge->fire, teleport, idle, spent, defeat)

    python mf_preview.py
"""
import os

from PIL import Image, ImageDraw

import mf_base as M
from mf_base import B
import mi_view as V
import mf_export as X
import mi_roar

OUT = M.SCRATCH


def title(im, text):
    out = Image.new('RGBA', (im.width, im.height + 26), V.DARK)
    out.paste(im, (0, 26))
    ImageDraw.Draw(out).text((6, 6), text, fill=(255, 214, 110, 255))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    frames = {}
    sections = []
    for cls, times in X.SHEETS:
        fr = [X.px_of(f) for f in cls.figs()]
        frames[cls.NAME] = fr
        ims = [V.label(V.up(B.image(p), 4), '%d' % i) for i, p in enumerate(fr)]
        sections.append(title(V.row(ims), '%s  %s' % (cls.NAME, times)))
    V.col(sections, gap=12).save(os.path.join(OUT, 'contact_4x.png'))
    rows = [V.on_mat(fr) for fr in frames.values()]
    V.col(rows, gap=6).save(os.path.join(OUT, 'game_scale.png'))
    roar = mi_roar.frames()
    gifs = {
        'recover': (frames['matt_recover'] * 3, [180] * 12),
        'hit': (frames['matt_recover'][:1] + frames['matt_hit'] + frames['matt_recover'][:1],
                [300, 70, 120, 400]),
        'yell_tell': (frames['matt_yell_tell'] + roar[1:] * 6, [200, 200] + [60] * 18),
        'mystic_cast': (frames['matt_mystic_cast'] + frames['matt_idle'][:1], [225, 225, 75, 75, 400]),
        'trueshot': (frames['matt_trueshot_charge'] * 2 + frames['matt_trueshot_fire'],
                     [120] * 8 + [60, 80, 500]),
        'teleport': (frames['matt_teleport'], [50] * 6),
        'idle': (frames['matt_idle'], [160] * 4),
        'spent': (frames['matt_spent'] * 2, [150] * 8),
        'defeat': (frames['matt_defeat'], [130, 110, 110, 130, 180, 1200]),
    }
    for name, (fr, dur) in gifs.items():
        V.gif(fr, os.path.join(OUT, name + '.gif'), 4, dur)
    for n in ['contact_4x.png', 'game_scale.png'] + [k + '.gif' for k in gifs]:
        print(os.path.join(OUT, n))


if __name__ == '__main__':
    main()
