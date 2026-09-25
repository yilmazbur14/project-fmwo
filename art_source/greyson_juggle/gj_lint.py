"""python gj_lint.py  - craft, palette, shading and placement checks on Greyson's juggle frames.

Reads his approved sheets and writes nothing.

THE NUMBERS COME FROM HIS OWN SHEETS, measured every run: the pure-black keyline's share, the colour
count, and how his skin ramp (1..6) and his purple ramp (A..E) are spread, per frame. The reference is
every FRONT view he has approved -- greyson_redesign f0-f1 (the design of record) and the fight
approval's f0, f2, f4 -- since every juggle frame shows his front. The purple ramp is held to the
fight frames alone, the ones that wear the cannon (the redesign's purple is only the trunks).

THE LIGHT IS MEASURED, not assumed (light_slope): the average tone step from a pixel's up-left
neighbour to its down-right one, within one ramp. Lit from the upper left it is positive. A turned
but not re-lit raster goes negative upside down -- the negative control proves the measure can tell.
Every frame must stay positive, in his sheets' range.

Craft: pure black (#000000) is his keyline; no semi-alpha, nothing off the fight palette, no
pinholes, no edge of his figure that is not keyline, no stray pixels. Effects (dust, arcs, sweat,
shock ticks) float free of him by design and are exempt from the keyline rules.

Placement: every frame is re-drawn on a padded canvas, and the figure must not reach past the frame
(nothing clipped); nothing sits on the frame's top row or side columns; the ground frames stand on
the feet row.
"""
import os
import sys
from collections import Counter

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gj_rig as R        # noqa: E402
import gj_poses as P      # noqa: E402
from PIL import Image     # noqa: E402

K = R.K
ASSETS = os.path.normpath(os.path.join(HERE, '..', '..', 'Assets', 'Characters', 'Greyson'))
FRONTS = (('greyson_redesign', (0, 1)), ('greyson_fight_approval', (0, 2, 4)))
CANNON_FRONTS = (('greyson_fight_approval', (0, 2, 4)),)
FW = 112
KEY = (0, 0, 0)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
RGB = {k: v[:3] for k, v in K.PAL.items()}
SKIN = [RGB[k] for k in '123456']
PURPLE = [RGB[k] for k in 'ABCDE']
RAMP_OF = {}
for _name, _keys in (('skin', '123456'), ('hair', 'abcde'), ('purple', 'ABCDE'), ('white', 'WXx')):
    for _i, _k in enumerate(_keys):
        RAMP_OF[RGB[_k]] = (_name, _i)
GROUND = (0, 7, 9, 10, 11)


def light_slope(get, w, h, only=None):
    """The mean tone step from a pixel's up-left neighbour to its down-right one, within one ramp
    (all ramps, or only the one named)."""
    tot = n = 0
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            m = RAMP_OF.get(get(x, y))
            if not m or (only and m[0] != only):
                continue
            a, b = RAMP_OF.get(get(x - 1, y - 1)), RAMP_OF.get(get(x + 1, y + 1))
            if a and b and a[0] == b[0] == m[0]:
                tot += b[1] - a[1]
                n += 1
    return tot / float(n) if n else 0.0


def shares(c, ramp):
    n = sum(c.get(v, 0) for v in ramp)
    return [c.get(v, 0) / float(n) if n else 0.0 for v in ramp]


def stats_of(get, w, h):
    c = Counter()
    for y in range(h):
        for x in range(w):
            p = get(x, y)
            if p is not None:
                c[p] += 1
    n = sum(c.values())
    sk, pu = shares(c, SKIN), shares(c, PURPLE)
    return {'key': c.get(KEY, 0) / float(n), 'cols': len(c), 'skin': sk, 'purple': pu,
            'slope': light_slope(get, w, h), 'n': n,
            'slope_skin': light_slope(get, w, h, 'skin'),
            'slope_purple': light_slope(get, w, h, 'purple'),
            'shadow_skin': sk[4] + sk[5], 'deep_skin': sk[5], 'shadow_purple': pu[3] + pu[4]}


def _getter(px, ox=0):
    def get(x, y):
        p = px[ox + x, y]
        return p[:3] if p[3] else None
    return get


def reference(sheets=FRONTS):
    rows = []
    for name, frames in sheets:
        im = Image.open(os.path.join(ASSETS, name + '.png')).convert('RGBA')
        px = im.load()
        for f in frames:
            rows.append(stats_of(_getter(px, f * FW), FW, FW))

    def band(key, i=None):
        vals = [r[key] if i is None else r[key][i] for r in rows]
        return (min(vals), max(vals))
    return {'key': band('key'), 'cols': band('cols'), 'slope': band('slope'),
            'skin': [band('skin', i) for i in range(6)],
            'purple': [band('purple', i) for i in range(5)],
            'slope_skin': band('slope_skin'), 'slope_purple': band('slope_purple'),
            'shadow_skin': band('shadow_skin'), 'deep_skin': band('deep_skin'),
            'shadow_purple': band('shadow_purple')}, len(rows)


def figure(img):
    """The largest 8-connected piece: him. Everything else is an effect."""
    px = img.load()
    W, H = img.size
    seen, best = set(), []
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
            if (x == 0 or x == W - 1 or y == 0) and p[3]:
                bad['on the frame edge'] += 1
            if (x, y) not in body:
                continue
            if not any(o(x + dx, y + dy) for dx, dy in N8):
                bad['stray'] += 1
            if any(not o(x + dx, y + dy) for dx, dy in N4) and p[:3] != KEY:
                bad['keyline gap'] += 1
    return bad, body


def negative_control():
    """The measure must be able to fail: the approved idle's RASTER turned (never re-lit) reads
    negative upside down."""
    im = Image.open(os.path.join(ASSETS, 'greyson_redesign.png')).convert('RGBA').crop((0, 0, FW, FW))
    out = []
    for ang in (0, 90, 180):
        r = im.rotate(-ang, resample=Image.NEAREST, expand=True)
        out.append((ang, light_slope(_getter(r.load()), r.width, r.height)))
    return out


SLACK_KEY = 0.02
# THE RAMP GUARD. The failure the contract warns of is the shadow swallowing the ramp when a turned
# figure is re-lit wrongly (one pass measured 31% deep shadow against a 14% source), so each frame's
# SHADOW shares are held near his sheets': the skin's two darkest tones, its darkest alone, and the
# purple's two darkest. The individual tones are printed for reading; they move honestly with the
# angle (a limb lit along its length has no dark side; his chest turned to the light has more
# highlight), so they are not held to the upright sheets one by one.
SLACK_SHADOW = 0.08
SLACK_DEEP = 0.06
SLACK_PURPLE = 0.10
# JUSTIFIED OUTLIERS: {frame: {measure: bound}}, each with its reason; past the bound it fails again.
EXEMPT = {}


def frames():
    for i, (name, fn, _) in enumerate(P.FRAMES):
        cv = fn()
        yield i, name, cv


def main():
    band, nref = reference()
    gun_band, ngun = reference(CANNON_FRONTS)
    print('reference: his %d approved front views (%s)'
          % (nref, ', '.join('%s f%s' % (n, '/'.join(map(str, f))) for n, f in FRONTS)))
    print('  black %.1f-%.1f%%   colours %d-%d   light slope %.2f-%.2f'
          % (100 * band['key'][0], 100 * band['key'][1], band['cols'][0], band['cols'][1],
             band['slope'][0], band['slope'][1]))
    print('  skin 1..6   ' + '  '.join('%4.1f-%4.1f' % (100 * a, 100 * b) for a, b in band['skin']))
    print('  purple A..E ' + '  '.join('%4.1f-%4.1f' % (100 * a, 100 * b)
                                      for a, b in gun_band['purple'])
          + '   (the %d fight fronts, cannon and trunks)' % ngun)
    print('  shadow shares: skin 5+6 %.1f-%.1f%%, skin 6 %.1f-%.1f%%, purple D+E %.1f-%.1f%%'
          % (100 * band['shadow_skin'][0], 100 * band['shadow_skin'][1], 100 * band['deep_skin'][0],
             100 * band['deep_skin'][1], 100 * gun_band['shadow_purple'][0],
             100 * gun_band['shadow_purple'][1]))
    print('  light slope per ramp: skin %.2f-%.2f, purple %.2f-%.2f'
          % (band['slope_skin'] + gun_band['slope_purple']))
    print('  negative control (the approved idle raster turned, never re-lit): '
          + ', '.join('%d deg %+.2f' % t for t in negative_control()))
    print()
    print('%-9s %6s %4s %6s %5s %5s  %-29s %-24s %s'
          % ('frame', 'black', 'col', 'slope', 'skin', 'purp', 'skin 1..6', 'purple A..E',
             'findings'))
    fatal = 0
    rows = []
    for i, name, cv in frames():
        img = cv.image()
        s = stats_of(_getter(img.load()), img.width, img.height)
        bad, body = craft(img)
        fails, noted = [], []
        ex = EXEMPT.get(name, {})
        lo, hi = band['key']
        if not lo - SLACK_KEY <= s['key'] <= hi + SLACK_KEY:
            fails.append('black %.1f%%' % (100 * s['key']))
        if s['cols'] > band['cols'][1] + 2:
            fails.append('%d colours' % s['cols'])
        if s['slope'] < band['slope'][0] * 0.75:
            fails.append('LIGHT SLOPE %.2f' % s['slope'])
        for label, v, lim in (('skin shadow', s['shadow_skin'], band['shadow_skin'][1] + SLACK_SHADOW),
                              ('skin deepest', s['deep_skin'], band['deep_skin'][1] + SLACK_DEEP),
                              ('purple shadow', s['shadow_purple'],
                               gun_band['shadow_purple'][1] + SLACK_PURPLE)):
            if v <= lim:
                continue
            ok = ex.get(label)
            if ok is not None and v <= ok:
                noted.append('%s %.1f%% (justified)' % (label, 100 * v))
            else:
                fails.append('%s %.1f%% over %.1f%%' % (label, 100 * v, 100 * lim))
        for label in ('slope_skin', 'slope_purple'):
            if s[label] <= 0.0:
                fails.append('%s %.2f: NOT LIT FROM THE UPPER LEFT' % (label, s[label]))
        e = P.extent(cv.fig)
        if e[0] < 1 or e[1] < 1 or e[2] > R.W - 2 or e[3] > R.H - 1:
            fails.append('CLIPPED (figure spans %s)' % (e,))
        fy = max(y for (x, y) in body)
        if i in GROUND and fy != R.FEET[1]:
            fails.append('lowest row %d, not the feet row %d' % (fy, R.FEET[1]))
        fails += ['%s %d' % (k, v) for k, v in sorted(bad.items())]
        fatal += len(fails)
        rows.append((i, name, s))
        print('%-9s %5.1f%% %4d %6.2f %5.2f %5.2f  %-29s %-24s %s'
              % (name, 100 * s['key'], s['cols'], s['slope'], s['slope_skin'], s['slope_purple'],
                 ' '.join('%4.1f' % (100 * v) for v in s['skin']),
                 ' '.join('%4.1f' % (100 * v) for v in s['purple']),
                 '; '.join(fails) or ('clean' + (' -- ' + '; '.join(noted) if noted else ''))))
    print('\n%d findings' % fatal)
    return fatal


if __name__ == '__main__':
    sys.exit(1 if main() else 0)
