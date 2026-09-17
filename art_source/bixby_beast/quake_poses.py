"""Pose builders for beast Bixby's combined POUND + SPIN attack.

Sheets built from these:
  bixby_pound.png   6 frames  rear up (0-1) -> slam (2-3) -> recoil / re-cock (4-5); frames 2..5 loop per slam
  bixby_spin.png    8 frames  lead-in (0-1) -> 360 spin loop (2-5) -> wobble to a stop (6-7)
  bixby_dizzy.png   4 frames  grounded sway loop

Everything is in the approved rig's DESIGN space (frame = design + (0, DY)); the ground line is design y 149
== frame y 151 == the feet anchor, and every frame is 192x160.
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from lib import *
import anim_rig as AR
import beast as BS
import beast_poses as BP
import limbs as LM
from beast_poses import side_group, side_group_R, TAILS_FLICK, TAILS_DROOP, HEADBAND_TAILS_HOVER

DY = BP.DY
GROUND = 149          # design space
FW, FH = 192, 160


def arms_layer(P, dy=DY):
    """Just the two front legs, so a raised / slamming claw can be composited OVER the side heads.
    build_body2 draws the front legs before the heads, which buries them in any pose where the arms
    leave the floor; the duplicate underneath is pixel-identical so the overlay is invisible elsewhere."""
    H = P.get('H', 160)
    lib.set_size(FW, H)
    cv = Canvas(FW, H)
    AR.STATE['crack'] = P.get('crack_glow', P.get('glow', 2))
    AR.STATE['claw'] = P.get('claw_scale', 1.0)
    PR = AR.right_params(P)
    LM.front_leg(cv, P, +1)
    LM.front_leg(cv, PR, -1)
    out = Canvas(FW, H)
    out.blit(cv, 0, dy)
    return out

# heads lashing straight back over the shoulders while he rears
TAILS_BACK = [[(0, -1), (-7, -7), (-16, -12), (-26, -14), (-36, -19), (-45, -21)],
              [(0, 1.5), (-8, -2), (-18, -7), (-28, -7), (-38, -12), (-47, -11)]]


# ==================================================================== POUND
def _pound_common(P):
    """glow + face defaults shared by every pound frame"""
    P.setdefault('eyes_mid', 'angry')
    P.setdefault('eyes_side', 'angry')
    return P


def pound_pose(i):
    """0-1 rear back, 2-3 slam + impact, 4-5 recoil and re-cock (2..5 loop)"""
    if i == 0:
        # weight shifts onto the hind legs, front paws break contact, heads start to lift
        P = AR.pose(
            body_dy=-3,
            w_root=(84, 88), w_elbow=(60, 56), w_wrist=(34, 16), w_thumb=(40, 7),
            w_tips=[(10, 24), (7, 56), (14, 90), (44, 108)], w_attach=(80, 112), w_scallop=0.38,
            f_sh=(62, 97), f_el=(52, 112), f_wr=(56, 124), f_paw=(58, 130), claw_scale=1.05,
            h_hip=(83, 126), h_knee=(81, 134), h_ankle=(79, 143), h_paw=(78, 146),
            tail_path=[(86, 128), (68, 137), (50, 142), (33, 140), (22, 132), (18, 120)],
            tail_tip=(18, 119), tail_curve_c=(44, 124),
            mh=(96, 20), mc_top=72, mh_jaw=1, sh_jaw=1,
            tails=TAILS_FLICK,
        )
        P.update(side_group((20, 40), (66, 95)))
        return _pound_common(P)
    if i == 1:
        # PEAK REAR: up on the hind legs, belly bared, both front claws cocked high and wide, heads thrown up
        P = AR.pose(
            body_dy=-9,
            w_root=(84, 82), w_elbow=(54, 42), w_wrist=(24, 8), w_thumb=(30, 2),
            w_tips=[(7, 18), (5, 50), (9, 86), (39, 106)], w_attach=(80, 106), w_scallop=0.34,
            f_sh=(62, 90), f_el=(50, 106), f_wr=(60, 116), f_paw=(64, 121), claw_scale=1.2,
            h_hip=(83, 120), h_knee=(81, 131), h_ankle=(79, 143), h_paw=(78, 146),
            tail_path=[(86, 124), (68, 136), (50, 145), (32, 147), (20, 141), (15, 130)],
            tail_tip=(15, 129), tail_curve_c=(44, 122),
            mh=(96, 12), mc_top=64, mh_jaw=4, sh_jaw=3,
            eyes_mid='roar', eyes_side='roar', mouth_mid='roar', mouth_side='roar',
            tails=TAILS_BACK, side_rot=(26, -26),
        )
        P.update(side_group((12, 30), (66, 88)))
        return _pound_common(P)
    if i == 2:
        # DRIVING DOWN: body falling, claws whipping down past the shoulders, heads snapping forward
        P = AR.pose(
            body_dy=0,
            w_root=(84, 92), w_elbow=(54, 62), w_wrist=(22, 52), w_thumb=(17, 43),
            w_tips=[(6, 66), (4, 96), (12, 124), (44, 136)], w_attach=(78, 118), w_scallop=0.32,
            f_sh=(62, 100), f_el=(46, 114), f_wr=(42, 128), f_paw=(40, 135), claw_scale=1.15,
            h_hip=(83, 125), h_knee=(81, 134), h_ankle=(79, 143), h_paw=(78, 146),
            tail_path=[(86, 128), (68, 138), (50, 144), (33, 143), (22, 135), (19, 123)],
            tail_tip=(19, 122), tail_curve_c=(44, 124),
            mh=(96, 22), mc_top=74, mh_jaw=5, sh_jaw=3,
            eyes_mid='roar', eyes_side='roar', mouth_mid='roar', mouth_side='roar',
            tails=TAILS_FLICK, side_rot=(12, -12),
        )
        P.update(side_group((17, 42), (66, 98)))
        return _pound_common(P)
    if i == 3:
        # IMPACT: both claws buried in the floor, body squashed over them, heads jolted down, wings slammed out
        P = AR.pose(
            body_dy=9,
            w_root=(84, 100), w_elbow=(52, 86), w_wrist=(16, 96), w_thumb=(10, 88),
            w_tips=[(5, 108), (4, 128), (14, 146), (46, 150)], w_attach=(78, 128), w_scallop=0.28,
            f_sh=(62, 110), f_el=(43, 121), f_wr=(37, 134), f_paw=(34, 142), claw_scale=1.2,
            h_hip=(82, 133), h_knee=(80, 139), h_ankle=(78, 144), h_paw=(77, 146),
            tail_path=[(84, 137), (64, 145), (44, 149), (28, 147), (18, 140), (14, 130)],
            tail_tip=(14, 129), tail_curve_c=(40, 126),
            mh=(96, 40), mc_top=92, mh_jaw=6, sh_jaw=4,
            eyes_mid='roar', eyes_side='roar', mouth_mid='roar', mouth_side='roar',
            tails=HEADBAND_TAILS_HOVER, side_rot=(6, -6),
        )
        P.update(side_group((11, 60), (66, 106)))
        return _pound_common(P)
    if i == 4:
        # RECOIL: the floor throws him back up, claws peeling off it, heads bouncing
        P = AR.pose(
            body_dy=1,
            w_root=(84, 92), w_elbow=(56, 66), w_wrist=(26, 46), w_thumb=(22, 36),
            w_tips=[(9, 58), (8, 90), (16, 118), (45, 130)], w_attach=(80, 116), w_scallop=0.34,
            f_sh=(62, 101), f_el=(46, 112), f_wr=(44, 126), f_paw=(44, 132), claw_scale=1.15,
            h_hip=(83, 126), h_knee=(81, 135), h_ankle=(79, 143), h_paw=(78, 146),
            tail_path=[(86, 129), (68, 139), (50, 145), (33, 144), (22, 136), (18, 124)],
            tail_tip=(18, 123), tail_curve_c=(44, 124),
            mh=(96, 24), mc_top=76, mh_jaw=3, sh_jaw=2,
            eyes_mid='angry', eyes_side='angry', mouth_mid='roar', mouth_side='roar',
            tails=TAILS_FLICK, side_rot=(14, -14),
        )
        P.update(side_group((17, 44), (66, 99)))
        return _pound_common(P)
    # 5: RE-COCK -- back up on the hind legs with the claws high, one notch tighter than frame 1 so 5 -> 2 loops
    P = AR.pose(
        body_dy=-7,
        w_root=(84, 84), w_elbow=(55, 46), w_wrist=(26, 10), w_thumb=(32, 3),
        w_tips=[(5, 18), (3, 52), (8, 88), (39, 106)], w_attach=(80, 108), w_scallop=0.34,
        f_sh=(62, 92), f_el=(50, 107), f_wr=(59, 117), f_paw=(63, 122), claw_scale=1.18,
        h_hip=(83, 122), h_knee=(81, 132), h_ankle=(79, 143), h_paw=(78, 146),
        tail_path=[(86, 125), (68, 136), (50, 144), (32, 146), (21, 139), (16, 128)],
        tail_tip=(16, 127), tail_curve_c=(44, 122),
        mh=(96, 15), mc_top=67, mh_jaw=4, sh_jaw=3,
        eyes_mid='roar', eyes_side='roar', mouth_mid='roar', mouth_side='roar',
        tails=TAILS_BACK, side_rot=(22, -22),
    )
    P.update(side_group((13, 33), (66, 91)))
    return _pound_common(P)


# ==================================================================== DIZZY
# he is upright but can't hold a line: the whole figure rocks about the feet, the heads lag behind the
# body and swing the other way, every eye is a swirl. Deliberately NOT the recover slump -- he is
# standing up, wide-legged and reeling, which is what makes it read as a punish window.
DIZZY_SWAY = [(-3.5, 3, -3), (0.0, 0, 0), (3.5, 3, 3), (0.0, 1, 0)]


def dizzy_pose(i):
    rot, bob, lag = DIZZY_SWAY[i]
    k = 6 + bob
    P = AR.pose(
        body_dy=k,
        w_root=(84, 96 + bob), w_elbow=(58, 74 + bob), w_wrist=(26, 78 + bob), w_thumb=(21, 69 + bob),
        w_tips=[(10, 88), (9, 111), (19, 131), (48, 140)], w_attach=(78, 120), w_scallop=0.34,
        f_sh=(63, 107 + bob), f_el=(48, 120), f_wr=(42, 132), f_paw=(40, 138), claw_scale=0.66,
        h_hip=(82, 133 + bob), h_knee=(79, 138), h_ankle=(76, 143), h_paw=(74, 144),
        tail_path=[(84, 136), (64, 143), (44, 147), (28, 145), (17, 139), (13, 130)],
        tail_r=[5.6, 5.0, 4.4, 3.7, 3.0, 2.4], tail_tip=(13, 129), tail_curve_c=(40, 126),
        mh=(96, 34 + bob), mc_top=86 + bob, mh_jaw=4, sh_jaw=3,
        eyes_mid='dizzy', eyes_side='dizzy', mouth_mid='pant', mouth_side='pant',
        tongue_L=4, tongue_R=5, tongue_sway_L=lag, tongue_sway_R=lag,
        glow=1, crack_glow=1, tail_glow=1,
        tails=TAILS_DROOP,
        side_rot=(-10 + lag * 2, 10 + lag * 2),
        rot=(rot, (96, 151)),
    )
    P.update(side_group((12 - lag, 56 + bob), (64, 104 + k)))
    P.update(side_group_R((138 - lag, 56 + bob), (128, 104 + k)))
    return P


def pound_paws(i):
    """(left, right) front paw centres in FRAME coords for the frame's pose"""
    P = pound_pose(i)
    x, y = P['f_paw']
    return (x, y + DY), (192 - x, y + DY)


def pound_layers(i):
    P = pound_pose(i)
    wings, body = AR.render(P, dy=DY)
    return dict(wings=wings, body=body, arms=arms_layer(P))


if __name__ == '__main__':
    import anim_common as AC
    frs = []
    for i in range(6):
        L = pound_layers(i)
        c = Canvas(FW, FH)
        for k in ('wings', 'body', 'arms'):
            c.blit(L[k], 0, 0)
        frs.append(c)
    AC.preview(AC.strip_of(frs), 'pound_draft.png', 3, guides=True)
    print('paws:', [pound_paws(i) for i in range(6)])
