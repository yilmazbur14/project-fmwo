"""Eric sword-throw / leap / slam draft frames. Each builder returns a 128x128 char grid."""
import os
from sprites import *

SEG = os.path.join(HERE, 'seg')


def overlay(g, name):
    p = os.path.join(SEG, name + '.seg')
    if os.path.exists(p):
        load_seg(p, g)
    return g


def body4(g, up=(0, 0), mid=(0, 0)):
    """Arms-overhead body from earthquake frame 4 (legs static, belly and chest/head/arms offsettable)."""
    copy_region(g, R[4], 40, 104, 84, 124)
    copy_region(g, R[4], 40, 96, 84, 104, mid[0], mid[1])
    copy_region(g, R[4], 40, 66, 84, 96, up[0], up[1])


def throw_windup_0():
    g = blank()
    SW_UR60.put(g, 62, 68)
    body4(g)
    return overlay(g, 'windup0')


def throw_windup_1():
    g = blank()
    SW_UR60.transpose().fliph().put(g, 62, 72)
    body4(g, (2, 2), (1, 1))
    return overlay(g, 'windup1')


FRAMES = [
    ('throw_windup_0', throw_windup_0),
    ('throw_windup_1', throw_windup_1),
]

if __name__ == '__main__':
    import sys
    name = sys.argv[1]
    x0, y0, x1, y1 = [int(v) for v in sys.argv[2].split(',')]
    g = dict(FRAMES)[name]()
    save_txt('cur_%s.txt' % name, g, x0, y0, x1, y1)
    print(open('cur_%s.txt' % name).read())


def throw_windup_1():  # noqa: F811  (placement chosen from v_w1opts)
    g = blank()
    s = SW_UR60.transpose().fliph()
    s.put(g, 64, 76)
    body4(g, (2, 2), (1, 1))
    s.put(g, 64, 76, only=lambda X, Y: Y <= 74 and X >= 64)
    return overlay(g, 'windup1')


def throw_release_0():
    import fx
    g = blank()
    fx.arc_smear(g, 60.5, 64.5, -30, 112, 41, 36, 18, gaps=((26, 29, 20), (33, 35, 5)))
    s = SW_UR60.fliph()
    s.put(g, 57, 60)
    body4(g, (0, -2), (0, -1))
    return overlay(g, 'release0')


def throw_release_1():
    g = blank()
    copy_region(g, R[11], 40, 76, 90, 106, 0, 1)
    copy_region(g, R[11], 40, 106, 90, 127, 0, 0, keep=lambda x, y, c: not (57 <= x <= 63))
    copy_region(g, R[21], 52, 106, 70, 122)
    return overlay(g, 'release1')


FRAMES = [
    ('throw_windup_0', throw_windup_0),
    ('throw_windup_1', throw_windup_1),
    ('throw_release_0', throw_release_0),
    ('throw_release_1', throw_release_1),
]


def empty_wait_0():
    return overlay(blank(), 'wait0')


def empty_wait_1():
    g = overlay(blank(), 'wait0')
    # breathe: chest/head/arms up 1px, torso seam duplicated at row 97 (idle does the same kind of lift)
    src = [r[:] for r in g]
    for y in range(76, 113):
        for x in range(FS):
            arm = x <= 50 or x >= 70
            if y <= 96 or (arm and y <= 111):
                g[y][x] = src[y + 1][x] if not (arm and y == 111) else src[y + 1][x]
    return overlay(g, 'wait1')


def leap_0():
    return overlay(blank(), 'leap0')


def dust(g, cx, cy, flip=False):
    import fx
    s = -1 if flip else 1
    for dx, dy, r in [(0, 0, 3.6), (-5, 1.5, 2.8), (4, 2, 2.4), (-9, 2.5, 1.8)]:
        fx.disc(g, cx + s * dx, cy + dy, r, 'L', only_empty=True)
    for dx, dy, r in [(0, -0.6, 2.6), (-5, 1.0, 1.8), (4, 1.5, 1.4), (-9, 2.2, 1.0)]:
        fx.disc(g, cx + s * dx, cy + dy, r, 'w')


def leap_1():
    g = blank()
    copy_region(g, R[4], 40, 66, 84, 104, 0, -3)
    overlay(g, 'leap1_legs')
    copy_region(g, R[4], 50, 104, 72, 110, 0, -3, keep=lambda x, y, c: c in 'bBk' and y <= 107)
    dust(g, 45, 118)
    dust(g, 75, 118, flip=True)
    return overlay(g, 'leap1')


def leap_2():
    g = overlay(blank(), 'leap2')
    mirror_seg(g, 'leap2_larm')
    return overlay(g, 'leap2_fix')


def leap_3():
    return overlay(blank(), 'leap3')


FRAMES = [
    ('throw_windup_0', throw_windup_0),
    ('throw_windup_1', throw_windup_1),
    ('throw_release_0', throw_release_0),
    ('throw_release_1', throw_release_1),
    ('empty_wait_0', empty_wait_0),
    ('empty_wait_1', empty_wait_1),
    ('leap_0', leap_0),
    ('leap_1', leap_1),
    ('leap_2', leap_2),
    ('leap_3', leap_3),
]


PLANT_ANCHOR = (44, 79)   # grip centre of the planted sword in slam_0 (sword top-left = (37,73))
SINK = 22                 # how far slam_1/slam_2 drive the sword into the ground
GROUND_Y = 126            # row where the planted sword's tip meets the ground


def planted(g, dy=0, clip_ground=True):
    ax, ay = PLANT_ANCHOR
    SW_PLANT.put(g, ax, ay + dy, only=(lambda X, Y: Y <= GROUND_Y - 1 or (dy == 0)) if clip_ground else None)


def slam_0():
    g = blank()
    planted(g)
    return overlay(g, 'slam0')


def burst(g):
    import fx, math
    cx, cy = PLANT_ANCHOR[0] + 0.5, GROUND_Y - 1
    fx.disc(g, cx, cy, 9)
    for ang, ln, wd in [(15, 30, 3), (38, 26, 4), (62, 24, 4), (90, 30, 5), (118, 24, 4), (142, 26, 4), (165, 30, 3)]:
        a = math.radians(ang)
        for t in range(0, ln):
            w = wd * (1 - t / ln)
            px, py = cx + math.cos(a) * t, cy - math.sin(a) * t * 0.8
            fx.disc(g, px, py, max(w, 0.6))
    for y in range(GROUND_Y - 2, GROUND_Y + 1):
        for x in range(4, 90):
            d = abs(x + 0.5 - cx)
            if d < 44 - (GROUND_Y - y) * 8:
                g[y][x] = 'w'


def slam_1():
    g = blank()
    planted(g, SINK)
    overlay(g, 'slam1')
    burst(g)
    return overlay(g, 'slam1_fx')


def slam_2():
    g = blank()
    planted(g, SINK)
    overlay(g, 'slam1')
    return overlay(g, 'slam2_fx')


def recover_0():
    g = blank()
    planted(g, -9, clip_ground=False)
    overlay(g, 'recover0')
    return overlay(g, 'recover0_fx')


def recover_1():
    import fx
    g = blank()
    fx.arc_smear(g, 44.5, 85.5, 22, 118, 47, 40, 26, gaps=((30, 33, 70),))
    copy_region(g, R[21], 0, 0, FS, FS)
    return overlay(g, 'recover1')


FRAMES += [
    ('slam_0', slam_0),
    ('slam_1', slam_1),
    ('slam_2', slam_2),
    ('recover_0', recover_0),
    ('recover_1', recover_1),
]


def throw_release_0():  # noqa: F811
    import fx
    g = blank()
    fx.arc_smear(g, 60.5, 67.5, 2, 121, 43, 41, 15, gaps=((31, 33, 60), (24, 26, 85)))
    s = SW_UR60.fliph()
    s.put(g, 56, 62)
    body4(g)
    return overlay(g, 'release0')


FRAMES[2] = ('throw_release_0', throw_release_0)


def mirror_seg(g, name, axis2=120):
    sub = load_seg(os.path.join(SEG, name + '.seg'))
    for y in range(FS):
        for x in range(FS):
            c = sub[y][x]
            if c != '.':
                if 0 <= x < FS:
                    g[y][x] = c
                X = axis2 - x
                if 0 <= X < FS:
                    g[y][X] = c


def throw_release_1():  # noqa: F811
    g = overlay(blank(), 'release1_body')
    mirror_seg(g, 'release1_larm')
    return overlay(g, 'release1')


FRAMES[3] = ('throw_release_1', throw_release_1)


def arm(g, pts, rs=(3.2, 2.6), fist_r=3.0, knuckles=True, glint=True):
    """pts = shoulder, elbow, wrist, fist-centre. Draws a rounded armoured arm with a gauntlet fist."""
    import limbs
    (sx, sy), (ex, ey), (wx, wy), (fx_, fy) = pts
    lines = []
    if knuckles:
        lines.append(((fx_ - 1.6, fy + 0.2), (fx_ + 1.6, fy + 0.2)))
    return limbs.limb(g, [(sx, sy, ex, ey, rs[0]), (ex, ey, wx, wy, rs[1]),
                          (fx_, fy, fx_, fy, fist_r, 'noglint')], glint=glint, lines=lines)


PLANT_ANCHOR = (44, 79)
SINK = 30


def slam_0():  # noqa: F811
    g = blank()
    planted(g)
    load_seg(os.path.join(SEG, 'crouch_torso.seg'), g)
    load_seg(os.path.join(SEG, 'crouch_legs.seg'), g)
    arm(g, [(49.5, 96.5), (47.5, 89.5), (45.5, 84), (44.5, 79.5)])
    arm(g, [(71.5, 96.5), (79.5, 94.5), (85.5, 90.5), (87.5, 88.5)])
    return overlay(g, 'slam0')


def slam_body_deep(g):
    load_seg(os.path.join(SEG, 'crouch_torso.seg'), g)
    # torso 2px deeper than slam_0 is approximated by shifting the torso block down 2
    tmp = blank()
    load_seg(os.path.join(SEG, 'crouch_torso.seg'), tmp)
    for y in range(FS - 1, -1, -1):
        for x in range(FS):
            g[y][x] = tmp[y - 2][x] if y >= 2 and tmp[y - 2][x] != '.' else ('.' if y < 108 else g[y][x])
    load_seg(os.path.join(SEG, 'crouch_legs.seg'), g)


def slam_1():  # noqa: F811
    g = blank()
    planted(g, SINK)
    slam_body_deep(g)
    arm(g, [(49.5, 98.5), (46.5, 104.5), (45, 108), (44.5, 110.5)])
    arm(g, [(71.5, 98.5), (62.5, 104.5), (50, 105.5), (44.5, 105.5)])
    burst(g)
    return overlay(g, 'slam1_fx')


def slam_2():  # noqa: F811
    g = blank()
    planted(g, SINK)
    slam_body_deep(g)
    arm(g, [(49.5, 98.5), (46.5, 104.5), (45, 108), (44.5, 110.5)])
    arm(g, [(71.5, 98.5), (62.5, 104.5), (50, 105.5), (44.5, 105.5)])
    return overlay(g, 'slam2_fx')


FRAMES[10] = ('slam_0', slam_0)
FRAMES[11] = ('slam_1', slam_1)
FRAMES[12] = ('slam_2', slam_2)


PLANT_ANCHOR = (41, 79)
SINK = 26


def lean_torso(g, shear):
    """Stamp crouch_torso with a per-row horizontal shift: shear = list of (ymax, dx)."""
    tmp = blank()
    load_seg(os.path.join(SEG, 'crouch_torso.seg'), tmp)
    for y in range(FS):
        dx = 0
        for ymax, d in shear:
            if y <= ymax:
                dx = d
                break
        for x in range(FS):
            c = tmp[y][x]
            if c != '.' and 0 <= x + dx < FS:
                g[y][x + dx] = c


LEAN = [(92, -5), (99, -4), (103, -3), (105, -2), (107, -1)]


def slam_0():  # noqa: F811
    g = blank()
    planted(g)
    load_seg(os.path.join(SEG, 'crouch_torso.seg'), g)
    load_seg(os.path.join(SEG, 'crouch_legs.seg'), g)
    arm(g, [(49.5, 96.5), (46.5, 89.5), (43, 84), (41.5, 79.5)])
    arm(g, [(71.5, 96.5), (79.5, 94.5), (85.5, 90.5), (87.5, 88.5)])
    return overlay(g, 'slam0')


def slam_pose(g):
    planted(g, SINK)
    load_seg(os.path.join(SEG, 'crouch_legs.seg'), g)
    lean_torso(g, LEAN)
    arm(g, [(45.5, 97.5), (38.5, 102.5), (39.5, 106), (41.5, 106.5)])
    arm(g, [(67.5, 97.5), (56.5, 103.5), (46, 101.5), (41.5, 101.5)])


def slam_1():  # noqa: F811
    g = blank()
    slam_pose(g)
    burst(g)
    return overlay(g, 'slam1_fx')


def slam_2():  # noqa: F811
    g = blank()
    slam_pose(g)
    return overlay(g, 'slam2_fx')


FRAMES[10] = ('slam_0', slam_0)
FRAMES[11] = ('slam_1', slam_1)
FRAMES[12] = ('slam_2', slam_2)


SINK = 28


def slam_pose(g):  # noqa: F811
    planted(g, SINK)
    load_seg(os.path.join(SEG, 'crouch_legs.seg'), g)
    lean_torso(g, LEAN)
    arm(g, [(66.5, 97.5), (76.5, 101.5), (80.5, 96), (80.5, 92.5)])
    arm(g, [(45.5, 97.5), (42.5, 102.5), (41.5, 104.5), (41.5, 106.5)])


def stamp_seg(g, name, dx=0, dy=0, shear=None):
    tmp = load_seg(os.path.join(SEG, name + '.seg'))
    for y in range(FS):
        sx = dx
        if shear:
            for ymax, d in shear:
                if y <= ymax:
                    sx = dx + d
                    break
        for x in range(FS):
            c = tmp[y][x]
            if c != '.' and 0 <= x + sx < FS and 0 <= y + dy < FS:
                g[y + dy][x + sx] = c


def recover_0():  # noqa: F811
    g = blank()
    planted(g, -9, clip_ground=False)
    stamp_seg(g, 'stand_legs')
    stamp_seg(g, 'stand_torso', shear=[(88, 2), (95, 1), (127, 0)])
    arm(g, [(70.5, 91.5), (78.5, 97.5), (81, 91), (80.5, 87.5)])
    arm(g, [(51.5, 91.5), (47.5, 83), (43.5, 76), (41.5, 70.5)])
    return overlay(g, 'recover0_fx')


FRAMES[13] = ('recover_0', recover_0)


def leg(g, hip, knee, ankle, toe, r=(3.4, 2.9, 1.9)):
    import limbs
    return limbs.limb(g, [(hip[0], hip[1], knee[0], knee[1], r[0]), (knee[0], knee[1], ankle[0], ankle[1], r[1]),
                          (ankle[0], ankle[1], toe[0], toe[1], r[2], 'noglint')],
                      lines=[((knee[0] - 2.5, knee[1]), (knee[0] + 2.5, knee[1]))])


def only_empty(fn):
    """Run a drawing fn on a scratch grid and copy only onto transparent cells of g."""
    def wrap(g, *a, **k):
        tmp = blank()
        fn(tmp, *a, **k)
        for y in range(FS):
            for x in range(FS):
                if tmp[y][x] != '.' and g[y][x] == '.':
                    g[y][x] = tmp[y][x]
    return wrap


def open_hand(g, pts, rs=(3.2, 2.6), r=2.8):
    return arm(g, pts, rs, fist_r=r, knuckles=False)


def throw_release_1():  # noqa: F811
    import fx
    g = blank()
    fx.arc_smear(g, 60.5, 92.5, -40, 150, 30, 29, 27, gaps=((29.5, 31, 40),))
    stamp_seg(g, 'stand_torso', dy=2, shear=[(90, 2), (127, 0)])
    stamp_seg(g, 'stand_legs')
    arm(g, [(71.5, 95.5), (77.5, 101.5), (77, 105), (74.5, 107.5)], knuckles=False)
    arm(g, [(52.5, 95.5), (57.5, 102.5), (66, 105.5), (70.5, 106.5)], knuckles=False)
    return overlay(g, 'release1')


def leap_1():  # noqa: F811
    g = blank()
    leg(g, (55.5, 104), (55.5, 111.5), (56, 117.5), (56.5, 120.5))
    leg(g, (64.5, 104), (64.5, 111.5), (64, 117.5), (63.5, 120.5))
    copy_region(g, R[4], 40, 66, 84, 110, 0, -3)
    dust(g, 45, 119)
    dust(g, 75, 119, flip=True)
    return overlay(g, 'leap1')


def leap_2():  # noqa: F811
    g = blank()
    load_seg(os.path.join(SEG, 'leap2.seg'), g)
    for y in range(89, 103):          # replace the hand-drawn chest with the clean standing torso
        for x in range(FS):
            g[y][x] = '.'
    stamp_seg(g, 'stand_torso', shear=None)
    for y in range(103, 115):
        pass
    load_seg(os.path.join(SEG, 'leap2_legs.seg'), g)
    open_hand(g, [(50.5, 91.5), (44.5, 85.5), (40.5, 80), (39, 77)])
    open_hand(g, [(69.5, 91.5), (75.5, 85.5), (79.5, 80), (81, 77)])
    return overlay(g, 'leap2_fix')


def leap_3():  # noqa: F811
    g = blank()
    leg(g, (55.5, 107), (55.5, 114.5), (56, 120.5), (56.5, 123.5))
    leg(g, (64.5, 107), (64.5, 114), (65, 119.5), (65.5, 122.5))
    stamp_seg(g, 'stand_torso')
    stamp_seg(g, 'stand_legs_belt')
    pass  # head kept straight (glaring)
    open_hand(g, [(50.5, 92.5), (44.5, 99), (38.5, 104), (35.5, 106.5)])
    open_hand(g, [(69.5, 92.5), (62.5, 101), (52.5, 106), (48.5, 108.5)])
    return overlay(g, 'leap3_fix')


for i, (n, f) in enumerate(FRAMES):
    if n in ('throw_release_1', 'leap_1', 'leap_2', 'leap_3', 'recover_1', 'slam_1', 'slam_2'):
        FRAMES[i] = (n, globals()[n])


def _put(g, x, y, c='w', empty_only=False):
    if 0 <= x < FS and 0 <= y < FS and (not empty_only or g[y][x] == '.'):
        g[y][x] = c


def _thick_line(g, p0, p1, w0, w1, c='w', empty_only=False):
    import math
    n = int(max(abs(p1[0] - p0[0]), abs(p1[1] - p0[1])) * 2) + 1
    for i in range(n + 1):
        t = i / n
        x = p0[0] + (p1[0] - p0[0]) * t
        y = p0[1] + (p1[1] - p0[1]) * t
        r = w0 + (w1 - w0) * t
        for yy in range(int(y - r - 1), int(y + r + 2)):
            for xx in range(int(x - r - 1), int(x + r + 2)):
                if (xx + 0.5 - x) ** 2 + (yy + 0.5 - y) ** 2 <= r * r:
                    _put(g, xx, yy, c, empty_only)


def burst(g):  # noqa: F811
    """Big white ground impact at the sword base: flash column, dome, ground spray, rays and chunks."""
    import fx
    cx = PLANT_ANCHOR[0] + 0.5
    gy = GROUND_Y
    # dome
    for y in range(gy - 9, gy + 1):
        for x in range(FS):
            if ((x + 0.5 - cx) / 21.0) ** 2 + ((y + 0.5 - gy) / 9.0) ** 2 <= 1.0:
                _put(g, x, y)
    # flash column hugging the blade, ragged
    jag = [0, 1, 1, 0, -1, 0, 1, 2, 1, 0, 0, 1, 0, -1, 0, 1, 1, 0, 1, 2, 1, 1, 0, 1, 2, 2, 1, 2, 3, 2, 3, 3, 4]
    for i, y in enumerate(range(gy - 25, gy - 8)):
        hw = 3 + (y - (gy - 25)) * 0.34 + jag[i % len(jag)] * 0.6
        for x in range(int(cx - hw), int(cx + hw) + 1):
            _put(g, x, y)
    for x in range(int(cx) - 1, int(cx) + 2):
        for y in range(gy - 30, gy - 25):
            if abs(x + 0.5 - cx) <= (y - (gy - 31)) * 0.45:
                _put(g, x, y)
    # ground spray wedges
    _thick_line(g, (cx - 18, gy - 2), (cx - 36, gy - 1), 2.6, 0.6)
    _thick_line(g, (cx + 18, gy - 2), (cx + 40, gy - 1), 2.6, 0.6)
    # rays (behind Eric: only on empty pixels)
    for (ex, ey, w0) in [(cx - 26, gy - 30, 2.0), (cx - 34, gy - 16, 1.6), (cx + 22, gy - 34, 2.0), (cx + 36, gy - 20, 1.6)]:
        _thick_line(g, (cx + (ex - cx) * 0.35, gy - 8 + (ey - gy) * 0.2), (ex, ey), w0, 0.5, empty_only=True)
    # chunks
    for (x, y, s) in [(-24, -38, 2), (-31, -26, 2), (-15, -44, 1), (27, -40, 2), (33, -30, 1), (-36, -10, 1), (43, -12, 2)]:
        for yy in range(s):
            for xx in range(s):
                _put(g, int(cx + x) + xx, gy + y + yy, empty_only=True)


def slam_2_fx(g):
    """Impact hold: shock arcs along the ground (like earthquake frame 9) plus flying flecks (frame 10)."""
    import math
    cx, cy = PLANT_ANCHOR[0] + 0.5, GROUND_Y - 1.5
    for rx, ry, spans, w in [(30, 7, [(160, 200), (-20, 20)], 1.1), (44, 10, [(165, 195), (-15, 12)], 1.0)]:
        for a0, a1 in spans:
            steps = 60
            for i in range(steps + 1):
                a = math.radians(a0 + (a1 - a0) * i / steps)
                x = cx + rx * math.cos(a)
                y = cy - ry * math.sin(a) * -1 if False else cy + ry * math.sin(a) * 0.0 - abs(math.sin(a)) * ry
                ww = w * (1 - abs(i / steps - 0.5))
                for yy in range(int(y - 1), int(y + 2)):
                    for xx in range(int(x - 1), int(x + 2)):
                        if (xx + 0.5 - x) ** 2 + (yy + 0.5 - y) ** 2 <= (0.6 + ww) ** 2:
                            _put(g, xx, yy, empty_only=True)
    # small residual flash at the base
    for y in range(GROUND_Y - 4, GROUND_Y + 1):
        for x in range(FS):
            if ((x + 0.5 - cx) / 9.0) ** 2 + ((y + 0.5 - GROUND_Y) / 4.0) ** 2 <= 1.0:
                _put(g, x, y)
    for (x, y, s) in [(-20, -52, 2), (-33, -36, 2), (-12, -60, 1), (24, -58, 2), (38, -40, 2), (-44, -22, 1), (50, -24, 1), (6, -66, 1)]:
        for yy in range(s):
            for xx in range(s):
                _put(g, int(cx + x) + xx, GROUND_Y + y + yy, empty_only=True)


def slam_1():  # noqa: F811
    g = blank()
    slam_pose(g)
    burst(g)
    return overlay(g, 'slam1_fx')


def slam_2():  # noqa: F811
    g = blank()
    slam_pose(g)
    slam_2_fx(g)
    return overlay(g, 'slam2_fx')


for i, (n, f) in enumerate(FRAMES):
    if n in ('slam_1', 'slam_2'):
        FRAMES[i] = (n, globals()[n])


def ring_arc(g, cx, cy, rx, ry, a0, a1, w):
    import math
    steps = 120
    for i in range(steps + 1):
        t = i / steps
        a = math.radians(a0 + (a1 - a0) * t)
        x = cx + rx * math.cos(a)
        y = cy - ry * math.sin(a)
        r = 0.45 + w * math.sin(math.pi * t)
        for yy in range(int(y - 2), int(y + 3)):
            for xx in range(int(x - 2), int(x + 3)):
                if (xx + 0.5 - x) ** 2 + (yy + 0.5 - y) ** 2 <= r * r:
                    _put(g, xx, yy, empty_only=True)


def slam_2_fx(g):  # noqa: F811
    cx, gy = PLANT_ANCHOR[0] + 0.5, GROUND_Y
    ring_arc(g, cx, gy - 3, 28, 8, 140, 205, 1.0)
    ring_arc(g, cx, gy - 3, 28, 8, -25, 40, 1.0)
    ring_arc(g, cx, gy - 4, 36, 10, 150, 190, 0.7)
    ring_arc(g, cx, gy - 4, 36, 10, -12, 28, 0.7)
    for y in range(gy - 4, gy + 1):
        for x in range(FS):
            if ((x + 0.5 - cx) / 8.0) ** 2 + ((y + 0.5 - gy) / 4.0) ** 2 <= 1.0:
                _put(g, x, y)
    for (x, y, s) in [(-20, -52, 2), (-31, -38, 2), (-12, -62, 1), (-38, -20, 1), (26, -60, 2), (40, -44, 1), (6, -70, 1)]:
        for yy in range(s):
            for xx in range(s):
                _put(g, int(cx + x) + xx, gy + y + yy, empty_only=True)


def recover_1():  # noqa: F811
    import fx
    g = blank()
    fx.smear2(g, 50.5, 82.5, 16, 150, 45, 22, 42, r_out_tail=43, gaps=((31, 33, 0.35, 1.0), (37, 38, 0.55, 1.0)))
    copy_region(g, R[21], 0, 0, FS, FS)
    return overlay(g, 'recover1')


def throw_release_1():  # noqa: F811
    import fx
    g = blank()
    stamp_seg(g, 'stand_torso', dy=2, shear=[(90, 2), (127, 0)])
    stamp_seg(g, 'stand_legs')
    arm(g, [(71.5, 95.5), (77.5, 101.5), (77, 105), (74.5, 107.5)], knuckles=False)
    arm(g, [(52.5, 95.5), (57.5, 102.5), (66, 105.5), (70.5, 106.5)], knuckles=False)
    fx.smear2(g, 61.5, 93.5, -38, 115, 24, 13, 21, r_out_tail=22, gaps=((17.5, 18.5, 0.4, 1.0),), empty_only=True)
    return overlay(g, 'release1')


def recover_0():  # noqa: F811
    import fx
    g = blank()
    planted(g, -9, clip_ground=False)
    stamp_seg(g, 'stand_legs')
    stamp_seg(g, 'stand_torso', shear=[(88, 2), (95, 1), (127, 0)])
    arm(g, [(70.5, 91.5), (78.5, 97.5), (81, 91), (80.5, 87.5)])
    arm(g, [(51.5, 91.5), (47.5, 83), (43.5, 76), (41.5, 70.5)])
    # upward yank streaks beside the blade
    for x, y0, y1 in [(31, 94, 108), (29, 104, 112), (51, 98, 112), (53, 108, 116)]:
        for y in range(y0, y1):
            _put(g, x, y, empty_only=True)
    # clods / flecks shaken off the tip and a puff where it came out
    for (x, y, s) in [(36, 120, 2), (46, 118, 2), (33, 114, 1), (49, 122, 1), (39, 110, 1)]:
        for yy in range(s):
            for xx in range(s):
                _put(g, x + xx, y + yy, empty_only=True)
    fx.disc(g, 41.5, 124.0, 3.0, 'L', only_empty=True)
    fx.disc(g, 36.5, 124.8, 2.0, 'L', only_empty=True)
    fx.disc(g, 46.5, 124.8, 2.0, 'L', only_empty=True)
    fx.disc(g, 41.5, 123.4, 2.1, 'w')
    fx.disc(g, 36.5, 124.4, 1.3, 'w')
    fx.disc(g, 46.5, 124.4, 1.3, 'w')
    return overlay(g, 'recover0_fx')


for i, (n, f) in enumerate(FRAMES):
    if n in ('recover_0', 'recover_1', 'throw_release_1'):
        FRAMES[i] = (n, globals()[n])


def throw_release_0():  # noqa: F811
    import fx
    g = blank()
    fx.smear2(g, 57.5, 64.5, 123, 2, 41, 11, 39, r_out_tail=41, gaps=((28, 30, 0.45, 1.0), (21, 23, 0.25, 0.75)))
    SW_UR60.fliph().put(g, 56, 62)
    body4(g)
    return overlay(g, 'release0')


for i, (n, f) in enumerate(FRAMES):
    if n == 'throw_release_0':
        FRAMES[i] = (n, throw_release_0)


def leap_1():  # noqa: F811
    g = blank()
    leg(g, (55.5, 104), (55.5, 111.5), (56, 117.5), (56.5, 120.5))
    leg(g, (64.5, 104), (64.5, 111.5), (64, 117.5), (63.5, 120.5))
    copy_region(g, R[4], 40, 70, 84, 110, 0, -3)   # skip the earthquake sword hilt above the fists
    g[67][60] = g[68][60] = g[69][60] = 'k'
    dust(g, 45, 119)
    dust(g, 75, 119, flip=True)
    return overlay(g, 'leap1')


for i, (n, f) in enumerate(FRAMES):
    if n == 'leap_1':
        FRAMES[i] = (n, leap_1)
