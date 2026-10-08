"""Jordan's puppets: the shared PUPPET PALETTE (approval pass).

Every one of the nine puppets is drawn from these keys and nothing else, so the undead family reads
as one set whatever colours each boss started in. A take is a full key -> colour table; the keys and
the ramps are the same in every take, so a boss's recipe table (jp_bosses) works under either take.

Both takes share the body: blood reds, pitch blacks, ash-grey dead skin, bone whites and dark iron.
They differ only in the ACCENT, Jordan's power holding the puppets together:
  take A, "Blood & Ash": an EMBER glow in the eyes, the gold of his mask eyes and crown flames;
          the string rings glint bone, the stitches are black thread.
  take B, "Rune": the eyes, the rings' glint and the stitch thread all burn RUNE-BLUE, the exact two
          blues of his rune circle and rim light (#66C6EC, #2B6C99), so the strings' magic visibly
          runs through the puppets and they read against his red-and-black body.

Ramps run DARK -> LIGHT. Several keys are shared between ramps on purpose (that is how the palette
stays at 16 colours): the pitch-black cloth ramp's lit step is the ash skin's shadow, its base is the
socket and skin-deep colour, and its deep step is also the iron's deep step and the deepest crease.

Two keys are ALIASES, not colours: HG (a string ring's glint) and ST (stitch thread). Each takes an
existing colour of its take (take A: bone and black; take B: the two rune blues), so a stamp can say
"glint" or "thread" once and each take colours it its own way without adding a 17th colour.
"""


def hx(s):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


# What each key is for (the report prints this).
ROLE = {
    'K': 'keyline: pure black, the silhouette and every interior separation',
    'P1': 'pitch deep: black cloth in shadow, iron deep, the deepest skin crease',
    'D2': 'pitch base: black cloth and hair; ash deep; the eye sockets',
    'A2': 'pitch lit / ash shadow: the sheen on black cloth and hair, dead skin in shadow',
    'A3': 'ash mid: dead skin turning from the light; bone in shadow',
    'A4': 'ash base: dead skin; old bone',
    'A5': 'ash lit / bone base: lit dead skin, bone, linen, teeth',
    'B1': 'bone highlight: the whitest whites (bone, specular hits)',
    'R1': 'blood deep: red cloth in deep shadow, wounds, mouths',
    'R2': 'blood shadow; the raw line of a stitched cut',
    'R3': 'blood base: the red garments; red hair',
    'R4': 'blood lit',
    'I2': 'iron base: blades, plates, the string rings',
    'I3': 'iron lit',
    'G1': 'glow core: the pupils (the only light the scene does not light)',
    'G2': 'glow halo: the ring round a pupil',
    'HG': "alias: a string ring's glint (A: bone B1, B: rune G1)",
    'ST': 'alias: stitch thread (A: black K, B: rune G2)',
}

_BODY = {
    'K': hx('000000'),
    'P1': hx('17111D'), 'D2': hx('2C2434'), 'A2': hx('4A4356'),
    'A3': hx('6E6A80'), 'A4': hx('9893A5'), 'A5': hx('CFC6B2'), 'B1': hx('F1EAD4'),
    'R1': hx('36091C'), 'R2': hx('661127'), 'R3': hx('9F1C2E'), 'R4': hx('D2403A'),
    'I2': hx('3A4153'), 'I3': hx('68718A'),
}

TAKES = {
    'A': dict(_BODY, G1=hx('FFD55C'), G2=hx('FF7A2E')),     # "Blood & Ash": ember
    'B': dict(_BODY, G1=hx('66C6EC'), G2=hx('2B6C99')),     # "Rune": his rune circle's two blues
}
TAKES['A'].update({'HG': TAKES['A']['B1'], 'ST': TAKES['A']['K']})
TAKES['B'].update({'HG': TAKES['B']['G1'], 'ST': TAKES['B']['G2']})
TAKE_NAMES = {'A': 'Blood & Ash', 'B': 'Rune'}

KEYS = list(TAKES['A'])
ALIASES = ('HG', 'ST')
COLOUR_KEYS = [k for k in KEYS if k not in ALIASES]

RAMPS = {
    'pitch': ['P1', 'D2', 'A2'],
    'ash': ['P1', 'D2', 'A2', 'A3', 'A4', 'A5'],
    'bone': ['A3', 'A4', 'A5', 'B1'],
    'blood': ['R1', 'R2', 'R3', 'R4'],
    'iron': ['P1', 'I2', 'I3', 'B1'],
    'glow': ['G2', 'G1'],
}

# One step darker / lighter along the ramp a key belongs to (the first ramp listed wins), for the
# shading passes (the sunken ring round a socket, a crack's lit lip).
DARKER, LIGHTER = {}, {}
for _name in ('ash', 'blood', 'pitch', 'iron', 'bone', 'glow'):
    _r = RAMPS[_name]
    for _i, _k in enumerate(_r):
        DARKER.setdefault(_k, _r[max(_i - 1, 0)])
        LIGHTER.setdefault(_k, _r[min(_i + 1, len(_r) - 1)])
for _k in ('K', 'HG', 'ST'):
    DARKER[_k] = LIGHTER[_k] = _k


def colours(take):
    return TAKES[take]


def hexes(take):
    return {k: '#%02X%02X%02X' % v[:3] for k, v in TAKES[take].items()}
