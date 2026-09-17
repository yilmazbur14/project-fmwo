import sys
def show(path, x0, y0, x1, y1):
    rows = open(path).read().split('\n')
    hdr1 = '    ' + ''.join(str((x // 10) % 10) for x in range(x0, x1 + 1))
    hdr2 = '    ' + ''.join(str(x % 10) for x in range(x0, x1 + 1))
    print(hdr1); print(hdr2)
    for y in range(y0, y1 + 1):
        print('%3d %s' % (y, rows[y][x0:x1 + 1]))
if __name__ == '__main__':
    a = sys.argv
    show(a[1], int(a[2]), int(a[3]), int(a[4]), int(a[5]))
