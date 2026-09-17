import sys
from kitlib import *
# stack.py out.png cropx cropy cropw croph in1 in2 ...
out = sys.argv[1]; cx, cy, cw, ch = map(int, sys.argv[2:6]); ins = sys.argv[6:]
rows = []
for f in ins:
    w, h, px = read_png(f)
    rows += crop(px, cx, cy, cw, ch)
    rows += [[(255, 0, 255, 255)] * cw for _ in range(4)]
write_png(out, cw, len(rows), rows)
print("stacked", len(ins), "->", out, cw, len(rows))
