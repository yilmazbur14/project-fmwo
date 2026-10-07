"""matt_echo.png: Matt's Echo Roars body sheet, one strip of 6 frames of 96x96 (PLAN.md section 5).

    f0  echo_inhale       planted (on matt_roar's own stance, soles 33/63), hands cupped round his mouth, chest up, cheeks puffed, spikes rising
    f1  echo_psych        the same cupped stance, mouth open on NOTHING: brows up, a wink, a smug grin,
                          tongue out; normal eyes, crest not flared (must not read as matt_roar f1-3)
    f2  echo_psych hold   the laugh after: shoulders up, eyes shut, a HA mouth
    f3  boomburst_windup  wide sumo stance, leaning back, fists clenched at his sides, chest hugely
                          inflated, spikes flared
    f4  boomburst_blast   lunging forward, arms thrown back, mouth at its widest, red eyes
    f5  boomburst_blast hold  the recoil and hold: still roaring, arms swinging back forward

Built on the scratch copy of Matt's approved rig (art_source/matt, matt_intro, matt_fight,
matt_glass), imported read-only. No rings, badges or FX are baked in.
"""
import ea_base as E
from ea_base import B, A, G, F, H, L, PZ, FF, MH, MM, sh, poly, sym, matt
import ea_psych_gen as PG
import ea_hands as EH

NAME = 'matt_echo'
LABELS = ['f0 echo_inhale', 'f1 echo_psych', 'f2 psych laugh', 'f3 boomburst_windup', 'f4 boomburst_blast',
          'f5 blast hold']
APPROVAL = (0, 1, 4)


# ------------------------------------------------------------------ shared pieces
def wide_legs(drop, stance, lean=1.6, creases=()):
    """Both feet planted wide (screen-space stance), the hips dropped `drop` texels into a squat.
    `creases`: left-leg crease lines (lists of texels), mirrored onto the right leg; the trousers
    pulled tight across a wide squat fold up from the inner knee, as the stomp's lifted leg does."""
    def fn(f):
        parts = L.walk_legs(drop, (-stance, 0, -lean), (stance, 0, lean), screen=True)
        lines = list(creases) + [[(96 - x, y) for (x, y) in c] for c in creases]
        for part, ol in parts:
            if not ol:
                continue                      # feet: leave them alone
            for c in lines:
                hit = [p for p in c if p in part]
                for p in hit:
                    part[p] = 'k'
                for (x, y) in hit:            # the fold's lit lip above it
                    q = (x, y - 1)
                    if q in part and part[q] != 'k' and q not in c:
                        part[q] = B.LIGHTER.get(part[q], part[q])
        return parts
    return fn


def _crease(part, lines):
    for c in lines:
        hit = [p for p in c if p in part]
        for p in hit:
            part[p] = 'k'
        for (x, y) in hit:
            q = (x, y - 1)
            if q in part and part[q] != 'k' and q not in c:
                part[q] = B.LIGHTER.get(part[q], part[q])


def roar_legs(creases=()):
    """matt_roar's own legs, pixel for pixel: the rig's trousers and feet at stance 2 (sole centres
    33 / 63), so the inhale and the psych chain into the reused roar f1-3 without the feet moving.
    `creases` as wide_legs (left leg, mirrored)."""
    def fn(f):
        P = matt.Pose(True)                   # the roar's pose: stance 2
        trousers = matt.trousers(P)
        _crease(trousers, list(creases) + [[(96 - x, y) for (x, y) in c] for c in creases])
        return [(trousers, True)] + [(ft, False) for ft in matt.feet(P)]
    return fn


def puffed_shirt(swell=1.0):
    """The sweatshirt with the chest thrown out: broader and higher across the chest, the waist kept,
    lit as a fuller dome."""
    s = swell
    part = {p: 'C' for p in poly(sym([(48, 48.5 - s), (41, 49 - s), (35.5 - s, 50.5 - s * 0.8),
                                       (31 - s * 1.5, 52.5 - s * 0.5), (30 - s * 1.5, 56), (30.5 - s, 61),
                                       (32, 65), (32.5, 68.5), (33, 71), (48, 71)]))}
    sh.ellipsoid(part, 47, 56.5 - s, 19 + s * 1.5, 14.5, 'ABCDE', (0.93, 0.74, 0.34, 0.0), bulge=1.0 + 0.15 * s)
    for (x, y) in list(part):
        row = [px for (px, py) in part if py == y]
        edge = min(x - min(row), max(row) - x)
        if 60 <= y <= 70 and edge <= 1:
            part[(x, y)] = B.DARKER[part[(x, y)]]
    return part


def mega_arms(dy=0, elbow=(23, 68), wrist=(35, 57)):
    """Both hands cupped round the mouth like a megaphone (his Trueshot hands), forearms rising from
    the elbows in front of the chest; forearm, cuff and hand stamped over the face."""
    el, wr = (elbow[0], elbow[1] + dy), (wrist[0], wrist[1] + dy)
    left = A.bent(0, (25, 57 + dy), (24, 59 + dy), el, wr, hand=MH.MEGA_L, fore_layer='front')
    right = A.bent(1, (71, 57 + dy), (72, 59 + dy), (96 - el[0], el[1]), (96 - wr[0], wr[1]),
                   hand=MH.MEGA_R, fore_layer='front')
    return [left, right]


# knee creases (left leg; mirrored). KNEE_ROAR sits on matt_roar's own legs (the inhale, 2026-10-04 feet fix)
KNEE_ROAR = [[(36, 82), (37, 81), (38, 80), (39, 79), (40, 78), (41, 77), (42, 76)], [(31, 83), (32, 82), (33, 81), (34, 80)]]
KNEE_F0 = [[(36, 82), (37, 81), (38, 80), (39, 79), (40, 78), (41, 77), (42, 76)], [(33, 85), (34, 84), (35, 83), (36, 82)]]
KNEE_F3 = [[(34, 83), (35, 82), (36, 81), (37, 80), (38, 79), (39, 78), (40, 77)], [(30, 85), (31, 84), (32, 83), (33, 82)]]

# crests
SP_RISING = PZ.lerp_spikes(PZ.SP_PERK, PZ.SP_TENSE, 0.6)            # lifting with the breath
SP_BLOWN = [(0, 8, 21, 6.4, 2.0, 0.0), (-52, 8, 29, 6.4, 2.0, -1.0), (-97, 9, 30, 7.2, 2.4, -1.5)]


# ------------------------------------------------------------------ f0 the inhale
def inhale():
    face = FF.puffed(G.BR_ANGRY, G.EY_SQUEEZE)        # straining to hold a lungful
    return F.Fig(arms=mega_arms(dy=-2, elbow=(22, 68), wrist=(34, 57)), legs=roar_legs(creases=KNEE_ROAR),
                 body=(0, -1), head=(0, -2), neck=True, torso_fn=lambda: puffed_shirt(1.8),
                 face=(face, G.X0, G.Y0), spikes=SP_RISING)


# ------------------------------------------------------------------ f1 the psych, f2 the laugh
BR_UP = [(30, 39, 'hhhhh'), (31, 38, 'hh'), (31, 43, 'hh'),           # both brows hitched up
         (30, 52, 'hhhhh'), (31, 51, 'hh'), (31, 56, 'hh')]
EY_WINK = [(35, 37, 'kkkkkkk'), (36, 38, 'kWhhXk'), (37, 39, 'kkkk'),   # one eye wide open on you
           (35, 54, 'kkkk'), (36, 53, 'k'), (36, 58, 'k'), (37, 53, '1111')]  # the other shut in a wink
PSYCH_ROWS = PG.build(PG.OPEN_A, PG.TONGUE_IN_C, tongue_out=PG.TONGUE_OUT_C, depth=1)
LAUGH_ROWS = PG.build(PG.OPEN_A, PG.TONGUE_B, depth=4)


def psych_face():
    return G.with_jaw(G.face(BR_UP, EY_WINK, [(42, 59, 'k')]), PSYCH_ROWS)


def laugh_face():
    return G.with_jaw(G.face(G.BR_HIGH, G.EY_ARC), LAUGH_ROWS)


def psych():
    return F.Fig(arms=mega_arms(dy=-1, elbow=(21, 68), wrist=(31, 58)), legs=roar_legs(),
                 body=(0, -1), head=(0, -1), collar=False, torso_fn=lambda: puffed_shirt(1.0),
                 face=(psych_face(), G.X0, G.Y0), spikes=PZ.SP_PERK)


def laugh():
    arms = [A.hang(0, upper_rot=12, fore_rot=-14, shoulder_dy=-4), A.hang(1, upper_rot=12, fore_rot=-14, shoulder_dy=-4)]
    return F.Fig(arms=arms, legs=roar_legs(), body=(0, -1), head=(0, 1), collar=False,
                 face=(laugh_face(), G.X0, G.Y0), spikes=PZ.lerp_spikes(PZ.SP_PERK, PZ.SP_IDLE, 0.5))


# ------------------------------------------------------------------ f3-f5 the BOOMBURST
def windup():
    """Sumo-wide, the hips sunk, leaning back: the chin up off a neck, the chest blown up like a drum,
    fists clenched and pulled in at his sides with the elbows cocked out, cheeks full, the crest flaring."""
    arms = [A.hang(0, upper_rot=38, fore_rot=-30, shoulder_dy=0), A.hang(1, upper_rot=38, fore_rot=-30, shoulder_dy=0)]
    face = FF.puffed(G.BR_ANGRY, G.EY_WIDE)
    return F.Fig(arms=arms, legs=wide_legs(4, 7, creases=KNEE_F3), body=(0, 2), head=(0, -2), neck=True,
                 torso_fn=lambda: puffed_shirt(3.8), face=(face, G.X0, G.Y0), spikes=PZ.SP_BRISTLE)


SPLAY_L, SPLAY_R = EH.hand(0), EH.hand(1)


def back_arms(d=0):
    """Both arms flung back and up behind him, fingers splayed: drawn behind the body, so the torso
    covers the shoulders' inner halves (the ports half turned away) and the crest overlaps the hands."""
    left = A.bent(0, (25, 55 + d), (23, 56 + d), (14, 47 + d), (12, 38 + d), hand=SPLAY_L, layer='back')
    right = A.bent(1, (71, 55 + d), (73, 56 + d), (82, 47 + d), (84, 38 + d), hand=SPLAY_R, layer='back')
    return [left, right]


def blast():
    """Lunging into it: the hips dropped into the widest squat, the chest thrown out, the head thrust
    forward over it, the jaw at its deepest, the red eyes, the crest blown flat back by his own blast."""
    return F.Fig(roar=True, collar=False, arms=back_arms(0), legs=wide_legs(5, 7), body=(0, 3), head=(0, 0),
                 torso_fn=lambda: puffed_shirt(2.8), face=(G.ROAR_DEEP, G.X0, G.Y0), spikes=SP_BLOWN)


# the recoil: the roar's red eyes and snarl over the yell's jaw, a texel less gape than the blast
HOLD_FACE = G.ROAR[:43 - G.Y0] + B.rows_of(G.YELL_ROWS)


def hold():
    """The recoil and hold: the hips come up a little out of the lunge, the arms swing back round to
    hang flared at his sides, the crest settles from blown-back to the roar's flare, still roaring."""
    arms = [A.hang(0, upper_rot=30, fore_rot=4, shoulder_dy=-2), A.hang(1, upper_rot=30, fore_rot=4, shoulder_dy=-2)]
    return F.Fig(roar=True, collar=False, arms=arms, legs=wide_legs(3, 7), body=(0, 2), head=(0, 0),
                 torso_fn=lambda: puffed_shirt(2.0), face=(HOLD_FACE, G.X0, G.Y0),
                 spikes=PZ.lerp_spikes(SP_BLOWN, PZ.SP_ROAR, 0.5))


def figs():
    return [inhale(), psych(), laugh(), windup(), blast(), hold()]
