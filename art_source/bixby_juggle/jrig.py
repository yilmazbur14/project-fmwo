"""rig.build, turned: the approved rig's stamp order, every part built under relight.lit() for the turn
its layer will be given, so the key light stays on top after the turn.

build(P, theta) is a line-for-line copy of art_source/bixby_redesign/rig.py:build (the rig is imported,
never edited), except that each part the rig stamps mirrored is BUILT again under the mirrored light
rather than mirrored after the fact, and the hand-drawn paw maps are relit when turned. At theta 0 it is
pixel-identical to rig.build for every pose of every live sheet (regress()).

layers(P, theta, heads) builds the same frame as separate layers (body, left side head, right side
head, middle head) so each head can be turned on its own, lolling on its neck. Composited back to
front at one common turn they are pixel-identical to build() (regress()).
"""
import math

import jcommon  # noqa: F401  (paths)
import body as B
import heads
import rig
import rig_body as RB
import rig_heads as RH
import rig_wings as RW
from pal import BCanvas, fill, mir, poly
from shapes import half, poly_line, recolor, spt
import relight

BONE = 'wxyz'

# body.chest's light is a painted patch at the top of the chest (mostly under the middle head's collar)
# plus shade along its bottom and sides. Turning the patch with the light would bare a big white field the
# approved frames never show, so a turned chest keeps the patch where the rig paints it and instead gets
# the patch's job done by a 1px lit rim on whichever edge now faces the light (the bottom and side shade
# recipes are relit by relight.lit as usual).
CHEST_PTS = [(95.5, 84), (106, 85), (113, 91), (116, 101), (115, 111), (111, 117), (110, 126),
             (106, 120), (103, 130), (99, 122), (95.5, 131)]
CHEST_HI = [(95.5, 90), (102, 90), (107, 96), (106, 104), (100, 108), (95.5, 108)]


def chest(dy=0, theta=0.0):
    """body.chest, pixel for pixel at theta 0 (checked in regress), with a lit rim facing up when turned."""
    if theta % 360 == 0:
        return B.chest(dy)
    c = fill(poly(spt(half(CHEST_PTS), 0, dy)), 'x')
    recolor(c, relight.edge(c, 0, 1, 2), 'y')
    recolor(c, relight.edge(c, 1, 0, 1), 'y')
    recolor(c, relight.edge(c, -1, 0, 1), 'y')
    recolor(c, poly(spt(half(CHEST_HI), 0, dy)), 'w', only='x')
    recolor(c, relight.edge(c, 0, -1, 1), 'w', only='x')
    for seg in ([(104, 110), (106, 118)], [(100, 112), (101, 121)], [(110, 104), (111, 112)]):
        for s in (seg, [(191 - x, y) for (x, y) in seg]):
            for q in poly_line(spt(s, 0, dy)):
                if q in c and c[q] in 'xw':
                    c[q] = 'y'
    return c


def torso(theta, dx=0, dy=0):
    """rig_body.torso with the relit chest."""
    parts = [B.mantle(dy), B.belly(dy), chest(dy, theta)]
    if dx:
        parts = [{(x + dx, y): k for (x, y), k in p.items()} for p in parts]
    return parts


def relight_paw(part, theta, mirrored):
    """A hand-drawn paw map lit for a turned frame. Its bone tones are regenerated the way the maps are
    painted: each toe (the bone between the black toe lines) shaded along its bottom and one column down
    its outer side, lit along its top and inner side; the whole paw's outer side one step darker still.
    The vertical recipes are relit for the turn (relight.lit); the side ones stay with the paw. Upright,
    the map is returned untouched."""
    if theta % 360 == 0:
        return part
    out = dict(part)
    whole = set(part)
    bone = {p: 'x' for p, k in part.items() if k in BONE}
    with relight.lit(theta, mirrored):
        e = relight.edge
        recolor(bone, e(bone, 0, 1, 2), 'y')
        recolor(bone, e(bone, 0, 1, 1), 'z')
        recolor(bone, e(bone, 1, 0, 1), 'y')
        recolor(bone, e(whole, 1, 0, 2), 'z')
        recolor(bone, e(bone, 0, -1, 1), 'w', only='x')
        recolor(bone, e(bone, -1, 0, 1), 'w', only='x')
    out.update(bone)
    return out


def _mirrored(fn, theta):
    """A right-side part built under the mirrored light (the caller mirrors it to the left)."""
    with relight.lit(theta, mirrored=True):
        return fn()


def wings_canvas(P, theta=0.0):
    """Both wings (the rig stamps them first, behind everything)."""
    cv = BCanvas(w=P.get('W', 192), h=P.get('H', 160))
    if 'wings' in set(P.get('hide', ())):
        return cv
    PL = P.get('wings_left')
    with relight.lit(theta, mirrored=True):
        left = RW.parts(PL if PL is not None else P['wings'])
    with relight.lit(theta):
        right = RW.parts(P['wings'])
    for p in left:
        cv.stamp(mir(p))
    for p in right:
        cv.stamp(p)
    return cv


def tails_canvas(P, theta=0.0):
    """Liam's headband tails, knotted behind the middle head's ear (next in the rig's order). They belong
    to the middle head: a head turned on its own takes them with it."""
    cv = BCanvas(w=P.get('W', 192), h=P.get('H', 160))
    if 'tails' in set(P.get('hide', ())):
        return cv
    mid = RH.mid_xf(P.get('mid', {}), P.get('bob', 0))
    tm = bool(P.get('tails_mirror'))
    with relight.lit(theta, mirrored=tm):
        ts = heads.headband_tails(mid, wave=P.get('tails_wave', 0))
    for t in ts:
        cv.stamp(mir(t) if tm else t)
    return cv


def body_canvas(P, theta=0.0):
    """The body behind the heads, after the wings and the headband tails: tail, legs and paws, torso,
    side necks."""
    bob = P.get('bob', 0)
    hide = set(P.get('hide', ()))
    cv = BCanvas(w=P.get('W', 192), h=P.get('H', 160))
    if 'tail' not in hide:
        path = [(x, y + bob) for (x, y) in P['tail_path']]
        tx, ty = P['tail_tip']
        with relight.lit(theta):
            cv.stamp(RB.tail(path))
            cv.stamp(RB.tail_tip((tx, ty + bob)))
    planted = set(P.get('planted', ()))
    hind_l = P['hind_left'] if P.get('hind_left') is not None else P.get('hind')
    with relight.lit(theta):
        hr = RB.hind_leg(P.get('hind'), 0, bob)
    hl = _mirrored(lambda: RB.hind_leg(hind_l, 0, bob), theta)
    hpaw_r = relight_paw(RB.paw(False, rig._joint(P.get('hind'), RB.HIND, 'paw'), 'hind' in planted, 0, bob),
                         theta, False)
    hpaw_l = relight_paw(RB.paw(False, rig._joint(hind_l, RB.HIND, 'paw'), 'hind' in planted, 0, bob),
                         theta, True)
    if 'legs' not in hide:
        for i, p in enumerate(hr):
            cv.stamp(mir(hl[i]))
            cv.stamp(p)
        cv.stamp(mir(hpaw_l), outline=False)
        cv.stamp(hpaw_r, outline=False)
    tdx, tdy = P.get('torso', (0, 0))
    with relight.lit(theta):
        for p in torso(theta, tdx, tdy + bob):
            cv.stamp(p)
    front_l = P['front_left'] if P.get('front_left') is not None else P.get('front')
    with relight.lit(theta):
        fr = RB.front_leg(P.get('front'), 0, bob)
    fl = _mirrored(lambda: RB.front_leg(front_l, 0, bob), theta)
    fpaw_r = relight_paw(RB.paw(True, rig._joint(P.get('front'), RB.FRONT, 'paw'), 'front' in planted, 0, bob),
                         theta, False)
    fpaw_l = relight_paw(RB.paw(True, rig._joint(front_l, RB.FRONT, 'paw'), 'front' in planted, 0, bob),
                         theta, True)
    if 'legs' not in hide:
        for i, p in enumerate(fr):
            cv.stamp(mir(fl[i]))
            cv.stamp(p)
        cv.stamp(mir(fpaw_l), outline=False)
        cv.stamp(fpaw_r, outline=False)
    nb, nt = P.get('neck', ((118, 98), (142, 82)))
    nl = P.get('neck_left') or (nb, nt)
    if 'necks' not in hide:
        with relight.lit(theta):
            neck_r = RB.side_neck(nb, nt, 0, bob)
        neck_l = _mirrored(lambda: RB.side_neck(nl[0], nl[1], 0, bob), theta)
        cv.stamp(mir(neck_l))
        cv.stamp(neck_r)
    return cv


def side_canvases(P, theta_l=0.0, theta_r=0.0):
    """(left, right) side head canvases, already in place (the left mirrored), each lit for its turn."""
    bob = P.get('bob', 0)
    sp = dict(P.get('side', {}))
    spl = P['side_left'] if P.get('side_left') is not None else sp
    left = BCanvas(w=P.get('W', 192), h=P.get('H', 160))
    left.px = mir(_mirrored(lambda: RH.side_head(bob=bob, **spl), theta_l).px)
    right = BCanvas(w=P.get('W', 192), h=P.get('H', 160))
    with relight.lit(theta_r):
        right.px = dict(RH.side_head(bob=bob, **sp).px)
    return left, right


def mid_canvas(P, theta=0.0):
    bob = P.get('bob', 0)
    cv = BCanvas(w=P.get('W', 192), h=P.get('H', 160))
    with relight.lit(theta):
        RH.mid_head(cv, bob=bob, **P.get('mid', {}))
    return cv


def build(P, theta=0.0):
    """The whole frame on one canvas, as rig.build stamps it (no side_face / front_over_sides: the
    juggle never uses them)."""
    assert not P.get('side_face') and not P.get('front_over_sides')
    cv = wings_canvas(P, theta)
    cv.px.update(tails_canvas(P, theta).px)
    cv.px.update(body_canvas(P, theta).px)
    hide = set(P.get('hide', ()))
    if 'side' not in hide:
        left, right = side_canvases(P, theta, theta)
        cv.px.update(left.px)
        cv.px.update(right.px)
    if 'mid' not in hide:
        mid = mid_canvas(P, theta)
        cv.px.update(mid.px)
    for f in P.get('fx', []):
        f(cv, P)
    sx, sy = P.get('shift', (0, 0))
    if sx or sy:
        cv.px = {(x + sx, y + sy): k for (x, y), k in cv.px.items()}
    return cv


def regress():
    """At theta 0, build() must be rig.build pixel for pixel on every pose of every live sheet that the
    juggle's build supports (the fly, with its side_face and shear, and the pound, with its
    front_over_sides, are rig.build's alone)."""
    import rig_poses as RP
    cases = [('hover_up', rig.HOVER_UP), ('hover_down', rig.HOVER_DOWN), ('sig', rig.SIGNATURE)]
    for name in ('hover', 'takeoff', 'land', 'roar', 'recover', 'hit', 'dizzy'):
        for i, P in enumerate(getattr(RP, name)()):
            cases.append(('%s%d' % (name, i), P))
    bad = 0
    for name, P in cases:
        a = rig.build(P).px
        b = build(P, 0).px
        if a != b:
            diff = sum(1 for q in set(a) | set(b) if a.get(q) != b.get(q))
            print('DIFF', name, diff)
            bad += 1
    print('jrig.regress: %d poses, %d differ from rig.build' % (len(cases), bad))
    return bad


if __name__ == '__main__':
    import sys
    sys.exit(regress())
