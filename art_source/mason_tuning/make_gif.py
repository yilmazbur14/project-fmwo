"""Turn the burst frames shoot_mason_tuning.gd leaves in ./out into one GIF.

    python make_gif.py [out/mason_poo_line.gif]

The shooter saves every 3rd frame of a 60 fps run, so the GIF plays at 20 fps.
"""
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'mason_nuggets'))
from pngio import read_png
from gifio import write_gif

OUT = os.path.join(HERE, 'out')
DELAY_CS = 5

frames = []
for path in sorted(glob.glob(os.path.join(OUT, 'mason_burst_*.png'))):
    _, _, pixels = read_png(path)
    frames.append(pixels)
if not frames:
    raise SystemExit('no burst frames in %s' % OUT)

colours = {tuple(p[:3]) for frame in frames for row in frame for p in row}
print('%d frames, %dx%d, %d colours' % (len(frames), len(frames[0][0]), len(frames[0]), len(colours)))

target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUT, 'mason_poo_line.gif')
write_gif(target, frames, [DELAY_CS] * len(frames))
print('wrote', target, '%.1f KB' % (os.path.getsize(target) / 1024.0))
