import glob, colorsys, os
from png import read_png
root = r'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters'
seen = {}
for f in glob.glob(root + '/*/*.png'):
    rel = os.path.relpath(f, root).replace(os.sep, '/')
    try:
        w, h, px = read_png(f)
    except Exception:
        continue
    for row in px:
        for p in row:
            if p[3] == 0: continue
            hh, ss, vv = colorsys.rgb_to_hsv(p[0] / 255, p[1] / 255, p[2] / 255)
            if 0.20 < hh < 0.45 and ss > 0.3 and vv > 0.3:
                k = '#%02X%02X%02X' % p[:3]
                seen.setdefault(k, set()).add(rel)
for k, v in sorted(seen.items()):
    print(k, sorted(v))
