"""Arena mockups (1920x1080) over the Godot-rendered ArenaScene, 6x comparison sheet, and hover GIF."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png, write_png, crop, scale, blank, paste
from gifio import write_gif

HERE = os.path.dirname(os.path.abspath(__file__))
FINAL = os.path.join(HERE, '..', 'final')
PREVIEWS = os.path.join(HERE, '..')          # scratchpad/bixby_beast/
ARENA = os.path.join(HERE, '..', 'arena_render', 'arena00000002.png')
PLAYER = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/MainPlayer/player_4dir_sheet.png'
BIXBY = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Bixby/bixby.png'
FLOOR = (136, 180, 99, 255)
S = 3
SHADOW_ALPHA = 0.38


def blit_scaled(dst, src, x0, y0, s=S):
    H, W = len(dst), len(dst[0])
    for y, row in enumerate(src):
        for x, p in enumerate(row):
            if p[3] == 0:
                continue
            for dy in range(s):
                yy = y0 + y * s + dy
                if not 0 <= yy < H:
                    continue
                r = dst[yy]
                for dx in range(s):
                    xx = x0 + x * s + dx
                    if 0 <= xx < W:
                        r[xx] = p


def shade_scaled(dst, src, x0, y0, alpha, s=S):
    H, W = len(dst), len(dst[0])
    for y, row in enumerate(src):
        for x, p in enumerate(row):
            if p[3] == 0:
                continue
            for dy in range(s):
                yy = y0 + y * s + dy
                if not 0 <= yy < H:
                    continue
                r = dst[yy]
                for dx in range(s):
                    xx = x0 + x * s + dx
                    if 0 <= xx < W:
                        q = r[xx]
                        r[xx] = (int(round(q[0] * (1 - alpha))), int(round(q[1] * (1 - alpha))), int(round(q[2] * (1 - alpha))), 255)


def arena_base():
    w, h, px = read_png(ARENA)
    px = [[tuple(p) for p in row] for row in px]
    # remove the render's own player so the placed player sprite is the only one
    for y in range(870, 932):
        for x in range(940, 980):
            px[y][x] = FLOOR
    return px


def mockup(kind):
    px = arena_base()
    beast_w, beast_h, beast = read_png(os.path.join(FINAL, 'bixby_beast.png'))
    fire_w, fire_h, fire = read_png(os.path.join(FINAL, 'bixby_beast_firebreath.png'))
    sh_w, sh_h, shadow = read_png(os.path.join(FINAL, 'bixby_beast_shadow.png'))
    pw, ph, player_sheet = read_png(PLAYER)
    player = crop(player_sheet, 0, 32, 32, 32)          # row 1, frame 0: back view facing up
    # sprite top-left on screen; hover anchor (96,152) -> (960, 586)
    X0, Y0 = 960 - 96 * S, 586 - 152 * S
    hover_gap = 40                                        # texels between hover anchor and shadow centre
    sx0 = 960 - 96 * S
    sy0 = 586 + hover_gap * S - 25 * S
    shade_scaled(px, crop(shadow, 0, 0, 192, 48), sx0, sy0, SHADOW_ALPHA)
    if kind == 'hover':
        blit_scaled(px, crop(beast, 0, 0, 192, 160), X0, Y0)
    else:
        blit_scaled(px, crop(fire, 192 * 2, 0, 192, 256), X0, Y0)
    blit_scaled(px, player, 960 - 16 * S, 905 - 28 * S)
    out = os.path.join(PREVIEWS, 'mockup_arena_%s_1920x1080.png' % kind)
    write_png(out, 1920, 1080, px)
    return out


def closeup_sheet():
    s = 6
    bg = (40, 44, 52, 255)
    items = []
    w, h, px = read_png(BIXBY)
    items.append(px)
    w, h, px = read_png(os.path.join(FINAL, 'bixby_swallow_draft.png'))
    items.append(px)
    w, h, px = read_png(os.path.join(FINAL, 'bixby_beast.png'))
    items.append(crop(px, 0, 0, 192, 160))
    w, h, px = read_png(os.path.join(FINAL, 'bixby_beast_firebreath.png'))
    items.append(crop(px, 384, 0, 192, 256))
    gap = 12
    W = sum(len(it[0]) * s for it in items) + gap * (len(items) + 1)
    Hh = max(len(it) * s for it in items) + gap * 2
    out = blank(W, Hh, bg)
    x = gap
    for it in items:
        ih = len(it) * s
        y = Hh - gap - ih                                   # bottom-aligned so the scale difference is honest
        panel = scale(it, s, (58, 64, 74, 255))
        paste(out, panel, x, y)
        x += len(it[0]) * s + gap
    path = os.path.join(PREVIEWS, 'closeup_6x_original_gag_beast_firebreath.png')
    write_png(path, W, Hh, out)
    return path


def hover_gif():
    w, h, px = read_png(os.path.join(FINAL, 'bixby_beast.png'))
    sw, shh, spx = read_png(os.path.join(FINAL, 'bixby_beast_shadow.png'))
    frames = []
    gap = 40
    W, H = 208, 152 + gap + 30
    for i in range(4):
        cv = blank(W, H, FLOOR)
        sh = crop(spx, 192 * i, 0, 192, 48)
        for y, row in enumerate(sh):
            for x, p in enumerate(row):
                if p[3]:
                    yy, xx = 4 + 152 + gap - 25 + y, 8 + x
                    if 0 <= yy < H and 0 <= xx < W:
                        q = cv[yy][xx]
                        cv[yy][xx] = tuple(int(round(q[k] * (1 - SHADOW_ALPHA))) for k in range(3)) + (255,)
        paste(cv, crop(px, 192 * i, 0, 192, 160), 8, 4)
        frames.append(scale(cv, 3))
    path = os.path.join(PREVIEWS, 'bixby_beast_hover_loop_3x.gif')
    write_gif(path, frames, [14, 10, 12, 10])
    return path


def fire_gif():
    w, h, px = read_png(os.path.join(FINAL, 'bixby_beast_firebreath.png'))
    frames = []
    for i in (0, 1, 2, 1, 2):
        cv = blank(208, 264, FLOOR)
        paste(cv, crop(px, 192 * i, 0, 192, 256), 8, 4)
        frames.append(scale(cv, 2))
    path = os.path.join(PREVIEWS, 'bixby_beast_firebreath_2x.gif')
    write_gif(path, frames, [40, 12, 14, 8, 14])
    return path


if __name__ == '__main__':
    what = sys.argv[1:] or ['hover', 'fire', 'sheet', 'gif']
    if 'hover' in what:
        print(mockup('hover'))
    if 'fire' in what:
        print(mockup('fire'))
    if 'sheet' in what:
        print(closeup_sheet())
    if 'gif' in what:
        print(hover_gif())
        print(fire_gif())
