"""python lint.py  - craft, palette and shading checks on Computah's juggle frames.

Reads nothing but his approved sheets and writes nothing at all.

THE NUMBERS COME FROM HIS OWN SHEETS, measured here every run rather than typed in:
the keyline share and colour count per frame, and how his two ramps -- the six-tone
shell and the five-tone armour -- are distributed.  The juggle frames are held to
the band those sheets actually span (with a little slack), per frame.

THE RAMP BAND IS THE LIGHTING RULE'S TRIPWIRE.  A tumbling sprite that has been
rotated instead of re-lit ends up lit from below, and the symptom that gives it away
is the ramp collapsing into its tails (Mason's first relight measured 31% deep shadow
against a 14% source).  Computah's frames are shaded by his rig's own Canvas against
its one fixed light, so they should sit inside his sheets' band; if a later change
breaks that, this fails.

Craft: no pure black anywhere (his keyline is #0C111A), no semi-alpha, nothing off
his palette, no pinholes, and no edge of his body that is not keyline -- except the
thin motion streaks, which are air and are drawn without one on purpose.
"""
import glob
import os
import sys
from collections import Counter

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import jrig as J          # noqa: E402
import poses             # noqa: E402
from PIL import Image    # noqa: E402

ASSETS = os.path.normpath(os.path.join(HERE, '..', '..', 'Assets', 'Characters',
                                       'Computah'))
KEY = (0x0C, 0x11, 0x1A)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))


def hx(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


SHELL = [hx(c) for c in J.M.PAL['shell']]
ARMOUR = [hx(c) for c in J.M.PAL['armour']]
STREAK = poses.STREAK[:3]


RAMP_OF = {}
for _i, _v in enumerate(SHELL):
    RAMP_OF[_v] = ('shell', _i)
for _i, _v in enumerate(ARMOUR):
    RAMP_OF[_v] = ('armour', _i)


def light_slope(get, w, h):
    """Which way the light falls, measured rather than assumed.  For every texel of
    his shell or armour whose up-left and down-right neighbours are on the SAME
    ramp, take (ramp step down-right) - (ramp step up-left).  Lit from the upper
    left, a surface darkens going down-right and this is positive; a sprite that
    has been turned without re-lighting goes negative wherever it is upside down."""
    tot = n = 0
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            a, b = RAMP_OF.get(get(x - 1, y - 1)), RAMP_OF.get(get(x + 1, y + 1))
            m = RAMP_OF.get(get(x, y))
            if a and b and m and a[0] == b[0] == m[0]:
                tot += b[1] - a[1]
                n += 1
    return tot / float(n) if n else 0.0


def shares(c, ramp):
    n = sum(c.get(v, 0) for v in ramp)
    return [c.get(v, 0) / n if n else 0.0 for v in ramp]


def frame_counter(px, x0, x1, h):
    c = Counter()
    for y in range(h):
        for x in range(x0, x1):
            p = px[x, y]
            if p[3]:
                c[p[:3]] += 1
    return c


def reference():
    """His approved 96x96 body sheets: the allowed colours, and the per-frame bands."""
    allowed = set()
    rows = []
    for path in sorted(glob.glob(os.path.join(ASSETS, 'computah_*.png'))):
        im = Image.open(path).convert('RGBA')
        if im.height != 96 or im.width % 96:
            continue                        # props are their own size and rules
        px = im.load()
        for f in range(im.width // 96):
            c = frame_counter(px, f * 96, (f + 1) * 96, 96)
            if not c:
                continue
            allowed |= set(c)
            n = sum(c.values())
            ox = f * 96

            def get(x, y, px=px, ox=ox):
                p = px[ox + x, y]
                return p[:3] if p[3] else None
            rows.append({'key': c.get(KEY, 0) / n, 'cols': len(c),
                         'shell': shares(c, SHELL), 'armour': shares(c, ARMOUR),
                         'slope': light_slope(get, 96, 96)})
    band = {
        'key': (min(r['key'] for r in rows), max(r['key'] for r in rows)),
        'cols': (min(r['cols'] for r in rows), max(r['cols'] for r in rows)),
        'shell': [(min(r['shell'][i] for r in rows), max(r['shell'][i] for r in rows))
                  for i in range(6)],
        'armour': [(min(r['armour'][i] for r in rows),
                    max(r['armour'][i] for r in rows)) for i in range(5)],
        'deep': (min(r['shell'][4] + r['shell'][5] for r in rows),
                 max(r['shell'][4] + r['shell'][5] for r in rows)),
        'slope': (min(r['slope'] for r in rows), max(r['slope'] for r in rows)),
    }
    return allowed, band, len(rows)


def figure(g):
    """His body: the largest 8-connected run of opaque pixels."""
    W, H = len(g[0]), len(g)
    seen = [[False] * W for _ in range(H)]
    best = []
    for y in range(H):
        for x in range(W):
            if not g[y][x][3] or seen[y][x]:
                continue
            stack, part = [(x, y)], []
            seen[y][x] = True
            while stack:
                a, b = stack.pop()
                part.append((a, b))
                for dx, dy in N8:
                    u, v = a + dx, b + dy
                    if 0 <= u < W and 0 <= v < H and g[v][u][3] and not seen[v][u]:
                        seen[v][u] = True
                        stack.append((u, v))
            if len(part) > len(best):
                best = part
    return set(best)


def craft(g, allowed):
    W, H = len(g[0]), len(g)
    bad = Counter()
    body = figure(g)

    def o(x, y):
        return 0 <= x < W and 0 <= y < H and g[y][x][3] > 0

    for y in range(H):
        for x in range(W):
            p = g[y][x]
            if not p[3]:
                if all(o(x + dx, y + dy) for dx, dy in N4):
                    bad['pinhole'] += 1
                continue
            if p[3] != 255:
                bad['semi-alpha'] += 1
            if p[:3] == (0, 0, 0):
                bad['pure black'] += 1
            if p[:3] not in allowed and p[:3] != STREAK:
                bad['off-palette'] += 1
            if (x, y) not in body:
                continue
            if sum(o(x + dx, y + dy) for dx, dy in N4) < 2 and p[:3] != STREAK:
                bad['orphan'] += 1
            edge = any(not o(x + dx, y + dy) for dx, dy in N4)
            if edge and p[:3] not in (KEY, STREAK):
                bad['keyline gap'] += 1
    return bad


def stats(g):
    c = Counter(p[:3] for row in g for p in row if p[3])
    n = sum(c.values())
    sh = shares(c, SHELL)
    def get(x, y):
        p = g[y][x]
        return p[:3] if p[3] else None
    return {'key': c.get(KEY, 0) / n, 'cols': len(c), 'shell': sh,
            'armour': shares(c, ARMOUR), 'deep': sh[4] + sh[5], 'n': n,
            'slope': light_slope(get, len(g[0]), len(g))}


# Slack on the bands, because a juggle frame is allowed to be a little more extreme
# than any one pose on his sheets -- a body rolled to face the light honestly catches
# a touch more highlight -- but not to leave them.
SLACK_KEY = 0.02
SLACK_RAMP = 0.05
MAX_COLOURS = 32          # computah_redesign/checks.py's own ceiling

# JUSTIFIED OUTLIERS -- the contract's "except for justified outliers like an extreme
# rotation", written down per frame and per number so nothing else can hide behind
# them.  tumble_a and tumble_b are the two most-inverted frames of the turn (135 and
# 225 degrees): turned over, faces of him that no upright sheet frame ever shows to
# the light -- the soles and the undersides of the pelvis and the barrel -- face it,
# and he honestly catches more highlight and throws less deep shadow than any upright
# frame.  The light itself is measured by the slope column and stays firmly positive
# on both (a turned-not-relit raster reads about -0.4 at these angles; see
# light_slope), so this is the pose, not the lighting.
EXEMPT = {
    'tumble_a': {'shell[0]': 0.37, 'armour[3]': 0.33},
    'tumble_b': {'shell[0]': 0.41, 'deep': 0.09},
}


def main():
    allowed, band, nref = reference()
    print('reference: %d frames of his approved 96x96 sheets, %d colours'
          % (nref, len(allowed)))
    print('  keyline %.1f-%.1f%%   colours %d-%d   deep shell (4+5) %.1f-%.1f%%'
          % (100 * band['key'][0], 100 * band['key'][1], band['cols'][0],
             band['cols'][1], 100 * band['deep'][0], 100 * band['deep'][1]))
    print('  light slope (tone step down-right) %.2f-%.2f' % band['slope'])
    print('  shell  ' + '  '.join('%4.1f-%4.1f' % (100 * a, 100 * b)
                                  for a, b in band['shell']))
    print('  armour ' + '  '.join('%4.1f-%4.1f' % (100 * a, 100 * b)
                                  for a, b in band['armour']))
    print()
    print('%-15s %6s %4s %6s %5s  %-35s %-26s %s'
          % ('frame', 'key', 'col', 'deep', 'slope', 'shell hi..deep',
             'armour hi..deep', 'findings'))
    fatal = 0
    for name, fn, _ in poses.FRAMES:
        g = fn()
        s = stats(g)
        bad = craft(g, allowed)
        fails = []
        lo, hi = band['key']
        if not lo - SLACK_KEY <= s['key'] <= hi + SLACK_KEY:
            fails.append('keyline %.1f%%' % (100 * s['key']))
        if s['cols'] > MAX_COLOURS:
            fails.append('%d colours' % s['cols'])
        ex = EXEMPT.get(name, {})
        noted = []

        def check(label, v, lo, hi):
            if lo - SLACK_RAMP <= v <= hi + SLACK_RAMP:
                return
            lim = ex.get(label)
            # an exemption is a bound, not a blank cheque: past it, it fails again
            if lim is not None and (v <= lim if v > hi else v >= lim):
                noted.append('%s %.1f%% (justified)' % (label, 100 * v))
            else:
                fails.append('%s %.1f%%' % (label, 100 * v))

        check('deep', s['deep'], *band['deep'])
        for i, (lo, hi) in enumerate(band['shell']):
            check('shell[%d]' % i, s['shell'][i], lo, hi)
        for i, (lo, hi) in enumerate(band['armour']):
            check('armour[%d]' % i, s['armour'][i], lo, hi)
        if s['slope'] < band['slope'][0] * 0.75:
            fails.append('LIGHT SLOPE %.2f (lit from the wrong side?)' % s['slope'])
        fails += ['%s %d' % (k, v) for k, v in sorted(bad.items())]
        fatal += len(fails)
        print('%-15s %5.1f%% %4d %5.1f%% %5.2f  %-35s %-26s %s'
              % (name, 100 * s['key'], s['cols'], 100 * s['deep'], s['slope'],
                 ' '.join('%4.1f' % (100 * v) for v in s['shell']),
                 ' '.join('%4.1f' % (100 * v) for v in s['armour']),
                 '; '.join(fails) or ('clean' + (' -- ' + '; '.join(noted)
                                                     if noted else ''))))
    print('\n%d findings' % fatal)
    return fatal


if __name__ == '__main__':
    sys.exit(1 if main() else 0)
