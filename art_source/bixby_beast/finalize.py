"""Build all final strips + per-layer strips into ../final/ (staging), then report anchors."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from lib import *
from pal import PALC, BLACK
import beast as BS
import firebreath as FB
import fire as FX
import shadow as SHD
import gag2 as GAG
import view

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'final')
os.makedirs(OUT, exist_ok=True)


def strip_of(canvases, fw, fh):
    s = Canvas(fw * len(canvases), fh)
    for i, c in enumerate(canvases):
        s.blit(c, fw * i, 0)
    return s


def hover():
    comps, wings_l, body_l = [], [], []
    for key in BS.FLAP:
        Q = dict(BS.HOVER)
        Q.update({k: v for k, v in key.items() if k != 'dy'})
        dy = key['dy'] + BS.Y0
        wings = BS.build_wings(BS.shifted(Q, dy))
        body = BS.build_body(BS.HOVER)
        bl = Canvas(192, 160)
        bl.blit(body, 0, dy)
        comp = wings.copy()
        comp.blit(bl, 0, 0)
        comps.append(comp)
        wings_l.append(wings)
        body_l.append(bl)
    strip_of(comps, 192, 160).save(os.path.join(OUT, 'bixby_beast.png'))
    strip_of(wings_l, 192, 160).save(os.path.join(OUT, 'layer_beast_wings.png'))
    strip_of(body_l, 192, 160).save(os.path.join(OUT, 'layer_beast_body.png'))
    return comps


def firebreath():
    FW, FH = FB.FW, FB.FH
    poses = [FB.WINDUP, FB.LUNGE, FB.LUNGE]
    wings_l, body_l = [], []
    for P in poses:
        dy = BS.Y0
        w = BS.build_wings(BS.shifted(P, dy))
        wl = Canvas(FW, FH)
        wl.blit(w, 0, 0)
        b = BS.build_body(P)
        bl = Canvas(FW, FH)
        bl.blit(b, 0, dy)
        wings_l.append(wl)
        body_l.append(bl)
    probe = wings_l[1].copy()
    probe.blit(body_l[1], 0, 0)
    om = FB.mouth_origin(probe, (80, 62, 112, 102))
    ol = FB.mouth_origin(probe, (40, 72, 72, 102))
    orr = FB.mouth_origin(probe, (120, 72, 152, 102))
    origins = dict(mid=om, left=ol, right=orr)
    conv = (92, 152)
    fire_l = [Canvas(FW, FH),
              FX.render(FW, FH, FX.streams_for(origins, conv, 146, 40, stage=0.45), seed=3, embers=8),
              FX.render(FW, FH, FX.streams_for(origins, conv, 146, 40, stage=1.0), seed=5, embers=16)]
    # wind-up: charging embers rising from each mouth (fire layer, frame 0)
    probe0 = wings_l[0].copy()
    probe0.blit(body_l[0], 0, 0)
    o0 = [FB.mouth_origin(probe0, (80, 50, 112, 90)), FB.mouth_origin(probe0, (20, 55, 60, 90)), FB.mouth_origin(probe0, (132, 55, 172, 90))]
    LICK = ["...r.", "..rOr", ".rOr.", "rOLr.", "rOOr.", ".rr.."]

    def lick(cv, x0, y0, flip=False):
        for dy_, row in enumerate(LICK):
            for dx_, ch in enumerate(row):
                if ch != '.':
                    cv.put(x0 + (4 - dx_ if flip else dx_), y0 + dy_, PALC[ch])
    om0, ol0, or0 = o0
    if om0:
        lick(fire_l[0], int(om0[0]) - 17, int(om0[1]) - 9, flip=True)
        lick(fire_l[0], int(om0[0]) + 12, int(om0[1]) - 9)
    if ol0:
        lick(fire_l[0], int(ol0[0]) - 12, int(ol0[1]) - 8, flip=True)
    if or0:
        lick(fire_l[0], int(or0[0]) + 7, int(or0[1]) - 8)
    comps = []
    for i in range(3):
        c = Canvas(FW, FH)
        c.blit(wings_l[i], 0, 0)
        c.blit(body_l[i], 0, 0)
        c.blit(fire_l[i], 0, 0)
        comps.append(c)
    strip_of(comps, FW, FH).save(os.path.join(OUT, 'bixby_beast_firebreath.png'))
    strip_of(wings_l, FW, FH).save(os.path.join(OUT, 'layer_fire_wings.png'))
    strip_of(body_l, FW, FH).save(os.path.join(OUT, 'layer_fire_body.png'))
    strip_of(fire_l, FW, FH).save(os.path.join(OUT, 'layer_fire_fx.png'))
    return comps, origins, o0


def shadow():
    frames = [SHD.frame(k) for k in SHD.SPANS]
    strip_of(frames, 192, 48).save(os.path.join(OUT, 'bixby_beast_shadow.png'))
    return frames


def gag():
    cv = GAG.build()
    cv.save(os.path.join(OUT, 'bixby_swallow_draft.png'))
    base = Canvas(64, 72)
    base.blit(from_png(GAG.SRC), 0, GAG.OY)
    base.save(os.path.join(OUT, 'layer_gag_base.png'))
    edits = Canvas(64, 72)
    for y in range(72):
        for x in range(64):
            if cv.px[y][x] != base.px[y][x]:
                edits.px[y][x] = cv.px[y][x]
    # pixels the gag erased (transparent over opaque base) cannot live in an overlay layer: list them
    erased = [(x, y) for y in range(72) for x in range(64) if cv.px[y][x] is None and base.px[y][x] is not None]
    edits.save(os.path.join(OUT, 'layer_gag_edits.png'))
    return cv, erased


if __name__ == '__main__':
    h = hover()
    f, origins, o0 = firebreath()
    shadow()
    g, erased = gag()
    print('fire origins (lunge frames 1-2):', {k: (round(v[0], 1), round(v[1], 1)) for k, v in origins.items()})
    print('wind-up mouth centres (frame 0):', [(round(o[0], 1), round(o[1], 1)) if o else None for o in o0])
    print('gag erased pixels:', len(erased))
    print('ok')
