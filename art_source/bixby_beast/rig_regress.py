"""Regression: the extended rig (anim_rig) must rebuild the approved hover + fire-breath frames pixel for pixel."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from lib import *
import anim_rig as AR
import beast as BS
import firebreath as FB
from pngio import read_png

ASSETS = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Bixby/'


def frame_px(path, i, fw, fh):
    w, h, px = read_png(path)
    return [[tuple(px[y][fw * i + x]) for x in range(fw)] for y in range(fh)]


def diff(cv, ref):
    n = 0
    for y in range(cv.h):
        for x in range(cv.w):
            a = cv.px[y][x]
            b = ref[y][x]
            if a is None and b[3] == 0:
                continue
            if a is None or tuple(a) != b:
                n += 1
    return n


ok = True
for i, key in enumerate(BS.FLAP):
    Q = dict(BS.HOVER)
    Q.update({k: v for k, v in key.items() if k != 'dy'})
    dy = key['dy'] + BS.Y0
    wings, body = AR.render(Q, dy=dy)
    comp = AR.compose(wings, body)
    d = diff(comp, frame_px(ASSETS + 'bixby_beast.png', i, 192, 160))
    print('hover frame', i, 'diff', d)
    ok &= d == 0
for i, P in enumerate([FB.WINDUP, FB.LUNGE]):
    wings, body = AR.render(P, dy=BS.Y0)
    comp = Canvas(192, 256)
    comp.blit(wings, 0, 0)
    comp.blit(body, 0, 0)
    ref = frame_px(ASSETS + 'bixby_beast_firebreath.png', i, 192, 256)
    # compare the beast only (the fire layer on the approved frames sits on top): mask out fire pixels
    w, h, fx = read_png(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'final', 'layer_fire_fx.png'))
    n = 0
    for y in range(256):
        for x in range(192):
            if fx[y][192 * i + x][3]:
                continue
            a = comp.px[y][x]
            b = ref[y][x]
            if a is None and b[3] == 0:
                continue
            if a is None or tuple(a) != b:
                n += 1
    print('fire frame', i, 'diff (outside fire)', n)
    ok &= n == 0
print('REGRESSION', 'PASS' if ok else 'FAIL')
