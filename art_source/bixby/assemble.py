"""Assemble layers: body -> side heads -> centre head -> overlay. Writes previews."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from canvas import *
from palette import PAL
from pngio import upscale, write_png

BODY = sys.argv[1] if len(sys.argv) > 1 else 'body_auto'
TAG = sys.argv[2] if len(sys.argv) > 2 else 'wip'
COLLARS = [('collar_l', 5, 33), ('collar_r', 42, 33)]
HEADS = [('head_l', 3, 14), ('head_r', 36, 14), ('head_c', 18, 1)]

def assemble(body=BODY, overlay='overlay'):
    g = [list(r) for r in load_rows(os.path.join(HERE, 'parts', body + '.txt'))]
    for name, ox, oy in COLLARS + HEADS:
        stamp(g, load_rows(os.path.join(HERE, 'parts', name + '.txt')), ox, oy)
    ov = os.path.join(HERE, 'parts', overlay + '.txt')
    if os.path.exists(ov):
        stamp(g, load_rows(ov), 0, 0)
    return g

if __name__ == '__main__':
    g = assemble()
    save_rows(os.path.join(HERE, TAG + '.txt'), g)
    save_png(os.path.join(HERE, TAG + '_8x.png'), g, PAL, 8, bg='checker')
    save_png(os.path.join(HERE, TAG + '_1x.png'), g, PAL, 1)
    pix = to_pix(g, PAL)
    W3, H3, o3 = upscale(64, 64, pix, 3, bg=(40, 44, 52, 255))
    write_png(os.path.join(HERE, TAG + '_3x.png'), W3, H3, o3)
    print('ok')
