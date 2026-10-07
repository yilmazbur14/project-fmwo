"""Write Jordan's five fight sheets (in his approved v2 look), each PNG with its .aseprite beside it,
after checking every frame.

A bare run writes nothing, and a scratch folder inside the live Assets tree is refused:

    python janim_export.py <scratch_dir>     # write all ten files there, for checking
    python janim_export.py --ship            # write them into Assets/Characters/Jordan/

It only ever writes these names: jordan_idle, jordan_summon, jordan_taunt, jordan_hit, jordan_defeat
(.png and .aseprite). Each file is built in a temp folder and moved into place in one step, and each
.aseprite is re-exported and compared with its PNG pixel for pixel (art_source/imgdiff.pixel_diff).

Checked before anything is written, per frame:
  - the frame is 96x96, the strip is horizontal, frame 0 leftmost
  - the lowest drawn row is 95 (his feet, or his knees and the fallen box, stand on it)
  - every colour is one of the approved v2 sheet's 40 (jordan_redesign_v2.png), the black is pure
    #000000, no semi-alpha
  - no keyline gaps, no stray pixels, no pinholes (v2's sneakers close the approved rig's one gap,
    so there are no exceptions)
  - black ratio within 27-32.5% (the skinny build's frames run 30.7-31.9%: thin limbs are mostly
    outline, and the skinny build has less cloth and less jeans inside the same keyline; 27-31.5% for
    the fitted tee earlier on 2026-09-28, 27-29.5% before it)
  - idle frame 0 is v2's frame 0 and summon frame 2 is v2's frame 1, pixel for pixel
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import janim_base as B  # noqa: E402
import janim_idle  # noqa: E402
import janim_summon  # noqa: E402
import janim_taunt  # noqa: E402
import janim_hit  # noqa: E402
import janim_defeat  # noqa: E402

MODULES = [janim_idle, janim_summon, janim_taunt, janim_hit, janim_defeat]
# 27-29.5% until 2026-09-28; the fitted tee (approved "everywhere" that day) takes cloth off a figure
# whose outline stays the same length, so every frame's keyline share rises 1.3-1.6 points (the fitted
# frames run 29.4-31.0%, the hit's impact frame the highest): the ceiling moved to 31.5%. The skinny
# build (approved the same day, art_source/jordan_fit/skinny) thins the arms, the jeans and the tee
# inside keylines that barely shorten: its frames run 30.7-31.9% (the hit's impact frame the highest
# again), so the ceiling moves to 32.5%, the same half-point clear of the highest frame.
BLACK_RANGE = (0.27, 0.325)


def _under(path, root):
    """True if `path` is `root` or inside it, compared by realpath (8.3 short names can't slip past)."""
    p, r = os.path.normcase(os.path.realpath(path)), os.path.normcase(os.path.realpath(root))
    return p == r or p.startswith(r + os.sep)


def approved_colours():
    im = B.approved_sheet()
    flat = getattr(im, 'get_flattened_data', None)
    return {c for c in (flat() if flat else im.getdata()) if c[3]}


def check(mod, allowed):
    """Returns (strip image, per-frame report rows, problems)."""
    fr = mod.frames()
    problems, rows = [], []
    for i, (px, fx) in enumerate(fr):
        im = B.to_image(px)
        st = B.stats(im)
        flat = getattr(im, 'get_flattened_data', None)
        data = list(flat() if flat else im.getdata())
        cols = {c for c in data if c[3]}
        bad_cols = cols - allowed
        blacks = {c for c in cols if c[:3] == (0, 0, 0)}
        a = B.audit(px, fx)
        gaps = a['gaps']
        low = max(y for (x, y) in px)
        tag = '%s f%d' % (mod.NAME, i)
        if bad_cols:
            problems.append('%s: colours outside the approved 40: %s' % (tag, sorted(bad_cols)[:5]))
        if blacks - {(0, 0, 0, 255)}:
            problems.append('%s: impure black %s' % (tag, blacks))
        if st['semi']:
            problems.append('%s: %d semi-transparent pixels' % (tag, st['semi']))
        if gaps or a['lone'] or a['holes'] or a['keys']:
            problems.append('%s: gaps %s lone %s holes %s keys %s' % (tag, gaps[:6], a['lone'][:6], a['holes'][:6],
                                                                      a['keys']))
        if low != 95:
            problems.append('%s: lowest drawn row is %d, not 95' % (tag, low))
        if not (BLACK_RANGE[0] <= st['black'] <= BLACK_RANGE[1]):
            problems.append('%s: black ratio %.1f%% outside %.1f-%.1f%%' % (tag, 100 * st['black'],
                                                                             100 * BLACK_RANGE[0], 100 * BLACK_RANGE[1]))
        rows.append((i, st, len(cols), B.bbox(px)))
    im = B.strip([px for px, _fx in fr])
    if im.size != (96 * len(fr), 96):
        problems.append('%s: strip is %s' % (mod.NAME, im.size))
    for i, ref in getattr(mod, 'APPROVED', {}).items():
        d = B.pixel_diff(im.crop((96 * i, 0, 96 * i + 96, 96)),
                         B.approved_sheet().crop((96 * ref, 0, 96 * ref + 96, 96)))
        if d:
            problems.append('%s f%d is not approved frame %d: %s' % (mod.NAME, i, ref, d))
    return im, rows, problems


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    if argv[0] == '--ship':
        out_dir = B.ASSETS
    else:
        out_dir = os.path.abspath(argv[0])
        if _under(out_dir, os.path.join(B.ROOT, 'Assets')):
            print('refusing %s: it is inside the live Assets tree; only --ship writes there' % out_dir)
            return 2
    allowed = approved_colours()
    assert len(allowed) == 40, len(allowed)
    built, all_problems = [], []
    for mod in MODULES:
        im, rows, problems = check(mod, allowed)
        built.append((mod, im, rows))
        all_problems += problems
    if all_problems:
        print('NOT WRITTEN, problems:')
        for p in all_problems:
            print('  ' + p)
        return 1
    status = 0
    for mod, im, rows in built:
        png, ase, rt = B.write_sheet(mod.NAME, im, out_dir)
        sheet = B.stats(im)
        print('%s  %dx%d, %d frames, times %s%s' % (os.path.basename(png), im.width, im.height, len(rows),
                                                   mod.TIMES, ', loops' if mod.LOOP else ', once'))
        print('   .aseprite round trip:', rt or 'identical')
        for i, st, ncol, bb in rows:
            print('   f%d  opaque %4d  colours %2d  black %.1f%%  semi %d  rows %d..%d' % (
                i, st['opaque'], ncol, 100 * st['black'], st['semi'], bb[1], bb[3]))
        print('   sheet: colours %d, black %.1f%%' % (sheet['colours'], 100 * sheet['black']))
        status |= 1 if rt else 0
    print('written to', out_dir)
    return status


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
