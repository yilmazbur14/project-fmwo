"""matt_aim_dot.png: one dot of the Trueshot aim line. 2 frames of 3x3:
  frame 0   dim gold, while the aim tracks the player
  frame 1   lit white-gold, from the lock (the line flashes white) to the release
The code places one every 24 px along the line. The pivot is the centre texel (1, 1), the frame's centre,
so it needs no offset. A plus shape: at 3x it is a 9 px cross that stays a dot, not a square, on the mat.
"""
FRAME_SIZE = (3, 3)
NOTE = '2 frames: f0 dim gold (tracking), f1 lit white-gold (locked)'

DIM = ['.A.',
       'AOA',
       '.A.']
LIT = ['.Y.',
       'YHY',
       '.Y.']


def frames():
    return [list(DIM), list(LIT)]
