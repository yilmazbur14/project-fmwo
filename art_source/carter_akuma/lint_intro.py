"""Checks on the entrance sheets: binary alpha, palette size, feet anchor,
frame bounds, and that the spliced settle frames match the approved sheet
pixel for pixel."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png, crop

C = r"C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Carter"
W = H = 96
FAIL = []


def check(path, fw, fh, feet=None):
    w, h, px = read_png(path)
    n = w // fw
    alphas, cols = set(), set()
    for row in px:
        for p in row:
            alphas.add(p[3])
            if p[3]:
                cols.add(tuple(p))
    print('\n%-24s %dx%d  %d frames of %dx%d' %
          (os.path.basename(path), w, h, n, fw, fh))
    print('  alphas %s   colours %d' % (sorted(alphas), len(cols)))
    if not alphas <= {0, 255}:
        FAIL.append('%s: non-binary alpha' % path)
    for f in range(n):
        ys = [y for y in range(fh) for x in range(fw) if px[y][f * fw + x][3]]
        xs = [x for y in range(fh) for x in range(fw) if px[y][f * fw + x][3]]
        if not ys:
            print('  f%-2d EMPTY' % f)
            continue
        lo = max(ys)
        tag = ''
        if feet is not None and f >= feet[0] and lo != feet[1]:
            tag = '   <-- feet at %d, expected %d' % (lo, feet[1])
            FAIL.append('%s f%d feet row %d' % (path, f, lo))
        print('  f%-2d rows %2d..%2d  cols %2d..%2d%s'
              % (f, min(ys), lo, min(xs), max(xs), tag))
    return px, n


intro, n = check(C + '/carter_intro.png', W, H, feet=(4, 95))
check(C + '/carter_aura.png', W, H)
gw, gh, _ = read_png(C + '/carter_mark_glow.png')
check(C + '/carter_mark_glow.png', gw // 6, gh)
fw, fh, _ = read_png(C + '/carter_intro_flash.png')
check(C + '/carter_intro_flash.png', fw, fh)

# the settle frames must BE the approved frames
_, _, appr = read_png(C + '/carter_akuma.png')
for intro_f, appr_f, name in ((14, 1, 'signature'), (16, 0, 'idle')):
    a = crop(intro, intro_f * W, 0, W, H)
    b = crop(appr, appr_f * W, 0, W, H)
    same = all(a[y][x] == b[y][x] for y in range(H) for x in range(W))
    print('\nintro f%d == approved f%d (%s): %s'
          % (intro_f, appr_f, name, 'EXACT' if same else 'MISMATCH'))
    if not same:
        FAIL.append('intro f%d != approved f%d' % (intro_f, appr_f))

print('\n' + ('FAILURES:\n  ' + '\n  '.join(FAIL) if FAIL else 'all checks passed'))
