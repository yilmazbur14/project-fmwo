"""Sheet definitions: frame builders, frame sizes, timings (ms) and Aseprite tags for every deliverable.

    python sheets.py <out_dir> [sheet ...]     renders the named sheets (default all) as strips + 3x previews
"""
import os
import sys
from PIL import Image

import frames as F
import crater as CR
import body
from jr import Layer, FW, FH


def eric_frame(builder):
    pose = builder()
    fr, L = body.render(pose)
    return fr


def layer_image(lay):
    im = Image.new('RGBA', (FW, FH))
    im.putdata([p for row in lay.rgba() for p in row])
    return im


def decal_image(d):
    return d.image()


# name: (frame builders, (w, h), durations ms, tags [(name, first, last) 0-based inclusive])
SHEETS = {
    'eric_broken': dict(
        frames=[(lambda b=b: layer_image(eric_frame(b))) for b in F.BROKEN], size=(FW, FH),
        durations=[60, 70, 70, 100, 100, 160, 160, 160],
        tags=[('reel', 0, 2), ('kneel', 3, 4), ('slumped', 5, 7)]),
    'eric_broken_sword': dict(
        frames=[(lambda b=b: layer_image(b())) for b in F.SWORD], size=(FW, FH),
        durations=[40, 50, 50, 50, 50, 50, 1000],
        tags=[('plunge', 0, 3), ('wobble', 4, 5), ('planted', 6, 6)]),
    'eric_juggle': dict(
        frames=[(lambda b=b: layer_image(eric_frame(b))) for b in F.JUGGLE], size=(FW, FH),
        durations=[50, 70, 110, 110, 110, 110, 80, 100, 100, 1000],
        tags=[('hit', 0, 1), ('tumble', 2, 5), ('crash', 6, 7), ('bounce', 8, 8), ('lying', 9, 9)]),
    'eric_winded': dict(
        frames=[(lambda b=b: layer_image(eric_frame(b))) for b in F.WINDED], size=(FW, FH),
        durations=[150, 150, 150, 150],
        tags=[('winded', 0, 3)]),
    'eric_crash_crater': dict(
        frames=[(lambda b=b: decal_image(b())) for b in (CR.flash, CR.crack, CR.settle, CR.held)], size=(128, 48),
        durations=[60, 80, 300, 1000],
        tags=[('flash', 0, 0), ('crack', 1, 1), ('settle', 2, 2), ('held', 3, 3)]),
}


def render_frames(name):
    spec = SHEETS[name]
    out = []
    for fn in spec['frames']:
        im = fn()
        assert im.size == spec['size'], (name, im.size)
        out.append(im)
    return out


def strip(frames):
    w, h = frames[0].size
    s = Image.new('RGBA', (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        s.paste(f, (i * w, 0))
    return s


if __name__ == '__main__':
    out = sys.argv[1]
    names = sys.argv[2:] or list(SHEETS)
    os.makedirs(out, exist_ok=True)
    for n in names:
        fr = render_frames(n)
        s = strip(fr)
        s.save(os.path.join(out, n + '.png'))
        bg = Image.new('RGBA', s.size, (0x7e, 0xa8, 0x5b, 255))
        bg.alpha_composite(s)
        k = 3 if n != 'eric_crash_crater' else 4
        bg.resize((s.size[0] * k // 2, s.size[1] * k // 2), Image.NEAREST).save(os.path.join(out, n + '_prev.png'))
        for i, f in enumerate(fr):
            print(n, i, f.getbbox())
