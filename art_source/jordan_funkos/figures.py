"""Figure definitions (head + torso + role colours) for the rig."""
from rig import *

# ------------------------------------------------------------------------------ plumber
PAL_PLUMBER = {
    'K': '000000',
    '5': 'ffa084', '4': 'ee5a44', '3': 'cc2f2f', '2': '921f2c', '1': '561425',
    's': 'fadcb8', 'S': 'eec39a', 't': 'd6aa7c', 'T': 'ae8358',
    'm': '2c1810', 'n': '4a2818', 'N': '7a4424',
    'b': '78b4f0', 'B': '4a82d8', 'd': '2e56a8', 'D': '1e2f66',
    'Y': 'fbf236', 'y': 'd99a2a', 'W': 'ffffff',
    'h': '9a5e3a', 'H': '5e3420',
}
#                  0123456789ABCDE
PLUMBER_MASTER = """
...KKKKKKK.....
..K5443Y33K....
.K544YYYYY2K...
.K4433Y3Y22KK..
.K12222222344K.
.KnSSKttKtTKK..
.KNTtnnsSnnK...
..KTmmmmmmK....
..K3KbYBYK3K...
..KtKdBBdKtK...
...KhHKKhhHK...
...KKKK.KKKK...
"""
PLUMBER = Figure(
    'plumber', PAL_PLUMBER, PLUMBER_MASTER, 5,
    torso="""
3bb3
bYBY
dBBd
""",
    roles={'a': '3', 'A': '4', 'h': 't', 'H': 'T', 'n': 'd', 'N': 'D',
           's': 'h', 'S': 'H', 'z': 'h', 'f': 'h', 'F': 'H', 'Z': 'h'})

# ------------------------------------------------------------------------------ hedgehog
PAL_HEDGEHOG = {
    'K': '000000',
    'c': '9ccbff', 'C': '5b95f5', 'l': '2f64d6', 'L': '22419c', 'v': '172660',
    's': 'fbe3c0', 'S': 'f2c894', 't': 'd9a066', 'T': 'b07a48',
    'Y': 'fbf236', 'y': 'e0a020', 'o': 'df7126', 'W': 'ffffff', 'w': 'cbdbfc',
    'n': '222034',
}
#                   0123456789ABCDE
HEDGEHOG_MASTER = """
.KK..KKKK.K....
.KCKKCccCKcK...
..KCCCcclCllK..
KKKCCClllllLK..
.KCClllWKlWKK..
..KKLllWKlWKSK.
.KCLllLLSsSSSnK
.KKKLLLKTTSSTKK
....KlKlSSlKK..
....KSKLllLKSK.
....KYWKKKYWK..
....KKKK.KKKK..
"""
HEDGEHOG = Figure(
    'hedgehog', PAL_HEDGEHOG, HEDGEHOG_MASTER, 7,
    torso="""
llll
lSSl
LllL
""",
    roles={'a': 'l', 'A': 'C', 'h': 'S', 'H': 't', 'n': 'l', 'N': 'L',
           's': 'Y', 'S': 'W', 'z': 'W', 'f': 'Y', 'F': 'W', 'Z': 'W'})

# ------------------------------------------------------------------------------ mascot
PAL_MASCOT = {
    'K': '000000',
    'W': 'ffffff', 'w': 'eef3ff', 'p': 'cbdbfc', 'g': '9badb7', 'G': '6d7a92',
    'F': '8fb4ff', 'L': '639bff', 'f': '5b6ee1', 'x': '3f3f74', 'X': '2a2850',
    'a': '99e550', 'e': '6abe30', 'E': '37946e',
    'n': '222034', 'N': '3a3960',
}
#                 0123456789ABCD
MASCOT_MASTER = """
...KKKKKK.....
.KKWWwwwpKK...
KwWWwLffffLK..
KwWwfWfffWfK..
KwwpffffffxK..
KppgfxxgxxKKK.
.KpgggGGGKaeK.
..KKKKKKKKeEK.
...KKLffxKKK..
..KWKfffxKWK..
...KNnKKNnK...
...KKKK.KKKK..
"""
MASCOT = Figure(
    'mascot', PAL_MASCOT, MASCOT_MASTER, 5,
    torso="""
ffff
Lffx
fffx
""",
    roles={'a': 'f', 'A': 'L', 'h': 'W', 'H': 'p', 'n': 'x', 'N': 'X',
           's': 'N', 'S': 'n', 'z': 'W', 'f': 'N', 'F': 'n', 'Z': 'W'})

# ------------------------------------------------------------------------------ gamer
PAL_GAMER = {
    'K': '000000',
    '1': 'd7a1f0', '2': 'a86ad0', '3': '8246b0', '4': '5c2f86', '5': '3a1c5c',
    's': 'fadcb8', 'S': 'eec39a', 't': 'd6aa7c', 'T': 'ae8358',
    'h': '4a2818', 'H': '6b3419',
    'k': '2b2d33', 'm': '5c6067', 'c': '5fcde4', 'C': 'cbf7ff',
    'j': '41444b', 'J': '2b2d33', 'W': 'ffffff', 'w': 'cbdbfc',
}
#                0123456789ABCD
GAMER_MASTER = """
....KKKKKK....
..KK21k2223K..
.K211k222233K.
.K21khhhhhK3K.
KkkkKhSKSKhK4K
KccmKSSSSSSK4K
KkkmKtSSSTK44K
.KKK4mmmKK44K.
..K3K2W2WK3K..
..KsK3223KsK..
...KWwKKWwK...
...KKKK.KKKK..
"""
GAMER = Figure(
    'gamer', PAL_GAMER, GAMER_MASTER, 5,
    torso="""
3223
2W2W
3223
""",
    roles={'a': '3', 'A': '2', 'h': 's', 'H': 'S', 'n': 'j', 'N': 'J',
           's': 'W', 'S': 'w', 'z': 'W', 'f': 'W', 'F': 'w', 'Z': 'W'})

FIGURES = [PLUMBER, HEDGEHOG, MASCOT, GAMER]
