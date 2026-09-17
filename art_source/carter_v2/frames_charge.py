from approved import *
import paint_charge as pc


def f5():
    return copyg(CHARGE)


def f6():
    # legs mirrored (right knee drives, left leg pushes off), shaded with the house light
    legF = {48: (31, 43), 49: (30, 44), 50: (30, 45), 51: (30, 45), 52: (30, 45), 53: (31, 45), 54: (32, 44), 55: (33, 43)}
    bootF = {54: (31, 45), 55: (31, 45), 56: (30, 45), 57: (30, 45), 58: (30, 45), 59: (31, 44), 60: (32, 43)}
    legB = {49: (18, 30), 50: (17, 29), 51: (17, 28), 52: (17, 28), 53: (17, 27), 54: (17, 27), 55: (17, 26)}
    bootB = {55: (16, 27), 56: (16, 27), 57: (16, 27), 58: (16, 27), 59: (15, 27), 60: (15, 27), 61: (14, 28),
             62: (14, 28), 63: (14, 28)}
    parts = [Part('legF', 4, 'skin', span_pixels(legF)), Part('bootF', 3, 'boot', span_pixels(bootF)),
             Part('legB', 2, 'skin', span_pixels(legB)), Part('bootB', 1, 'boot', span_pixels(bootB))]
    legs, lab = shade(parts, term_x=44)
    for x in range(10, 50):  # boot top rims + lifted boot toe rim
        for y in range(54, 63):
            if lab[y][x] in ('bootF', 'bootB') and legs[y][x] in 'qkK' and legs[y - 1][x] == '#':
                legs[y][x] = 'g' if lab[y][x] == 'bootB' else 'q'
                break
    # speed lines shifted up 4 so they stream past between frames
    g = blank()
    for x, a, b, w in pc.SPEED:
        a2, b2 = max(0, a - 4), b - 4
        n = b2 - a2 + 1
        if n < 3:
            continue
        for i, y in enumerate(range(a2, b2 + 1)):
            t = i / max(1, n - 1)
            g[y][x] = 'L' if t < 0.25 else ('F' if t < 0.55 else 'f')
            if w == 2 and t >= 0.4:
                g[y][x + 1] = 'L' if t < 0.6 else 'F'
    # extra streak low on the left where the pushing leg now is
    for i, y in enumerate(range(40, 50)):
        g[y][9] = 'L' if i < 3 else ('F' if i < 6 else 'f')
    paste(g, legs)
    sp, _ = pc.paint([pc.L_SPEEDO], with_speed=False)
    paste(g, sp)
    upper, _ = pc.paint([pc.L_TORSO, pc.L_ARM_TRAIL, pc.L_DELT_LEAD], with_speed=False)
    upper = over_head(upper)
    fore, _ = pc.paint([pc.L_FOREARM, pc.L_FIST], with_speed=False)
    paste(upper, fore)
    # bob: upper body 1px lower, clipped so it never covers the speedo outline row
    moved = blank()
    paste(moved, upper, 0, 1)
    for y in range(64):
        for x in range(64):
            if moved[y][x] != '.' and not (y >= 44 and sp[y][x] != '.'):
                g[y][x] = moved[y][x]
    return g


def over_head(g):
    return paste(g, HEAD_TUCK)
