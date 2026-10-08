import sys, os
sys.dont_write_bytecode = True
from PIL import Image
from common import zoom, save, paste, ASSETS
import trophy as T
sheet = Image.open(os.path.join(ASSETS, 'Characters/MainPlayer/player_4dir_sheet.png')).convert('RGBA')
idle = sheet.crop((0, 0, 32, 32))
bg = Image.open(os.path.join(os.path.dirname(__file__), '..', '..', 'cap', 'bg_calm0.png')).convert('RGBA')
crop = bg.crop((240, 130, 400, 230)).copy()
st = T.stand().image()
STAND_BOTTOM = int(sys.argv[1]) if len(sys.argv) > 1 else 40
def put(cv, take, bx, by):
    tro = T.trophy(take).image(); sp = T.spec(take)
    paste(cv, idle, (bx, by))
    sx, sy = bx + 15 - T.S['CX'], by + STAND_BOTTOM - (st.height - 1)
    paste(cv, st, (sx, sy))
    seat = sy + T.S['SEAT_Y']
    paste(cv, tro, (bx + 15 - sp['CX'], seat - (tro.height - 1)))
c = crop.copy()
put(c, 'A', 20, 20); put(c, 'B', 70, 20)
paste(c, T.trophy('A').image(), (120, 10)); paste(c, T.trophy('B').image(), (138, 10)); paste(c, st, (122, 40))
save(zoom(c, 6), 'work/look_scale.png')
