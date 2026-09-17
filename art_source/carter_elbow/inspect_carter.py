import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from pngio import read_png, write_png, upscale
from collections import Counter

SCR = os.path.dirname(__file__)
PROJ = 'C:/Users/theyi/OneDrive/Documents/new-game-project'

src = sys.argv[1]
name = sys.argv[2]
fw = int(sys.argv[3]) if len(sys.argv) > 3 else 64
w, h, pix = read_png(src)
print('size', w, h)
cnt = Counter()
for y in range(h):
    for x in range(w):
        cnt[pix[y][x]] += 1
print('unique colours', len(cnt))
for c, n in cnt.most_common():
    print('  #%02x%02x%02x a=%3d  %d' % (c[0], c[1], c[2], c[3], n))

# 8x upscale with frame grid
W, H, up = upscale(w, h, pix, 8, bg='checker', grid=(fw, 0, (255, 0, 255, 255)))
write_png(os.path.join(SCR, name + '_8x.png'), W, H, up)
print('wrote', name + '_8x.png')
