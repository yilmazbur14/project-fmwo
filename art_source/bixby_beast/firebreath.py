"""Fire-breath key pose: 3 frames of 192x256 (same origin as the 192x160 hover frame).
F0 wind-up (heads reared back, throats charging), F1 lunge + burst, F2 lunge + full stream.
Body and fire are rendered as separate layers."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from lib import *
from pal import PALC, BLACK
import beast as BS
import fire as FX
import view

FW, FH = 192, 256

BASE = dict(BS.HOVER)
BASE['H'] = FH

WINDUP = dict(BASE)
WINDUP.update(
    mh=(96, 19), mc_top=71,
    sh=(20, 37), sc_a=(32, 78), sc_b=(56, 74), sn_top=(45, 78),
    w_elbow=(60, 54), w_wrist=(40, 8), w_thumb=(45, 1),
    w_tips=[(10, 16), (7, 50), (16, 88), (46, 110)],
    mh_jaw=1, sh_jaw=1,
    f_sh=(62, 101), f_el=(52, 114), f_wr=(50, 126), f_paw=(48, 132),
)

LUNGE = dict(BASE)
LUNGE.update(
    mh=(96, 30), mc_top=83, mc_sag=2.5,
    side_facing='in', sh=(22, 52), sh_jaw=3, mh_jaw=4,
    sc_a=(38, 95), sc_b=(62, 91), sn_top=(50, 86),
    f_sh=(62, 101), f_el=(46, 113), f_wr=(38, 124), f_paw=(35, 130),
    w_elbow=(60, 58), w_wrist=(40, 10), w_thumb=(45, 2),
    w_tips=[(11, 19), (9, 52), (16, 88), (44, 110)],
    tails=[[(0, -1), (7, -8), (15, -14), (25, -17), (34, -23), (43, -25)],
           [(0, 1.5), (9, -3), (18, -9), (28, -10), (37, -15), (46, -15)]],
)


def mouth_origin(cv, box):
    """centroid of the hottest (white) pixels inside a box -> fire origin"""
    x0, y0, x1, y1 = box
    pts = [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1) if cv.get(x, y) == PALC['W']]
    hot = [(x, y) for (x, y) in pts if any(cv.get(x + dx, y + dy) in (PALC['L'], PALC['O']) for dx in (-1, 0, 1) for dy in (-1, 0, 1))]
    use = hot or pts
    if not use:
        return None
    return (sum(p[0] for p in use) / len(use) + 0.5, sum(p[1] for p in use) / len(use) + 0.5)


def build(pose, dy=0):
    dy = dy + BS.Y0
    wings = BS.build_wings(BS.shifted(pose, dy))
    body = BS.build_body(pose)
    comp = Canvas(FW, FH)
    comp.blit(wings, 0, 0)
    comp.blit(body, 0, dy)
    return comp


if __name__ == '__main__':
    tag = sys.argv[1] if len(sys.argv) > 1 else 'fb1'
    f0 = build(WINDUP)
    f1 = build(LUNGE)
    # fire origins from the rendered mouths
    om = mouth_origin(f1, (80, 62, 112, 102))
    ol = mouth_origin(f1, (40, 72, 72, 102))
    orr = mouth_origin(f1, (120, 72, 152, 102))
    print('origins', om, ol, orr)
    origins = dict(mid=om, left=ol, right=orr)
    conv = (92, 152)
    fire1 = FX.render(FW, FH, FX.streams_for(origins, conv, 146, 40, stage=0.45), seed=3, embers=8)
    fire2 = FX.render(FW, FH, FX.streams_for(origins, conv, 146, 40, stage=1.0), seed=5, embers=16)
    frames = []
    for body, fire in ((f0, None), (f1, fire1), (f1, fire2)):
        c = body.copy()
        if fire is not None:
            c.blit(fire, 0, 0)
        frames.append(c)
    strip = Canvas(FW * 3, FH)
    for i, c in enumerate(frames):
        strip.blit(c, FW * i, 0)
    strip.save(os.path.join(view.PREV, '%s_strip.png' % tag))
    view.zoom_canvas(strip, 2, '%s_strip_2x.png' % tag)
    view.zoom_canvas(frames[2], 3, '%s_f2_3x.png' % tag)
    print('ok')
