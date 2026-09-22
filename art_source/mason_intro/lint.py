"""python lint.py  - craft, palette and keyline checks on fry_trail.png.

WHAT IS BEING HELD TO WHAT
mason_sheet.png is the number this has to answer to, and the number that matters
is the keyline COLOUR: Mason's is #000000, pure black, 9,650 texels of his sheet.
That is not a value to carry across from another character - Computah's keyline
is #0C111A with no pure black in it at all - so it is measured off his sheet
here rather than written down.

The keyline SHARE cannot be Mason's 24.1% and should not be.  A share is
perimeter over area, and these are sticks: a fry is four texels thick, so two of
its six rows are keyline before a single decision is made about how to draw it.
The band below is the range Mason's own food props already run at -
nugget_meteor 6.3%, nugget_target 12.6%, nugget_impact 15.3%, poo_bomb 23.5%,
his sheet 24.1% - opened at the top for geometry that is nearly all edge.  It is
there to catch a keyline that has gone two texels thick, not to make a fry as
black as a wrestler.  It did its job once already: at three texels of thickness
the sheet came out 43% keyline, which is what sent the fries to four.

Colour COUNT is checked as containment, not as a number.  Mason's sheet carries
25 colours because he has skin, a hood, a beard, denim and boots; a fry has hot
oil and ketchup.  Matching 25 would mean inventing 19.  What is checked is that
every colour here is one of his 25.
"""
import os
import sys
from collections import Counter

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import fries  # noqa: E402

SHEET = r'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Mason/mason_sheet.png'
STRIP = os.path.join(HERE, 'fry_trail.png')
BLACK = (0, 0, 0)
KEYLINE = (0.18, 0.46)
N4 = fries.N4


def craft(g, allowed):
    bad = Counter()

    def o(x, y):
        return 0 <= x < fries.FW and 0 <= y < fries.FH and g[y][x][3]

    for y in range(fries.FH):
        for x in range(fries.FW):
            if not o(x, y):
                if all(o(x + dx, y + dy) for dx, dy in N4):
                    bad['hole'] += 1
                continue
            if g[y][x][:3] not in allowed:
                bad['off-palette'] += 1
            # Fill touching the frame border means its keyline fell off the edge
            # and the piece will read as sliced.  Black on the border is fine.
            if g[y][x][:3] != BLACK and (x in (0, fries.FW - 1)
                                         or y in (0, fries.FH - 1)):
                bad['keyline clipped'] += 1
            if g[y][x][:3] == BLACK and all(o(x + dx, y + dy) for dx, dy in N4):
                edge = [(x + dx, y + dy) for dx, dy in N4
                        if any(not o(x + dx + ex, y + dy + ey) for ex, ey in N4)]
                if len(edge) >= 2 and all(g[b][a][:3] == BLACK for a, b in edge):
                    bad['thick keyline'] += 1
    return bad


def centring(g):
    """Every piece has to sit on texel (16, 8): the code drops these with a
    centred Sprite2D origin, and a piece drawn off centre lands off the floor
    point.  Crumbs are deliberately thrown wide, so 2 texels of slack."""
    xs = [x for y in range(fries.FH) for x in range(fries.FW) if g[y][x][3]]
    ys = [y for y in range(fries.FH) for x in range(fries.FW) if g[y][x][3]]
    cx, cy = (min(xs) + max(xs) + 1) / 2.0, (min(ys) + max(ys) + 1) / 2.0
    return cx, cy, abs(cx - fries.CX) > 2.0 or abs(cy - fries.CY) > 2.0


def main():
    sheet = Image.open(SHEET).convert('RGBA')
    allowed = {p[:3] for p in sheet.get_flattened_data() if p[3]}
    print('mason_sheet.png: %d colours, keyline %s at %.1f%%'
          % (len(allowed), '#%02X%02X%02X' % BLACK,
             100.0 * sum(1 for p in sheet.get_flattened_data() if p[:3] == BLACK and p[3])
             / sum(1 for p in sheet.get_flattened_data() if p[3])))
    if BLACK not in allowed:
        print('  !! pure black is not on his sheet - re-measure before trusting this')
        return 1

    strip = Image.open(STRIP).convert('RGBA')
    n = len(fries.FRAMES)
    if strip.size != (fries.FW * n, fries.FH):
        print('  !! strip is %s, expected %s' % (strip.size, (fries.FW * n, fries.FH)))
        return 1

    fatal = 0
    used = set()
    print('\n%-9s %6s %8s %8s  %s' % ('frame', 'texels', 'keyline', 'centre', 'findings'))
    for name, fn in fries.FRAMES:
        g = fn()
        c = Counter(g[y][x][:3] for y in range(fries.FH) for x in range(fries.FW)
                    if g[y][x][3])
        used |= set(c)
        total = sum(c.values())
        key = c.get(BLACK, 0) / total
        bad = craft(g, allowed)
        cx, cy, off = centring(g)
        fails = []
        if not KEYLINE[0] <= key <= KEYLINE[1]:
            fails.append('keyline %.1f%% outside %.0f-%.0f%%'
                         % (100 * key, 100 * KEYLINE[0], 100 * KEYLINE[1]))
        if off:
            fails.append('centre (%.1f, %.1f) is off (%.0f, %.0f)'
                         % (cx, cy, fries.CX, fries.CY))
        fatal += len(fails) + bad['hole'] + bad['off-palette'] + bad['keyline clipped']
        print('%-9s %6d %7.1f%% %4.1f,%-4.1f %s'
              % (name, total, 100 * key, cx, cy,
                 '; '.join(fails) or (dict(bad) if bad else 'clean')))

    c = Counter(p[:3] for p in strip.get_flattened_data() if p[3])
    total = sum(c.values())
    print('\nfry_trail.png: %d colours, %d opaque texels, keyline %.1f%%'
          % (len(c), total, 100.0 * c.get(BLACK, 0) / total))
    for col, k in c.most_common():
        print('   #%02X%02X%02X %5d %5.1f%%   %s'
              % (col + (k, 100.0 * k / total,
                        'on mason_sheet' if col in allowed else '!! NOT ON HIS SHEET')))
    stray = used - allowed
    if stray:
        fatal += len(stray)
        print('   !! %d colour(s) not on his sheet' % len(stray))
    print('\n%d fatal finding(s)' % fatal)
    return fatal


if __name__ == '__main__':
    sys.exit(1 if main() else 0)
