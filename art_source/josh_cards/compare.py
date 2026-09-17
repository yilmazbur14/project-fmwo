"""Side-by-side comparison sheet: new Josh vs his approved redesign vs the quality bar."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png, write_png

ASSET = r'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/'
BG = (46, 44, 58, 255)
LINE = (86, 82, 104, 255)


def tile(px, w, h, sx, sy, cw, ch, f):
    out = []
    for Y in range(ch * f):
        row = []
        for X in range(cw * f):
            x, y = sx + X // f, sy + Y // f
            p = px[y][x] if 0 <= y < h and 0 <= x < w else (0, 0, 0, 0)
            row.append(p)
        out.append(row)
    return out


def blit(dst, src, ox, oy):
    for y, row in enumerate(src):
        for x, p in enumerate(row):
            if p[3] and 0 <= oy + y < len(dst) and 0 <= ox + x < len(dst[0]):
                dst[oy + y][ox + x] = p


def sheet(path, items, f=6, pad=10):
    tiles = []
    for (src, sx, sy, cw, ch) in items:
        w, h, px = read_png(src)
        tiles.append((tile(px, w, h, sx, sy, cw, ch, f), cw * f, ch * f))
    W = sum(t[1] for t in tiles) + pad * (len(tiles) + 1)
    H = max(t[2] for t in tiles) + pad * 2
    img = [[BG] * W for _ in range(H)]
    x = pad
    for i, (t, tw, th) in enumerate(tiles):
        y = H - pad - th
        for yy in range(y - 1, y + th + 1):
            for xx in (x - 1, x + tw):
                if 0 <= yy < H and 0 <= xx < W:
                    img[yy][xx] = LINE
        blit(img, t, x, y)
        x += tw + pad
    write_png(path, W, H, img)
    print('wrote', path, W, 'x', H)


if __name__ == '__main__':
    OUT = sys.argv[1]
    sheet(OUT + '/compare_6x.png', [
        (OUT + '/f0.png', 0, 0, 80, 80),
        (OUT + '/f1.png', 0, 0, 80, 80),
        (ASSET + 'Josh/josh_redesign.png', 0, 0, 64, 64),
        (ASSET + 'Mason/mason.png', 0, 0, 64, 64),
    ])
