"""Liam v2 glasses-push: frame definitions (poses, tails, fx) and composition."""
import math, os
from lib import *
import build
from build import tcapsule_mask, tcapsule_normal, shade_fn, JACKET, layer, ribbon
from anim import arm_pose, head_variant, star, compose, blk, load_layer

# ------------------------------------------------------------------ tails variants (anchored at the knot, shift with head)
TAILS = {
    'down':  ([(41, 12), (43, 16), (44, 21), (45, 26)],
              [(42, 10), (45.5, 13), (48.5, 17), (50.5, 21), (52.5, 25), (55.5, 27)]),
    'up':    ([(41, 12), (45, 12.5), (49, 13.5), (53, 13)],
              [(42, 10), (46, 9), (50, 9.5), (54, 8.5), (58, 6.5)]),
    'flick': ([(41, 12), (45, 11), (49, 11.5), (53, 10.5), (56, 9)],
              [(42, 10), (46, 8), (50, 7), (54, 7.5), (58, 6), (61, 4)]),
    'mid':   ([(41, 12), (44.5, 14.5), (48, 17), (51, 19)],
              [(42, 10), (46, 11), (50, 12.5), (54, 14), (57, 14), (60, 12.5)]),
    'hold':  ([(41, 12), (44, 15.5), (46.5, 19.5), (48.5, 23)],
              [(42, 10), (46, 12), (50, 14.5), (53.5, 17), (57, 18), (60, 17)]),
    'hold2': ([(41, 12), (44, 15.5), (46.5, 20), (48, 24)],
              [(42, 10), (46, 12.5), (50, 15), (53.5, 18), (57, 19.5), (60, 19)]),
}

def tails_layer(kind):
    L = layer()
    b, a_ = TAILS[kind]
    ribbon(L, b, r=1.7, ramp='Yy')
    ribbon(L, a_, r=1.8, ramp='yT')
    return L

# ------------------------------------------------------------------ hands
FIST_UP = [  # finger-up fist; fist body cols 2..11 rows 6..13, finger cols 8..11 rows 0..6
    ".........##..",
    "........#as#.",
    "........#ad#.",
    "........#sd#.",
    "........#sd#.",
    ".......#fsd#.",
    "....####ssf#.",
    "...#aasssdf#.",
    "..#asssdddf#.",
    "..#sfsfsff#..",
    "..#ssdsddf#..",
    "..#dddfff#...",
    "...#ffff#....",
    "....####.....",
]

def arm_push():
    L = arm_pose(delt=(11.5, 30.5, 5.2), up=(11, 31, 7, 25, 4.6, 3.5), fore=(7, 25, 17, 21, 3.4, 3.1), cuff=(0.4, 2.3))
    blk(L, 15, 11, FIST_UP)
    return L

def arm_windup():
    L = arm_pose(delt=(11.0, 31.5, 5.3), up=(10, 33, 6, 40, 4.8, 4.0), fore=(6, 40, 13.5, 36, 3.6, 3.2), cuff=(0.4, 2.3))
    blk(L, 10, 25, FIST_UP)
    return L

def smear_shape(L, pts, widths, ramp):
    """Tapered smear along a polyline with per-point radius; colour bands along its length (lead -> tail)."""
    n = len(pts)
    m = [[False] * W for _ in range(H)]
    tval = [[0.0] * W for _ in range(H)]
    total = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(n - 1))
    acc = 0.0
    for i in range(n - 1):
        (ax, ay), (bx, by) = pts[i], pts[i + 1]
        seg = math.hypot(bx - ax, by - ay)
        mm = tcapsule_mask(ax, ay, bx, by, widths[i], widths[i + 1])
        for y in range(H):
            for x in range(W):
                if mm[y][x] and not m[y][x]:
                    m[y][x] = True
                    t, qx, qy = build.seg_t(x + .5, y + .5, ax, ay, bx, by)
                    tval[y][x] = (acc + t * seg) / total
        acc += seg
    def f(x, y):
        k = min(len(ramp) - 1, int(tval[y][x] * len(ramp)))
        return ramp[k]
    paint_part(L, m, f)
    return m

def line(L, x0, y0, x1, y1, ch='#'):
    n = max(abs(x1 - x0), abs(y1 - y0))
    for i in range(n + 1):
        x = round(x0 + (x1 - x0) * i / n)
        y = round(y0 + (y1 - y0) * i / n)
        if 0 <= x < W and 0 <= y < H:
            L[y][x] = ch

def arm_smear_up():
    """Hand arriving fast: arm mid-swing, fist just below its final spot (motion arcs added in fx)."""
    L = arm_pose(delt=(11.4, 31.0, 5.2), up=(11, 32, 6, 28, 4.6, 3.6), fore=(6, 28, 15, 25, 3.4, 3.1), cuff=(0.4, 2.3))
    blk(L, 13, 15, FIST_UP)
    return L

FAR_FIST = [
    ".######.",
    "#aasssd#",
    "#assssd#",
    "#ssssdf#",
    "#fsfsdf#",
    "#dsdsff#",
    ".#dfff#.",
    "..####..",
]

def arm_smear_down():
    """Hand dropping: arm swinging back down beside the body, fist a little above its rest spot."""
    L = arm_pose(delt=(11.0, 31.5, 5.3), up=(10, 33, 5, 39, 4.7, 3.9), fore=(5, 39, 7, 45, 3.6, 3.3), cuff=(0.4, 2.3))
    blk(L, 3, 44, FAR_FIST)
    return L

def arc(L, pts, ch='#'):
    for i in range(len(pts) - 1):
        line(L, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], ch)

# ------------------------------------------------------------------ fx
def fx_layer(kind):
    L = layer()
    if kind == 'speed_up':
        # motion arcs sweeping up from the chest to the hand
        # short dashes trailing under the fist, plus one in open space beside the elbow
        line(L, 17, 30, 16, 33)
        line(L, 20, 30, 19, 34)
        line(L, 23, 30, 22, 33)
        arc(L, [(2, 36), (2, 32), (3, 28)])
    elif kind == 'flash':
        star(L, 33, 13, 8, diag=3)
        star(L, 21, 12, 3)
        for (x0, y0, x1, y1) in ((43, 5, 47, 1), (45, 13, 50, 13), (42, 20, 46, 24), (33, 3, 33, 0), (24, 4, 21, 1)):
            line(L, x0, y0, x1, y1)
    elif kind == 'shrink':
        star(L, 33, 13, 5, diag=1)
        star(L, 21, 12, 1)
    elif kind == 'twinkle':
        star(L, 34, 12, 2)
    elif kind == 'speed_down':
        arc(L, [(14, 24), (12, 29), (11, 34), (11, 38)])
        arc(L, [(9, 23), (6, 27), (3, 32), (2, 37)])
        arc(L, [(16, 31), (15, 35), (14, 39)])
    return L

# ------------------------------------------------------------------ frame table
FRAMES = [
    # name,      dur, head_dy, mouth,  lenses,  arm,          tails,   fx
    ('idle',     100, 0,  None,    None,    'base',       'base',  None),
    ('windup',   220, 1,  'smirk', 'dim',   'windup',     'down',  None),
    ('snap',      40, 0,  'smirk', 'dim',   'smear_up',   'up',    'speed_up'),
    ('flash',     80, -1, 'big',   'flash', 'push',       'flick', 'flash'),
    ('sparkle',   80, -1, 'big',   'flash', 'push',       'mid',   'shrink'),
    ('hold',     520, -1, 'big',   None,    'push',       'hold',  'twinkle'),
    ('hold2',    280, -1, 'big',   None,    'push',       'hold2', None),
    ('release',   50, 0,  None,    None,    'smear_down', 'mid',   'speed_down'),
    ('settle',   130, 1,  None,    None,    'base',       'down',  None),
]

def build_frames():
    B = {k: load_layer(k) for k in ('tails', 'legs', 'torso', 'far', 'near', 'head')}
    arms = {'base': B['far'], 'windup': arm_windup(), 'smear_up': arm_smear_up(), 'push': arm_push(),
            'smear_down': arm_smear_down()}
    frames = []
    for (name, dur, dy, mouth, lenses, arm, tails, fx) in FRAMES:
        head = shift(head_variant(B['head'], mouth=mouth, lenses=lenses), 0, dy)
        tl = shift(B['tails'] if tails == 'base' else tails_layer(tails), 0, dy)
        a = arms[arm]
        if arm == 'base':
            order = [tl, B['legs'], B['torso'], a, B['near'], head]
        else:
            order = [tl, B['legs'], B['torso'], B['near'], head, a]
        if fx:
            order.append(fx_layer(fx))
        frames.append((name, dur, compose(order)))
    return frames

def contact_sheet(frames, path, s=4, labels=True):
    n = len(frames)
    gap = 4
    Wt = n * 64 + (n + 1) * gap
    Ht = 64 + 2 * gap
    bg = (58, 64, 84, 255)
    img = [[bg] * Wt for _ in range(Ht)]
    for i, (name, dur, cv) in enumerate(frames):
        rgba = to_rgba(cv)
        ox = gap + i * (64 + gap)
        for y in range(64):
            for x in range(64):
                if rgba[y][x][3] == 255:
                    img[gap + y][ox + x] = rgba[y][x]
    w2, h2, big = scale(Wt, Ht, img, s)
    write_png(path, w2, h2, big)

if __name__ == '__main__':
    os.makedirs('out/anim', exist_ok=True)
    frames = build_frames()
    for i, (name, dur, cv) in enumerate(frames):
        open('out/anim/f%02d_%s.txt' % (i, name), 'w').write(to_text(cv))
    contact_sheet(frames[:5], 'out/anim/sheet_a.png', 4)
    contact_sheet(frames[4:], 'out/anim/sheet_b.png', 4)
    print('frames', len(frames))
