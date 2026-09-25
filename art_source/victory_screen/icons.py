"""Boss face icons for the rank ladder (40x40 cells; art visible inside the slot window).
Built from the approved sprites' heads (1:1 pixels, remapped to DB32 by hand-checked tables),
duo slots as diagonal tag-team splits, plus an original INVITE envelope icon.
Frame order (approved boss order):
0 Burak, 1 Eric, 2 Computah, 3 Matt, 4 Mason,
5 Josh, 6 Danny, 7 Carter, 8 Liam & Bixby, 9 Jordan (final boss), 10 Invite.
python icons.py outdir"""
import sys, math
from cv import *
import slots

ASSETS = "C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/"
CHAR = ASSETS + "Characters/"
S = 40
ORDER = ['burak', 'eric', 'computah', 'matt', 'mason', 'josh', 'danny', 'carter', 'liam_bixby',
         'jordan', 'invite']


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def nearest(h):
    r, g, b = rgb(h)
    best, bd = None, 1e18
    for c in DB32:
        R, G, B = rgb(c)
        rm = (r + R) / 2
        d = (2 + rm / 256) * (r - R) ** 2 + 4 * (g - G) ** 2 + (2 + (255 - rm) / 256) * (b - B) ** 2
        if d < bd:
            bd, best = d, c
    return best


def in_win(x, y, pad=0.0):
    return math.hypot(x + 0.5 - 20, y + 0.5 - 20) <= slots.WIN + pad


PAD = 1.2   # draw 1px under the inner black line so the frame always covers the edge

# shared skin remaps (sprite custom ramps -> DB32)
SKIN_MAP = {'f0b98e': SKIN, 'fbd6b0': SKIN, 'db976c': TAN, 'b86c4e': RUST, '84412f': BROWN,
            'f09c86': PINK, 'b58773': TAN, 'd9ab93': SKIN, 'fadcb8': SKIN, 'd6aa7c': TAN}

REMAP = {
    # Burak is cut from his cutscene sheet, the only art of him with his face to camera.
    'burak': dict(SKIN_MAP, **{'120c10': K, '17111a': K, '181920': NAVY, '24212a': NAVY,
                               '292b39': NAVY, '2e2430': PLUM, '3b3e50': SLATE, '3e3944': SLATE,
                               '515569': DASH, '6a6470': ASH, '6c7187': ASH, '8e93a8': DGREY,
                               '9a98a6': DGREY, 'aab2c0': GREY, 'c9d2df': PALE, 'eef2f7': WHITE,
                               '112660': INDIGO, '252a42': NAVY, '373e60': INDIGO, '4c5782': INDIGO,
                               '6a76a6': GREY, '1b3f8e': STEEL, '2a62c4': BLURPLE, '4a8ae6': SKY,
                               '8cc0ff': PALE, '5a3524': BROWN, '6a2a2a': BROWN}),
    'eric': dict(SKIN_MAP, **{'ffb45e': TAN, 'f58a38': ORANGE, 'df6c22': ORANGE, 'b04c16': RUST,
                              '7a3010': BROWN, '4a1c08': PLUM, 'f3c9a2': SKIN, 'fde6cc': SKIN,
                              'dca27a': TAN, 'b8795a': RUST, '8a5040': BROWN, 'a3b1c2': GREY,
                              'eaf0f6': WHITE, 'cdd7e2': PALE, '3a2418': PLUM}),
    'mech': dict(SKIN_MAP, **{'d4cc2e': YEL, 'ece45a': YEL, '908a17': BRASS, '5e5a10': MUD,
                              'b8794a': RUST, '3c4450': NAVY, '514c57': DASH, '5a6570': ASH,
                              '6e6873': ASH, '7b8893': DGREY, '8d8791': DGREY, 'c4d2da': PALE,
                              'eef3f6': WHITE, 'b0aab4': GREY, '24212a': NAVY, '37333d': NAVY,
                              'fff7a0': WHITE, 'd6dee5': PALE, '8a5236': RUST, '4a1a1a': PLUM,
                              '604090': PURPLE}),
    # ffd2d8/ff5a62/e0203c only ever colour his eye slits, so they take the hottest ramp on the
    # sheet (white core in a red slit) - at portrait size that glare is what identifies him.
    # The aura that falls outside the window keeps its own ramp for the rest of the sheet's uses:
    # PLUM/PURPLE for the wisps, RED/PINK for the flames.
    'carter': dict(SKIN_MAP, **{'221208': K, '111131': NAVY, '0c1430': NAVY, '150f33': NAVY,
                                '19062a': NAVY, '2e0c4c': PLUM, '23184e': PLUM, '34236d': PURPLE,
                                '4e1878': PURPLE, '7c2eb0': PURPLE, '780c28': PLUM, 'c01830': RED,
                                'e0203c': RED, 'ff5a62': PINK, 'ff4a3c': PINK, 'ffd2d8': WHITE,
                                'd0ae74': TAN, 'c08a58': TAN, 'c8a46a': TAN, 'f0d8a4': SKIN,
                                'fff2d6': WHITE, 'e6ecf2': WHITE, 'd66c28': ORANGE, 'f09040': ORANGE,
                                'b05b21': RUST, 'ffb45e': TAN, '703414': BROWN, '552619': BROWN,
                                '58341c': BROWN, '3a2010': PLUM, '32210f': PLUM, '4a2210': PLUM,
                                '14204a': NAVY, '1b1c4c': NAVY, '1d2b60': INDIGO, '292767': INDIGO,
                                '2d4392': STEEL, '4a6ed8': BLURPLE, 'bed6ff': PALE, 'a07e4c': BRASS,
                                'a07c46': BRASS, '74562e': MUD, '6e5230': MUD, '50381c': BROWN,
                                # The approved 2026-09-23 polish (art_source/carter_polish lib.PAL)
                                # uses four hexes the old sheet did not. The gi's deepest navy joins
                                # its neighbour on NAVY, not nearest()'s black, which would punch it
                                # into the keyline; the wraps' deepest step and the slit's deep
                                # corners go to BROWN (the slit tapers like the sprite's, red to
                                # ember); the mid bead tone sits between the beads' TAN and BROWN.
                                '060a1e': NAVY, '42301a': BROWN, '90102a': BROWN, '84542e': RUST}),
    # His deepened palette: bone duster (WHITE..DASH), wine fedora crown (PLUM/RED, one PINK
    # highlight - the mid wine shares RED so the crown doesn't read pink at portrait size), gold
    # band and spade rim on DB32's own gold ramp, hair on BROWN/RUST and a PLUM iris in a WHITE
    # eye now that the shades are off. The lens blues are still here for the rest of the sheet.
    'josh': dict(SKIN_MAP, **{'0d0d13': K, '130b09': K, '1f1d17': K, '1c1c24': NAVY, '24160f': PLUM,
                              '2b0a12': PLUM, '3d261a': PLUM, '5f3c29': BROWN, 'b58773': TAN,
                              'e0917c': PINK, 'd9ab93': SKIN, 'f4ead6': WHITE, 'fff0dc': WHITE,
                              'e8e2ce': PALE, 'c6bfa4': GREY, '918b72': DGREY, '5e5a48': DASH,
                              '39362b': SLATE, '8a5b3d': RUST, '3a2014': PLUM,
                              '4d1420': PLUM, '7a2032': RED, 'a63b4b': RED,
                              'c96c74': PINK, '7a5216': MUD, 'b07d22': BRASS, 'e0ab35': TAN,
                              'f5d94e': YEL, 'fff3b0': WHITE, '0d1f4a': NAVY, '20203c': NAVY,
                              '32335c': INDIGO, '45487f': INDIGO, '1b3f86': STEEL, 'bde0ff': PALE,
                              '32323e': NAVY, '50505e': DASH, '7e7e90': DGREY, 'e07a2c': ORANGE,
                              # The approved 2026-09-23 redesign (art_source/josh_redesign lib.PAL).
                              # Cream duster, collar rims, card faces, eye whites and the tooth take
                              # the old bone duster's ramp, light to dark, so the collar never merges
                              # into his skin the way nearest() would put it (SKIN).
                              'f6efdc': WHITE, 'e6dbbe': PALE, 'c8b994': GREY, '9e8d68': DGREY,
                              '6b5d44': DASH, '463c2c': SLATE,
                              # Crimson collar, gloves and pips: dark crimson shares RED with the
                              # base, the same call as the wine crown's mid tones above.
                              '4a0c16': PLUM, '861826': RED, 'c2283a': RED, 'e8605a': PINK,
                              # Waistcoat: the darkest step joins NAVY; the lit edge steps up to
                              # BLURPLE rather than nearest()'s PURPLE, which changes its hue.
                              '14142a': NAVY, '5e63a0': BLURPLE}),
    'mason': dict(SKIN_MAP, **{'90765e': RUST, '7d5631': BROWN, 'd4cc2e': TAN, 'ae8358': RUST,
                               'fadcb8': SKIN}),
    'liam': dict(SKIN_MAP, **{'1b0f0d': K, '120a08': K, '36201a': PLUM, '56352a': BROWN,
                              'a96b43': RUST, 'c3885a': TAN, 'b8794a': TAN, '6e7d86': ASH,
                              '7b8893': DGREY, '4a5563': DASH, 'b3c0c9': GREY, 'a3b1bc': GREY,
                              'd6dee5': PALE, 'eef4f7': WHITE, 'c4d2da': PALE}),
    'bixby': dict(SKIN_MAP, **{'c97a3c': ORANGE, 'ede4d6': WHITE, 'f4e9dc': WHITE, 'e8ecf2': WHITE,
                               'c7bbab': SKIN, '948779': DGREY, '6b3419': BROWN, '6a3c22': BROWN,
                               '4a2818': PLUM, '2c1810': PLUM, '3b1e12': PLUM, '9c5428': RUST,
                               '8a5530': RUST, 'e9a55f': TAN, 'ff9a3c': TAN, '6e1e22': BROWN,
                               '5a1a22': PLUM, 'e0524a': PINK, 'a8b0be': GREY, '6e6e78': ASH,
                               '5e6674': ASH}),
    # The approved 2026-09-23 redesign (art_source/jordan_redesign kit.PAL), every colour inside his
    # window by hand. His light olive skin goes the way the other light skins do - the lit and base
    # tones on SKIN, then TAN, RUST, BROWN - not nearest()'s TAN for the base, which would swallow the
    # TAN shadows that make his tired eyes; the dark brown hair on K, PLUM, BROWN, RUST like Josh's, its
    # second-darkest tone on PLUM rather than nearest()'s NAVY and the quiff's greasy sheen on TAN
    # rather than nearest()'s KHAKI green; the lip PINK so it reads in the beard. The box's red header
    # (cleared from the cell by jordan_cell) and the shirt's darks and collar trim below the chin go
    # the way Josh's crimson does, for any re-frame.
    'jordan': dict(SKIN_MAP, **{'7a2626': BROWN, 'b05e97': PURPLE, 'e49acd': ROSE, '8a4574': PURPLE,
                                'ae8358': RUST, '90765e': BROWN, 'f2c0df': PALE,
                                'eccda5': SKIN, 'd5ad85': SKIN, 'b58a63': TAN, '876046': RUST,
                                '573a2b': BROWN, 'a8604f': PINK, '1a110d': K, '2b1c15': PLUM,
                                '432d21': PLUM, '5f412e': BROWN, '7f5b3e': RUST, 'a27b57': TAN,
                                'f3eee4': WHITE, 'c9293f': RED, 'ec5a5b': PINK, '8c1b2d': RED,
                                '4c0d1a': PLUM, '2c2f39': NAVY,
                                # v2, approved 2026-09-24 (art_source/jordan_v2 jv2_base.PAL): his
                                # pallor skin SKIN, SKIN, TAN, then DGREY for the sallow shadows (the
                                # lid, the tired bags, the ear) and DASH for the deepest - not
                                # nearest()'s KHAKI green face; the dull lip RUST; the greasy hair's
                                # pale-yellow shine WHITE as Josh's is, not nearest()'s SKIN.
                                'e7d8b6': SKIN, 'cdb694': SKIN, 'aa9173': TAN, '7d6353': DGREY,
                                '4e3a33': DASH, '9a6558': RUST, 'fff3b0': WHITE}),
    # Matt: the approved 2026-09-23 matt.png frame 0 (art_source/matt/pal.py), every colour of it
    # by hand - see art_source/derived_0923/icons_0923.py. The dyed tips go WHITE, YEL, YEL, TAN,
    # BRASS: a step brighter than Josh's gold, and not nearest()'s TAN for e2b13c, which is his skin
    # shadow - on a half-scale head the yellow tips are what says Matt. The blue-black hair K, NAVY,
    # INDIGO, INDIGO, where nearest() merges its deepest tone into the base and puts its sheen on
    # greenish SLATE; the lavender crewneck PALE, BLURPLE, INDIGO; the charcoal NAVY to ASH.
    'matt': dict(SKIN_MAP, **{'552619': BROWN, 'fff6be': WHITE, 'f8db66': YEL, 'e2b13c': YEL,
                              'ac7c26': TAN, '6a4618': BRASS, '15121f': K, '272337': NAVY,
                              '3c3654': INDIGO, '5c5480': INDIGO, 'd5d9ec': PALE, '9da1c0': GREY,
                              'dcdeff': WHITE, 'b3b6f2': PALE, '8e91da': BLURPLE, '6d6fbc': BLURPLE,
                              '4f4d96': INDIGO, '332f68': INDIGO, '1a1a25': NAVY, '2a2a38': NAVY,
                              '3f3f52': DASH, '5a5a70': ASH, '2c0a1c': PLUM, '5c1634': PLUM,
                              'c8526e': PINK, 'ee8ca2': PINK}),
    # Computah: the redesigned robot of 2026-09-22, computah_idle.png frame 0, every colour of it
    # by hand - see art_source/derived_0923/icons_0923.py. His keyline is #0C111A (the sheet has
    # no pure black), which goes to K, the ladder's keyline. The lit dome a063dc is PURPLE, not
    # nearest()'s BLURPLE, which turns the dome blue; its shade 592687 PLUM, not INDIGO; the
    # visor's dark steels NAVY, not INDIGO or SLATE; the eyes' hot core PINK in a RED rim.
    'computah': dict(SKIN_MAP, **{'0c111a': K, '0d1118': K, '131821': K, '1a212c': NAVY,
                                  '222a38': NAVY, '2a3341': NAVY, '2b3444': NAVY, '3c4757': NAVY,
                                  '3f4a5c': NAVY, '5e6c82': ASH, '6c7a8e': ASH, '8091a8': DGREY,
                                  'a6b8cc': GREY, 'cedcea': PALE, 'd8e4f2': WHITE, 'f2f8ff': WHITE,
                                  'c892f2': ROSE, 'a063dc': PURPLE, '7c3bb4': PURPLE,
                                  '592687': PLUM, '391555': PLUM, '93302c': RED, 'ff4436': PINK,
                                  'a9ffb4': LIME, '4fe066': GREEN, '1f9a38': GREEN, '2a7a3c': TEAL}),
    # Captain Burak: his approved boss design, burak_boss.png frame 0, every colour of it by hand -
    # see art_source/derived_0923/icons_0923.py. The skin's base d79864 sits on TAN, its shadow
    # ac714f on RUST, not nearest()'s olive BRASS; the hair K, PLUM, BROWN, RUST like Jordan's, not
    # nearest()'s NAVY; the tricorn NAVY lit INDIGO, not SLATE and DASH; his gold trim is Josh's
    # ramp exactly and maps as Josh's does; the coat's crimson as Josh's; the bandana PINK and RED.
    'burak_boss': dict(SKIN_MAP, **{'e2a874': SKIN, 'd79864': TAN, 'be8254': TAN, 'ac714f': RUST,
                                    'a88068': RUST, 'c8705e': RUST, '0d0909': K, '1a1212': K,
                                    '281810': PLUM, '2a1d19': PLUM, '36251e': PLUM, '503729': BROWN,
                                    '5c3b28': BROWN, '7c5438': RUST, '15151d': NAVY, '23232f': NAVY,
                                    '353547': NAVY, '4e4f66': INDIGO, '444a5c': DASH,
                                    '6d7589': DGREY, 'fff3b0': WHITE, 'f5d94e': YEL, 'e0ab35': TAN,
                                    'b07d22': BRASS, '7a5216': MUD, 'd8434f': PINK, 'b02436': RED,
                                    '7e162b': RED, '4a0c1b': PLUM, 'd95763': PINK, 'ac3232': RED,
                                    '6e1f22': RED, 'fffcf4': WHITE, 'e8e1d3': WHITE, 'dce3ee': PALE,
                                    'c3b9a9': GREY, 'a6afc1': GREY}),
}


def crop_icon(key, src, cx, cy):
    """Source pixel (cx,cy) -> cell (20,20)."""
    sp = load(src)
    rm = REMAP.get(key, {})
    cv = Canvas(S, S)
    unmapped = set()
    for y in range(S):
        for x in range(S):
            if not in_win(x, y, PAD):
                continue
            c = sp.get(cx + x - 20, cy + y - 20)
            if c is None:
                continue
            if c in rm:
                c = rm[c]
            elif c not in DB:
                unmapped.add(c)
                c = nearest(c)
            cv.set(x, y, c)
    if unmapped:
        print('  note: %s used nearest() for %s' % (key, sorted(unmapped)))
    return cv


def bg_disc(cv, col, shade):
    """empty window pixels -> server-icon background colour with a lower-right shade crescent."""
    for y in range(S):
        for x in range(S):
            if in_win(x, y, PAD) and cv.get(x, y) is None:
                d = math.hypot(x + 0.5 - 17.5, y + 0.5 - 17.5)
                cv.set(x, y, shade if d > 14.0 else col)


def split(a, b, slope, cut=20):
    """diagonal tag-team split with a 1px black divider."""
    cv = Canvas(S, S)
    for y in range(S):
        for x in range(S):
            if not in_win(x, y, PAD):
                continue
            v = x + (y - 20) * slope
            src = a if v < cut else b
            cv.set(x, y, src.get(x, y))
            if cut - 0.5 <= v < cut + 0.5:
                cv.set(x, y, K)
    return cv


ENVELOPE = [
    "kkkkkkkkkkkkkkkkkkkkkk",
    "kPkPPPPPPPPPPPPPPPPkPk",
    "kWPkPPPPPPPPPPPPPPkPWk",
    "kWWPkPPPPPPPPPPPPkPWWk",
    "kWWWPkkPPPPPPPPkkPWWWk",
    "kWWWWWWkkPPPPkkWWWWWWk",
    "kWWWWWWWWkkkkWWWWWWWWk",
    "kWWWWWWUWWWWWWUWWWWWWk",
    "kWWWWWWUUUUUUUUWWWWWWk",
    "kWWWWWUUIUUUUIUUWWWWWk",
    "kWWWWWUUUUUUUUUUWWWWWk",
    "kWWWWWWUUUWWUUUWWWWWWk",
    "kGGGGGGGGGGGGGGGGGGGGk",
    "kkkkkkkkkkkkkkkkkkkkkk",
]


def invite_icon():
    cv = Canvas(S, S)
    bg_disc(cv, BLURPLE, INDIGO)
    # rays behind the envelope
    for y in range(S):
        for x in range(S):
            if in_win(x, y, PAD):
                ang = math.degrees(math.atan2(y + 0.5 - 20, x + 0.5 - 20)) % 45
                if ang < 11 and math.hypot(x + 0.5 - 20, y + 0.5 - 20) > 8 and cv.get(x, y) == BLURPLE:
                    cv.set(x, y, SKY)
    cv.grid(ENVELOPE, {'k': K, 'W': WHITE, 'P': PALE, 'G': GREY, 'U': BLURPLE, 'I': WHITE}, 9, 13)
    for (sx, sy) in [(9, 7), (27, 29)]:
        cv.grid(["..Y..", ".YWY.", "YWWWY", ".YWY.", "..Y.."], {'Y': YEL, 'W': WHITE}, sx, sy)
    for y in range(S):
        for x in range(S):
            if not in_win(x, y, PAD):
                cv.set(x, y, None)
    return cv


QUESTION = [
    "..MMMM..",
    ".MM..MM.",
    "MM....MM",
    "......MM",
    ".....MM.",
    "....MM..",
    "...MM...",
    "...MM...",
    "........",
    "...MM...",
]


def placeholder_icon(col, shade):
    """A boss with no art yet: a blank disc with a question mark, so the slot reads as 'to be
    designed' instead of pretending to be a portrait."""
    cv = Canvas(S, S)
    bg_disc(cv, col, shade)
    cv.grid(QUESTION, {'M': K}, 16, 15)
    return cv


def carter_cell():
    """Carter's slot, cut from the approved 2026-09-23 polish itself (carter_polish.png frame 0 -
    the head is the same in both of its frames) so it does not wait on carter_akuma.png, which the
    polish is replacing: (143,26) on the new carter_akuma.png lands on the top of his dome. Centred
    on the head's own axis (the window's centre is half a pixel up-left of (cx, cy), so 48 puts it
    on 47.5) and high enough that the dome's top line meets the disc's edge - any higher and the
    aura's navy crest reads as hair - with the brows, the glowing slits, the moustache and the
    mouth below it."""
    cv = crop_icon('carter', CHAR + "Carter/carter_polish.png", 48, 37)
    bg_disc(cv, BLURPLE, INDIGO)
    return cv


def jordan_cell():
    """Jordan's slot, cut from the approved v2 redesign (2026-09-24, jordan_redesign_v2.png frame 0,
    the idle; art_source/jordan_derived/ladder_v2.py). (51, 25) is the 09-23 framing moved with his
    head, which v2 slumps 2px forward and 1px down: the window's centre on x50.5, between the back of
    his head and the tip of his nose, its top and bottom on the greasy crest (y10) and his chin (y39) -
    the whole head, the oily clumps flecked with shine and dandruff, the heavy brows, the tired eyes,
    the lip in the patchy beard. The gold collector box beside his face starts at x62, inside the
    disc's right edge, where a sliver of it reads as a stray dark stripe, so the box is cleared and the
    disc shows through: x62 on, from row 26 down (his crest reaches x63 higher up, and stays)."""
    cx, cy = 51, 25
    cv = crop_icon('jordan', CHAR + "Jordan/jordan_redesign_v2.png", cx, cy)
    for y in range(S):
        for x in range(S):
            if cx + x - 20 >= 62 and cy + y - 20 >= 26:
                cv.set(x, y, None)
    bg_disc(cv, GREEN, TEAL)
    return cv


# Matt (frame 3) and Computah (frame 2) are cut at HALF scale, not 1:1: the window is 27 px across,
# Matt's five-spike crest is 54 and Computah's head with its ear pods 51, so at 1:1 neither his
# yellow-tipped crest nor the robot's silhouette could be in it. Each grid below is the approved
# frame taken 2:1 - one pixel per 2x2 block - in the sprite's own colours, keyed per hex, then
# hand-cleaned where halving broke a keyline. art_source/derived_0923/icons_0923.py derives the
# grids, measures how much of each is the sprite's own, and holds the reasoning.
def grid_cell(key, rows, pal, ox, oy, col, shade):
    """A half-scale head from a grid of its sprite's own colours (pal: grid key -> hex), coloured
    through REMAP[key] as crop_icon colours a crop, with grid (0, 0) on cell (ox, oy)."""
    rm = REMAP[key]
    cv = Canvas(S, S)
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch != '.' and in_win(ox + i, oy + j, PAD):
                h = pal[ch]
                cv.set(ox + i, oy + j, rm[h] if h in rm else h)
    bg_disc(cv, col, shade)
    return cv


# matt.png frame 0 from x20 y0, 2:1; keys as art_source/matt/pal.py names them.
MATT_PAL = {'k': '000000', '1': 'fbd6b0', '2': 'f0b98e', '3': 'db976c', '4': 'b86c4e',
            '5': '84412f', '6': '552619', 'a': 'fff6be', 'b': 'f8db66', 'c': 'e2b13c',
            'd': 'ac7c26', 'e': '6a4618', 'h': '15121f', 'i': '272337', 'j': '3c3654',
            'l': '5c5480', 'W': 'ffffff', 'X': 'd5d9ec', 'A': 'dcdeff', 'B': 'b3b6f2',
            'C': '8e91da', 'D': '6d6fbc', 'E': '4f4d96', 'F': '332f68', 'K': '1a1a25',
            'L': '2a2a38', 'M': '3f3f52', 'N': '5a5a70', 'x': '9da1c0', 'm': '2c0a1c',
            'n': '5c1634', 'q': 'c8526e', 'r': 'ee8ca2'}
MATT_HEAD = [
    "..............k.............",
    ".............kbk............",
    "............kack............",
    ".......kk...kacdk..kkk......",
    "......kbcck.kacdk.kacdk.....",
    "......kbcck.kbihkkabdk......",
    ".......kbciiljihklacdk......",
    ".......kbiiijjihljihk.......",
    "..kkkkkkkiiijjihhiihkkkkkkk.",
    "kbbbbbjjhiijjiihhihhlljaabbk",
    "kcccciiiijijjiihhihhjjicccdk",
    ".kkddiiiijjjjiiihhhhiiihdkk.",
    "...khiiiijhiiiiiihhiiihhk...",
    "....kkiiihiihiihhhiihhhk....",
    ".....kiiiikkkkkkkkkiiik.....",
    "......kii1122222223kiik.....",
    "......kik2hh2222hhh3kik.....",
    "......kikkkk22222kkkkik.....",
    ".....k3k1WhX22222WhXk4k.....",
    ".....k4k123221222232k5k.....",
    ".....k4k122222122223k5k.....",
    "......kk122223432223kk......",
    "........k22kkkkkkkk3k.......",
    "........k22kWWWWWk33k.......",
    "........k122kkkkk33k........",
    ".......kbk2222334kkdk.......",
    "........kbkkkkkkkcddk.......",
    "........kbbcccccccddk.......",
]


def matt_cell():
    """Matt's slot, from the approved 2026-09-23 matt.png frame 0 (the idle) at half scale: all
    five spikes of the crest with their yellow tips - the outer pair's points under the ring -
    over the brows, the eyes and the lopsided grin, the yellow collar at the foot of the disc.
    Sky-blue disc, the complement the yellow tips stand out on."""
    return grid_cell('matt', MATT_HEAD, MATT_PAL, 6, 6, SKY, BLURPLE)


# computah_idle.png frame 0 (the idle his fight plays) from x16 y5, 2:1; keyline #0C111A.
COMPUTAH_PAL = {'k': '0c111a', 'K': '0d1118', 'Q': '131821', 'n': '1a212c', 'v': '222a38',
                'w': '2a3341', 'x': '2b3444', 'y': '3c4757', 'z': '3f4a5c', '5': '5e6c82',
                '6': '6c7a8e', '8': '8091a8', 'g': 'a6b8cc', 'p': 'cedcea', 'q': 'd8e4f2',
                'W': 'f2f8ff', 'D': '391555', 'C': '592687', 'B': '7c3bb4', 'A': 'a063dc',
                'H': 'c892f2', 'r': '93302c', 'R': 'ff4436', 't': '2a7a3c', 'G': '1f9a38',
                'L': '4fe066', 'V': 'a9ffb4'}
COMPUTAH_HEAD = [
    "..k..........................",
    ".kVkk........................",
    "kVVLk........................",
    "kVVLLk.......................",
    "kLLLppkk.....................",
    ".kkkgpppk....................",
    "....kpppWk...kkkkkkk.........",
    ".....kp8pWkkkHHAAAAAkk.......",
    "......kgpkkHAAAAAAABBBk......",
    ".......kkBAAAAAAAAABBBBk.....",
    "......kABkkkkkkkkkkkkkCCk....",
    ".....kABk6666666666666kDDk...",
    ".....kBBkvrRRvvvvvrRRvkDDk...",
    "....kkkBkvrRRvvvvvrRRvkDkkk..",
    "...kADDCkvrrrvvvvvrrrvkBBBBk.",
    "..kADWWDkvvvvvvvvvvvvvkDWWDCk",
    "..kAgggpkvqKqKqKqKqKqvkDgggDk",
    "..kDgw8gkvvvvvvvvvvvvvkDgw5Dk",
    "..kCDpgDkkkkkkkkkkkkkkkDpgDDk",
    "...kDDDDkpgpppppppg855kCDDDk.",
    "....kkkk.kgggggggg855k.kkkk..",
    "..........k888888855k........",
    "...........kkkkkkkkk...kkk...",
    "..kkkkkk....kWWppp8k.kkAABkk.",
    ".kABBBCCkkkkkkkkkkkkkABBBBCk.",
    "kABBBBCCkAAAABBBBBBAkBBBBBCk.",
    "kABBBCCDkCCCCCCCCCCCkBBBBBBBk",
    "kBBBCCDDkDkkkkkkkkkkkkBBBBBBD",
]


def computah_cell():
    """Computah's slot, from the redesigned robot of 2026-09-22 (computah_idle.png frame 0) at
    half scale: the purple dome, the visor with its red eyes and grille, both ear pods, the chin
    plate and the antenna stalk running off under the ring. The slot showed Greyson in the
    retired mech until now. Lime disc: his charge green, the complement of his purple."""
    return grid_cell('computah', COMPUTAH_HEAD, COMPUTAH_PAL, 5, 6, LIME, GREEN)


# burak_boss.png frame 0 (Captain Burak, the idle) from x22 y1, 2:1.
BURAK_PAL = {'k': '000000', '1': 'e2a874', '2': 'd79864', '3': 'be8254', '4': 'ac714f',
             '5': 'a88068', '6': 'c8705e', 'h': '0d0909', 'i': '1a1212', 'j': '281810',
             'J': '2a1d19', 'l': '36251e', 'm': '503729', 'n': '5c3b28', 'o': '7c5438',
             'T': '15151d', 'U': '23232f', 'V': '353547', 'W': '4e4f66', 'X': '444a5c',
             'Y': '6d7589', 'a': 'fff3b0', 'b': 'f5d94e', 'c': 'e0ab35', 'd': 'b07d22',
             'e': '7a5216', 'A': 'd8434f', 'B': 'b02436', 'C': '7e162b', 'D': '4a0c1b',
             'E': 'd95763', 'F': 'ac3232', 'G': '6e1f22', 'w': 'fffcf4', 'x': 'e8e1d3',
             'y': 'dce3ee', 'z': 'c3b9a9', 'q': 'a6afc1'}
BURAK_HEAD = [
    "kk......kkkkkkkkkkk......k......",
    ".kk...kWWWWWWWWVVVUk....ck......",
    ".kbkkkWWWWWWWWVVVUUUTkkck.......",
    "..kbbkkkWWWWVVVVUUUkkccck.......",
    "...TVbbbkkkVVVUUkkcccUUk....kk..",
    "....kkTVbbbkkUkcccUUkkkkkkkkEGk.",
    "...kkhmkkTUbaccTTkkkiikEEEEGGk..",
    "....kmhmJkkkUcTkkJJiihkFFFkk....",
    "....kmlJihmJkkhJJJJJhikkkkkk....",
    "...khhJihlJihiihiJJhJhkGGGFEkk..",
    "...khmihlihhkJJhhhiJhikkkkkkkk..",
    "...khihmihhk2kJiiihhhik.........",
    "...khhhlhik222Jikkiihikk........",
    "...khhhhkk2222khk3kiihik........",
    "...Jhkikkkkk22kikkkiikik........",
    "...kkkk1kkk2222ikk4kkkkk........",
    "....k4k1wkw22223kw44knk.........",
    "....k3k1222222223334k4..........",
    ".....kk1222223223334k...........",
    "......k1222234323k34k...........",
    "X.....k122kkkkkkk434k...........",
    "YXk...k112266322334k............",
    "wqXk...k12235323344.............",
    ".kyYXkkkkk3333444kkkkk..........",
    "..kkqkkBkkkkkkkkkkCCBBC.........",
    "..kAkkkkBk2yxxzykCCkBBCD........",
]


def burak_boss_cell():
    """Burak's slot, from his approved boss design (burak_boss.png frame 0, the idle) at half
    scale: the tricorn's crown and its gold-trimmed brim sweeping down to the front point - the
    upturned tips under the ring - over the curtain bangs parted on his forehead, the eyes, the
    smirk rising to his right, and the red bandana tails at the ring. The slot showed the hooded
    cutscene Burak until now; the cyan disc is the slot's own."""
    return grid_cell('burak_boss', BURAK_HEAD, BURAK_PAL, 7, 8, CYAN, STEEL)


def build():
    ic = {}
    ic['burak'] = burak_boss_cell()
    ic['matt'] = matt_cell()
    ic['danny'] = crop_icon('danny', CHAR + "Danny/danny.png", 38, 16)
    bg_disc(ic['danny'], KHAKI, MUD)
    ic['eric'] = crop_icon('eric', CHAR + "Eric/eric_redesign_sheet.png", 64, 53)
    bg_disc(ic['eric'], STEEL, NAVY)
    ic['computah'] = computah_cell()
    # Their own slots each now, off their final solo sheets: Josh's approved redesign (frame 0 of
    # josh_cards.png), framed high enough that the whole spade medallion, the band and the brim
    # read as his hat, with both eyes, the smirk's tooth glint and the top of the boxed beard
    # below it - and Carter's polished head (carter_cell), framed on the dome, the glare and the
    # beard like the other portraits.
    ic['josh'] = crop_icon('josh', CHAR + "Josh/josh_cards.png", 42, 21)
    bg_disc(ic['josh'], ORANGE, RUST)
    ic['carter'] = carter_cell()
    ic['mason'] = crop_icon('mason', CHAR + "Mason/mason.png", 32, 20)
    bg_disc(ic['mason'], RED, BROWN)
    a = crop_icon('liam', CHAR + "Liam/liam.png", 38, 18)
    bg_disc(a, TEAL, OLIVE)
    b = crop_icon('bixby', CHAR + "Bixby/bixby.png", 26, 15)
    bg_disc(b, SKY, BLURPLE)
    ic['liam_bixby'] = split(a, b, -0.35)
    ic['jordan'] = jordan_cell()
    ic['invite'] = invite_icon()
    return [ic[k] for k in ORDER]


def strip(frames):
    out = Canvas(S * len(frames), S)
    for i, f in enumerate(frames):
        out.blit(f, i * S, 0)
    return out


if __name__ == '__main__':
    od = sys.argv[1].rstrip('/') + '/'
    fr = build()
    strip(fr).save(od + 'rank_icons.png')
    # preview: icons under frames (rows: cleared / current / locked; the invite shows GOAL in row 0)
    sl = slots.build()
    prev = Canvas(S * len(fr), S * 3)
    for i, f in enumerate(fr):
        for row, st in enumerate([1, 2, 0]):
            prev.blit(f, i * S, row * S)
            prev.blit(sl[4 if (i == len(fr) - 1 and st == 1) else st], i * S, row * S)
    prev.save(od + 'rank_icons_preview.png')
    print('ok')
