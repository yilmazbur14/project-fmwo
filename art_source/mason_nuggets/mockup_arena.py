"""1920x1080 arena mock-up mid-shower, on a real movie-writer render of the Mason fight
(crowd, ropes, boss bar, hearts). Mason (hold pose, frame 18) sits exactly where the
game draws him; every effect is at integer 3x, the player at his 2x."""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from compose import *

DEST = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'previews')
os.makedirs(DEST, exist_ok=True)
RENDER = ('C:/Users/theyi/AppData/Local/Temp/claude/C--Users-theyi-OneDrive-Documents-new-game-project/'
          'a7fc2846-afef-472d-979b-e17143793a0f/scratchpad/player_facing/renders/clean/f00000150.png')
PLAYER = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/MainPlayer/player_4dir_sheet.png'

mason = Sheet(os.path.join(OUT, 'mason_sheet.png'), 64, 64)
meteor = Sheet(os.path.join(OUT, 'nugget_meteor.png'), 48, 64)
target = Sheet(os.path.join(OUT, 'nugget_target.png'), 48, 26)
impact = Sheet(os.path.join(OUT, 'nugget_impact.png'), 64, 48)
player = Sheet(PLAYER, 32, 32)

V = (-math.sin(math.radians(20)), math.cos(math.radians(20)))
S = 3

c = Canvas.from_png(RENDER)
# paint out the idle Mason + player that are baked into the render (plain mat there)
c.rect(852, 178, 1062, 388, MAT)

MASON_POS = (960, 280)          # measured from the render: frame 0 content bbox 867..1046 x 187..375

markers = [                     # (marker frame, centre, meteor distance still to fall in screen px, meteor frame)
    (3, (520, 575), 95, 0),
    (2, (1290, 520), 250, 1),
    (2, (1060, 790), 340, 2),
    (1, (1545, 760), 470, 3),
    (0, (330, 845), 650, 1),
]
IMPACT = (2, (805, 505))
PLAYER_POS = (690, 700)
PLAYER_FRAME = (2, 1)           # walking, back view (facing Mason)

for f, (x, y), d, mf in markers:
    c.place(target.frame(f), x, y, S)
c.place(impact.frame(IMPACT[0]), IMPACT[1][0], IMPACT[1][1], S)
# y-sorted characters
chars = [(MASON_POS[1] + 96, 'mason'), (PLAYER_POS[1] + 32, 'player')]
for _, who in sorted(chars):
    if who == 'mason':
        c.place(mason.frame(18), MASON_POS[0], MASON_POS[1], S)
    else:
        col, row = PLAYER_FRAME
        c.place(player.frame(col, row), PLAYER_POS[0], PLAYER_POS[1], 2)
# meteors are in the air: drawn over everything, nugget centre on the 20-degree fall line
for f, (x, y), d, mf in markers:
    nx, ny = x - V[0] * d, y - V[1] * d
    c.place(meteor.frame(mf), nx, ny, S, anchor=(16.5, 48.0))

out = os.path.join(DEST, 'mockup_arena_nugget_shower_1920x1080.png')
c.save(out)
print('wrote', out)
