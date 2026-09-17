"""Merge designer A + B v2 parts (40 x 256x192) with validation.
Usage: python merge_sheet_v2.py [out.png]"""
import sys
import os
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pngio import read_png, write_png, blank

FW, FH, N = 256, 192, 40
PA = os.path.join(HERE, 'part_a_v2.png')
PB = 'C:/Users/theyi/AppData/Local/Temp/claude/C--Users-theyi-OneDrive-Documents-new-game-project/a7fc2846-afef-472d-979b-e17143793a0f/scratchpad/eric_anim_b/part_b_v2.png'
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'merged_sheet_v2.png')
APPROVED = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Eric/eric_redesign_v2.png'
A = set(range(0, 13)) | set(range(21, 32))
B = set(range(13, 21)) | set(range(32, 40))

wa, ha, a = read_png(PA)
wb, hb, b = read_png(PB)
problems = []
if (wa, ha) != (FW * N, FH) or (wb, hb) != (FW * N, FH):
    problems.append(f'size mismatch: part_a {wa}x{ha}, part_b {wb}x{hb}, expected {FW * N}x{FH}')


def filled(px, i):
    return any(px[y][x][3] for y in range(FH) for x in range(i * FW, i * FW + FW))


for i in range(N):
    fa, fb = filled(a, i), filled(b, i)
    if fa and fb:
        problems.append(f'frame {i}: filled in BOTH parts')
    if not fa and not fb:
        problems.append(f'frame {i}: EMPTY')
    if i in A and fb:
        problems.append(f'frame {i}: part_b wrote into an A index')
    if i in B and fa:
        problems.append(f'frame {i}: part_a wrote into a B index')
for name, px in (('part_a', a), ('part_b', b)):
    extra = set(Counter(p[3] for r in px for p in r)) - {0, 255}
    if extra:
        problems.append(f'{name} has semi-transparent alpha: {sorted(extra)}')
sheet = blank(FW * N, FH, (0, 0, 0, 0))
for y in range(FH):
    for x in range(FW * N):
        sheet[y][x] = a[y][x] if a[y][x][3] else b[y][x]
_, _, ref = read_png(APPROVED)
d21 = sum(1 for y in range(FH) for x in range(FW) if sheet[y][21 * FW + x] != ref[y][x] and (sheet[y][21 * FW + x][3] or ref[y][x][3]))
if d21:
    problems.append(f'frame 21 differs from eric_redesign_v2.png by {d21} px')
feet = [i for i in range(N) if not any(sheet[FH - 1][x][3] for x in range(i * FW, i * FW + FW))]
if feet:
    problems.append(f'frames without anything on the bottom row (feet anchor): {feet}')
write_png(OUT, FW * N, FH, sheet)
print('problems:', problems if problems else 'none')
print('wrote', OUT)
