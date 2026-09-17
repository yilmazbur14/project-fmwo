"""Render one part-B v2 frame in its own process and pickle its RGBA pixels (robust against interpreter crashes)."""
import sys
import pickle
import faulthandler
faulthandler.enable()
from base2 import *

i = int(sys.argv[1])
out = sys.argv[2]
if 13 <= i <= 20:
    import whirl2
    fr = whirl2.whirl_frame(i)
else:
    import throw2
    fr = throw2.FRAMES[i]()
pickle.dump(fr.rgba(), open(out, 'wb'))
extra = ''
if i == 34:
    extra = str(throw2.RELEASE)
if i == 39:
    extra = str(throw2.CATCH)
print('ok', i, extra)
