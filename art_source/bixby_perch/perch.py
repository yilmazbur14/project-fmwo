"""The perch rig: beast Bixby hanging off the middle of the top rope, facing the camera.

Built from the approved redesign's parts, imported read-only from art_source/bixby_redesign (the
redesign artist's rig_heads / rig_faces / rig_wings / rig_body, which reproduce the approved frames
pixel for pixel), re-posed: the three heads drop below the rope and lean out over the ring, the hind
legs reach up and hook their talons over the rope, the forelegs hang, and the wings spread up and out
over the crowd. Symmetric about x = 95.5 (a pixel at x mirrors to 191 - x) except the tail and Liam's
headband tails, as in the approved design, and wherever a pose gives a left side of its own.

The top rope has the gate's doorway in the middle (screen x 852..1067); with him centred on x 960 the
rope only exists at frame columns <= 59 and >= 132, so the talons hook it either side of the doorway.

build(P) takes a pose dict. Every field is optional except wings, hind, front, neck, side and mid:
  wings, wings_left   rig_wings poses (right; the left mirrored from wings_left or wings)
  tail_path, tail_tip the tail's centre line and the white tip's base (None hides the tail)
  band_wave           wave of Liam's headband tails
  hind, hind_left     joints hip, hock, ankle, paw of the right hind leg (a left one authored as a right)
  grip                'hook' (talons over the rope) or 'open' (letting go); see hindleg.py
  torso               (dx, dy) for mantle, belly and chest
  front, front_left   rig_body.FRONT joints (absolute)
  neck, neck_left     (base, top) of the right side neck
  side, side_left     rig_heads.side_head kwargs, or {'draw': fn() -> right head pixels}; side_left is
                      built as a right head and mirrored
  side_out            both side heads turned outward (the approved ones look in at the middle)
  mid                 rig_heads.mid_head kwargs, or {'draw': fn(cv)} for a head drawn another way
  fx_back, fx         callables fx(cv) stamped behind everything / over everything
  front_over_sides    forelegs stamped over the side heads
Stamp order, back to front: fx_back, wings, headband tails, tail, hind legs, torso, forelegs, side
necks, side heads, middle head, fx.
"""
from common import canvas, pal, heads, RB, RW, RH, FH
from pal import mir
import hindleg

def side_px(S):
    """The right side head's pixels. rig_heads.side_head draws on a 160-row canvas, so a head lower than
    that is built higher and moved down (it moves as a whole, so this is the same drawing)."""
    S = dict(S)
    dy = S.pop('dy', 0) + S.pop('bob', 0)
    lift = max(0, dy - 20)
    head = RH.side_head(dy=dy - lift, **S)
    return {(x, y + lift): k for (x, y), k in head.px.items()}


def stamp_pair(cv, right, left=None, outline=True):
    cv.stamp(mir(left if left is not None else right), outline=outline)
    cv.stamp(right, outline=outline)


def build(P, h=FH):
    cv = canvas(h)
    for f in P.get('fx_back', []):
        f(cv)
    RW.build(cv, P['wings'], mir, P.get('wings_left'))
    M = P['mid']
    mid_xf = RH.mid_xf(M, M.get('bob', 0)) if 'draw' not in M else M.get('xf')
    if mid_xf is not None and not P.get('hide_band_tails'):
        for t in heads.headband_tails(mid_xf, wave=P.get('band_wave', 0)):
            cv.stamp(mir(t) if P.get('band_mirror') else t)
    if P.get('tail_path'):
        cv.stamp(RB.tail(P['tail_path']))
        cv.stamp(RB.tail_tip(P['tail_tip']))
    grip = P.get('grip', 'hook')
    hr = hindleg.leg(P['hind'], grip)
    hl = hindleg.leg(P['hind_left'], P.get('grip_left', grip)) if P.get('hind_left') else None
    for i, p in enumerate(hr):
        stamp_pair(cv, p, hl[i] if hl else None)
    tdx, tdy = P.get('torso', (0, 0))
    for p in RB.torso(tdx, tdy):
        cv.stamp(p)

    def front_legs():
        fr = RB.front_leg(P['front'])
        fl = RB.front_leg(P['front_left']) if P.get('front_left') else None
        for i, p in enumerate(fr):
            stamp_pair(cv, p, fl[i] if fl else None)
        paw_r = RB.paw(True, P['front']['paw'])
        paw_l = RB.paw(True, P['front_left']['paw']) if P.get('front_left') else None
        stamp_pair(cv, paw_r, paw_l, outline=False)
    if not P.get('front_over_sides'):
        front_legs()
    nb, nt = P['neck']
    nl = P.get('neck_left')
    stamp_pair(cv, RB.side_neck(nb, nt), RB.side_neck(nl[0], nl[1]) if nl else None)
    if 'draw' in P['side']:
        right = P['side']['draw']()
        left = P['side_left']['draw']() if P.get('side_left') else right
    else:
        right = side_px(P['side'])
        left = side_px(P['side_left']) if P.get('side_left') else right
    if P.get('side_out'):
        # both side heads turned outward: the right-head drawing (it looks left) goes on the left, its
        # mirror on the right (as rig.build's side_face)
        left_out = {(x - 121, y): k for (x, y), k in left.items()}
        right_out = mir({(x - 121, y): k for (x, y), k in right.items()})
        cv.px.update(left_out)
        cv.px.update(right_out)
    else:
        cv.px.update(mir(left))
        cv.px.update(right)
    if P.get('front_over_sides'):
        front_legs()
    if 'draw' in M:
        M['draw'](cv)
    else:
        RH.mid_head(cv, **M)
    for f in P.get('fx', []):
        f(cv)
    return cv


def fore(dy=0, dx=0, **over):
    """The approved front leg moved by (dx, dy), with any joints overridden (absolute)."""
    J = {k: (v[0] + dx, v[1] + dy) for k, v in RB.FRONT.items()}
    J.update(over)
    return J
