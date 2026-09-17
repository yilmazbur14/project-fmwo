from base2 import *
from pngio import read_png
_, _, A = read_png('../../eric_redesign/part_a_v2.png')
_, _, Bp = read_png('../part_b_v2.png')
W = len(A[0])
fa = [i for i in range(40) if any(A[y][x][3] for y in range(192) for x in range(i * 256, (i + 1) * 256))]
fb = [i for i in range(40) if any(Bp[y][x][3] for y in range(192) for x in range(i * 256, (i + 1) * 256))]
print('A frames', fa)
print('B frames', fb)
print('overlap', sorted(set(fa) & set(fb)), 'missing', sorted(set(range(40)) - set(fa) - set(fb)))
merged = [[(Bp[y][x] if Bp[y][x][3] else A[y][x]) for x in range(W)] for y in range(192)]
seq = [12, 13, 20, 21, 31, 32, 39, 21]
ims = [crop(merged, i * 256, 0, 256, 192) for i in seq]
strip(ims, 1, '../preview_v2/merge_seams_1x.png')
