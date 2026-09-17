"""Hand-drawn parts for the idle. Each part: (x0, y0, rows). '.' keeps what is underneath, '_' erases."""

# Near (flexing) fist: knuckles up/toward head, curled fingers facing viewer, thumb across the front
NEAR_FIST = (4, 8, [
    "...######...",
    "..#1aaass#..",
    ".#aaassssd#.",
    "#aasssssddf#",
    "#asssssdsdf#",
    "#sssfsfsfdf#",
    "#sssfsfsfff#",
    ".#dsdddddf#.",
    "..#ddffff#..",
    "...######...",
])

# Far fist planted on the hip (seen from outside): back of hand + finger rolls
FAR_FIST = (41, 42, [
    "..#####....",
    ".#ssaas#...",
    "#sssssdd#..",
    "#sdsdsdf#..",
    "#dfdfdff#..",
    "#dfdfdff#..",
    ".#######...",
])

SPEEDO = (19, 43, [
    "..#########################..",
    ".#oOOOOOOOOOOOOOOOOOOOOpppP#.",
    ".#pppppppppppppppppppppPPPq#.",
    "..#OoOOOOOOOOOOOOOOOOpppPq#..",
    "...#OOOOOOOOOOOOOOOOppPPq#...",
    "....##OOOOOOOOOOOOOpppPq#....",
    "......##OOOOOOOOOpppPP##.....",
    "........###pOOOppPPq##.......",
    "...........#########.........",
])

NEAR_BOOT = (12, 54, [
    "....###########...",
    "...#VvvXXXXXXxx#..",
    "...#vXXXXXXXXXx#..",
    "...#vXXvXXXXXxx#..",
    "...#vXXXXXXXXxx#..",
    "..#vXXXvXXXXXxx#..",
    ".#VvXXXXXXXXXXx#..",
    "#VVvXXXXXXXXXxx#..",
    "#vvXXXXXXXXXxxx#..",
    ".###############..",
])

FAR_BOOT = (37, 54, [
    "..###########.....",
    ".#vvXXXXXXxxx#....",
    ".#vXXXXXXXXxx#....",
    ".#vXXvXXXXXxx#....",
    ".#vXXXXXXXXxxx#...",
    ".#vXXXvXXXXXxxx#..",
    ".#vXXXXXXXXXXxxx#.",
    ".#vXXXXXXXXXXXxxx#",
    ".#vXXXXXXXXXXXxxx#",
    ".#################",
])
