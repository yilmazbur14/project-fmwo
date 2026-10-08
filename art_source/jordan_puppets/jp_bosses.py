"""Jordan's puppets: the per-boss RECIPE DATA the treatment (jp_core.treat) runs on.

For each boss:
  sheet / frame / feet / idle   his finale idle, exactly as JordanFinaleLayout.CAMEOS plays it
  table        every colour of his palette -> (material, puppet key). Covers his idle AND every fight
               sheet (jp_export --carry reports any colour a sheet adds that the table lacks).
  parts        boxes on his KEY frame (the idle frame listed first), tracked into any other frame.
  overlays     hand-drawn touches as data, in KEY-frame coordinates, each riding one part.
  tatter       which cloth hems get the automatic V-notch cut.
  hooks        string points: head, back, wrist_l, wrist_r, knee_l, knee_r (texels on the key frame).
               "l"/"r" are SCREEN left/right on the unflipped sheet. The back point is recorded, not
               drawn: it is between the shoulder blades, behind the body in every front view.

Nothing in this module reads or writes files beyond what jp_core reads (the source PNGs).
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jp_core as C  # noqa: E402


class Boss:
    def __init__(self, name, title, sheet, frame, feet, idle, table, parts=None, overlays=None,
                 tatter=None, hooks=None, fx_specks=(), fallback=None, notes=(), carry=(), tables=(),
                 regions=(), frame_data=None):
        self.name, self.title = name, title
        self.sheet, self.fw, self.fh = sheet, frame[0], frame[1]
        self.feet = feet
        self.idle = list(idle)
        self.table = C.table(table)
        self.parts = parts or {}
        self.overlays = overlays or []
        self.tatter = tatter or []
        self.hooks = hooks or {}
        self.fx_specks = set(fx_specks)
        self.fallback = fallback
        self.notes = list(notes)
        self.carry = list(carry)          # (sheet, frame width) pairs for the carry test
        # another form drawn in its own palette (Danny's sumo): sheets under a path prefix use its table
        self.tables = [(prefix, C.table(t)) for prefix, t in tables]
        # {name, part, boxes (key-frame coords), table}: a prop's own colour mapping inside boxes
        self.regions = [dict(r, table=C.table(r['table'])) for r in regions]
        # per sheet (path under Assets/Characters): {'parts': {frame: {part: (dx, dy) or None}},
        # 'regions': {region: [boxes in that sheet's frame texels]}, 'hooks': {frame: {hook: ((x, y),
        # stamp or None) or None}}}: the hand-set data for frames the tracker cannot read
        self.frame_data = frame_data or {}

    def table_for(self, sheet_rel):
        for prefix, t in self.tables:
            if sheet_rel and sheet_rel.replace(chr(92), '/').startswith(prefix):
                return t
        return self.table

    def key_frame(self):
        return C.frame(self.sheet, self.fw, self.fh, self.idle[0])

    def src(self, f=None, sheet=None, fw=None, fh=None):
        return C.frame(sheet or self.sheet, fw or self.fw, fh or self.fh, self.idle[0] if f is None else f)


BOSSES = {}


def add(b):
    BOSSES[b.name] = b
    return b


# Shared stamps -------------------------------------------------------------------------------
# A string ring (screw eye) seen face-on: an iron loop round a black hole, inside its own keyline.
# The anchor (0, 0) is the hole: the texel the engine ties the string to. 'H' is its glint (bone in
# take A, rune-blue in take B). Every ring sits wholly INSIDE the silhouette (the twin rule).
RING = C.stamp(-2, -2, '''
|.KKK.|
|KjHjK|
|KiKiK|
|KpipK|
|.KKK.|
''')
# The small ring for the 64-texel cast (Danny, Mason, Liam) and for thin limbs: a 3x3 loop.
RING_S = C.stamp(-1, -1, '''
|jHj|
|iKi|
|pip|
''')


def ring_hook(part, x, y, stamp=None):
    return {'part': part, 'at': (x, y), 'stamp': RING if stamp is None else stamp}


def back_hook(part, x, y, fallback=('crown', 'head')):
    """Between the shoulder blades: recorded for the engine, never drawn (behind the body). Where the
    torso is not recognisable (a roar redraws his chest) it rides the head instead."""
    return {'part': part, 'at': (x, y), 'stamp': None, 'behind': True, 'fallback': tuple(fallback)}


def ov(name, part, px, on=None, off=None):
    return {'name': name, 'part': part, 'px': px, 'on': on, 'off': off}


SKIN = ('skin',)

# ============================================================================= GREYSON
# The house skin ramp is shared by Greyson, Matt, Carter and Josh: one mapping serves all four.
HOUSE_SKIN = '''
skin  A5  FBD6B0
skin  A4  F0B98E
skin  A3  DB976C
skin  A2  B86C4E
skin  D2  84412F
skin  P1  552619
'''

GREYSON_TABLE = 'line K 000000\n' + HOUSE_SKIN + '''
# strawberry-blonde mane, brows, moustache -> bleached bone: light hair keeps its value (it is
# the first thing that says "Greyson"), dark hair goes pitch (see the hair rule in jp_export)
hair  B1  FFF1B4 F7D06A
hair  A5  E5A548
hair  A4  C27434
hair  A3  8C4522
# purple posing trunks + the arm cannon (Computah's paint ramp) -> blood
cloth R4  C892F2 A063DC
cloth R3  7C3BB4
cloth R2  592687
cloth R1  391555
# whites: boots, teeth, sclera, glints; the barbell bar -> bone
bone  B1  FFFFFF
bone  A5  D5D9EC
bone  A3  9DA1C0
# charcoal boot soles -> pitch
pitch D2  3F3F52
pitch P1  2A2A38
# barbell plates -> iron
metal I2  3C4757
metal P1  1A212C
# gold wire glasses -> blood-red wire (iron wire vanished into the ash and read as a visor)
metal R4  FFE98C
metal R3  D4A23A
# the blue eyes glow by colour too, so they burn on the frames the socket overlay cannot reach (his
# profile over the shoulder, the tumbles); where it does reach, it repaints them as on the idle
eye   G1  1E3566
eye   G2  639BFF
eye   R3  B4DCFF
# the forehead vein -> blood, bright on the ash
vein  R4  D95763
vein  R2  9E3A48
'''

MATT_TABLE = 'line K 000000\n' + HOUSE_SKIN + '''
# Exploud lavender: the sweatshirt and trainers -> blood
cloth R4  DCDEFF B3B6F2 8E91DA
cloth R3  6D6FBC
cloth R2  4F4D96
cloth R1  332F68
# Exploud butter yellow: dyed tips, ribbing, port rims -> bone
trim  B1  FFF6BE F8DB66
trim  A5  E2B13C
trim  A4  AC7C26
trim  A2  6A4618
# blue-black hair -> pitch (its lavender sheen turns ash)
hair  A3  5C5480
hair  A2  3C3654
hair  D2  272337
hair  P1  15121F
# mouth: throat, wall, tongue -> blood
mouth R4  FFC4D0 EE8CA2
mouth R3  C8526E
mouth R2  962C50
mouth R1  5C1634
mouth P1  2C0A1C
# whites: teeth, socks, soles -> bone
bone  B1  FFFFFF
bone  A5  D5D9EC
bone  A3  9DA1C0
# the roar's red eyes -> glow
eye   G1  FFD6DC FF4A58
eye   G2  CF1E38
eye   R1  780C24
# charcoal: trousers, speaker cones -> pitch
pitch A2  5A5A70 3F3F52
pitch D2  2A2A38
pitch P1  1A1A25
# the shout's sound rings (effect frames only) -> bone
fx    B1  F2F3FF
fx    A5  C4C9FA
'''

# ---- Greyson: the key frame is idle f0 (barbell on the left shoulder, arm cannon hanging right).
GREYSON_PARTS = {
    'head': {'box': (38, 26, 72, 50), 'radius': 12, 'min': 0.55},
    'torso': {'box': (46, 50, 72, 76), 'radius': 12, 'min': 0.5},
    'arm_l': {'box': (16, 48, 46, 78), 'radius': 14, 'min': 0.5},
    'arm_r': {'box': (74, 48, 108, 100), 'radius': 14, 'min': 0.5},
    'leg_l': {'box': (36, 78, 56, 111), 'radius': 10, 'min': 0.55},
    'leg_r': {'box': (57, 78, 78, 111), 'radius': 10, 'min': 0.55},
    # small features the hooks ride: they stay recognisable when a whole limb does not
    'crown': {'box': (46, 26, 66, 36), 'radius': 14, 'min': 0.7},
    'fist_l': {'box': (34, 52, 47, 66), 'radius': 16, 'min': 0.7},
    'muzzle_r': {'box': (88, 84, 108, 100), 'radius': 16, 'min': 0.7},
    'knee_l': {'box': (38, 88, 56, 100), 'radius': 8, 'min': 0.7},
    'knee_r': {'box': (57, 88, 75, 100), 'radius': 8, 'min': 0.7},
}
GREYSON_OVERLAYS = [
    # Sockets: the lens strip goes dark and each pupil burns (sclera -> socket, iris -> halo, pupil -> core)
    ov('sockets', 'head', C.merge(
        C.stamp(49, 38, '|dhgh|'), C.stamp(60, 38, '|hghd|'),
        C.stamp(48, 41, '|------|'), C.stamp(59, 41, '|------|'))),
    # Marionette jaw: two seams from the mouth corners straight down to the chin line
    ov('jaw', 'head', C.merge(C.stamp(51, 47, '|K|\n|K|\n|K|'), C.stamp(61, 47, '|K|\n|K|\n|K|'))),
    # The autopsy seam down the sternum to the navel: a raw red cut laced with black stitches
    ov('seam', 'torso', C.merge(
        C.stamp(57, 52, '\n'.join(['|2|'] * 21)),
        *[C.stamp(56, y, '|SSS|') for y in range(53, 73, 3)]), on=SKIN),
    # Torn open over the ribs on his right side: three ribs slanting down toward the sternum, the
    # hole's upper lip in shadow (black), its lower lip raw (blood). Skin and its lines only, so an arm
    # swung across his side (the spirit shot) hides it
    ov('ribs', 'torso', C.stamp(62, 61, """
|.KKKK..|
|K111wK.|
|K11wl12|
|K1wl112|
|2wl11w2|
|21111l2|
|.21wl2.|
|..222..|
"""), on=('skin', 'line')),
]
GREYSON_TATTER = [
    # the trunks' leg openings, torn over the thighs
    {'part': 'torso', 'mats': ('cloth',), 'centre_x': 57, 'rows': (76, 84), 'cols': (44, 72), 'inner': True,
     'seed': 11, 'depth': 2, 'keep': 2},
]
GREYSON_HOOKS = {
    'head': ring_hook('crown', 56, 28),
    'back': back_hook('torso', 57, 57),
    'wrist_l': ring_hook('fist_l', 39, 53),
    'wrist_r': ring_hook('muzzle_r', 100, 88),
    'knee_l': ring_hook('knee_l', 47, 95),
    'knee_r': ring_hook('knee_r', 66, 95),
}

# His back views (pose_a, pose_c: the lat spread and the back double biceps from behind): the string
# ties on in plain sight, so its ring is drawn there, on the spine between the shoulder blades just
# under the hair (the back is drawn identically in all six frames).
GREYSON_FRAMES = {
    rel: {'hooks': {f: {'back': ((57, 61), RING)} for f in range(3)}}
    for rel in ('Greyson/greyson_pose_a.png', 'Greyson/greyson_pose_c.png')
}
# The spirit shot's last frame swings the cannon across his chest, so the whole-torso match fails;
# its uncovered lower left matches the idle exactly (0.97 at no offset), so the torso is pinned there
GREYSON_FRAMES['Greyson/greyson_spirit.png'] = {'parts': {3: {'torso': (0, 0)}}}
add(Boss('greyson', 'Greyson', 'Greyson/greyson_idle.png', (112, 112), (56, 111), [0, 1, 2, 3], GREYSON_TABLE,
         parts=GREYSON_PARTS, overlays=GREYSON_OVERLAYS, hooks=GREYSON_HOOKS, tatter=GREYSON_TATTER,
         frame_data=GREYSON_FRAMES,
         carry=[('Greyson/greyson_pose_a.png', 112), ('Greyson/greyson_pose_b.png', 112),
                ('Greyson/greyson_pose_c.png', 112), ('Greyson/greyson_pose_hit.png', 112),
                ('Greyson/greyson_spirit.png', 112), ('Greyson/greyson_hit.png', 112),
                ('Greyson/greyson_juggle.png', 192)]))

# ---- Matt: the key frame is idle f0 (the easy grin, arms down).
MATT_PARTS = {
    'head': {'box': (24, 1, 72, 52), 'radius': 12, 'min': 0.55},
    'torso': {'box': (30, 50, 66, 72), 'radius': 10, 'min': 0.5},
    'arm_l': {'box': (10, 50, 30, 84), 'radius': 10, 'min': 0.5},
    'arm_r': {'box': (66, 50, 86, 84), 'radius': 10, 'min': 0.5},
    'leg_l': {'box': (28, 72, 48, 95), 'radius': 8, 'min': 0.55},
    'leg_r': {'box': (48, 72, 68, 95), 'radius': 8, 'min': 0.55},
    'crown': {'box': (40, 0, 56, 20), 'radius': 14, 'min': 0.7},
    'hand_l': {'box': (10, 70, 28, 84), 'radius': 12, 'min': 0.7},
    'hand_r': {'box': (68, 70, 86, 84), 'radius': 12, 'min': 0.7},
    'knee_l': {'box': (30, 74, 46, 86), 'radius': 8, 'min': 0.7},
    'knee_r': {'box': (50, 74, 66, 86), 'radius': 8, 'min': 0.7},
}
MATT_OVERLAYS = [
    ov('sockets', 'head', C.merge(
        C.stamp(39, 36, '|dhgd|'), C.stamp(40, 37, '|dd|'),
        C.stamp(54, 36, '|dghd|'), C.stamp(55, 37, '|dd|'),
        C.stamp(38, 38, '|-----|'), C.stamp(53, 38, '|-----|'))),
    ov('jaw', 'head', C.merge(C.stamp(43, 48, '|K|\n|K|\n|K|\n|K|'), C.stamp(54, 48, '|K|\n|K|\n|K|'))),
    # A rip in the sweatshirt, lower left: three ribs slanting down toward the middle
    ov('rip', 'torso', C.stamp(36, 58, """
|.K.KK.K.|
|KaKwaKaK|
|K1wl111K|
|Kwl11w1K|
|K11wl11K|
|K1wl11wK|
|.KaKaaK.|
|..K.KK..|
""")),
]
MATT_TATTER = [
    # the trouser legs, torn over the socks
    {'part': 'torso', 'mats': ('pitch',), 'centre_x': 48, 'rows': (80, 86), 'cols': (28, 68), 'inner': True,
     'seed': 5, 'depth': 2, 'keep': 3},
]
MATT_HOOKS = {
    'head': ring_hook('crown', 48, 12),
    'back': back_hook('torso', 48, 58),
    'wrist_l': ring_hook('hand_l', 14, 72),
    'wrist_r': ring_hook('hand_r', 82, 72),
    'knee_l': ring_hook('knee_l', 38, 80),
    'knee_r': ring_hook('knee_r', 58, 80),
}
# His defeat: he crumples (f2) and sits with his doll (f3-5); the chest is partly hidden by his hands
# and the doll, so the whole-torso match dips under its threshold on f2 and f5. Its neighbours say
# where it is (f2 halfway down at +4; f5 sat, as f3-4, at +10): pinned, so the rip does not blink.
MATT_FRAMES = {
    'Matt/matt_defeat.png': {'parts': {2: {'torso': (0, 4)}, 5: {'torso': (0, 10)}}},
}
add(Boss('matt', 'Matt', 'Matt/matt_idle.png', (96, 96), (48, 95), [0, 1, 2, 3], MATT_TABLE,
         parts=MATT_PARTS, overlays=MATT_OVERLAYS, hooks=MATT_HOOKS, tatter=MATT_TATTER, frame_data=MATT_FRAMES,
         carry=[('Matt/matt_yell_tell.png', 96), ('Matt/matt_yell_up.png', 96), ('Matt/matt_roar.png', 96)]))


# ============================================================================= CAPTAIN BURAK
BURAK_TABLE = '''
line  K   000000
# skin (his own warm ramp) -> ash
skin  A5  E2A874
skin  A4  D79864
skin  A3  BE8254 A88068
skin  A2  AC714F
skin  D2  7C5438
mouth R2  C8705E
# dark brown hair -> pitch
hair  P1  0D0909
hair  D2  1A1212 2A1D19
hair  A2  36251E
hair  A3  503729
# the captain's coat, feather, sash -> blood (it was red already: it goes deeper)
cloth R1  4A0C1B
cloth R2  7E162B 6E1F22
cloth R3  B02436 AC3232
cloth R4  D8434F D95763
# tricorn, boots, trousers -> pitch
pitch P1  15151D 23232F
pitch D2  353547 281810
pitch A2  4E4F66 5C3B28
# gold braid, buttons, buckle -> bone
trim  A3  7A5216
trim  A4  B07D22
trim  A5  E0AB35
trim  B1  F5D94E FFF3B0
# the shirt -> bone linen
bone  A4  C3B9A9
bone  A5  E8E1D3
bone  B1  FFFCF4
# cutlass, flintlock barrel, chain -> iron
metal I2  444A5C
metal I3  6D7589
metal A4  A6AFC1
metal B1  DCE3EE
'''

BURAK_PARTS = {
    'head': {'box': (20, 1, 72, 49), 'radius': 12, 'min': 0.55},
    'face': {'box': (34, 24, 62, 49), 'radius': 12, 'min': 0.6},
    'crown': {'box': (36, 1, 60, 10), 'radius': 12, 'min': 0.7},
    'torso': {'box': (36, 48, 60, 80), 'radius': 10, 'min': 0.5},
    'fist_l': {'box': (24, 50, 37, 70), 'radius': 14, 'min': 0.65},
    'hand_r': {'box': (64, 60, 76, 72), 'radius': 14, 'min': 0.65},
    'knee_l': {'box': (36, 84, 47, 94), 'radius': 8, 'min': 0.7},
    'knee_r': {'box': (49, 84, 60, 94), 'radius': 8, 'min': 0.7},
}
BURAK_OVERLAYS = [
    ov('sockets', 'face', C.merge(
        C.stamp(39, 33, '|dhghd|'), C.stamp(39, 34, '|-ddd-|'),
        C.stamp(54, 33, '|hghd|'), C.stamp(53, 34, '|-ddd-|'),
        C.stamp(38, 35, '|.---.|'), C.stamp(53, 35, '|.---.|'))),
    ov('jaw', 'face', C.merge(C.stamp(42, 43, '\n'.join(['|K|'] * 6)), C.stamp(54, 42, '\n'.join(['|K|'] * 7)))),
    # a stitched scar down the lit cheek
    ov('scar', 'face', C.merge(C.stamp(37, 35, '\n'.join(['|2|'] * 6)),
                               *[C.stamp(36, y, '|SSS|') for y in (36, 38, 40)]), on=SKIN),
]
BURAK_TATTER = [
    # the coat tails' braided hems, ragged
    {'part': 'torso', 'mats': ('cloth', 'trim'), 'centre_x': 48, 'rows': (84, 90), 'seed': 3, 'depth': 4, 'keep': 3,
     'spacing': (2, 5), 'depths': (2, 3, 3, 4)},
]
BURAK_HOOKS = {
    'head': ring_hook('crown', 48, 3),
    'back': back_hook('torso', 48, 58),
    'wrist_l': ring_hook('fist_l', 26, 61),
    'wrist_r': ring_hook('hand_r', 73, 66),
    'knee_l': ring_hook('knee_l', 41, 87),
    'knee_r': ring_hook('knee_r', 54, 87),
}
BURAK_GUN = '''
# the flintlock's brass and steel -> dark iron (the coat's gold braid and the cutlass, drawn in the
# same colours, stay bone and bright steel)
metal P1  7A5216 444A5C
metal I2  B07D22 6D7589
metal I3  E0AB35 A6AFC1 DCE3EE
metal B1  F5D94E FFF3B0
'''
# His powder kegs (BurakBoss/FX/: the barrel he lays, its break, its landing), drawn in his palette:
# the keg's wood is his skin ramp and its hoops his hat's navy, so as a PROP it gets its own table:
# a charred black keg bound in bone hoops, the blood-red X, and a fuse burning in the family's glow.
BURAK_KEG_TABLE = '''
line  K   000000
wood  A3  E2A874 D79864
wood  A2  BE8254
wood  D2  AC714F 5C3B28
wood  P1  7C5438 2A1D19 281810
metal B1  A6AFC1
metal A5  6D7589
metal A4  353547
metal A3  23232F
metal P1  15151D
cloth R4  D8434F
cloth R3  B02436
fx    G1  F5D94E FFF3B0
fx    G2  E0AB35
bone  A4  C3B9A9
bone  A5  E8E1D3
'''
BURAK_REGIONS = [
    {'name': 'flintlock', 'part': 'hand_r', 'boxes': [(62, 69, 68, 75), (69, 62, 88, 91)], 'table': BURAK_GUN},
]
# The flintlock on the sheets where his gun hand leaves its idle place: holstered in the sash
# (throw), aimed at the camera (fire), hanging from his hand (broken, hit). Boxes in each sheet's frame
# texels, clear of the coat's own gold braid.
BURAK_FRAMES = {
    'BurakBoss/burak_throw.png': {'regions': {'flintlock': [(57, 62, 65, 87)]}},
    'BurakBoss/burak_fire.png': {'regions': {'flintlock': [(70, 52, 92, 80)]}},
    'BurakBoss/burak_broken.png': {'regions': {'flintlock': [(69, 62, 91, 94)]}},
    'BurakBoss/burak_hit.png': {'regions': {'flintlock': [(69, 60, 91, 94)]}},
    # his defeat: the gun sags in his hand (f2) and lies on the floor (f3-5); f0-1 track as usual.
    # He sinks 13 texels by the last frame, crying, past the face's 12-texel search: pinned there.
    'BurakBoss/burak_defeat.png': {
        'regions': {'flintlock': {2: [(69, 73, 88, 94)], 3: [(70, 79, 92, 94)], 4: [(70, 79, 92, 94)],
                                  5: [(70, 79, 92, 94)]}},
        'parts': {5: {'face': (0, 13), 'head': (0, 13)}},
    },
}
add(Boss('captain_burak', 'Captain Burak', 'BurakBoss/burak_idle.png', (96, 96), (48, 95), [0, 1, 2, 3], BURAK_TABLE,
         frame_data=BURAK_FRAMES,
         parts=BURAK_PARTS, overlays=BURAK_OVERLAYS, hooks=BURAK_HOOKS, tatter=BURAK_TATTER, regions=BURAK_REGIONS,
         tables=[('BurakBoss/FX/', BURAK_KEG_TABLE)],
         carry=[('BurakBoss/burak_throw.png', 96), ('BurakBoss/burak_fire.png', 96),
                ('BurakBoss/burak_broken.png', 96), ('BurakBoss/burak_hit.png', 96),
                ('BurakBoss/burak_boss_juggle.png', 192), ('BurakBoss/FX/burak_barrel.png', 48, 'prop')]))


# ============================================================================= DANNY
# The finale's idle is the small Danny (danny_walk f1). His fight's attacks (the butt slams) are the
# SUMO's sheets under Danny/Sumo/, drawn in a wider palette where two of the small Danny's shirt
# shadows (663931, 45283C) are skin: the sumo gets its own table.
DANNY_TABLE = '''
line  K   000000
# skin (DawnBringer ramp) -> ash
skin  A4  EEC39A
skin  A3  D9A066
skin  D2  8F563B
# shirt and shorts (red already) -> blood
cloth R4  D95763
cloth R3  AC3232
cloth R2  663931
cloth R1  45283C
# the striped beanie -> pitch with bone stripes
hat   A5  CBDBFC
hat   D2  5B6EE1
# boots -> pitch
pitch P1  222034
pitch D2  323C39
pitch A2  595652
# gold chain -> bone
trim  B1  FBF236
trim  A4  DF7126
# whites on his other small sheets (flex, grip, tear) -> bone
bone  B1  FFFFFF
# the small Danny's dialogue / intro art only
bone  A4  3F3F74 639BFF
'''
DANNY_SUMO_TABLE = '''
line  K   000000
# the sumo's skin: two more tones, and the small Danny's shirt shadows are skin creases here. Set a
# step lighter than the small Danny's: the sumo's mass is mostly shadow tones, which at A2/D2 went
# muddy against the black keyline
skin  A5  FADCB8 EEC39A
skin  A4  D9A066
skin  A3  B67A4B
skin  A2  8F563B
skin  D2  663931
skin  P1  45283C
# beanie and mawashi blues -> pitch with bone stripes
hat   B1  F0F5FF
hat   A5  CBDBFC
hat   A4  97ABEF
hat   A3  8595B8
hat   A2  7D90F0
hat   D2  639BFF 5B6EE1
hat   P1  3F3F74 222034
# the red neck rope -> blood
cloth R2  7A2430
cloth R3  AC3232
cloth R4  D95763
# gold -> bone
trim  B1  FBF236 FFFBC4
trim  A5  F0B432
trim  A4  DF7126
trim  A3  8A4B1F
# whites: wristbands, the snot bubble, the apron's crest -> bone
bone  B1  FFFFFF
# boots on the evolve sheet
pitch D2  323C39
pitch A2  595652
'''
DANNY_PARTS = {
    'head': {'box': (20, 1, 43, 28), 'radius': 10, 'min': 0.6},
    'face': {'box': (20, 13, 43, 28), 'radius': 10, 'min': 0.6},
    'crown': {'box': (24, 1, 40, 8), 'radius': 10, 'min': 0.7},
    'torso': {'box': (18, 26, 45, 46), 'radius': 10, 'min': 0.5},
    'hand_l': {'box': (9, 40, 20, 49), 'radius': 10, 'min': 0.7},
    'hand_r': {'box': (43, 40, 54, 49), 'radius': 10, 'min': 0.7},
    'knee_l': {'box': (20, 49, 30, 56), 'radius': 8, 'min': 0.7},
    'knee_r': {'box': (33, 49, 43, 56), 'radius': 8, 'min': 0.7},
}
DANNY_OVERLAYS = [
    # his sleepy shut eyes become glowing slits under heavy lids, the bags gone black
    ov('sockets', 'face', C.merge(
        C.stamp(25, 19, '|dhgd|'), C.stamp(35, 19, '|dghd|'),
        C.stamp(25, 20, '|dddd|'), C.stamp(35, 20, '|dddd|'),
        C.stamp(24, 21, '|.--.|'), C.stamp(36, 21, '|.--.|'))),
    ov('jaw', 'face', C.merge(C.stamp(29, 25, '|K|\n|K|\n|K|'), C.stamp(34, 25, '|K|\n|K|\n|K|'))),
    # a stitched gash across the belly
    ov('belly', 'torso', C.merge(
        C.stamp(20, 43, '|22222222|'), C.stamp(28, 42, '|222222|'),
        *[C.stamp(x, 42, '|S|\n|S|\n|S|') for x in (21, 24, 27)],
        *[C.stamp(x, 41, '|S|\n|S|\n|S|') for x in (30, 33)]), on=SKIN),
]
DANNY_TATTER = [
    # the shirt's hem, torn where it rides up over his belly
    {'part': 'torso', 'mats': ('cloth',), 'centre_x': 32, 'rows': (38, 45), 'cols': (18, 46), 'inner': True,
     'seed': 9, 'depth': 2, 'keep': 3, 'spacing': (4, 7), 'depths': (1, 2)},
    # the shorts' legs, a single-texel fray over his shins
    {'part': 'torso', 'mats': ('cloth',), 'centre_x': 32, 'rows': (48, 52), 'inner': True,
     'seed': 4, 'depth': 1, 'keep': 2, 'spacing': (2, 4), 'depths': (1,)},
]
DANNY_HOOKS = {
    'head': ring_hook('crown', 32, 3, RING_S),
    'back': back_hook('torso', 32, 32),
    'wrist_l': ring_hook('hand_l', 12, 45, RING_S),
    'wrist_r': ring_hook('hand_r', 51, 45, RING_S),
    'knee_l': ring_hook('knee_l', 25, 52, RING_S),
    'knee_r': ring_hook('knee_r', 38, 52, RING_S),
}
add(Boss('danny', 'Danny', 'Danny/danny_walk.png', (64, 64), (32, 63), [1], DANNY_TABLE,
         parts=DANNY_PARTS, overlays=DANNY_OVERLAYS, hooks=DANNY_HOOKS, tatter=DANNY_TATTER,
         tables=[('Danny/Sumo/', DANNY_SUMO_TABLE)],
         carry=[('Danny/danny_walk.png', 64)]))


# ============================================================================= ERIC
# The finale's idle is his entrance f3 (no sword in hand: it is planted in the arena). His fight
# sheet (eric_sheet_v2, 40 frames, the greatsword in every frame) shares the palette plus the
# sword's grip leather and a few effect glints, all in this table.
ERIC_TABLE = '''
line  K   000000
# skin -> ash
skin  A5  FDE6CC
skin  A4  F3C9A2
skin  A3  DCA27A
skin  A2  B8795A
skin  D2  9C6038 8A5040
# the great red beard and hair -> blood (red hair keeps its warmth: dried blood)
hair  R4  FFB45E F58A38
hair  R3  DF6C22
hair  R2  B04C16
hair  R1  7A3010
hair  P1  4A1C08
eye   D2  3A2418
# the white plate -> bleached bone: he stays the white knight, now in a dead man's armour
metal B1  FFFFFF EAF0F6
metal A5  CDD7E2
metal A4  A3B1C2
metal A3  7A86A0
metal A2  525A74
# chainmail and the greatsword's steel -> iron
metal B1  D4D8DC
metal I3  A3A8AE 7C8187
metal I2  5C6067 41444B
metal P1  2B2D33
# the crimson cape -> blood
cloth R3  8A1F38
cloth R2  5E142C
cloth R1  3C0C20
# the red cross -> bright blood
cloth R4  E2402F
cloth R3  B0242A
# belt leather and the sword's grip -> pitch
pitch A2  74432A C48A58
pitch D2  4E2C1C
pitch P1  331C12
# buckle -> bone
trim  B1  FFF0A8
trim  A5  F2C457
trim  A4  C48A2C
trim  A3  8A5A1C
# effect glints on the fight sheet
fx    B1  D8F2FF 7CC4F0
fx    I3  3A78C0
fx    R4  FF7A5C
fx    R2  74161F
# ship 2 (09-28): colours his other sheets add. The cape's lit side (the bear hug's flung flap, the
# tumble) -> bright blood; the winded, open mouth -> bright blood; the buckle's deepest shade -> ash
# (one step under the buckle's bone); the bear hug aura's white-hot core -> bone (the aura itself goes
# rune-blue in its own region, ERIC_AURA; these are its few sparks outside it)
cloth R4  B83246
mouth R4  E05A64
trim  A2  5A3A12
fx    B1  FFF7D6
'''
ERIC_PARTS = {
    'head': {'box': (116, 119, 146, 158), 'radius': 14, 'min': 0.55},
    'face': {'box': (120, 126, 142, 142), 'radius': 14, 'min': 0.6},
    'crown': {'box': (120, 119, 143, 128), 'radius': 14, 'min': 0.7},
    'torso': {'box': (112, 150, 152, 178), 'radius': 12, 'min': 0.5},
    'cuff_l': {'box': (96, 170, 112, 186), 'radius': 14, 'min': 0.65},
    'cuff_r': {'box': (150, 170, 166, 186), 'radius': 14, 'min': 0.65},
    'knee_l': {'box': (104, 180, 124, 191), 'radius': 8, 'min': 0.65},
    'knee_r': {'box': (138, 180, 160, 191), 'radius': 8, 'min': 0.65},
}
ERIC_OVERLAYS = [
    ov('sockets', 'face', C.merge(
        C.stamp(124, 135, '|dgh|'), C.stamp(135, 135, '|hgd|'),
        C.stamp(124, 136, '|---|'), C.stamp(135, 136, '|---|'))),
    # the jaw hinges down through the beard from the mouth corners
    ov('jaw', 'face', C.merge(C.stamp(127, 140, '\n'.join(['|K|'] * 5)), C.stamp(134, 140, '\n'.join(['|K|'] * 5)))),
]
ERIC_TATTER = [
    # the cape's hem, ragged
    {'part': 'torso', 'mats': ('cloth',), 'centre_x': 131, 'rows': (178, 191), 'seed': 21, 'depth': 3, 'keep': 3,
     'spacing': (2, 5), 'depths': (2, 3, 3)},
]
ERIC_HOOKS = {
    'head': ring_hook('crown', 131, 122),
    'back': back_hook('torso', 131, 160),
    'wrist_l': ring_hook('cuff_l', 98, 177),
    'wrist_r': ring_hook('cuff_r', 163, 176),
    'knee_l': ring_hook('knee_l', 114, 185),
    'knee_r': ring_hook('knee_r', 148, 185),
}
def minus(full, hole):
    """The box `full` with the box `hole` cut out of it, as up to four boxes (all inclusive)."""
    fx0, fy0, fx1, fy1 = full
    hx0, hy0, hx1, hy1 = hole
    out = []
    if hy0 > fy0:
        out.append((fx0, fy0, fx1, hy0 - 1))
    if hy1 < fy1:
        out.append((fx0, hy1 + 1, fx1, fy1))
    if hx0 > fx0:
        out.append((fx0, hy0, hx0 - 1, hy1))
    if hx1 < fx1:
        out.append((hx1 + 1, hy0, fx1, hy1))
    return out


# THE BEAR HUG'S AURA (approved default, 09-28: his magic glow goes Jordan's rune blue). On the charge
# (plant f0, charge f1-2) a gold flame wraps him in his own buckle's colours; in its region the gold
# goes the family glow, white-hot and bright to G1, the flame's darker body and edge to G2. The region is
# the whole frame but the belt row, where the same colours are his buckle and studs.
ERIC_AURA = '''
glow  G1  FFF7D6 FFF0A8
glow  G2  F2C457 C48A2C 8A5A1C
'''
ERIC_REGIONS = [{'name': 'aura', 'part': 'torso', 'boxes': [], 'table': ERIC_AURA}]
_FULL_ERIC = (0, 0, 255, 191)
# The player in his arms (hug grab f7, squeeze f8-10, toss f11) is the player's own drawing: his colours
# (the blue shirt, dark hair and trousers, skin, the brown shoe) keep their own pixels there.
ERIC_PLAYER = ('5FABEC 2F78D0 1F58A8 112C5E 173E80 B0DCFF 7A7486 5A5466 4A4854 3A3544 33313B 26232B 221F28 '
               '17151B 141218 0F0E12 0C0B0F EFB582 D79864 AC714F 87553C 6A3F2E 5A3A12').split()


def _keep(box):
    return {'boxes': [box], 'colours': ERIC_PLAYER}


def _back(x, y, ring=False):
    """A back point set by hand; `ring`: a back view, where the ring is drawn on his back."""
    return {'back': ((x, y), RING if ring else None)}


ERIC_FRAMES = {
    # the whirlwind: f13-19 turn out of every part the tracker knows (f20 it finds again). f15-17 are his
    # back: the ring is drawn on the cape between the pauldrons, under the collar.
    'Eric/eric_sheet_v2.png': {'hooks': {
        13: _back(128, 157), 14: _back(146, 150), 15: _back(128, 153, True), 16: _back(127, 154, True),
        17: _back(127, 153, True), 18: _back(128, 157), 19: _back(132, 157)}},
    'Eric/eric_bearhug_v2.png': {
        'regions': {'aura': {0: minus(_FULL_ERIC, (113, 175, 141, 182)),
                             1: minus(_FULL_ERIC, (113, 179, 142, 186)),
                             2: minus(_FULL_ERIC, (114, 179, 143, 186))}},
        'keep': {7: _keep((112, 142, 142, 181)), 8: _keep((110, 145, 145, 174)), 9: _keep((116, 147, 140, 181)),
                 10: _keep((119, 147, 136, 181)), 11: _keep((139, 88, 178, 129))},
    },
    # winded: leaning on his sword, 3 texels left of the idle
    'Eric/eric_winded.png': {'hooks': {f: _back(128, 160) for f in range(4)}},
    # broken: knocked back (f1), then kneeling and slumping; f0 tracks
    'Eric/eric_broken.png': {'hooks': {
        1: _back(131, 155), 2: _back(120, 163), 3: _back(126, 163), 4: _back(126, 165), 5: _back(129, 166),
        6: _back(130, 167), 7: _back(129, 167)}},
    # the juggle tumbles: no back point, as on every shipped juggle
    'Eric/eric_juggle.png': {'hooks': {f: {'back': None} for f in range(10)}},
}
add(Boss('eric', 'Eric', 'Eric/eric_entrance.png', (256, 192), (128, 191), [3], ERIC_TABLE,
         parts=ERIC_PARTS, overlays=ERIC_OVERLAYS, hooks=ERIC_HOOKS, tatter=ERIC_TATTER,
         regions=ERIC_REGIONS, frame_data=ERIC_FRAMES,
         carry=[('Eric/eric_sheet_v2.png', 256)]))


# ============================================================================= MASON
# The finale's idle is mason_sheet f0-1. The nugget costume is his whole body: its breading goes
# BONE (a bleached nugget: it keeps the light, breaded read that says "Mason"; a blood-red nugget read
# as a red hoodie), the comb and tongue stay blood, the beak ring, chicken feet and earmuffs go bone,
# and his own face goes ash (kept a step darker, as his complexion is).
MASON_TABLE = '''
line  K   000000
# the nugget's breading -> bone
cloth B1  FADCB8
cloth A5  EEC39A
cloth A4  D6AA7C
cloth A3  AE8358
# the comb -> blood; its highlight and his tongue -> bright blood
comb  R3  AC3232
mouth R4  D95763
# the beak ring and the chicken feet -> bone
trim  B1  FBF236
trim  A5  D4CC2E
trim  A3  726E17
# the chicken legs -> bone, darker
trim  A4  A09050
trim  A2  605020
# his face -> ash, a step darker than the cast (his complexion is)
skin  A3  90765E
skin  A2  7D5631
# the earmuffs, eye whites, teeth -> bone
bone  B1  FFFFFF
# on his other frames: the nugget bucket (red and white), the nuggets in it, the phone, sweat, stink
cloth R2  7A2A30
bone  A5  CBDBFC
bone  A4  9BADB7
cloth R3  D9A066
cloth R1  8F563B 45283C
pitch P1  1A1A1A
pitch A2  666666
fx    G2  639BFF
fx    A3  4B692F
'''
MASON_PARTS = {
    'head': {'box': (12, 1, 52, 31), 'radius': 10, 'min': 0.6},
    'face': {'box': (26, 15, 38, 28), 'radius': 10, 'min': 0.6},
    'crown': {'box': (22, 1, 42, 10), 'radius': 10, 'min': 0.7},
    'torso': {'box': (14, 30, 50, 52), 'radius': 10, 'min': 0.5},
    'arm_l': {'box': (3, 38, 16, 49), 'radius': 10, 'min': 0.7},
    'arm_r': {'box': (47, 38, 61, 49), 'radius': 10, 'min': 0.7},
    'leg_l': {'box': (20, 52, 29, 57), 'radius': 6, 'min': 0.7},
    'leg_r': {'box': (34, 52, 43, 57), 'radius': 6, 'min': 0.7},
}
MASON_OVERLAYS = [
    ov('sockets', 'face', C.merge(
        C.stamp(28, 17, '|ddd|\n|dgd|\n|dhd|'), C.stamp(33, 17, '|ddd|\n|dgd|\n|dhd|'))),
    # the costume split open down its front and laced shut
    ov('seam', 'torso', C.merge(
        C.stamp(31, 33, '\n'.join(['|2|'] * 16)),
        *[C.stamp(30, y, '|SSS|') for y in range(34, 49, 3)]), on=('cloth',)),
]
MASON_TATTER = [
    {'part': 'torso', 'mats': ('cloth',), 'centre_x': 32, 'rows': (44, 53), 'seed': 13, 'depth': 2, 'keep': 3,
     'spacing': (2, 5), 'depths': (1, 2, 2)},
]
MASON_HOOKS = {
    'head': ring_hook('crown', 32, 5, RING_S),
    'back': back_hook('torso', 32, 40),
    'wrist_l': ring_hook('arm_l', 7, 44, RING_S),
    'wrist_r': ring_hook('arm_r', 56, 44, RING_S),
    'knee_l': ring_hook('leg_l', 24, 55, RING_S),
    'knee_r': ring_hook('leg_r', 39, 55, RING_S),
}
# Ship 2 (09-28). The squat (poop f6) screws his eyes shut, < >: the sockets overlay would light two
# round pupils over them, so the squint itself is lit instead (as Danny's slam), by hand. The defeated
# slump (f14) drops his head 16 texels, past the tracker's reach: its back point is set by hand.
MASON_FRAMES = {
    'Mason/mason_sheet.png': {
        'overlays': {6: [ov('squint', None, C.merge(C.stamp(28, 23, '|mgh|\n|gmm|\n|mgh|'),
                                                    C.stamp(33, 23, '|hgm|\n|mmg|\n|hgm|')))]},
        'hooks': {14: {'back': ((31, 50), None)}},
    },
    'Mason/mason_juggle.png': {'hooks': {f: {'back': None} for f in range(12)}},
}
add(Boss('mason', 'Mason', 'Mason/mason_sheet.png', (64, 64), (32, 63), [0, 1], MASON_TABLE,
         parts=MASON_PARTS, overlays=MASON_OVERLAYS, hooks=MASON_HOOKS, tatter=MASON_TATTER,
         frame_data=MASON_FRAMES,
         carry=[('Mason/mason_sheet.png', 64), ('Mason/mason_juggle.png', 128)]))


# ============================================================================= JOSH
# The finale's idle is josh_idle f0-3: the card-thrower, wide crimson hat with a card in the band,
# cream long coat with red lapels, blue vest, a fan of cards. The coat and the cards share their
# creams, so both go bone together (cards are bone-white paper; the coat a yellowed shroud) and no
# region is needed to tell them apart.
JOSH_TABLE = 'line K 000000\n' + HOUSE_SKIN + '''
skin  A3  E0917C
# brown hair and beard -> pitch
hair  A3  8A5B3D
hair  A2  5F3C29
hair  D2  3D261A
hair  P1  24160F 130B09
# the hat, lapels, gloves, card pips -> blood (it was crimson already)
cloth R4  C96C74 E8605A
cloth R3  A63B4B C2283A
cloth R2  861826 7A2032
cloth R1  4D1420 4A0C16
cloth P1  2B0A12
# the cream coat and the cards -> bone
bone  B1  F6EFDC
bone  A5  E6DBBE
bone  A4  C8B994
bone  A3  9E8D68
bone  A2  6B5D44
# the blue vest and navy trousers -> pitch
pitch A2  5E63A0
pitch D2  45487F 20203C
pitch P1  32335C 14142A
# gold buttons, chain, the spade badge -> bone
trim  B1  F5D94E FFF3B0
trim  A5  E0AB35
trim  A4  B07D22
trim  A3  7A5216
# glints and the card-throw flare on his fight sheets
bone  B1  FFFFFF
fx    G2  E07A2C
'''
JOSH_PARTS = {
    'head': {'box': (19, 5, 62, 36), 'radius': 10, 'min': 0.55},
    'face': {'box': (30, 19, 52, 36), 'radius': 10, 'min': 0.6},
    'crown': {'box': (28, 5, 50, 15), 'radius': 10, 'min': 0.7},
    'torso': {'box': (27, 29, 56, 58), 'radius': 10, 'min': 0.5},
    'hand_l': {'box': (12, 38, 26, 50), 'radius': 12, 'min': 0.65},
    'hand_r': {'box': (44, 47, 56, 58), 'radius': 12, 'min': 0.65},
    'coat': {'box': (22, 56, 58, 71), 'radius': 8, 'min': 0.6},
    'knee_l': {'box': (35, 58, 42, 70), 'radius': 8, 'min': 0.7},
    'knee_r': {'box': (43, 58, 50, 70), 'radius': 8, 'min': 0.7},
}
JOSH_OVERLAYS = [
    ov('sockets', 'face', C.merge(
        C.stamp(37, 26, '|dhgd|'), C.stamp(45, 26, '|hgd|'),
        C.stamp(37, 27, '|---|'), C.stamp(45, 27, '|---|'))),
    # the jaw hinge cut through the black beard: a black seam with a lit lip on the jaw's side
    ov('jaw', 'face', C.merge(C.stamp(39, 33, '|Km|\n|Km|\n|Km|'), C.stamp(45, 33, '|mK|\n|mK|\n|mK|'))),
    # the long coat torn and laced up across its left tail
    ov('seam', 'coat', C.merge(
        C.stamp(26, 58, '|2.......|\n|.2......|\n|..2.....|\n|...2....|\n|....2...|\n|.....2..|\n|......2.|'),
        C.stamp(26, 59, '|S|'), C.stamp(28, 61, '|S|'), C.stamp(30, 63, '|S|'),
        C.stamp(27, 57, '|S|'), C.stamp(29, 59, '|S|'), C.stamp(31, 61, '|S|')), on=('bone',)),
]
JOSH_TATTER = [
    # the coat tails' hem, ragged
    {'part': 'coat', 'mats': ('bone',), 'centre_x': 40, 'rows': (66, 71), 'seed': 17, 'depth': 3, 'keep': 3,
     'spacing': (2, 5), 'depths': (2, 3, 3)},
]
JOSH_HOOKS = {
    'head': ring_hook('crown', 48, 10, RING_S),
    'back': back_hook('torso', 42, 45),
    'wrist_l': ring_hook('hand_l', 22, 46, RING_S),
    'wrist_r': ring_hook('hand_r', 50, 51, RING_S),
    'knee_l': ring_hook('knee_l', 38, 64, RING_S),
    'knee_r': ring_hook('knee_r', 46, 64, RING_S),
}
# Ship 2 (09-28): his card magic goes Jordan's rune blue (approved default). The flare round a thrown
# card, the throw's arc, the sparkles, the spade sigil and the card trail are drawn in the same golds
# as his buttons, chain, hat band and cuffs, so they get their own region, boxed frame by frame, clear of
# his costume. The orange flare edge (E07A2C) is magic-only and already glows by his table. The hit
# and defeat frames' impact stars are not his magic: they stay as his table has them.
JOSH_MAGIC = '''
glow  G1  FFF3B0 F5D94E
glow  G2  E0AB35 B07D22 7A5216
'''
JOSH_REGIONS = [{'name': 'magic', 'part': 'torso', 'boxes': [], 'table': JOSH_MAGIC}]
JOSH_FRAMES = {
    'Josh/josh_throw.png': {
        # the flare round the cocked card (f0), the arc as it leaves (f1), the sparkles (f2)
        'regions': {'magic': {0: [(49, 20, 65, 37)], 1: [(58, 21, 76, 42)], 2: [(70, 33, 79, 44)]}},
        # f1: the hat tips and the tracker loses his crown (0.67 of 0.7); set at the crown's own offset
        # there, the head ring stays on all four frames of the throw
        'hooks': {1: {'head': ((52, 11), RING_S)}},
    },
    'Josh/josh_intro.png': {'regions': {'magic': {
        0: [(3, 17, 9, 23), (66, 19, 72, 25)], 1: [(0, 17, 21, 23), (0, 30, 15, 49)], 2: [(9, 29, 13, 33)],
        3: [(66, 14, 70, 18)], 4: [(53, 9, 74, 25)], 5: [(65, 29, 79, 66), (58, 67, 79, 78)]}}},
    'Josh/josh_mount.png': {'regions': {'magic': {
        0: [(55, 61, 67, 79)], 1: [(59, 70, 63, 74)], 2: [(72, 41, 74, 44)]}}},
    'Josh/josh_dismount.png': {'regions': {'magic': {
        1: [(16, 75, 20, 79), (61, 75, 65, 79)], 2: [(6, 30, 12, 36), (22, 29, 26, 33)]}}},
    # his back points where no part of the idle is left to track: the hit's recoil, the recovery crouch,
    # the defeat's fall to his knees (a point 3 texels under the collar, as on the idle)
    'Josh/josh_hit.png': {'hooks': {0: {'back': ((39, 45), None)}, 1: {'back': ((40, 45), None)}}},
    'Josh/josh_recovery.png': {'hooks': {0: {'back': ((49, 55), None)}, 1: {'back': ((49, 54), None)},
                                         2: {'back': ((49, 53), None)}, 3: {'back': ((49, 54), None)}}},
    'Josh/josh_defeat.png': {'hooks': {0: {'back': ((38, 45), None)}, 1: {'back': ((39, 48), None)},
                                       2: {'back': ((44, 52), None)}, 3: {'back': ((44, 57), None)},
                                       4: {'back': ((44, 57), None)}, 5: {'back': ((44, 57), None)}}},
    'Josh/josh_juggle.png': {'hooks': {f: {'back': None} for f in range(12)}},
}
add(Boss('josh', 'Josh', 'Josh/josh_idle.png', (80, 80), (40, 79), [0, 1, 2, 3], JOSH_TABLE,
         parts=JOSH_PARTS, overlays=JOSH_OVERLAYS, hooks=JOSH_HOOKS, tatter=JOSH_TATTER,
         regions=JOSH_REGIONS, frame_data=JOSH_FRAMES,
         carry=[('Josh/josh_throw.png', 80), ('Josh/josh_cards.png', 80)]))


# ============================================================================= CARTER
# The finale's idle is carter_idle f0-3: bald, the orange beard, the serious glowing eyes, the dark
# gi, rope belt, prayer beads, hand wraps, a cross earring and his crimson aura spikes. His eyes
# already glow: the table turns that glow into the family's; the rest is sockets-free.
CARTER_TABLE = 'line K 000000\n' + HOUSE_SKIN + '''
# the aura spikes' own dark outline -> the family's pure-black keyline
line  K   19062A
# the orange beard -> blood (red hair keeps its warmth)
hair  R4  FFB45E F09040
hair  R3  D66C28
hair  R2  B05B21
hair  R1  703414
# his glowing eyes -> the family's glow; the shadow over them -> socket dark
eye   G1  FFD2D8 FF5A62
eye   G2  E0203C
eye   R1  90102A
eye   D2  4A2210
# the dark gi -> pitch
pitch A2  2D4392
pitch D2  1D2B60 14204A 1B1C4C 23184E
pitch P1  0C1430 150F33 111131 060A1E
# the aura spikes and their motes -> blood
fx    R2  780C28
fx    R1  2E0C4C
fx    R3  C01830 7C2EB0
# rope belt, prayer beads, hand wraps -> bone (bone beads)
trim  A5  C8A46A C08A58 D0AE74
trim  B1  F0D8A4 FFF2D6
trim  A4  A07C46 84542E A07E4C
trim  A3  74562E 58341C 6E5230
trim  A2  50381C 3A2010 42301A
trim  D2  32210F
# the cross earring -> iron and bone
metal B1  E6ECF2
metal A4  BED6FF
metal I3  9BADB7
# on his other sheets: the gi's purple folds, the aura, his red flare and glow effects
pitch D2  292767 34236D
fx    R1  4E1878 54061A
fx    G2  FF4A3C
fx    G1  FF9A6A FFE2C0
fx    R3  B45AE0
fx    R4  E2A2F4
metal I3  6B7C8C
bone  B1  FFFFFF
'''
CARTER_PARTS = {
    'head': {'box': (32, 24, 62, 52), 'radius': 12, 'min': 0.55},
    'face': {'box': (34, 34, 62, 52), 'radius': 12, 'min': 0.6},
    'crown': {'box': (38, 24, 58, 34), 'radius': 12, 'min': 0.7},
    'torso': {'box': (32, 50, 64, 70), 'radius': 10, 'min': 0.5},
    'wrap_l': {'box': (13, 64, 26, 82), 'radius': 10, 'min': 0.65},
    'wrap_r': {'box': (70, 64, 83, 82), 'radius': 10, 'min': 0.65},
    'knee_l': {'box': (30, 72, 46, 86), 'radius': 8, 'min': 0.65},
    'knee_r': {'box': (50, 72, 66, 86), 'radius': 8, 'min': 0.65},
}
CARTER_OVERLAYS = [
    # sunken under his burning eyes
    ov('sockets', 'face', C.merge(C.stamp(39, 42, '|------|'), C.stamp(51, 42, '|------|')), on=SKIN),
    # the skull stitched shut across his bald crown
    ov('scalp', 'crown', C.merge(
        C.stamp(41, 31, '|2222|'), C.stamp(45, 30, '|2222222|'), C.stamp(52, 31, '|22222|'),
        *[C.stamp(x, 29 if 45 <= x <= 51 else 30, '|S|\n|S|\n|S|') for x in (42, 45, 48, 51, 54)]), on=SKIN),
    # the jaw hinge down through the beard
    ov('jaw', 'face', C.merge(C.stamp(45, 47, '|K|\n|K|\n|K|\n|K|'), C.stamp(50, 47, '|K|\n|K|\n|K|\n|K|'))),
]
CARTER_TATTER = [
    # the gi's trouser legs, frayed over his bare feet
    {'part': 'torso', 'mats': ('pitch',), 'centre_x': 48, 'rows': (82, 88), 'inner': True, 'seed': 29,
     'depth': 2, 'keep': 3, 'spacing': (2, 5), 'depths': (1, 2)},
]
CARTER_HOOKS = {
    'head': ring_hook('crown', 48, 27),
    'back': back_hook('torso', 48, 58),
    'wrist_l': ring_hook('wrap_l', 20, 72),
    'wrist_r': ring_hook('wrap_r', 75, 72),
    'knee_l': ring_hook('knee_l', 39, 79),
    'knee_r': ring_hook('knee_r', 57, 79),
}
# Ship 2 (09-28). His back views: the Beam Rush's pass (rush_pass f0-2, three-quarter from behind) and
# the entrance's materialising (intro f1-9, his back and the 天 on it; f10 the turning silhouette): the
# back ring is drawn between the shoulder blades - on rush_pass right of the mark, on the entrance at
# the prayer beads' line under the collar, clear of the mark. Intro f0 is the aura's lone eye before he
# forms: the point sits on the eye, no ring. The rest are the frames the tracker cannot read.
CARTER_FRAMES = {
    'Carter/carter_rush_pass.png': {'hooks': {0: _back(55, 57, True), 1: _back(53, 59, True), 2: _back(51, 59, True)}},
    'Carter/carter_intro.png': {'hooks': dict(
        [(0, _back(47, 59))] + [(f, _back(48, 51, True)) for f in range(1, 10)] + [(10, _back(45, 50, True))])},
    'Carter/carter_spent.png': {'hooks': {0: _back(48, 71), 3: _back(48, 71)}},
    'Carter/carter_defeat.png': {'hooks': {3: _back(46, 71), 4: _back(47, 74), 5: _back(47, 74)}},
    'Carter/carter_messatsu_fire.png': {'hooks': {1: _back(41, 61)}},
    'Carter/carter_juggle.png': {'hooks': {f: {'back': None} for f in range(12)}},    # 12 frames of 192x144
}
# His Raging Demon clones (Demon/demon_clone, demon_clone_ghost) float free of any string: effect
# sheets recoloured by his table alone, their authored fade kept, their red eyes the family glow as his
# own eyes are (his aura's table has those two reds as flare).
CARTER_CLONE_EYES = '''
eye   G1  FF4A3C
eye   G2  C01830
'''
add(Boss('carter', 'Carter', 'Carter/carter_idle.png', (96, 96), (48, 95), [0, 1, 2, 3], CARTER_TABLE,
         parts=CARTER_PARTS, overlays=CARTER_OVERLAYS, hooks=CARTER_HOOKS, tatter=CARTER_TATTER,
         frame_data=CARTER_FRAMES,
         carry=[('Carter/carter_rush.png', 96), ('Carter/carter_messatsu_charge.png', 96)]))


# ============================================================================= LIAM
# The finale's idle is liam.png f0: curly hair, the ninja headband, the white-glare glasses, the
# black beard and big grin, brown vest, grey tie, blue trousers. The glare white is also his teeth,
# collar and cuffs, so the lenses get their own mapping inside the tracked lens boxes.
LIAM_TABLE = '''
line  K   000000
# skin -> ash
skin  A5  FADCB8
skin  A4  EEC39A
skin  A3  D9A066
skin  A2  B8794A
skin  D2  8A5236
# curly hair and beard -> pitch
hair  A3  56352A
hair  A2  36201A
hair  D2  1B0F0D
hair  P1  120A08
# the headband's plate and the belt buckle -> iron
metal B1  EEF4F7
metal I3  B3C0C9
metal I2  7B8893
metal P1  4B555E
# the headband cloth and the tie -> bone (they were the light grey on his brown: they stay light)
bone  B1  C4D2DA
bone  A5  9BADB7
bone  A4  6E7D86
bone  A3  4A5563
# the brown vest and belt -> blood, deeper
cloth R4  C3885A
cloth R3  A96B43
cloth R2  8F563B
cloth R1  663931
cloth P1  45283C
# teeth, collar, cuffs (and the lens glare, outside the lenses) -> bone
bone  B1  FFFFFF
bone  A5  D6DEE5 CBDBFC
bone  A4  A3B1BC
# the blue trousers -> pitch
pitch A3  6B6BB0
pitch A2  4C4C8C
pitch D2  3A3A70
pitch P1  26264C 181830
# the shoes -> pitch
pitch A2  6A4A3A
pitch D2  45302A
pitch P1  2A1B16
# the glasses-push glint on his talk sheet
fx    G1  FFF6A8
'''
LIAM_LENSES = '''
# inside the lenses: the glare goes dark and its glints burn (the sockets behind the glasses)
eye   D2  FFFFFF
eye   G2  CBDBFC
'''
LIAM_PARTS = {
    'head': {'box': (13, 1, 45, 27), 'radius': 10, 'min': 0.55},
    'face': {'box': (16, 11, 40, 27), 'radius': 10, 'min': 0.6},
    'crown': {'box': (17, 1, 43, 8), 'radius': 10, 'min': 0.7},
    'torso': {'box': (12, 26, 50, 46), 'radius': 10, 'min': 0.5},
    'cuff_l': {'box': (2, 42, 12, 54), 'radius': 10, 'min': 0.65},
    'cuff_r': {'box': (43, 38, 58, 51), 'radius': 10, 'min': 0.65},
    'knee_l': {'box': (12, 46, 28, 57), 'radius': 6, 'min': 0.65},
    'knee_r': {'box': (33, 46, 50, 57), 'radius': 6, 'min': 0.65},
}
LIAM_REGIONS = [
    {'name': 'lenses', 'part': 'face', 'boxes': [(19, 14, 24, 16), (27, 14, 33, 16)], 'table': LIAM_LENSES},
]
LIAM_OVERLAYS = [
    # a burning pupil behind each dark lens
    ov('sockets', 'face', C.merge(C.stamp(21, 15, '|hg|'), C.stamp(29, 15, '|gh|'))),
    # the jaw hinge through the black beard, from the grin's corners
    ov('jaw', 'face', C.merge(C.stamp(20, 23, '|Km|\n|Km|\n|Km|'), C.stamp(32, 23, '|mK|\n|mK|\n|mK|'))),
]
LIAM_TATTER = [
    # the trouser legs, frayed over his shoes
    {'part': 'torso', 'mats': ('pitch',), 'centre_x': 31, 'rows': (53, 58), 'inner': True, 'seed': 31,
     'depth': 2, 'keep': 3, 'spacing': (2, 5), 'depths': (1, 2)},
]
LIAM_HOOKS = {
    'head': ring_hook('crown', 30, 4, RING_S),
    'back': back_hook('torso', 31, 36),
    'wrist_l': ring_hook('cuff_l', 7, 45, RING_S),
    'wrist_r': ring_hook('cuff_r', 54, 42, RING_S),
    'knee_l': ring_hook('knee_l', 18, 52, RING_S),
    'knee_r': ring_hook('knee_r', 40, 52, RING_S),
}
add(Boss('liam', 'Liam', 'Liam/liam.png', (64, 64), (32, 63), [0], LIAM_TABLE,
         parts=LIAM_PARTS, overlays=LIAM_OVERLAYS, hooks=LIAM_HOOKS, tatter=LIAM_TATTER, regions=LIAM_REGIONS,
         carry=[('Liam/liam_glasses_push.png', 64)]))


# ============================================================================= DANNY, THE SUMO
# Not in the finale's cameo line-up (that is the small Danny above), but it is the Danny whose fight
# sheets the puppet attack uses (the butt slams: danny_sumo_idle / _jump / _air / _slam), so it gets
# its own key frame, parts and hooks. It shares the sumo table the small Danny uses for Danny/Sumo/.
SUMO_PARTS = {
    # his jump sheet is 16 texels taller than the idle (bottom-aligned), so the parts search further
    'head': {'box': (58, 2, 118, 50), 'radius': 24, 'min': 0.55},
    'face': {'box': (62, 27, 114, 50), 'radius': 24, 'min': 0.6},
    'crown': {'box': (66, 2, 110, 16), 'radius': 24, 'min': 0.7},
    'torso': {'box': (48, 50, 128, 100), 'radius': 24, 'min': 0.5},
    'band_l': {'box': (16, 80, 32, 98), 'radius': 24, 'min': 0.65},
    'band_r': {'box': (128, 80, 144, 98), 'radius': 24, 'min': 0.65},
    'knee_l': {'box': (8, 104, 44, 126), 'radius': 24, 'min': 0.6},
    'knee_r': {'box': (132, 104, 168, 126), 'radius': 24, 'min': 0.6},
}
SUMO_OVERLAYS = [
    # his shut eyes become glowing slits between the heavy lids
    ov('sockets', 'face', C.merge(C.stamp(68, 32, '|dhggghd|'), C.stamp(99, 32, '|dhggghd|'),
                                  C.stamp(68, 34, '|-------|'), C.stamp(99, 34, '|-------|')), on=SKIN + ('line',)),
    ov('jaw', 'face', C.merge(C.stamp(82, 42, '\n'.join(['|K|'] * 5)), C.stamp(92, 42, '\n'.join(['|K|'] * 5)))),
    # the great belly stitched across
    ov('belly', 'torso', C.merge(
        C.stamp(64, 76, '|' + '2' * 48 + '|'),
        *[C.stamp(x, 75, '|S|\n|S|\n|S|') for x in range(66, 112, 4)]), on=SKIN),
]
SUMO_HOOKS = {
    'head': ring_hook('crown', 88, 7),
    'back': back_hook('torso', 88, 60),
    'wrist_l': ring_hook('band_l', 24, 89),
    'wrist_r': ring_hook('band_r', 136, 89),
    'knee_l': ring_hook('knee_l', 26, 114),
    'knee_r': ring_hook('knee_r', 150, 114),
}
# The slam's impact frame squashes him 34 texels flatter: the idle's face no longer fits, so its eyes'
# glowing squint, the crown ring and the back point are set by hand (the beanie top is at row 41 there;
# the back sits 3/4 of the idle's 58-texel drop below it, as the squash scales him).
SUMO_FRAMES = {
    'Danny/Sumo/danny_sumo_slam.png': {
        'overlays': {1: [ov('sockets', None, C.merge(C.stamp(72, 70, '|hgggh|'), C.stamp(99, 70, '|hgggh|')))]},
        'hooks': {1: {'head': ((88, 46), RING), 'back': ((88, 84), None)}},
    },
}
add(Boss('danny_sumo', 'Danny (sumo)', 'Danny/Sumo/danny_sumo_idle.png', (176, 144), (88, 143), [0, 1, 2, 3],
         DANNY_SUMO_TABLE, parts=SUMO_PARTS, overlays=SUMO_OVERLAYS, hooks=SUMO_HOOKS, frame_data=SUMO_FRAMES,
         carry=[('Danny/Sumo/danny_sumo_jump.png', 176), ('Danny/Sumo/danny_sumo_air.png', 176),
                ('Danny/Sumo/danny_sumo_slam.png', 176)]))
