"""python lint.py  - craft and shading checks on the juggle sheet.

Three kinds of damage are easy to ship across twelve frames and hard to see:

  * rotation crumbs -- orphan pixels, a keyline gone two thick, a hole punched in
    the middle of a body;
  * a colour that is not on mason_sheet.png; and
  * the SHADING going wrong, which is the one that nearly got through.  The first
    relight refitted an ellipse to each rotated bounding box, and the result was
    31% deep shadow against Mason's own 14%: the ramp collapsed into its tails
    and every rotated frame read as a flat blob.  It looked plausible.  Only the
    measurement caught it, so the measurement lives here now, per frame, with a
    band that fails the build.

The orphan and keyline checks run on HIS BODY only.  Impact lines and drifting
dust are one-pixel-wide on purpose and would otherwise drown the real findings.
"""
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'mason'))

import jlib as J          # noqa: E402
import poses              # noqa: E402
from png import read_png  # noqa: E402
from rig import CREAM_HI, CREAM, CREAM_MID, CREAM_DEEP, hex2rgba  # noqa: E402

SHEET = r'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Mason/mason_sheet.png'
BLACK = (0, 0, 0)
RAMP = [hex2rgba(c)[:3] for c in (CREAM_HI, CREAM, CREAM_MID, CREAM_DEEP)]

# Mason's own sheet is 24.1% keyline over 19 frames, and its frames run 22.6-28.4%.
# A 128x96 frame has a longer border for the same body, so it can only hit that by
# carrying interior line -- which it does, because the wings and soles are outlined
# over the body.  Anything outside this band means the frame has stopped doing that.
KEYLINE = (0.20, 0.32)
# Ramp shares, highlight to deep.  His sheet is 14.6/35.5/35.9/14.0; a body rolled
# to face the key light honestly catches more highlight and throws more shadow, so
# the tails are allowed to run wide -- but not to swallow the mid-tones, which is
# exactly what a broken relight does.
RAMP_BAND = ((0.05, 0.32), (0.22, 0.45), (0.18, 0.45), (0.08, 0.30))


def craft(g, allowed):
    bad = Counter()
    body = set(J.figure(g))

    def o(x, y):
        return 0 <= x < J.W and 0 <= y < J.H and g[y][x][3]

    for y in range(J.H):
        for x in range(J.W):
            if not o(x, y):
                if all(o(x + dx, y + dy) for dx, dy in J.N4):
                    bad['hole'] += 1
                continue
            if g[y][x][:3] not in allowed:
                bad['off-palette'] += 1
            if (x, y) not in body:
                continue
            if sum(o(x + dx, y + dy) for dx, dy in J.N4) < 2:
                bad['orphan'] += 1
            if g[y][x][:3] == BLACK and all(o(x + dx, y + dy) for dx, dy in J.N4):
                edge = [(x + dx, y + dy) for dx, dy in J.N4
                        if any(not o(x + dx + ex, y + dy + ey) for ex, ey in J.N4)]
                if len(edge) >= 2 and all(g[b][a][:3] == BLACK for a, b in edge):
                    bad['thick keyline'] += 1
    return bad


def shading(g):
    c = Counter(p[:3] for row in g for p in row if p[3])
    n = sum(c.values())
    ramp = sum(c.get(v, 0) for v in RAMP)
    key = c.get(BLACK, 0) / n
    shares = [c.get(v, 0) / ramp for v in RAMP] if ramp else [0] * 4
    fails = []
    if not KEYLINE[0] <= key <= KEYLINE[1]:
        fails.append('keyline %.1f%% outside %.0f-%.0f%%'
                     % (100 * key, 100 * KEYLINE[0], 100 * KEYLINE[1]))
    for i, (lo, hi) in enumerate(RAMP_BAND):
        if not lo <= shares[i] <= hi:
            fails.append('ramp[%d] %.1f%% outside %.0f-%.0f%%'
                         % (i, 100 * shares[i], 100 * lo, 100 * hi))
    return key, shares, fails


def main():
    _, _, sheet = read_png(SHEET)
    allowed = {p[:3] for row in sheet for p in row if p[3]}
    total = fatal = 0
    print('%-15s %-8s %-28s %s' % ('frame', 'keyline', 'ramp hi/base/mid/deep', 'findings'))
    for name, fn, _ in poses.FRAMES:
        g = fn()
        bad = craft(g, allowed)
        key, shares, fails = shading(g)
        total += sum(bad.values()) + len(fails)
        fatal += len(fails) + bad['hole'] + bad['off-palette']
        print('%-15s %6.1f%%  %-28s %s'
              % (name, 100 * key, ' '.join('%4.1f%%' % (100 * s) for s in shares),
                 '; '.join(fails) or (dict(bad) if bad else 'clean')))
    # Orphans and keyline junctions are reported but not fatal: a one-pixel impact
    # line has no 4-neighbours by design, and two black outlines meeting at a wing
    # root is a junction, not a doubled keyline.  Both were checked at 6x by eye.
    # A hole, an off-palette colour or a ramp outside its band always is fatal.
    print('\n%d findings reported, %d of them fatal '
          '(shading band, holes, off-palette)' % (total, fatal))
    return fatal


if __name__ == '__main__':
    sys.exit(1 if main() else 0)
