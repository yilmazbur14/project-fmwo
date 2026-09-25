"""Matt's palette, and the hook that installs it into the shared toolkit.

The toolkit is art_source/josh_redesign/lib.py, imported and never edited. Its Canvas.image() looks
colours up in the module global lib.PAL, so install() swaps that dict for this one at run time.
Bytecode writing is switched off first so importing it leaves Josh's folder untouched.

One key per colour. Ramps run light -> dark.
"""
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'josh_redesign'))
import lib  # noqa: E402


def hx(s):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


PAL = {
    'k': hx('000000'),                                   # keyline, pure black
    # skin: the house ramp (Carter's and Josh's), light -> dark
    '1': hx('FBD6B0'), '2': hx('F0B98E'), '3': hx('DB976C'), '4': hx('B86C4E'), '5': hx('84412F'),
    '6': hx('552619'),
    # Exploud lavender: the sweatshirt, trainers
    'A': hx('DCDEFF'), 'B': hx('B3B6F2'), 'C': hx('8E91DA'), 'D': hx('6D6FBC'), 'E': hx('4F4D96'),
    'F': hx('332F68'),
    # Exploud butter yellow: dyed tips, ribbing, port rims
    'a': hx('FFF6BE'), 'b': hx('F8DB66'), 'c': hx('E2B13C'), 'd': hx('AC7C26'), 'e': hx('6A4618'),
    # hair, blue-black with a lavender sheen
    'h': hx('15121F'), 'i': hx('272337'), 'j': hx('3C3654'), 'l': hx('5C5480'),
    # mouth: throat -> wall -> tongue
    'm': hx('2C0A1C'), 'n': hx('5C1634'), 'p': hx('962C50'), 'q': hx('C8526E'), 'r': hx('EE8CA2'),
    'R': hx('FFC4D0'),
    # whites: teeth, socks, soles
    'W': hx('FFFFFF'), 'X': hx('D5D9EC'), 'x': hx('9DA1C0'),
    # Exploud red: the roar's eyes
    'O': hx('FFD6DC'), 'P': hx('FF4A58'), 'Q': hx('CF1E38'), 'T': hx('780C24'),
    # charcoal: trousers, speaker cones
    'K': hx('1A1A25'), 'L': hx('2A2A38'), 'M': hx('3F3F52'), 'N': hx('5A5A70'),
    # sound rings
    'z': hx('F2F3FF'), 'Z': hx('C4C9FA'),
}

RAMPS = {
    'skin': '123456',
    'lav': 'ABCDEF',
    'yel': 'abcde',
    'hair': 'ljih',
    'mouth': 'Rrqpnm',
    'white': 'WXx',
    'red': 'OPQT',
    'char': 'NMLK',
}

DARKER, LIGHTER = {}, {}
for _r in RAMPS.values():
    for _i, _k in enumerate(_r):
        DARKER[_k] = _r[min(_i + 1, len(_r) - 1)]
        LIGHTER[_k] = _r[max(_i - 1, 0)]


def install():
    lib.PAL = PAL
    return lib


install()
