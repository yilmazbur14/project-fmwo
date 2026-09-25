"""Posable wings for the animation rig. The same construction as wings.py (which is fixed to its two
approved poses), driven by a pose dict, with extra poses for the flight set and a shift/scale so a
pose can be reused higher, lower or folded in.

A pose dict has: shoulder, elbow, wrist, thumb, tips (4, leading to trailing), tears (4 runs of
zig-zag points after each tip; the last run ends at the body), holes, burn (hot points on the torn
edge), knuckles, and claw ('up' hooks the leading finger's tip outward, 'down' hooks it downward).
"""
import copy

from pal import fill, poly
from shapes import capsule, edge, poly_line, recolor
import wings as W

UP = dict(copy.deepcopy(W.POSES['up']), claw='up')
DOWN = dict(copy.deepcopy(W.POSES['down']), claw='down')

# The in-betweens of the hover flap: arm level with the shoulder, fingers fanned out and down.
MID = dict(
    shoulder=(116, 82), elbow=(144, 58), wrist=(170, 44), thumb=(168, 34),
    tips=[(186, 40), (187, 72), (180, 100), (160, 106)],
    tears=[[(182, 46), (185, 51), (179, 54), (182, 60), (177, 63), (183, 67)],
           [(182, 79), (184, 85), (177, 86), (179, 92), (175, 95)],
           [(174, 101), (170, 97), (167, 104), (163, 101)],
           [(154, 104), (149, 100), (145, 107), (138, 104), (131, 106)]],
    holes=[[(174, 58), (178, 60), (175, 64)], [(166, 84), (170, 86), (167, 90)]],
    burn=[(177, 63), (175, 95), (167, 104), (145, 107)],
    knuckles=[(178, 42), (179, 58), (175, 72), (165, 75)],
    claw='up')

# The upstroke in-between: rising again with the membrane trailing, fingers drawn in.
MID_UP = dict(
    shoulder=(116, 82), elbow=(140, 56), wrist=(164, 36), thumb=(160, 27),
    tips=[(186, 42), (186, 66), (175, 90), (156, 102)],
    tears=[[(182, 48), (185, 53), (179, 55), (182, 60), (177, 62)],
           [(181, 71), (182, 77), (176, 78), (177, 84), (172, 86)],
           [(168, 92), (164, 90), (161, 97), (157, 95)],
           [(150, 101), (145, 98), (141, 104), (135, 102), (130, 106)]],
    holes=[[(171, 52), (175, 54), (172, 58)], [(160, 76), (164, 78), (161, 82)]],
    burn=[(177, 62), (172, 86), (161, 97), (141, 104)],
    knuckles=[(175, 39), (175, 51), (170, 63), (160, 69)],
    claw='up')

# Flared for a landing or a roar: spread high and wide, the fingers splayed.
FLARE = dict(
    shoulder=(116, 80), elbow=(140, 43), wrist=(161, 10), thumb=(155, 4),
    tips=[(185, 5), (187, 26), (187, 52), (183, 80)],
    tears=[[(181, 10), (184, 13), (179, 15), (182, 19), (177, 21)],
           [(183, 31), (185, 37), (179, 39), (182, 44), (177, 47)],
           [(183, 57), (184, 63), (178, 64), (180, 70), (175, 73)],
           [(177, 85), (172, 83), (168, 90), (160, 88), (154, 96), (146, 94), (138, 103),
            (130, 104)]],
    holes=[[(170, 14), (174, 16), (172, 20), (168, 18)], [(178, 44), (182, 46), (179, 50)]],
    burn=[(177, 21), (177, 47), (175, 73), (168, 90), (154, 96)],
    knuckles=[(174, 7), (175, 18), (175, 30), (172, 44)],
    claw='up')

# Draped flat on the ground beside him, spent (recover / hit): the arm lies out along the floor, the
# membrane spills over it and pools on the ground.
DRAPE = dict(
    shoulder=(118, 104), elbow=(146, 110), wrist=(172, 118), thumb=(178, 110),
    tips=[(187, 124), (187, 142), (180, 152), (160, 152)],
    tears=[[(184, 129), (186, 133), (182, 135)],
           [(184, 146), (182, 150), (180, 149)],
           [(175, 150), (172, 153), (167, 150), (163, 153)],
           [(152, 150), (146, 153), (140, 149), (133, 151), (126, 146), (122, 140)]],
    holes=[[(170, 130), (174, 132), (171, 136)], [(154, 138), (158, 140), (155, 144)]],
    burn=[(182, 135), (180, 149), (167, 150), (140, 149)],
    knuckles=[(181, 121), (180, 130), (176, 136), (166, 136)],
    claw='down')

# Folded in tight against the back (a crouch that is about to spring): little of it shows.
FOLD = dict(
    shoulder=(116, 84), elbow=(136, 62), wrist=(150, 34), thumb=(146, 26),
    tips=[(166, 30), (172, 50), (168, 74), (156, 96)],
    tears=[[(163, 35), (166, 40), (161, 42)],
           [(168, 55), (170, 61), (165, 63), (167, 69)],
           [(164, 78), (162, 84), (159, 88)],
           [(150, 96), (146, 100), (140, 97), (132, 102)]],
    holes=[[(158, 50), (161, 52), (159, 55)]],
    burn=[(161, 42), (165, 63), (159, 88), (146, 100)],
    knuckles=[(158, 32), (161, 42), (159, 54), (153, 64)],
    claw='up')


def moved(P, dx=0, dy=0, sx=1.0, sy=1.0, about=(116, 82)):
    """A pose moved and optionally squashed about a point (the shoulder by default)."""
    ax, ay = about

    def m(p):
        return (ax + (p[0] - ax) * sx + dx, ay + (p[1] - ay) * sy + dy)
    Q = dict(P)
    for k in ('shoulder', 'elbow', 'wrist', 'thumb'):
        Q[k] = m(P[k])
    for k in ('tips', 'burn', 'knuckles'):
        Q[k] = [m(p) for p in P[k]]
    for k in ('tears', 'holes'):
        Q[k] = [[m(p) for p in run] for run in P[k]]
    return Q


def lerp(A, Bp, t):
    """Blend two poses with the same point counts (for in-betweens)."""
    def mix(a, b):
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    Q = dict(A)
    for k in ('shoulder', 'elbow', 'wrist', 'thumb'):
        Q[k] = mix(A[k], Bp[k])
    for k in ('tips', 'burn', 'knuckles'):
        Q[k] = [mix(a, b) for a, b in zip(A[k], Bp[k])]
    for k in ('tears', 'holes'):
        Q[k] = [[mix(a, b) for a, b in zip(ra, rb)] for ra, rb in zip(A[k], Bp[k])]
    return Q


def _rp(p):
    return (int(round(p[0])), int(round(p[1])))


def membrane(P):
    pts = [P['shoulder'], P['elbow'], P['wrist']]
    for tip, tear in zip(P['tips'], P['tears']):
        pts.append(tip)
        pts.extend(tear)
    m = poly(pts)
    for h in P['holes']:
        m -= poly(h)
    part = fill(m, 'B')
    for tip in P['tips']:
        for q in poly_line([P['wrist'], tip]):
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    r = (q[0] + dx, q[1] + dy)
                    if r in part:
                        part[r] = 'A'
    upper = poly([P['shoulder'], P['elbow'], P['wrist'], P['tips'][0]] + P['tears'][0] + [P['tips'][1]])
    recolor(part, upper, 'C', only='B')
    arm_side = set()
    for q in poly_line([P['shoulder'], P['elbow'], P['wrist'], P['tips'][0]]):
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                arm_side.add((q[0] + dx, q[1] + dy))
    body = set(part)
    rimset = set()
    for (x, y) in body:
        if (x, y) in arm_side:
            continue
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in body:
                rimset.add((x, y))
                break
    for p in rimset:
        part[p] = 'u'
    for (bx, by) in P['burn']:
        for (x, y) in list(rimset):
            d = abs(x - bx) + abs(y - by)
            if d <= 1:
                part[(x, y)] = 'P'
            elif d <= 3:
                part[(x, y)] = 'v'
    return part


def bones(P):
    arm = capsule(P['shoulder'], P['elbow'], 3.4, 2.8) | capsule(P['elbow'], P['wrist'], 2.8, 2.2)
    fingers = set()
    for tip in P['tips']:
        fingers |= capsule(P['wrist'], tip, 1.5, 0.6)
    for (kx, ky) in P['knuckles']:
        fingers |= capsule((kx, ky), (kx, ky), 1.8, 1.8)
    b = fill(arm | fingers, 'c')
    recolor(b, edge(b, 0, -1, 1), 'd')
    recolor(b, edge(b, -1, 0, 1), 'e')
    recolor(b, edge(b, 0, 1, 1), 'b')
    for (kx, ky) in P['knuckles']:
        q = _rp((kx, ky - 1))
        if q in b:
            b[q] = 'f'
    wx, wy = P['wrist']
    knuckle = fill(capsule((wx - 2, wy), (wx + 2, wy), 2.6, 2.6), 'd')
    recolor(knuckle, edge(knuckle, 0, -1, 1), 'e')
    knuckle[_rp((wx - 1, wy - 2))] = 'f'
    return b, knuckle


def claws(P):
    wx, wy = P['wrist']
    tx, ty = P['thumb']
    out = [W.claw((wx - 3, wy - 1), (wx + 1, wy - 2), (tx, ty))]
    fx, fy = P['tips'][0]
    if P.get('claw', 'up') == 'up':
        out.append(W.claw((fx - 4, fy + 1), (fx - 2, fy + 3), (fx + 2, fy - 1)))
    else:
        out.append(W.claw((fx - 2, fy - 3), (fx, fy - 4), (fx, fy + 3)))
    return out


def parts(P):
    b, kn = bones(P)
    return [membrane(P), b, kn] + claws(P)


def build(cv, P, mirror_fn, P_left=None):
    """Stamp both wings: the right from P, the left mirrored from P_left (or P). The left goes first,
    as in wings.build, so the right one wins where they meet."""
    left = parts(P_left if P_left is not None else P)
    right = parts(P)
    for p in left:
        cv.stamp(mirror_fn(p))
    for p in right:
        cv.stamp(p)
