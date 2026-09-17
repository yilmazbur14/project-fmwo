"""Chase (run) cycle: 4 frames. Contact frames: head nods forward+down (squash), back foot kicks up.
Pass frames: whole figure airborne 1px (stretch), shoes tucked."""
from figures import *

#          x: -4 -3 -2 -1  0  1  2  3  4  5  6  7
C0 = """
............
....####....
.KKK####K...
KsSK#h##KKK.
.KKnnKKNffFK
...KK..KKKK.
............
"""
C1 = """
............
....####....
..KK####KK..
.KhK####KhK.
..KfFKssSK..
..KKKKKKKK..
............
"""
C2 = """
............
....####....
.KKK####KK..
KfFK####KhK.
.KKNNKKnssSK
...KK..KKKK.
............
"""
C3 = """
............
..K.####.K..
.KhK####KhK.
..KK####KK..
..KsSKffFK..
..KKKKKKKK..
............
"""
POSES = [C0, C1, C2, C3]
OFFS = [((2, 1), (0, 0)), ((1, 0), (0, -1)), ((2, 1), (0, 0)), ((1, 0), (0, -1))]

DL = hx('fff6e4')
DM = hx('e2d6b8')
DD = hx('b3a585')
SPD = hx('ffffff')
SPD2 = hx('d8e4f0')
DUST = (DL, DM, DD, SPD, SPD2)


def puff(cx, cy, size):
    if size == 3:
        shape = [".mm.", "mLLm", "dmmd", ".dd."]
    elif size == 2:
        shape = [".m.", "mLm", ".d."]
    else:
        shape = ["m"]
    pts = []
    h = len(shape)
    w = len(shape[0])
    for yy, row in enumerate(shape):
        for xx, ch in enumerate(row):
            if ch == '.':
                continue
            pts.append((cx - w // 2 + xx, cy - h + 1 + yy, {'L': DL, 'm': DM, 'd': DD}[ch]))
    return pts


def streak(x0, y, n, fade=1):
    return [(x0 + k, y, SPD if k >= fade else SPD2) for k in range(n)]


def dust(i):
    if i in (0, 2):
        return puff(5, 20, 3) + puff(2, 20, 1) + streak(1, 12 + (i // 2), 3)
    return puff(3, 19, 2) + puff(1, 20, 1) + streak(0, 10 + (i // 2), 4) + streak(2, 14 - (i // 2), 2)


def chase_frames(fig, with_dust=True):
    out = []
    for i, (pose, (ho, bo)) in enumerate(zip(POSES, OFFS)):
        f = fig.frame(pose, head_off=ho, body_off=bo)
        close_outline(f)
        if with_dust:
            for (x, y, c) in dust(i):
                if 0 <= x < 24 and 0 <= y < 24 and f[y][x][3] == 0:
                    f[y][x] = c
        out.append(f)
    return out


if __name__ == '__main__':
    rows = []
    allfr = []
    for fig in FIGURES:
        fr = chase_frames(fig)
        allfr.append(fr)
        for i, f in enumerate(fr):
            lint_outline(f, '%s c%d' % (fig.name, i), allow=DUST)
        rows.append(hstack([zoom(f, 8, ARENA_GREEN, True) for f in fr], gap=8))
    save(vstack(rows, gap=8), WIP + 'chase_sheet.png')
    arena_check([fr[1] for fr in allfr] + [fr[0] for fr in allfr], 'chase_arena', 2)
    print('ok')
