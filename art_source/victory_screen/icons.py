"""Boss face icons for the rank ladder (40x40 cells; art visible inside the slot window).
Built from the approved sprites' heads (1:1 pixels, remapped to DB32 by hand-checked tables),
duo slots as diagonal tag-team splits, plus an original INVITE envelope icon.
Frame order (approved boss order):
0 Burak, 1 Eric, 2 Greyson & Computah (mech), 3 Matt (placeholder - no art yet), 4 Mason,
5 Josh, 6 Danny, 7 Carter, 8 Liam & Bixby, 9 Jordan (final boss), 10 Invite.
python icons.py outdir"""
import sys, math
from cv import *
import slots

ASSETS = "C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/"
CHAR = ASSETS + "Characters/"
S = 40
ORDER = ['burak', 'eric', 'mech', 'matt', 'mason', 'josh', 'danny', 'carter', 'liam_bixby',
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
                                'a07c46': BRASS, '74562e': MUD, '6e5230': MUD, '50381c': BROWN}),
    # His deepened palette: bone duster (WHITE..DASH), wine fedora crown (PLUM/RED, one PINK
    # highlight - the mid wine shares RED so the crown doesn't read pink at portrait size), gold
    # band and spade rim on DB32's own gold ramp, and lenses dark enough for the PALE streak to
    # stay the glint.
    'josh': dict(SKIN_MAP, **{'0d0d13': K, '130b09': K, '1f1d17': K, '1c1c24': NAVY, '24160f': PLUM,
                              '2b0a12': PLUM, '3d261a': PLUM, '5f3c29': BROWN, 'b58773': TAN,
                              'e0917c': PINK, 'd9ab93': SKIN, 'f4ead6': WHITE, 'fff0dc': WHITE,
                              'e8e2ce': PALE, 'c6bfa4': GREY, '918b72': DGREY, '5e5a48': DASH,
                              '39362b': SLATE, '4d1420': PLUM, '7a2032': RED, 'a63b4b': RED,
                              'c96c74': PINK, '7a5216': MUD, 'b07d22': BRASS, 'e0ab35': TAN,
                              'f5d94e': YEL, 'fff3b0': WHITE, '0d1f4a': NAVY, '20203c': NAVY,
                              '32335c': INDIGO, '45487f': INDIGO, '1b3f86': STEEL, 'bde0ff': PALE,
                              '32323e': NAVY, '50505e': DASH, '7e7e90': DGREY, 'e07a2c': ORANGE}),
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
    'jordan': dict(SKIN_MAP, **{'7a2626': BROWN, 'b05e97': PURPLE, 'e49acd': ROSE, '8a4574': PURPLE,
                                'ae8358': RUST, '90765e': BROWN, 'f2c0df': PALE}),
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


def build():
    ic = {}
    ic['burak'] = crop_icon('burak', ASSETS + "Cutscenes/Intro/burak_cutscene.png", 166, 26)
    bg_disc(ic['burak'], CYAN, STEEL)
    ic['matt'] = placeholder_icon(GREY, DASH)
    ic['danny'] = crop_icon('danny', CHAR + "Danny/danny.png", 38, 16)
    bg_disc(ic['danny'], KHAKI, MUD)
    ic['eric'] = crop_icon('eric', CHAR + "Eric/eric_redesign_sheet.png", 64, 53)
    bg_disc(ic['eric'], STEEL, NAVY)
    ic['mech'] = crop_icon('mech', CHAR + "GreysonMech/greyson_mech.png", 48, 24)
    bg_disc(ic['mech'], PURPLE, PLUM)
    # Their own slots each now, off their final solo sheets: Josh's idle, whose head is drawn for
    # this crop - low enough to keep the hair he's identified by and the goatee, which costs the
    # top of the spade - and Carter's crossed-arms pose, framed on the glare and the beard like
    # the other portraits.
    ic['josh'] = crop_icon('josh', CHAR + "Josh/josh_cards.png", 40, 31)
    bg_disc(ic['josh'], ORANGE, RUST)
    ic['carter'] = crop_icon('carter', CHAR + "Carter/carter_akuma.png", 143, 26)
    bg_disc(ic['carter'], BLURPLE, INDIGO)
    ic['mason'] = crop_icon('mason', CHAR + "Mason/mason.png", 32, 20)
    bg_disc(ic['mason'], RED, BROWN)
    a = crop_icon('liam', CHAR + "Liam/liam.png", 38, 18)
    bg_disc(a, TEAL, OLIVE)
    b = crop_icon('bixby', CHAR + "Bixby/bixby.png", 26, 15)
    bg_disc(b, SKY, BLURPLE)
    ic['liam_bixby'] = split(a, b, -0.35)
    ic['jordan'] = crop_icon('jordan', CHAR + "Jordan/jordan.png", 33, 17)
    bg_disc(ic['jordan'], GREEN, TEAL)
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
