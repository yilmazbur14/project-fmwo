"""preview / export helpers"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import importlib
from pngio import write_png, scale, blank, paste, read_png, crop
from gifio import write_gif

FL = (136, 180, 99, 255)
GROUND = (104, 140, 76, 255)


def render(indices):
    import frames
    importlib.reload(frames)
    out = {}
    for i in indices:
        out[i] = frames.FRAMES[i]().rgba()
    return out


def on_bg(px, bg=FL):
    return [[(p if p[3] else bg) for p in row] for row in px]


def strip(imgs, order, s, path, pad=6, ground=True):
    fw = 128 * s
    W = pad + len(order) * (fw + pad)
    H = fw + 2 * pad
    canvas = blank(W, H, FL)
    if ground:
        for y in range(pad + fw, H):
            for x in range(W):
                canvas[y][x] = GROUND
    for k, i in enumerate(order):
        paste(canvas, scale(imgs[i], s), pad + k * (fw + pad), pad)
    write_png(path, W, H, canvas)


def zoom(px, s, path, region=None):
    if region:
        px = crop(px, *region)
    z = scale(on_bg(px), s)
    write_png(path, len(z[0]), len(z), z)


def gif(imgs, order, durations, path, s=3):
    frames_ = [scale(on_bg(imgs[i]), s) for i in order]
    write_gif(path, [[[p[:3] for p in row] for row in f] for f in frames_], [max(2, int(round(d * 100))) for d in durations])


if __name__ == '__main__':
    idx = [int(a) for a in sys.argv[1].split(',')]
    s = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    imgs = render(idx)
    strip(imgs, idx, s, sys.argv[3] if len(sys.argv) > 3 else 'preview.png')
