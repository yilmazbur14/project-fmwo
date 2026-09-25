"""jordan_taunt.png: 4 frames, looping. The punish window. In v2's look.

He hoists the chase edition over his head on a stick arm to show the crowd and throws his head back
laughing, the other hand on his hip: chest wide open, eyes shut, not looking at the player at all.
The raised arm's baggy sleeve has fallen back and bunched at his shoulder.

  0  head back, mouth wide on the laugh, the box held high
  1  the laugh shakes him down a pixel; the box dips with him, the jaw half closes
  2  back up and the box pumped a pixel higher, a glint off it
  3  down again (as 1)
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import janim_base as B  # noqa: E402
import janim_box as BX  # noqa: E402
import janim_heads as HD  # noqa: E402

J = B.jordan
V = B.V2B
NAME = 'jordan_taunt'
TIMES = [0.13, 0.11, 0.13, 0.11]
LOOP = True

HEAD_TILT = -11            # degrees, thrown back
HEAD_PIVOT = (45, 33)      # the top of the neck, behind the jaw (head space)
HEAD_AT = B.V2F.HEAD_AT[1]  # v2's upright head offset (the fist-pump's); the tilt is on top of it
BOX_TOP_LEFT = (66, 3)     # where the box sits when held high (build), before the frame's bob


def laugh_head(name, dx, dy):
    part = B.tilt2(HD.head(name), HEAD_TILT, HEAD_PIVOT, 'xy')
    B.close_gaps(part)
    return B.shift(part, dx, dy)


def far_raised_sleeve(arm):
    """v2's raised sleeve (jv2_body.raised_sleeve) mirrored onto his far shoulder for the arm that
    holds the box up: fallen back and bunched round the top of the arm, its opening facing up the arm
    (the dark inside either side of it, the trim across), on the shadow side of him."""
    pts = [(34.6, 43.6), (44.6, 43.6), (45, 46.4), (43.4, 49.2), (40.2, 50.4), (36.6, 49.4), (34.8, 46.6)]
    part = B.fill(B.poly([(99 - x, y) for (x, y) in pts]), 'R')
    B.rim(part, 'V', 1, 0)
    B.rim(part, 'v', 0, 1, only='RV')
    B.stroke(part, [(62, 45), (59, 48), (58, 49)], 'V', only='R')
    for y, (lo, hi), key in ((41, (56, 63), '1'), (42, (55, 64), 'v')):
        xs = [x for (x, yy) in arm if yy == y]
        a0, a1 = (min(xs) - 1, max(xs) + 1) if xs else (99, -99)      # the arm and its keyline
        for x in range(lo, hi + 1):
            if x < a0 or x > a1:
                part[(x, y)] = key
    for x in range(55, 65):
        part[(x, 43)] = '1'
    return part


def far_arm_up(box_dy=0):
    """His left arm raised to hold the box up: a stick arm out of the sleeve bunched at his shoulder,
    a bony elbow, the wrist under the hand that carries the box. On his shadow side, like v2's far
    arm."""
    wx, wy = BOX_TOP_LEFT[0] + 1.4, BOX_TOP_LEFT[1] + 22.8 + box_dy    # the wrist, under the hand
    arm = V.limb([((58.4, 47.5), (63.6, 37.4), 1.55, 1.45), ((63.6, 37.4), (wx, wy), 1.45, 1.3)],
                 knobs=((63.6, 37.6, 1.8),), base='c', lit='d', shade='b')
    for (x, y) in list(arm):                   # the raised arm catches the light on its inner side
        if arm[(x, y)] == 'c' and x <= 63 and y <= 40:
            arm[(x, y)] = 'd'
    sl = far_raised_sleeve(arm)
    through = {q: k for q, k in arm.items() if q[1] in (41, 42)}
    return [(arm, True), (sl, True), (through, False)]


def sparkle(cx, cy):
    out = {(cx, cy): 'W'}
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        out[(cx + dx, cy + dy)] = 'Q'
    return out


def build(dip=0, box_dy=0, head='laugh', glint=None):
    cv = B.Canvas(96, 96)
    cv.stamp(V.legs())
    for s in V.shoes():
        cv.stamp(s, outline=False)
    up = lambda part: B.shift(part, 0, dip)  # noqa: E731
    bdy = dip + box_dy
    for part, ol in far_arm_up(box_dy):
        cv.stamp(up(part), outline=ol)
    cv.stamp(up(V.neck(HEAD_AT[0])))
    cv.stamp(up(V.shirt(0)))
    B.dandruff(cv.px, 0, dip)
    cv.stamp(B.rec('head', laugh_head(head, HEAD_AT[0], HEAD_AT[1] + dip)), outline=False)
    hip = V.near_arm_hip()
    for part, ol in hip:
        cv.stamp(up(part), outline=ol)
    B.rec('hand_near', up(hip[2][0]))
    box = BX.box_at(0, (0, 0), (BOX_TOP_LEFT[0], BOX_TOP_LEFT[1] + bdy))
    cv.stamp(B.rec('box', box), outline=False)
    hand = B.amap(V.FAR_HAND_BOX, BOX_TOP_LEFT[0] - 2, BOX_TOP_LEFT[1] + 17 + bdy)
    cv.stamp(B.rec('hand_far', hand), outline=False)
    fx = {}
    if glint:
        fx = B.rec('glint', sparkle(glint[0], glint[1] + bdy))
        for q, k in fx.items():
            cv.px[q] = k
    return cv, set(fx)


def builders():
    return [lambda: build(dip=0, box_dy=0, head='laugh'),
            lambda: build(dip=1, box_dy=0, head='laugh_mid'),
            lambda: build(dip=0, box_dy=-1, head='laugh', glint=(83, 2)),
            lambda: build(dip=1, box_dy=0, head='laugh_mid')]


def frames_info():
    return B.make_frames(builders())


def frames():
    return [(px, fx) for px, fx, _info in frames_info()]


if __name__ == '__main__':
    for i, (px, fx) in enumerate(frames()):
        st = B.stats(B.to_image(px))
        a = B.audit(px, fx)
        print(i, st, 'gaps', a['gaps'], 'lone', a['lone'], 'holes', a['holes'], 'keys', a['keys'])
