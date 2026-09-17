"""Preview tooling for Josh's animation set: per-animation GIFs, a 6x contact sheet of every
frame, and the 1920x1080 arena mockups.  Preview only - nothing here ships."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jlib import W, H, to_rgba
from pngio import read_png, write_png
from gif import write_gif
from mockup import label, blit_scaled

BG = (40, 38, 52, 255)
LINE = (92, 88, 112, 255)
GRID = (58, 56, 74, 255)
ASSET = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/'


def flat(c, bg=BG):
    g = to_rgba(c)
    return [[(p[:3] + (255,)) if p[3] else bg for p in row] for row in g]


def up(px, f):
    h, w = len(px), len(px[0])
    return [[px[y // f][x // f] for x in range(w * f)] for y in range(h * f)]


def anim_gif(path, canvases, delays, f=5):
    write_gif(path, [up(flat(c), f) for c in canvases], delays)
    print('   gif  %-26s %dx%d  %d frames' % (os.path.basename(path), W * f, H * f, len(canvases)))


def contact(path, rows, f=6, pad=10, cap=26, title='JOSH ANIMATION SET'):
    """rows: list of (name, [canvases]).  One animation per row, frames left to right."""
    ncol = max(len(cs) for _, cs in rows)
    tw, th = W * f, H * f
    lab_w = 150
    TW = lab_w + ncol * (tw + pad) + pad
    TH = 64 + sum(th + cap + pad for _ in rows) + pad
    img = [[BG] * TW for _ in range(TH)]
    label(img, pad + 4, 18, title, sc=5)
    y = 64
    for (name, cs) in rows:
        label(img, pad + 4, y + th // 2 - 8, name, sc=3, col=(255, 240, 180, 255))
        x = lab_w
        for i, c in enumerate(cs):
            tile = up(flat(c), f)
            for yy in range(y - 1, y + th + 1):
                for xx in (x - 1, x + tw):
                    if 0 <= yy < TH and 0 <= xx < TW:
                        img[yy][xx] = LINE
            for yy in range(th):
                img[y + yy][x:x + tw] = tile[yy]
            # feet line at source row 79
            for xx in range(x, x + tw, 6):
                for k in range(f):
                    img[y + 79 * f + k][xx] = (200, 80, 90, 255)
            label(img, x + 4, y + th + 6, str(i), sc=3, col=(190, 200, 220, 255))
            x += tw + pad
        y += th + cap + pad
    write_png(path, TW, TH, img)
    print('   sheet %-26s %dx%d' % (os.path.basename(path), TW, TH))


def arena(path, bgpath, items, title, subtitle):
    """items: (png path, frame index, frame w, ox, oy_feet, scale, flip, caption)"""
    bw, bh, bg = read_png(bgpath)
    img = [[p[:3] + (255,) for p in row] for row in bg]
    GROUND = 900
    pw, ph, ppx = read_png(ASSET + 'MainPlayer/player_4dir_sheet.png')
    blit_scaled(img, ppx, pw, ph, 0, 0, 32, 32, 250, GROUND - 32 * 2, 2)
    label(img, 226, GROUND + 16, 'PLAYER 2X', sc=3)
    for (src, idx, fw, ox, oy, sc, flip, cap_text) in items:
        w, h, px = read_png(src)
        blit_scaled(img, px, w, h, idx * fw, 0, fw, 80, ox, oy, sc, flip=flip)
        label(img, ox + 4, GROUND + 16, cap_text, sc=3)
    for x in range(200, 1500):
        if x % 8 < 4:
            for y in (GROUND, GROUND + 1):
                img[y][x] = (255, 240, 180, 255)
    label(img, 220, 130, title, sc=6)
    label(img, 220, 190, subtitle, sc=3)
    write_png(path, bw, bh, img)
    print('   arena %-26s %dx%d' % (os.path.basename(path), bw, bh))
