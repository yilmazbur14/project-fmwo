"""PLACEHOLDER puppets for the previews only: Greyson's and Matt's approved idle frame 0, READ from
Assets and greyed (pure-black keyline kept, every other colour to a flat 4-step grey by its
brightness). The undead puppet designs are the other artist's (art_source/jordan_puppets/); none
of this ships.

Each stand-in has its frame's feet point (the scene's floor contact, as JordanFinaleLayout uses
them) and a back HOOK: the texel between the shoulder blades the strings tie to. It is on the
puppet's back, so from the front it is hidden: a string runs behind the head and shoulders to it.
"""
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import jp_rig as R  # noqa: E402,F401
import jg_base as B  # noqa: E402
from PIL import Image  # noqa: E402

GREYS = [B.hx('2E2E36'), B.hx('4E4E58'), B.hx('76767F'), B.hx('A2A2AA')]

# hooks per the build plan (jordan_puppet_master/PLAN.md section 7): with the feet on the plan's
# spots, each lands on the plan's hook - Greyson (864, ~250), Matt (1248, ~265), Captain Burak
# (640, ~300), Danny (1300, ~220) px. The roster artist's real back hooks replace these.
PUPPETS = {
    'greyson': {'sheet': os.path.join(B.ROOT, 'Assets', 'Characters', 'Greyson', 'greyson_idle.png'),
                'frame': (112, 112), 'feet': (56, 111), 'hook': (56, 56), 'rift': 'std'},
    'matt': {'sheet': os.path.join(B.ROOT, 'Assets', 'Characters', 'Matt', 'matt_idle.png'),
             'frame': (96, 96), 'feet': (48, 95), 'hook': (48, 45), 'rift': 'std'},
    'captain_burak': {'sheet': os.path.join(B.ROOT, 'Assets', 'Characters', 'BurakBoss', 'burak_idle.png'),
                      'frame': (96, 96), 'feet': (48, 95), 'hook': (48, 48), 'rift': 'std'},
    'danny': {'sheet': os.path.join(B.ROOT, 'Assets', 'Characters', 'Danny', 'Sumo', 'danny_sumo_idle.png'),
              'frame': (176, 144), 'feet': (88, 143), 'hook': (88, 70), 'rift': 'wide'},
}


def placeholder(name):
    """(image, feet, hook): the greyed stand-in, its feet point and back hook in its frame."""
    spec = PUPPETS[name]
    w, h = spec['frame']
    src = Image.open(spec['sheet']).convert('RGBA').crop((0, 0, w, h))
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    sp, op = src.load(), out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = sp[x, y]
            if a == 0:
                continue
            if (r, g, b) == (0, 0, 0):
                op[x, y] = (0, 0, 0, 255)
                continue
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            k = 0 if lum < 70 else 1 if lum < 125 else 2 if lum < 185 else 3
            op[x, y] = GREYS[k]
    return out, spec['feet'], spec['hook']
