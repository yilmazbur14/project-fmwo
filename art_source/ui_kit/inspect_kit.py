import sys, collections
from pngio import read_png, write_png, upscale
P = "C:/Users/theyi/OneDrive/Documents/new-game-project/"
files = sys.argv[1:]
for f in files:
    w, h, px = read_png(P + f)
    cnt = collections.Counter(p for row in px for p in row if p[3] > 0)
    print(f, w, h, "opaque colors:", len(cnt))
    for c, n in cnt.most_common(40):
        print("   #%02x%02x%02x a=%d n=%d" % (c[0], c[1], c[2], c[3], n))
