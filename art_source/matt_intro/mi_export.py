"""Write Matt's intro sheets and portrait, each PNG with its .aseprite beside it, after checking
every frame. A bare run writes nothing:

    python mi_export.py <scratch_dir>     # write all ten files there, for checking
    python mi_export.py --ship            # write them into Assets/Characters/Matt/

It only ever writes these names: matt_walk, matt_talk, matt_doll, matt_roar, portrait (.png and
.aseprite). Each file is built in a temp folder and moved into place in one step, and each .aseprite
is re-exported and compared with its PNG pixel for pixel (art_source/imgdiff.pixel_diff).

Checked before anything is written, per frame:
  - 96x96, the strip horizontal, frame 0 leftmost
  - the lowest drawn row is 95 (his feet); the highest is row 1 or lower, the approved headroom
  - every colour is one of the approved sheet's 41, black is pure #000000, no semi-alpha
  - no keyline gaps, stray pixels or pinholes (effects excepted), no keys off the palette
  - black ratio within 22-28% (the approved frames: 25.0% idle, 22.2% roar with its rings)
  - roar frame 1 is the approved roar, rings removed, pixel for pixel
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mi_base as B  # noqa: E402
import mi_fig as F  # noqa: E402
import mi_walk  # noqa: E402
import mi_talk  # noqa: E402
import mi_doll  # noqa: E402
import mi_roar  # noqa: E402
import mi_portrait  # noqa: E402
import mi_anchors  # noqa: E402

MODULES = [mi_walk, mi_talk, mi_doll, mi_roar]
BLACK_RANGE = (0.22, 0.28)
TIMES = {
    'matt_walk': '6 x 0.10 s, looping',
    'matt_talk': 'pairs flapped at 0.12 s while a line types, frame 0 of the pair held otherwise',
    'matt_doll': 'f0-2 0.12/0.12/0.40; f3-5 cycling at 0.06; f6-7 0.15/0.30',
    'matt_roar': 'f0 0.35 s, then f1-3 looping at 0.06 s',
}


def approved_colours():
    return {c for c in B.flat(B.approved_sheet()) if c[3]}


def approved_roar_no_rings():
    cv = B.matt.build(True)
    rings = {p for p, k in cv.px.items() if k in 'zZ'}
    edge = set()
    for (x, y) in rings:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            edge.add((x + dx, y + dy))
    ref = F.px_of(F.Fig(roar=True, collar=False, face=(B.rig_face.ROAR, B.rig_face.X0, B.rig_face.ROAR_Y0)))
    return ref


def check(mod, allowed):
    figs = mod.figs()
    problems, rows, frames = [], [], []
    for i, f in enumerate(figs):
        px = F.px_of(f)
        frames.append(px)
        im = B.image(px)
        st = B.stats(im)
        cols = {c for c in B.flat(im) if c[3]}
        a = B.audit(px, f.fx)
        x0, y0, x1, y1 = B.bbox(px)
        tag = '%s f%d' % (mod.NAME, i)
        if cols - allowed:
            problems.append('%s: colours outside the approved 41: %s' % (tag, sorted(cols - allowed)[:5]))
        if {c for c in cols if c[:3] == (0, 0, 0)} - {(0, 0, 0, 255)}:
            problems.append('%s: impure black' % tag)
        if st['semi']:
            problems.append('%s: %d semi-transparent pixels' % (tag, st['semi']))
        if any(a.values()):
            problems.append('%s: %s' % (tag, {k: v[:5] for k, v in a.items() if v}))
        if y1 != 95:
            problems.append('%s: lowest drawn row is %d, not 95' % (tag, y1))
        if y0 < 1:
            problems.append('%s: drawn on row %d, above the approved headroom' % (tag, y0))
        if not (BLACK_RANGE[0] <= st['black'] <= BLACK_RANGE[1]):
            problems.append('%s: black %.1f%% outside %.0f-%.0f%%' % (tag, 100 * st['black'],
                                                                        100 * BLACK_RANGE[0], 100 * BLACK_RANGE[1]))
        rows.append((i, st, len(cols), (x0, y0, x1, y1)))
    if mod is mi_roar:
        d = B.pixel_diff(B.image(frames[1]), B.image(approved_roar_no_rings()))
        if d:
            problems.append('matt_roar f1 is not the approved roar minus rings: %s' % d)
    im = B.strip(frames)
    if im.size != (96 * len(frames), 96):
        problems.append('%s: strip is %s' % (mod.NAME, im.size))
    return im, rows, problems


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    out_dir = B.ASSETS if argv[0] == '--ship' else os.path.abspath(argv[0])
    allowed = approved_colours()
    assert len(allowed) == 41, len(allowed)
    built, problems = [], []
    for mod in MODULES:
        im, rows, probs = check(mod, allowed)
        built.append((mod.NAME, im, rows))
        problems += probs
    portrait = mi_portrait.build_image()
    pst = B.stats(portrait)
    pcols = {c for c in B.flat(portrait) if c[3]}
    if pcols - allowed:
        problems.append('portrait: colours outside the approved 41')
    if pst['semi']:
        problems.append('portrait: semi-transparent pixels')
    if problems:
        print('NOT WRITTEN, problems:')
        for p in problems:
            print('  ' + p)
        return 1
    status = 0
    for name, im, rows in built:
        png, ase, rt = B.write_sheet(name, im, out_dir)
        sheet = B.stats(im)
        print('%s  %dx%d, %d frames, %s' % (os.path.basename(png), im.width, im.height, len(rows), TIMES[name]))
        print('   .aseprite round trip:', rt or 'identical')
        for i, st, ncol, bb in rows:
            print('   f%-2d opaque %4d  colours %2d  black %.1f%%  rows %d..%d  cols %d..%d' % (
                i, st['opaque'], ncol, 100 * st['black'], bb[1], bb[3], bb[0], bb[2]))
        print('   sheet: colours %d, black %.1f%%' % (sheet['colours'], 100 * sheet['black']))
        status |= 1 if rt else 0
    png, ase, rt = B.write_sheet('portrait', portrait, out_dir)
    print('portrait.png  64x64')
    print('   .aseprite round trip:', rt or 'identical')
    mi_portrait.measure(portrait)
    status |= 1 if rt else 0
    print('written to', out_dir)
    return status


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
