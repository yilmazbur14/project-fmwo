"""The demon-lord palette (the user's 2026-09-28 reference): black obsidian armour, lava cracks
whose dim end is the Peach tee's own reds, a white-hot core ringed in the tee's pink, dark leather
wings, and the cold rune-light rim. Keyline: pure black, as measured on Jordan's v2 sheet.

A1 adds three of Jordan's own pallor skin tones and two beard browns (his face shows); A2 (the
full mask) uses none of them.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jg_base import JORDAN, hx  # noqa: E402

LORD = {
    'k': hx('000000'),                                   # keyline (Jordan's: pure black)
    # obsidian, dark -> light
    '1': hx('0D0B12'), '2': hx('19151F'), '3': hx('28222F'), '4': hx('3B3346'), '5': hx('564B63'),
    # rune-light rim (the cold backlight)
    '6': hx('2B6C99'), '7': hx('66C6EC'),
    # lava: the dim end is the Peach tee's reds (v2 keys V, R, T), then orange, gold, white-hot
    'V': JORDAN['V'], 'R': JORDAN['R'], 'T': JORDAN['T'],
    'r': hx('FF8C3A'), 'O': JORDAN['O'], 'Y': JORDAN['Y'], 'w': hx('FFFFFF'),
    # the tee's pink, kept in the core
    'P': JORDAN['P'], 'Q': JORDAN['Q'],
    # wing leather: near-black with a blood-red cast
    'm': hx('130A10'), 'n': hx('22101A'), 'M': hx('3A1523'),
}

# A1: Jordan's face shows, in shadow (v2 pallor skin, the three darkest steps) and his beard.
FACE = {
    'a': JORDAN['a'], 'b': JORDAN['b'], 'c': JORDAN['c'], 'd': JORDAN['d'],
    'h': JORDAN['h'], 'i': JORDAN['i'],
}

PAL_A1 = dict(LORD)
PAL_A1.update(FACE)
PAL_A2 = dict(LORD)

OBS = ('1', '2', '3', '4', '5')     # obsidian plate ramp (dark -> light); '1' ends up black
LAVA = ('V', 'R', 'T', 'r', 'O', 'Y')
LEATHER = ('m', 'n', 'M')
