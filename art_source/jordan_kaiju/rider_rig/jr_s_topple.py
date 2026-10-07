"""jordan_topple: 6 frames, once (0.06, 0.08, 0.10, 0.10, 0.10, 0.11). The parried stomp jolts the kaiju
and flings him off its head: he flails through the air, goes over backwards butt-first in a pratfall,
and lands sitting on the mat.

  0  the jolt: bounced up off the seat, arms flung up, the box hoisted, the sneaker kicked out, a yelp
  1  tipping back off the head: the legs kicking up in front, the near arm windmilling
  2  the pratfall: tipped right back, legs up, arms thrown up, the box held high (never let go)
  3  dropping: coming round, legs still up, arms flailing the other way
  4  butt-first: nearly upright again, legs out in front, bracing for the mat
  5  on the mat (soles and butt on row 95): the bump: hair knocked flat, legs bounced up, arms out,
     dust puffs. Then jordan_dismount_daze.

Every frame is built upright from the rig's parts and then (f1-f4) turned about his hips with the
juggle's RotSprite turner (jr_rot), as the approved juggle's air frames are. PIVOT = his hips (the turn
centre), SEAT on f0, SOLES on f5.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jr_common as C  # noqa: E402
import jr_fig as F     # noqa: E402
import jr_mat as M     # noqa: E402
import jr_rot as ROT   # noqa: E402
import jr_sheet as S   # noqa: E402
import jr_s_daze as D  # noqa: E402

NAME = 'jordan_topple'
TIMES = [0.06, 0.08, 0.10, 0.10, 0.10, 0.11]
LOOP = False
KIND = 'mat'
OFFSET = (-1, 0)
NOTE = ('Start: SEAT (f0) on the kaiju RIDER_SEAT; end: SOLES (f5) on the knock-off spot (his butt and heel on '
        'row 95). PIVOT = his hips on every frame, for the arc between. f5 leads into jordan_dismount_daze f0.')
HIP = (49.0, 68.0)


def flail_fig(face, hair, near_wr, near_hand, far_wr, box_d, near_leg, far_leg, shoes=(-1, -1), up=(0, 0),
              head_tilt=0, near_bend=1, far_bend=-1, box_deg=0):
    """An upright 'flailing' body in build coordinates (before any turn)."""
    ux, uy = up
    fig = F.Fig()
    fh, fk, fa = far_leg
    fig.stamp(M.leg(fh, fk, fa, lit_side=False, hem=fa))
    fig.stamp(M.shoe('far', (fa[0] + 1, fa[1]), quarter=shoes[1]), outline=False)
    fig.stamp_all(M.arm_to('far', ux, uy, far_wr, bend=far_bend))
    fig.stamp(M.hips(0, -2))
    M.torso(fig, ux, uy, frame=1)
    hd = F.head(face, hair=hair, dx=F.HEAD_AT[0] + ux, dy=F.HEAD_AT[1] + uy, tilt=head_tilt)
    fig.stamp(hd, outline=False, name='head')
    nh, nk, na = near_leg
    fig.stamp(M.shoe('near', (na[0] + 1, na[1]), quarter=shoes[0]), outline=False)
    fig.stamp(M.leg(nh, nk, na, hem=na))
    fig.stamp_all(M.arm_to('near', ux, uy, near_wr, bend=near_bend))
    if near_hand:
        rows, at = near_hand
        fig.stamp(F.map_at(rows, *at), outline=False)
    if box_d is None:                       # the box let go: the far hand open at the wrist
        fig.stamp(F.map_at(F.HAND_HANG_FAR, far_wr[0] - 3.5, far_wr[1] - 0.5), outline=False)
        return fig
    bdx, bdy = box_d
    box = F.open_box(bdx, bdy)
    hand = F.far_hand_box(bdx, bdy)
    fig.stamp(box, outline=False, name='box')
    fig.stamp(hand, outline=False)
    return fig


def turned(fig, deg, place):
    """Turn the whole figure `deg` (clockwise +) about the hips and land the hips on `place`."""
    px = ROT.turn(fig.px, deg, HIP, place) if deg else C.shift(fig.px, int(place[0] - HIP[0]), int(place[1] - HIP[1]))
    out = F.Fig()
    out.cv.px.update(px)
    head = fig.pts['head']
    hp = ROT.turn(dict(head), deg, HIP, place) if deg else C.shift(head, int(place[0] - HIP[0]), int(place[1] - HIP[1]))
    out.pts['head'] = {q: px[q] for q in hp if q in px} or hp
    return out


def f0():
    """The jolt, on the seat: the rider bounced up 3, arms flung up, the box hoisted, a yelp."""
    fig = F.Fig()
    import jr_rider as RR
    near = M.arm_to('near', 0, 0, (31.5, 41.0), bend=-1) + [(F.map_at(F.HAND_OPEN_BACK, 25, 35), False)]
    far = M.arm_to('far', 0, 0, (68.0, 38.0), bend=-1)
    head = F.head('yelp', hair='whip_a', dx=F.HEAD_AT[0] - 1, dy=F.HEAD_AT[1], tilt=-6)
    RR.rider(up=(0, 0), head=head, far=far, near=near, box=F.open_box(4, -12), far_hand=F.far_hand_box(4, -12),
             shin=(4, -3), fig=fig)
    fig.cv.px = C.shift(fig.px, 0, -3)
    fig.pts = {k: C.shift(v, 0, -3) for k, v in fig.pts.items()}
    return fig, (49, 70), 'the jolt: bounced 3 texels up off the seat (SEAT = the texel that was on it)'


AIR = (52, 68)          # where the hips hang on the air frames (build coords)


def f1():
    fig = flail_fig('yelp', 'whip_a', near_wr=(33.0, 33.0), near_hand=(F.HAND_OPEN_BACK, (27, 27)),
                    far_wr=(69.0, 37.0), box_d=(5, -13),
                    near_leg=((47.0, 68.0), (58.0, 66.5), (66.0, 61.0)),
                    far_leg=((52.0, 67.5), (62.0, 64.0), (71.0, 66.0)), near_bend=-1)
    return turned(fig, -18, AIR), AIR, 'tipping back off the head'


def f2():
    fig = flail_fig('yelp', 'whip_b', near_wr=(29.0, 36.0), near_hand=(F.HAND_OPEN_BACK, (23, 31)),
                    far_wr=(70.0, 33.0), box_d=(6, -17),
                    near_leg=((47.0, 68.0), (58.5, 63.5), (68.0, 58.5)),
                    far_leg=((52.0, 67.5), (62.5, 61.0), (71.5, 55.0)), near_bend=-1)
    return turned(fig, -38, AIR), AIR, 'the pratfall: tipped right back'


def f3():
    fig = flail_fig('yelp', 'whip_a', near_wr=(30.0, 52.0), near_hand=(F.HAND_OPEN_BACK, (24, 49)),
                    far_wr=(71.0, 40.0), box_d=(7, -10),
                    near_leg=((47.0, 68.0), (58.0, 64.0), (66.5, 67.5)),
                    far_leg=((52.0, 67.5), (62.0, 62.0), (70.5, 59.0)), near_bend=-1)
    return turned(fig, -24, (AIR[0], AIR[1] + 3)), (AIR[0], AIR[1] + 3), 'dropping, flailing'


def f4():
    fig = flail_fig('yelp', 'whip_b', near_wr=(30.0, 40.0), near_hand=(F.HAND_OPEN_BACK, (24, 35)),
                    far_wr=(69.0, 38.0), box_d=(5, -12),
                    near_leg=((47.0, 68.0), (58.5, 65.0), (68.5, 64.0)),
                    far_leg=((52.0, 67.5), (62.5, 63.0), (72.0, 61.0)), near_bend=-1)
    return turned(fig, -8, (AIR[0], AIR[1] + 8)), (AIR[0], AIR[1] + 8), 'butt-first, about to land'


def f5():
    """On the mat: the daze sit, bounced: legs up off the mat, arms out, hair knocked flat, dust."""
    fig = F.Fig()
    head = F.head('yelp', hair='flopped', dx=F.HEAD_AT[0] + D.UP[0] - 2, dy=F.HEAD_AT[1] + D.UP[1] + 1, tilt=-4)
    D.sit_body(fig, head=head)
    for (x, y, r) in ((23, 94, 2), (30, 92, 1), (79, 94, 2), (86, 92, 1), (35, 94, 1)):
        fig.fxput(M.dust(x, y, r), under=True)
    return fig, None, 'the bump: down on the mat'


def frames():
    out = []
    for i, b in enumerate((f0, f1, f2, f3, f4, f5)):
        fig, pivot, note = b()
        a = {'CROWN': S.crown(fig.px, fig.pts['head'])}
        if i == 0:
            a['SEAT'] = pivot            # place on RIDER_SEAT: his butt shows 3 texels above it (the bounce)
            a['PIVOT'] = (49, 64)
        elif pivot is not None:
            a['PIVOT'] = (int(pivot[0]), int(pivot[1]))
        else:
            a['SOLES'] = (49, 95)
            a['PIVOT'] = (49, 91)
        fr = S.to_frame(fig, OFFSET, a, on_mat=(i == 5), note=note)
        S.fill_holes(fr.px)
        out.append(fr)
    return out
