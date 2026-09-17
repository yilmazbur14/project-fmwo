"""1920x1080 arena mockups for the Liam/Bixby entrance.
Base: Godot movie-writer render of Scenes/Core/ArenaScene.tscn (its own player painted out and re-placed).
Sprites at 3x (boss scale); the player at 2x (MainPlayer.tscn CharacterBody2D scale); shadows blended at 38%.
The dialogue box in (b) is the real balloon.tscn rendered by Godot over black and white (exact alpha recovered)."""
import math
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png, write_png, crop
from lib import *
from pal import *
import throne
import compose
import carriers
import slap
import swallow
import transform

HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.path.normpath(os.path.join(HERE, '..'))
OUT = os.path.join(SP, 'liam_entrance')
ARENA = os.path.join(SP, 'le_arena', 'arena00000002.png')
BAL_BLACK = os.path.join(SP, 'le_balloon', 'bal00000008.png')
BAL_WHITE = os.path.join(SP, 'le_balloon', 'bal00000018.png')
PLAYER = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/MainPlayer/player_4dir_sheet.png'
FLOOR = (136, 180, 99, 255)
SHADOW_ALPHA = 0.38
os.makedirs(OUT, exist_ok=True)


def arena_base():
    w, h, px = read_png(ARENA)
    px = [[tuple(p) for p in row] for row in px]
    for y in range(868, 934):
        for x in range(936, 984):
            px[y][x] = FLOOR
    return px


def blit(dst, cv, x0, y0, s=3):
    H, W = len(dst), len(dst[0])
    for y in range(cv.h):
        row = cv.px[y]
        for x in range(cv.w):
            p = row[x]
            if p is None:
                continue
            for dy in range(s):
                yy = y0 + y * s + dy
                if 0 <= yy < H:
                    r = dst[yy]
                    for dx in range(s):
                        xx = x0 + x * s + dx
                        if 0 <= xx < W:
                            r[xx] = p


def blit_px(dst, px, x0, y0, s):
    cv = Canvas(len(px[0]), len(px))
    for y, row in enumerate(px):
        for x, p in enumerate(row):
            if p[3]:
                cv.px[y][x] = tuple(p)
    blit(dst, cv, x0, y0, s)


def shadow(dst, cx, cy, rx, ry, alpha=SHADOW_ALPHA, s=3):
    """pixel-art ellipse shadow in texels (s px each), multiplied onto the floor"""
    m = ell(0, 0, rx, ry)
    H, W = len(dst), len(dst[0])
    for (tx, ty) in m:
        for dy in range(s):
            for dx in range(s):
                X, Y = int(cx + tx * s + dx), int(cy + ty * s + dy)
                if 0 <= X < W and 0 <= Y < H:
                    q = dst[Y][X]
                    dst[Y][X] = (int(q[0] * (1 - alpha)), int(q[1] * (1 - alpha)), int(q[2] * (1 - alpha)), 255)


def tint(dst, col, alpha):
    for row in dst:
        for i, q in enumerate(row):
            row[i] = (int(q[0] + (col[0] - q[0]) * alpha), int(q[1] + (col[1] - q[1]) * alpha), int(q[2] + (col[2] - q[2]) * alpha), 255)


def player(dst, feet_x, feet_y):
    w, h, px = read_png(PLAYER)
    fr = crop(px, 0, 32, 32, 32)          # row 1: back view, facing up the arena
    # sprite feet are on row ~27 of the 32px frame, centred at x 16
    shadow(dst, feet_x - 1, feet_y - 1, 6, 1.6, s=2)
    blit_px(dst, fr, feet_x - 32, feet_y - 28 * 2, 2)


def balloon(dst):
    wb, hb, B = read_png(BAL_BLACK)
    ww, hw, Wt = read_png(BAL_WHITE)
    for y in range(780, 1080):
        for x in range(0, 1920):
            b, w = B[y][x], Wt[y][x]
            a = 1.0 - ((w[0] - b[0]) + (w[1] - b[1]) + (w[2] - b[2])) / (3 * 255.0)
            if a <= 0.01:
                continue
            q = dst[y][x]
            col = [min(255, b[i] / a) if a > 0 else 0 for i in range(3)]
            dst[y][x] = tuple(int(q[i] * (1 - a) + col[i] * a) for i in range(3)) + (255,)


def rot90(cv, cw=True):
    out = Canvas(cv.h, cv.w)
    for y in range(cv.h):
        for x in range(cv.w):
            c = cv.px[y][x]
            if c is None:
                continue
            if cw:
                out.px[x][cv.h - 1 - y] = c
            else:
                out.px[cv.w - 1 - x][y] = c
    return out


def procession_canvas(walk=True):
    frames = dict(zip(['c1', 'c2', 'c3', 'c4'], carriers.build_all()))
    if walk:
        frames['c1'] = carriers.c1_walk()[1]
    cv = Canvas(216, 146)
    compose.procession(cv, 12, 2, carrier_frames=frames)
    return cv, (12, 2)


def palanquin_set_down():
    f0, f1 = throne.build()
    cv = Canvas(throne.FW, throne.FH)
    cv.blit(f1)
    cv.blit(f0)
    cv.blit(from_png(compose.BIX_PNG), *compose.BIXBY_POS)
    return cv


SWEAT_STAMP = """
.k.
kbk
kWBk
.kk.
"""


def collapsed_carriers(dst, gx, gy):
    """the four carriers flopped on the floor, exhausted (rotated straining poses); gx = palanquin left edge"""
    cs = carriers.build_all()
    # (sprite, clockwise, x offset from palanquin left, y offset from ground, sweat drop offset in texels)
    spots = [(cs[2], False, -210, -36, (4, 2)), (cs[0], False, -118, 18, (4, 4)),
             (cs[1], True, 606, 22, (22, 4)), (cs[3], True, 700, -30, (24, 3))]
    for cv, cw, dx, dy, (sx, sy) in spots:
        r = rot90(cv, cw)
        x0, y0 = gx + dx, gy + dy
        shadow(dst, x0 + r.w * 3 // 2, y0 + r.h * 3 - 30, 13, 3)
        blit(dst, r, x0, y0)
        sw = Canvas(8, 8)
        sw.stamp(SWEAT_STAMP, 0, 0, {'k': BLACK, 'b': SWEAT[1], 'B': SWEAT[2], 'W': WHITE})
        blit(dst, sw, x0 + sx * 3, y0 + sy * 3)


def mock_a():
    px = arena_base()
    cv, (ox, oy) = procession_canvas(walk=True)
    X0, Y0 = 960 - (ox + 96) * 3, 118
    # floor shadows: dais footprint between the pole rows, plus each carrier
    gy_rear = Y0 + (oy + compose.REAR_Y + 31) * 3
    gy_front = Y0 + (oy + compose.FRONT_Y + 31) * 3
    shadow(px, X0 + (ox + 96) * 3, (gy_rear + gy_front) // 2 - 6, 74, 7)
    for name, (x, y) in compose.CARRIER_POS.items():
        shadow(px, X0 + (ox + x + 16) * 3, Y0 + (oy + y + 31) * 3 - 3, 8, 2.2)
    blit(px, cv, X0, Y0)
    player(px, 960, 905)
    path = os.path.join(OUT, 'mockup_a_procession_1920x1080.png')
    write_png(path, 1920, 1080, px)
    return path


def mock_b():
    px = arena_base()
    pal = palanquin_set_down()
    X0 = 960 - 96 * 3
    ground = 600
    Y0 = ground - 124 * 3
    shadow(px, 960, ground - 30, 80, 10)
    blit(px, pal, X0, Y0)
    import liam_seated
    blit(px, liam_seated.build(), X0 + compose.LIAM_POS[0] * 3, Y0 + compose.LIAM_POS[1] * 3)
    collapsed_carriers(px, X0, ground - 30)
    player(px, 960, 770)
    balloon(px)
    path = os.path.join(OUT, 'mockup_b_throne_dialogue_1920x1080.png')
    write_png(path, 1920, 1080, px)
    return path


def background_scene(px):
    """throne set down upstage, carriers flopped beside it; returns Bixby/Liam ground row for the foreground"""
    f0, f1 = throne.build()
    pal = Canvas(throne.FW, throne.FH)
    pal.blit(f1)
    pal.blit(f0)
    X0 = 960 - 96 * 3
    ground = 470
    Y0 = ground - 124 * 3
    shadow(px, 960, ground - 30, 80, 10)
    blit(px, pal, X0, Y0)
    collapsed_carriers(px, X0, ground - 30)


def storyboard_mock(frame_cv, name, feet_y=770, liam_shadow=True):
    px = arena_base()
    background_scene(px)
    FX0 = 960 - 62 * 3
    FY0 = feet_y - 96 * 3
    shadow(px, FX0 + (slap.BX + 32) * 3, feet_y - 4, 28, 4)
    if liam_shadow:
        shadow(px, FX0 + (slap.LX + 30) * 3, feet_y - 4, 22, 3.5)
    blit(px, frame_cv, FX0, FY0)
    player(px, 960, 945)
    path = os.path.join(OUT, name)
    write_png(path, 1920, 1080, px)
    return path


def mock_c():
    keys, fed = slap.build()
    return storyboard_mock(keys[1], 'mockup_c_smack_1920x1080.png')


def mock_d():
    fr = swallow.build()
    return storyboard_mock(fr[1], 'mockup_d_chomp_1920x1080.png', liam_shadow=False)


def mock_e():
    px = arena_base()
    background_scene(px)
    feet_y = 770
    bix_feet_x = 960 - 62 * 3 + (slap.BX + 32) * 3
    player(px, 960, 945)
    tint(px, (255, 250, 214), 0.62)
    fl = transform.build()[2]
    TX0 = bix_feet_x - transform.CX * 3
    TY0 = feet_y - (transform.GROUND + 1) * 3
    blit(px, fl, TX0, TY0)
    path = os.path.join(OUT, 'mockup_e_transform_flash_1920x1080.png')
    write_png(path, 1920, 1080, px)
    return path


if __name__ == '__main__':
    which = sys.argv[1:] or ['a', 'b', 'c', 'd', 'e']
    for k in which:
        print(globals()['mock_' + k]())
