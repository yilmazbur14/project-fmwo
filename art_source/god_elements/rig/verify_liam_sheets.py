"""Prove the scratch Liam rig rebuilds every live sheet the puppet set twins, pixel-identically."""
import os, sys
from ge_common import *
import le_full as F, le_build as LB
import le_a34poses3 as Q
from imgdiff import pixel_diff
LIVE = CHARS + '/Liam/Elements/'
q = {n: fn for n, fn, *_ in Q.ALL}
f = {n: fn for n, fn, _t in F.SHEETS if fn}
ok = True
for name in ('channel', 'blow', 'ignite', 'cast_left', 'cast_right', 'slam_rise', 'wobble', 'fall', 'downed', 'defeat', 'juggle'):
    if name == 'juggle':
        frames, info = F.juggle()
    elif name in q:
        frames = [c for c, _ in q[name]()]
    else:
        frames = [c for c, _ in f[name]()]
    im = LB.strip(frames)
    d = pixel_diff(im, Image.open(LIVE + 'liam_%s.png' % name))
    print(name, len(frames), frames[0].shape, 'IDENTICAL' if not d else d)
    ok &= not d
print('ALL IDENTICAL' if ok else 'MISMATCH')
