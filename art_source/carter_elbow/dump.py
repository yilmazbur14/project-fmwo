"""dump.py src fw frame [x0 y0 x1 y1] -> ascii grid using carter palette"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png

PAL = {
    (0, 0, 0, 0): '.',
    (0, 0, 0, 255): 'K',
    (0xd9, 0xa0, 0x66, 255): 's',
    (0xb8, 0x79, 0x4a, 255): 'm',
    (0xf0, 0xc0, 0x88, 255): 'h',
    (0xa0, 0x6b, 0x3e, 255): 'd',
    (0x8c, 0x5a, 0x34, 255): 'D',
    (0x3a, 0x6f, 0xd8, 255): 'B',
    (0x5a, 0x8f, 0xf0, 255): 'L',
    (0x28, 0x50, 0xa8, 255): 'b',
    (0x1a, 0x1a, 0x1a, 255): 'k',
    (0xc2, 0x66, 0x2b, 255): 'O',
    (0xa8, 0x5a, 0x24, 255): 'o',
    (0x8f, 0x4a, 0x1e, 255): 'r',
    (0x5a, 0x2e, 0x12, 255): 'n',
    (0x1a, 0x10, 0x08, 255): 'e',
    (0xff, 0xff, 0xff, 255): 'w',
    (0xe8, 0xc6, 0x4a, 255): 'G',
    (0xa8, 0x86, 0x2a, 255): 'g',
}
src = sys.argv[1]
fw = int(sys.argv[2])
fr = int(sys.argv[3])
w, h, pix = read_png(src)
x0, y0, x1, y1 = 0, 0, fw, h
if len(sys.argv) > 4:
    x0, y0, x1, y1 = [int(v) for v in sys.argv[4:8]]
print('    ' + ''.join(str((x // 10) % 10) for x in range(x0, x1)))
print('    ' + ''.join(str(x % 10) for x in range(x0, x1)))
for y in range(y0, y1):
    line = ''
    for x in range(x0, x1):
        p = pix[y][fr * fw + x]
        if p[3] == 0:
            p = (0, 0, 0, 0)
        line += PAL.get(p, '?')
    print('%3d ' % y + line)
