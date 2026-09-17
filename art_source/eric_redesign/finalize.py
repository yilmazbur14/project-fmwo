from compose import build
from pngio import write_png, scale, read_png
from lib import to_grid
FL = (136, 180, 99, 255)
DST = "C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Eric/"
for v in ('sword', 'hammer'):
    cv = build(v)
    cv.save(DST + f'eric_redesign_{v}.png')
    cv.save(f'eric_redesign_{v}.png')
    cv.save(f'eric_redesign_{v}_8x.png', 8, FL)
    open(f'eric_redesign_{v}_grid.txt', 'w').write(to_grid(cv) + '\n')
print('ok')
