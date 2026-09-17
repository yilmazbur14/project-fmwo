"""Place Burak's cutscene frames on the finished street layers (3x mockups)."""
import sys
sys.path.insert(0, '../cutscene_env')
from pngio import read_png, write_png, upscale

A = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Cutscenes/Intro/'
FEET = 262
HIP_X = 30

sky = read_png(A + 'street_sky.png')
bld = read_png(A + 'street_buildings.png')
fg = read_png(A + 'street_fg.png')
rain = read_png(A + 'rain_overlay.png')
burak = read_png(A + 'burak_cutscene.png')


def blend(dst, p):
    a = p[3]
    if a == 0:
        return dst
    if a == 255:
        return p
    t = a / 255.0
    return tuple(int(round(dst[i] * (1 - t) + p[i] * t)) for i in range(3)) + (255,)


def layer(canvas, img, sx, sy, x0=0, fw=None):
    w, h, pix = img
    fw = fw or w
    for y in range(360):
        yy = y - sy
        if not 0 <= yy < h:
            continue
        for x in range(640):
            xx = x - sx
            if 0 <= xx < fw:
                canvas[y][x] = blend(canvas[y][x], pix[yy][x0 + xx])


def shot(cam, hip_x, frame, rain_frame, name):
    c = [[(0, 0, 0, 255)] * 640 for _ in range(360)]
    layer(c, sky, -int(round(cam * 0.25)), 0)
    layer(c, bld, -cam, 0)
    layer(c, burak, hip_x - cam - HIP_X, FEET - 63, x0=frame * 64, fw=64)
    layer(c, fg, -cam, 0)
    layer(c, rain, 0, 0, x0=rain_frame * 640, fw=640)
    W, H, big = upscale(640, 360, c, 3)
    write_png('mock/' + name, W, H, big)


shot(0, 300, 3, 0, 'mock_burak_walk_gloomy_3x.png')
shot(640, 915, 11, 1, 'mock_burak_notice_3x.png')
shot(640, 915, 16, 2, 'mock_burak_resolve_3x.png')
print('ok')
