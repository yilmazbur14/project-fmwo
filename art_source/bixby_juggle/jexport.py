"""Build Bixby's juggle sheet and his leap shadow.

    python jexport.py              # SAFE: writes NOTHING anywhere; prints the numbers and the anchors
    python jexport.py --preview    # also the previews, into the scratchpad only (jcommon.SCRATCH)
    python jexport.py --ship       # ALSO writes Assets/Characters/Bixby/bixby_juggle.png and
                                   # bixby_leap_shadow.png, each PNG in one save with its .aseprite beside
                                   # it, both round-tripped through Aseprite and checked pixel for pixel
                                   # (art_source/imgdiff.py). Refuses unless the lint is clean.

The sheet: 12 frames of 256x256 in one strip (jposes.FRAMES order, Mason's): hit 0-1, tumble 2-6 (2 the
hang, 3-6 one full turn), crash 7-9, down 10-11.
"""
import os
import subprocess
import sys

import numpy as np
from PIL import Image

import jcommon as C
import jcompose as JC
import jlint
import jmeasure as M
import jposes
import jrot
import jshadow
from imgdiff import pixel_diff

OUT_PNG = os.path.join(C.BIXBY, 'bixby_juggle.png')
OUT_ASE = os.path.join(C.BIXBY, 'bixby_juggle.aseprite')
SHADOW_PNG = os.path.join(C.BIXBY, 'bixby_leap_shadow.png')
SHADOW_ASE = os.path.join(C.BIXBY, 'bixby_leap_shadow.aseprite')
ASEPRITE = r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe'
AIR = (1, 2, 3, 4, 5, 6)                  # frames the finisher lifts
GROUND = (0, 7, 8, 9, 10, 11)             # frames standing or lying on the feet row


def build():
    frames, figures, metas = [], [], []
    for name, fn, hold in jposes.FRAMES:
        a = fn()
        frames.append(a)
        figures.append(jposes.LAST_FIGURE)
        metas.append(JC.LAST)
    return frames, figures, metas


def strip(frames):
    out = Image.new('RGBA', (C.W * len(frames), C.H), (0, 0, 0, 0))
    for i, a in enumerate(frames):
        out.alpha_composite(jrot.to_img(a), (i * C.W, 0))
    return out


def bbox(a):
    ys, xs = np.nonzero(a)
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))


def centroid(a):
    ys, xs = np.nonzero(a)
    return (round(float(xs.mean()) + 0.5, 1), round(float(ys.mean()) + 0.5, 1))


def report(frames, figures, metas):
    print('sheet: %d frames of %dx%d in one strip (%dx%d), hframes %d, vframes 1'
          % (len(frames), C.W, C.H, C.W * len(frames), C.H, len(frames)))
    print('feet texel (ground frames %s): %s' % (list(GROUND), C.FEET))
    print('tumble_centre (the pivot every air frame turns round): %s' % (C.TUMBLE_CENTRE,))
    print()
    print('%-3s %-13s %-5s %-22s %-22s %-14s %s' % ('#', 'frame', 'hold', 'drawn x0,y0-x1,y1',
                                                    'him x0,y0-x1,y1', 'his centroid', 'numbers'))
    tops_all, tops_him = [], []
    for i, ((name, fn, hold), a, fig) in enumerate(zip(jposes.FRAMES, frames, figures)):
        b, bf = bbox(a), bbox(fig)
        m = M.measure(jrot.to_img(a))
        print('%-3d %-13s %-5.2f %-22s %-22s %-14s key %5.2f%% col %d semi %d'
              % (i, name, hold, '%d,%d-%d,%d' % b, '%d,%d-%d,%d' % bf, centroid(fig),
                 100 * m['keyline'], m['colours'], m['semi']))
        if i in AIR:
            tops_all.append(b[1])
            tops_him.append(bf[1])
            if b[1] < bf[1]:
                print('    (effects reach row %d here, above his %d; top_row for the sheet is still his)' % (b[1], bf[1]))
        edge = b[0] < 2 or b[1] < 2 or b[2] > C.W - 3 or b[3] > C.H - 3
        if edge:
            print('    ! drawn inside the 2-texel frame margin')
    print()
    print('top_row (the highest row drawn on any air frame, effects included): %d; his own highest: %d'
          % (min(tops_all), min(tops_him)))
    if min(tops_all) < min(tops_him):
        print('    ! an effect sets top_row: the headroom of the finisher should be set by him')
    print('ground frames: lowest drawn row of him', {i: bbox(figures[i])[3] for i in GROUND})
    print()
    print('Liam\'s headband plate (middle, and its top edge), per frame:')
    for i in range(len(frames)):
        P, layers = metas[i]
        c = JC.plate_texel(P, layers, 13)
        t = JC.plate_texel(P, layers, 9)
        k = jrot.KEY_OF.get(int(frames[i][c[1], c[0]]), '.')
        print('  %2d %-13s plate middle %s (texel is %r)  top edge %s' % (i, jposes.FRAMES[i][0], c, k, t))
    print()
    print('leap shadow: 3 frames of %dx%d, centre (%d, %d); ellipses %s'
          % (jshadow.SW, jshadow.SH, jshadow.CX, jshadow.CY, '; '.join(jshadow.extents())))


def aseprite_roundtrip(png, ase):
    subprocess.run([ASEPRITE, '-b', png, '--save-as', ase], check=True)
    back = os.path.join(C.SCRATCH, 'roundtrip_' + os.path.basename(png))
    subprocess.run([ASEPRITE, '-b', ase, '--save-as', back], check=True)
    return pixel_diff(Image.open(png), Image.open(back))


def ship(sheet, shadow):
    os.makedirs(C.BIXBY, exist_ok=True)
    ok = True
    for im, png, ase in ((sheet, OUT_PNG, OUT_ASE), (shadow, SHADOW_PNG, SHADOW_ASE)):
        im.save(png)                                   # the PNG in one save
        d = aseprite_roundtrip(png, ase)
        print('wrote %s and %s; aseprite round trip: %s' % (png, ase, d or 'pixel-exact'))
        ok &= d is None
    if not ok:
        raise SystemExit('a round trip differs')


def main():
    write = '--ship' in sys.argv
    preview = '--preview' in sys.argv or write
    bad = jlint.main()
    frames, figures, metas = build()
    print()
    report(frames, figures, metas)
    sheet = strip(frames)
    shadow = jshadow.sheet()
    if preview:
        import jpreview
        holds = [h for _, _, h in jposes.FRAMES]
        names = ['%d %s' % (i, n) for i, (n, _, _) in enumerate(jposes.FRAMES)]
        d = jpreview.run(frames, holds, names, C.SCRATCH)
        sheet.save(os.path.join(d, 'bixby_juggle_1x.png'))
        shadow.save(os.path.join(d, 'bixby_leap_shadow_1x.png'))
        jrot.upscale(shadow, 4).save(os.path.join(d, 'bixby_leap_shadow_4x.png'))
        print('previews in', d)
    if write:
        if bad:
            raise SystemExit('lint has findings: nothing written to Assets')
        ship(sheet, shadow)


if __name__ == '__main__':
    main()
