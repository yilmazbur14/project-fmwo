"""Merge designer A + B parts into the 40-frame sheet with validation. Usage: python merge_sheet.py"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pngio import read_png, write_png, blank
from collections import Counter
PA = os.path.join(HERE, 'part_a.png')
PB = 'C:/Users/theyi/AppData/Local/Temp/claude/C--Users-theyi-OneDrive-Documents-new-game-project/a7fc2846-afef-472d-979b-e17143793a0f/scratchpad/eric_anim_b/part_b.png'
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'eric_redesign_sheet_merged.png')
A = set(range(0, 13)) | set(range(21, 32))
B = set(range(13, 21)) | set(range(32, 40))
wa, ha, a = read_png(PA)
wb, hb, b = read_png(PB)
assert (wa, ha) == (5120, 128) and (wb, hb) == (5120, 128), ((wa, ha), (wb, hb))
def filled(px, i):
    return any(px[y][x][3] for y in range(128) for x in range(i * 128, i * 128 + 128))
problems = []
for i in range(40):
    fa, fb = filled(a, i), filled(b, i)
    owner = 'A' if i in A else 'B'
    if fa and fb:
        problems.append(f'frame {i}: filled in BOTH parts')
    if not fa and not fb:
        problems.append(f'frame {i}: EMPTY')
    if owner == 'A' and fb:
        problems.append(f'frame {i}: B wrote into an A index')
    if owner == 'B' and fa:
        problems.append(f'frame {i}: A wrote into a B index')
alphas = Counter(p[3] for r in b for p in r)
if set(alphas) - {0, 255}:
    problems.append(f'part_b has semi-transparent alpha values: {sorted(set(alphas) - {0, 255})}')
sheet = blank(5120, 128, (0, 0, 0, 0))
for y in range(128):
    for x in range(5120):
        p = a[y][x] if a[y][x][3] else b[y][x]
        sheet[y][x] = p
write_png(OUT, 5120, 128, sheet)
print('problems:', problems if problems else 'none')
print('wrote', OUT)
