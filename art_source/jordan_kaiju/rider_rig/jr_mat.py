"""Jordan off the kaiju: legs, shoes and whole-body poses for the mat and air sheets (topple, daze,
climb, butt-land, box-open, toss). Build coordinates (soles on row 95 standing; the mat is row 95).

The legs posed here are v2's thin jeans legs rebuilt from joints (hip, knee, ankle) as capsules of v2's
widths (4px thighs, 4px shins, 5px knees), shaded by v2's jeans rules turned to the limb (lit edge
'S' toward the upper left, 's' the lit top, 'N' base, 'n' the shadow side and underside); the
sneakers are the approved maps, turned by exact quarter turns or (for other angles) RotSprite.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jr_common as C  # noqa: E402
import jr_fig as F     # noqa: E402
import jr_ride as R    # noqa: E402
import jr_rot as ROT   # noqa: E402

V, JB, J = F.V, F.JB, F.J
shift = C.shift


#LEGS

def jeans_limb(segments, knees=(), lit_side=True):
    """A thin jeans leg through joints: segments [(p0, p1, r0, r1)], knee knobs [(x, y, r)]."""
    shape = set()
    for (p0, p1, r0, r1) in segments:
        shape |= JB.capsule(p0, p1, r0, r1)
    for (cx, cy, r) in knees:
        shape |= C.ellipse(cx, cy, r, r)
    part = C.fill(shape, 'N')
    C.rim(part, 'S' if lit_side else 's', -1, 0)
    C.rim(part, 's', 0, -1, only='N')
    C.rim(part, 'n', 1, 0)
    C.rim(part, 'n', 0, 1, only='N')
    return part


def leg(hip, knee, ankle, lit_side=True, r=(1.9, 1.7, 1.6), knee_r=2.1, hem=None):
    """One thin jeans leg hip -> knee -> ankle; `hem`: (x, y) of a bunched stack at the ankle."""
    part = jeans_limb([(hip, knee, r[0], r[1]), (knee, ankle, r[1], r[2])], [(knee[0], knee[1], knee_r)], lit_side)
    if hem:
        hx, hy = hem
        st = C.fill(C.ellipse(hx, hy, 2.6, 2.0), 'N')
        for q in st:
            if q not in part:
                part[q] = 'n' if (q[0] + q[1]) % 2 else 's'
    return part


def hips(dx=0, dy=0):
    """The jeans seat under the tee (the rider's seat, flattened), moved by (dx, dy)."""
    return shift(R.seat(), dx, dy)


#SHOES (the approved maps; ANKLE is the point the shin ends on)

SHOE_ANKLE = {'near': (40, 89), 'far': (54, 89)}
# a keyline over the top of a shoe (where a hem would cover it), to close it when no hem does
_TOP_K = {'near': [(37, 88), (38, 88), (39, 88), (40, 88), (41, 88), (42, 88)],
          'far': [(51, 88), (52, 88), (53, 88), (54, 88), (55, 88), (56, 88)]}


def shoe(which, ankle, quarter=0, deg=0.0, close_top=True):
    """The approved sneaker `which` ('near' / 'far') with its ankle on `ankle`, turned `quarter`
    quarter turns clockwise (exact) and then `deg` more (RotSprite)."""
    far, near = J.shoes()
    part = dict(near if which == 'near' else far)
    if which == 'near':
        part[(47, 91)] = 'k'                     # v2's toe-cap gap closer
    if close_top:
        for q in _TOP_K[which]:
            part.setdefault(q, 'k')
    ax, ay = SHOE_ANKLE[which]
    if quarter:
        part = ROT.quarter(part, quarter, (ax + 0.5, ay + 0.5), (ax + 0.5, ay + 0.5))
    if deg:
        part = ROT.rotsprite(part, deg, (ax + 0.5, ay + 0.5), (ax + 0.5, ay + 0.5))
    return shift(part, int(round(ankle[0])) - ax, int(round(ankle[1])) - ay)


#UPPER BODY

def torso(fig, dx, dy, frame=0, lean=None):
    """v2's neck (leaning `lean`, default with the idle head), tee and dandruff, moved by (dx, dy)."""
    fig.stamp(shift(V.neck(F.HEAD_AT[0] if lean is None else lean), dx, dy))
    fig.stamp(shift(V.shirt(frame), dx, dy))
    JB.dandruff(fig.px, dx, dy)


def near_root(dx, dy):
    return (F.NEAR_ROOT[0] + dx, F.NEAR_ROOT[1] + dy)


def far_root(dx, dy):
    return (F.FAR_ROOT[0] + dx, F.FAR_ROOT[1] + dy)


def arm_to(which, dx, dy, wrist, bend=1, twist=(0, 0)):
    """An arm from its shoulder (moved with the body, plus `twist`) to `wrist`, elbow by IK."""
    if which == 'near':
        sh = near_root(dx + twist[0], dy + twist[1])
        el = F.ik(sh, wrist, F.UPPER_L, F.FORE_L, bend)
        return F.near_arm(sh, el, wrist)
    sh = far_root(dx + twist[0], dy + twist[1])
    el = F.ik(sh, wrist, 9.52, 7.6, bend)
    return F.far_arm(sh, el, wrist)


def closed_box(deg=0, uv=(0, 0), at=(61, 25)):
    """The approved (closed) chase-edition box via janim_box (straight edges kept at any angle)."""
    return JB.close_gaps(F.JBX.box_at(deg, uv, at)) if deg else F.JBX.box_at(0, uv, at)


def sparkle(cx, cy, big=True):
    out = {(cx, cy): 'W'}
    if big:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            out[(cx + dx, cy + dy)] = 'Q'
    return out


# small spinning daze stars (effects: gold, no keyline), two phases of a twinkle
STAR5 = ["..O..", ".OYO.", "OYWYO", ".OYO.", "..O.."]
STAR3 = [".O.", "OYO", ".O."]


def star(cx, cy, big=True):
    rows = STAR5 if big else STAR3
    h = len(rows) // 2
    return C.amap(rows, cx - h, cy - h)


DUST_BIG = ["..00..", ".0009.", "009999", ".9999."]
DUST_SMALL = [".0.", "009", ".9."]


def dust(cx, cy, r=1):
    """A small dust puff on the mat (effect pixels: the sneaker sole's white and pale grey), its base on cy."""
    rows = DUST_BIG if r > 1 else DUST_SMALL
    return C.amap(rows, cx - len(rows[0]) // 2, cy - len(rows) + 1)
