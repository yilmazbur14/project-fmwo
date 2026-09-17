"""Approval previews: 6x line-up of the new Josh beside his approved redesign, plus a glow GIF."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png, write_png
from mockup import label

ASSET = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/'
BG = (40, 38, 52, 255)
LINE = (92, 88, 112, 255)


def tile(px, w, h, sx, sy, cw, ch, f):
    return [[px[sy + Y // f][sx + X // f] if 0 <= sy + Y // f < h and 0 <= sx + X // f < w
             else (0, 0, 0, 0) for X in range(cw * f)] for Y in range(ch * f)]


def sheet(path, items, f=6, pad=16, cap=34, title=None):
    tiles = []
    for (src, sx, sy, cw, ch, cap_text) in items:
        w, h, px = read_png(src)
        tiles.append((tile(px, w, h, sx, sy, cw, ch, f), cw * f, ch * f, cap_text))
    top = 54 if title else pad
    W = sum(t[1] for t in tiles) + pad * (len(tiles) + 1)
    H = max(t[2] for t in tiles) + top + pad + cap
    img = [[BG] * W for _ in range(H)]
    if title:
        label(img, pad + 4, 16, title, sc=4)
    x = pad
    for (t, tw, th, cap_text) in tiles:
        y = H - pad - cap - th
        for yy in range(y - 1, y + th + 1):
            for xx in (x - 1, x + tw):
                if 0 <= yy < H and 0 <= xx < W:
                    img[yy][xx] = LINE
        for yy, row in enumerate(t):
            for xx, p in enumerate(row):
                if p[3]:
                    img[y + yy][x + xx] = p[:3] + (255,)
        label(img, x + 2, H - pad - cap + 8, cap_text, sc=3)
        x += tw + pad
    write_png(path, W, H, img)
    print('wrote', os.path.basename(path), W, 'x', H)


if __name__ == '__main__':
    OUT = sys.argv[1]
    J = ASSET + 'Josh/'
    sheet(OUT + '/preview_lineup_6x.png', [
        (J + 'josh_cards.png', 0, 0, 80, 80, 'NEW IDLE'),
        (J + 'josh_cards.png', 80, 0, 80, 80, 'NEW SIGNATURE POSE'),
        (J + 'josh_redesign.png', 0, 0, 64, 64, 'APPROVED JOSH'),
        (ASSET + 'Mason/mason.png', 0, 0, 64, 64, 'MASON QUALITY BAR'),
    ], f=6, title='JOSH CARD SHOWMAN 6X')
    # Sunglasses decision is settled: shades up on the brim.  This sheet just shows the likeness
    # match against his approved face.
    sheet(OUT + '/preview_face_8x.png', [
        (J + 'josh_cards.png', 18, 6, 46, 48, 'NEW FACE'),
        (J + 'josh_redesign.png', 12, 0, 42, 34, 'APPROVED FACE'),
    ], f=8, title='LIKENESS CHECK')
