"""Render Mason's juggle sheet.

  python build.py            -> mason_juggle.png (12 frames of 128x96), the mat
                                shadow, 3x/6x previews and the frame table

Before it writes anything it checks the five approved keys against the strip they
were approved from.  Frames 0, 2, 3, 7 and 10 of the sheet ARE those keys; if a
later tweak drifts one of them the build stops rather than quietly shipping art
nobody signed off.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, os.path.join(HERE, '..', 'mason'))

import jlib as J          # noqa: E402
import poses              # noqa: E402
import shadow             # noqa: E402
from png import read_png  # noqa: E402
from zoom import write_png  # noqa: E402

KEYS_PNG = os.path.join(HERE, 'mason_juggle_keys.png')
SHEET = os.path.join(HERE, 'mason_juggle.png')


def strip(grids, w, h):
    out = [[(0, 0, 0, 0)] * (len(grids) * w) for _ in range(h)]
    for i, g in enumerate(grids):
        for y in range(h):
            for x in range(w):
                out[y][i * w + x] = g[y][x]
    return len(grids) * w, h, out


def upscale(w, h, px, f, cell=None):
    W2, H2 = w * f, h * f
    out = []
    for Y in range(H2):
        row = []
        for X in range(W2):
            p = px[Y // f][X // f]
            if p[3] == 0:
                c = 60 if ((X // f) + (Y // f)) % 2 == 0 else 48
                p = (c, c, c, 255)
            row.append(p)
        out.append(row)
    if cell:
        for i in range(1, w // cell):
            for Y in range(H2):
                out[Y][i * cell * f] = (150, 40, 150, 255)
    return W2, H2, out


def check_approved(grids):
    """Frames 0, 2, 3, 7, 10 must still be the keys that were signed off."""
    if not os.path.exists(KEYS_PNG):
        print('! no approved keys strip to check against')
        return
    _, _, keys = read_png(KEYS_PNG)
    order = ['launch', 'hang', 'tumble', 'crash', 'down']
    bad = 0
    for i, name in enumerate(order):
        fi = poses.APPROVED_AT[name]
        diff = sum(1 for y in range(J.H) for x in range(J.W)
                   if tuple(grids[fi][y][x]) != tuple(keys[y][i * J.W + x]))
        if diff:
            print('! frame %d (%s) has drifted from the approved key: %d px'
                  % (fi, name, diff))
            bad += 1
    print('approved keys intact at frames %s'
          % sorted(poses.APPROVED_AT.values()) if not bad else '')
    if bad:
        raise SystemExit('approved art changed; fix or re-approve before shipping')


def main():
    grids = [fn() for _, fn, _ in poses.FRAMES]
    check_approved(grids)

    w, h, px = strip(grids, J.W, J.H)
    write_png(SHEET, w, h, px)
    print('wrote mason_juggle.png %dx%d (%d frames of %dx%d)'
          % (w, h, len(grids), J.W, J.H))
    for f in (3, 6):
        W2, H2, o = upscale(w, h, px, f, cell=J.W)
        write_png(os.path.join(HERE, 'mason_juggle_%dx.png' % f), W2, H2, o)
        print('wrote mason_juggle_%dx.png %dx%d' % (f, W2, H2))

    shadow.build(HERE)

    print()
    print('%-3s %-15s %-6s %-16s %-16s %s'
          % ('#', 'frame', 'hold', 'frame bbox', 'figure bbox', 'figure mid x'))
    air, over = [], []
    for i, ((name, fn, hold), g) in enumerate(zip(poses.FRAMES, grids)):
        b = J.bbox_of(g)
        fn()                      # re-run to capture the figure before its effects
        x0, y0, x1, y1 = J.LAST_FIGURE
        print('%-3d %-15s %-6.2f %-16s %-16s %.1f'
              % (i, name, hold, '%d,%d-%d,%d' % b,
                 '%d,%d-%d,%d' % (x0, y0, x1 - 1, y1 - 1), (x0 + x1 - 1) / 2))
        if y1 - 1 < 95:
            air.append(b[1])
        if b[1] < y0:
            over.append('%s: effects reach row %d, he only reaches %d'
                        % (name, b[1], y0))
    print('\nfeet point      %s' % (J.FEET,))
    print('tumble centre   %s' % (J.TUMBLE_CENTRE,))
    print('top_row         %d  (highest row drawn on an airborne frame)' % min(air))
    for w in over:
        print('  ! %s' % w)
    print('loop            frames %d-%d, %.2fs a turn'
          % (poses.TAGS['tumble'][0], poses.TAGS['tumble'][1],
             sum(poses.FRAMES[i][2] for i in range(poses.TAGS['tumble'][0],
                                                   poses.TAGS['tumble'][1] + 1))))


if __name__ == '__main__':
    main()
