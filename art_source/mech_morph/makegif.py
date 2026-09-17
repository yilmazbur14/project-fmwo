from pngio import *
from gifw import write_gif
import sys
G=(92,140,84,255)
w,h,px=read_png('morph_strip.png')
frames=[scale(crop(px,i*96,0,96,96),3,G) for i in range(8)]
dur=[260,130,130,110,110,120,220,700]
write_gif('morph_preview_3x.gif',frames,dur)
# roundtrip check: decode not available; print size
import os; print(os.path.getsize('morph_preview_3x.gif'))
