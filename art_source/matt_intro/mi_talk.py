"""matt_talk.png: Matt's dialogue poses for the intro, 2 frames each (mouth closed, mouth open), in
the order of the user's script:

    0-1   friendly        "are you enjoying your time so far?"   arms loose, palms out, warm smile
    2-3   awkward_laugh   "haha... you're right..."             hand behind his head, sweat drop
    4-5   proud           "calm cool and collected" / "I love RuneScape!"   thumb to chest, fist on hip
    6-7   nervous         "Hehe.... ya..."                       index fingers poking, eyes sliding away
    8-9   irritated       "Buddy, I said top 5..."               strained grin, twitching brow, anger mark
    10-11 shout           "NO I DID NOT."                        braced, fists flared, mouth wide
    12-13 sheepish        "haha"                                 scratching his head, eyes shut, blush
    14-15 furious         "ENOUGH."                              fists up, red-faced, veins, steam, crest bristling
    16-17 puzzled         "You don't think it's in the top 5?"   head tilted, one brow up, a small shrug

The plan's tag names map onto this order as: friendly 0, laugh 2, proud 4, forced 6, irritated 8,
snap 10, sheepish 12, furious 14, puzzled 16.

Inside a pair only the mouth (and the steam, which is an effect) changes, so flapping between the
two frames never jitters the body.
"""
import mi_base as B
import mi_arms as A
import mi_faces as G
import mi_fig as F
import mi_hands as H
import mi_poses as PZ

NAME = 'matt_talk'
POSES = ['friendly', 'awkward_laugh', 'proud', 'nervous', 'irritated', 'shout', 'sheepish', 'furious',
         'puzzled']


def part(rows, x, y):
    return B.amap(rows, x, y)


def friendly(open_):
    arms = PZ.pair((25, 57), (24, 60), (17, 66), (15, 70), H.OPEN_DOWN_L, H.OPEN_DOWN_R)
    face = G.face(G.BR_RELAX, G.EY_SOFT, G.M_SMILE_OPEN if open_ else G.M_SMILE)
    return F.Fig(arms=arms, face=(face, G.X0, G.Y0), spikes=PZ.SP_PERK)


def awkward_laugh(open_):
    arms = [A.hang(0),
            PZ.one(1, (25, 56), (24, 56), (19, 37), (31, 31), None, cuff=False)]
    face = G.face(G.BR_WORRY, G.EY_ARC, G.M_LAUGH if open_ else G.M_GRIN_TEETH)
    extra = [(part(G.SWEAT, 58, 24), False, 'front')]
    return F.Fig(arms=arms, face=(face, G.X0, G.Y0), parts=extra, head=(-1, 0), spikes=PZ.SP_DROOP)


def proud(open_):
    arms = [PZ.one(0, (25, 56), (24, 59), (17, 63), (29, 58), H.THUMB_L),
            PZ.one(1, (25, 57), (24, 60), (13, 63), (18, 70), H.FIST_R)]
    face = G.face(G.BR_HIGH, G.EY_SMUG, G.M_GRIN_BIG if open_ else G.M_SMIRK)
    return F.Fig(arms=arms, face=(face, G.X0, G.Y0), spikes=PZ.SP_PERK, head=(0, -1), neck=True)


def nervous(open_):
    arms = PZ.pair((25, 56), (24, 59), (18, 66), (33, 62), H.POKE_L, H.POKE_R)
    face = G.face(G.BR_WORRY, G.EY_SIDE, G.M_SMALL_OPEN if open_ else G.M_WAVY)
    extra = [(part(G.SWEAT, 59, 25), False, 'front')]
    return F.Fig(arms=arms, face=(face, G.X0, G.Y0), parts=extra, head=(0, 1), spikes=PZ.SP_DROOP)


def irritated(open_):
    arms = PZ.hang_pair(upper_rot=6, fore_rot=4, shoulder_dy=-1)
    face = G.face(G.BR_TWITCH, G.EY_ANGRY, G.M_STRAINED_OPEN if open_ else G.M_STRAINED)
    extra = [(part(G.VEIN, 55, 21), False, 'front')]
    return F.Fig(arms=arms, face=(face, G.X0, G.Y0), parts=extra, spikes=PZ.SP_TENSE)


def shout(open_):
    arms = PZ.hang_pair(upper_rot=22, fore_rot=10, shoulder_dy=-2)
    if open_:
        face = G.with_jaw(G.face(G.BR_ANGRY, G.EY_ANGRY), G.YELL_ROWS)
    else:
        face = G.face(G.BR_ANGRY, G.EY_ANGRY, G.M_SCOWL)
    return F.Fig(arms=arms, face=(face, G.X0, G.Y0), spikes=PZ.SP_TENSE, stance=2, head=(0, 1))


def sheepish(open_):
    arms = [PZ.one(0, (25, 56), (24, 58), (13, 47), (22, 37), H.SCRATCH_L,
                   fore_layer='front', hand_layer='front'),
            A.hang(1)]
    face = G.face(G.BR_WORRY, G.EY_ARC, G.M_HAHA if open_ else G.M_SMALL_SMILE, G.BLUSH)
    return F.Fig(arms=arms, face=(face, G.X0, G.Y0), spikes=PZ.SP_DROOP, head=(-1, 0))


def furious(open_):
    arms = PZ.pair((25, 56), (24, 57), (13, 57), (15, 47), H.FIST_UP_L, H.FIST_UP_R)
    # steam off both ears, rising outward: a small puff at the ear, a big one above it
    if open_:
        face = G.flushed(G.with_jaw(G.face(G.BR_FURY, G.EY_BLANK), G.ENOUGH_ROWS))
        steam = [(part(G.PUFF_C, 28, 30), False, 'front'), (part(G.PUFF_A, 19, 23), False, 'front'),
                 (part(G.PUFF_C, 64, 30), False, 'front'), (part(G.PUFF_A, 68, 23), False, 'front')]
    else:
        face = G.flushed(G.face(G.BR_FURY, G.EY_BLANK, G.M_GRIT))
        steam = [(part(G.PUFF_B, 26, 28), False, 'front'), (part(G.PUFF_C, 22, 23), False, 'front'),
                 (part(G.PUFF_B, 63, 28), False, 'front'), (part(G.PUFF_C, 70, 23), False, 'front')]
    extra = [(part(G.VEIN, 55, 20), False, 'front'), (part(G.VEIN, 32, 20), False, 'front')] + steam
    f = F.Fig(arms=arms, face=(face, G.X0, G.Y0), parts=extra, spikes=PZ.SP_BRISTLE, stance=2)
    f.fx = set().union(*[set(p) for p, _, _ in steam])
    return f


def puzzled(open_):
    # the shrug: elbows in, forearms up and out, palms open to the front, shoulders hitched
    arms = [A.bent(0, (25, 55), (24, 57), (19, 64), (13, 58), hand=H.OPEN_UP_L),
            A.bent(1, (71, 55), (72, 57), (77, 64), (83, 58), hand=H.OPEN_UP_R)]
    face = G.face(G.BR_PUZZLED, G.EY_ROUND, G.M_HUH if open_ else G.M_HMM)
    # the head tilts toward screen-left: shifted over, the whole crest leaning with it
    return F.Fig(arms=arms, face=(face, G.X0, G.Y0), spikes=PZ.SP_IDLE, tilt=-9, head=(-2, 0),
                 body=(0, 0))


BUILDERS = [friendly, awkward_laugh, proud, nervous, irritated, shout, sheepish, furious, puzzled]


def figs():
    out = []
    for b in BUILDERS:
        out.append(b(False))
        out.append(b(True))
    return out


def frames():
    return [F.px_of(f) for f in figs()]
