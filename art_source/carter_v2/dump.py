"""dump.py IN x y w h -> prints the region as palette-indexed characters + legend (for studying pixel structure)"""
import sys
sys.path.insert(0, r"C:/Users/theyi/AppData/Local/Temp/claude/C--Users-theyi-OneDrive-Documents-new-game-project/a7fc2846-afef-472d-979b-e17143793a0f/scratchpad/carter_v2")
from pngio import read_png
a = sys.argv[1:]
w, h, pix = read_png(a[0])
x0, y0, cw, ch = map(int, a[1:5]) if len(a) >= 5 else (0, 0, w, h)
chars = "#abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@$%&*+=?<>"
pal = {}
lines = []
for y in range(y0, y0 + ch):
    s = ''
    for x in range(x0, x0 + cw):
        p = pix[y][x]
        if p[3] == 0:
            s += '.'
            continue
        key = p
        if key not in pal:
            if p[:3] == (0, 0, 0):
                pal[key] = '#'
            else:
                used = set(pal.values())
                for c in chars[1:]:
                    if c not in used:
                        pal[key] = c
                        break
        s += pal[key]
    lines.append('%2d %s' % (y, s))
print('    ' + ''.join(str((x0 + i) // 10 % 10) for i in range(cw)))
print('    ' + ''.join(str((x0 + i) % 10) for i in range(cw)))
print('\n'.join(lines))
for k, v in sorted(pal.items(), key=lambda kv: kv[1]):
    print(v, '#%02x%02x%02x a=%d' % (k[0], k[1], k[2], k[3]))
