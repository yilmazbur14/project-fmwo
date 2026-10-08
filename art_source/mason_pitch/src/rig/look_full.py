import sys; sys.dont_write_bytecode = True
import importlib
from view import to_img, zoom, strip
from PIL import Image
mod = importlib.import_module(sys.argv[1])
names = sys.argv[2:] or [n for n, _ in mod.FRAMES]
poses = dict(mod.FRAMES)
z = int(__import__('os').environ.get('Z', '6'))
imgs = [zoom(to_img(mod.render(poses[n])), z) for n in names]
rows = [imgs[i:i + 5] for i in range(0, len(imgs), 5)]
ss = [strip(r) for r in rows]
W = max(s.width for s in ss); H = sum(s.height + 4 for s in ss)
out = Image.new('RGBA', (W, H), (70, 70, 80, 255)); y = 0
for s in ss:
    out.alpha_composite(s, (0, y)); y += s.height + 4
out.save('../../look_full.png')
