import sys
rows = open(sys.argv[1]).read().split('\n')
y0 = int(sys.argv[2]) if len(sys.argv) > 2 else 0
y1 = int(sys.argv[3]) if len(sys.argv) > 3 else 63
x0 = int(sys.argv[4]) if len(sys.argv) > 4 else 0
x1 = int(sys.argv[5]) if len(sys.argv) > 5 else 63
print('    ' + ''.join(str(x // 10) for x in range(x0, x1 + 1)))
print('    ' + ''.join(str(x % 10) for x in range(x0, x1 + 1)))
for y in range(y0, y1 + 1):
    print('%2d  %s' % (y, rows[y][x0:x1 + 1]))
