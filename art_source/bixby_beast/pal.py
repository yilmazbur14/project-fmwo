"""Beast Bixby palette. Ramps are brightest -> darkest.
Identity colours are copied exactly from the approved sprites:
  tan / fur / ear / dark(saddle) / collar / iron  <- Bixby/bixby.png
  band / tails / pants / shoes / glasses          <- Liam/liam.png
  wing membrane                                  <- Eric cape crimson (eric_redesign_v2)
  lava / fire                                    <- DB32 yellow/orange/red + mech pale yellow
"""


def hexc(s):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


BLACK = (0, 0, 0, 255)

RAMPS = {
    'tan':    ['E9A55F', 'C97A3C', '9C5428', '6B3419', '4A2818'],
    'fur':    ['FFFFFF', 'EDE4D6', 'C7BBAB', '948779', '6B6157'],
    'ear':    ['8A5530', '6A3C22', '4A2818', '2C1810', '1B0F0D'],
    'dark':   ['7E7A8C', '5C5868', '3A3542', '26222C', '121016'],
    'wing':   ['E0524A', 'AC3232', '8A1F38', '5E142C', '3C0C20'],
    'collar': ['E0524A', 'AC3232', '6E1E22', '4A1A1A'],
    'iron':   ['E8ECF2', 'A8B0BE', '5E6674', '3C4450'],
    'lava':   ['FFFFFF', 'FFF7A0', 'FBF236', 'F58A38', 'DF7126', 'AC3232', '6E1E22'],
    'mouth':  ['E8788A', 'B84A60', '5A1A22', '3C0C20'],
    'band':   ['EEF4F7', 'B3C0C9', '7B8893', '4B555E'],
    'tails':  ['9BADB7', '6E7D86', '4A5563'],
    'pants':  ['6B6BB0', '4C4C8C', '3A3A70', '26264C'],
    'shoe':   ['6A4A3A', '45302A', '2A1B16'],
}

# one char per colour for ASCII stamps ('.', ' ', '_', '-', '+' are reserved)
PAL = {
    'k': '000000',
    # tan head fur
    '1': 'E9A55F', '2': 'C97A3C', '3': '9C5428', '4': '6B3419', '5': '4A2818',
    # white fur / underbelly / fangs
    'W': 'FFFFFF', 'w': 'EDE4D6', 'v': 'C7BBAB', 'u': '948779', 't': '6B6157',
    # ears (c == 5)
    'a': '8A5530', 'b': '6A3C22', 'c': '4A2818', 'd': '2C1810', 'e': '1B0F0D',
    # saddle-black armour / bones / horns / claws
    'G': '7E7A8C', 'B': '5C5868', 'D': '3A3542', 'J': '26222C', 'Z': '121016',
    # wing crimson (P, Q shared with collar)
    'P': 'E0524A', 'Q': 'AC3232', 'R': '8A1F38', 'S': '5E142C', 'T': '3C0C20',
    # collar dark reds
    'r': '6E1E22', 's': '4A1A1A',
    # iron
    'x': 'E8ECF2', 'X': 'A8B0BE', 'y': '5E6674', 'Y': '3C4450',
    # lava / fire / glowing eyes
    'L': 'FFF7A0', 'O': 'FBF236', 'o': 'F58A38', 'F': 'DF7126',
    # mouth / tongue
    'm': 'E8788A', 'n': 'B84A60', 'M': '5A1A22',
    # Liam headband plate + tails
    'h': 'EEF4F7', 'i': 'B3C0C9', 'j': '7B8893', 'l': '4B555E',
    'H': '9BADB7', 'I': '6E7D86', 'K': '4A5563',
    # Liam pants + shoes (gag frame)
    '6': '6B6BB0', '7': '4C4C8C', '8': '3A3A70', '9': '26264C',
    'f': '6A4A3A', 'g': '45302A', 'E': '2A1B16',
    # nose highlight, glasses glint
    'N': '6E6E78', 'C': 'CBDBFC',
}

PALC = {k: hexc(v) for k, v in PAL.items()}
RAMPC = {k: [hexc(c) for c in v] for k, v in RAMPS.items()}

# darker / lighter neighbours (first ramp that registers a colour wins)
DARKER, LIGHTER = {}, {}
for name in ['tan', 'fur', 'ear', 'dark', 'wing', 'collar', 'iron', 'lava', 'mouth', 'band', 'tails', 'pants', 'shoe']:
    cs = RAMPC[name]
    for i, c in enumerate(cs):
        DARKER.setdefault(c, cs[min(i + 1, len(cs) - 1)])
        LIGHTER.setdefault(c, cs[max(i - 1, 0)])


def C(ch):
    return PALC[ch]
