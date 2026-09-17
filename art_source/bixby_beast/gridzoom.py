"""zoom a region with a pixel grid and coordinate ticks every 5 px"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png, write_png
import anim_common as AC

def gridzoom(px_get, x0, y0, w, h, s, out, bg=(96, 112, 104, 255)):
    W, H = w * s + 20, h * s + 20
    img = [[(40, 40, 40, 255)] * W for _ in range(H)]
    for y in range(h):
        for x in range(w):
            p = px_get(x0 + x, y0 + y)
            c = p if (p is not None and p[3]) else bg
            for dy in range(s):
                for dx in range(s):
                    img[20 + y * s + dy][20 + x * s + dx] = c
    for x in range(w + 1):
        col = (255, 255, 0, 255) if (x0 + x) % 5 == 0 else (70, 70, 70, 255)
        for yy in range(20, H):
            if (x0 + x) % 5 == 0 or yy % 2 == 0:
                img[yy][min(W - 1, 20 + x * s)] = col
        if (x0 + x) % 5 == 0:
            for yy in range(0, 18):
                img[yy][min(W - 1, 20 + x * s)] = col
    for y in range(h + 1):
        col = (255, 255, 0, 255) if (y0 + y) % 5 == 0 else (70, 70, 70, 255)
        for xx in range(20, W):
            if (y0 + y) % 5 == 0 or xx % 2 == 0:
                img[min(H - 1, 20 + y * s)][xx] = col
        if (y0 + y) % 5 == 0:
            for xx in range(0, 18):
                img[min(H - 1, 20 + y * s)][xx] = col
    write_png(os.path.join(AC.PREV, out), W, H, img)

if __name__ == '__main__':
    path, x0, y0, w, h, s, out = sys.argv[1], *[int(v) for v in sys.argv[2:7]], sys.argv[7]
    ww, hh, px = read_png(path)
    gridzoom(lambda x, y: tuple(px[y][x]) if 0 <= x < ww and 0 <= y < hh else None, x0, y0, w, h, s, out)
    print('ok')
