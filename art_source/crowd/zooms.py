import sys
from pngio import read_png, write_png, scale
w, h, px = read_png(sys.argv[1])
specs = [s.split(':') for s in sys.argv[3:]]   # x0:width:frame
rows_out = []
Z = int(sys.argv[2])
maxw = max(int(s[1]) for s in specs) * Z
for x0, cw, fr in specs:
    x0, cw, fr = int(x0), int(cw), int(fr)
    c = [[(p if p[3] else (0, 0, 0, 255)) for p in row[fr*640 + x0: fr*640 + x0 + cw]] for row in px]
    big = scale(c, Z)
    for r in big:
        rows_out.append(r + [(40, 40, 40, 255)] * (maxw - len(r)))
    rows_out.extend([[(120, 120, 120, 255)] * maxw for _ in range(4)])
write_png('prev/zooms.png', maxw, len(rows_out), rows_out)
print('ok')
