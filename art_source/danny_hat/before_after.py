"""Before/after 6x close-ups of every file whose hat was recoloured (before/ holds the pre-recolour copies)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', 'le_src')))
from pngio import read_png, write_png, crop, scale, blank, paste

DANNY = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Danny'
S = 6
BG = (34, 36, 44, 255)
PANEL = (96, 112, 104, 255)

CROPS = {
    'danny.png': (0, 0, 128, 64),
    'portrait.png': (0, 0, 64, 64),
    'DannyDialogue.png': (24, 0, 40, 32),
    'DannyIntro_pixel.png': (272, 30, 104, 62),
    'DannyIntro.png': (860, 90, 240, 160),
}


def sheet(name):
    x, y, w, h = CROPS[name]
    a = crop(read_png(os.path.join(HERE, 'before', name))[2], x, y, w, h)
    b = crop(read_png(os.path.join(DANNY, name))[2], x, y, w, h)
    gap = 8
    W = (w * 2) * S + gap * 3
    H = h * S + gap * 2
    out = blank(W, H, BG)
    paste(out, scale([[tuple(p) for p in row] for row in a], S, PANEL), gap, gap)
    paste(out, scale([[tuple(p) for p in row] for row in b], S, PANEL), gap * 2 + w * S, gap)
    path = os.path.join(HERE, '%s_before_after_6x.png' % name[:-4])
    write_png(path, W, H, out)
    return path


if __name__ == '__main__':
    for n in CROPS:
        print(sheet(n))
