"""The ladder heads of 2026-09-23 (Assets/UI/Screens/rank_icons.png): Matt's (frame 3), Computah's
(frame 2) and Captain Burak's (frame 0). This module derives and checks them; ladder.py writes them
into art_source/victory_screen/icons.py, which is what builds the strip.

CAPTAIN BURAK (frame 0, boss 1, @member) is his approved boss design, burak_boss.png frame 0 - the
slot showed the hooded cutscene Burak. His tricorn is 52 px wide and widest at its top, where the
disc is narrowest, so even halved its upturned tips sit under the ring; what reads is its crown and
the gold-trimmed brim sweeping down to the front point, over the curtain bangs parted on his
forehead, the eyes, the smirk rising to his right, and the red bandana tails at the ring's edge.
The hand pass redrew the brim's trim along the sprite's own trim path as one continuous line -
halving broke it into keyline and dark BRASS - lit gold on the left arm and the sprite's shadowed
gold on the right, with the point's pale glint; gave each eye its white and pupil; lifted the
smirk's right corner a row, as the sprite's is; softened the nose to one shadow.

WHY HALF SCALE, not the 1:1 crop the other nine slots use. The slot's window is a disc of radius
13.6 (victory_screen/slots.py WIN): 27 pixels across.
  - MATT: his five-spike crest is 54 px wide on the 96 px sprite (x21..75), the outer pair
    near-horizontal at x21 and x75. At 1:1 the window holds his face and nothing of the tips - and
    the yellow-tipped crest (his Exploud tubes) is what makes the slot read as Matt. Halved, crest
    tip to chin is 28 x 27 and all five tips land inside the ring.
  - COMPUTAH: at 1:1 the window holds only his visor (30 px of it); the dome's curve, both ear
    pods and the antenna - his robot silhouette - fall outside, and the slot reads as a dark screen
    with two red squares. Halved, the whole head fits: dome, visor, red eyes, grille, pods, chin,
    and the antenna stalk running off toward the ring. It also puts slots 2 and 3 at one scale.

HOW. Each head is its sprite taken 2:1 - every grid pixel stands for one 2x2 block of the approved
frame (Matt: matt.png frame 0 from x20 y0; Computah: computah_idle.png frame 0 from x16 y5) - by a
keyline-aware majority (raw_half), then hand-cleaned where halving broke a keyline or merged a
feature. provenance() prints, for each head, how many grid pixels carry a colour found in their
own 2x2 block of the sprite, and how many equal raw_half's pick, so the cleaning is measured, not
asserted. The grid is written in the sprite's own colours (a key per sprite hex, below); icons.py
colours it through REMAP[<name>] into DB32, exactly as crop_icon colours a crop.

WHAT THE HAND PASS DID
  Matt: the three upper tips re-shaped as tapered 3-wide points, each keylined and lit on its
    upper left (a -> WHITE, b/c -> YEL) with its shade side (d); the outer pair as wedges whose top
    edges run straight into the hair's outline, the tips' last keyline pixel sitting under the
    ring's black; the V gaps between the inner tips kept open; the hair's silhouette closed where
    halving opened it; the brows as short dark bars, the right one level with its
    lid (it is raised a pixel on the sprite, which halves away); each eye white / iris / pale
    under its lid; one nose shadow; the lopsided grin as its top line (rising at the right corner),
    a row of teeth and its bottom line; the ears as their own keylined shapes; the chin line and
    the yellow collar below it.
  Computah: raw_half kept him almost whole. The grille's white dots, which halving averaged away,
    are put back on every other pixel (the sprite has 8 across 24 px; the half has 6 across 11);
    one stray grille-end pixel is removed so the visor is symmetric.

DB32. Every colour of each approved frame is mapped by hand (REMAP_MATT, REMAP_COMPUTAH, which
ladder.py writes into icons.py as REMAP['matt'] and REMAP['computah']). Where nearest() would have
gone wrong, and so was not used:
  Matt: his tip gold e2b13c -> YEL, not nearest's TAN (the tips must read yellow; TAN is his skin
    shadow); the deepest hair 15121f -> K, not NAVY (which would merge it with the base); the hair
    sheen 3c3654 -> INDIGO, not nearest's greenish SLATE; the lavender sheen 5c5480 -> INDIGO, not
    PURPLE's red-violet.
  Computah: the lit dome a063dc -> PURPLE, not nearest's BLURPLE, which would turn his dome blue;
    the dome shade 592687 -> PLUM, not INDIGO; the visor's rim darks 3c4757/3f4a5c -> NAVY, not
    INDIGO; his keyline #0C111A (measured: 21.6% of frame 0, and the sheet has no pure black) ->
    K, the ladder's own keyline, as every other slot's.

    python icons_0923.py        # print both grids' provenance and write their previews
"""
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import k923 as K                                                 # noqa: E402
from PIL import Image                                            # noqa: E402

CHAR = os.path.join(K.ASSETS, 'Characters')

# ---------------------------------------------------------------------------------------- Matt
MATT_SRC = os.path.join(CHAR, 'Matt', 'matt.png')
MATT_FRAME = (0, 0, 96, 96)
MATT_BLOCK = (20, 0)                   # grid (0, 0) is the sprite's 2x2 block at x20..21, y0..1
MATT_AT = (6, 6)                       # grid (0, 0) lands on cell (6, 6): crest centred on x20
MATT_DISC = ('SKY', 'BLURPLE')
# His palette keys, as art_source/matt/pal.py names them (checked against that file on every run).
MATT_PAL = {'k': '000000', '1': 'fbd6b0', '2': 'f0b98e', '3': 'db976c', '4': 'b86c4e', '5': '84412f',
            '6': '552619', 'a': 'fff6be', 'b': 'f8db66', 'c': 'e2b13c', 'd': 'ac7c26', 'e': '6a4618',
            'h': '15121f', 'i': '272337', 'j': '3c3654', 'l': '5c5480', 'W': 'ffffff', 'X': 'd5d9ec',
            'A': 'dcdeff', 'B': 'b3b6f2', 'C': '8e91da', 'D': '6d6fbc', 'E': '4f4d96', 'F': '332f68',
            'K': '1a1a25', 'L': '2a2a38', 'M': '3f3f52', 'N': '5a5a70', 'x': '9da1c0',
            'm': '2c0a1c', 'n': '5c1634', 'q': 'c8526e', 'r': 'ee8ca2'}
MATT_HEAD = [
    "..............k.............",   # 0  the centre tip's point
    ".............kbk............",   # 1
    "............kack............",   # 2
    ".......kk...kacdk..kkk......",   # 3  the inner pair's tops
    "......kbcck.kacdk.kacdk.....",   # 4  three tips, lit upper left
    "......kbcck.kbihkkabdk......",   # 5
    ".......kbciiljihklacdk......",   # 6
    ".......kbiiijjihljihk.......",   # 7
    "..kkkkkkkiiijjihhiihkkkkkkk.",   # 8  the outer pair's top edges
    "kbbbbbjjhiijjiihhihhlljaabbk",   # 9  the outer tips (col 0 and 27 sit under the ring)
    "kcccciiiijijjiihhihhjjicccdk",   # 10
    ".kkddiiiijjjjiiihhhhiiihdkk.",   # 11
    "...khiiiijhiiiiiihhiiihhk...",   # 12
    "....kkiiihiihiihhhiihhhk....",   # 13
    ".....kiiiikkkkkkkkkiiik.....",   # 14 hairline
    "......kii1122222223kiik.....",   # 15
    "......kik2hh2222hhh3kik.....",   # 16 brows
    "......kikkkk22222kkkkik.....",   # 17 lids
    ".....k3k1WhX22222WhXk4k.....",   # 18 eyes, ears
    ".....k4k123221222232k5k.....",   # 19
    ".....k4k122222122223k5k.....",   # 20
    "......kk122223432223kk......",   # 21 nose
    "........k22kkkkkkkk3k.......",   # 22 the grin's top line, its right corner up
    "........k22kWWWWWk33k.......",   # 23 teeth
    "........k122kkkkk33k........",   # 24 its bottom line
    ".......kbk2222334kkdk.......",   # 25 chin, collar
    "........kbkkkkkkkcddk.......",   # 26
    "........kbbcccccccddk.......",   # 27
]
REMAP_MATT = {
    # skin: the house ramp, exactly as icons.SKIN_MAP maps it
    'fbd6b0': 'SKIN', 'f0b98e': 'SKIN', 'db976c': 'TAN', 'b86c4e': 'RUST', '84412f': 'BROWN',
    '552619': 'BROWN',
    # the dyed tips, collar and port rims
    'fff6be': 'WHITE', 'f8db66': 'YEL', 'e2b13c': 'YEL', 'ac7c26': 'TAN', '6a4618': 'BRASS',
    # blue-black hair
    '15121f': 'K', '272337': 'NAVY', '3c3654': 'INDIGO', '5c5480': 'INDIGO',
    # whites
    'd5d9ec': 'PALE', '9da1c0': 'GREY',
    # the lavender crewneck and trainers
    'dcdeff': 'WHITE', 'b3b6f2': 'PALE', '8e91da': 'BLURPLE', '6d6fbc': 'BLURPLE', '4f4d96': 'INDIGO',
    '332f68': 'INDIGO',
    # charcoal trousers and speaker cones
    '1a1a25': 'NAVY', '2a2a38': 'NAVY', '3f3f52': 'DASH', '5a5a70': 'ASH',
    # the grin's mouth
    '2c0a1c': 'PLUM', '5c1634': 'PLUM', 'c8526e': 'PINK', 'ee8ca2': 'PINK',
}

# ---------------------------------------------------------------------------------------- Computah
COMPUTAH_SRC = os.path.join(CHAR, 'Computah', 'computah_idle.png')
COMPUTAH_FRAME = (0, 0, 96, 96)          # frame 0 of the idle his fight scene plays
COMPUTAH_BLOCK = (16, 5)
COMPUTAH_AT = (5, 6)
COMPUTAH_DISC = ('LIME', 'GREEN')
COMPUTAH_KEYLINE = (12, 17, 26)         # #0C111A
# Keys for his 27 frame-0 colours (his rig names none); lower case for keyline and darks.
COMPUTAH_PAL = {'k': '0c111a', 'K': '0d1118', 'Q': '131821', 'n': '1a212c', 'v': '222a38',
                'w': '2a3341', 'x': '2b3444', 'y': '3c4757', 'z': '3f4a5c', '5': '5e6c82',
                '6': '6c7a8e', '8': '8091a8', 'g': 'a6b8cc', 'p': 'cedcea', 'q': 'd8e4f2',
                'W': 'f2f8ff', 'D': '391555', 'C': '592687', 'B': '7c3bb4', 'A': 'a063dc',
                'H': 'c892f2', 'r': '93302c', 'R': 'ff4436', 't': '2a7a3c', 'G': '1f9a38',
                'L': '4fe066', 'V': 'a9ffb4'}
COMPUTAH_HEAD = [
    "..k..........................",   # 0  the antenna bulb (under the ring)
    ".kVkk........................",   # 1
    "kVVLk........................",   # 2
    "kVVLLk.......................",   # 3
    "kLLLppkk.....................",   # 4  the stalk
    ".kkkgpppk....................",   # 5
    "....kpppWk...kkkkkkk.........",   # 6  the dome
    ".....kp8pWkkkHHAAAAAkk.......",   # 7
    "......kgpkkHAAAAAAABBBk......",   # 8
    ".......kkBAAAAAAAAABBBBk.....",   # 9
    "......kABkkkkkkkkkkkkkCCk....",   # 10 the visor
    ".....kABk6666666666666kDDk...",   # 11
    ".....kBBkvrRRvvvvvrRRvkDDk...",   # 12 red eyes
    "....kkkBkvrRRvvvvvrRRvkDkkk..",   # 13 ear pods
    "...kADDCkvrrrvvvvvrrrvkBBBBk.",   # 14
    "..kADWWDkvvvvvvvvvvvvvkDWWDCk",   # 15
    "..kAgggpkvqKqKqKqKqKqvkDgggDk",   # 16 the grille, its dots put back
    "..kDgw8gkvvvvvvvvvvvvvkDgw5Dk",   # 17
    "..kCDpgDkkkkkkkkkkkkkkkDpgDDk",   # 18
    "...kDDDDkpgpppppppg855kCDDDk.",   # 19 the chin plate
    "....kkkk.kgggggggg855k.kkkk..",   # 20
    "..........k888888855k........",   # 21
    "...........kkkkkkkkk...kkk...",   # 22
    "..kkkkkk....kWWppp8k.kkAABkk.",   # 23 neck, shoulders
    ".kABBBCCkkkkkkkkkkkkkABBBBCk.",   # 24
    "kABBBBCCkAAAABBBBBBAkBBBBBCk.",   # 25
    "kABBBCCDkCCCCCCCCCCCkBBBBBBBk",   # 26
    "kBBBCCDDkDkkkkkkkkkkkkBBBBBBD",   # 27
]
REMAP_COMPUTAH = {
    # keyline #0C111A and the near-blacks
    '0c111a': 'K', '0d1118': 'K', '131821': 'K',
    # the visor and the dark steels
    '1a212c': 'NAVY', '222a38': 'NAVY', '2a3341': 'NAVY', '2b3444': 'NAVY', '3c4757': 'NAVY',
    '3f4a5c': 'NAVY',
    # steel, dark to light
    '5e6c82': 'ASH', '6c7a8e': 'ASH', '8091a8': 'DGREY', 'a6b8cc': 'GREY', 'cedcea': 'PALE',
    'd8e4f2': 'WHITE', 'f2f8ff': 'WHITE',
    # purple armour
    'c892f2': 'ROSE', 'a063dc': 'PURPLE', '7c3bb4': 'PURPLE', '592687': 'PLUM', '391555': 'PLUM',
    # red eyes: hot core lighter, as Carter's glare
    '93302c': 'RED', 'ff4436': 'PINK',
    # the antenna bulb and the battery cells
    'a9ffb4': 'LIME', '4fe066': 'GREEN', '1f9a38': 'GREEN', '2a7a3c': 'TEAL',
}

# ---------------------------------------------------------------------------------------- Captain Burak
# Frame 0 of the ladder (boss 1, @member): his approved boss design, burak_boss.png frame 0 (the
# idle), replacing the hooded cutscene Burak the slot showed.
BURAK_SRC = os.path.join(CHAR, 'BurakBoss', 'burak_boss.png')
BURAK_FRAME = (0, 0, 96, 96)
BURAK_BLOCK = (22, 1)
BURAK_AT = (7, 8)
BURAK_DISC = ('CYAN', 'STEEL')          # the slot's own disc, kept
BURAK_PAL = {'k': '000000',
             # skin, light -> dark (the approved VS pose's ramp), stubble, lip
             '1': 'e2a874', '2': 'd79864', '3': 'be8254', '4': 'ac714f', '5': 'a88068', '6': 'c8705e',
             # dark brown hair, dark -> light
             'h': '0d0909', 'i': '1a1212', 'j': '281810', 'J': '2a1d19', 'l': '36251e', 'm': '503729',
             'n': '5c3b28', 'o': '7c5438',
             # the tricorn, dark -> lit; the cutlass's dark steels
             'T': '15151d', 'U': '23232f', 'V': '353547', 'W': '4e4f66', 'X': '444a5c', 'Y': '6d7589',
             # gold trim (Josh's exact ramp), light -> dark
             'a': 'fff3b0', 'b': 'f5d94e', 'c': 'e0ab35', 'd': 'b07d22', 'e': '7a5216',
             # the crimson coat, light -> dark
             'A': 'd8434f', 'B': 'b02436', 'C': '7e162b', 'D': '4a0c1b',
             # the red bandana, light -> dark
             'E': 'd95763', 'F': 'ac3232', 'G': '6e1f22',
             # whites: shirt and cutlass
             'w': 'fffcf4', 'x': 'e8e1d3', 'y': 'dce3ee', 'z': 'c3b9a9', 'q': 'a6afc1'}
BURAK_HEAD = [
    "kk......kkkkkkkkkkk......k......",   # 0  the tricorn: its tips (under the ring), the crown's top
    ".kk...kWWWWWWWWVVVUk....ck......",   # 1
    ".kbkkkWWWWWWWWVVVUUUTkkck.......",   # 2
    "..kbbkkkWWWWVVVVUUUkkccck.......",   # 3  the gold brim: lit left arm, shadowed right
    "...TVbbbkkkVVVUUkkcccUUk....kk..",   # 4
    "....kkTVbbbkkUkcccUUkkkkkkkkEGk.",   # 5
    "...kkhmkkTUbaccTTkkkiikEEEEGGk..",   # 6  the brim's front point, its glint
    "....kmhmJkkkUcTkkJJiihkFFFkk....",   # 7
    "....kmlJihmJkkhJJJJJhikkkkkk....",   # 8
    "...khhJihlJihiihiJJhJhkGGGFEkk..",   # 9  bandana tails
    "...khmihlihhkJJhhhiJhikkkkkkkk..",   # 10
    "...khihmihhk2kJiiihhhik.........",   # 11 curtain bangs parted over the forehead
    "...khhhlhik222Jikkiihikk........",   # 12
    "...khhhhkk2222khk3kiihik........",   # 13
    "...Jhkikkkkk22kikkkiikik........",   # 14
    "...kkkk1kkk2222ikk4kkkkk........",   # 15 lids
    "....k4k1wkw22223kw44knk.........",   # 16 eyes
    "....k3k1222222223334k4..........",   # 17
    ".....kk1222223223334k...........",   # 18
    "......k1222234323k34k...........",   # 19 nose; the smirk's right corner up
    "X.....k122kkkkkkk434k...........",   # 20 the smirk
    "YXk...k112266322334k............",   # 21 lower lip
    "wqXk...k12235323344.............",   # 22
    ".kyYXkkkkk3333444kkkkk..........",   # 23 chin
    "..kkqkkBkkkkkkkkkkCCBBC.........",   # 24 collar
    "..kAkkkkBk2yxxzykCCkBBCD........",   # 25
]
REMAP_BURAK_BOSS = {
    # skin: base on TAN (d79864 is TAN to within 8), lit SKIN, shadow RUST - not nearest()'s olive BRASS
    'e2a874': 'SKIN', 'd79864': 'TAN', 'be8254': 'TAN', 'ac714f': 'RUST', 'a88068': 'RUST', 'c8705e': 'RUST',
    # hair: K, PLUM, BROWN, RUST like Jordan's dark brown - not nearest()'s NAVY for the mids
    '0d0909': 'K', '1a1212': 'K', '281810': 'PLUM', '2a1d19': 'PLUM', '36251e': 'PLUM', '503729': 'BROWN',
    '5c3b28': 'BROWN', '7c5438': 'RUST',
    # the tricorn NAVY, lit INDIGO - not nearest()'s greenish SLATE and warm DASH; the cutlass steels
    '15151d': 'NAVY', '23232f': 'NAVY', '353547': 'NAVY', '4e4f66': 'INDIGO', '444a5c': 'DASH', '6d7589': 'DGREY',
    # gold trim: Josh's ramp, mapped as Josh's is
    'fff3b0': 'WHITE', 'f5d94e': 'YEL', 'e0ab35': 'TAN', 'b07d22': 'BRASS', '7a5216': 'MUD',
    # crimson coat, as Josh's crimson
    'd8434f': 'PINK', 'b02436': 'RED', '7e162b': 'RED', '4a0c1b': 'PLUM',
    # the bandana: PINK and RED, its shade RED too so the tails stay red
    'd95763': 'PINK', 'ac3232': 'RED', '6e1f22': 'RED',
    # whites
    'fffcf4': 'WHITE', 'e8e1d3': 'WHITE', 'dce3ee': 'PALE', 'c3b9a9': 'GREY', 'a6afc1': 'GREY',
}

HEADS = {
    'matt': dict(src=MATT_SRC, frame=MATT_FRAME, block=MATT_BLOCK, at=MATT_AT, disc=MATT_DISC,
                 pal=MATT_PAL, head=MATT_HEAD, remap=REMAP_MATT, keyline=(0, 0, 0)),
    'computah': dict(src=COMPUTAH_SRC, frame=COMPUTAH_FRAME, block=COMPUTAH_BLOCK, at=COMPUTAH_AT,
                     disc=COMPUTAH_DISC, pal=COMPUTAH_PAL, head=COMPUTAH_HEAD, remap=REMAP_COMPUTAH,
                     keyline=COMPUTAH_KEYLINE),
    'burak_boss': dict(src=BURAK_SRC, frame=BURAK_FRAME, block=BURAK_BLOCK, at=BURAK_AT, disc=BURAK_DISC,
                       pal=BURAK_PAL, head=BURAK_HEAD, remap=REMAP_BURAK_BOSS, keyline=(0, 0, 0)),
}


# ---------------------------------------------------------------------------------------- checks
def check_matt_pal():
    """MATT_PAL's keys must mean what art_source/matt/pal.py says they mean."""
    txt = open(os.path.join(K.ART, 'matt', 'pal.py'), encoding='utf-8').read()
    theirs = {k: v.lower() for k, v in re.findall(r"'(\w)': hx\('([0-9A-Fa-f]{6})'\)", txt)}
    bad = {k: (v, theirs.get(k)) for k, v in MATT_PAL.items() if theirs.get(k) != v}
    assert not bad, 'MATT_PAL disagrees with art_source/matt/pal.py: %s' % bad


def sprite_keys(name):
    h = HEADS[name]
    inv = {v: k for k, v in h['pal'].items()}
    im = Image.open(h['src']).convert('RGBA').crop(h['frame'])
    px = im.load()
    g, missing = {}, set()
    for y in range(im.height):
        for x in range(im.width):
            c = px[x, y]
            if c[3]:
                hx = '%02x%02x%02x' % c[:3]
                if hx in inv:
                    g[(x, y)] = inv[hx]
                else:
                    missing.add(hx)
    assert not missing, '%s: sprite colours with no key: %s' % (name, sorted(missing))
    return g, im


def raw_half(name, w, hgt):
    """The 2:1 keyline-aware majority the hand pass started from: a block with a keyline pixel on
    the silhouette keeps the keyline, otherwise its commonest colour (a keyline wins a tie)."""
    g, _ = sprite_keys(name)
    bx, by = HEADS[name]['block']
    dark = {'k', 'K', 'Q'} if name == 'computah' else {'k'}
    out = {}
    for j in range(hgt):
        for i in range(w):
            blk = [g.get((bx + 2 * i + a, by + 2 * j + b), '.') for b in (0, 1) for a in (0, 1)]
            ne = blk.count('.')
            if ne >= 3:
                continue
            if any(c in dark for c in blk) and ne >= 1:
                out[(i, j)] = 'k'
                continue
            cnt = Counter(c for c in blk if c != '.').most_common()
            if len(cnt) > 1 and cnt[0][1] == cnt[1][1] and 'k' in (cnt[0][0], cnt[1][0]):
                out[(i, j)] = 'k'
                continue
            out[(i, j)] = cnt[0][0]
    return out


def provenance(name):
    """How much of the grid is the sprite's own: pixels whose colour occurs in their own 2x2 block,
    and pixels equal to raw_half's pick."""
    h = HEADS[name]
    rows = h['head']
    assert len({len(r) for r in rows}) == 1, '%s: ragged grid' % name
    assert set(''.join(rows)) - {'.'} <= set(h['pal']), '%s: unknown keys' % name
    g, _ = sprite_keys(name)
    bx, by = h['block']
    raw = raw_half(name, len(rows[0]), len(rows))
    n = own = same = 0
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch == '.':
                continue
            n += 1
            blk = {g.get((bx + 2 * i + a, by + 2 * j + b)) for b in (0, 1) for a in (0, 1)}
            own += ch in blk
            same += raw.get((i, j)) == ch
    return n, own, same


def remapped(name):
    """The grid in DB32 (hex), as icons.py's grid_cell colours it: '.' stays None."""
    import_cv()
    h = HEADS[name]
    out = []
    for r in h['head']:
        row = []
        for ch in r:
            if ch == '.':
                row.append(None)
                continue
            hx = h['pal'][ch]
            row.append(getattr(CV, h['remap'][hx]) if hx in h['remap'] else hx)
        out.append(row)
    return out


CV = None


def import_cv():
    """victory_screen's cv with its writer stubbed (it is never allowed to write from here)."""
    global CV
    if CV is None:
        vsd = os.path.join(K.ART, 'victory_screen')
        if vsd not in sys.path:
            sys.path.insert(0, vsd)
        import pngio
        import cv

        def _refuse(*a, **k):
            raise RuntimeError('icons_0923 never lets the victory-screen pipeline write')
        pngio.write_png = _refuse
        cv.write_png = _refuse
        CV = cv
    return CV


def check_remap(name):
    """Every colour of the approved frame has a hand-picked DB32 entry (or is DB32 already)."""
    cv = import_cv()
    h = HEADS[name]
    _, im = sprite_keys(name)
    cols = {'%02x%02x%02x' % c[:3] for c in K.flat(im) if c[3]}
    missing = sorted(c for c in cols if c not in h['remap'] and c not in cv.DB)
    assert not missing, '%s: frame colours with no REMAP entry: %s' % (name, missing)
    for hx, nm in h['remap'].items():
        assert getattr(cv, nm) in cv.DB, (name, hx, nm)
    return len(cols)


def keyline_stats(name):
    h = HEADS[name]
    im = Image.open(h['src']).convert('RGBA')
    f0 = im.crop(h['frame'])
    return K.stats(f0, key=h['keyline']), K.stats(im, key=h['keyline']), K.stats(f0)


def main():
    check_matt_pal()
    for name in HEADS:
        n, own, same = provenance(name)
        cols = check_remap(name)
        f0, sheet, black = keyline_stats(name)
        kl = '#%02X%02X%02X' % HEADS[name]['keyline']
        print('%-9s grid %dx%d: %d pixels; %d (%.1f%%) a colour from their own 2x2 block of the sprite; '
              '%d (%.1f%%) equal to the raw 2:1 majority' % (
                  name, len(HEADS[name]['head'][0]), len(HEADS[name]['head']), n, own, 100.0 * own / n,
                  same, 100.0 * same / n))
        print('          frame colours %d, all mapped by hand; keyline %s = %.1f%% of frame 0 (%.1f%% of the sheet),'
              ' pure black %.1f%%' % (cols, kl, 100 * f0['key'], 100 * sheet['key'], 100 * black['key']))


if __name__ == '__main__':
    main()
