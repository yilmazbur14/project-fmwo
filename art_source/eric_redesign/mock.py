"""flat silhouette mocks to choose weapon composition"""
import math
from lib import *
from pngio import blank, paste, scale, write_png

FL = (136, 180, 99, 255)


def flat(cv, mask, ch):
    cv.part(mask, {'W': 'plate', 'K': 'iron', 'R': 'cape', '3': 'hair', 't': 'skin', 'm': 'leath', 'C': 'plate', 'X': 'red'}[ch],
            ('flat', 0, 0), th=[9, 9, 0.0, -2, -3], outline=True,
            bias={'W': -1, 'C': 1, 'X': -1}.get(ch, 0))


def body(cv, arms='L'):
    cape = poly(sym_pts([(48, 40), (30, 40), (15, 47), (10, 60), (7, 76), (6, 90), (9, 94), (13, 90), (18, 95), (23, 91), (28, 95), (32, 92), (48, 93)]))
    flat(cv, cape, 'R')
    for s in (0, 1):
        f = (lambda m: m) if s == 0 else mirror
        flat(cv, f(poly([(24, 89), (42, 89), (44, 92), (44.5, 96), (19, 96), (19, 93)])), 'W')
        flat(cv, f(poly([(27, 84), (42, 84), (43, 91), (26, 91)])), 'C')
        flat(cv, f(ell(34.5, 85, 6.5, 4.5)), 'W')
    for s in (0, 1):
        f = (lambda m: m) if s == 0 else mirror
        flat(cv, f(poly([(24, 69), (46, 75), (46.5, 81), (44, 85), (36, 86.5), (28, 85), (23, 79)])), 'W')
    flat(cv, poly(sym_pts([(48, 76), (43.5, 76), (43, 86), (44.5, 90), (48, 88)])), 'R')
    flat(cv, poly(sym_pts([(48, 70), (24, 65), (23.5, 71), (30, 74.5), (40, 77.5), (48, 78.5)])), 'm')
    torso = poly(sym_pts([(48, 34), (39, 35), (31, 38), (26, 43), (23, 50), (21.5, 57), (22, 63), (24.5, 68), (29, 72), (36, 74.5), (42, 75.5), (48, 75.8)]))
    flat(cv, torso, 'W')
    flat(cv, poly(sym_pts([(48, 48), (46, 48), (46, 52), (41, 52), (41, 56), (46, 56), (46, 64), (48, 64)])), 'X')
    # arms
    # viewer-right arm (his left): akimbo
    if 'R' in arms:
        flat(cv, poly([(70, 48), (82, 46), (89, 58), (86, 66), (80, 62)]), 'K')
        flat(cv, poly([(80, 60), (88, 60), (84, 70), (76, 72), (73, 67)]), 'W')
        flat(cv, ell(73, 69, 5, 5), 'W')
    for s in (0, 1):
        f = (lambda m: m) if s == 0 else mirror
        flat(cv, f(ell(20, 53, 12, 6, -16)), 'W')
        flat(cv, f(ell(22, 47.5, 13, 7, -14)), 'W')
        flat(cv, f(ell(23.5, 41, 13, 10, -12)), 'W')
        flat(cv, f(ell(23, 40, 4.5, 4.5)), 'X')
    flat(cv, poly(sym_pts([(48, 35), (40, 35), (34, 38), (33, 42), (38, 44), (48, 45)])), 'C')


def head(cv):
    flat(cv, ell(48, 25, 12.5, 13.5), 't')
    hair = union(ell(48, 19.5, 14.5, 11), poly([(33.5, 20), (38.5, 20), (38.5, 33), (33.5, 33)]), poly([(62.5, 20), (57.5, 20), (57.5, 33), (62.5, 33)]))
    hair = sub(hair, poly(sym_pts([(48, 34), (38.5, 34), (38.5, 23), (41, 20), (48, 19)])))
    flat(cv, hair, '3')
    flat(cv, poly(sym_pts([(48, 49), (43, 47), (38, 44), (34.5, 39), (33.5, 33), (34, 28), (37, 29), (39, 31), (43, 32), (48, 31.5)])), '3')


def sword_shoulder(cv):
    # fist near shoulder, blade over shoulder behind head to top right
    b0 = (26, 38)
    tip = (90, 7)
    d = (tip[0] - b0[0], tip[1] - b0[1])
    L = math.hypot(*d)
    u = (d[0] / L, d[1] / L)
    p = (-u[1], u[0])
    hw = 7
    pts = [(b0[0] + p[0] * hw, b0[1] + p[1] * hw), (b0[0] - p[0] * hw, b0[1] - p[1] * hw),
           (tip[0] - p[0] * hw - u[0] * 0, tip[1] - p[1] * hw), (tip[0] + p[0] * hw - u[0] * 6, tip[1] + p[1] * hw - u[1] * 6)]
    return pts, u, p


def draw_sword_shoulder(cv):
    pts, u, p = sword_shoulder(cv)
    flat(cv, poly(pts), 'K')


def arm_L_raised(cv):
    flat(cv, poly([(9, 50), (21, 50), (20, 60), (10, 62)]), 'K')
    flat(cv, poly([(9, 58), (19, 57), (24, 44), (16, 42)]), 'W')


def grip_shoulder(cv):
    # grip down-left from guard (26,38) along -u
    _, u, p = sword_shoulder(cv)
    g0 = (26, 38)
    g1 = (g0[0] - u[0] * 16, g0[1] - u[1] * 16)
    flat(cv, poly([(g0[0] + p[0] * 2, g0[1] + p[1] * 2), (g0[0] - p[0] * 2, g0[1] - p[1] * 2), (g1[0] - p[0] * 2, g1[1] - p[1] * 2), (g1[0] + p[0] * 2, g1[1] + p[1] * 2)]), 'm')
    flat(cv, poly([(g0[0] + p[0] * 10, g0[1] + p[1] * 10), (g0[0] - p[0] * 10, g0[1] - p[1] * 10), (g0[0] - p[0] * 10 - u[0] * 3, g0[1] - p[1] * 10 - u[1] * 3), (g0[0] + p[0] * 10 - u[0] * 3, g0[1] + p[1] * 10 - u[1] * 3)]), 'K')
    flat(cv, ell(g1[0], g1[1], 3, 3), 'K')
    flat(cv, ell(19, 42, 5.5, 5), 'W')


def mock_A():
    cv = Canvas()
    body(cv, arms='R')
    draw_sword_shoulder(cv)
    head(cv)
    arm_L_raised(cv)
    grip_shoulder(cv)
    return cv


def mock_P_sword():
    cv = Canvas()
    body(cv, arms='')
    # arm L akimbo mirrored
    flat(cv, mirror(poly([(70, 48), (82, 46), (89, 58), (86, 66), (80, 62)])), 'K')
    flat(cv, mirror(poly([(80, 60), (88, 60), (84, 70), (76, 72), (73, 67)])), 'W')
    flat(cv, mirror(ell(73, 69, 5, 5)), 'W')
    head(cv)
    # planted sword on right: axis x=85
    flat(cv, poly([(78, 38), (92, 38), (92, 86), (88, 93), (85, 96), (82, 93), (78, 86)]), 'K')
    flat(cv, poly([(73, 34), (95, 34), (95, 39), (73, 39)]), 'K')
    flat(cv, poly([(83, 18), (87, 18), (87, 34), (83, 34)]), 'm')
    flat(cv, ell(85, 16, 3.5, 3), 'K')
    # arm: upper arm down from shoulder, forearm up to grip
    flat(cv, poly([(72, 50), (84, 50), (86, 60), (76, 62)]), 'K')
    flat(cv, poly([(76, 58), (86, 58), (88, 36), (80, 36)]), 'W')
    flat(cv, ell(85, 30, 5.5, 5), 'W')
    return cv


def mock_H_upright():
    cv = Canvas()
    body(cv, arms='')
    flat(cv, mirror(poly([(70, 48), (82, 46), (89, 58), (86, 66), (80, 62)])), 'K')
    flat(cv, mirror(poly([(80, 60), (88, 60), (84, 70), (76, 72), (73, 67)])), 'W')
    flat(cv, mirror(ell(73, 69, 5, 5)), 'W')
    head(cv)
    flat(cv, poly([(82.5, 20), (87.5, 20), (87.5, 95), (82.5, 95)]), 'm')
    flat(cv, poly([(66, 4), (95, 4), (95, 26), (66, 26)]), 'K')
    flat(cv, poly([(76, 55), (86, 55), (86, 36), (78, 38)]), 'W')
    flat(cv, poly([(72, 50), (84, 50), (86, 60), (76, 62)]), 'K')
    flat(cv, ell(85, 46, 5.5, 5), 'W')
    return cv


def mock_H_shoulder():
    cv = Canvas()
    body(cv, arms='R')
    _, u, p = sword_shoulder(cv)
    b0 = (26, 38)
    # haft
    a0 = (b0[0] - u[0] * 18, b0[1] - u[1] * 18)
    a1 = (b0[0] + u[0] * 50, b0[1] + u[1] * 50)
    flat(cv, poly([(a0[0] + p[0] * 2.5, a0[1] + p[1] * 2.5), (a0[0] - p[0] * 2.5, a0[1] - p[1] * 2.5), (a1[0] - p[0] * 2.5, a1[1] - p[1] * 2.5), (a1[0] + p[0] * 2.5, a1[1] + p[1] * 2.5)]), 'm')
    c = (b0[0] + u[0] * 56, b0[1] + u[1] * 56)
    ang = math.degrees(math.atan2(u[1], u[0]))
    flat(cv, rrect(c[0], c[1], 20, 32, ang, ch=2), 'K')
    head(cv)
    arm_L_raised(cv)
    flat(cv, ell(19, 42, 5.5, 5), 'W')
    return cv


if __name__ == '__main__':
    mocks = [mock_A(), mock_P_sword(), mock_H_shoulder(), mock_H_upright()]
    S = 3
    pad = 10
    out = blank(pad + (96 * S + pad) * len(mocks), 96 * S + 2 * pad, FL)
    for i, m in enumerate(mocks):
        paste(out, scale(m.rgba(), S), pad + i * (96 * S + pad), pad)
    write_png('mock_compositions.png', len(out[0]), len(out), out)
