"""The approved key frames must not move.

golden/ holds the three frames (plus the two no-FX bodies) the user signed off on at
96x96.  Every later pose was bolted onto the same rig, so it is easy to nudge a
shared helper and silently redraw an approved frame.  This fails if that happens.

Compared with art_source/imgdiff.py, not a bare getbbox(): getbbox() defaults to
alpha_only and would pass two frames that share a silhouette and differ in every
colour.

  python regress.py        # 0 if the rig still reproduces the approved frames
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
from imgdiff import pixel_diff                                    # noqa: E402
from PIL import Image                                             # noqa: E402

import computah_mm as M                                           # noqa: E402

GOLDEN = {
    # The approved key frame was drawn while the chest plate was a beam capacitor
    # that fills, so it shows one lit cell.  The battery came back afterwards and the
    # shipped idle sheet's row 0 is FULL - four green cells.  Nothing else about the
    # drawing moved, which is exactly what this check is for.
    "idle_key.png": lambda: M.build_idle(0, M.CORE["key"]),
    "beam_charge.png": lambda: M.build_charge(True),
    "beam_ready.png": lambda: M.build_ready(True),
    "beam_charge_nofx.png": lambda: M.build_charge(False),
    "beam_ready_nofx.png": lambda: M.build_ready(False),
}


def main():
    M._set_frame(96)
    bad = 0
    for name, fn in sorted(GOLDEN.items()):
        want = Image.open(os.path.join(HERE, "golden", name))
        d = pixel_diff(want, fn().to_image())
        print("%-24s %s" % (name, d or "matches the approved frame"))
        bad += d is not None
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
