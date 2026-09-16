import sys, fxpng
def norm(p):
    # fully transparent pixels compare equal regardless of stored rgb
    return (0, 0, 0, 0) if p[3] == 0 else tuple(p)
def cmp(a_path, b_path):
    wa, ha, a = fxpng.read_png(a_path)
    wb, hb, b = fxpng.read_png(b_path)
    if (wa, ha) != (wb, hb):
        return 'SIZE MISMATCH %dx%d vs %dx%d' % (wa, ha, wb, hb)
    diff = [(x, y, a[y][x], b[y][x]) for y in range(ha) for x in range(wa) if norm(a[y][x]) != norm(b[y][x])]
    return 'IDENTICAL (%dx%d)' % (wa, ha) if not diff else 'DIFF %d px, first: %s' % (len(diff), diff[:5])
if __name__ == '__main__':
    pairs = sys.argv[1:]
    for i in range(0, len(pairs), 2):
        print(pairs[i + 1].split('/')[-1], 'vs', pairs[i].split('/')[-1], '->', cmp(pairs[i], pairs[i + 1]))
