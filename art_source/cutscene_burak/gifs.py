"""GIF previews + identity comparison from the final strip PNG.  python gifs.py [strip.png]"""
import sys, os
from pngio import read_png, write_png, scale as pscale
import gif

STRIP = sys.argv[1] if len(sys.argv) > 1 else 'out/burak_cutscene_1x.png'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'out/gif'
os.makedirs(OUT, exist_ok=True)
w, h, px = read_png(STRIP)
N = w // 64
FR = [[row[i * 64:(i + 1) * 64] for row in px] for i in range(N)]

BG_TOP = (70, 76, 96)
BG_GROUND = (46, 48, 60)
TICK = (96, 100, 120)

RANGES = {'walk_gloomy': (0, 7), 'stop': (8, 9), 'notice': (10, 12), 'read': (13, 14), 'resolve': (15, 18),
          'walk_purpose': (19, 24)}
TIMING = {  # ms per frame
    'walk_gloomy': [150] * 8,
    'stop': [160, 420],
    'notice': [300, 380, 650],
    'read': [800, 800],
    'resolve': [240, 360, 220, 900],
    'walk_purpose': [120] * 6,
}
SPEED = {'walk_gloomy': 3, 'walk_purpose': 4}  # sprite px advanced per frame


def canvas(cw, ch, ground_y, scroll=0):
    img = []
    for y in range(ch):
        if y <= ground_y:
            img.append([BG_TOP] * cw)
        else:
            img.append([BG_GROUND] * cw)
    for x in range(cw):
        if (x + scroll) % 8 == 0:
            for y in range(ground_y + 1, min(ch, ground_y + 3)):
                img[y][x] = TICK
    return img


def paste(img, fr, ox, oy):
    for y in range(64):
        for x in range(64):
            p = fr[y][x]
            if p[3]:
                X, Y = ox + x, oy + y
                if 0 <= X < len(img[0]) and 0 <= Y < len(img):
                    img[Y][X] = p[:3]


def up(img, s):
    _, _, big = pscale(len(img[0]), len(img), img, s)
    return big


def anim_gif(name, s=4, loops=1):
    a, b = RANGES[name]
    frames, delays = [], []
    for _ in range(loops):
        for k, i in enumerate(range(a, b + 1)):
            img = canvas(80, 72, 63 + 4)
            paste(img, FR[i], 8, 4)
            frames.append(up(img, s))
            delays.append(TIMING[name][k])
    if name in ('stop', 'resolve', 'notice'):
        delays[-1] += 700
    gif.write_gif(os.path.join(OUT, 'burak_%s.gif' % name), frames, delays)


def sequence_gif(s=3):
    plan = [('walk_gloomy', 2), ('stop', 1), ('notice', 1), ('read', 2), ('resolve', 1), ('walk_purpose', 3)]
    steps = []  # (frame index, delay, dx before drawing)
    for name, loops in plan:
        a, b = RANGES[name]
        for _ in range(loops):
            for k, i in enumerate(range(a, b + 1)):
                dx = SPEED.get(name, 0)
                if name == 'stop':
                    dx = 3 if k == 0 else 0
                if name == 'walk_purpose' and not steps[-1][0] in range(19, 25):
                    dx = 4
                steps.append((i, TIMING[name][k], dx))
    xs, x = [], 0
    for idx, (i, d, dx) in enumerate(steps):
        if idx > 0:
            x += dx
        xs.append(x)
    cw = 64 + xs[-1] + 24
    frames, delays = [], []
    for (i, d, dx), x in zip(steps, xs):
        img = canvas(cw, 72, 63 + 4)
        paste(img, FR[i], 8 + x, 4)
        frames.append(up(img, s))
        delays.append(d)
    delays[-1] += 1200
    gif.write_gif(os.path.join(OUT, 'burak_full_sequence.gif'), frames, delays)
    return len(steps), cw


def identity_strip(s=3):
    _, _, ref = read_png('C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/MainPlayer/Sprite-0004-sheet.png')
    _, _, side = read_png('C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/MainPlayer/MainC Side Idle (A).png')
    pad = 6
    cw = 32 + pad + 32 + pad * 2 + N * 64
    img = [[(88, 94, 112)] * cw for _ in range(64)]
    for y in range(32):
        for x in range(32):
            p = ref[y][x]
            if p[3]:
                img[32 + y][x] = p[:3]
            q = side[y][x]
            if q[3]:
                img[32 + y][32 + pad + x] = q[:3]
    ox = 32 + pad + 32 + pad * 2
    for i in range(N):
        for y in range(64):
            for x in range(64):
                p = FR[i][y][x]
                if p[3]:
                    img[y][ox + i * 64 + x] = p[:3]
        for y in range(64):
            img[y][ox + i * 64] = tuple(max(0, c - 18) for c in img[y][ox + i * 64])
    big = up([[p + (255,) for p in row] for row in img], s)
    write_png(os.path.join(OUT, 'burak_identity_3x.png'), cw * s, 64 * s, big)


if __name__ == '__main__':
    for name in RANGES:
        anim_gif(name, loops=2 if name in ('walk_gloomy', 'walk_purpose', 'read') else 1)
    n, cw = sequence_gif()
    identity_strip()
    print('sequence steps', n, 'canvas', cw)
    for f in sorted(os.listdir(OUT)):
        print(f, os.path.getsize(os.path.join(OUT, f)))
