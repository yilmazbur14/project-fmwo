"""3x (1920x1080) mockups: walk start, arrival at the poster, poster close-up under the dialogue box."""
from pngio import read_png, write_png, upscale
from lib import Canvas, RGB
from compose import frame
from street import FEET
from overlays import rain_frame

ASSETS = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets'
OUT = 'C:/Users/theyi/AppData/Local/Temp/claude/C--Users-theyi-OneDrive-Documents-new-game-project/a7fc2846-afef-472d-979b-e17143793a0f/scratchpad/cutscene_env/mockups'

sky = Canvas.load('out/street_sky.png')
st = Canvas.load('out/street_buildings.png')
fg = Canvas.load('out/street_fg.png')

# dialogue panel from Scenes/balloon.tscn: offsets 162..1758 x 816..1068 at 1920x1080 -> art px
DLG = (54, 272, 585, 355)
PLACEHOLDER_W, PLACEHOLDER_H = 18, 48


def to_rgba(c):
    return [[(RGB[k] + (255,)) if k is not None else (0, 0, 0, 0) for k in row] for row in c.p]


def over(dst, src_rgba, x0, y0):
    for y, row in enumerate(src_rgba):
        for x, p in enumerate(row):
            if p[3] == 255 and 0 <= y0 + y < len(dst) and 0 <= x0 + x < len(dst[0]):
                dst[y0 + y][x0 + x] = p


def nine_slice(path, w, h, m=10):
    sw, sh, src = read_png(path)
    out = []
    for y in range(h):
        if y < m:
            sy = y
        elif y >= h - m:
            sy = sh - (h - y)
        else:
            sy = m + (y - m) * (sh - 2 * m) // (h - 2 * m)
        row = []
        for x in range(w):
            if x < m:
                sx = x
            elif x >= w - m:
                sx = sw - (w - x)
            else:
                sx = m + (x - m) * (sw - 2 * m) // (w - 2 * m)
            row.append(src[sy][sx])
        out.append(row)
    return out


def dialogue(rgba, name_len=34, lines=(300, 236)):
    x0, y0, x1, y1 = DLG
    over(rgba, nine_slice(ASSETS + '/UI/ui_dialogue_frame.png', x1 - x0 + 1, y1 - y0 + 1), x0, y0)
    grey = RGB['F'] + (255,)
    name = RGB['d'] + (255,)
    tx, ty = x0 + 12, y0 + 12
    for yy in range(ty, ty + 5):
        for xx in range(tx, tx + name_len):
            rgba[yy][xx] = name
    for i, ln in enumerate(lines):
        for yy in range(ty + 14 + i * 13, ty + 19 + i * 13):
            for xx in range(tx, tx + ln):
                rgba[yy][xx] = grey


def placeholder(c, x_center):
    x0 = x_center - PLACEHOLDER_W // 2
    y1 = FEET
    y0 = FEET - PLACEHOLDER_H + 1
    x1 = x0 + PLACEHOLDER_W - 1
    c.rect(x0, y0, x1, y1, 'F')
    c.box(x0, y0, x1, y1, 'K')
    c.line(x0, y0, x1, y1, 'K')
    c.line(x1, y0, x0, y1, 'K')


def street_shot(cam, burak_x, rain_seed=None):
    f = frame([(sky, 0.25, 0), (st, 1.0, 0)], cam)
    placeholder(f, burak_x - cam)
    for y in range(360):
        for x in range(640):
            k = fg.get(x + cam, y)
            if k is not None:
                f.p[y][x] = k
    if rain_seed is not None:
        r = rain_frame(rain_seed)
        f.blit(r, 0, 0)
    return f


def save3(rgba, name):
    W, H, big = upscale(640, 360, rgba, 3)
    write_png(OUT + '/' + name, W, H, big)


if __name__ == '__main__':
    import os
    os.makedirs(OUT, exist_ok=True)
    save3(to_rgba(street_shot(0, 150, rain_seed=100)), 'mock_walk_start_3x.png')
    save3(to_rgba(street_shot(640, 915, rain_seed=117)), 'mock_walk_poster_3x.png')
    rg = to_rgba(street_shot(640, 915, rain_seed=134))
    dialogue(rg)
    save3(rg, 'mock_walk_poster_dialogue_3x.png')
    pc = Canvas.load('out/poster_closeup.png')
    rg = to_rgba(pc)
    dialogue(rg)
    save3(rg, 'mock_poster_closeup_dialogue_3x.png')
    print('ok')
