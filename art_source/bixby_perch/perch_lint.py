"""Lint the perch frames with the redesign's own checks (bixby_redesign/lint.py: detached islands and
coloured pixels on the silhouette with no keyline outside them), plus the frame rules: nothing above
the 33-row headroom, a 2px side margin, and nothing below row 159.

    python perch_lint.py
"""
import common  # noqa: F401  (puts the rig on the path)
import lint as rlint
import perch
import poses
import rig
from common import TOP_ROW, FW, FH

# fire, suction streaks and sweat may sit bare against the background (light has no keyline)
BARE_OK = 'wYPpNnrxyzWU'


def run(verbose=True):
    Ps = poses.frames()
    cvs = [perch.build(P) for P in Ps] + [rig.build(poses.release_upright())]
    problems = 0
    for i, cv in enumerate(cvs):
        comps = rlint.islands(cv.px)
        small = [c for c in comps if len(c) < 6]
        bare = rlint.bare_edges(cv.px, allow=BARE_OK)
        xs = [p[0] for p in cv.px]
        ys = [p[1] for p in cv.px]
        bad = []
        if small:
            bad.append('small islands %s' % [(min(c), len(c)) for c in small][:4])
        if bare:
            bad.append('unkeylined %s' % bare[:4])
        if min(ys) < TOP_ROW:
            bad.append('above the headroom (row %d)' % min(ys))
        if max(ys) > FH - 1:
            bad.append('below the frame (row %d)' % max(ys))
        if min(xs) < 2 or max(xs) > FW - 3:
            bad.append('inside the side margin (x %d..%d)' % (min(xs), max(xs)))
        problems += bool(bad)
        if verbose:
            print('%2d  x %3d..%3d  y %3d..%3d  %s' % (i, min(xs), max(xs), min(ys), max(ys), '; '.join(bad) or 'ok'))
    return problems


if __name__ == '__main__':
    import sys
    sys.exit(1 if run() else 0)
