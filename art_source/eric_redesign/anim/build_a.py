"""render all designer-A frames, write part_a.png (40x128 strip, only A indices), previews, gifs"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tools
from pngio import write_png, blank, paste, scale
A = list(range(0, 13)) + list(range(21, 32))
imgs = tools.render(A)
sheet = blank(40 * 128, 128, (0, 0, 0, 0))
for i in A:
    paste(sheet, imgs[i], i * 128, 0)
write_png('../part_a.png', 40 * 128, 128, sheet)
# 3x strips (two rows so they stay viewable)
tools.strip(imgs, list(range(0, 13)), 3, 'strip3x_eq.png')
tools.strip(imgs, list(range(21, 32)), 3, 'strip3x_idle_down.png')
# gifs at the old scene timings
eq_t = [0.16666667, 0.08333333, 0.08333334, 0.08333334, 0.08333333, 0.08333334, 0.08333333, 0.08333333, 0.08333334, 0.08333333, 0.08333333]
tools.gif(imgs, list(range(0, 11)), eq_t, 'gif_earthquake.gif')
tools.gif(imgs, [11, 12, 21], [0.0833, 0.0833, 0.25], 'gif_post_slam.gif')
tools.gif(imgs, list(range(0, 13)) + [21, 22, 23, 24], eq_t + [0.0833, 0.0833, 0.25, 0.25, 0.25, 0.25], 'gif_earthquake_full.gif')
tools.gif(imgs, [21, 22, 23, 24], [0.25] * 4, 'gif_idle.gif')
tools.gif(imgs, [21, 22, 23, 24, 25, 26, 21, 22, 23, 24], [0.25] * 10, 'gif_idle_variants.gif')
tools.gif(imgs, [27, 28, 29, 30, 31], [0.2] * 5, 'gif_downed.gif')
import pickle
pickle.dump(imgs, open('frames_a.pkl', 'wb'))
print('ok', len(A))
