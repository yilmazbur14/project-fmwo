"""Report pixels inside the frame margin (sprite layers: 2px, fx layers: 1px) per sheet/layer/frame."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_sheets as S
import anim_defeat as D

def check(names=None, verbose=True):
    bad = 0
    sheets = dict(S.SHEETS)
    sheets['defeat'] = D.frames
    for name, fn in sheets.items():
        if names and name not in names:
            continue
        for i, fr in enumerate(fn()):
            for L, cv in fr.items():
                if cv is None:
                    continue
                m = 1 if L.startswith('fx') else 2
                pts = [(x, y) for y in range(cv.h) for x in range(cv.w) if cv.px[y][x] is not None and (x < m or x > cv.w - 1 - m or y < m or y > cv.h - 1 - m)]
                if pts:
                    bad += 1
                    if verbose:
                        xs = sorted(set(p[0] for p in pts)); ys = sorted(set(p[1] for p in pts))
                        print('%-8s f%d %-9s %4d px  x%s y%s' % (name, i, L, len(pts), (xs[:6] + ['..'] + xs[-3:]) if len(xs) > 9 else xs, (ys[:6] + ['..'] + ys[-3:]) if len(ys) > 9 else ys))
    print('margin violations:', bad)
    return bad

if __name__ == '__main__':
    check(sys.argv[1:] or None)
