"""Carter's face, traced from Assets/Characters/Carter/carter_redesign.png
and scaled to the 30px head: heavy furrowed brows, a flat deadpan lid slit,
a flat unimpressed mouth, the cross earring.  The only change is the eye -
the Satsui no Hado burns the pupils out and leaves red glow in the slit.

'.' leaves whatever is underneath.  Palette chars come from lib.PAL.
"""

# anchored at x=36, y=22   (24 wide: x 36..59, mirror pairs across x=47.5)
BROWS = """
55555..............55555
6555555..........5555556
.66555555......55555566.
"""

# anchored at x=36, y=26
# 2 rows of heavy black lid over a 2-row glowing slit: Carter's deadpan
# proportions with the sclera replaced by Satsui no Hado red.
EYES = """
.kkkkkkkk......kkkkkkkk.
.kkkkkkkk......kkkkkkkk.
.kVOOOOVk......kVOOOOVk.
.k777777k......k777777k.
..kwwwwk........kwwwwk..
...vvvv..........vvvv...
"""

# anchored at x=45, y=27
NOSE = """
..tuv.
..tuv.
.stuvw
.stuvw
.sttvw
.wkkwv
..vww.
"""

# anchored at x=44, y=35
MOUTH = """
.555555.
kkkkkkkk
k444444k
.566665.
"""

# cross earring hanging off the left lobe - anchored at x=30, y=32
EARRING = """
...k...
...k...
..kkk..
..k#k..
kkk#kkk
k##%##k
kkk&kkk
..k&k..
..kkk..
"""
