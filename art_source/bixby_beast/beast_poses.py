"""Pose builders for the beast Bixby combat sheets (fly / land / recover / hit / takeoff / roar).
All poses are rig parameter dicts in DESIGN space (frame = design + (0, DY)); the ground line is design y 149
(frame y 151 == the feet anchor)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from lib import *
import anim_rig as AR
import beast as BS

DY = 2
HOVER = BS.HOVER
FLAP = BS.FLAP

HEADBAND_TAILS_HOVER = [[(0, -1), (8, -6), (18, -11), (29, -12), (40, -18), (50, -18)],
                        [(0, 1.5), (9, -1), (19, -6), (30, -5), (41, -10), (51, -8)]]
TAILS_DROOP = [[(0, -1), (5, 5), (10, 12), (14, 19), (16, 27), (17, 35)],
               [(0, 1.5), (4, 8), (7, 15), (9, 22), (9, 30), (8, 38)]]
TAILS_FLICK = [[(0, -1), (8, -9), (17, -16), (27, -19), (36, -26), (44, -30)],
               [(0, 1.5), (9, -4), (19, -10), (29, -11), (38, -17), (48, -18)]]


def side_group(sh, base=None, top_dx=0, top_dy=0):
    """left side head group with the approved head / collar / neck-top offsets (from the hover pose)"""
    sx, sy = sh
    d = dict(sh=sh, sc_a=(sx + 12, sy + 41), sc_b=(sx + 36, sy + 37), sn_top=(sx + 25 + top_dx, sy + 40 + top_dy))
    if base is not None:
        d['sn_base'] = base
    return d


def side_group_R(sh_R, base_R=None, top_dx=0, top_dy=0):
    """right side head group given the right head's box origin (real coords, the head faces right)"""
    rx, ry = sh_R
    sx = 150 - rx                                   # equivalent left-side box x
    a, b = (sx + 12, ry + 41), (sx + 36, ry + 37)
    d = dict(sh_R=sh_R, sc_a_R=(192 - b[0], b[1]), sc_b_R=(192 - a[0], a[1]),
             sn_top_R=(192 - (sx + 25 + top_dx), ry + 40 + top_dy))
    if base_R is not None:
        d['sn_base_R'] = base_R
    return d


# ================================================================== grounded legs
def planted_legs(k=0, spread=0, bend=0):
    """front paws on the ground line, hind paws tucked just behind them. k lowers the shoulders/hips (crouch)."""
    return dict(
        f_sh=(62, 101 + k), f_el=(50 - spread, 118 + k * 0.6 + bend), f_wr=(46 - spread, 134 + bend * 0.3),
        f_paw=(45 - spread, 141), claw_scale=0.72,
        h_hip=(82, 128 + k), h_knee=(80 - spread * 0.3, 136 + k * 0.4), h_ankle=(79 - spread * 0.3, 143), h_paw=(78 - spread * 0.3, 146),
    )


# ================================================================== LAND
def land_pose(i):
    if i == 0:
        # wings flare high and wide to brake, legs reach for the floor, heads look down at the landing spot
        P = AR.pose(
            w_root=(84, 92), w_elbow=(60, 52), w_wrist=(36, 10), w_thumb=(42, 3),
            w_tips=[(9, 20), (6, 52), (12, 86), (43, 106)], w_attach=(80, 112), w_scallop=0.36,
            f_sh=(62, 101), f_el=(52, 119), f_wr=(49, 133), f_paw=(48, 141), claw_scale=1.0,
            h_hip=(83, 128), h_knee=(82, 136), h_ankle=(81, 145), h_paw=(81, 148),
            tail_path=[(86, 129), (68, 136), (50, 136), (34, 128), (26, 116), (24, 104)],
            tail_tip=(24, 103), tail_curve_c=(50, 120),
            mh=(96, 24), mc_top=76, mh_jaw=1, sh_jaw=1,
            tails=TAILS_FLICK,
        )
        P.update(side_group((21, 44), (66, 97)))
        return P
    if i == 1:
        # IMPACT: squash, legs buckle outward, wings slammed down and out, heads jolted down
        k = 10
        P = AR.pose(
            body_dy=k,
            w_root=(84, 100), w_elbow=(54, 84), w_wrist=(18, 92), w_thumb=(11, 85),
            w_tips=[(6, 104), (6, 125), (15, 145), (46, 149)], w_attach=(78, 128), w_scallop=0.30,
            f_sh=(62, 111), f_el=(46, 124), f_wr=(40, 136), f_paw=(38, 141), claw_scale=0.72,
            h_hip=(82, 138), h_knee=(79, 142), h_ankle=(77, 145), h_paw=(76, 146),
            tail_path=[(84, 140), (64, 146), (44, 149), (28, 147), (18, 140), (14, 130)],
            tail_tip=(14, 129), tail_curve_c=(40, 126),
            mh=(96, 42), mc_top=94, mh_jaw=3, sh_jaw=2,
            tails=HEADBAND_TAILS_HOVER,
        )
        P.update(side_group((12, 62), (66, 107)))
        return P
    # settle into a heavy crouch: rebound a little, wings half folded, heads lowering, still glowing
    k = 7
    P = AR.pose(
        body_dy=k,
        w_root=(84, 98), w_elbow=(58, 70), w_wrist=(24, 70), w_thumb=(20, 61),
        w_tips=[(6, 84), (6, 110), (16, 132), (46, 142)], w_attach=(78, 124), w_scallop=0.36,
        f_sh=(62, 108), f_el=(48, 123), f_wr=(43, 136), f_paw=(41, 141), claw_scale=0.72,
        h_hip=(82, 135), h_knee=(80, 140), h_ankle=(78, 144), h_paw=(77, 146),
        tail_path=[(84, 139), (64, 145), (44, 148), (28, 146), (18, 139), (14, 129)],
        tail_tip=(14, 128), tail_curve_c=(40, 126),
        mh=(96, 38), mc_top=90, mh_jaw=1, sh_jaw=1,
        tails=HEADBAND_TAILS_HOVER,
    )
    P.update(side_group((14, 58), (66, 104)))
    return P


# ================================================================== TAKEOFF
def takeoff_pose(i):
    if i == 0:
        # deep crouch, wings cocked high for the downbeat, heads low and forward
        k = 12
        P = AR.pose(
            body_dy=k,
            w_root=(84, 100), w_elbow=(64, 50), w_wrist=(52, 8), w_thumb=(58, 2),
            w_tips=[(30, 6), (18, 32), (18, 66), (40, 100)], w_attach=(80, 122), w_scallop=0.40,
            f_sh=(62, 113), f_el=(46, 126), f_wr=(41, 137), f_paw=(40, 141), claw_scale=0.72,
            h_hip=(82, 139), h_knee=(79, 143), h_ankle=(77, 145), h_paw=(76, 146),
            tail_path=[(84, 141), (64, 146), (44, 149), (28, 146), (20, 137), (20, 126)],
            tail_tip=(20, 125), tail_curve_c=(40, 126),
            mh=(96, 44), mc_top=96, mh_jaw=0, sh_jaw=0,
            tails=HEADBAND_TAILS_HOVER,
        )
        P.update(side_group((14, 64), (66, 109)))
        return P
    if i == 1:
        # huge downbeat: wings swept down and wide, legs pushing off, heads up
        P = AR.pose(
            body_dy=2,
            w_root=(84, 94), w_elbow=(48, 88), w_wrist=(12, 92), w_thumb=(7, 85),
            w_tips=[(6, 106), (6, 129), (17, 148), (46, 150)], w_attach=(80, 126), w_scallop=0.28,
            f_sh=(62, 103), f_el=(52, 120), f_wr=(48, 135), f_paw=(47, 142), claw_scale=0.85,
            h_hip=(83, 130), h_knee=(82, 137), h_ankle=(81, 144), h_paw=(81, 147),
            tail_path=[(86, 131), (68, 140), (48, 146), (30, 145), (18, 137), (12, 126)],
            tail_tip=(12, 125), tail_curve_c=(40, 128),
            mh=(96, 22), mc_top=74, mh_jaw=2, sh_jaw=1,
            tails=TAILS_FLICK,
        )
        P.update(side_group((20, 42), (66, 99)))
        return P
    # rising: legs dangle, wings sweep back up (hover frame 3 wings), body at hover height
    P = dict(HOVER)
    P.update({k: v for k, v in FLAP[3].items() if k != 'dy'})
    P.update(tails=TAILS_FLICK)
    return P


# ================================================================== HIT (from the exhausted pose)
def exhausted(k=0, head=0, side=0, jaw=2, wing=0, tongue=(4, 5), sway=(0, 0), eyes='tired', mouth='pant',
              eyes_side='tired', mouth_side='pant', glow=1, mh=None, sh=None, sh_R=None, wing_lift=0, tails=None):
    P = AR.pose(
        body_dy=8 + k,
        w_root=(84, 99 + k), w_elbow=(55, 68 + wing - wing_lift), w_wrist=(14, 101 + wing - wing_lift * 1.5),
        w_thumb=(9, 93 + wing - wing_lift * 1.5),
        w_tips=[(6, 114 - wing_lift), (6, 134 - wing_lift * 0.5), (14, 150), (42, 151)], w_attach=(74, 130), w_scallop=0.36,
        tail_path=[(84, 140), (64, 146), (44, 149), (26, 147), (16, 140), (13, 130)],
        tail_r=[5.6, 5.0, 4.4, 3.7, 3.0, 2.4], tail_tip=(13, 129), tail_curve_c=(40, 126),
        h_hip=(82, 136), h_knee=(80, 141), h_ankle=(78, 144), h_paw=(76, 146),
        f_sh=(63, 109 + k), f_el=(52, 125), f_wr=(48, 137), f_paw=(47, 142), claw_scale=0.7,
        mh=mh or (96, 64 + head), mc_show=False, neck_show=False,
        tails=tails or TAILS_DROOP,
        glow=glow, eyes_mid=eyes, mouth_mid=mouth, mh_jaw=jaw,
        eyes_side=eyes_side, mouth_side=mouth_side, sh_jaw=1, tongue_L=tongue[0], tongue_R=tongue[1],
        tongue_sway_L=sway[0], tongue_sway_R=sway[1],
    )
    P.update(side_group(sh or (9, 80 + side), (62, 104 + k)))
    if sh_R is not None:
        P.update(side_group_R(sh_R, (192 - 62, 104 + k)))
    return P


RECOVER_LOOP = [
    dict(k=0, head=0, side=0, jaw=2, wing=0, tongue=(4, 5), sway=(0, 0)),
    dict(k=1, head=1, side=1, jaw=3, wing=1, tongue=(5, 6), sway=(1, -1)),
    dict(k=2, head=3, side=2, jaw=3, wing=2, tongue=(5, 6), sway=(1, -1)),
    dict(k=1, head=2, side=1, jaw=2, wing=1, tongue=(4, 5), sway=(0, 0)),
]


def recover_pose(i):
    return exhausted(**RECOVER_LOOP[i])


def hit_pose(i):
    if i == 0:
        # SNAP: every head whips up and out, eyes squeezed shut, yelping; wings jolt; body jolts up
        P = exhausted(k=-3, mh=(96, 50), sh=(8, 62), sh_R=(142, 62), jaw=4, wing=0, wing_lift=10, tongue=(0, 0),
                      eyes='shut', mouth='yelp', eyes_side='shut', mouth_side='yelp', tails=TAILS_FLICK)
        P['sn_base'], P['sn_base_R'] = (64, 94), (128, 94)
        P['side_rot'] = (14, -14)
        return P
    return exhausted(k=0, mh=(96, 58), sh=(8, 74), sh_R=(142, 74), jaw=1, wing=0, wing_lift=4, tongue=(0, 0),
                     eyes='shut', mouth='shut', eyes_side='shut', mouth_side='shut')


# ================================================================== ROAR (grounded, fight start)
def roar_pose(i):
    if i == 0:
        # wind-up: coil down, wings folded tight and high, heads pulled in, teeth clenched
        k = 9
        P = AR.pose(
            body_dy=k,
            w_root=(84, 98), w_elbow=(66, 56), w_wrist=(58, 16), w_thumb=(64, 8),
            w_tips=[(40, 10), (30, 34), (30, 68), (50, 100)], w_attach=(80, 120), w_scallop=0.42,
            **planted_legs(k=8, spread=2),
            tail_path=[(84, 139), (64, 145), (44, 148), (28, 145), (20, 135), (20, 124)],
            tail_tip=(20, 123), tail_curve_c=(40, 126),
            mh=(96, 40), mc_top=92, mh_jaw=0, sh_jaw=0,
            eyes_mid='angry', mouth_mid='shut', eyes_side='angry', mouth_side='shut',
            tails=HEADBAND_TAILS_HOVER,
        )
        P.update(side_group((18, 60), (66, 106)))
        return P
    # ROAR: stand tall, wings flung wide open and up, all three heads thrust up with jaws gaping
    j = 1 if i == 2 else 0
    P = AR.pose(
        body_dy=1,
        w_root=(84, 90), w_elbow=(56, 50 - j), w_wrist=(30, 11 - j), w_thumb=(35, 4),
        w_tips=[(8, 18 - j), (6, 50), (10, 84), (40, 106)], w_attach=(80, 112), w_scallop=0.34,
        **planted_legs(k=0, spread=4),
        tail_path=[(86, 131), (68, 138), (50, 138), (34, 128), (26, 114), (26, 100)],
        tail_tip=(26, 99), tail_curve_c=(50, 120),
        mh=(96, 12 - j), mc_top=67, mh_jaw=7, sh_jaw=4,
        eyes_mid='roar', mouth_mid='roar', eyes_side='roar', mouth_side='roar',
        tails=TAILS_FLICK, side_rot=(24 + j * 2, -24 - j * 2),
    )
    P.update(side_group((14 - j, 30 - j), (66, 94)))
    return P


# ================================================================== FLY (banking to the right)
FLY_PIVOT = (96, 100)
FLY_ANGLE = 11
FLY_FLAP = [0, 2, 3]          # hover wing keys used for the 3-frame flap: up -> down -> recovering


def squeeze_wing(key, fx, dx=0, dy=0, root=(84, 90)):
    """scale a hover wing key horizontally about the wing root (fx < 1 = narrower), then offset"""
    out = {}
    for k in ('w_elbow', 'w_wrist', 'w_thumb', 'w_attach'):
        x, y = key[k]
        out[k] = (root[0] + (x - root[0]) * fx + dx, y + dy)
    out['w_tips'] = [(root[0] + (x - root[0]) * fx + dx, y + dy) for x, y in key['w_tips']]
    return out


def fly_pose(i):
    """flight pose facing right: legs tucked back, tail streaming behind, every head looking ahead, the leading
    (right) wing narrower; the whole figure is then banked FLY_ANGLE degrees clockwise (RotSprite) about FLY_PIVOT"""
    key = FLAP[FLY_FLAP[i]]
    P = AR.pose(
        f_sh=(62, 101), f_el=(52, 113), f_wr=(46, 122), f_paw=(41, 126),
        f_sh_R=(130, 101), f_el_R=(138, 115), f_wr_R=(138, 126), f_paw_R=(135, 131),
        h_hip=(83, 128), h_knee=(80, 134), h_ankle=(75, 141), h_paw=(71, 144),
        h_hip_R=(109, 128), h_knee_R=(108, 135), h_ankle_R=(104, 142), h_paw_R=(100, 145),
        tail_path=[(86, 129), (66, 134), (46, 132), (28, 124), (16, 112), (10, 98)],
        tail_r=[5.8, 5.2, 4.5, 3.8, 3.1, 2.5], tail_tip=(10, 97), tail_curve_c=(56, 116),
        face_L='in',
        tails=[[(0, -1), (-4, -9), (-12, -16), (-22, -19), (-32, -25), (-41, -27)],
               [(0, 1.5), (-5, -4), (-14, -9), (-24, -10), (-34, -15), (-43, -15)]],
        rot=(FLY_ANGLE, FLY_PIVOT),
    )
    P.update(squeeze_wing(key, 1.0))
    # the bank lifts the trailing wing: tuck its thumb claw 3px so it stays inside the frame after rotation
    P['w_thumb'] = (P['w_thumb'][0] + 1, P['w_thumb'][1] + 3)
    for k, v in squeeze_wing(key, 0.80, dy=6).items():
        if k == 'w_tips':
            P['w_tips_R'] = [(192 - x, y) for x, y in v]
        else:
            P[k + '_R'] = (192 - v[0], v[1])
    return P, key['dy']
