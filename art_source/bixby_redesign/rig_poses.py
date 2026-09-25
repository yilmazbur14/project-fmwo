"""Pose lists for each live sheet, in the frame order BixbyBeastArtLayout.gd plays them."""
import copy

import rig_faces2 as F2
import rig_fx as FX
import rig_stance as ST
import rig_wings as RW
from rig import HOVER_DOWN, HOVER_UP, SIGNATURE, pose  # noqa: F401

UP_TAIL = HOVER_UP['tail_path']
DOWN_TAIL = HOVER_DOWN['tail_path']
# the tail lying along the ground behind him when he stands or crouches
GROUND_TAIL = [(66, 134), (48, 146), (30, 150), (16, 146), (10, 138), (10, 130)]


def mix_path(a, b, t):
    return [(pa[0] + (pb[0] - pa[0]) * t, pa[1] + (pb[1] - pa[1]) * t) for pa, pb in zip(a, b)]


def mix_pt(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def moved_path(path, dx=0, dy=0):
    return [(x + dx, y + dy) for (x, y) in path]


def ground_tail(drop):
    """The tail's root rides down with the body; the rest lies along the floor."""
    root = (66, 126 + min(drop, 20) * 0.7)
    return [root, (48, 142), (30, 147), (16, 144), (10, 136), (10, 128)], (12, 128)


def grounded(drop, wings, tail_dy=None, mid=None, side=None, fx=(), **kw):
    """A pose standing on the ground line, the body `drop` px below the hover."""
    S = ST.stance(drop, **kw)
    P = pose(HOVER_UP, wings=wings)
    P.update(S)
    P['tail_path'], P['tail_tip'] = ground_tail(drop)
    if mid:
        P['mid'].update(mid)
    if side:
        P['side'].update(side)
    P['fx'] = list(fx)
    return P


#HOVER

def hover():
    """0 wings up (approved), 1 downstroke, 2 wings down (approved), 3 upstroke. The body rises on
    the downstroke and sinks back; the tail and Liam's headband tails swing a beat behind."""
    return [
        HOVER_UP,
        pose(HOVER_UP, wings=RW.MID, bob=-1, tails_wave=1,
             tail_path=mix_path(UP_TAIL, DOWN_TAIL, 0.5), tail_tip=mix_pt((12, 118), (12, 134), 0.5)),
        HOVER_DOWN,
        pose(HOVER_UP, wings=RW.MID_UP, bob=-1, tails_wave=0,
             tail_path=mix_path(UP_TAIL, DOWN_TAIL, 0.6), tail_tip=mix_pt((12, 118), (12, 134), 0.6)),
    ]


#FLY (drawn flying right; the fight mirrors it to fly left)

FLY_TAIL = [(64, 124), (46, 128), (30, 126), (17, 121), (8, 116), (4, 110)]


def fly():
    """0 wings up, 1 downbeat, 2 recovering. Both side heads turn into the flight, the lead head
    low and forward, the far one high; legs trail back, the tail streams out behind, Liam's headband
    tails stream back too."""
    out = []
    for wings, bob, lines in ((RW.UP, 0, [(2, 16, 58), (6, 24, 96), (2, 12, 128)]),
                              (RW.DOWN, -2, [(4, 20, 50), (2, 14, 88), (8, 26, 118)]),
                              (RW.MID_UP, -1, [(2, 18, 64), (4, 22, 104), (2, 10, 134)])):
        # a touch narrower, so the lean doesn't carry the wingtips off the frame
        P = pose(HOVER_UP, wings=RW.moved(wings, sx=0.92), bob=bob, side_face='right', tails_mirror=True,
                 tails_wave=1 if bob else 0)
        P['side'] = dict(dx=2, dy=3)
        P['side_left'] = dict(dy=-5)
        P['mid'] = dict(dx=3)
        P['front'] = ST.front_joints((121, 100), (130, 141), bend=1, planted=False)
        P['front_left'] = ST.front_joints((119, 100), (116, 140), bend=1, planted=False)
        P['hind'] = ST.hind_joints((134, 110), (144, 143), bend=1)
        P['hind_left'] = ST.hind_joints((138, 110), (166, 141), bend=1)
        P['tail_path'] = FLY_TAIL
        P['tail_tip'] = (6, 112)
        P['fx'] = [FX.speed_lines(lines)]
        P['shear'] = 0.045          # leaning into the flight: the top ~7px ahead of the feet
        out.append(P)
    return out


#TAKEOFF

def takeoff():
    """0 crouch, wings raised to beat; 1 the downbeat, still on the ground, dust thrown out;
    2 rising, legs leaving the ground, grit falling back."""
    f0 = grounded(14, RW.FLARE, front_x=124, hind_x=156)
    f1 = grounded(10, RW.DOWN, front_x=124, hind_x=156, tail_dy=4,
                  fx=[FX.dust(28, 3, drift=-1), FX.dust(164, 3, drift=1), FX.dust(52, 2, drift=-1),
                      FX.dust(140, 2, drift=1)])
    f1['tails_wave'] = 1
    f2 = pose(HOVER_UP, wings=RW.MID_UP, bob=-2, tails_wave=0,
              tail_path=mix_path(UP_TAIL, DOWN_TAIL, 0.3), tail_tip=mix_pt((12, 118), (12, 134), 0.3))
    f2['fx'] = [FX.pebbles([(40, 147, 2), (58, 144, 1), (134, 146, 2), (151, 143, 1), (96, 149, 1),
                            (74, 150, 2), (120, 150, 1)])]
    return [f0, f1, f2]


#LAND

def land():
    """0 wings flared while he comes down, legs reaching for the floor; 1 the impact, crouched
    deep with dust bursting out; 2 the heavy crouch, the dust settling."""
    f0 = pose(HOVER_UP, wings=RW.FLARE, bob=-2)
    f0['front'] = ST.front_joints((119, 100), (123, 146), planted=False)
    f0['hind'] = ST.hind_joints((136, 110), (152, 147))
    f1 = grounded(18, RW.moved(RW.DOWN, dy=6), front_x=126, hind_x=158, head_dy=21,
                  fx=[FX.dust(18, 3, drift=-1), FX.dust(173, 3, drift=1), FX.dust(36, 3, drift=-1),
                      FX.dust(156, 3, drift=1), FX.dust(58, 3, drift=-1), FX.dust(134, 3, drift=1),
                      FX.dust(80, 2, drift=-1), FX.dust(112, 2, drift=1)])
    f2 = grounded(15, RW.FOLD, front_x=125, hind_x=157, head_dy=17,
                  fx=[FX.dust(18, 3, drift=-1), FX.dust(173, 3, drift=1), FX.dust(34, 2, drift=-1),
                      FX.dust(158, 2, drift=1)])
    return [f0, f1, f2]


#ROAR (grounded)

def roar():
    """0 the coil: crouched, heads drawn in, wings folded; 1-2 the roar: standing tall, heads
    thrown up, maws blazing, wings flared, the air ringing - 2 is 1 shaken a texel over."""
    f0 = grounded(10, RW.FOLD, front_x=124, hind_x=156, head_dy=14, side_dx=-4, side_dy=16)
    rays = [FX.rays(96, 60, n=12, r0=44, r1=52), FX.rays(40, 84, n=6, r0=30, r1=36, phase=0.5),
            FX.rays(151, 84, n=6, r0=30, r1=36, phase=0.2)]
    f1 = grounded(0, RW.FLARE, front_x=122, hind_x=154, head_dy=-2, side_dx=3, side_dy=-4,
                  mid=dict(mouth='inhale', low_dy=5), side=dict(mouth='roar', low_dy=3),
                  fx=rays + [FX.pebbles([(30, 149, 2), (60, 146, 1), (132, 147, 2), (160, 144, 1)])])
    f2 = copy.deepcopy(f1)
    f2['shift'] = (1, 0)
    f2['fx'] = [FX.rays(96, 60, n=12, r0=46, r1=54, phase=0.26), FX.rays(40, 84, n=6, r0=32, r1=38, phase=1.0),
                FX.rays(151, 84, n=6, r0=32, r1=38, phase=0.7),
                FX.pebbles([(24, 146, 1), (54, 149, 2), (138, 149, 1), (166, 147, 2)])]
    return [f0, f1, f2]


#RECOVER (the punish window: spent, flat out, tongues out, panting)

SLUMP_TAIL = [(66, 140), (48, 148), (30, 150), (18, 147), (12, 142), (11, 136)]


def slump(breath=0, mid=None, side=None, fx=()):
    # the belly rests on the floor (its lowest row on the ground line at a drop of 15)
    P = grounded(14 + (1 if breath else 0), RW.DRAPE, front_paw=ST.planted_front(110),
                 hind_paw=ST.planted_hind(162), head_dy=44 + breath, side_dx=4, side_dy=38 + breath)
    P['tail_path'] = SLUMP_TAIL
    P['tail_tip'] = (12, 136)
    P['mid'].update(dict(eyes='tired', tongue=F2.mid_tongue_long))
    P['side'].update(dict(eyes='tired', tongue=F2.side_tongue_long()))
    if mid:
        P['mid'].update(mid)
    if side:
        P['side'].update(side)
    P['fx'] = list(fx)
    return P


def recover():
    """Four panting beats: the heads sink and lift with each breath, sweat flicks off."""
    return [
        slump(0, fx=[FX.sweat(64, 56), FX.sweat(126, 54)]),
        slump(1, fx=[FX.sweat(60, 52), FX.sweat(130, 50), FX.sweat(22, 90, -1)]),
        slump(2, fx=[FX.sweat(56, 49), FX.sweat(168, 88)]),
        slump(1, fx=[FX.sweat(70, 58, -1), FX.sweat(122, 57)]),
    ]


#HIT (while he's down)

def hit():
    """0 the heads snap back from the blow, eyes squeezed shut, yelping, sparks; 1 the wince."""
    f0 = slump(0, mid=dict(dy=36, eyes='shut', mouth='yelp', low_dy=5, tongue=None),
               side=dict(dy=31, eyes='shut', mouth='roar', low_dy=3, tongue=None),
               fx=[FX.star4(70, 44, 4), FX.star4(124, 40, 4), FX.star4(96, 32, 3), FX.star4(40, 70, 3),
                   FX.star4(154, 66, 3)])
    f0['torso'] = (0, 12)
    f1 = slump(2, mid=dict(dy=47, eyes='shut', tongue=None), side=dict(dy=41, eyes='shut', tongue=None),
               fx=[FX.star4(62, 56, 2), FX.star4(132, 54, 2)])
    return [f0, f1]


#DIZZY

def dizzy():
    """Standing but reeling: the body sways, the heads loll out of step, swirl eyes, tongues out,
    stars circling his head."""
    out = []
    sway = [(-2, 0), (0, 1), (2, 0), (0, 1)]
    for i, (sx, sy) in enumerate(sway):
        P = grounded(6, RW.moved(RW.DOWN, dy=4), front_x=123, hind_x=155, head_dy=8 + sy,
                     side_dy=10 + (2 if i % 2 else -1), side_dx=2,
                     mid=dict(eyes='dizzy', tongue=F2.mid_tongue_long, dx=sx),
                     side=dict(eyes='dizzy', tongue=F2.side_tongue_long()))
        P['side_left'] = dict(P['side'], dy=10 + (-1 if i % 2 else 2))
        ang = i * 1.5708 / 2
        import math
        stars = []
        for j in range(3):
            a = ang + j * 2.094
            stars.append(FX.star5(int(round(96 + sx + math.cos(a) * 22)), int(round(11 + math.sin(a) * 4))))
        P['fx'] = stars
        out.append(P)
    return out


#POUND (the combined attack: rear back, then slam, looped)

IMPACT_X = 158          # where the claws land, and the mirror at 191 - 158 = 33 (BixbyBeastArtLayout)


def pound():
    """0-1 the rear back (held until he slams), 2 coming down, 3 the claws hit the floor wide apart,
    4 the recoil in a cloud of dust, 5 rising for the next."""
    # the front legs strike toward us, so they are drawn over the side heads throughout
    # (the middle head is already at the top of the frame: the rear shows in the raised claws, the
    # side heads lifting and the body rising off its hind legs)
    f0 = grounded(-4, RW.FLARE, hind_x=154, front_planted=False, front_paw=(146, 116),
                  mid=dict(dy=-1), side=dict(dy=-7, dx=2))
    f1 = grounded(-6, RW.FLARE, hind_x=154, front_planted=False, front_paw=(152, 100),
                  mid=dict(mouth='inhale', low_dy=5, dy=0), side=dict(mouth='roar', low_dy=3, dy=-9, dx=3))
    f2 = grounded(6, RW.UP, hind_x=156, front_planted=False, front_paw=(156, 130), shoulder=(122, 100),
                  mid=dict(dy=6), side=dict(dy=2, dx=2))
    f3 = grounded(18, RW.moved(RW.DOWN, dy=4), hind_x=158, front_paw=ST.planted_front(IMPACT_X),
                  shoulder=(126, 100), mid=dict(dy=19), side=dict(dy=6, dx=3),
                  fx=[FX.ground_flash(IMPACT_X, w=18, h=10), FX.ground_flash(191 - IMPACT_X, w=18, h=10),
                      FX.dust(IMPACT_X + 18, 3), FX.dust(191 - IMPACT_X - 18, 3, drift=-1),
                      FX.dust(IMPACT_X - 16, 2, drift=-1), FX.dust(191 - IMPACT_X + 16, 2)])
    f4 = grounded(12, RW.MID, hind_x=157, front_paw=ST.planted_front(IMPACT_X - 2), shoulder=(125, 100),
                  mid=dict(dy=13), side=dict(dy=5, dx=3),
                  fx=[FX.dust(IMPACT_X + 16, 3), FX.dust(191 - IMPACT_X - 16, 3, drift=-1),
                      FX.dust(IMPACT_X - 14, 3, drift=-1), FX.dust(191 - IMPACT_X + 14, 3),
                      FX.pebbles([(172, 140, 2), (18, 138, 2), (146, 134, 1), (44, 132, 1)])])
    f5 = grounded(4, RW.MID_UP, hind_x=156, front_planted=False, front_paw=(142, 128), shoulder=(122, 100),
                  mid=dict(dy=3), side=dict(dy=1, dx=2),
                  fx=[FX.dust(IMPACT_X + 20, 2), FX.dust(191 - IMPACT_X - 20, 2, drift=-1)])
    out = [f0, f1, f2, f3, f4, f5]
    for P in out:
        P['front_over_sides'] = True
    return out
