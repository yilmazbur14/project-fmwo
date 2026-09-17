"""Preview helpers: python preview.py strip.png [frame] [x0] [w] [zoom]"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pngio import read_png, write_png, scale

BG = (0, 0, 0, 255)


def load(path):
    w, h, px = read_png(path)
    return w, h, px


def frame(px, i, fw=640, fh=40):
    return [row[i * fw:(i + 1) * fw] for row in px[:fh]]


def flat(px, bg=BG):
    return [[p if p[3] else bg for p in row] for row in px]


if __name__ == '__main__':
    path = sys.argv[1]
    mode = sys.argv[2]
    w, h, px = load(path)
    nf = w // 640
    outdir = os.path.join(HERE, 'prev')
    os.makedirs(outdir, exist_ok=True)
    if mode == 'stack3':
        # all frames stacked vertically at 3x with a 6px grey separator
        rows = []
        for i in range(nf):
            fr = flat(frame(px, i))
            big = scale(fr, 3)
            rows.extend(big)
            rows.extend([[(60, 60, 60, 255)] * 1920 for _ in range(6)])
        write_png(os.path.join(outdir, 'stack3.png'), 1920, len(rows), rows)
    elif mode == 'zoom':
        i, x0, cw, z = int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
        fr = flat(frame(px, i))
        c = [row[x0:x0 + cw] for row in fr]
        big = scale(c, z)
        name = sys.argv[7] if len(sys.argv) > 7 else f'z_f{i}_x{x0}_{z}x.png'
        write_png(os.path.join(outdir, name), cw * z, 40 * z, big)
    elif mode == 'zoomframes':
        # same crop from every frame, stacked, for animation checking
        x0, cw, z = int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
        rows = []
        for i in range(nf):
            fr = flat(frame(px, i))
            c = [row[x0:x0 + cw] for row in fr]
            rows.extend(scale(c, z))
            rows.extend([[(90, 90, 90, 255)] * (cw * z) for _ in range(z)])
        name = sys.argv[6] if len(sys.argv) > 6 else f'zf_x{x0}_{z}x.png'
        write_png(os.path.join(outdir, name), cw * z, len(rows), rows)
    print('ok')
