"""Build the final 640x360 intro background and run QA checks."""
from collections import Counter
from compose import compose
from pngio import read_png, write_png, scale, crop
from canvas import RGB2KEY
import danny, papers, bg

cv = compose()
cv.save('DannyIntro_pixel.png')
w, h, rows = read_png('DannyIntro_pixel.png')
assert (w, h) == (640, 360), (w, h)
c = Counter(px for row in rows for px in row)
bad = [p for p in c if p[:3] not in RGB2KEY or p[3] != 255]
assert not bad, bad
px, layer = danny.build()
dy = max(y for (x, y) in px) + danny.ORIGIN[1]
top, apron = bg.desk_masks()
assert dy < 270 and max(y for x, y in top) < 270 and max(s[3] for s in papers.SHEETS) + 2 < 270
print('OK: 640x360, %d DB32 colours, Danny max y %d, desk top max y %d, papers max y %d'
      % (len(c), dy, max(y for x, y in top), max(s[3] for s in papers.SHEETS) + 2))
write_png('final_full_2x.png', scale(rows, 2))
write_png('final_center_3x.png', scale(crop(rows, 170, 25, 470, 275), 3))
