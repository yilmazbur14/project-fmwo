"""The animation rig: one pose dict in, one frame out, in the approved stamp order.

    import rig
    P = rig.pose(rig.HOVER_UP, bob=-1)          # copy a base pose and override fields
    im = rig.build(P).image()

rig.regress() checks that HOVER_UP / HOVER_DOWN / SIGNATURE are pixel-identical to the approved
frames from frame.py, so everything built here shares the approved look.

Pose fields (all optional, see HOVER_UP for defaults):
  wings, wings_left   rig_wings pose dicts (right; the left is mirrored from wings_left or wings)
  bob                 moves body, heads and tail together (not the wings, as in frame.py)
  tail_path, tail_tip the tail's centre line and the white tip's base point (absolute, pre-bob)
  torso               (dx, dy) for mantle, chest and belly
  front, front_left   rig_body.FRONT joint overrides for the right / left front leg (absolute)
  hind, hind_left     rig_body.HIND joint overrides
  planted             paws flat on the ground instead of hanging (per leg pair: 'front', 'hind')
  neck                ((base), (top)) of the right side neck; mirrored for the left
  side, side_left     rig_heads.side_head(...) kwargs for the right / left side head
  mid                 rig_heads.mid_head(...) kwargs
  tails_wave          wave of Liam's headband tails
  fx                  list of callables fx(cv, pose) stamped last
"""
import copy

from pal import BCanvas, both, mir
import heads
import rig_body as RB
import rig_heads as RH
import rig_wings as RW

HOVER_UP = dict(
    wings=RW.UP, wings_left=None, bob=0,
    tail_path=[(66, 126), (48, 140), (30, 146), (16, 140), (9, 127), (10, 116)], tail_tip=(12, 118),
    torso=(0, 0), front={}, front_left=None, hind={}, hind_left=None, planted=(),
    neck=((118, 98), (142, 82)),
    side=dict(), side_left=None,
    mid=dict(),
    tails_wave=0,
    fx=[],
    hide=(),
)

HOVER_DOWN = dict(copy.deepcopy(HOVER_UP), wings=RW.DOWN, bob=-2, tails_wave=1,
                  tail_path=[(66, 128), (48, 142), (30, 148), (17, 147), (10, 141), (10, 134)],
                  tail_tip=(12, 134))

SIGNATURE = dict(copy.deepcopy(HOVER_UP), side=dict(mouth='roar', dx=2, dy=-3, low_dy=3),
                 mid=dict(mouth='inhale', dy=-2, low_dy=5, fx='inhale'))


def pose(base, **kw):
    P = copy.deepcopy(base)
    for k, v in kw.items():
        P[k] = v
    return P


def _mirror_joints(J):
    return None if J is None else {k: (191 - v[0], v[1]) for k, v in J.items()}


def build(P):
    bob = P.get('bob', 0)
    hide = set(P.get('hide', ()))
    cv = BCanvas(w=P.get('W', 192), h=P.get('H', 160))
    if 'wings' not in hide:
        RW.build(cv, P['wings'], mir, P.get('wings_left'))
    mid = RH.mid_xf(P.get('mid', {}), bob)
    if 'tails' not in hide:
        for t in heads.headband_tails(mid, wave=P.get('tails_wave', 0)):
            cv.stamp(mir(t) if P.get('tails_mirror') else t)
    # tail
    if 'tail' not in hide:
        path = [(x, y + bob) for (x, y) in P['tail_path']]
        cv.stamp(RB.tail(path))
        tx, ty = P['tail_tip']
        cv.stamp(RB.tail_tip((tx, ty + bob)))
    planted = set(P.get('planted', ()))
    # hind legs + paws (right authored, left mirrored unless given)
    hr = RB.hind_leg(P.get('hind'), 0, bob)
    hl = RB.hind_leg(P['hind_left'], 0, bob) if P.get('hind_left') is not None else None
    hpaw_r = RB.paw(False, _joint(P.get('hind'), RB.HIND, 'paw'), 'hind' in planted, 0, bob)
    hpaw_l = RB.paw(False, _joint(P.get('hind_left'), RB.HIND, 'paw'), 'hind' in planted, 0, bob) \
        if hl is not None else None
    for i, p in enumerate(hr):
        cv.stamp(mir(hl[i]) if hl is not None else mir(p))
        cv.stamp(p)
    cv.stamp(mir(hpaw_l) if hpaw_l is not None else mir(hpaw_r), outline=False)
    cv.stamp(hpaw_r, outline=False)
    # torso
    tdx, tdy = P.get('torso', (0, 0))
    for p in RB.torso(tdx, tdy + bob):
        cv.stamp(p)
    # front legs + paws (over the side heads instead, with front_over_sides: a strike toward us)
    fr = RB.front_leg(P.get('front'), 0, bob)
    fl = RB.front_leg(P['front_left'], 0, bob) if P.get('front_left') is not None else None
    fpaw_r = RB.paw(True, _joint(P.get('front'), RB.FRONT, 'paw'), 'front' in planted, 0, bob)
    fpaw_l = RB.paw(True, _joint(P.get('front_left'), RB.FRONT, 'paw'), 'front' in planted, 0, bob) \
        if fl is not None else None

    def front_legs():
        for i, p in enumerate(fr):
            cv.stamp(mir(fl[i]) if fl is not None else mir(p))
            cv.stamp(p)
        cv.stamp(mir(fpaw_l) if fpaw_l is not None else mir(fpaw_r), outline=False)
        cv.stamp(fpaw_r, outline=False)
    if not P.get('front_over_sides'):
        front_legs()
    # side necks
    nb, nt = P.get('neck', ((118, 98), (142, 82)))
    neck_r = RB.side_neck(nb, nt, 0, bob)
    nl = P.get('neck_left')
    neck_l = RB.side_neck(nl[0], nl[1], 0, bob) if nl is not None else None
    cv.stamp(mir(neck_l) if neck_l is not None else mir(neck_r))
    cv.stamp(neck_r)
    # side heads: the left is the mirror of a right-side build. With side_face='right' both face the
    # way he flies: the right one is built at the mirrored spot and flipped over too.
    if 'side' not in hide:
        sp = dict(P.get('side', {}))
        right = RH.side_head(bob=bob, **sp)
        left = RH.side_head(bob=bob, **P['side_left']) if P.get('side_left') is not None else right
        cv.px.update(mir(left.px))
        if P.get('side_face') == 'right':
            sp['dx'] = -121 - sp.get('dx', 0)
            cv.px.update(mir(RH.side_head(bob=bob, **sp).px))
        else:
            cv.px.update(right.px)
    if P.get('front_over_sides'):
        front_legs()
    # middle head
    if 'mid' not in hide:
        RH.mid_head(cv, bob=bob, **P.get('mid', {}))
    for f in P.get('fx', []):
        f(cv, P)
    sx, sy = P.get('shift', (0, 0))
    if sx or sy:
        cv.px = {(x + sx, y + sy): k for (x, y), k in cv.px.items()}
    shear = P.get('shear', 0)
    if shear:
        # lean into the flight: rows shift right the higher they are, the feet row stays put
        cv.px = {(x + int(round((151 - y) * shear)), y): k for (x, y), k in cv.px.items()}
    return cv


def _joint(J, base, key):
    if J and key in J:
        return J[key]
    return base[key]


def regress():
    import frame
    from imgdiff import pixel_diff
    bad = 0
    for name, P, fp in (('up', HOVER_UP, 'up'), ('down', HOVER_DOWN, 'down'), ('sig', SIGNATURE, 'sig')):
        a = build(P).image()
        b = frame.build(fp, frame.BOB[fp]).image()
        d = pixel_diff(a, b)
        print('%-5s %s' % (name, d or 'pixel-identical to frame.py'))
        bad += d is not None
    return bad


if __name__ == '__main__':
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.exit(regress())
