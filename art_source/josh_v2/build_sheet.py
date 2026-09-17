"""Assemble Josh's 13-frame sheet + previews.  usage: python build_sheet.py [frame indices to preview at 8x]"""
import sys, importlib
from jlib import *
from pngio import write_png, scale, checker_bg
from gif import write_gif

SHEET = os.path.join(HERE, 'sheet')
os.makedirs(SHEET, exist_ok=True)

# scene timings (Scenes/Bosses/CarterAndJoshScene.tscn, AnimationLibrary_josh)
ANIMS = [
    ('idle', [0, 1, 2], [350, 350, 350]),
    ('telegraph', [3, 4], [200, 200]),
    ('charge', [5, 6], [120, 120]),
    ('recover', [7, 8, 9], [250, 250, 250]),
    ('hit', [10], [200]),
    ('defeated', [11, 12], [350, 1400]),   # last frame holds in game; long delay in preview
]
TELEGRAPH_TINT = (1.7, 1.7, 1.35)


def frame_builders():
    import frames_all as F
    return F.FRAMES


def tint(rgba, t):
    out = []
    for row in rgba:
        r2 = []
        for p in row:
            if p[3] == 0:
                r2.append(p)
            else:
                r2.append((min(255, int(p[0] * t[0])), min(255, int(p[1] * t[1])), min(255, int(p[2] * t[2])), 255))
        out.append(r2)
    return out


def flat_bg(rgba, bg=(70, 66, 80, 255)):
    return [[p if p[3] == 255 else bg for p in row] for row in rgba]


def build_all(only=None):
    FR = frame_builders()
    frames = []
    for i, fn in enumerate(FR):
        if only is not None and i not in only:
            try:
                c = from_text(open(os.path.join(SHEET, 'f%02d.txt' % i)).read())
            except FileNotFoundError:
                c = fn()
        else:
            c = fn()
        open(os.path.join(SHEET, 'f%02d.txt' % i), 'w').write(to_text(c))
        frames.append(c)
    return frames


def main():
    only = set(int(a) for a in sys.argv[1:]) if len(sys.argv) > 1 else None
    frames = build_all(only)
    n = len(frames)
    rgba = [to_rgba(c) for c in frames]
    # strip
    strip = [sum((rgba[i][y] for i in range(n)), []) for y in range(H)]
    write_png(os.path.join(SHEET, 'josh_sheet.png'), W * n, H, strip)
    # 3x strip with frame separators on dark bg
    s3 = flat_bg(strip)
    _, _, big = scale(W * n, H, s3, 3)
    for y in range(H * 3):
        for i in range(1, n):
            big[y][i * W * 3] = (255, 0, 255, 255)
    write_png(os.path.join(SHEET, 'josh_sheet_3x.png'), W * n * 3, H * 3, big)
    # 8x previews of requested frames
    for i in (only if only is not None else range(n)):
        if i < n:
            preview(frames[i], os.path.join(SHEET, 'f%02d_8x.png' % i))
    # gifs at 3x on dark bg
    for name, idx, delays in ANIMS:
        if max(idx) >= n:
            continue
        gfr = []
        for i in idx:
            fr = rgba[i]
            if name == 'telegraph':
                fr = tint(fr, TELEGRAPH_TINT)
            _, _, b = scale(W, H, flat_bg(fr), 3)
            gfr.append(b)
        write_gif(os.path.join(SHEET, 'anim_%s.gif' % name), gfr, delays)
    # alpha check
    alphas = set(p[3] for row in strip for p in row)
    bboxes = []
    for i, c in enumerate(frames):
        xs = [x for y in range(H) for x in range(W) if c[y][x] != '.']
        ys = [y for y in range(H) for x in range(W) if c[y][x] != '.']
        bboxes.append((i, min(xs), max(xs), min(ys), max(ys)))
    print('frames', n, 'alphas', sorted(alphas))
    for b in bboxes:
        print('  f%02d bbox x %d-%d y %d-%d' % b)


if __name__ == '__main__':
    main()
