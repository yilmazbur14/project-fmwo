"""Previews for review, written only to the session scratchpad (mi_base.SCRATCH), never to Assets:

    contact_4x.png        every frame of every sheet at 4x, labelled, plus the portrait
    walk.gif              the walk loop at 4x, 0.10 s a frame
    doll.gif              the whole doll beat at 4x: pull 0.12/0.12/0.40, the scream cycled at 0.06,
                          the stow 0.15/0.30
    roar.gif              the brace 0.35 s, then the roar loop at 0.06 s
    portrait_6x.png       the portrait at 6x beside the same crop of frame 0, with both sets of numbers,
                          and the portrait at balloon size beside the cast's
    game_scale.png        every sheet at 3x on the arena mat

    python mi_preview.py
"""
import os

from PIL import Image, ImageDraw

import mi_base as B
import mi_view as V
import mi_walk
import mi_talk
import mi_doll
import mi_roar
import mi_portrait

OUT = B.SCRATCH
DOLL_NAMES = ['reach', 'pull', 'hold', 'scream a', 'scream b', 'scream c', 'stow', 'exhale']
ROAR_NAMES = ['brace', 'roar a', 'roar b', 'roar c']


def labelled(frames, names, s=4):
    return [V.label(V.up(B.image(f), s), n) for f, n in zip(frames, names)]


def grid(ims, per_row=6, gap=8):
    rows = [V.row(ims[i:i + per_row], gap=gap) for i in range(0, len(ims), per_row)]
    return V.col(rows, gap=gap)


def title(im, text):
    out = Image.new('RGBA', (im.width, im.height + 26), V.DARK)
    out.paste(im, (0, 26))
    ImageDraw.Draw(out).text((6, 6), text, fill=(255, 214, 110, 255))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    walk = mi_walk.frames()
    talk = mi_talk.frames()
    doll = mi_doll.frames()
    roar = mi_roar.frames()
    talk_names = ['%d %s %s' % (i, mi_talk.POSES[i // 2], 'open' if i % 2 else 'shut') for i in range(len(talk))]
    sections = [
        title(grid(labelled(walk, ['%d' % i for i in range(6)])), 'matt_walk.png  6 frames, 0.10 s, loop'),
        title(grid(labelled(talk, talk_names)), 'matt_talk.png  9 poses x (mouth shut, open)'),
        title(grid(labelled(doll, ['%d %s' % (i, n) for i, n in enumerate(DOLL_NAMES)])), 'matt_doll.png  8 frames'),
        title(grid(labelled(roar, ['%d %s' % (i, n) for i, n in enumerate(ROAR_NAMES)])), 'matt_roar.png  4 frames, no rings'),
    ]
    port = mi_portrait.build_image()
    sections.append(title(V.label(V.up(port, 4), 'portrait 64x64'), 'portrait.png'))
    V.col(sections, gap=14).save(os.path.join(OUT, 'contact_4x.png'))

    V.gif(walk, os.path.join(OUT, 'walk.gif'), 4, [100] * 6)
    seq = doll[:3] + (doll[3:6] * 6) + doll[6:]
    dur = [120, 120, 400] + [60] * 18 + [150, 300]
    V.gif(seq, os.path.join(OUT, 'doll.gif'), 4, dur)
    rseq = [roar[0]] + roar[1:] * 10
    V.gif(rseq, os.path.join(OUT, 'roar.gif'), 4, [350] + [60] * 30)

    crop = B.image(mi_portrait.sprite_crop(), mi_portrait.N, mi_portrait.N)
    p, s = B.stats(port), B.stats(crop)
    a = V.label(V.up(port, 6), 'portrait.png 6x: black %.1f%%, %d colours' % (100 * p['black'], p['colours']))
    b = V.label(V.up(crop, 6), 'frame 0, x23-73 y6-56 (same crop) 6x: black %.1f%%, %d colours'
                % (100 * s['black'], s['colours']))
    cast = [V.label(V.up(port, 2), 'Matt (balloon size)')]
    for n in ('Jordan', 'Josh', 'Carter'):
        im = Image.open(os.path.join(B.ROOT, 'Assets', 'Characters', n, 'portrait.png')).convert('RGBA')
        cast.append(V.label(V.up(im, 2), n))
    V.col([V.row([a, b], gap=16), V.row(cast, gap=12)], gap=16).save(os.path.join(OUT, 'portrait_6x.png'))

    rows = [V.on_mat(walk), V.on_mat(talk[:9]), V.on_mat(talk[9:]), V.on_mat(doll), V.on_mat(roar)]
    V.col(rows, gap=6).save(os.path.join(OUT, 'game_scale.png'))
    for n in ('contact_4x.png', 'walk.gif', 'doll.gif', 'roar.gif', 'portrait_6x.png', 'game_scale.png'):
        print(os.path.join(OUT, n))


if __name__ == '__main__':
    main()
