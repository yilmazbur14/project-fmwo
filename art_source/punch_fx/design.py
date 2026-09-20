"""The punch FX designs and the geometry they share with the punch hitbox.

Everything is in the player's own texels (player_4dir_sheet.png draws at 2x). Local coordinates are
texels from the centre of a 32x32 player frame, x right and y down, the same space as
PlayerScript.PUNCH_HITBOXES.

THE SWOOSH is drawn once, in punch space, and turned to each facing:
  a  runs along the punch, 0 at the back of the reach box and 10 at its far edge;
  c  runs across it, 0..5, drawn for the right punch with c=0 on top.
A pixel at (a, c) covers one texel of the facing's v2 box (V2_BOXES), so the full-extension frame
fills the box's far edge and both of its sides exactly: what the swoosh shows is what the punch hits.
The left punch is the right one mirrored, as the player's sheet mirrors it; up and down are the right
one turned a quarter turn, which for a design symmetric across the arm is the same as mirroring.
"""

# The proposed reach boxes, in texels from the player's frame centre. Each contains today's box and
# reaches 3 texels (6 px) further: right/left 13 -> 16, up 18 -> 21, down 19 -> 22; 6 texels across
# instead of 4.33. Facing order is PlayerScript.Facing: DOWN, UP, LEFT, RIGHT.
V2_BOXES = {
    0: (-2, 11, 6, 11),     # DOWN   x -2..4,  y 11..22
    1: (-7, -21, 6, 11),    # UP     x -7..-1, y -21..-10
    2: (-16, -9, 11, 6),    # LEFT   x -16..-5, y -9..-3
    3: (5, -9, 11, 6),      # RIGHT  x 5..16,  y -9..-3
}
# Today's boxes, for the mockups' red outlines (PlayerScript.PUNCH_HITBOXES).
CURRENT_BOXES = {
    0: (-1.665, 11.33, 4.33, 7.67),
    1: (-6.165, -18.0, 4.33, 7.67),
    2: (-13.0, -8.165, 7.67, 4.33),
    3: (5.33, -8.165, 7.67, 4.33),
}
FACINGS = ['down', 'up', 'left', 'right']
ALONG = 11
ACROSS = 6


def texel_of(facing, a, c):
    """Local texel (its top-left corner) that punch-space pixel (a, c) lands on for `facing`."""
    x, y, w, h = V2_BOXES[facing]
    if facing == 3:          # right: along +x, across +y
        return x + a, y + c
    if facing == 2:          # left: the right punch mirrored
        return x + w - 1 - a, y + c
    if facing == 1:          # up: along -y, across +x
        return x + c, y + h - 1 - a
    return x + w - 1 - c, y + a   # down: along +y, across -x


# DB32 letters used here.
PAL = {
    'W': (255, 255, 255),   # white: the leading edge
    'P': (203, 219, 252),   # pale blue-white
    'C': (95, 205, 228),    # cyan
    'b': (99, 155, 255),    # blue
    'B': (91, 110, 225),    # deeper blue
    'I': (63, 63, 116),     # indigo, the rim that keeps white readable over white armour
    'K': (0, 0, 0),         # outline (the star)
    'Y': (251, 242, 54),    # yellow (the charged star)
    'O': (223, 113, 38),    # orange (the charged star)
}

# The swoosh, punch space, right-punch orientation: rows are c (0 = top), columns are a (0 = back).
# Frame 0 plays on sheet column 7 (the arm snapping out), frame 1 on column 8 (full extension),
# frame 2 once the arm is back, over the reach it just covered.
SWOOSH = [
    [  # 0: launch. The fist is at a=1..2 (a=0..1 punching up); a small crescent hugs its front.
        "...........",
        "..bPW......",
        "....bW.....",
        "....bW.....",
        "..bPW......",
        "...........",
    ],
    [  # 1: full extension. The fist is at a=3..5. A crescent moon whose apex is the far edge (a=10)
       # and whose horns trail back beside the fist, spanning the box's width (c=0..5). White for the
       # green floor, a blue inner rim so it still reads over white armour.
        "....bCP....",
        "......bWWW.",
        ".......bWWW",
        ".......bWWW",
        "......bWWW.",
        "....bCP....",
    ],
    [  # 2: the afterimage: a thinner crescent, still marking the far edge and the width.
        ".......b...",
        "........bP.",
        ".........bP",
        ".........bP",
        "........bP.",
        ".......b...",
    ],
]
