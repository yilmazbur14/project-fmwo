"""The two trophy takes side by side, for the pick."""
import os
import sys
sys.dont_write_bytecode = True
from PIL import Image, ImageDraw, ImageFont
from common import save, zoom, OUT, stats
import trophy as T
import champion as C
import build as BD

CAP = os.path.realpath(os.path.join(OUT, '..', 'cap'))
bg = Image.open(os.path.join(CAP, 'bg_state_08.png')).convert('RGBA')
MAT = (136, 182, 101, 255)
BODY = (304, 149)
CELL_AT = (BODY[0] - C.BODY_AT[0], BODY[1] - C.BODY_AT[1])


def panel(take):
    f = ImageFont.load_default(size=22)
    s = ImageFont.load_default(size=15)
    W, H = 900, 1010
    p = Image.new('RGBA', (W, H), (24, 22, 34, 255))
    d = ImageDraw.Draw(p)
    title = {'A': 'TAKE A - THE GLOVE CUP (recommended)', 'B': 'TAKE B - THE TITLE CUP'}[take]
    d.text((20, 14), title, fill=(251, 210, 60), font=f)
    blurb = {'A': 'Classic two-handled loving cup, navy plinth + gold plate, Burak-blue glove emblem.',
             'B': 'Lidded chalice + star finial, plinth wrapped in a red title belt, slanted # buckle.'}[take]
    d.text((20, 44), blurb, fill=(220, 220, 230), font=s)
    t = T.trophy(take).image()
    st = stats(t)
    d.text((20, 64), f'{t.width}x{t.height} px, {st["colours"]} colours, {st["black"]}% black keyline, no semi-alpha',
           fill=(160, 160, 180), font=s)
    # 10x the cup alone, on the mat green
    big = zoom(t, 10, MAT)
    p.paste(big, (20, 92))
    # on the stand, waiting (idle loop frames 0, 3, 8) at 5x
    x = 20 + big.width + 30
    d.text((x, 92), 'waiting on the stand (shine loop)', fill=(200, 200, 210), font=s)
    for i, fi in enumerate((0, 3, 8)):
        cell = BD.stand_cell(take, *BD.IDLE[fi][:2])
        c = zoom(cell.crop((4, 26, 36, 64)), 4, MAT)
        p.paste(c, (x + i * 140, 116))
    # the drop frame and a hold frame at 4x
    y = 116 + 38 * 4 + 40
    d.text((20, y), 'in his hands: the DROP frame (lift) and the hold loop', fill=(200, 200, 210), font=s)
    for i, n in enumerate(('gather_a', 'lift', 'hold_2', 'hold_3')):
        c = zoom(C.compose(take, n), 4, MAT)
        p.paste(c, (20 + i * 175, y + 24))
        d.text((24 + i * 175, y + 26 + 256), n + ('  <- on the drop' if n == 'lift' else ''),
               fill=(160, 160, 180), font=s)
    # in the arena at game scale (3x), roaring crowd
    y2 = y + 24 + 64 * 4 + 34
    arena = bg.copy()
    arena.alpha_composite(C.compose(take, 'hold_1'), CELL_AT)
    crop = arena.crop((230, 100, 410, 200)).resize((540, 300), Image.NEAREST)
    d.text((20, y2), 'at game scale (3x) on the real arena', fill=(200, 200, 210), font=s)
    p.paste(crop, (20, y2 + 22))
    return p


if __name__ == '__main__':
    a, b = panel('A'), panel('B')
    sheet = Image.new('RGBA', (a.width * 2 + 20, a.height), (10, 10, 16, 255))
    sheet.paste(a, (0, 0)); sheet.paste(b, (a.width + 20, 0))
    print(save(sheet, 'compare/trophy_takes_compare.png'))
