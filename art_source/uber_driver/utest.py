import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ulib, uparts as P
from uhead import HEAD

TORSO = {24: (23, 26), 25: (22, 26), 26: (21, 27), 27: (21, 32), 28: (21, 34), 29: (21, 35),
         30: (22, 35), 31: (22, 36)}
for y in range(32, 37): TORSO[y] = (23, 36)
for y in range(37, 42): TORSO[y] = (23, 37)
for y in range(42, 46): TORSO[y] = (23, 36)

SHOE = ['.KKKKK.....',
        'KNNUUnKK...',
        'KNUUUUUnnK.',
        'KMMMMMMMMMK',
        'KKKKKKKKKKK']
SHOE_FAR = ulib.remap(SHOE, ulib.FAR)


def build(dx=0):
    L = []
    # far leg + shoe
    L.append(P.sprite_layer(SHOE_FAR, 28 + dx, 59))
    fl = [(32, 45), (32, 52), (32, 59)]
    L.append(P.render(P.mask_stroke(fl, [2.8, 2.4, 2.2]), lambda x, y: P.stroke_normal(x, y, fl, [2.8, 2.4, 2.2]), P.RAMP_CHAR_FAR))
    # near leg + shoe
    L.append(P.sprite_layer(SHOE, 25 + dx, 59))
    nl = [(29, 45), (29, 52), (29, 59)]
    L.append(P.render(P.mask_stroke(nl, [2.8, 2.4, 2.2]), lambda x, y: P.stroke_normal(x, y, nl, [2.8, 2.4, 2.2]), P.RAMP_CHAR))
    # torso
    L.append(P.render(P.mask_spans(TORSO), P.span_normal(TORSO, 24, 45), P.RAMP_GREEN))
    # head
    L.append(P.sprite_layer(HEAD, 21, 7))
    # near arm
    arm = [(29, 30), (29, 36), (30, 42)]
    rad = [2.6, 2.3, 2.0]
    L.append(P.render(P.mask_stroke(arm, rad), lambda x, y: P.stroke_normal(x, y, arm, rad), P.RAMP_GREEN))
    hand = [(30, 44), (30, 46)]
    L.append(P.render(P.mask_stroke(hand, [1.6, 1.5]), lambda x, y: P.stroke_normal(x, y, hand, [1.6, 1.5]), P.RAMP_SKIN))
    return P.compose(L)


if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    f = build()
    ulib.write_crop(os.path.join(here, 'test_stand.png'), [f], 14, 4, 49, 63, 9)
    print(ulib.dump(f))
