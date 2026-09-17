"""Assemble beast Bixby from parts + heads for a given pose."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from lib import *
from pal import PALC, RAMPC, BLACK
import parts as PT
import heads as HD
import view
import body as BD
import collars as CL
import limbs as LM

HOVER = dict(
    # wings (left side; right mirrored)
    w_root=(84, 90), w_elbow=(58, 60), w_wrist=(35, 15), w_thumb=(39, 5),
    w_tips=[(8, 28), (9, 63), (19, 96), (48, 112)], w_attach=(80, 114), w_scallop=0.42,
    # tail
    tail_path=[(86, 129), (68, 140), (48, 147), (30, 146), (18, 137), (13, 125)],
    tail_r=[5.8, 5.2, 4.5, 3.8, 3.1, 2.5], tail_tip=(13, 124),
    # legs
    h_hip=(83, 128), h_knee=(82, 134), h_ankle=(80, 143), h_paw=(80, 146),
    f_sh=(62, 101), f_el=(50, 116), f_wr=(47, 128), f_paw=(45, 134),
    # side necks / collars
    sn_base=(66, 97), sn_top=(46, 80), sc_a=(33, 81), sc_b=(57, 77), sc_thick=7.5, sc_sag=1.2, sh_c=(68, 98),
    # middle collar
    mc_top=72, mc_h=9, mc_sag=1.8, mc_halfw=19,
    # heads
    mh=(96, 20),
    sh=(21, 40),
    glasses=(56, 20),
)


Y0 = 2   # global design offset inside the frame (keeps >=3 texel margins)

# wing keyframes (left wing, before body bob). F0 = hero pose (wings raised & spread)
FLAP = [
    dict(w_elbow=(58, 60), w_wrist=(35, 15), w_thumb=(39, 5), w_tips=[(8, 28), (9, 63), (19, 96), (48, 112)], w_attach=(80, 114), dy=1),
    dict(w_elbow=(56, 69), w_wrist=(26, 40), w_thumb=(26, 29), w_tips=[(7, 52), (10, 84), (23, 110), (50, 120)], w_attach=(80, 116), dy=0),
    dict(w_elbow=(57, 80), w_wrist=(24, 66), w_thumb=(20, 56), w_tips=[(8, 84), (16, 111), (33, 130), (58, 133)], w_attach=(82, 119), dy=-1),
    dict(w_elbow=(56, 69), w_wrist=(28, 38), w_thumb=(29, 27), w_tips=[(8, 62), (13, 93), (27, 118), (52, 126)], w_attach=(80, 117), dy=0),
]


def shifted(P, dy):
    Q = dict(P)
    for k in ('w_root', 'w_elbow', 'w_wrist', 'w_thumb', 'w_attach'):
        Q[k] = (P[k][0], P[k][1] + dy)
    Q['w_tips'] = [(x, y + dy) for x, y in P['w_tips']]
    return Q


def build_frame(P, key):
    Q = dict(P)
    Q.update({k: v for k, v in key.items() if k != 'dy'})
    dy = key['dy'] + Y0
    wings = build_wings(shifted(Q, dy))
    body = build_body(P)
    wings.blit(body, 0, dy)
    return wings, body


def build_wings(P):
    lib.set_size(192, P.get('H', 160))
    cv = Canvas(192, P.get('H', 160))
    LM.wing(cv, P, +1)
    LM.wing(cv, P, -1)
    return cv


def build_body(P):
    lib.set_size(192, P.get('H', 160))
    cv = Canvas(192, P.get('H', 160))
    LM.tail(cv, P)
    LM.hind_leg(cv, P, +1)
    LM.hind_leg(cv, P, -1)
    BD.torso(cv, P)
    LM.front_leg(cv, P, +1)
    LM.front_leg(cv, P, -1)
    BD.shoulder(cv, P, +1)
    BD.shoulder(cv, P, -1)
    BD.side_neck(cv, P, +1)
    BD.side_neck(cv, P, -1)
    for side in (1, -1):
        a, b = P['sc_a'], P['sc_b']
        if side < 0:
            a, b = (192 - b[0], b[1]), (192 - a[0], a[1])
        CL.collar(cv, a, b, P['sc_thick'], P['sc_sag'], n_spikes=3, spike_len=5.5, spike_w=2.3, studs=2)
    # middle neck fur behind the head
    ox, oy = P['mh']
    neck = ell(ox, oy + 51, 21, 15)
    cv.part(neck, 'fur', ('sphere', ox - 6, oy + 50, 24, 14, 0.1), TH_B)
    HD.headband_tails(cv, ox, oy, P)
    sx, sy = P['sh']
    sj = P.get('sh_jaw', 0)
    if P.get('side_facing', 'out') == 'out':
        HD.side_head(cv, sx, sy, +1, 'spikes', sj)
        HD.side_head(cv, 150 - sx, sy, -1, 'bull', sj)
        HD.glasses_on_horn(cv, sx + 35, sy - 20)
    else:
        HD.side_head(cv, sx, sy, -1, 'spikes', sj)
        HD.side_head(cv, 150 - sx, sy, +1, 'bull', sj)
        HD.glasses_on_horn(cv, sx + 7 - 18, sy - 20, flip=True)
    CL.collar(cv, (77, P['mc_top']), (115, P['mc_top']), P['mc_h'], P['mc_sag'], n_spikes=4, spike_len=7.0, spike_w=2.8, studs=3, light_c=(88, P['mc_top'] - 2))
    HD.middle_horns(cv, ox, oy, P)
    HD.middle_head(cv, ox, oy, P)
    return cv


def build(P=HOVER):
    wings = build_wings(P)
    body = build_body(P)
    wings.blit(body, 0, 0)
    return wings


if __name__ == '__main__':
    tag = sys.argv[1] if len(sys.argv) > 1 else 'v16'
    frames = []
    for i, key in enumerate(FLAP):
        cv, body = build_frame(HOVER, key)
        cv.save(os.path.join(view.PREV, '%s_f%d.png' % (tag, i)))
        frames.append(cv)
    strip = Canvas(192 * 4, 160)
    for i, cv in enumerate(frames):
        strip.blit(cv, 192 * i, 0)
    strip.save(os.path.join(view.PREV, '%s_strip.png' % tag))
    view.zoom_canvas(frames[0], 4, '%s_4x.png' % tag)
    view.zoom_canvas(strip, 2, '%s_strip_2x.png' % tag)
    print('ok')
