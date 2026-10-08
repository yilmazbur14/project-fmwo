"""The approval pass's frames, before and after, built in memory from the rigs. Writes nothing.

  idle f0     jordan_idle.png frame 0, which is v2's approved frame 0 (jv2_frames.build(0))
  summon f2   jordan_summon.png frame 2, the pop / fist-pump, which is v2's approved frame 1
  portrait    Assets/Characters/Jordan/portrait.png, jordan_derived/portrait_v2.py's method
  idle strip  all four idle frames (janim_idle's builders), for the in-game mock

"before" is the rig as it is, and check() proves it equals the live PNGs pixel for pixel
(imgdiff.pixel_diff). "after" is the same builders run inside jfit_body.fitted(), which swaps the
fitted tee into the imported jv2_body module for the length of the `with` block only.

Nothing here edits another rig: jordan_anims and jordan_derived are imported and run as they are.
Their own "must equal the approved frame" checks (janim_base.make_frames) compare against the
shipped jordan_redesign_v2.png, which the fitted frames by design do not equal, so the fitted strips
are built by calling their frame builders directly.
"""
import contextlib
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
ROOT = os.path.dirname(ART)
sys.path.insert(0, HERE)
import jfit_body as JF  # noqa: E402

for _d in ('jordan_anims', 'jordan_derived'):
    _p = os.path.join(ART, _d)
    if _p not in sys.path:
        sys.path.append(_p)

import jv2_frames as F  # noqa: E402  (read-only)
import janim_base as AB  # noqa: E402  (read-only)
import janim_idle as AI  # noqa: E402  (read-only)
import janim_summon as AS  # noqa: E402  (read-only)
import portrait_v2 as PV  # noqa: E402  (read-only; its main() is never called)
import dkit  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402
from PIL import Image  # noqa: E402

B = JF.B
ASSETS = os.path.join(ROOT, 'Assets', 'Characters', 'Jordan')


def live(name):
    return Image.open(os.path.join(ASSETS, name + '.png')).convert('RGBA')


def live_frame(name, i, size=96):
    return live(name).crop((size * i, 0, size * i + size, size))


def _ctx(fitted):
    return JF.fitted() if fitted else contextlib.nullcontext()


#THE SPRITE FRAMES

def idle_f0(fitted):
    with _ctx(fitted):
        return F.frame_px(0)


def summon_f2(fitted):
    with _ctx(fitted):
        return F.frame_px(1)


def idle_strip(fitted, with_fx=False):
    """[px] for the four idle frames, frame coordinates (with_fx: [(px, fx pixels)])."""
    out = []
    with _ctx(fitted):
        for b in AI.builders():
            cv, fx = b()
            out.append((AB.finish(cv), {(x + AB.ANCHOR_SHIFT, y) for (x, y) in fx}))
    return out if with_fx else [px for px, _fx in out]


def summon_pump(fitted):
    """janim_summon's own build of its pop frame (frame 2), to prove it still equals v2's frame 1."""
    with _ctx(fitted):
        return AB.finish(AS.build_pump()[0])


#THE PORTRAIT

# portrait_v2.BODY is hand detail on v2's body at 1.5x. The entries on the parts the fit leaves alone
# are kept as they are: the thin neck, the collar band, the drip stain's core and the crown's jewel.
# The ones drawn for the sack go: the drooping near sleeve's two creases where it bunched, and the far
# side's long vertical drape fold and armpit. The fitted near sleeve gets back the lower of v2's two
# creases (its underside pulled in toward the armpit, the one a snug sleeve on a raised elbow still
# makes), with its lit lip.
KEEP = [(34, 48), (35, 48), (36, 48), (37, 48), (38, 48), (30, 52), (31, 53), (40, 51),           # neck
        (27, 56), (30, 57), (31, 57), (32, 57), (33, 57), (42, 54), (42, 55), (39, 56),           # collar
        (41, 57), (42, 58),                                                                       # drip
        (32, 60)]                                                                                 # jewel
FIT_DETAIL = {(21, 62): 'k', (20, 63): 'k', (22, 61): 'T'}
BODY_FIT = {q: PV.BODY[q] for q in KEEP}
BODY_FIT.update(FIT_DETAIL)


def portrait_px(fitted):
    if not fitted:
        return PV.build()
    saved = PV.BODY
    PV.BODY = BODY_FIT
    try:
        with JF.fitted():
            return PV.build()
    finally:
        PV.BODY = saved


def portrait(fitted):
    return dkit.image(portrait_px(fitted), PV.W, PV.H, PV.PAL)


def portrait_target(fitted):
    """The derived-art target: the same crop of the (fitted) sprite's frame 0 at 1x, box, far hand and
    raised forearm out, as portrait_v2.crop_numbers measures it."""
    with _ctx(fitted):
        return PV.crop_numbers()


#MEASURING

def stats(im):
    s = B.stats(im)
    return {'opaque': s['opaque'], 'colours': s['colours'], 'black': s['black'], 'semi': s['semi']}


def check():
    """Everything the approval pass must prove; returns printable lines, raises on a failure."""
    out, bad = [], []

    def ok(name, d):
        out.append('%-58s %s' % (name, 'identical' if d is None else d))
        if d is not None:
            bad.append(name)
    ok('before idle f0 == live jordan_idle.png f0', pixel_diff(B.image(idle_f0(False)), live_frame('jordan_idle', 0)))
    ok('before summon f2 == live jordan_summon.png f2', pixel_diff(B.image(summon_f2(False)), live_frame('jordan_summon', 2)))
    strip = idle_strip(False)
    for i, px in enumerate(strip):
        ok('before idle strip f%d == live jordan_idle.png f%d' % (i, i), pixel_diff(B.image(px), live_frame('jordan_idle', i)))
    ok('before portrait == live portrait.png', pixel_diff(portrait(False), live('portrait')))
    ok('fitted idle strip f0 == fitted idle f0', pixel_diff(B.image(idle_strip(True)[0]), B.image(idle_f0(True))))
    ok('fitted summon build_pump == fitted v2 frame 1', pixel_diff(B.image(summon_pump(True)), B.image(summon_f2(True))))
    ok('v2 parts restored after the fitted builds', pixel_diff(B.image(idle_f0(False)), live_frame('jordan_idle', 0)))
    allowed = {c for c in B.image(F.frame_px(0)).getdata() if c[3]} | {c for c in B.image(F.frame_px(1)).getdata() if c[3]}
    for name, px, fx in (('fitted idle f0', idle_f0(True), set()), ('fitted summon f2', summon_f2(True), F.fx_pixels(1))):
        a = B.audit(px, fx)
        im = B.image(px)
        cols = {c for c in im.getdata() if c[3]}
        low = max(y for (x, y) in px)
        line = '%s: gaps %d, lone %d, holes %d, stray keys %s, colours outside v2\'s %d, lowest row %d' % (
            name, len(a['gaps']), len(a['lone']), len(a['holes']), a['keys'] or 'none', len(cols - allowed), low)
        out.append(line)
        if a['gaps'] or a['lone'] or a['holes'] or a['keys'] or (cols - allowed) or low != 95:
            bad.append(name)
    for i, (px, fx) in enumerate(idle_strip(True, with_fx=True)):
        a = B.audit(px, fx)
        cols = {c for c in B.image(px).getdata() if c[3]}
        out.append('fitted idle f%d: gaps %d, lone %d, holes %d, stray keys %s, colours outside v2s %d' % (
            i, len(a['gaps']), len(a['lone']), len(a['holes']), a['keys'] or 'none', len(cols - allowed)))
        if a['gaps'] or a['lone'] or a['holes'] or a['keys'] or (cols - allowed):
            bad.append('fitted idle f%d' % i)
    if bad:
        raise SystemExit('\n'.join(out) + '\nFAILED: %s' % bad)
    return out


def numbers():
    """(name, before stats, after stats) rows for the report."""
    rows = []
    rows.append(('idle f0', stats(B.image(idle_f0(False))), stats(B.image(idle_f0(True)))))
    rows.append(('summon f2 (fist-pump)', stats(B.image(summon_f2(False))), stats(B.image(summon_f2(True)))))
    for i in (1, 2, 3):
        rows.append(('idle f%d' % i, stats(B.image(idle_strip(False)[i])), stats(B.image(idle_strip(True)[i]))))
    rows.append(('portrait', stats(portrait(False)), stats(portrait(True))))
    return rows


if __name__ == '__main__':
    for ln in check():
        print(ln)
    for name, b, a in numbers():
        print('%-22s before: black %5.2f%%, colours %2d, opaque %4d | after: black %5.2f%%, colours %2d, opaque %4d'
              % (name, 100 * b['black'], b['colours'], b['opaque'], 100 * a['black'], a['colours'], a['opaque']))
    for fitted in (False, True):
        n, blk, cols = portrait_target(fitted)
        print('portrait target (same crop of %s f0 at 1x): black %.2f%%, colours %d' % ('fitted' if fitted else 'v2', 100 * blk, cols))
