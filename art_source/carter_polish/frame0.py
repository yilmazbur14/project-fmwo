"""Frame 0: Carter standing, arms hanging, fists wrapped. Front view, 96x96, soles on row 95.

Build order is back to front; the parts live in their own modules:
  lower  - shins, bare feet, gi trousers (torn hem burning to violet), rope belt, knot and tails
  arms   - one continuous shape per arm, shoulder to wrist, and the wrapped fists
  jacket - the torn sleeveless gi: collar, caps with torn teeth, side panels, lapel bands
  chest  - the chest between the lapels, and the prayer beads
  head   - the head, face, beard and cross earring
  aura   - the Satsui no Hado flames behind him
Every part carries or gets its keyline as it is stamped, so a part laid over another cuts its own
black line into it; the arm is ONE part per side so no keyline ever crosses it (the approved sheet
outlined delt, upper arm and forearm separately and the arm read as stacked pieces).

    python frame0.py <out dir>      # writes f0.png and zoomed views there
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib                                                                    # noqa: E402
from lib import Canvas, grow                                                  # noqa: E402
import head as HD                                                             # noqa: E402
import chest as CH                                                            # noqa: E402
import arms as AR                                                             # noqa: E402
import jacket as JK                                                           # noqa: E402
import lower as LO                                                            # noqa: E402
import aura as AU                                                             # noqa: E402


def build():
    cv = Canvas()
    cv.stamp(LO.shins())
    for f in LO.feet():
        cv.stamp(f, outline=False)
    cv.stamp(LO.trousers())
    cv.stamp(AR.arm_l(), outline=False)
    cv.stamp(AR.arm_r(), outline=False)
    for j in JK.jacket():
        cv.stamp(j)
    cv.stamp(CH.chest(), outline=False)
    for b in CH.beads():
        cv.stamp(b, outline=False)
    cv.stamp(LO.belt(), outline=False)
    cv.stamp(LO.knot(), outline=False)
    cv.stamp(LO.tails(), outline=False)
    cv.stamp(AR.fist_l(), outline=False)
    cv.stamp(AR.fist_r(), outline=False)
    cv.stamp(HD.head(), outline=False)
    cv.stamp(HD.earring(), outline=False)
    # the aura goes behind everything, with a pixel of air between it and his keyline
    body = set(cv.px)
    cv.stamp(AU.flames(AU.IDLE, grow(body, 1), AU.IDLE_ORDER), outline=False, under=True)
    cv.stamp(AU.embers(AU.IDLE_EMBERS), outline=False, under=True)
    return cv


if __name__ == '__main__':
    SP = sys.argv[1]
    im = build().image()
    im.save(os.path.join(SP, 'f0.png'))
    lib.grid_view(im, 8, 14, 0, 81, 95).save(os.path.join(SP, 'f0_8x.png'))
    lib.upscale(lib.on_bg(im), 3).save(os.path.join(SP, 'f0_3x.png'))
    print(lib.stats(im))
