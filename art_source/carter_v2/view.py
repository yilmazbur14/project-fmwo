"""view.py IN OUT SCALE [x y w h] [bg]  -> nearest-neighbour zoom of a region, checker bg, optional grid lines every 64px"""
import sys
sys.path.insert(0, r"C:/Users/theyi/AppData/Local/Temp/claude/C--Users-theyi-OneDrive-Documents-new-game-project/a7fc2846-afef-472d-979b-e17143793a0f/scratchpad/carter_v2")
from pngio import read_png, write_png

def crop(pix, x, y, w, h):
    out = []
    for yy in range(y, y + h):
        row = []
        for xx in range(x, x + w):
            if 0 <= yy < len(pix) and 0 <= xx < len(pix[0]):
                row.append(pix[yy][xx])
            else:
                row.append((0, 0, 0, 0))
        out.append(row)
    return out

def zoom(pix, s, bg='checker', gridpx=0):
    h = len(pix); w = len(pix[0])
    out = []
    for Y in range(h * s):
        y = Y // s
        row = []
        for X in range(w * s):
            x = X // s
            p = pix[y][x]
            if p[3] < 255:
                if bg == 'checker':
                    c = 205 if ((X // (s * 4) + Y // (s * 4)) % 2 == 0) else 175
                    base = (c, c, c)
                else:
                    base = bg
                a = p[3] / 255.0
                p = tuple(int(p[i] * a + base[i] * (1 - a)) for i in range(3)) + (255,)
            if gridpx and ((X % (gridpx * s) == 0 and X) or (Y % (gridpx * s) == 0 and Y)):
                p = (255, 0, 255, 255)
            row.append(p)
        out.append(row)
    return out

if __name__ == '__main__':
    a = sys.argv[1:]
    w, h, pix = read_png(a[0])
    s = int(a[2])
    if len(a) >= 7:
        x, y, cw, ch = map(int, a[3:7])
        pix = crop(pix, x, y, cw, ch)
    bg = 'checker'
    if len(a) >= 8:
        bg = tuple(int(a[7][i:i+2], 16) for i in (0, 2, 4))
    z = zoom(pix, s, bg)
    write_png(a[1], len(z[0]), len(z), z)
    print('wrote', a[1], len(z[0]), 'x', len(z))
