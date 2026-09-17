"""Composite the UI-kit mock-up over the new background and drop the new keycaps into the navy cards.
Read-only use of the UI designer's mock; all outputs go to controls/out/."""
import os
from pngio import read_png, write_png

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
UK = os.path.join(HERE, '..', 'ui_kit', 'final')
S = 3

mw, mh, mock = read_png(os.path.join(UK, 'test_cards_buttons_t.png'))
bw, bh, bgp = read_png(os.path.join(HERE, 'final', 'controls_bg.png'))
assert (mw, mh) == (bw * S, bh * S)
CHECKER = {(0xaa, 0xaa, 0xaa, 255), (0xc8, 0xc8, 0xc8, 255)}
NAVY = (0x22, 0x20, 0x34, 255)

out = [row[:] for row in mock]
# keep only the first "I'm ready!" button; the other two are hover/pressed state samples
for y in range(860, 990):
    for x in range(500, 1400):
        out[y][x] = (0xaa, 0xaa, 0xaa, 255)
# clear the old key icons inside the cards (panel fill is flat navy)
for (x0, y0, x1, y1) in [(216, 484, 377, 609), (763, 496, 876, 615), (1283, 496, 1396, 615)]:
    for y in range(y0 - 2, y1 + 3):
        for x in range(x0 - 2, x1 + 3):
            out[y][x] = NAVY
# background shows wherever the mock is checkerboard
for y in range(mh):
    for x in range(mw):
        if out[y][x] in CHECKER:
            out[y][x] = bgp[y // S][x // S]


def paste_key(name, cx, cy):
    w, h, px = read_png(os.path.join(HERE, 'final', name))
    # snap to the 3x grid so key pixels line up with background pixels
    ox = int(round((cx - w * S / 2) / S)) * S
    oy = int(round((cy - h * S / 2) / S)) * S
    for y in range(h * S):
        for x in range(w * S):
            p = px[y // S][x // S]
            if p[3]:
                out[oy + y][ox + x] = p


paste_key('key_arrows.png', 296.5, 546.5)
paste_key('key_q.png', 819.5, 555.5)
paste_key('key_w.png', 1339.5, 555.5)
write_png(os.path.join(OUT, 'uikit_layout_3x.png'), mw, mh, out)

# close-ups at game scale: right strip + third card, left strip + first card
def crop(x0, y0, x1, y1, name):
    write_png(os.path.join(OUT, name), x1 - x0, y1 - y0, [row[x0:x1] for row in out[y0:y1]])


crop(1080, 0, 1920, 1080, 'uikit_right_3x.png')
crop(0, 0, 700, 1080, 'uikit_left_3x.png')
print('ok')
