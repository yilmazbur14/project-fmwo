"""find 1px transparent seams sandwiched between black outline pixels (the guard/blade gap bug)"""
import sys
import scaled  # noqa path
from pngio import read_png


def seams(px, x0, y0, w, h, min_run=3):
    def op(x, y):
        return 0 <= x < x0 + w and 0 <= y < y0 + h and x >= x0 and y >= y0 and px[y][x][3] > 0

    def black(x, y):
        return op(x, y) and px[y][x][:3] == (0, 0, 0)
    hits = []
    # horizontal seam rows: transparent pixel with black directly above and below
    for y in range(y0 + 1, y0 + h - 1):
        run = []
        for x in range(x0, x0 + w + 1):
            ok = x < x0 + w and not op(x, y) and black(x, y - 1) and black(x, y + 1)
            if ok:
                run.append(x)
            else:
                if len(run) >= min_run:
                    hits.append(('row', y, run[0] - x0, run[-1] - x0))
                run = []
    for x in range(x0 + 1, x0 + w - 1):
        run = []
        for y in range(y0, y0 + h + 1):
            ok = y < y0 + h and not op(x, y) and black(x - 1, y) and black(x + 1, y)
            if ok:
                run.append(y)
            else:
                if len(run) >= min_run:
                    hits.append(('col', x - x0, run[0] - y0, run[-1] - y0))
                run = []
    return hits


if __name__ == '__main__':
    path, fw = sys.argv[1], int(sys.argv[2])
    w, h, px = read_png(path)
    fh = h
    n = w // fw
    for i in range(n):
        hs = seams(px, i * fw, 0, fw, fh)
        if hs:
            print('frame', i, hs)
    print(path.split('/')[-1], 'frames', n, 'checked')
