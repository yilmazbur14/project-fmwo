"""Compare two PNGs pixel-exactly (fully transparent pixels compare equal regardless of rgb)."""
import sys
from pngio import read_png


def norm(p):
    return [[(0, 0, 0, 0) if px[3] == 0 else px for px in row] for row in p]


def compare(a, b):
    wa, ha, pa = read_png(a)
    wb, hb, pb = read_png(b)
    if (wa, ha) != (wb, hb):
        return 'SIZE MISMATCH %s vs %s' % ((wa, ha), (wb, hb))
    pa, pb = norm(pa), norm(pb)
    diff = [(x, y, pa[y][x], pb[y][x]) for y in range(ha) for x in range(wa) if pa[y][x] != pb[y][x]]
    partial = sum(1 for row in pb for px in row if px[3] not in (0, 255))
    return '%dx%d, %d differing px, %d partial-alpha px %s' % (wa, ha, len(diff), partial, diff[:3])


if __name__ == '__main__':
    print(compare(sys.argv[1], sys.argv[2]))
