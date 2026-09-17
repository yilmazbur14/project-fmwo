"""Game-scale check: sprites at 3x (boss scale) next to the player at 2x (MainPlayer.tscn scale) on the floor colour."""
import os
from pngio import read_png, write_png, crop, blank
import view

PLAYER = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/MainPlayer/player_4dir_sheet.png'


def blit(dst, px, x0, y0, s):
    H, W = len(dst), len(dst[0])
    for y, row in enumerate(px):
        for x, p in enumerate(row):
            if p[3] == 0:
                continue
            for dy in range(s):
                for dx in range(s):
                    X, Y = x0 + x * s + dx, y0 + y * s + dy
                    if 0 <= X < W and 0 <= Y < H:
                        dst[Y][X] = p


def player_px(row=0, frame=0):
    w, h, px = read_png(PLAYER)
    return crop(px, frame * 32, row * 32, 32, 32)


def check(items, name, W=None, H=None, floor_y=None):
    """items: list of (rgba rows, scale, x) all bottom-aligned on floor_y (screen px)"""
    W = W or sum(len(p[0]) * s + 30 for p, s, _ in items) + 30
    H = H or max(len(p) * s for p, s, _ in items) + 40
    floor_y = floor_y or H - 20
    out = blank(W, H, view.FLOOR)
    for px, s, x in items:
        blit(out, px, x, floor_y - len(px) * s, s)
    path = os.path.join(view.PREV, name)
    write_png(path, W, H, out)
    return path
