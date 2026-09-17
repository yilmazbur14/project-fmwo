"""cmp3x.py OUT grid_or_png[:frame] ... -> side by side at 3x on light bg + dark bg rows"""
import sys
from lib import *
R = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/'
def load(spec):
    fr = 0
    if spec.endswith('.txt') or '.txt:' in spec:
        path = spec.split(':')[0] if spec.count(':') > 1 and not spec[1] == ':' else spec
        return grid_to_pix(load_grid(spec))
    if '@' in spec:
        spec, fr = spec.split('@'); fr = int(fr)
    w, h, p = read_png(spec if ':' in spec[:3] else R + spec)
    return crop_pix(p, fr * 64, 0, 64, 64)
out = sys.argv[1]
s = int(sys.argv[2])
imgs = [zoom(load(a), s, bg=(236, 236, 240, 255)) for a in sys.argv[3:]]
dark = [zoom(load(a), s, bg=(52, 56, 66, 255)) for a in sys.argv[3:]]
top = hcat(imgs); bot = hcat(dark)
save(out, top + bot)
print('wrote', out)
