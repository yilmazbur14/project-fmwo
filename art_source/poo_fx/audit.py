import sys
def load(path, fw, fh, n):
    lines = [l.rstrip('\n') for l in open(path) if not l.startswith('#')]
    assert len(lines) == fh * n, (len(lines), fh * n)
    return [lines[i * fh:(i + 1) * fh] for i in range(n)]
def audit(g, name, edge_ok='Kt'):
    H = len(g); W = len(g[0])
    at = lambda x, y: g[y][x] if 0 <= x < W and 0 <= y < H else '.'
    orphans, gaps, clumps = [], [], []
    for y in range(H):
        for x in range(W):
            c = g[y][x]
            if c == '.':
                continue
            nb = [at(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            if all(n == '.' for n in nb):
                orphans.append((x, y, c))
            if c not in edge_ok and '.' in nb:
                gaps.append((x, y, c))
            if x < W - 1 and y < H - 1 and c == 'K' and at(x + 1, y) == 'K' and at(x, y + 1) == 'K' and at(x + 1, y + 1) == 'K':
                clumps.append((x, y))
    print('%s: orphans=%d gaps=%d 2x2-black=%d' % (name, len(orphans), len(gaps), len(clumps)))
    if orphans: print('   orphans', orphans)
    if gaps: print('   gaps', gaps[:40])
    if clumps: print('   clumps', clumps)
if __name__ == '__main__':
    path, fw, fh, n = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
    for i, g in enumerate(load(path, fw, fh, n)):
        audit(g, 'frame %d' % i)
