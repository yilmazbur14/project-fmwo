"""Greyson's takeover sheets, PRE-CANNON (both arms flesh, no barbell): the cutscene where he finds
Computah beaten (scratchpad greyson_fight/PLAN.md section 6). Built on the approved rig (read-only,
via gf_base) in the approved look; 112x112 frames, feet at (56, 111).

  greyson_walk (6)  the heavy stomp in (gf_walk's cycle) with the 'rage' face: crying and furious.
  greyson_talk (6)  three upset poses, each shut then open (for the mouth flap while a line types):
                      0-1 grief  both fists at his sides (the approved idle arms); "That was my
                                 gym partner."
                      2-3 fond   his right fist pressed to his chest; "I hit my first 225 on bench
                                 with this little guy. That was a long time ago."
                      4-5 fury   both fists clenched in front of his chest; "Now you've really
                                 messed up."
Faces are gf_faces_tk's; arms are the approved idle arm (gr_arms) or the fight rig's CARRY arm
(gf_arms: the forearm folded across the chest, the fist in front of it), fists the approved ones.

    python -B gf_takeover.py      # prints each frame's numbers and audit; writes nothing
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gf_base as B  # noqa: E402
import gf_fig  # noqa: E402
import gf_arms  # noqa: E402
import gf_walk  # noqa: E402
import gf_faces_tk as FT  # noqa: E402

K, gr_fig, gr_arms, gr_hands, gr_face = B.K, B.gr_fig, B.gr_arms, B.gr_hands, B.gr_face

CHEST_FIST = (41.0, 55.0)        # a fist held in front of the chest (left-side coordinates)
IDLE_FIST = (25.0, 84.5)         # the approved fist beside the thigh


def arm(kind, side):
    """(arm part, fist centre in left-side coordinates) for one arm."""
    if kind == 'idle':
        return K.despeckle(gr_arms.arm('idle', side)), IDLE_FIST
    if kind == 'chest':
        part = gf_fig.arm_layer(gf_arms.CARRY, gf_arms.CARRY_FORMS, gf_arms.CARRY_SPEC, side)
        return K.despeckle(part), CHEST_FIST
    raise KeyError(kind)


def front(arms, face):
    """A front-view frame: the approved legs, boots, trunk and trunks, the two arms given as
    (screen-left kind, screen-right kind), the approved fists and a takeover face."""
    cv = K.Canvas()
    gf_fig.front_base(cv, lat_flare=0.5)
    fists = []
    for side, kind in enumerate(arms):
        part, fist = arm(kind, side)
        cv.stamp(part)
        fists.append((side, fist))
    # a fist at the thigh goes under the head; a fist held up at the chest is in front of the
    # mane's locks, as the fight idle's bar fist is
    for side, c in fists:
        if arms[side] != 'chest':
            cv.stamp(gr_hands.fist('idle', side, c), outline=False)
    cv.stamp(FT.head(face), outline=False)
    for side, c in fists:
        if arms[side] == 'chest':
            cv.stamp(gr_hands.fist('idle', side, c), outline=False)
    return gf_fig.finish(cv, FT.face(face))


# ------------------------------------------------------------------------------------ talk

TALK = [
    ('grief', ('idle', 'idle'), 'grief'),
    ('grief open', ('idle', 'idle'), 'grief_open'),
    ('fond', ('chest', 'idle'), 'fond'),
    ('fond open', ('chest', 'idle'), 'fond_open'),
    ('fury', ('chest', 'chest'), 'rage'),
    ('fury open', ('chest', 'chest'), 'rage_open'),
]


def talk(i):
    name, arms, face = TALK[i]
    return front(arms, face), {'name': name, 'face': face, 'mouth': FT.MOUTH[face]}


# ------------------------------------------------------------------------------------ walk

def walk(i):
    cv, info = gf_walk.frame(i, head=(FT.head('rage'), FT.face('rage')))
    mx, my = FT.MOUTH['rage']
    info['mouth'] = (mx, my + info['drop'])
    return cv, info


SHEETS = {'greyson_walk': (walk, 6), 'greyson_talk': (talk, 6)}

if __name__ == '__main__':
    for sheet, (fn, n) in SHEETS.items():
        for i in range(n):
            cv, info = fn(i)
            a = B.audit(cv.px)
            print(sheet, i, info.get('name'), K.stats(cv.image()), 'bbox', K.bbox(cv.px),
                  'audit', {k: len(v) for k, v in a.items()})
