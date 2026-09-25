"""Build the deliverable sprite strips: 2 frames of 80x80 laid out horizontally (hframes=2)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jlib import W, H, to_rgba
from pngio import write_png
import frames

ASSET = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Josh/'


def strip(shades_up=True):
    fs = [frames.frame0(shades_up=shades_up), frames.frame1(shades_up=shades_up)]
    sheet = [[(0, 0, 0, 0)] * (W * len(fs)) for _ in range(H)]
    for i, c in enumerate(fs):
        g = to_rgba(c)
        for y in range(H):
            for x in range(W):
                sheet[y][i * W + x] = g[y][x]
    return sheet, W * len(fs), H


if __name__ == '__main__':
    # SUPERSEDED 2026-09-23: josh_cards.png is now built by art_source/josh_redesign/export.py. Run
    # bare, this script used to write the OLD design over the shipped sprite, so it now needs an
    # explicit output folder and refuses the shipped one.
    if len(sys.argv) < 2 or os.path.normcase(os.path.abspath(sys.argv[1])).rstrip('\\/') \
            == os.path.normcase(os.path.abspath(ASSET)).rstrip('\\/'):
        sys.exit('superseded rig: pass an output folder other than Assets/Characters/Josh '
                 '(josh_cards.png comes from art_source/josh_redesign/export.py)')
    # The user picked shades-up; that is the only sprite we ship.  The shades-down look still
    # exists behind head.build(shades_up=False) if it is ever wanted again.
    out = sys.argv[1] if len(sys.argv) > 1 else ASSET
    sheet, w, h = strip()
    p = (out + '/josh_cards.png').replace('//', '/')
    write_png(p, w, h, sheet)
    print('wrote', p, w, 'x', h)
