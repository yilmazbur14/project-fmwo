"""Zoomed crops of several frames side by side: python zoom.py <sheet> x0 y0 x1 y1 [scale] [frames]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib, sheet_tools as st
import anims_ground as ag
from PIL import Image

def main():
    name = sys.argv[1]
    x0, y0, x1, y1 = map(int, sys.argv[2:6])
    s = int(sys.argv[6]) if len(sys.argv) > 6 else 12
    fn, n, _ = ag.SHEETS[name]
    idx = [int(v) for v in sys.argv[7].split(',')] if len(sys.argv) > 7 else list(range(n))
    tiles = []
    for i in idx:
        im = st.to_image(fn(i)).crop((x0, y0, x1 + 1, y1 + 1))
        tiles.append(lib.grid(im, s, major=5))
    w = sum(t.width for t in tiles) + 6 * (len(tiles) - 1)
    out = Image.new('RGBA', (w, tiles[0].height), (10, 10, 12, 255))
    x = 0
    for t in tiles:
        out.paste(t, (x, 0)); x += t.width + 6
    out.save(os.path.join(st.WIP, 'zoom_%s.png' % name))

main()
