from pngio import *
from collections import Counter
w, h, px = read_png(r"C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Computah/computah.png")
print(w, h)
fw = w // 20
# crop frames 12..18 into strip
sel = list(range(12, 20))
rows = [[px[y][f*fw + x] for f in sel for x in range(fw)] for y in range(h)]
W, H, up = upscale(fw*len(sel), h, rows, 6, bg=(40, 40, 40, 255))
write_png("frames_12_19.png", W, H, up)
cnt = Counter()
for f in sel:
    for y in range(h):
        for x in range(fw):
            p = px[y][f*fw+x]
            if p[3] > 0: cnt[p] += 1
for c, n in cnt.most_common(40): print(c, n)
# bounding boxes per frame
for f in range(20):
    xs = [x for y in range(h) for x in range(fw) if px[y][f*fw+x][3] > 0]
    ys = [y for y in range(h) for x in range(fw) if px[y][f*fw+x][3] > 0]
    print(f, min(xs), max(xs), min(ys), max(ys))
