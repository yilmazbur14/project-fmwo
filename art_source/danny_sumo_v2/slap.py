"""Frame 1, the signature pose: the hundred-hand slap as it winds up.

Same ready crouch as the idle from the belt down. His right palm (viewer's left) is cocked high
beside his head, elbow out; his left palm (viewer's right) is already driving at the viewer, big and
foreshortened in front of his gut, the first of the hundred. He is awake: the bubble has popped,
the eyes are open in a glare and the mouth is shouting.

(A shiko stomp was blocked in first and dropped: at this build, a front view has no room for a
raised leg to go up without passing in front of the far shoulder, and a shallower lift read as a
kick or an arm. See shiko_blockin.py.)

Same frame contract as the idle: 176x144, anchor (88, 144), soles' keyline on row 143.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sumo_lib import (Canvas, spoly, capsule, ellipse, sculpt, shade, amap, taper_line, stats, view, MIR,  # noqa: E402
                      SKIN)
import sumo_lib as L  # noqa: E402
import face as F  # noqa: E402
import hands as HN  # noqa: E402
import limbs as LB  # noqa: E402
import danny_v2 as D  # noqa: E402
import lib as jl  # noqa: E402

SHADOW = D.SHADOW
SKINSET = set(SKIN)


# ------------------------------------------------------------------ THE COCKED ARM (viewer's left)
C_UPPER = [(38, 56), (30, 54), (20, 55), (12, 58.5), (7, 64), (6.5, 71), (10, 76.5), (17, 77), (25, 73), (33, 69),
           (40, 66.5)]
C_BICEPS = [(34, 57), (25, 55.5), (17, 57.5), (12.5, 62), (16, 66.5), (24.5, 64.5), (33, 62.5)]
C_FORE = [(7.5, 68), (5.5, 59), (5.5, 50), (7.5, 42), (12, 36), (18.5, 35), (22.5, 39.5), (22.5, 48), (20, 58),
          (16.5, 67), (12, 72)]
C_BRACHIO = [(6.5, 62), (6, 52), (8, 45), (12.5, 44), (14, 53), (12, 63)]
C_WRAP = [(8.5, 31), (21.5, 30.5), (23, 34), (22.5, 38.5), (9, 39), (7.5, 35)]


def palm(cx, cy, s=1.0, thumb=-1, exposure=0.0, fan=1.0, thumb_reach=15.0):
    """An open palm facing the viewer, fingers up and fanned so each one reads at 3x; thumb=-1 puts
    the thumb on the viewer's left. Returned as keylined layers in stamp order: (part, outline)."""
    P = lambda pts: spoly([(cx + x * s, cy + y * s) for (x, y) in pts])  # noqa: E731
    heel = P([(-8.5, 8.5), (-9.8, 1.5), (-8.8, -5.5), (8.8, -5.5), (9.8, 1.5), (8.5, 8.5), (0, 10.5)])
    fingers = []
    # (base x, lean at the tip, length, radius): index next to the thumb ... little finger
    for dx, lean, ln, r in ((-6.2, -3.6, 8.8, 2.3), (-2.1, -1.2, 11.0, 2.4), (2.2, 1.2, 10.4, 2.35),
                            (6.3, 3.6, 7.6, 2.1)):
        if thumb > 0:
            dx, lean = -dx, -lean
        fingers.append(capsule((cx + dx * s, cy - 4.5 * s), (cx + (dx + lean * fan) * s, cy - (4.5 + ln) * s),
                               r * s, (r - 0.3) * s))
    th = capsule((cx + thumb * 8.6 * s, cy + 3.0 * s), (cx + thumb * thumb_reach * s, cy - 3.5 * s), 2.6 * s,
                 2.2 * s)
    layers = []
    # the palm side is the lit, soft side of the hand, with the heart line across it
    hp = shade(heel, sigma=3.5 * s, exposure=0.08 + exposure, cuts=L.CUTS, wrap=L.SKIN_WRAP)
    for i in range(-6, 6):
        q = (int(round(cx + i * s)), int(round(cy - 1.0 * s + abs(i) * 0.12 * s)))
        if q in hp:
            hp[q] = '4'
    layers.append((hp, True))
    for f in fingers:
        layers.append((shade(f, sigma=2.0 * s, exposure=0.05 + exposure, cuts=L.CUTS, wrap=L.SKIN_WRAP), True))
    layers.append((shade(th, sigma=2.2 * s, exposure=0.05 + exposure, cuts=L.CUTS, wrap=L.SKIN_WRAP), True))
    return layers


def cocked_arm(cv):
    cv.stamp(sculpt(spoly(C_UPPER), [(spoly(C_BICEPS), 2.2, 0.35)], sigma=4.5, exposure=0.05), shadow=SHADOW)
    cv.stamp(sculpt(spoly(LB.DELT), [(spoly(LB.DELT_FRONT), 2.6, 0.25), (spoly(LB.DELT_SIDE), 2.6, 0.25)],
                    sigma=6.5, exposure=0.06), shadow=SHADOW, under=1)
    cv.stamp(sculpt(spoly(C_FORE), [(spoly(C_BRACHIO), 2.0, 0.3)], sigma=4.0, exposure=0.06), shadow=SHADOW)
    wrap = spoly(C_WRAP, 1)
    part = {p: 'W' for p in wrap}
    for (x, y) in wrap:
        if (x + y) % 4 == 0:
            part[(x, y)] = 'H'
    jl.rim(part, 'h', 1, 0, depth=1)
    jl.rim(part, 'H', 0, 1, depth=1)
    cv.stamp(part)
    for layer, outline in palm(15.0, 20.5, 1.05, thumb=-1, fan=1.2, thumb_reach=10.5):
        cv.stamp(layer, outline=outline)


# ------------------------------------------------------------------ THE STRIKING ARM (viewer's right)
S_UPPER = [(137, 58), (145, 57), (152, 60), (157, 66), (158.5, 74), (156, 81), (150, 85), (143, 84), (138, 78),
           (135, 70)]
S_BICEPS = [(140, 60.5), (147, 60), (152, 64.5), (153, 72), (148, 77.5), (142, 74), (139, 67)]
S_FORE = [(151, 76), (155, 81), (153, 88), (146, 92.5), (138, 94), (131, 92.5), (129.5, 87), (134, 82),
          (142, 78.5)]
S_BRACHIO = [(147, 78), (153, 81), (151, 87), (145, 89), (140, 86.5), (142, 81)]
S_WRAP = [(127, 81.5), (134, 80.5), (136.5, 85), (136, 91), (130, 93.5), (126, 89)]
PALM_AT = (118.5, 79.5)
PALM_SCALE = 1.3
# two motion arcs trailing the strike, swept from where the palm came from
ARCS = [((118.5, 79.5), 22.0, -35, 25), ((118.5, 79.5), 26.5, -28, 18)]


def striking_arm(cv):
    cv.stamp(sculpt(spoly(S_UPPER), [(spoly(S_BICEPS), 2.2, 0.32)], sigma=4.5, exposure=0.03), shadow=SHADOW)
    dl = [(MIR - x, y) for (x, y) in LB.DELT]
    cv.stamp(sculpt(spoly(dl), [(spoly([(MIR - x, y) for (x, y) in LB.DELT_FRONT]), 2.6, 0.25),
                                (spoly([(MIR - x, y) for (x, y) in LB.DELT_SIDE]), 2.6, 0.25)],
                    sigma=6.5, exposure=0.06), shadow=SHADOW, under=1)
    cv.stamp(sculpt(spoly(S_FORE), [(spoly(S_BRACHIO), 2.0, 0.3)], sigma=4.0, exposure=0.04), shadow=SHADOW)
    wrap = spoly(S_WRAP, 1)
    part = {p: 'W' for p in wrap}
    for (x, y) in wrap:
        if (MIR - x + y) % 4 == 0:
            part[(x, y)] = 'H'
    jl.rim(part, 'h', 1, 0, depth=1)
    jl.rim(part, 'h', 0, 1, depth=1)
    cv.stamp(part)
    for layer, outline in palm(*PALM_AT, s=PALM_SCALE, thumb=-1, exposure=0.03):
        cv.stamp(layer, outline=outline, shadow=SHADOW)


def speed_lines(cv):
    """Motion arcs on the far side of the striking palm: a bright head that thins to a cool tail."""
    import math
    for (cx, cy), r, a0, a1 in ARCS:
        pts = []
        for i in range(0, 25):
            a = math.radians(a0 + (a1 - a0) * i / 24.0)
            q = (int(round(cx + r * math.cos(a))), int(round(cy + r * math.sin(a))))
            if not pts or pts[-1] != q:
                pts.append(q)
        n = len(pts)
        for i, q in enumerate(pts):
            if q in cv.px:
                continue
            t = i / max(1, n - 1)
            if 0.2 < t < 0.8:
                cv.px[q] = 'W' if 0.35 < t < 0.65 else 'H'


# ------------------------------------------------------------------ THE AWAKE FACE
# The eyes open: a heavy black lid slanting down to the inner corner (the glare; the beanie hides
# the brows), white under it, the pupil pushed to the inner side, a lower lid in shadow.
EYE_AWAKE_L = [
    # x: 0-4   5-9   10-13
    "kkk.. ..... ....",    # 0  the lid's outer end, high
    "3kkkk k.... ....",    # 1
    ".kWWW kkkkk ....",    # 2  the lid slants down to the inner corner: the glare
    ".kWWU UWkkk kk..",    # 3  the pupil centred on the white, so the pair looks straight out
    "..kWU UWWWW kkk.",    # 4
    "..3kk kkkkk kkk3",    # 5  lower lid
    "...33 44444 33..",    # 6
]
F._check(EYE_AWAKE_L, 'EYE_AWAKE_L')
EYE_AWAKE_R = [''.join(F.DOWN.get(c, c) for c in r.replace(' ', '')[::-1]) for r in EYE_AWAKE_L]

# The shout: the frown's arch thrown wide open, upper teeth, the dark of the mouth and the tongue.
MOUTH_SHOUT = [
    # x: 78-82 83-87 88-92 93-97
    "..... kkkkk kkkkk .....",    # 0
    "...kk WWWWW WWWWW kk...",    # 1
    "..k11 hWWhW WhWWh 11k..",    # 2
    "..k11 11111 11111 11k..",    # 3
    "..k11 1rrrr rrr11 11k..",    # 4
    "...k1 1rrrr rrrr1 1k...",    # 5
    "....k kk111 111kk k....",    # 6
    "..... .4kkk kkk4. .....",    # 7
]
F._check(MOUTH_SHOUT, 'MOUTH_SHOUT')


def awake_features(cv):
    for part in (amap(EYE_AWAKE_L, 66, 27), amap(EYE_AWAKE_R, 96, 27), amap(F.NOSE, 81, 31),
                 amap(MOUTH_SHOUT, 78, 43)):
        for q, k in part.items():
            cv.px[q] = k


# ------------------------------------------------------------------ BUILD
def build():
    cv = Canvas()
    D.stage_legs(cv)
    D.stage_belt(cv)
    D.stage_torso(cv)
    D.stage_neck(cv)
    cocked_arm(cv)
    D.stage_head(cv, features=awake_features, bubble=False)
    striking_arm(cv)
    L.clean_lone(cv.px)
    return cv


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    os.makedirs(out, exist_ok=True)
    im = build().image()
    im.save(os.path.join(out, 'v2_f1.png'))
    view(im, 4, os.path.join(out, 'v2_f1_4x.png'))
    print(stats(im))
