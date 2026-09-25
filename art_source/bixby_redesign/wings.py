"""Tattered, bony wings (right wing; the left mirrors). Two poses: the top of the upstroke and the
bottom of the downstroke.

Bones are violet-rimmed charcoal with knuckles and bone-white hooks at the thumb and the leading
finger. The membrane is dark wine, torn into zig-zags along its trailing edges and holed, and the
tears smoulder: an ember rim inside the keyline, burning hotter (orange, then yellow) at the deepest
point of each tear.
"""
from pal import fill, poly
from shapes import capsule, edge, poly_line, recolor

POSES = {
    'up': dict(
        shoulder=(116, 80), elbow=(138, 47), wrist=(157, 11), thumb=(151, 4),
        tips=[(185, 5), (188, 31), (187, 62), (178, 94)],
        # the trailing edge after each tip, as zig-zag tears (the last run ends at the body)
        tears=[[(182, 11), (185, 14), (179, 17), (182, 21), (176, 23), (182, 26)],
               [(183, 38), (185, 43), (178, 45), (182, 50), (176, 53), (183, 57)],
               [(182, 70), (183, 76), (176, 76), (178, 83), (172, 85), (177, 90)],
               [(170, 96), (165, 92), (162, 99), (155, 96), (151, 103), (144, 100), (138, 107),
                (130, 106)]],
        holes=[[(166, 15), (170, 17), (168, 21), (164, 19)], [(176, 31), (180, 33), (177, 37)],
               [(170, 60), (174, 62), (171, 66)]],
        burn=[(176, 23), (176, 53), (172, 85), (162, 99), (151, 103)],
        knuckles=[(172, 8), (173, 22), (172, 37), (167, 52)]),
    # the downstroke: the wrist and its thumb hook swing out past the side head's ear, the fingers
    # rake down beside the legs
    'down': dict(
        shoulder=(116, 86), elbow=(150, 96), wrist=(183, 110), thumb=(188, 100),
        tips=[(188, 124), (184, 143), (170, 150), (148, 142)],
        tears=[[(185, 129), (187, 133), (182, 134), (184, 139)],
               [(179, 144), (180, 149), (175, 147)],
               [(165, 146), (162, 150), (157, 145), (153, 148)],
               [(144, 136), (140, 132), (136, 126), (131, 121), (128, 114)]],
        holes=[[(176, 122), (180, 124), (177, 128)], [(162, 130), (166, 132), (163, 136)]],
        burn=[(182, 134), (175, 147), (162, 150), (140, 132)],
        knuckles=[(186, 117), (184, 126), (177, 130), (166, 126)]),
}


def membrane(pose):
    P = POSES[pose]
    pts = [P['shoulder'], P['elbow'], P['wrist']]
    for tip, tear in zip(P['tips'], P['tears']):
        pts.append(tip)
        pts.extend(tear)
    m = poly(pts)
    for h in P['holes']:
        m -= poly(h)
    part = fill(m, 'B')
    # darker folds along each finger
    for tip in P['tips']:
        for q in poly_line([P['wrist'], tip]):
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    r = (q[0] + dx, q[1] + dy)
                    if r in part:
                        part[r] = 'A'
    # the upper panel, nearest the arm, catches a little light
    upper = poly([P['shoulder'], P['elbow'], P['wrist'], P['tips'][0]] + P['tears'][0] + [P['tips'][1]])
    recolor(part, upper, 'C', only='B')
    # smouldering edges: every membrane pixel touching the outside or a hole, except along the arm
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
    # the deepest point of each tear burns hot
    for (bx, by) in P['burn']:
        for (x, y) in list(rimset):
            d = abs(x - bx) + abs(y - by)
            if d <= 1:
                part[(x, y)] = 'P'
            elif d <= 3:
                part[(x, y)] = 'v'
    return part


def bones(pose):
    P = POSES[pose]
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
        if (kx, ky - 1) in b:
            b[(kx, ky - 1)] = 'f'
    wx, wy = P['wrist']
    knuckle = fill(capsule((wx - 2, wy), (wx + 2, wy), 2.6, 2.6), 'd')
    recolor(knuckle, edge(knuckle, 0, -1, 1), 'e')
    knuckle[(wx - 1, wy - 2)] = 'f'
    return b, knuckle


def claw(base_l, base_r, tip):
    c = fill(poly([base_l, base_r, tip]), 'x')
    recolor(c, edge(c, -1, 0, 1), 'w')
    recolor(c, edge(c, 1, 0, 1), 'y')
    return c


def claws(pose):
    P = POSES[pose]
    wx, wy = P['wrist']
    tx, ty = P['thumb']
    out = [claw((wx - 3, wy - 1), (wx + 1, wy - 2), (tx, ty))]
    # a hook off the leading finger's tip
    fx, fy = P['tips'][0]
    if pose == 'up':
        out.append(claw((fx - 4, fy + 1), (fx - 2, fy + 3), (fx + 2, fy - 1)))
    else:
        out.append(claw((fx - 2, fy - 3), (fx, fy - 4), (fx, fy + 3)))
    return out


def build(cv, pose, mirror_fn):
    parts = [membrane(pose)]
    b, kn = bones(pose)
    parts += [b, kn] + claws(pose)
    for p in parts:
        cv.stamp(mirror_fn(p))
    for p in parts:
        cv.stamp(p)
