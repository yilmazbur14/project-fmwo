"""python aaudit.py [SHEET ...]  - the full audit for the fight set, per frame:

  * clipping: no drawn fill on the frame's edges (a shape cut by the frame), keyline only on the
    feet row (95) and nothing below it;
  * palette: only the approved burak_boss.png colours, no semi-alpha;
  * craft: no holes (a transparent pixel walled in on four sides) or orphan pixels;
  * numbers: opaque px, colours and black share, against the approved sheet (25.4%, 38 colours);
  * anchors: crown and mouth, plus each sheet's own (muzzle, release, blade hand -> tip, strike arc).
"""
import os
import sys
from collections import Counter

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import akit as A  # noqa: E402
import kit  # noqa: E402
import sheets as S  # noqa: E402
from PIL import Image  # noqa: E402

APPROVED = os.path.normpath(os.path.join(HERE, '..', '..', 'Assets', 'Characters', 'BurakBoss', 'burak_boss.png'))
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def approved_colours():
    im = Image.open(APPROVED).convert('RGBA')
    return {c[:3] for c in kit.pixels_of(im) if c[3]}


def audit_frame(px, fw, fh, allowed, bust=False):
    """bust: a portrait, a window cut out of a frame, whose edges cut its shapes by design; the
    clipping checks are skipped for it, every other check stands."""
    im = kit.image(px, fw, fh)
    data = kit.pixels_of(im)
    pix = [c for c in data if c[3]]
    c = Counter(p[:3] for p in pix)
    semi = sum(1 for p in data if 0 < p[3] < 255)
    bad = []
    edge = [(x, y) for (x, y), k in px.items() if k != 'k' and (x in (0, fw - 1) or y == 0)]
    if edge and not bust:
        bad.append('fill on the frame edge %s' % sorted(edge)[:4])
    feet = [(x, y) for (x, y), k in px.items() if y == fh - 1 and k != 'k']
    if feet and not bust:
        bad.append('fill on the feet row %s' % sorted(feet)[:4])
    off = set(c) - allowed
    if off:
        bad.append('off-palette %s' % sorted('#%02X%02X%02X' % t for t in off))
    if semi:
        bad.append('semi-alpha %d' % semi)
    holes = sum(1 for y in range(fh) for x in range(fw)
                if (x, y) not in px and all((x + dx, y + dy) in px for dx, dy in N4))
    if holes:
        bad.append('%d holes' % holes)
    n8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
    orph = [q for q in px if not any((q[0] + dx, q[1] + dy) in px for dx, dy in n8)]
    if orph:
        bad.append('%d isolated px %s' % (len(orph), orph[:3]))
    return {'opaque': len(pix), 'colours': len(c), 'black': c.get((0, 0, 0), 0) / max(1, len(pix)),
            'bad': bad, 'bbox': (min(x for (x, y) in px), min(y for (x, y) in px),
                                 max(x for (x, y) in px), max(y for (x, y) in px))}


def crown_mouth(P):
    """The crown (top of the hat, or of the hair when it is off) and the mouth centre, as texels:
    the approved hat's front-point crown is (48, 1) and the mouth (48, 41) before any offset."""
    hx, hy = P.head
    bx, by = P.bob
    if P.hat is not None:
        crown = (48 + bx + hx + P.hat_off[0] + P.ox, 1 + by + hy + P.hat_off[1] + P.oy)
    else:
        crown = (48 + bx + hx + P.ox, 9 + by + hy + P.oy)
    mouth = (48 + bx + hx + P.ox, 41 + by + hy + P.oy)
    return crown, mouth


def main(names):
    allowed = approved_colours()
    fatal = 0
    for name in names:
        frames = S.SHEETS[name]()
        tot = Counter()
        print('%s: %d frames' % (name, len(frames)))
        for i, (n, P, hold) in enumerate(frames):
            px = A.render(P)
            r = audit_frame(px, P.fw, P.fh, allowed, bust=P.crop is not None)
            im = kit.image(px, P.fw, P.fh)
            tot.update(p[:3] for p in kit.pixels_of(im) if p[3])
            crown, mouth = crown_mouth(P)
            anc = S.anchors(name, i, P)
            fatal += len(r['bad'])
            print('  f%-2d %-10s %.2fs  opaque %4d  colours %2d  black %4.1f%%  box %s  crown %s mouth %s  %s%s'
                  % (i, n, hold, r['opaque'], r['colours'], 100 * r['black'], r['bbox'], crown, mouth,
                     '; '.join(r['bad']) or 'clean',
                     ''.join('  %s %s' % kv for kv in anc.items())))
        n_ = sum(tot.values())
        print('  sheet: colours %d, black %.1f%%' % (len(tot), 100 * tot[(0, 0, 0)] / n_))
    return fatal


if __name__ == '__main__':
    names = sys.argv[1:] or list(S.SHEETS)
    sys.exit(1 if main(names) else 0)
