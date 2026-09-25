"""Shared setup for Bixby's juggle sheet.

Imports the approved beast rig in art_source/bixby_redesign READ-ONLY (it is never edited; new work
lives in this folder), and fixes the juggle frame: its size, the feet texel for the ground frames, the
pivot the air frames turn round, and where previews go (the scratchpad, never Assets).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
RIG = os.path.join(ART, 'bixby_redesign')
ROOT = os.path.dirname(ART)
for p in (ART, RIG, HERE):
    if p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)
# (HERE first, then the rig, then art_source for imgdiff; none of this folder's module names shadow
# a rig module's)

BIXBY = os.path.join(ROOT, 'Assets', 'Characters', 'Bixby')
SCRATCH = ('C:/Users/theyi/AppData/Local/Temp/claude/C--Users-theyi-OneDrive-Documents-new-game-project/'
           'a7fc2846-afef-472d-979b-e17143793a0f/scratchpad/juggle/bixby/')

# The rig's own frame: 192x160, feet on (96, 151), symmetry axis x = 95.5.
LOCAL_W, LOCAL_H = 192, 160
LOCAL_FEET = (96, 151)

# The juggle frame. Big enough for the whole beast at any turn with the wings out: from the pivot his
# farthest texel is a raised wingtip about 127 texels away, so the air frames' pivot needs that much
# room on every side it can swing to.
W, H = 256, 256
FEET = (128, 200)                # the ground frames' feet texel (0, 7-11)
LOCAL_PIVOT = (96, 96)           # his middle in his own frame: the chest, where his mass is
# Where the air frames put that middle: the finisher's camera follows it.
TUMBLE_CENTRE = (128, 136)
# local -> juggle frame for a ground frame drawn upright
GROUND_OFFSET = (FEET[0] - LOCAL_FEET[0], FEET[1] - LOCAL_FEET[1])

N_FRAMES = 12
