from collections import Counter
from pngio import read_png

w1, h1, A = read_png('../part_b.png')
w2, h2, R = read_png('../preview/rt_part_b.png')
print('sizes', (w1, h1), (w2, h2))
diff = 0
alpha = Counter()
for y in range(h1):
    ra, rr = A[y], R[y]
    for x in range(w1):
        pa, pr = ra[x], rr[x]
        alpha[pa[3]] += 1
        if not (pa == pr or (pa[3] == 0 and pr[3] == 0)):
            diff += 1
print('aseprite export vs part_b.png diff pixels:', diff)
print('alpha values:', dict(alpha))
B = set(list(range(13, 21)) + list(range(32, 40)))
bad, empty = [], []
for i in range(40):
    has = any(A[y][x][3] for y in range(128) for x in range(i * 128, (i + 1) * 128))
    if i in B and not has:
        empty.append(i)
    if i not in B and has:
        bad.append(i)
print('non-B frames with pixels:', bad, '| B frames empty:', empty)
