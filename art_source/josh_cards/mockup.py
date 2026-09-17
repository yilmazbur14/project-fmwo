"""1920x1080 arena mockup: new Josh at 3x beside the player at 2x, on a real arena frame."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png, write_png

ASSET = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/'


def blit_scaled(dst, src_px, sw, sh, sx, sy, cw, ch, ox, oy, f, flip=False):
    DH, DW = len(dst), len(dst[0])
    for Y in range(ch * f):
        for X in range(cw * f):
            ux = (cw - 1 - X // f) if flip else (X // f)
            p = src_px[sy + Y // f][sx + ux]
            if p[3] == 0:
                continue
            dx, dy = ox + X, oy + Y
            if 0 <= dx < DW and 0 <= dy < DH:
                dst[dy][dx] = p[:3] + (255,)


def label(dst, x, y, text, col=(255, 240, 180, 255), sc=3):
    FONT = {
        'A': ["010", "101", "111", "101", "101"], 'B': ["110", "101", "110", "101", "110"],
        'C': ["011", "100", "100", "100", "011"], 'D': ["110", "101", "101", "101", "110"],
        'E': ["111", "100", "110", "100", "111"], 'F': ["111", "100", "110", "100", "100"],
        'G': ["011", "100", "101", "101", "011"], 'H': ["101", "101", "111", "101", "101"],
        'I': ["111", "010", "010", "010", "111"], 'J': ["001", "001", "001", "101", "010"],
        'K': ["101", "110", "100", "110", "101"], 'L': ["100", "100", "100", "100", "111"],
        'M': ["101", "111", "111", "101", "101"], 'N': ["101", "111", "111", "111", "101"],
        'O': ["010", "101", "101", "101", "010"], 'P': ["110", "101", "110", "100", "100"],
        'R': ["110", "101", "110", "110", "101"], 'S': ["011", "100", "010", "001", "110"],
        'T': ["111", "010", "010", "010", "010"], 'U': ["101", "101", "101", "101", "011"],
        'V': ["101", "101", "101", "101", "010"], 'W': ["101", "101", "111", "111", "101"],
        'X': ["101", "101", "010", "101", "101"], 'Y': ["101", "101", "010", "010", "010"],
        'Z': ["111", "001", "010", "100", "111"], '0': ["111", "101", "101", "101", "111"],
        '1': ["010", "110", "010", "010", "111"], '2': ["111", "001", "111", "100", "111"],
        '3': ["111", "001", "111", "001", "111"], '4': ["101", "101", "111", "001", "001"],
        '5': ["111", "100", "111", "001", "111"], '6': ["111", "100", "111", "101", "111"],
        '7': ["111", "001", "001", "001", "001"], '8': ["111", "101", "111", "101", "111"],
        '9': ["111", "101", "111", "001", "111"], '.': ["000", "000", "000", "000", "010"],
        ' ': ["000", "000", "000", "000", "000"], '(': ["001", "010", "010", "010", "001"],
        ')': ["100", "010", "010", "010", "100"], ',': ["000", "000", "000", "010", "100"],
    }
    for k, ch in enumerate(text.upper() if text.upper() in FONT or True else text):
        g = FONT.get(ch if ch in FONT else ch.upper(), FONT[' '])
        for j in range(5):
            for i in range(3):
                if g[j][i] != '1':
                    continue
                for yy in range(sc):
                    for xx in range(sc):
                        X, Y = x + (k * 4 + i) * sc + xx, y + j * sc + yy
                        if 0 <= Y < len(dst) and 0 <= X < len(dst[0]):
                            dst[Y][X] = col


if __name__ == '__main__':
    OUT = sys.argv[1]
    bw, bh, bg = read_png(os.path.join(OUT, 'arena', 'frame00000002.png'))
    img = [[p[:3] + (255,) for p in row] for row in bg]

    jw, jh, jpx = read_png(os.path.join(OUT, 'josh_cards.png'))
    pw, ph, ppx = read_png(ASSET + 'MainPlayer/player_4dir_sheet.png')

    GROUND = 900
    # kept clear of the arena scene's own player sprite (it sits near x=960)
    blit_scaled(img, ppx, pw, ph, 0, 0, 32, 32, 250, GROUND - 32 * 2, 2)
    label(img, 226, GROUND + 16, 'PLAYER 2X', sc=3)
    blit_scaled(img, jpx, jw, jh, 0, 0, 80, 80, 360, GROUND - 80 * 3, 3, flip=True)
    label(img, 372, GROUND + 16, 'IDLE 3X', sc=3)
    blit_scaled(img, jpx, jw, jh, 80, 0, 80, 80, 640, GROUND - 80 * 3, 3, flip=True)
    label(img, 636, GROUND + 16, 'SIGNATURE POSE 3X', sc=3)
    for x in range(200, 900):                       # dashed ground line
        if x % 8 < 4:
            for y in (GROUND, GROUND + 1):
                img[y][x] = (255, 240, 180, 255)
    label(img, 220, 150, 'JOSH REDESIGN', sc=6)
    label(img, 220, 210, '80X80 FRAMES, 3X IN SCENE, FEET ON ROW 79', sc=3)
    write_png(os.path.join(OUT, 'arena_mockup.png'), bw, bh, img)
    print('wrote arena_mockup.png', bw, 'x', bh)
