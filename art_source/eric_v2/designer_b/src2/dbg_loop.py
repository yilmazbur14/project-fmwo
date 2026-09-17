import sys, faulthandler, gc
faulthandler.enable()
from base2 import *
import whirl2
for i in range(13, 21):
    print('frame', i, flush=True)
    whirl2.whirl_frame(i)
    print('  ok', flush=True)
