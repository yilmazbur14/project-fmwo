"""The one place Carter's drawn size lives.

He shipped at 288px on screen (96 rows of a 96x96 frame at the scene's scale 3)
- the same height as the redesigned Greyson, who is meant to be the wall of the
game, and 60px taller than Josh.  The frame, the strip layout, the feet plane
on row 95 and the mirror axis x' = 95 - x are all unchanged; he is simply drawn
smaller inside the frame, so the scene maths, the sheet layouts and the
hand-over frames all still hold and only the measured numbers move.

    0.84  ->  81 rows drawn  ->  243px on screen

which sits between Josh (76 rows, 228px) and Greyson (96 rows, 288px), and
leaves him reading as the heaviest thing in the ring without being the tallest.

Every build script calls apply() before it draws anything.  Nothing else should
set the scale, or his sheets will disagree with each other mid-fight.
"""
SCALE = 0.84
ANCHOR = (47.5, 96.0)          # mirror axis, floor plane


def apply():
    import lib
    lib.set_scale(SCALE, ANCHOR)
    return SCALE
