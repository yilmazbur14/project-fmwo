"""preview: python pv2.py name,name [scale] [out.png] [crop x,y,w,h]"""
import os
import sys
import frames2
from pngio import write_png, scale, blank, paste, crop

FL = (136, 180, 99, 255)
VIEWS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'views')


def on_bg(px, bg=FL):
    return [[(p if p[3] else bg) for p in row] for row in px]


def strip(imgs, s, path, pad=6):
    h, w = len(imgs[0]), len(imgs[0][0])
    W = pad + len(imgs) * (w * s + pad)
    H = h * s + 2 * pad
    cv = blank(W, H, FL)
    for k, im in enumerate(imgs):
        paste(cv, scale(im, s), pad + k * (w * s + pad), pad)
    write_png(path, W, H, cv)


def zoom(px, s, path, region=None):
    if region:
        px = crop(px, *region)
    z = scale(on_bg(px), s)
    write_png(path, len(z[0]), len(z), z)


if __name__ == '__main__':
    names = sys.argv[1].split(',')
    s = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    out = sys.argv[3] if len(sys.argv) > 3 else 'pv.png'
    region = tuple(int(v) for v in sys.argv[4].split(',')) if len(sys.argv) > 4 else None
    imgs = []
    for n in names:
        fr = frames2.F[n]()
        frames2.B.seal(fr)
        px = fr.rgba()
        imgs.append(crop(px, *region) if region else px)
    strip(imgs, s, os.path.join(VIEWS, out))
    print('ok', out)
