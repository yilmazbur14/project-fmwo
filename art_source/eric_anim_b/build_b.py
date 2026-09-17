"""Render part B (frames 13-20, 32-39) into the 40-frame 5120x128 layout, run checks, write previews + GIFs."""
import os
import sys
import time
import pickle
from collections import Counter
from base import *
import whirl
import throw
from gifio import write_gif
from pngio import blank, paste, crop, scale, write_png, read_png

OUT = os.path.dirname(HERE)          # scratchpad/eric_anim_b
PREV = os.path.join(OUT, 'preview')
os.makedirs(PREV, exist_ok=True)
FW = 128
B_FRAMES = list(range(13, 21)) + list(range(32, 40))

TIMINGS = {  # seconds per frame
    'whirlwind': ([13, 14, 15, 16, 17, 18, 19, 20], [0.0833, 0.1389, 0.1111, 0.1111, 0.1111, 0.1111, 0.1111, 0.0972]),
    'throw_windup': ([32, 33], [0.15, 0.40]),
    'throw_release': ([34, 35], [0.08, 0.22]),
    'empty_wait': ([36, 37], [0.12, 0.12]),
    'recall_catch': ([38, 39], [0.25, 0.15]),
}


def despeckle(px):
    """drop opaque pixels with no opaque 8-neighbour (stray smear fragments)"""
    out = [row[:] for row in px]
    for y in range(FW):
        for x in range(FW):
            if px[y][x][3]:
                if not any(px[y + dy][x + dx][3] for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                           if (dx or dy) and 0 <= x + dx < FW and 0 <= y + dy < FW):
                    out[y][x] = (0, 0, 0, 0)
    return out


def render_all(use_cache=False):
    cache_path = os.path.join(OUT, 'frames_b.pkl')
    if use_cache and os.path.exists(cache_path):
        return pickle.load(open(cache_path, 'rb'))
    imgs = {}
    for i in B_FRAMES:
        t = time.time()
        fr = whirl.whirl_frame(i) if i <= 20 else throw.FRAMES[i]()
        imgs[i] = despeckle(fr.rgba())
        print('frame', i, '%.1fs' % (time.time() - t))
    pickle.dump(imgs, open(cache_path, 'wb'))
    return imgs


def checks(imgs):
    ok = True
    report = []
    for i in B_FRAMES:
        px = imgs[i]
        alphas = Counter(p[3] for r in px for p in r)
        bad_alpha = [a for a in alphas if a not in (0, 255)]
        opaque = [(x, y) for y in range(FW) for x in range(FW) if px[y][x][3]]
        xs = [x for x, y in opaque]
        ys = [y for x, y in opaque]
        bottom = any(px[127][x][3] for x in range(FW))
        # isolated opaque pixels (no 8-neighbour)
        iso = []
        for x, y in opaque:
            n = 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if (dx or dy) and 0 <= x + dx < FW and 0 <= y + dy < FW and px[y + dy][x + dx][3]:
                        n += 1
            if n == 0:
                iso.append((x, y))
        # feet: opaque pixels in rows 118..127 (the sabatons) -> horizontal centre
        feet = [x for x, y in opaque if y >= 124 and px[y][x][:3] in (PALC['W'][:3], PALC['A'][:3], PALC['B'][:3], PALC['C'][:3], PALC['D'][:3], PALC['E'][:3], (0, 0, 0))]
        colours = len(set(p for r in px for p in r if p[3]))
        line = 'f%02d alpha=%s bbox=(%d,%d)-(%d,%d) bottom_row=%s isolated=%d colours=%d' % (
            i, dict(alphas), min(xs), min(ys), max(xs), max(ys), bottom, len(iso), colours)
        report.append(line)
        if bad_alpha or not bottom:
            ok = False
    return ok, report


def sheet(imgs):
    sh = blank(40 * FW, FW, (0, 0, 0, 0))
    for i in B_FRAMES:
        paste(sh, imgs[i], i * FW, 0)
    return sh


def gif(imgs, order, secs, path, s=3, bg=FL):
    frames = [[[p[:3] for p in row] for row in scale(rgba_on(imgs[i], bg), s)] for i in order]
    write_gif(path, frames, [max(2, int(round(d * 100))) for d in secs])


def strip_with_approved(imgs, order, path, s=3):
    ap = approved_px()
    ims = [ap] + [imgs[i] for i in order]
    strip(ims, s, path)


if __name__ == '__main__':
    use_cache = '--cache' in sys.argv
    imgs = render_all(use_cache)
    ok, rep = checks(imgs)
    print('\n'.join(rep))
    print('CHECKS', 'PASS' if ok else 'FAIL')
    sh = sheet(imgs)
    write_png(os.path.join(OUT, 'part_b.png'), 40 * FW, FW, sh)
    # previews
    strip_with_approved(imgs, TIMINGS['whirlwind'][0], os.path.join(PREV, 'strip3x_whirlwind_vs_approved.png'))
    strip_with_approved(imgs, list(range(32, 40)), os.path.join(PREV, 'strip3x_throw_vs_approved.png'))
    imgs[21] = approved_px()
    for name, (order, secs) in TIMINGS.items():
        gif(imgs, order, secs, os.path.join(PREV, 'gif_%s.gif' % name))
    # full attack in context: idle -> windup -> release -> wait x3 -> recall -> catch -> idle
    seq = [21, 32, 33, 34, 35] + [36, 37] * 4 + [38, 39, 21]
    secs = [0.4, 0.15, 0.40, 0.08, 0.22] + [0.12, 0.12] * 4 + [0.25, 0.15, 0.6]
    gif(imgs, seq, secs, os.path.join(PREV, 'gif_throw_full_sequence.gif'))
    gif(imgs, [21] + TIMINGS['whirlwind'][0] * 2 + [21], [0.4] + TIMINGS['whirlwind'][1] * 2 + [0.6],
        os.path.join(PREV, 'gif_whirlwind_from_idle.gif'))
    # grids (palette chars) for archival / revision
    rev = {v: k for k, v in PALC.items()}
    with open(os.path.join(OUT, 'part_b_grids.txt'), 'w') as f:
        for i in B_FRAMES:
            f.write('# frame %d\n' % i)
            for row in imgs[i]:
                f.write(''.join('.' if not p[3] else rev.get(tuple(p), '?') for p in row) + '\n')
    print('wrote part_b.png')
