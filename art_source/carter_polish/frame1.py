"""Frame 1: the signature pose - arms crossed, aura flaring. Front view, 96x96, soles on row 95.

Same body as frame 0 from the belt down, same head, same gi; the arms are in cross.py:
  A = his right arm (screen left): forearm crosses BEHIND, hand tucks under his left bicep.
  B = his left arm (screen right): forearm crosses IN FRONT, wrapped hand tucks under his right bicep.
In this pose the upper arms come forward over the gi and the torn caps ride on the shoulders, as in
the approved frame. The approved frame drew the front forearm as long 1px stripes, the back forearm
as a flat band of one dark tone, and the tucked hand as a khaki brick.

    python frame1.py <out dir>      # writes f1.png and a zoomed view there
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib                                                                    # noqa: E402
from lib import Canvas, grow                                                  # noqa: E402
import head as HD                                                             # noqa: E402
import chest as CH                                                            # noqa: E402
import jacket as JK                                                           # noqa: E402
import lower as LO                                                            # noqa: E402
import aura as AU                                                             # noqa: E402
import cross as CR                                                            # noqa: E402


KNUCKLES = [
    # (y, x0, keys): x 35-36 fingers, x 37 where the wrap stops at the knuckles
    (54, 35, "tuk"),
    (55, 35, "uvk"),
    (56, 35, "kkk"),
    (57, 35, "tuk"),
    (58, 35, "uvk"),
    (59, 35, "kkk"),
    (60, 35, "tuk"),
    (61, 35, "uvk"),
    (62, 35, "vwk"),
]


def build():
    cv = Canvas()
    cv.stamp(LO.shins())
    for f in LO.feet():
        cv.stamp(f, outline=False)
    cv.stamp(LO.trousers())
    for j in JK.jacket():
        cv.stamp(j)
    cv.stamp(CH.chest(), outline=False)
    for b in CH.beads():
        cv.stamp(b, outline=False)
    cv.stamp(LO.belt(), outline=False)
    cv.stamp(LO.knot(), outline=False)
    cv.stamp(LO.tails(), outline=False)

    parts = CR.arms()
    for part, outline in parts:
        cv.stamp(part, outline=outline)
    # the folded forearms sit tight on the rope belt: its shadow under their bottom keyline
    for part, _ in parts[4:]:
        low = {}
        for (x, y) in part:
            low[x] = max(low.get(x, y), y)
        for x, y in low.items():
            q = (x, y + 2)
            if cv.px.get((x, y + 1)) == 'k' and cv.px.get(q) in tuple('nopqr'):
                cv.px[q] = 'k'
    # the knuckles of his left hand peek out where it tucks under his right bicep (the approved
    # frame showed three knuckle dots here; these are the three fingers, keylined)
    lib.patch(cv.px, KNUCKLES)

    cv.stamp(HD.head(), outline=False)
    cv.stamp(HD.earring(), outline=False)
    body = set(cv.px)
    cv.stamp(AU.flames(AU.FLARE, grow(body, 1), AU.FLARE_ORDER), outline=False, under=True)
    cv.stamp(AU.embers(AU.FLARE_EMBERS), outline=False, under=True)
    return cv


if __name__ == '__main__':
    SP = sys.argv[1]
    cv = build()
    im = cv.image()
    im.save(os.path.join(SP, 'f1.png'))
    lib.grid_view(im, 8, 10, 0, 85, 95).save(os.path.join(SP, 'f1_8x.png'))
    print(lib.stats(im))
