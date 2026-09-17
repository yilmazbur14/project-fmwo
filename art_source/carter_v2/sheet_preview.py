"""Previews of the 2-frame strip: 8x checker, 3x on arena green, and cast comparison."""
import sys
from lib import *
R = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/'
idle = grid_to_pix(load_grid(os.path.join(HERE, 'idle.txt')))
charge = grid_to_pix(load_grid(os.path.join(HERE, 'charge.txt')))
GREEN = (136, 179, 99, 255)
save(os.path.join(HERE, 'frames_8x.png'), hcat([zoom(idle, 8), zoom(charge, 8)]))
save(os.path.join(HERE, 'frames_green_3x.png'), hcat([zoom(idle, 3, GREEN), zoom(charge, 3, GREEN)], bg=GREEN))
print('ok')
