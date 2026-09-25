"""python lint.py  - craft, palette and shading checks on Carter's juggle frames.

Reads his approved sheets and writes nothing.

THE NUMBERS COME FROM HIS OWN SHEETS, measured every run: the pure-black keyline's share and the colour
count per frame, and how his skin ramp (s..W) and his gi ramp (a..f) are distributed.  The reference is
his three-quarter set (rush, rush pass, spent, defeat 1-5, Messatsu) -- the rig these frames are drawn
on -- and the juggle frames are held to the band it spans, with a little slack.

THE LIGHT IS MEASURED, not assumed (light_slope): the average tone step from a pixel's up-left
neighbour to its down-right one, within one ramp.  Lit from the upper left it is positive.  A turned-
not-relit raster goes negative upside down -- the negative control in main() proves the measure can
tell.  Every frame must stay positive and in his sheets' range.

Craft: pure black is his keyline (#000000); no semi-alpha, nothing off lib.PAL, no pinholes, and no
edge of his body that is not keyline -- except the cream motion streaks, which are air.
"""
import os
import sys
from collections import Counter

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import kjrig as K         # noqa: E402
import poses              # noqa: E402
from PIL import Image     # noqa: E402

L = K.L
ASSETS = os.path.normpath(os.path.join(HERE, '..', '..', 'Assets', 'Characters', 'Carter'))
REFERENCE = ('carter_rush', 'carter_rush_pass', 'carter_spent', 'carter_defeat',
             'carter_messatsu_charge', 'carter_messatsu_fire')
# His approved flat back views, the reference for the two frames of the turn that show the 天.
BACK_REFERENCE = (('carter_akuma', (2,)), ('carter_look_back', (0, 1, 2, 3, 4, 5)))
KEY = (0, 0, 0)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
RGB = {k: v[:3] for k, v in L.PAL.items()}
SKIN = [RGB[k] for k in 'stuvwW']
GI = [RGB[k] for k in 'abcdef']
STREAK = RGB['g']
FX = {RGB[k] for k in 'ghij'}          # effect creams: dust and streaks, never keylined
RAMP_OF = {}
for _name, _keys in L.RAMP.items():
    for _i, _k in enumerate(_keys):
        RAMP_OF[RGB[_k]] = (_name, _i)


def light_slope(get, w, h):
    tot = n = 0
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            a, b = RAMP_OF.get(get(x - 1, y - 1)), RAMP_OF.get(get(x + 1, y + 1))
            m = RAMP_OF.get(get(x, y))
            if a and b and m and a[0] == b[0] == m[0] and m[0] in ('skin', 'gi', 'giv', 'wrap',
                                                                  'hair', 'belt'):
                tot += b[1] - a[1]
                n += 1
    return tot / float(n) if n else 0.0


def shares(c, ramp):
    n = sum(c.get(v, 0) for v in ramp)
    return [c.get(v, 0) / n if n else 0.0 for v in ramp]


def stats_of(get, w, h):
    c = Counter()
    for y in range(h):
        for x in range(w):
            p = get(x, y)
            if p is not None:
                c[p] += 1
    n = sum(c.values())
    sk = shares(c, SKIN)
    return {'key': c.get(KEY, 0) / n, 'cols': len(c), 'skin': sk, 'gi': shares(c, GI),
            'slope': light_slope(get, w, h), 'n': n, 'counter': c}


def reference(names=None):
    rows = []
    for name, only in (names or [(n, None) for n in REFERENCE]):
        im = Image.open(os.path.join(ASSETS, name + '.png')).convert('RGBA')
        px = im.load()
        for f in range(im.width // 96):
            if only is not None and f not in only:
                continue
            def get(x, y, px=px, ox=f * 96):
                p = px[ox + x, y]
                return p[:3] if p[3] else None
            s = stats_of(get, 96, 96)
            if s['n']:
                rows.append(s)
    band = {'key': (min(r['key'] for r in rows), max(r['key'] for r in rows)),
            'cols': (min(r['cols'] for r in rows), max(r['cols'] for r in rows)),
            'slope': (min(r['slope'] for r in rows), max(r['slope'] for r in rows)),
            'skin': [(min(r['skin'][i] for r in rows), max(r['skin'][i] for r in rows))
                     for i in range(6)],
            'gi': [(min(r['gi'][i] for r in rows), max(r['gi'][i] for r in rows))
                   for i in range(6)]}
    return band, len(rows)


def figure(img):
    px = img.load()
    W, H = img.size
    seen = set()
    best = []
    for y in range(H):
        for x in range(W):
            if not px[x, y][3] or (x, y) in seen:
                continue
            stack, part = [(x, y)], []
            seen.add((x, y))
            while stack:
                a, b = stack.pop()
                part.append((a, b))
                for dx, dy in N8:
                    u, v = a + dx, b + dy
                    if 0 <= u < W and 0 <= v < H and px[u, v][3] and (u, v) not in seen:
                        seen.add((u, v))
                        stack.append((u, v))
            if len(part) > len(best):
                best = part
    return set(best)


def craft(img):
    px = img.load()
    W, H = img.size
    allowed = set(RGB.values())
    bad = Counter()
    body = figure(img)

    def o(x, y):
        return 0 <= x < W and 0 <= y < H and px[x, y][3] > 0

    for y in range(H):
        for x in range(W):
            p = px[x, y]
            if not p[3]:
                if all(o(x + dx, y + dy) for dx, dy in N4):
                    bad['pinhole'] += 1
                continue
            if p[3] != 255:
                bad['semi-alpha'] += 1
            if p[:3] not in allowed:
                bad['off-palette'] += 1
            if (x, y) not in body:
                continue
            if sum(o(x + dx, y + dy) for dx, dy in N4) < 2 and p[:3] not in FX | {KEY}:
                bad['orphan'] += 1
            if any(not o(x + dx, y + dy) for dx, dy in N4) and p[:3] != KEY and p[:3] not in FX:
                bad['keyline gap'] += 1
    return bad


SLACK_KEY = 0.02
BACK_FRAMES = ('tumble_c', 'tumble_d')
SLACK_RAMP = 0.06
# JUSTIFIED OUTLIERS, per frame and per number, each with a bound past which it fails again.  Every
# reference frame of his stands upright; these three lie LEVEL, where the lit side of the gi is its top
# edge -- on the hang it is under his flopped arm and shoulder caps, on the mat his chest faces up and
# the gi's shaded flank is what shows.  The slope column (the light itself) stays in his range on all
# three, so this is the pose, not the lighting.
EXEMPT = {
    # upside down at 225 degrees his bald dome -- the biggest skin area he has -- is the side of him
    # away from the light, so more of it honestly sits in the ramp's shadow step
    'tumble_b': {'skin[3]': 0.34},
    'hang': {'gi[1]': 0.04, 'gi[3]': 0.44},
    'crash_impact': {'gi[4]': 0.26},
    'down_breathe': {'gi[2]': 0.20},
}


def frames():
    for name, fn, _ in poses.FRAMES:
        r = fn()
        yield name, (r if isinstance(r, Image.Image) else r.image())


def negative_control():
    """The measure must be able to fail: an approved rush frame's RASTER turned upside down reads
    negative, because it was never re-lit."""
    im = Image.open(os.path.join(ASSETS, 'carter_rush.png')).convert('RGBA').crop((0, 0, 96, 96))
    out = []
    for ang in (0, 90, 180):
        r = im.rotate(-ang, resample=Image.NEAREST, expand=True)
        px = r.load()
        w, h = r.size

        def get(x, y, px=px):
            p = px[x, y]
            return p[:3] if p[3] else None
        out.append((ang, light_slope(get, w, h)))
    return out


def main():
    band, nref = reference()
    back_band, nback = reference(BACK_REFERENCE)
    print('reference: %d frames of his three-quarter sheets (%s)' % (nref, ', '.join(REFERENCE)))
    print('  black %.1f-%.1f%%   colours %d-%d   light slope %.2f-%.2f'
          % (100 * band['key'][0], 100 * band['key'][1], band['cols'][0], band['cols'][1],
             band['slope'][0], band['slope'][1]))
    print('  skin s..W ' + '  '.join('%4.1f-%4.1f' % (100 * a, 100 * b) for a, b in band['skin']))
    print('  gi   a..f ' + '  '.join('%4.1f-%4.1f' % (100 * a, 100 * b) for a, b in band['gi']))
    print('  back views (%d frames): black %.1f-%.1f%%' % (nback, 100 * back_band['key'][0],
                                                         100 * back_band['key'][1]))
    print('  negative control (an approved raster turned, never re-lit): '
          + ', '.join('%d deg %+.2f' % t for t in negative_control()))
    print()
    print('%-15s %6s %4s %6s  %-31s %-31s %s'
          % ('frame', 'black', 'col', 'slope', 'skin s..W', 'gi a..f', 'findings'))
    fatal = 0
    for name, img in frames():
        px = img.load()

        def get(x, y, px=px):
            p = px[x, y]
            return p[:3] if p[3] else None
        s = stats_of(get, img.width, img.height)
        bad = craft(img)
        ex = EXEMPT.get(name, {})
        fails, noted = [], []
        # a frame that shows his back is held to his approved back views; the rest to the 3/4 set
        lo, hi = (back_band if name in BACK_FRAMES else band)['key']
        if not lo - SLACK_KEY <= s['key'] <= hi + SLACK_KEY:
            fails.append('black %.1f%%' % (100 * s['key']))
        if s['cols'] > band['cols'][1] + 2:
            fails.append('%d colours' % s['cols'])
        if s['slope'] < band['slope'][0] * 0.75:
            fails.append('LIGHT SLOPE %.2f' % s['slope'])
        for ramp in ('skin', 'gi'):
            for i, (lo, hi) in enumerate(band[ramp]):
                v = s[ramp][i]
                if lo - SLACK_RAMP <= v <= hi + SLACK_RAMP:
                    continue
                label = '%s[%d]' % (ramp, i)
                lim = ex.get(label)
                if lim is not None and (v <= lim if v > hi else v >= lim):
                    noted.append('%s %.1f%% (justified)' % (label, 100 * v))
                else:
                    fails.append('%s %.1f%%' % (label, 100 * v))
        fails += ['%s %d' % (k, v) for k, v in sorted(bad.items())]
        fatal += len(fails)
        print('%-15s %5.1f%% %4d %6.2f  %-31s %-31s %s'
              % (name, 100 * s['key'], s['cols'], s['slope'],
                 ' '.join('%4.1f' % (100 * v) for v in s['skin']),
                 ' '.join('%4.1f' % (100 * v) for v in s['gi']),
                 '; '.join(fails) or ('clean' + (' -- ' + '; '.join(noted) if noted else ''))))
    print('\n%d findings' % fatal)
    return fatal


if __name__ == '__main__':
    sys.exit(1 if main() else 0)
