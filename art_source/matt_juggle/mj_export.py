"""Write Matt's juggle sheet and his mat shadow, each PNG with its .aseprite beside it, after the
lint passes. A bare run writes nothing:

    python mj_export.py <scratch_dir>     # write the four files there, for checking
    python mj_export.py --ship            # write them into Assets/Characters/Matt/

It only ever writes these names: matt_juggle.png, matt_juggle.aseprite, matt_leap_shadow.png,
matt_leap_shadow.aseprite. Each is built in a temp folder by the intro rig's write_sheet
(art_source/matt_intro/mi_base.py), which saves the .aseprite through Aseprite's own CLI, checks
the .aseprite re-exports to exactly the PNG (art_source/imgdiff.pixel_diff: alpha everywhere,
colour wherever a pixel shows), moves both into place in one step, and checks them again where
they landed.

Then it prints what the coder needs: frame size and hframes, the feet texel, tumble_centre, top_row,
the timing per clip, and the numbers per frame.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mj_base as J  # noqa: E402
import mj_build as MB  # noqa: E402
import mj_lint as ML  # noqa: E402
import mj_poses as MP  # noqa: E402
import mj_shadow as MS  # noqa: E402

AIR_FRAMES = (1, 2, 3, 4, 5, 6)          # off the mat: the lift and the tumble
TUMBLE = (2, 3, 4, 5, 6)
CLIPS = [('launch', 0, 1, False), ('tumble', 2, 6, True), ('crash', 7, 9, False), ('down', 10, 11, True)]


def centroid(px):
    n = len(px)
    return (sum(x for (x, y) in px) / n + 0.5, sum(y for (x, y) in px) / n + 0.5)


def report(built):
    print('frame size      %dx%d, hframes %d (vframes 1), sheet %dx%d'
          % (J.W, J.H, len(built), J.W * len(built), J.H))
    print('feet            (%d, %d)  bottom-centre texel of the ground frames 0 and 7-11'
          % J.FEET)
    cs = [centroid(built[i].body) for i in TUMBLE]
    cx = sum(c[0] for c in cs) / len(cs)
    cy = sum(c[1] for c in cs) / len(cs)
    print('tumble_centre   (%d, %d)  measured centroid of his body over the tumble frames 2-6 '
          '(per frame %s); the turn pivot is %s' % (round(cx), round(cy),
                                                   ' '.join('(%.0f,%.0f)' % c for c in cs), MP.AIR))
    top_body = min(J.bbox(built[i].body)[1] for i in AIR_FRAMES)
    top_all = min(J.bbox(built[i].px)[1] for i in AIR_FRAMES)
    print('top_row         %d  highest row drawn on any airborne frame (%d counting effects)'
          % (min(top_body, top_all), top_all))
    for name, a, b, loop in CLIPS:
        print('  %-7s frames %d-%d  %s%s' % (name, a, b, ', '.join('%.2f' % built[i].hold for i in range(a, b + 1)),
                                           '  (loops)' if loop else ''))


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    out_dir = J.ASSETS if argv[0] == '--ship' else os.path.abspath(argv[0])
    built = MB.frames()
    rows, fatal = ML.lint(built, verbose=True)
    if fatal:
        print('\nNOT WRITTEN, %d fatal finding(s):' % len(fatal))
        for f in fatal:
            print('  ' + f)
        return 1
    sheet = J.strip([b.px for b in built])
    shadow = MS.sheet()
    status = 0
    for name, im in (('matt_juggle', sheet), ('matt_leap_shadow', shadow)):
        png, ase, rt = J.B.write_sheet(name, im, out_dir)
        print('%s  %dx%d   .aseprite round trip: %s' % (os.path.basename(png), im.width, im.height,
                                                        rt or 'identical'))
        status |= 1 if rt else 0
    print('shadow ellipses (low, mid, high):', ', '.join(MS.sizes(shadow)), 'in frames of %dx%d'
          % (MS.W, MS.H))
    print()
    report(built)
    print('\nwritten to', out_dir)
    return status


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
