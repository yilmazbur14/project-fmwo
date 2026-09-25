"""messatsu_ball / messatsu_eyes / messatsu_lock - what shows in the dark.

All three are drawn as light (additive), and all three live in the dark: the
curtain is down, his body shows at about 7%, and these are the only things the
player reads until the lights snap back on.  Over a stage that dark, additive
colour lands almost exactly as drawn - which is why these, unlike the beam,
can be light.

  BALL  the Satsui no Hado gathering at his palms.  Drawn at full size; the code
        grows it from 0.3 to 1.0 over the charge, so the smallest it is ever
        shown is about 29 px across.  It has to read as a ball and not a dot at
        that size, so the white-hot centre is kept big.  Six frames, looping:
        three arms of energy spiral IN, which is what charging looks like, and
        a bolt or two crackles off the skin.
  EYES  his two eye slits, in his own eye ramp (RAMPS['glow']), slanted down to
        the nose like his brows.  Frame 0 is the steady burn, frame 1 a glint.
  LOCK  the reticle closing on the player.  Violet, NEVER red or yellow.  Its
        six frames are the lock's PROGRESS, not a loop: the arcs rotate in and
        close, the four clamps push inward and it brightens, until frame 5 is
        locked.  It is drawn at its END size (ring radius 13 texels, 39 px at
        3x); the code keeps its own contraction by scaling it from 1.8 down to
        1.0 while the frames advance - the frames are the lock clicking, the
        scale is the squeeze.
"""
import math
import random
from mpal import (Cv, ray, bayer01, sheet, W, P, Q, R, S, T, GL)

# ------------------------------------------------------------------- ball

BS = 32
BC = 16.0


def _lump(a, f, base):
    """a radius that wobbles with angle, so the ball never reads as a disc"""
    return base * (1.0 + 0.07 * math.sin(3 * a + f * 1.05)
                   + 0.04 * math.sin(5 * a - f * 2.1))


def _plot(cv, x, y, c):
    x, y = int(math.floor(x)), int(math.floor(y))
    if 0 <= x < BS and 0 <= y < BS:
        cv.set(x, y, c)


def _bolt(cv, f, i):
    """a jagged bolt leaving the skin and bending round it, with a fork"""
    rnd = random.Random(f * 17 + i * 5)
    a = math.radians(rnd.randint(0, 359))
    r = 10.5
    turn = rnd.choice((-1, 1)) * 0.14
    pts = [(BC + math.cos(a) * r, BC + math.sin(a) * r)]
    for k in range(5):
        a += turn + rnd.uniform(-0.05, 0.05)
        r = min(14.6, r + 0.9 + rnd.uniform(-0.3, 0.5))    # never off the frame
        pts.append((BC + math.cos(a) * r, BC + math.sin(a) * r))
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
        for s in range(n + 1):
            t = s / float(n)
            _plot(cv, x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, P)
    # a short fork off the middle
    fx, fy = pts[2]
    fa = math.atan2(fy - BC, fx - BC) - turn * 6
    for k in range(1, 3):
        _plot(cv, fx + math.cos(fa) * k, fy + math.sin(fa) * k, Q)


def ball_frame(f):
    cv = Cv(BS, BS)
    for y in range(BS):
        for x in range(BS):
            dx, dy = x + 0.5 - BC, y + 0.5 - BC
            r = math.hypot(dx, dy)
            a = math.atan2(dy, dx)
            if r < _lump(a, f, 3.9):
                c = W
            elif r < _lump(a + 0.7, f, 6.4):
                c = P
            elif r < _lump(a + 1.9, f, 9.0):
                c = Q
            elif r < _lump(a + 2.6, f, 11.3):
                c = R
            elif r < _lump(a - 1.1, f, 13.2):
                c = S if bayer01(x + f, y) < 0.72 else None
            elif r < 15.3:
                c = T if bayer01(x, y + f) < 0.34 * (15.3 - r) / 2.1 else None
            else:
                c = None
            if c is not None:
                cv.set(x, y, c)
    # three arms of energy spiralling in, turning a sixth of a lap a frame
    for arm in range(3):
        a0 = math.radians(arm * 120.0 - f * 20.0)
        for s in range(40):
            t = s / 39.0
            r = 14.2 - 8.4 * t
            a = a0 + 2.5 * t
            _plot(cv, BC + math.cos(a) * r, BC + math.sin(a) * r,
                  Q if t < 0.35 else P)
    # crackle: one bolt, two on every other frame
    for i in range(1 + f % 2):
        _bolt(cv, f, i)
    # motes drawn in from outside
    for i in range(4):
        a = math.radians(i * 90.0 + 45.0 + f * 30.0)
        r = 15.4 - ((f * 2 + i * 3) % 6)
        _plot(cv, BC + math.cos(a) * r, BC + math.sin(a) * r, P if r > 12 else Q)
    return cv


def ball_sheet(path):
    return sheet([ball_frame(f) for f in range(6)], path)


# ------------------------------------------------------------------- eyes

EW, EH = 16, 8
# W ffffff, O ffd2d8, V ff5a62, X e0203c, Y 90102a, Z 54061a - his eye ramp
EPAL = {'W': GL[0], 'O': GL[1], 'V': GL[2], 'X': GL[3], 'Y': GL[4], 'Z': GL[5]}

# Each slit is 6 texels, slanted down to the nose with the hot end innermost;
# their centres are 9 texels (27 px at 3x) apart.  The frame's centre texel
# (8, 4) is the point between them.
EYES = [
    """
................
................
.ZY..........YZ.
.YXVO......OVXY.
..ZXVWO..OWVXZ..
....ZY....YZ....
................
................
""",
    """
................
.............Z..
.ZY.........ZOZ.
.YXVO......OWWVY
..ZXVWO..OWWVXZ.
....ZY....YOZ...
............Z...
................
""",
]


def eyes_frame(f):
    cv = Cv(EW, EH)
    cv.stamp(EYES[f], 0, 0, EPAL)
    return cv


def eyes_sheet(path):
    return sheet([eyes_frame(f) for f in range(2)], path)


# ------------------------------------------------------------------- lock

LS = 32
LC = 16.0
RING_R = 13.0


def _ring_arc(cv, r, a_mid, span, colour):
    for y in range(LS):
        for x in range(LS):
            dx, dy = x + 0.5 - LC, y + 0.5 - LC
            if abs(math.hypot(dx, dy) - r) > 0.52:
                continue
            a = math.degrees(math.atan2(dy, dx))
            if abs((a - a_mid + 180.0) % 360.0 - 180.0) <= span / 2.0:
                cv.set(x, y, colour)


def _clamp(cv, ang, r_out, r_in, colour, tip):
    """an inward-pointing wedge: a clamp closing on the target"""
    cv.paint(ray(LS, LS, LC, LC, ang, r_in, r_out, 0.6, 2.1), colour)
    a = math.radians(ang)
    x = int(math.floor(LC + math.cos(a) * (r_in + 0.5)))
    y = int(math.floor(LC + math.sin(a) * (r_in + 0.5)))
    if 0 <= x < LS and 0 <= y < LS:
        cv.set(x, y, tip)


def lock_frame(f):
    cv = Cv(LS, LS)
    # ---- the faint outer track, dashed, turning the other way
    for i in range(12):
        _ring_arc(cv, 14.7, i * 30.0 - f * 9.0, 11.0, T if f < 2 else S)
    # ---- the ring: four arcs rotating in and growing until they close up.
    # turn + span/2 stays under 37 degrees, so an arc never runs into a clamp
    span = (24.0, 34.0, 44.0, 54.0, 64.0, 74.0)[f]
    turn = (25.0, 20.0, 15.0, 10.0, 5.0, 0.0)[f]
    for k in range(4):
        mid = 45.0 + k * 90.0 + turn
        _ring_arc(cv, RING_R, mid, span, Q)
        if f >= 1:
            _ring_arc(cv, RING_R, mid, span * 0.34, (P, P, P, P, W)[f - 1])
        if f >= 4:
            _ring_arc(cv, RING_R - 1.0, mid, span * 0.8, (R, Q)[f - 4])
    # ---- four clamps at N/E/S/W, pushing in
    r_in = (12.6, 11.9, 11.2, 10.5, 9.8, 9.2)[f]
    for k in range(4):
        _clamp(cv, k * 90.0 - 90.0, 14.8, r_in, (Q, Q, Q, P, P, P)[f],
               (P, P, P, W, W, W)[f])
    if f == 5:
        # locked: a pip at each corner
        for k in range(4):
            a = math.radians(45.0 + k * 90.0)
            cv.set(int(LC + math.cos(a) * (RING_R + 2.0)),
                   int(LC + math.sin(a) * (RING_R + 2.0)), P)
    return cv


def lock_sheet(path):
    return sheet([lock_frame(f) for f in range(6)], path)
