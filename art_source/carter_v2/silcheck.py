import sys
from lib import *
a = load_grid(sys.argv[1]); b = load_grid(sys.argv[2])
bad = 0
for y in range(64):
    ra = ''.join('X' if c != '.' else '.' for c in a[y])
    rb = ''.join('X' if c != '.' else '.' for c in b[y])
    if ra != rb:
        bad += 1
        diff = ''.join('^' if ra[i] != rb[i] else ' ' for i in range(64))
        print('%02d new %s' % (y, ra)); print('   old %s' % rb); print('       %s' % diff)
print('rows differing:', bad)
