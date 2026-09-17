"""Build part B v2: frames 13-20 + 32-39 at 256x192 into the 40-frame 10240x192 layout; checks, previews, GIFs, grids."""
import os
import sys
import subprocess
from collections import Counter
from base2 import *
import runframes
from gifio import write_gif

OUT = os.path.dirname(HERE)
PREV = os.path.join(OUT, 'preview_v2')
os.makedirs(PREV, exist_ok=True)
B = list(range(13, 21)) + list(range(32, 40))

TIMINGS = {
    'whirlwind': ([13, 14, 15, 16, 17, 18, 19, 20], [0.0833, 0.1389, 0.1111, 0.1111, 0.1111, 0.1111, 0.1111, 0.0972]),
    'throw_windup': ([32, 33], [0.15, 0.40]),
    'throw_release': ([34, 35], [0.08, 0.22]),
    'empty_wait': ([36, 37], [0.12, 0.12]),
    'recall_catch': ([38, 39], [0.25, 0.15]),
}


def despeckle(px):
    out = [row[:] for row in px]
    for y in range(FH):
        for x in range(FW):
            if px[y][x][3] and not any(px[y + dy][x + dx][3] for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                                       if (dx or dy) and 0 <= x + dx < FW and 0 <= y + dy < FH):
                out[y][x] = (0, 0, 0, 0)
    return out


def checks(imgs):
    ok = True
    rep = []
    for i in B:
        px = imgs[i]
        alphas = Counter(p[3] for r in px for p in r)
        xs = [x for y in range(FH) for x in range(FW) if px[y][x][3]]
        ys = [y for y in range(FH) for x in range(FW) if px[y][x][3]]
        bottom = [x for x in range(FW) if px[FH - 1][x][3]]
        iso = sum(1 for y in range(FH) for x in range(FW) if px[y][x][3] and not any(
            px[y + dy][x + dx][3] for dy in (-1, 0, 1) for dx in (-1, 0, 1)
            if (dx or dy) and 0 <= x + dx < FW and 0 <= y + dy < FH))
        feet_c = (min(bottom) + max(bottom)) / 2 if bottom else -1
        rep.append('f%02d alpha=%s bbox=(%d,%d)-(%d,%d) bottom_row_px=%d feet_centre_x=%.1f isolated=%d colours=%d' % (
            i, dict(alphas), min(xs), min(ys), max(xs), max(ys), len(bottom), feet_c, iso,
            len(set(p for r in px for p in r if p[3]))))
        if any(a not in (0, 255) for a in alphas) or not bottom:
            ok = False
    return ok, rep


def gif(imgs, order, secs, path, s=2):
    frames = [[[p[:3] for p in row] for row in scale(rgba_on(imgs[i]), s)] for i in order]
    write_gif(path, frames, [max(2, int(round(d * 100))) for d in secs])


if __name__ == '__main__':
    use_cache = '--cache' in sys.argv
    raw = runframes.render(B, use_cache=use_cache)
    imgs = {i: despeckle(raw[i]) for i in B}
    ok, rep = checks(imgs)
    print('\n'.join(rep))
    print('CHECKS', 'PASS' if ok else 'FAIL')
    sheet = blank(40 * FW, FH, (0, 0, 0, 0))
    for i in B:
        paste(sheet, imgs[i], i * FW, 0)
    write_png(os.path.join(OUT, 'part_b_v2.png'), 40 * FW, FH, sheet)
    ap = approved_px()
    strip([ap] + [imgs[i] for i in TIMINGS['whirlwind'][0]], 2, os.path.join(PREV, 'strip2x_whirlwind_vs_v2base.png'))
    strip([ap] + [imgs[i] for i in range(32, 40)], 2, os.path.join(PREV, 'strip2x_throw_vs_v2base.png'))
    imgs[21] = ap
    for name, (order, secs) in TIMINGS.items():
        gif(imgs, order, secs, os.path.join(PREV, 'gif_%s.gif' % name))
    seq = [21, 32, 33, 34, 35] + [36, 37] * 4 + [38, 39, 21]
    secs = [0.4, 0.15, 0.40, 0.08, 0.22] + [0.12, 0.12] * 4 + [0.25, 0.15, 0.6]
    gif(imgs, seq, secs, os.path.join(PREV, 'gif_throw_full_sequence.gif'))
    gif(imgs, [21] + TIMINGS['whirlwind'][0] * 2 + [21], [0.4] + TIMINGS['whirlwind'][1] * 2 + [0.6],
        os.path.join(PREV, 'gif_whirlwind_from_idle.gif'))
    rev = {}
    for k, v in PALC.items():
        rev.setdefault(v, k)
    with open(os.path.join(OUT, 'part_b_v2_grids.txt'), 'w') as f:
        for i in B:
            f.write('# frame %d\n' % i)
            for row in imgs[i]:
                f.write(''.join('.' if not p[3] else rev.get(tuple(p), '?') for p in row) + '\n')
    print('wrote part_b_v2.png')
