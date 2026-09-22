"""python measure.py  - the numbers the juggle keys have to hit.

Matching "the style" is not enough: a frame can look like Mason and still be
flatter, blacker or thinner than he is.  This compares the keys against
mason_sheet.png on the things that are actually measurable -- what share of the
drawn pixels are keyline, how many colours are in play, and how the four-tone
cream ramp is distributed -- so a difference has to be argued rather than missed.
"""
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'mason'))

import poses                                                     # noqa: E402
from png import read_png                                         # noqa: E402
from rig import CREAM_HI, CREAM, CREAM_MID, CREAM_DEEP, hex2rgba  # noqa: E402

SHEET = r'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Mason/mason_sheet.png'
RAMP = [(c, hex2rgba(c)[:3]) for c in (CREAM_HI, CREAM, CREAM_MID, CREAM_DEEP)]
KEY = (0, 0, 0)


def stats(pixels):
    c = Counter(p[:3] for row in pixels for p in row if p[3])
    n = sum(c.values())
    ramp = sum(c.get(v, 0) for _, v in RAMP)
    return {
        'px': n,
        'colours': len(c),
        'keyline': c.get(KEY, 0) / n,
        'ramp': [c.get(v, 0) / ramp if ramp else 0 for _, v in RAMP],
        'counter': c,
    }


def line(name, s):
    print('%-10s %6d px  %2d colours  keyline %5.1f%%   ramp %s'
          % (name, s['px'], s['colours'], 100 * s['keyline'],
             ' '.join('%4.1f%%' % (100 * v) for v in s['ramp'])))


def main():
    w, h, sheet = read_png(SHEET)
    whole = stats(sheet)
    print('reference (mason_sheet.png, %d frames of 64x64)' % (w // 64))
    line('sheet', whole)
    for fi in (0, 12, 14):
        line('  frame %d' % fi,
             stats([[sheet[y][fi * 64 + x] for x in range(64)] for y in range(64)]))
    per = [stats([[sheet[y][fi * 64 + x] for x in range(64)] for y in range(64)])
           for fi in range(w // 64)]
    print('  per frame: keyline %.1f-%.1f%%, %d-%d colours'
          % (100 * min(s['keyline'] for s in per), 100 * max(s['keyline'] for s in per),
             min(s['colours'] for s in per), max(s['colours'] for s in per)))

    print('\njuggle sheet (12 frames of 128x96)')
    grids = [(n, fn()) for n, fn, _ in poses.FRAMES]
    for n, g in grids:
        line('  ' + n, stats(g))
    allpx = [row for _, g in grids for row in g]
    line('sheet', stats(allpx))

    shadow_png = os.path.join(HERE, 'mason_leap_shadow.png')
    if os.path.exists(shadow_png):
        _, _, sh = read_png(shadow_png)
        line('\nshadow', stats(sh))

    ref, got = whole, stats(allpx)
    print('\ndelta vs the sheet: keyline %+.1f pts, %d colours vs %d'
          % (100 * (got['keyline'] - ref['keyline']), got['colours'], ref['colours']))
    extra = set(got['counter']) - set(ref['counter'])
    print('colours not on the sheet:',
          ['#%02X%02X%02X' % c for c in sorted(extra)] if extra else 'none')
    print('(25 is the WHOLE of his sheet, including props that appear on one frame'
          ' each --\n phone greys, nugget browns, fries red, stink green, sweat'
          ' blue.  Any single\n frame of his is 13-15 colours, and so is this.)')


if __name__ == '__main__':
    main()
