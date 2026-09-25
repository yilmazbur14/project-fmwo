"""Captain Burak's head for the juggle: his hair without the tricorn (it flies off on the hit), and
the juggle's faces. Everything else comes unchanged from the approved rig (art_source/burak_boss).

Hatless hair (15.jpg, 17.jpg): a rounded, voluminous crown; the middle parting lifts the two
curtains into humps either side before they arc down over the temples; loose flyaways on top.
The approved curtain bangs, the lock over his right brow and the side locks are reused as they are.
"""
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
RIG = os.path.join(os.path.dirname(HERE), 'burak_boss')
for _p in (RIG,):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import head as H  # noqa: E402
from kit import amap, ellipse, fill, lock, shade_lock  # noqa: E402

# The crown: two locks lifting off the parting and arcing over the top of his head to the sides.
CROWN_LOCKS = [
    ((47, 14), (30, 20), 4.2, 1.6, -5.5),    # the left curtain's root, humped up off the parting
    ((48, 14), (66, 20), 4.2, 1.6, 5.5),     # the right one
    ((46, 11), (37, 12), 2.6, 1.0, -2.5),    # a curl of volume riding on top of the left hump
]

# The approved hair's lowest-row map, reused, and the rounded mass that now shows on top.
FLY_TOP = {(40, 6): 'k', (39, 5): 'k', (38, 5): 'k', (37, 6): 'k',
           (55, 5): 'k', (56, 4): 'k', (57, 4): 'k', (58, 5): 'k', (58, 6): 'k'}


def hair_back_hatless():
    shape = ellipse(48, 21, 18.8, 13.6) | ellipse(40, 16, 10, 8) | ellipse(56, 16, 10, 8)
    shape = {(x, y) for (x, y) in shape if y <= H.HAIR_LOW.get(x, -1)}
    return fill(shape, 'i')


# The lock over his right brow, tossed up by the hit so it clears the eye: the juggle's faces need
# both eyes to read.
SHORT_LOCK = ((49, 18), (51, 27), 2.0, 0.6, 1.5)


def hair_hatless(short_lock=True):
    """One part: the rounded back mass, the approved locks laid over it, then the crown locks; each
    seamed dark where it lies over another, as in head.hair()."""
    part = hair_back_hatless()
    locks = []
    specs = H.LOCKS_LEFT + H.LOCKS_RIGHT
    if short_lock:
        specs = specs[:-1] + [SHORT_LOCK]
    for spec in specs:
        locks.append(shade_lock(lock(*spec), 'mljih', (0.93, 0.78, 0.45, 0.05)))
    for spec in CROWN_LOCKS:
        locks.append(shade_lock(lock(*spec), 'mljih', (0.9, 0.72, 0.4, 0.05), tip_dark=0.85, root_dark=0.0))
    for lk in locks:
        for (x, y) in lk:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q in part and q not in lk:
                    part[q] = 'h'
        part.update(lk)
    # the parting itself: a dark seam where the two humps meet
    for q in ((47, 10), (47, 11), (47, 12), (48, 12), (47, 13)):
        if q in part:
            part[q] = 'h'
    return part


def flyaways_hatless():
    f = dict(H.FLYAWAYS)
    f.update(FLY_TOP)
    return f


# ------------------------------------------------------------------ the juggle's faces
# Feature overlays on the approved face, x 36-60 from y 28 (head.FEAT_X0/Y0), '.' keeps the skin.

FACES = {
    # the uppercut lands: the smirk wiped off. Eyes squeezed shut in > <, brows jammed up in shock,
    # the mouth a big gaping howl, a tooth's worth of white in it
    'hit': [
        # x: 36-40 41-45 46-50 51-55 56-60      y
        "..hhh h.... ..... ....h hh...",       # 28  brows shot up at the inner ends
        "..... hhh.. ..... ..hhh .....",       # 29
        "..... ..kk. ..... .kk.. .....",       # 30
        "...kk kk... ..... ...kk kk...",       # 31  > <  squeezed shut
        ".kk.. ..... ..... ..... ..kk.",       # 32
        "...kk kk... ..... ...kk kk...",       # 33
        "..... ..kk. ..... .kk.. .....",       # 34
        "..... ..... .2... ..... .....",       # 35
        "..... ..... .2.4. ..... .....",       # 36
        "..... ..... 3.244 ..... .....",       # 37
        "..... ..... 32445 ..... .....",       # 38
        "..... ...kk kkkkk kkk.. .....",       # 39  the howl
        "..... ..kWW Wxxxx xWWk. .....",       # 40
        "..... ..kxx xxxxx xxxxk .....",       # 41
        "..... ..kxx yyyyy yxxxk .....",       # 42  tongue
        "..... ...kx yyyyy yyxk. .....",       # 43
        "..... ....k kkkkk kkk.. .....",       # 44
        "..... ..... s.s.s ..... .....",       # 45
        "..... ..... ..... ..... .....",       # 46
    ],
    # launched: stunned, huge white eyes round two pin pupils, the jaw hanging open
    'stunned': [
        # x: 36-40 41-45 46-50 51-55 56-60      y
        "..hhh hhh.. ..... ..hhh hhh..",       # 28  brows flung up
        "...kk kkk.. ..... ...kk kkk..",       # 29
        "..kWW WWWk. ..... ..kWW WWWk.",       # 30
        ".kWWW WWWWk ..... .kWWW WWWWk",       # 31  O_O
        ".kWWW kWWWk ..... .kWWW kWWWk",       # 32  pin pupils
        ".kWWW WWWWk ..... .kWWW WWWWk",       # 33
        "..kWW WWWk. ..... ..kWW WWWk.",       # 34
        "...kk kkk.. .2... ...kk kkk..",       # 35
        "..... ..... .2.4. ..... .....",       # 36
        "..... ..... .2.44 ..... .....",       # 37
        "..... ..... 31245 ..... .....",       # 38
        "..... ....4 65565 ..... .....",       # 39
        "..... ....k kkkkk k.... .....",       # 40  the jaw dropped
        "..... ...kx xxxxx xk... .....",       # 41
        "..... ...kx xyyyx xk... .....",       # 42
        "..... ....k kkkkk k.... .....",       # 43
        "..... ..... ..... ..... .....",       # 44
        "..... ..... s.s.s ..... .....",       # 45
        "..... ..... ..... ..... .....",       # 46
    ],
    # the apex: limp and surprised. Big round eyes, irises dead centre, a little round "o"
    'surprised': [
        # x: 36-40 41-45 46-50 51-55 56-60      y
        "..h.. ...h. ..... .h... ..h..",       # 28  brows arched high
        "...hh hhh.. ..... ..hhh hh...",       # 29
        "..kkk kkkk. ..... .kkkk kkk..",       # 30
        ".kWWW WWWWk ..... kWWWW WWWk.",       # 31
        ".kWW9 99WWk ..... kWW99 9WWk.",       # 32  irises
        ".kWW9 k9WWk ..... kWW9k 9WWk.",       # 33
        "..kWW WWWk. ..... .kWWW WWk..",       # 34
        "...kk kkk.. .2... ..kkk kk...",       # 35
        "..... ..... .2.4. ..... .....",       # 36
        "..... ..... .2.44 ..... .....",       # 37
        "..... ..... 31245 ..... .....",       # 38
        "..... ....4 65565 ..... .....",       # 39
        "..... ..... ..... ..... .....",       # 40
        "..... ..... .kkk. ..... .....",       # 41  "o"
        "..... ..... kxxxk ..... .....",       # 42
        "..... ..... kxxxk ..... .....",       # 43
        "..... ..... .kkk. ..... .....",       # 44
        "..... ..... s...s ..... .....",       # 45
        "..... ..... ..... ..... .....",       # 46
    ],
    # tumbling: dizzy. White @ swirl eyes, a wobbly open mouth
    'dizzy': [
        # x: 36-40 41-45 46-50 51-55 56-60      y
        "..... ..... ..... ..... .....",       # 28
        "...kk kkk.. ..... ...kk kkk..",       # 29
        "..kWW WWWk. ..... ..kWW WWWk.",       # 30
        ".kWkk kkWWk ..... .kWkk kkWWk",       # 31  @ @
        ".kWkW WWkWk ..... .kWkW WWkWk",       # 32
        ".kWkW kWkWk ..... .kWkW kWkWk",       # 33
        ".kWWk kkWWk ..... .kWWk kkWWk",       # 34
        "..kWW WWWk. .2... ..kWW WWWk.",       # 35
        "...kk kkk.. .2.4. ...kk kkk..",       # 36
        "..... ..... .2.44 ..... .....",       # 37
        "..... ..... 31245 ..... .....",       # 38
        "..... ....4 65565 ..... .....",       # 39
        "..... ..... ..... ..... .....",       # 40
        "..... ..kk. ..... .kk.. .....",       # 41  a wobbly, slack open mouth
        "..... .kxxk k.kkk kxxk. .....",       # 42
        "..... ..kkx xkxxx kkk.. .....",       # 43
        "..... ....k kk.kk ..... .....",       # 44
        "..... ..... s...s ..... .....",       # 45
        "..... ..... ..... ..... .....",       # 46
    ],
    # the crash: pain. Eyes screwed shut, teeth clenched in a wide grimace
    'pain': [
        "..... ..... ..... ..... .....",       # 28
        "...hh hhh.. ..... ..hhh hh...",       # 29  brows crushed down to the nose
        "..... ..hhk ..... khh.. .....",       # 30
        "..... ..... ..... ..... .....",       # 31
        "..kkk kkk.. ..... ..kkk kkk..",       # 32  shut hard
        "...k. ..... ..... ..... .k...",       # 33
        "..... ..... ..... ..... .....",       # 34
        "..... ..... .2... ..... .....",       # 35
        "..... ..... .2.4. ..... .....",       # 36
        "..... ..... .2.44 ..... .....",       # 37
        "..... ..... 31245 ..... .....",       # 38
        "..... ....4 65565 ..... .....",       # 39
        "..... ..kkk kkkkk kkkk. .....",       # 40  the grimace
        "..... .kWkW kWkWk WkWk. .....",       # 41  clenched teeth
        "..... ..kkk kkkkk kkkk. .....",       # 42
        "..... ..... ..... ..... .....",       # 43
        "..... ..... ..... ..... .....",       # 44
        "..... ..... s.s.s ..... .....",       # 45
        "..... ..... ..... ..... .....",       # 46
    ],
    # out cold: X eyes, the tongue lolling out of a slack mouth
    'ko': [
        "..... ..... ..... ..... .....",       # 28
        "..... ..... ..... ..... .....",       # 29
        "..... ..... ..... ..... .....",       # 30
        "..k.. .k... ..... ..k.. .k...",       # 31  X eyes
        "...k. k.... ..... ...k. k....",       # 32
        "....k ..... ..... ....k .....",       # 33
        "...k. k.... ..... ...k. k....",       # 34
        "..k.. .k2.. ..... ..k.. .k...",       # 35
        "..... ..... .2.4. ..... .....",       # 36
        "..... ..... .2.44 ..... .....",       # 37
        "..... ..... 31245 ..... .....",       # 38
        "..... ....4 65565 ..... .....",       # 39
        "..... ...kk kkkkk kk... .....",       # 40  slack mouth
        "..... ..k.x xxxxx x.k.. .....",       # 41
        "..... ...kk kyyyk kk... .....",       # 42  the tongue out and down
        "..... ..... kyyyk ..... .....",       # 43
        "..... ..... .kyk. ..... .....",       # 44
        "..... ..... ..k.. ..... .....",       # 45
        "..... ..... ..... ..... .....",       # 46
    ],
}


def features(expr):
    return amap(FACES[expr], H.FEAT_X0, H.FEAT_Y0)
