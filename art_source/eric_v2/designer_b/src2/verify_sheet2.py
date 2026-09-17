from collections import Counter
from pngio import read_png
w1, h1, A = read_png('../part_b_v2.png')
w2, h2, R_ = read_png('../preview_v2/rt_part_b_v2.png')
print('sizes', (w1, h1), (w2, h2))
diff = 0
alpha = Counter()
for y in range(h1):
    for x in range(w1):
        pa, pr = A[y][x], R_[y][x]
        alpha[pa[3]] += 1
        if not (pa == pr or (pa[3] == 0 and pr[3] == 0)):
            diff += 1
print('aseprite export vs part_b_v2.png diff pixels:', diff)
print('alpha values:', dict(alpha))
