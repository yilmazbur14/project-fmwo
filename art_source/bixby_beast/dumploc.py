"""dump a grid file region in local coords: python dumploc.py grid.txt base_col base_row lx0 lx1 ly0 ly1"""
import sys
g = open(sys.argv[1]).read().split('\n')
bc, br = int(sys.argv[2]), int(sys.argv[3])
lx0, lx1, ly0, ly1 = [int(v) for v in sys.argv[4:8]]
print('     ' + ''.join(str((abs(x) // 10) % 10) for x in range(lx0, lx1 + 1)))
print('     ' + ''.join(str(abs(x) % 10) for x in range(lx0, lx1 + 1)))
for ly in range(ly0, ly1 + 1):
    r = br + ly
    row = g[r] if 0 <= r < len(g) else ''
    print('%4d ' % ly + ''.join(row[bc + lx] if 0 <= bc + lx < len(row) else ' ' for lx in range(lx0, lx1 + 1)))
