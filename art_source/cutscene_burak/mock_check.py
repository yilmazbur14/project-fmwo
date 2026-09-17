"""Reuse mock_street.py's compositing on a scratch strip.
python mock_check.py strip.png out_prefix cam hip frame[,frame...] [rainframe]
Writes <prefix>_f<frame>_3x.png full shots and <prefix>_crop_3x.png (poster region, frames side by side)."""
import sys, os
sys.path.insert(0, '../cutscene_env')
from pngio import read_png, write_png, upscale

A = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Cutscenes/Intro/'
FEET = 262
HIP_X = 30

sky = read_png(A + 'street_sky.png')
bld = read_png(A + 'street_buildings.png')
fg = read_png(A + 'street_fg.png')
rain = read_png(A + 'rain_overlay.png')


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


def shot(burak, cam, hip_x, frame, rain_frame):
    c = [[(0, 0, 0, 255)] * 640 for _ in range(360)]
    layer(c, sky, -int(round(cam * 0.25)), 0)
    layer(c, bld, -cam, 0)
    layer(c, burak, hip_x - cam - HIP_X, FEET - 63, x0=frame * 64, fw=64)
    layer(c, fg, -cam, 0)
    layer(c, rain, 0, 0, x0=rain_frame * 640, fw=640)
    return c


if __name__ == '__main__':
    strip, prefix, cam, hip = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    frames = [int(f) for f in sys.argv[5].split(',')]
    rain_frame = int(sys.argv[6]) if len(sys.argv) > 6 else 1
    burak = read_png(strip)
    crops = []
    for f in frames:
        c = shot(burak, cam, hip, f, rain_frame)
        W, H, big = upscale(640, 360, c, 3)
        write_png('%s_f%02d_3x.png' % (prefix, f), W, H, big)
        # poster region crop: x 220..380, y 150..270 (screen coords at 1x)
        crops.append([row[220:380] for row in c[150:270]])
    tri = []
    for y in range(120):
        row = []
        for k, cr in enumerate(crops):
            row += cr[y] + ([(255, 0, 255, 255)] if k < len(crops) - 1 else [])
        tri.append(row)
    W, H, big = upscale(len(tri[0]), len(tri), tri, 3)
    write_png('%s_crop_3x.png' % prefix, W, H, big)
    print('ok', W, H)
