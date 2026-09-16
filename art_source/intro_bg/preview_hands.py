import danny
from bg import build_background
from pngio import read_png, write_png, scale, crop
cv0, _, _ = build_background()
import copy
outs = []
for v in ['D', 'E']:
    danny.HAND = v
    cv = copy.deepcopy(cv0)
    danny.to_canvas(cv, danny.build())
    rows = cv.to_rgba()
    outs.append(crop(rows, 262, 90, 390, 150))
# stack vertically
stack = outs[0] + [[(255, 0, 255, 255)] * len(outs[0][0])] + outs[1]
write_png('hands_preview_5x.png', scale(stack, 5))
