"""Boss face icons for the rank ladder (40x40 cells; art visible inside the slot window).
Built from the approved sprites' heads (1:1 pixels, remapped to DB32 by hand-checked tables),
duo slots as diagonal tag-team splits, plus an original INVITE envelope icon.
Frame order (approved boss order):
0 Eric, 1 Computah & Greyson (mech), 2 Carter & Josh, 3 Mason, 4 Liam & Bixby,
5 Jordan (final boss), 6 Invite.
python icons.py outdir"""
import sys, math
from cv import *
import slots

CHAR = "C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/"
S = 40
ORDER = ['eric', 'mech', 'carter_josh', 'mason', 'liam_bixby', 'jordan', 'invite']


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
    'carter': dict(SKIN_MAP, **{'d66c28': ORANGE, 'f09040': TAN, '703414': BROWN, 'b05b21': RUST,
                                '4a2c1a': PLUM, 'e6ecf2': WHITE}),
    'josh': dict(SKIN_MAP, **{'130b09': K, '24160f': PLUM, '3a2014': PLUM, '3d261a': PLUM,
                              '5f3c29': BROWN, '8a5b3d': RUST, '173c8a': INDIGO, '2a67c9': BLURPLE,
                              '5fa8f0': SKY, 'c8ecff': PALE, 'd3d9e4': PALE, 'fff0dc': WHITE}),
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


def build():
    ic = {}
    ic['eric'] = crop_icon('eric', CHAR + "Eric/eric_redesign_sheet.png", 64, 53)
    bg_disc(ic['eric'], STEEL, NAVY)
    ic['mech'] = crop_icon('mech', CHAR + "GreysonMech/greyson_mech.png", 48, 24)
    bg_disc(ic['mech'], PURPLE, PLUM)
    a = crop_icon('carter', CHAR + "Carter/carter_redesign.png", 38, 16)
    bg_disc(a, BLURPLE, INDIGO)
    b = crop_icon('josh', CHAR + "Josh/josh_redesign.png", 25, 17)
    bg_disc(b, ORANGE, RUST)
    ic['carter_josh'] = split(a, b, 0.35)
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
