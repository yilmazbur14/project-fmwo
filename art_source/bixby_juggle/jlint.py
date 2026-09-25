"""python jlint.py [--control]  - craft, palette and shading checks on the juggle frames.

Per frame, against the approved beast sheets measured the same way (jmeasure.baseline):
  keyline share and colour count, inside the approved per-frame range widened a little;
  every colour on the approved palette, no semi-alpha;
  ramp shares per material inside the approved range widened (the shading trap: a relight gone wrong
  collapses a ramp into its tails);
  light: top-facing texels brighter than bottom-facing ones, per ramp, like every approved frame (a
  turned body that was not relit goes negative: --control proves the check catches it);
  craft on HIS BODY (not the effects): no pinholes, no stray crumbs, no coloured texel on the
  silhouette without a keyline.
"""
import sys

import numpy as np

import jcommon as C
import jmeasure as M
import jposes
import jrot

KEYLINE_PAD = 0.02          # the approved frames run 23.7-25.9% black
COLOUR_MIN = 30
RAMP_PAD = 0.06
# The whole frame must not read lit from below (the approved frames: fur +0.04..+0.11, charcoal
# +0.26..+0.46, bone +0.13..+0.32). The heads keep their hand-painted faces exactly, so an upside-down
# head brings its painted light with it; the whole-frame floor allows for that and no more.
LIGHT_MIN = {'fur': 0.0, 'charcoal': 0.12, 'bone': 0.0}
# The body layer alone is what relight.py lights; it has to sit in the approved bodies' band
# (measured on the live poses with the heads hidden: fur -0.02..+0.20, charcoal +0.37..+0.45,
# bone +0.15..+0.30), less a margin.
BODY_LIGHT_MIN = {'fur': -0.05, 'charcoal': 0.25, 'bone': 0.10}
# craft counts on the approved frames (jlint --baseline): pinholes 1-11, one-texel spikes 44-61
HOLES_MAX = 11
CRUMBS_MAX = 64

N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))


def components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, bool)
    comps = []
    for y, x in zip(*np.nonzero(mask)):
        if seen[y, x]:
            continue
        stack, comp = [(y, x)], []
        seen[y, x] = True
        while stack:
            b, a = stack.pop()
            comp.append((b, a))
            for dx, dy in N8:
                v, u = b + dy, a + dx
                if 0 <= v < h and 0 <= u < w and mask[v, u] and not seen[v, u]:
                    seen[v, u] = True
                    stack.append((v, u))
        comps.append(comp)
    return comps


def craft(body):
    """body: the frame's figure alone (a key array). Pinholes, crumbs, bare silhouette texels."""
    op = body > 0
    h, w = op.shape
    pad = np.pad(op, 1)
    n4 = sum(pad[1 + dy:h + 1 + dy, 1 + dx:w + 1 + dx].astype(int) for dx, dy in N4)
    holes = int((~op & (n4 == 4)).sum())
    crumbs = int((op & (n4 < 2)).sum())
    ring = op & (n4 < 4)
    bare = int((ring & (body != jrot.BLACK)).sum())
    comps = components(op)
    small = sorted(len(c) for c in comps if len(c) < 12)
    return dict(holes=holes, crumbs=crumbs, bare=bare, islands=small, parts=len(comps))


def ranges(rows):
    lo = {}
    hi = {}
    for _, m in rows:
        for key in ('keyline', 'colours'):
            lo[key] = min(lo.get(key, 1e9), m[key])
            hi[key] = max(hi.get(key, -1e9), m[key])
        for r, vals in m['ramps'].items():
            for i, v in enumerate(vals):
                k = (r, i)
                lo[k] = min(lo.get(k, 1e9), v)
                hi[k] = max(hi.get(k, -1e9), v)
    return lo, hi


def check(name, m, lo, hi, pal, body_craft=None, body_m=None):
    fails = []
    if body_m is not None:
        for r, mn in BODY_LIGHT_MIN.items():
            v = body_m['light'][r]
            if v is not None and v < mn:
                fails.append('body light %s %+.2f under %+.2f' % (r, v, mn))
    if not lo['keyline'] - KEYLINE_PAD <= m['keyline'] <= hi['keyline'] + KEYLINE_PAD:
        fails.append('keyline %.2f%% outside %.1f-%.1f%%' % (100 * m['keyline'], 100 * (lo['keyline'] - KEYLINE_PAD),
                                                          100 * (hi['keyline'] + KEYLINE_PAD)))
    if m['colours'] < COLOUR_MIN or m['colours'] > len(pal):
        fails.append('%d colours' % m['colours'])
    off = m['palette'] - pal
    if off:
        fails.append('off-palette %s' % sorted(off))
    if m['semi']:
        fails.append('%d semi-alpha' % m['semi'])
    for r in ('fur', 'charcoal', 'bone'):
        for i, v in enumerate(m['ramps'][r]):
            a, b = lo[(r, i)] - RAMP_PAD, hi[(r, i)] + RAMP_PAD
            if not a <= v <= b:
                fails.append('%s[%d] %.0f%% outside %.0f-%.0f%%' % (r, i, 100 * v, 100 * a, 100 * b))
    for r, mn in LIGHT_MIN.items():
        v = m['light'][r]
        if v is not None and v < mn:
            fails.append('light %s %+.2f (lit from below)' % (r, v))
    if body_craft:
        c = body_craft
        if c['holes'] > HOLES_MAX:
            fails.append('%d pinholes (approved frames: up to %d)' % (c['holes'], HOLES_MAX))
        if c['bare']:
            fails.append('%d unkeylined silhouette texels' % c['bare'])
        if c['crumbs'] > CRUMBS_MAX:
            fails.append('%d one-texel spikes (approved frames: up to %d)' % (c['crumbs'], CRUMBS_MAX))
        if c['parts'] > 1:
            fails.append('figure in %d pieces %s' % (c['parts'], c['islands']))
    return fails


def main(control=False):
    rows, pal = M.baseline()
    lo, hi = ranges(rows)
    print('approved: keyline %.2f-%.2f%%, colours %d-%d (palette %d)' % (100 * lo['keyline'], 100 * hi['keyline'],
                                                                        lo['colours'], hi['colours'], len(pal)))
    if control:
        import relight
        import contextlib

        @contextlib.contextmanager
        def nothing(theta, mirrored=False):
            yield
        relight.lit = nothing
        print('CONTROL: relight disabled (a plain turn), the light check should fail on turned frames')
    bad = 0
    for i, (name, fn, hold) in enumerate(jposes.FRAMES):
        a = fn()
        m = M.measure(jrot.to_img(a))
        fig = jposes.LAST_FIGURE
        cr = craft(fig) if fig is not None else None
        bm = M.measure(jrot.to_img(jposes.LAST_BODY)) if jposes.LAST_BODY is not None else None
        fails = check(name, m, lo, hi, pal, cr, bm)
        bad += bool(fails)
        print('%2d %-13s %s' % (i, name, M.fmt(m)))
        if bm:
            print('   body layer light: fur %+.2f char %+.2f bone %+.2f;  figure: %d holes, %d spikes, %d piece(s)'
                  % (bm['light']['fur'] or 0, bm['light']['charcoal'] or 0, bm['light']['bone'] or 0,
                     cr['holes'], cr['crumbs'], cr['parts']))
        print('   ' + ('; '.join(fails) if fails else 'clean'))
    print('%d of %d frames with findings' % (bad, len(jposes.FRAMES)))
    return bad


if __name__ == '__main__':
    sys.exit(1 if main('--control' in sys.argv) else 0)
