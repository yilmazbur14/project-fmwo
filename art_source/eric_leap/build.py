"""Assemble the draft strip, previews and GIFs."""
import os, sys
from frames import *
from gifio import write_gif

OUT = os.path.join(HERE, 'out')
BG = (120, 160, 120, 255)
ORDER = ['throw_windup_0', 'throw_windup_1', 'throw_release_0', 'throw_release_1', 'empty_wait_0', 'empty_wait_1',
         'leap_0', 'leap_1', 'leap_2', 'leap_3', 'slam_0', 'slam_1', 'slam_2', 'recover_0', 'recover_1']
ANIMS = [  # name, [(frame index in strip, ms)]
    ('throw_windup', [(0, 120), (1, 320)]),
    ('throw_release', [(2, 70), (3, 220)]),
    ('empty_wait', [(4, 260), (5, 260)]),
    ('leap', [(6, 200), (7, 80), (8, 160), (9, 140)]),
    ('slam', [(10, 90), (11, 70), (12, 380)]),
    ('recover', [(13, 180), (14, 160)]),
]


def build_grids():
    reg = dict(FRAMES)
    grids = []
    for n in ORDER:
        g = reg[n]()
        bad = {c for r in g for c in r if c != '.' and c not in PAL}
        assert not bad, (n, bad)
        grids.append(g)
    return grids


def rgba(g):
    return render(g)


def on_bg(px, s, bg=BG):
    return scale(px, s, bg)


def main():
    grids = build_grids()
    frames = [rgba(g) for g in grids]
    W = FS * len(frames)
    strip = [[(0, 0, 0, 0)] * W for _ in range(FS)]
    for i, f in enumerate(frames):
        for y in range(FS):
            strip[y][i * FS:(i + 1) * FS] = f[y]
    write_png(os.path.join(OUT, 'eric_sword_leap_draft.png'), W, FS, strip)
    # text archive of every frame grid
    os.makedirs(os.path.join(OUT, 'grids'), exist_ok=True)
    for i, (n, g) in enumerate(zip(ORDER, grids)):
        save_txt(os.path.join(OUT, 'grids', 'f%02d_%s.txt' % (i, n)), g, 0, 0, FS, FS)
    # gifs
    for name, seq in ANIMS:
        fr = [on_bg(frames[i], 3) for i, _ in seq]
        write_gif(os.path.join(OUT, 'gif_%s.gif' % name), fr, [max(2, round(ms / 10)) for _, ms in seq])
    # comparison strip at 3x: reference idle 21, earthquake 7-9, then the new frames
    refs = [R[21], R[7], R[8], R[9]]
    ref_px = []
    raw = ref_frames()
    for i in (21, 7, 8, 9):
        # composite semi-transparent reference pixels over the bg for a faithful look
        f = []
        for row in raw[i]:
            r2 = []
            for p in row:
                a = p[3] / 255.0
                r2.append(tuple(int(p[k] * a + BG[k] * (1 - a)) for k in range(3)) + (255,) if p[3] else (0, 0, 0, 0))
            f.append(r2)
        ref_px.append(f)
    s = 3
    allf = ref_px + frames
    gap = 4
    CW = len(allf) * FS * s + gap * s * (len(allf) - 1) + gap * s
    img = [[(40, 40, 40, 255)] * CW for _ in range(FS * s)]
    x = 0
    for k, f in enumerate(allf):
        sc = on_bg(f, s)
        for yy in range(FS * s):
            img[yy][x:x + FS * s] = sc[yy]
        x += FS * s + gap * s
        if k == len(ref_px) - 1:
            x += gap * s
    write_png(os.path.join(OUT, 'compare_3x.png'), CW, FS * s, img)
    print('ok', W, 'x', FS)


if __name__ == '__main__':
    main()
