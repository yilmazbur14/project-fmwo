"""Old Carter against new Carter, the player and Josh, all at true game scale.

The old size is re-rendered from the same rig at scale 1.0 rather than being
read off disk, so both figures come from identical code and the only difference
between them is the number in carter_scale.

    python preview_resize.py <scratch_dir>
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import lib
from pngio import read_png, write_png, scale, blank, paste, crop

A = r"C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters"
SCRATCH = sys.argv[1] if len(sys.argv) > 1 else '.'
BOSS, PLAYER = 3, 2
BG = (24, 21, 28, 255)
FLOOR = (92, 70, 116, 255)
RULE = (58, 50, 68, 255)
TICK = (150, 132, 172, 255)


def carter_at(s):
    """Every rasteriser reads lib.SCALE at CALL time, so the scale just has to
    be set before the draw - no module reloading.  (Reloading build actually
    fought this, because importing it re-applies the shipping scale.)"""
    import build
    lib.set_scale(s, (47.5, 96.0))
    return build.frame0().rgba()


def drawn_rows(f):
    ys = [y for y in range(len(f)) for x in range(len(f[0])) if f[y][x][3]]
    return min(ys), max(ys)


def player_frame(idx=10):
    w, h, px = read_png(A + '/MainPlayer/player_4dir_sheet.png')
    return crop(px, (idx % 10) * (w // 10), (idx // 10) * (h // 4),
                w // 10, h // 4)


def josh_frame():
    w, h, px = read_png(A + '/Josh/josh_idle.png')
    return crop(px, 0, 0, h, h)


def main():
    import carter_scale
    old = carter_at(1.0)
    new = carter_at(carter_scale.SCALE)
    ply = player_frame()
    jsh = josh_frame()

    figs = []
    for lbl, f, sc in (('OLD Carter', old, BOSS), ('NEW Carter', new, BOSS),
                       ('Josh', jsh, BOSS), ('player', ply, PLAYER)):
        t, b = drawn_rows(f)
        figs.append((lbl, f, sc, t, b, (b - t + 1) * sc))
        print('%-12s %3d rows drawn  ->  %3d px on screen' % (lbl, b - t + 1,
                                                             (b - t + 1) * sc))

    pad, gap = 40, 54
    tall = max(h for *_, h in figs)
    cw = [len(f[0]) * sc for _, f, sc, *_ in figs]
    Wc = pad * 2 + sum(cw) + gap * (len(figs) - 1)
    Hc = pad * 2 + tall + 30
    canvas = blank(Wc, Hc, BG)
    floor = Hc - pad
    # a rule every 48 screen px so the differences are countable
    for y in range(floor, pad - 30, -48):
        for x in range(pad // 2, Wc - pad // 2):
            canvas[y][x] = RULE
    x = pad
    for lbl, f, sc, t, b, hpx in figs:
        img = scale(f, sc)
        paste(canvas, img, x, floor - (b + 1) * sc)
        for xx in range(x, x + len(f[0]) * sc):
            if 0 <= floor < Hc:
                canvas[floor][xx] = FLOOR
        for yy in range(floor - hpx, floor):
            if (yy // 4) % 2 == 0:
                canvas[yy][x] = TICK
        x += len(f[0]) * sc + gap
    write_png(os.path.join(SCRATCH, 'resize_compare.png'), Wc, Hc, canvas)
    print('resize_compare.png %dx%d' % (Wc, Hc))


if __name__ == '__main__':
    main()
