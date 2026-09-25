"""python jlint.py  - craft, palette and shading checks on Captain Burak's juggle frames.

Three kinds of damage are easy to ship across twelve rotated frames and hard to see:

  * rotation crumbs: orphan pixels, holes punched in the middle of a body, a keyline gone two thick;
  * a colour that is not on the approved burak_boss.png (the juggle may only reuse his 38); and
  * the SHADING going wrong: a relight that refits the light to each rotated box collapses the ramp
    into its tails (Mason's first pass measured 31% deep shadow against his own 14%). So the ramps are
    measured here per frame, against the approved sheet's own split, with bands that fail the build.

The orphan / thick-keyline checks run on HIS BODY only: impact lines, motion arcs and specks are
one pixel wide on purpose. They are reported, not fatal; holes, off-palette colours, semi-alpha and
a ramp or keyline share outside its band are fatal.
"""
import os
import sys
from collections import Counter

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jkit as J  # noqa: E402
import jposes  # noqa: E402
import kit  # noqa: E402
from PIL import Image  # noqa: E402

APPROVED = os.path.normpath(os.path.join(HERE, '..', '..', 'Assets', 'Characters', 'BurakBoss', 'burak_boss.png'))
BLACK = (0, 0, 0)
RAMPS = {'coat': 'TRVv', 'skin': '2345'}
# His approved sheet is 24.8% / 25.9% keyline. A 192x144 juggle frame carries the same interior line
# (coat trim, face, limbs outlined over the body) but loses some to the rotations' re-outline.
KEYLINE_BAND = (0.20, 0.32)
# Ramp shares may move with the pose: a body turned to face the key light honestly catches more
# highlight, one turned away throws more shadow. They may not swallow the middle tones. The bands are
# set round the approved sheet's own split (printed by the lint).
RAMP_SLACK = {'coat': ((0.5, 2.2), (0.6, 1.5), (0.55, 1.7), (0.4, 2.4)),
              # the skin's deep floor is 0.25x, not 0.3x: lying head-right (frames 9-11) his jaw turns
              # to the upper-left light and honestly loses its shadow, and the hat hides the shaded
              # side of his head; the base tone, which a broken relight would swallow, stays at 43-54%
              'skin': ((0.3, 3.0), (0.6, 1.5), (0.5, 1.8), (0.25, 3.0))}


def rgb(k):
    return kit.PAL[k][:3]


def approved_sheet():
    im = Image.open(APPROVED).convert('RGBA')
    px = [c for c in kit.pixels_of(im) if c[3]]
    return im, px


def ramp_shares(counter, ramp):
    vals = [counter.get(rgb(k), 0) for k in ramp]
    n = sum(vals)
    return [v / n if n else 0.0 for v in vals], n


def craft(px, own):
    """px: frame keys; own: frame owners (to tell his body from the effects)."""
    bad = Counter()
    for y in range(J.FH):
        for x in range(J.FW):
            if (x, y) in px:
                continue
            if all((x + dx, y + dy) in px for dx, dy in J.N4):
                bad['hole'] += 1
    for q, k in px.items():
        if own.get(q) == 'fx':
            continue
        n = sum((q[0] + dx, q[1] + dy) in px for dx, dy in J.N4)
        if n < 2:
            bad['orphan'] += 1
        if k == 'k' and n == 4:
            # black with nothing but black and an edge on two sides: a doubled outer keyline
            edge = [(q[0] + dx, q[1] + dy) for dx, dy in J.N4
                    if any((q[0] + dx + ex, q[1] + dy + ey) not in px for ex, ey in J.N4)]
            if len(edge) >= 2 and all(px[e] == 'k' for e in edge):
                bad['thick keyline'] += 1
    return bad


def build_all():
    """Every frame's keys and owners (the owners come from a canvas rebuilt alongside)."""
    out = []
    for name, fn, hold in jposes.FRAMES:
        cv_holder = {}
        orig = J.finish

        def capture(cv):
            cv_holder['own'] = dict(cv.own)
            return orig(cv)
        J.finish = capture
        try:
            px = fn()
        finally:
            J.finish = orig
        out.append((name, px, cv_holder.get('own', {}), hold))
    return out


def main():
    ref_im, ref_px = approved_sheet()
    ref_cols = {c[:3] for c in ref_px}
    ref_c = Counter(c[:3] for c in ref_px)
    ref_black = ref_c[BLACK] / len(ref_px)
    ref_ramps = {name: ramp_shares(ref_c, ramp)[0] for name, ramp in RAMPS.items()}
    print('approved burak_boss.png: %d px, %d colours, keyline %.1f%%' % (len(ref_px), len(ref_cols), 100 * ref_black))
    for name in RAMPS:
        print('   %s ramp %s: %s' % (name, RAMPS[name], ' '.join('%4.1f%%' % (100 * s) for s in ref_ramps[name])))
    bands = {name: [(ref_ramps[name][i] * lo, ref_ramps[name][i] * hi) for i, (lo, hi) in enumerate(RAMP_SLACK[name])]
             for name in RAMPS}

    print('\n%-3s %-15s %6s %4s %7s %6s  %-26s %-26s %s' % ('#', 'frame', 'px', 'col', 'keyline', '(body)', 'coat T/R/V/v', 'skin 2/3/4/5', 'findings'))
    fatal = total = 0
    sheet_c = Counter()
    for i, (name, px, own, hold) in enumerate(build_all()):
        im = kit.image(px, J.FW, J.FH)
        pix = [c for c in kit.pixels_of(im) if c[3]]
        semi = sum(1 for c in kit.pixels_of(im) if 0 < c[3] < 255)
        c = Counter(p[:3] for p in pix)
        sheet_c.update(c)
        key = c[BLACK] / len(pix)
        fails = []
        off = set(c) - ref_cols
        if off:
            fails.append('off-palette %s' % sorted('#%02X%02X%02X' % t for t in off))
        if semi:
            fails.append('semi-alpha %d' % semi)
        if not KEYLINE_BAND[0] <= key <= KEYLINE_BAND[1]:
            fails.append('keyline %.1f%% outside %.0f-%.0f%%' % (100 * key, 100 * KEYLINE_BAND[0], 100 * KEYLINE_BAND[1]))
        shares = {}
        for rname, ramp in RAMPS.items():
            sh, n = ramp_shares(c, ramp)
            shares[rname] = sh
            if n >= 40:
                for j, (lo, hi) in enumerate(bands[rname]):
                    if not lo <= sh[j] <= hi:
                        fails.append('%s[%s] %.1f%% outside %.1f-%.1f%%' % (rname, ramp[j], 100 * sh[j], 100 * lo, 100 * hi))
        body = [kit.PAL[k][:3] for q, k in px.items() if own.get(q) != 'fx']
        key_body = sum(1 for t in body if t == BLACK) / max(1, len(body))
        bad = craft(px, own)
        total += sum(bad.values()) + len(fails)
        fatal += len(fails) + bad['hole']
        findings = '; '.join(fails + ['%d %s' % (v, k) for k, v in bad.items() if v]) or 'clean'
        print('%-3d %-15s %6d %4d %6.1f%% %5.1f%%  %-26s %-26s %s'
              % (i, name, len(pix), len(c), 100 * key, 100 * key_body,
                 ' '.join('%4.1f' % (100 * s) for s in shares['coat']),
                 ' '.join('%4.1f' % (100 * s) for s in shares['skin']), findings))
    n = sum(sheet_c.values())
    print('\nsheet: %d colours (approved sheet %d), keyline %.1f%% (approved %.1f%%)'
          % (len(sheet_c), len(ref_cols), 100 * sheet_c[BLACK] / n, 100 * ref_black))
    for rname, ramp in RAMPS.items():
        sh, _ = ramp_shares(sheet_c, ramp)
        print('   %s ramp %s: %s   (approved %s)' % (rname, ramp, ' '.join('%4.1f%%' % (100 * s) for s in sh),
                                                    ' '.join('%4.1f%%' % (100 * s) for s in ref_ramps[rname])))
    print('\n%d findings, %d fatal (holes, off-palette, semi-alpha, keyline or ramp outside its band)' % (total, fatal))
    return fatal


if __name__ == '__main__':
    sys.exit(1 if main() else 0)
