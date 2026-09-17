"""Quick in-game-scale check: sprite at 3x on the arena floor colour with the player (back view) for scale."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png, write_png, crop, scale, blank, paste
import view

FLOOR = (136, 180, 99, 255)
PLAYER = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/MainPlayer/player_4dir_sheet.png'

src = sys.argv[1]
out = sys.argv[2]
w, h, px = read_png(src)
pw, ph, ppx = read_png(PLAYER)
player = crop(ppx, 0, 32, 32, 32)       # row 1 = back view
W, H = 260, 200
cv = blank(W, H, FLOOR)
paste(cv, px, 10, 4)
paste(cv, player, 210, 150)
write_png(os.path.join(view.PREV, out), W * 3, H * 3, scale(cv, 3))
