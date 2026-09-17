"""Jeering Punch-Out-style stands for the defeat screen, built in the approved
crowd_v2 part language (art_source/crowd/crowd.py, copied here as crowdv2_ref).
Adds an XL figure size for this screen's closer camera plus jeer poses
(point at the ring, thumbs down, cupped-hands boo, fist shake, L-on-forehead)
and the GG EZ / L / skull signs."""
import random
import crowdv2_ref as cv
from crowdv2_ref import P, Bag, mirror_part, SYM, SHIFT_OF, SKINS, HAIRS, CLOTH, FOAM_RAMPS, METAL, rc
from crowdv2_ref import K0, NAVY, PLUM, DBRN, RUST, TAN, PEACH, GREY1, GREY3, ICE, WHITE, RED, PINK, BLURP, INDIGO, GOLD
from font import G35

W, H = 640, 360

# ------------------------------------------------------------------ depths
# 0 = spotlight spill (front centre) ... 5 = lost in the dark behind the title
DEPTHS = [
    dict(outline=NAVY, skin=0, cloth=0, hair=0, eyes=True, mouth=True),
    dict(outline=NAVY, skin=1, cloth=1, hair=1, eyes=True, mouth=True),
    dict(outline=K0, skin=1, cloth=2, hair=2, eyes=True, mouth=True),
    dict(outline=K0, skin=2, cloth=3, hair=2, eyes=True, mouth=False),
    dict(outline=K0, skin=3, cloth=3, hair=3, eyes=False, mouth=False),
    dict(outline=K0, skin=4, cloth=4, hair=4, eyes=False, mouth=False),
]

# ------------------------------------------------------------------ XL parts
# head interior x0..7, y0..8 ; eyes at (2,4),(5,4) ; centre2 = 7
XL_TORSO = P(-3, 9,
    '...KCCCCCCc...',
    '.KKCCCCCCCCcc.',
    'KKCCCCCCCCCCcc',
    'KCCcCCCCCCcCCc',
    *(['CCCcCCCCCCcCCc'] * 18))

XL_HEADS = {
    'short': P(0, 0,
        '.IHHHHh.',
        'IHHHHHHh',
        'HHHHHHHh',
        'HSSSSSSH',
        'SSeSSeSs',
        'SSSSSSSs',
        'SSSSSSSs',
        '.SSSSSs.',
        '..SSSs..'),
    'bald': P(0, 0,
        '..LLSS..',
        '.LLSSSs.',
        'LLSSSSSs',
        'LSSSSSSs',
        'SSeSSeSs',
        'SSSSSSSs',
        'SSSSSSSs',
        '.SSSSSs.',
        '..SSSs..'),
    'bangs': P(0, 0,
        '.IHHHHh.',
        'IHHHHHHh',
        'IHHHHHHh',
        'IHHHHHhh',
        'SSeSSeSs',
        'SSSSSSSs',
        'SSSSSSSs',
        '.SSSSSs.',
        '..SSSs..'),
    'long': P(-1, 0,
        '..IHHHHh..',
        '.IHHHHHHh.',
        'IHHSSSSHhh',
        'IHSSSSSSHh',
        'HSSeSSeSsh',
        'HSSSSSSSsh',
        'HSSSSSSSsh',
        'Hh.SSSSshh',
        'Hh..SSS.hh',
        'hh......hh'),
    'cap': P(-1, -1,
        '...UTTt...',
        '..UTTTTt..',
        '.UTTTTTTt.',
        '.UTTTTTTt.',
        'tttttttttt',
        '.SSeSSeSs.',
        '.SSSSSSSs.',
        '.SSSSSSSs.',
        '..SSSSSs..',
        '...SSSs...'),
    'beanie': P(0, -2,
        '...UT...',
        '..UTTt..',
        '.UTTTTt.',
        'UTTTTTTt',
        'UTTTTTTt',
        'tTtTtTtT',
        'SSeSSeSs',
        'SSSSSSSs',
        'SSSSSSSs',
        '.SSSSSs.',
        '..SSSs..'),
    'afro': P(-2, -3,
        '...IHHHHh...',
        '.IHHHIHHHHh.',
        'IHHIHHHHHIHh',
        'IHHHHHHHHHHh',
        'HHIHHHHHHHhh',
        'HHHHHHHHHHHh',
        'HHSSSSSSSSHh',
        'hHSSeSSeSSHh',
        '.hSSSSSSSshh',
        '..SSSSSSSs..',
        '...SSSSSs...',
        '....SSSs....'),
    'hood': P(-2, -1,
        '...KCCCCc...',
        '..KCCCCCCc..',
        '.KCCHHHHCCc.',
        'KCCHHHHHHCcc',
        'KCHSSSSSSHCc',
        'KCSSeSSeSSCc',
        'KCSSSSSSSsCc',
        'KCSSSSSSSsCc',
        'KC.SSSSSs.Cc',
        'KC..SSSs..Cc'),
    'headset': P(-2, 0,
        '...aAAAAa...',
        '..aIHHHHha..',
        '.AAHHHHHHAA.',
        'AAHSSSSSSHAA',
        'AASSeSSeSsAA',
        '.ASSSSSSSSs.',
        '..SSSSSSSs..',
        '...SSSSSs...',
        '....SSSs....'),
    'shades': P(0, 0,
        '.IHHHHh.',
        'IHHHHHHh',
        'HHHHHHHh',
        'HSSSSSSH',
        'gWgSSgWg',
        'SSSSSSSs',
        'SSSSSSSs',
        '.SSSSSs.',
        '..SSSs..'),
    'headband': P(0, 0,
        '.IHHHHh.',
        'IHHHHHHh',
        'HHHHHHHh',
        'TTTTTTTt',
        'SSeSSeSs',
        'SSSSSSSs',
        'SSSSSSSs',
        '.SSSSSs.',
        '..SSSs..'),
    'mohawk': P(0, -3,
        '...IH...',
        '...IH...',
        '...IH...',
        '.LLIHSs.',
        'LLSIHSSs',
        'LSSIHSSs',
        'SSSSSSSs',
        'SSeSSeSs',
        'SSSSSSSs',
        'SSSSSSSs',
        '.SSSSSs.',
        '..SSSs..'),
}
XL_MOUTHS = {
    'laugh': [(2, 6), (3, 6), (4, 6), (5, 6), (3, 7), (4, 7)],
    'open': [(3, 6), (4, 6), (3, 7), (4, 7)],
    'grin': [(2, 6), (3, 7), (4, 7), (5, 6)],
}

# arms are authored for the figure's LEFT side (screen left); mirrored for the right
XL_ARMS = {
    'up': P(-7, -3,
        'LSSs..',
        'SSSs..',
        'SSSs..',
        '.SSs..',
        '.SSs..',
        '.SSs..',
        '.SSs..',
        '..KCC.',
        '..KCC.',
        '..KCC.',
        '..KCCC',
        '...KCC',
        '...KCC',
        '...KCC'),
    'thumb': P(-10, 0,
        'LSSs.....',
        'SSSSs....',
        'SSSsSs...',
        '.Ss..Ss..',
        '.Ss..KC..',
        '.s....KC.',
        '......KC.',
        '.......KC',
        '.......KC',
        '.......KC'),
    'point': P(-14, 6,
        '...LSs.......',
        'SSSSSSSSs....',
        '...SSsSSSKCC.',
        '........KKCCC',
        '..........KCC'),
    'cup': P(-1, 5,
        '.LS',
        '.LS',
        '.Ss',
        'Ss.',
        'KC.',
        'KC.'),
    'hold': P(-4, -4,
        'Ss.',
        'Ss.',
        'Ss.',
        'Ss.',
        'Ss.',
        'Ss.',
        'Ss.',
        'KC.',
        'KC.',
        'KC.',
        'KCC',
        'KCC',
        '.KC',
        '.KC'),
    'loser': P(-2, -6,
        '..S...',
        '..S...',
        '..S...',
        '..SSSs',
        '.SSS..',
        '.SS...',
        'SSs...',
        'Ss....',
        'Ss....',
        'Ss....',
        'KC....',
        'KC....',
        'KCC...',
        '.KC...',
        '.KC...',
        '.KC...'),
}
IN_FRONT = {'cup', 'loser'}          # drawn over the head


def sign_from_text(text, big=False):
    """ICE card with RED text in the 3x5 font (auto-outlined when stamped)."""
    glyph_rows = [''] * 5
    for i, ch in enumerate(text):
        g = G35[ch]
        for r in range(5):
            glyph_rows[r] += g[r].replace('1', 'R').replace('0', 'B') + ('B' if i < len(text) - 1 else '')
    tw = len(glyph_rows[0])
    w = tw + 4
    rows = ['b' + 'B' * (w - 2) + 'b', 'B' * w]
    for r in glyph_rows:
        rows.append('BB' + r + 'BB')
    rows.append('B' * w)
    rows.append('b' * w)
    return rows


SIGN_ROWS = {
    'ggez': sign_from_text('GG EZ'.replace(' ', ' ')),
    'L': [
        'bBBBBBBBBb',
        'BBBBBBBBBB',
        'BBRRBBBBBB',
        'BBRRBBBBBB',
        'BBRRBBBBBB',
        'BBRRBBBBBB',
        'BBRRRRRBBB',
        'BBRRRRRBBB',
        'BBBBBBBBBB',
        'bbbbbbbbbb',
    ],
    'skull': [
        'GGGGGGGGGGG',
        'GGGWWWWWGGG',
        'GGWWWWWWWGG',
        'GGWGGWGGWGG',
        'GGWGGWGGWGG',
        'GGWWWGWWWGG',
        'GGGWWWWWGGG',
        'GGGWGWGWGGG',
        'GGGGGGGGGGG',
    ],
}
PROP_COL = cv.PROP_COL


def sign_part(name):
    rows = SIGN_ROWS[name]
    w = len(rows[0])
    ox = 4 - w // 2          # centred on the head (centre x = 3.5)
    oy = -4 - len(rows)      # bottom edge sits on the raised hands
    return P(ox, oy, *rows)


# ------------------------------------------------------------------ canvas
def stamp(canvas, part, fx, fy, colour_of, outline, clip=None):
    ox, oy, rows = part
    pts = {}
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch != '.':
                pts[(fx + ox + i, fy + oy + j)] = ch
    if outline is not None:
        for (x, y) in pts:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q not in pts and 0 <= q[0] < W and 0 <= q[1] < H and (clip is None or clip(*q)):
                    canvas[q[1]][q[0]] = outline
    for (x, y), ch in pts.items():
        if 0 <= x < W and 0 <= y < H and (clip is None or clip(x, y)):
            c = colour_of(ch)
            if c is not None:
                canvas[y][x] = c


def figure_colour(f, depth):
    d = DEPTHS[depth]
    mats = {
        'skin': SKINS[f['skin']], 'hair': HAIRS[f['hair']], 'cloth': CLOTH[f['cloth']],
        'hat': CLOTH[f['hat']], 'acc': FOAM_RAMPS['blurp'], 'metal': METAL,
    }

    def colour_of(ch):
        mat, off = SYM[ch]
        if mat == 'shade':
            return NAVY if depth < 2 else K0
        if mat == 'glint':
            return GREY1 if depth == 0 else rc(METAL, 1, d['hair'])
        if ch == 'e' and not d['eyes']:
            off = 0
        return rc(mats[mat], off, d[SHIFT_OF[mat]])
    return colour_of


PARTS = {
    'XL': (XL_TORSO, XL_HEADS, XL_ARMS, 7, XL_MOUTHS),
    'L': (cv.L_TORSO, cv.L_HEADS, cv.L_ARMS, 5, None),
    'S': (cv.S_TORSO, cv.S_HEADS, cv.S_ARMS, 4, None),
}


def draw_figure(canvas, f, clip=None):
    depth = f['depth']
    d = DEPTHS[depth]
    out = d['outline']
    fx, fy = f['fx'], f['fy']
    col = figure_colour(f, depth)
    torso, heads, arms, centre2, mouths = PARTS[f['size']]
    stamp(canvas, torso, fx, fy, col, out, clip)
    pose = f.get('pose')
    parts = []
    kind = None
    if pose:
        kind, side = pose[:-1], pose[-1]
        if f['size'] == 'S' and kind in ('point', 'thumb', 'loser', 'hold'):
            kind = 'v' if kind != 'hold' else 'up'
        if f['size'] == 'L' and kind in ('thumb', 'loser'):
            kind = 'up'
        base = arms[kind]
        if side in 'LB':
            parts.append(base)
        if side in 'RB':
            parts.append(mirror_part(base, centre2))
    front = kind in IN_FRONT or kind == 'cup'
    if not front:
        for p in parts:
            stamp(canvas, p, fx, fy, col, out, clip)
    stamp(canvas, heads[f['head']], fx, fy, col, out, clip)
    if d['mouth'] and f.get('mouth'):
        if f['size'] == 'XL':
            pts = mouths[f['mouth']]
        else:
            mx, my = cv.L_MOUTH if f['size'] == 'L' else cv.S_MOUTH
            pts = [(mx + i, my) for i in range(2 if f['size'] == 'L' else 1)]
        for (mx, my) in pts:
            x, y = fx + mx, fy + my
            if 0 <= x < W and 0 <= y < H and (clip is None or clip(x, y)):
                canvas[y][x] = col('m')
    if front:
        for p in parts:
            stamp(canvas, p, fx, fy, col, out, clip)
    if f.get('sign'):
        pal = PROP_COL[0 if depth <= 1 else 1]
        part = sign_part(f['sign'])
        stamp(canvas, part, fx, fy, lambda ch: pal[ch], out, clip)
        ox, oy, rows = part
        by = fy + oy + len(rows) - 1
        for hx in (fx + ox, fx + ox + len(rows[0]) - 1):
            for y in (by, by + 1):
                if 0 <= hx < W and 0 <= y < H:
                    canvas[y][hx] = col('S')


def lineup(out_png):
    """test sheet: every XL head + every jeer pose"""
    from pngio import write_png, upscale
    global W, H
    W, H = 230, 120
    canvas = [[NAVY] * W for _ in range(H)]
    heads = list(XL_HEADS)
    poses = [None, 'upL', 'thumbL', 'thumbR', 'pointL', 'pointR', 'cupB', 'loserL', 'holdB']
    x = 14
    rng = random.Random(3)
    for i, hname in enumerate(heads):
        f = dict(size='XL', depth=1, fx=8 + i * 18, fy=14, head=hname, skin=['fair', 'tan', 'deep'][i % 3],
                 hair=['black', 'brown', 'blonde', 'grey'][i % 4], cloth=['rust', 'dbrown', 'plum', 'r_teal'][i % 4],
                 hat=['navy', 'r_red', 'grey'][i % 3], pose=None, mouth=['laugh', 'open', 'grin'][i % 3])
        draw_figure(canvas, f)
    for i, pose in enumerate(poses):
        f = dict(size='XL', depth=0, fx=12 + i * 24, fy=78, head='short', skin='tan', hair='black',
                 cloth='rust', hat='navy', pose=pose, mouth='laugh',
                 sign={'holdB': 'ggez'}.get(pose))
        draw_figure(canvas, f)
    rows = [[(c[0], c[1], c[2], 255) for c in r] for r in canvas]
    w2, h2, big = upscale(W, H, rows, 6)
    write_png(out_png, w2, h2, big)
    W, H = 640, 360


if __name__ == '__main__':
    lineup('out/stands_lineup_6x.png')


# ------------------------------------------------------------------ layout
XL_HEAD_W = {'short': 6, 'bald': 3, 'bangs': 3, 'long': 4, 'cap': 4, 'beanie': 3, 'afro': 2,
             'hood': 2, 'headset': 2, 'shades': 2, 'headband': 2, 'mohawk': 1}
JEER_XL = {'still': 9, 'up': 4, 'thumb': 4, 'point': 4, 'cup': 3, 'loser': 1}
JEER_L = {'still': 12, 'up': 3, 'cup': 2, 'point': 2}
JEER_S = {'still': 20, 'up': 2}
MOUTH_XL = {'laugh': 5, 'open': 3, 'grin': 2}

# (size, fy, pitch, x0, depth_fn(x))
def _spill(near, mid, far, r1, r2):
    return lambda x: near if abs(x - 320) < r1 else (mid if abs(x - 320) < r2 else far)


FAR_ROWS = [
    ('S', 36, 8, 2, _spill(5, 5, 5, 0, 0)),
    ('S', 42, 8, 6, _spill(4, 5, 5, 110, 110)),
    ('L', 49, 11, -2, _spill(4, 4, 4, 0, 0)),
    ('L', 58, 11, 3, _spill(3, 3, 4, 170, 170)),
    ('XL', 70, 15, -4, _spill(2, 3, 3, 170, 170)),
    ('XL', 85, 15, 3, _spill(1, 2, 2, 130, 130)),
    ('XL', 97, 15, -3, _spill(0, 1, 1, 90, 90)),
]
SIDE_ROWS = [(y, 15) for y in range(110, 250, 14)]


def side_l(y):
    return 58 - (y - 121) * (100 / 240.0)


def make_row(rng, size, fy, pitch, x0, depth_fn, x_lo=-12, x_hi=652, keep=None):
    heads = Bag(rng, XL_HEAD_W if size == 'XL' else (cv.L_HEAD_W if size == 'L' else cv.S_HEAD_W), 4)
    skins = Bag(rng, cv.SKIN_W, 1)
    hairs = Bag(rng, cv.HAIR_W, 1)
    cloths = Bag(rng, cv.CLOTH_W, 2)
    hats = Bag(rng, cv.HAT_W, 3)
    jeers = Bag(rng, JEER_XL if size == 'XL' else (JEER_L if size == 'L' else JEER_S), 2)
    mouths = Bag(rng, MOUTH_XL, 1)
    figs = []
    x = x_lo + x0
    while x < x_hi:
        fx = x + rng.choice([0, 0, 0, 1, -1])
        fyy = fy + rng.choice([0, 0, 0, 0, 1])
        if keep is None or keep(fx, fyy):
            j = jeers.draw()
            if j == 'still':
                pose = None
            elif j == 'point':
                pose = 'point' + ('R' if fx < 320 else 'L')
            elif j == 'cup':
                pose = 'cupB'
            elif j == 'loser':
                pose = 'loserL'
            else:
                pose = j + rng.choice(['L', 'R'])
            f = dict(size=size, depth=depth_fn(fx), fx=fx, fy=fyy, head=heads.draw(), skin=skins.draw(),
                     hair=hairs.draw(), cloth=cloths.draw(), hat=hats.draw(), pose=pose, sign=None)
            if size == 'XL':
                f['mouth'] = 'open' if pose == 'cupB' else mouths.draw()
            else:
                f['mouth'] = rng.random() < 0.6
            figs.append(f)
        x += pitch
    return figs


def place_sign(row_figs, ax, name):
    f = min(row_figs, key=lambda g: abs(g['fx'] - ax))
    f['sign'] = name
    f['pose'] = 'holdB'
    f['mouth'] = 'laugh' if f['size'] == 'XL' else True
    if f['head'] in ('cap', 'beanie', 'afro', 'hood', 'mohawk'):
        f['head'] = 'short'
    return f


DARKER = cv.DARKER


def build_stands(seed=4):
    rng = random.Random(seed)
    canvas = [[K0 if y < 64 else NAVY for x in range(W)] for y in range(H)]
    rows = []
    for (size, fy, pitch, x0, dfn) in FAR_ROWS:
        rows.append(make_row(rng, size, fy, pitch, x0, dfn))
    # signs held up in the XL rows
    place_sign(rows[4], 178, 'ggez')
    place_sign(rows[4], 462, 'L')
    place_sign(rows[5], 548, 'skull')
    for figs in rows:
        figs.sort(key=lambda f: (f['pose'] is not None, f['sign'] is not None))
        for f in figs:
            draw_figure(canvas, f)
    # side stands, ringside (closer to camera): only the strips outside the ring
    for i, (fy, pitch) in enumerate(SIDE_ROWS):
        dfn = (lambda x: 2)
        left = make_row(rng, 'XL', fy, pitch, (i * 7) % pitch, dfn, x_lo=-12, x_hi=int(side_l(fy)) + 4,
                        keep=lambda fx, fyy: fx + 3 < side_l(fyy + 8) + 2)
        right = make_row(rng, 'XL', fy, pitch, (i * 5) % pitch, dfn, x_lo=int(639 - side_l(fy)) - 12, x_hi=652,
                         keep=lambda fx, fyy: fx + 3 > 639 - side_l(fyy + 8) - 2)
        for f in left + right:
            if f['pose'] and f['pose'].startswith('point'):
                f['pose'] = 'point' + ('R' if f['fx'] < 320 else 'L')
        for figs in (left, right):
            figs.sort(key=lambda f: (f['pose'] is not None))
            for f in figs:
                draw_figure(canvas, f)
    # rows hidden behind the lower ropes sink darker (like crowd_v2's fade_bottom)
    for y in range(109, 121):
        steps = 1 if y < 115 else 2
        for x in range(W):
            c = canvas[y][x]
            for _ in range(steps):
                c = DARKER.get(c, K0)
            canvas[y][x] = c
    # back rows sink into the dark behind the title (whole DB32 steps, no dither)
    for y, steps in ((33, 4), (34, 4), (35, 3), (36, 3), (37, 3), (38, 2), (39, 2), (40, 2), (41, 1), (42, 1), (43, 1)):
        for x in range(W):
            c = canvas[y][x]
            for _ in range(steps):
                c = DARKER.get(c, K0)
            canvas[y][x] = c
    for y in range(0, 33):
        for x in range(W):
            canvas[y][x] = K0
    return canvas


def to_img(canvas):
    from lib import Img
    im = Img(W, H)
    for y in range(H):
        for x in range(W):
            c = canvas[y][x]
            im.p[y][x] = None if c is None else '%02x%02x%02x' % c
    return im
