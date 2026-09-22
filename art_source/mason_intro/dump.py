"""python dump.py [frame]  - ASCII dump of a frame, to see the ramp texel by texel."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fries
KEY = {fries.hex2rgba(fries.BLACK): 'K', fries.hex2rgba(fries.YEL): 'Y',
       fries.hex2rgba(fries.YEL_MID): 'y', fries.hex2rgba(fries.YEL_DEEP): 'd',
       fries.hex2rgba(fries.RED): 'R', fries.hex2rgba(fries.RED_HI): 'r'}
which = sys.argv[1:] or [n for n, _ in fries.FRAMES]
for name, fn in fries.FRAMES:
    if name not in which: continue
    g = fn()
    print('--- %s ---' % name)
    for y in range(fries.FH):
        print('%2d %s' % (y, ''.join('.' if g[y][x][3] == 0 else KEY.get(g[y][x], '?')
                                     for x in range(fries.FW))))
