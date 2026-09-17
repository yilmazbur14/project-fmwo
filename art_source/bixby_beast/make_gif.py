"""Hover loop GIF preview: beast frames over their shadow on the arena floor colour, at 3x."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png, crop, scale, blank, paste
from gifio import write_gif
import view

FLOOR = (136, 180, 99, 255)
SHADOW_ALPHA = 0.38


def blend_shadow(dst, sh, ox, oy):
    for y, row in enumerate(sh):
        for x, p in enumerate(row):
            if p[3] == 0:
                continue
            yy, xx = oy + y, ox + x
            if 0 <= yy < len(dst) and 0 <= xx < len(dst[0]):
                q = dst[yy][xx]
                dst[yy][xx] = tuple(int(round(q[i] * (1 - SHADOW_ALPHA))) for i in range(3)) + (255,)


def main(strip_path, shadow_path, out_path, fw=192, fh=160, n=4, delays=(12, 10, 12, 10), hover_gap=22, s=3):
    w, h, px = read_png(strip_path)
    sw, shh, spx = read_png(shadow_path)
    frames = []
    W, H = fw + 16, fh + hover_gap + 30
    for i in range(n):
        cv = blank(W, H, FLOOR)
        sh = crop(spx, 192 * i, 0, 192, 48)
        # shadow centre (96, 25) placed hover_gap texels below the hover anchor (96, 152)
        blend_shadow(cv, sh, 8 + 96 - 96, 4 + 152 + hover_gap - 25)
        paste(cv, crop(px, fw * i, 0, fw, fh), 8, 4)
        frames.append(scale(cv, s))
    write_gif(out_path, frames, list(delays))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
    print('ok')
