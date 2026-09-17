"""Punch-Out style arena crowd generator for Project FMWO.

Every spectator is composed from hand-authored ASCII parts (torso, head, arms,
props). Each part is auto-outlined (4-neighbour) as it is stamped, so later
parts cut a clean dark line into earlier ones. Colours come from DB32 ramps and
are pushed darker per row depth.

Output: horizontal strip of 640x40 frames.
  frames 0-2 : idle loop
  frames 3-4 : cheer loop
"""
import os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pngio import write_png

FW, FH = 640, 40
N_IDLE, N_CHEER = 3, 2
NF = N_IDLE + N_CHEER

# ---------------------------------------------------------------- palette (DB32)
K0 = (0, 0, 0); NAVY = (34, 32, 52); PLUM = (69, 40, 60); DBRN = (102, 57, 49)
RUST = (143, 86, 59); ORNG = (223, 113, 38); TAN = (217, 160, 102); PEACH = (238, 195, 154)
YEL = (251, 242, 54); GRN = (106, 190, 48); TEAL = (55, 148, 110); OLIVE = (75, 105, 47)
MUD = (82, 75, 36); SLATE = (50, 60, 57); INDIGO = (63, 63, 116); STEEL = (48, 96, 130)
BLURP = (91, 110, 225); SKY = (99, 155, 255); CYAN = (95, 205, 228); ICE = (203, 219, 252)
WHITE = (255, 255, 255); GREY1 = (155, 173, 183); GREY2 = (132, 126, 135); GREY3 = (105, 106, 106)
GREY4 = (89, 86, 82); PURP = (118, 66, 138); RED = (172, 50, 50); PINK = (217, 87, 99)
MAUVE = (215, 123, 186); MOSS = (143, 151, 74); GOLD = (138, 111, 48)

# ramps run light -> dark; (ramp, base index at depth 0)
SKINS = {
    'fair': ([PEACH, TAN, RUST, DBRN, PLUM, NAVY, K0], 1),
    'tan':  ([TAN, RUST, DBRN, PLUM, NAVY, K0], 1),
    'deep': ([RUST, DBRN, PLUM, NAVY, K0, K0], 1),
}
HAIRS = {
    'black':  ([PLUM, NAVY, K0, K0], 1),
    'brown':  ([RUST, DBRN, PLUM, NAVY, K0], 1),
    'blonde': ([TAN, GOLD, MUD, NAVY, K0], 1),
    'ginger': ([ORNG, RUST, DBRN, PLUM, NAVY, K0], 1),
    'grey':   ([GREY1, GREY3, GREY4, SLATE, NAVY, K0], 1),
    'pink':   ([MAUVE, PURP, PLUM, NAVY, K0], 1),
    'blue':   ([CYAN, STEEL, INDIGO, NAVY, K0], 1),
}
CLOTH = {
    # crowd bulk: rusty browns, dark browns, plums
    'rust':   ([TAN, RUST, DBRN, PLUM, NAVY, K0], 1),
    'dbrown': ([RUST, DBRN, PLUM, NAVY, K0, K0], 1),
    'plum':   ([DBRN, PLUM, NAVY, K0, K0], 1),
    'navy':   ([INDIGO, NAVY, K0, K0], 1),
    'mud':    ([GOLD, MUD, SLATE, NAVY, K0], 1),
    'grey':   ([GREY3, GREY4, SLATE, NAVY, K0], 1),
    # muted "role colours" (base is the darker half of each hue)
    'r_red':    ([PINK, RED, DBRN, PLUM, NAVY, K0], 1),
    'r_blurp':  ([BLURP, INDIGO, NAVY, K0, K0], 1),
    'r_teal':   ([TEAL, OLIVE, SLATE, NAVY, K0], 1),
    'r_purple': ([MAUVE, PURP, PLUM, NAVY, K0], 1),
    'r_gold':   ([TAN, GOLD, MUD, NAVY, K0], 1),
    'r_blue':   ([SKY, STEEL, INDIGO, NAVY, K0], 1),
}
BULK = ['rust'] * 5 + ['dbrown'] * 5 + ['plum'] * 3 + ['navy', 'mud', 'grey']
ROLES = ['r_red', 'r_blurp', 'r_teal', 'r_purple', 'r_gold', 'r_blue']
FOAM_RAMPS = {
    'gold':  ([YEL, TAN, GOLD, MUD, NAVY, K0], 1),
    'blurp': ([SKY, BLURP, INDIGO, NAVY, K0], 1),
}
METAL = ([GREY1, GREY3, GREY4, SLATE, NAVY, K0], 1)

# per-row depth: 0 = front
DEPTHS = [
    dict(outline=NAVY, skin=0, cloth=0, hair=0, eyes=True,  mouth=True),
    dict(outline=NAVY, skin=1, cloth=1, hair=1, eyes=True,  mouth=True),
    dict(outline=K0,   skin=1, cloth=2, hair=2, eyes=True,  mouth=False),
    dict(outline=K0,   skin=1, cloth=3, hair=2, eyes=False, mouth=False),
]


# ---------------------------------------------------------------- parts
def P(ox, oy, *rows):
    return (ox, oy, rows)


# symbol -> (material, offset)
SYM = {
    'L': ('skin', -1), 'S': ('skin', 0), 's': ('skin', 1), 'e': ('skin', 3), 'm': ('skin', 3),
    'I': ('hair', -1), 'H': ('hair', 0), 'h': ('hair', 1),
    'K': ('cloth', -1), 'C': ('cloth', 0), 'c': ('cloth', 1),
    'U': ('hat', -1), 'T': ('hat', 0), 't': ('hat', 1),
    'X': ('acc', -1), 'Y': ('acc', 0), 'y': ('acc', 1),
    'A': ('metal', 0), 'a': ('metal', 1),
    'g': ('shade', 0), 'W': ('glint', 0),
}
SHIFT_OF = {'skin': 'skin', 'hair': 'hair', 'cloth': 'cloth', 'hat': 'cloth', 'acc': 'skin', 'metal': 'hair'}

# ---- LARGE figures (rows 2 and 3). Head interior is x0..5, y0..5; centre x=2.5
L_TORSO = P(-2, 6,
    '..KCCCCc..',
    '.KKCCCCCc.',
    'KKCCCCCCcc',
    'KCcCCCCcCc',
    *(['CCcCCCCcCc'] * 16))
L_HEADS = {
    'short': P(0, 0,
        '.IHHH.',
        'IHHHHh',
        'HSSSSH',
        'SeSSeS',
        'SSSSSs',
        '.SSSs.'),
    'bald': P(0, 0,
        '.LLSS.',
        'LLSSSs',
        'SSSSSs',
        'SeSSeS',
        'SSSSSs',
        '.SSSs.'),
    'bangs': P(0, 0,
        '.IHHH.',
        'IHHHHh',
        'IHHHHh',
        'SeSSeS',
        'SSSSSs',
        '.SSSs.'),
    'long': P(-1, 0,
        '..IHHH..',
        '.IHHHHh.',
        'IHSSSSHh',
        'HSeSSeSh',
        'HSSSSSsh',
        'Hh.SSshh',
        'Hh....hh'),
    'bun': P(0, -2,
        '..IH..',
        '..Hh..',
        '.IHHH.',
        'IHHHHh',
        'HSSSSH',
        'SeSSeS',
        'SSSSSs',
        '.SSSs.'),
    'cap': P(-1, -1,
        '..UTTt..',
        '.UTTTTt.',
        '.UTTTTt.',
        'tttttttt',
        '.SeSSeS.',
        '.SSSSSs.',
        '..SSSs..'),
    'beanie': P(0, -2,
        '..UT..',
        '.UTTt.',
        'UTTTTt',
        'UTTTTt',
        'tTtTtT',
        'SeSSeS',
        'SSSSSs',
        '.SSSs.'),
    'afro': P(-1, -2,
        '.IHHHHh.',
        'IHHIHHhh',
        'IHHHHHHh',
        'HHIHHHhh',
        'HHSSSSHh',
        'hSeSSeSh',
        '.SSSSSs.',
        '..SSSs..'),
    'mohawk': P(0, -2,
        '..IH..',
        '..IH..',
        '.LIHS.',
        'LSIHSs',
        'SSSSSs',
        'SeSSeS',
        'SSSSSs',
        '.SSSs.'),
    'headset': P(-1, 0,
        '.aAAAAa.',
        '.aHHHHa.',
        'AAHSSHAA',
        'AAeSSeAA',
        '.SSSSSs.',
        '..SSSs..'),
    'hood': P(-1, -1,
        '..KCCc..',
        '.KCCCCc.',
        'KCHHHHCc',
        'KCSSSSCc',
        'KCeSSeCc',
        'KCSSSsCc',
        'KC.SS.Cc'),
    'shades': P(0, 0,
        '.IHHH.',
        'IHHHHh',
        'HSSSSH',
        'gWggWg',
        'SSSSSs',
        '.SSSs.'),
    'cat': P(0, -2,
        'T....T',
        'TT..TT',
        '.IHHH.',
        'IHHHHh',
        'HSSSSH',
        'SeSSeS',
        'SSSSSs',
        '.SSSs.'),
    'balding': P(0, 0,
        '.LLSS.',
        'HLSSSH',
        'HSSSSH',
        'SeSSeS',
        'SSSSSs',
        '.SSSs.'),
    'headband': P(0, 0,
        '.IHHH.',
        'IHHHHh',
        'TTTTTt',
        'SeSSeS',
        'SSSSSs',
        '.SSSs.'),
}
L_MOUTH = (2, 5)  # two px at (2,5),(3,5)

L_ARMS = {
    'up': P(-4, -3,
        'LSs.',
        'SSs.',
        '.Ss.',
        '.Ss.',
        '.Ss.',
        '.Ss.',
        '.KC.',
        '.KC.',
        '.KC.',
        '.KCC',
        '.KCC'),
    'v': P(-6, -2,
        'LSs...',
        'SSs...',
        '.Ss...',
        '.Ss...',
        '..Ss..',
        '..KC..',
        '...KC.',
        '...KC.',
        '...KCC',
        '...KCC'),
    'point': P(-7, -2,
        'L......',
        '.SS....',
        '.SSs...',
        '..Ss...',
        '...Ss..',
        '...KC..',
        '....KC.',
        '....KC.',
        '....KCC',
        '....KCC'),
    'cup': P(-3, 3,
        '.LS',
        '.LS',
        '.Ss',
        'Ss.',
        'KC.',
        'KC.'),
    'hold': P(-3, -4,        # straight arm up to a sign's lower corner (hand drawn on the sign)
        'Ss.',
        'Ss.',
        'Ss.',
        'Ss.',
        'Ss.',
        'KC.',
        'KC.',
        'KC.',
        'KCC',
        'KCC'),
    'foam': P(-4, -2,        # raised arm that ends in the foam finger's cuff
        '.Ss.',
        '.Ss.',
        '.Ss.',
        '.Ss.',
        '.KC.',
        '.KC.',
        '.KC.',
        '.KC.',
        '.KCC',
        '.KCC'),
}

# ---- SMALL figures (rows 0 and 1). Head interior x0..4, y0..3; centre x=2
S_TORSO = P(-2, 5,
    '..KCCCc..',
    '.KCCCCCc.',
    *(['CCCCCCCCc'] * 16))
S_HEADS = {
    'short': P(0, 0,
        '.IHh.',
        'IHHHh',
        'HSSSH',
        'SeSeS',
        '.SSs.'),
    'bald': P(0, 0,
        '.LSS.',
        'LSSSs',
        'SSSSs',
        'SeSeS',
        '.SSs.'),
    'long': P(-1, 0,
        '..IHh..',
        '.IHHHh.',
        'IHSSSHh',
        'HSeSeSh',
        'HhSSshh'),
    'cap': P(-1, -1,
        '..UTt..',
        '.UTTTt.',
        'ttttttt',
        '.SSSSs.',
        '.SeSeS.',
        '..SSs..'),
    'beanie': P(0, -1,
        '.UTt.',
        'UTTTt',
        'tTtTt',
        'SSSSs',
        'SeSeS',
        '.SSs.'),
    'afro': P(-1, -1,
        '.IHHHh.',
        'IHHIHHh',
        'HHSSSHh',
        '.SSSSs.',
        '.SeSeS.',
        '..SSs..'),
    'bun': P(0, -2,
        '..H..',
        '.IHh.',
        'IHHHh',
        'HSSSH',
        'SSSSs',
        'SeSeS',
        '.SSs.'),
    'bangs': P(0, 0,
        '.IHh.',
        'IHHHh',
        'IHHHh',
        'SeSeS',
        '.SSs.'),
}
S_MOUTH = (2, 4)  # one px

S_ARMS = {
    'up': P(-4, -3,
        'SS.',
        'Ss.',
        '.S.',
        '.S.',
        '.S.',
        '.C.',
        '.CC',
        '.CC'),
    'v': P(-5, -2,
        'SS..',
        'Ss..',
        '.S..',
        '..S.',
        '..C.',
        '..CC',
        '..CC'),
    'cup': P(-2, 3,
        '.SS',
        '.S.',
        'C..',
        'C..'),
}

# ---- props (explicit colours, auto-outlined)
PROP_COL = [
    {'B': ICE, 'b': GREY1, 'R': RED, 'r': PINK, 'P': BLURP, 'p': INDIGO, 'G': NAVY,
     'O': GOLD, 'W': WHITE},
    {'B': GREY1, 'b': GREY3, 'R': RED, 'r': RED, 'P': INDIGO, 'p': NAVY, 'G': NAVY,
     'O': MUD, 'W': ICE},
]
SIGNS = {
    'heart': P(-2, -9,
        'bBBBBBBBb',
        'BBRrBRrBB',
        'BBRRRRRBB',
        'BBBRRRBBB',
        'BBBBRBBBB',
        'bbbbbbbbb'),
    'gg': P(-2, -9,
        'bBBBBBBBb',
        'BBPPBBPPB',
        'BPBBBPBBB',
        'BPBPBPBPB',
        'BBPPBBPPB',
        'bbbbbbbbb'),
    'at': P(-2, -11,
        'bBBBBBBBb',
        'BBBPPPBBB',
        'BBPBBBPBB',
        'BBPBPPPBB',
        'BBPBPPPBB',
        'BBPBBBBBB',
        'BBBPPPBBB',
        'bbbbbbbbb'),
    'bubble': P(-2, -9,
        '.PPPPPPP.',
        'PPPPPPPPP',
        'PPWPPPWPP',
        'PPPPPPPPP',
        'PPPGGGPPP',
        '.PPPPPPp.',
        '.Pp......'),
    'w': P(-2, -9,
        'bBBBBBBBb',
        'BBOBBBOBB',
        'BBOBBBOBB',
        'BBOBOBOBB',
        'BBBOBOBBB',
        'bbbbbbbbb'),
}

FOAM = P(-6, -12,          # blurple foam finger, index finger up; cuff sits on the raised arm
    '..XY.....',
    '..XY.....',
    '..XY.....',
    '..XYYYy..',
    '.XYYYYYy.',
    '.XYYYYYYy',
    '.XYYYYYYy',
    '.XYYYYYy.',
    '..YYYYy..',
    '..yyyy...',
    '..yyyy...')


def mirror_part(part, centre2):
    """Mirror a part about x = centre2/2. Light/shade symbols swap sides."""
    ox, oy, rows = part
    w = max(len(r) for r in rows)
    swap = {'L': 's', 's': 'L', 'K': 'c', 'c': 'K', 'U': 't', 't': 'U', 'I': 'h', 'h': 'I'}
    new_rows = [''.join(swap.get(ch, ch) for ch in reversed(r.ljust(w, '.'))) for r in rows]
    return (centre2 - (ox + w - 1), oy, tuple(new_rows))


# ---------------------------------------------------------------- canvas ops
def stamp(canvas, part, fx, fy, colour_of, outline):
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
                if q not in pts and 0 <= q[0] < FW and 0 <= q[1] < FH:
                    canvas[q[1]][q[0]] = outline
    for (x, y), ch in pts.items():
        if 0 <= x < FW and 0 <= y < FH:
            c = colour_of(ch)
            if c is not None:
                canvas[y][x] = c


# ---------------------------------------------------------------- crowd layout
ROWS = [
    dict(depth=3, size='S', y=2,  pitch=8,  x0=1),
    dict(depth=2, size='S', y=8,  pitch=8,  x0=5),
    dict(depth=1, size='L', y=15, pitch=11, x0=-3),
    dict(depth=0, size='L', y=22, pitch=11, x0=3),
]

L_HEAD_W = {'short': 6, 'bald': 3, 'bangs': 3, 'long': 5, 'bun': 2, 'cap': 4, 'beanie': 3,
            'afro': 2, 'mohawk': 1, 'headset': 2, 'hood': 2, 'shades': 2, 'cat': 1,
            'balding': 2, 'headband': 2}
S_HEAD_W = {'short': 7, 'bald': 3, 'long': 4, 'cap': 3, 'beanie': 3, 'afro': 2, 'bun': 2, 'bangs': 3}
SKIN_W = {'fair': 9, 'tan': 7, 'deep': 4}
HAIR_W = {'black': 6, 'brown': 6, 'blonde': 3, 'ginger': 1, 'grey': 2, 'pink': 1, 'blue': 1}
CLOTH_W = {'rust': 5, 'dbrown': 5, 'plum': 3, 'navy': 1, 'mud': 1, 'grey': 1,
           'r_red': 1, 'r_blurp': 1, 'r_teal': 1, 'r_purple': 1, 'r_gold': 1, 'r_blue': 1}
HAT_W = {'navy': 2, 'grey': 2, 'dbrown': 2, 'rust': 1, 'r_red': 1, 'r_blurp': 1, 'r_teal': 1,
         'r_purple': 1, 'r_gold': 1, 'r_blue': 1}
IDLE_L = {'still': 30, 'hop': 4, 'pump': 3, 'wave': 2, 'cup': 2, 'point': 1, 'raised': 1}
IDLE_S = {'still': 36, 'hop': 4, 'pump': 1, 'cup': 1}
CHEER_L = {'both': 12, 'single': 6, 'cup': 3, 'point': 2, 'hop': 4}
CHEER_S = {'both': 10, 'single': 7, 'cup': 2, 'hop': 9}


class Bag:
    """Shuffle bag: every refill holds each item `weight` times; recent picks are skipped
    so nothing clumps and the whole strip gets an even mix."""
    def __init__(self, rng, weights, avoid):
        self.rng, self.weights, self.avoid = rng, weights, avoid
        self.items, self.recent = [], []

    def draw(self):
        if not self.items:
            self.items = [k for k, w in self.weights.items() for _ in range(w)]
            self.rng.shuffle(self.items)
        pick = None
        for i, it in enumerate(self.items):
            if it not in self.recent[-self.avoid:]:
                pick = self.items.pop(i)
                break
        if pick is None:
            pick = self.items.pop(0)
        self.recent.append(pick)
        return pick


def make_crowd(seed):
    rng = random.Random(seed)
    figures = []
    for ri, row in enumerate(ROWS):
        big = row['size'] == 'L'
        heads = Bag(rng, L_HEAD_W if big else S_HEAD_W, 4)
        skins = Bag(rng, SKIN_W, 1)
        hairs = Bag(rng, HAIR_W, 1)
        cloths = Bag(rng, CLOTH_W, 2)
        hats = Bag(rng, HAT_W, 3)
        x = row['x0']
        while x < FW + 6:
            fx = x + rng.choice([0, 0, 0, 1, -1])
            fig = dict(row=ri, depth=row['depth'], size=row['size'], fx=fx,
                       fy=row['y'] + rng.choice([0, 0, 0, 0, 1]),
                       head=heads.draw(), cloth=cloths.draw(), skin=skins.draw(), hair=hairs.draw(),
                       hat=hats.draw(), acc='blurp', sign=None)
            figures.append(fig)
            x += row['pitch']
    return rng, figures


def assign_animation(rng, figures):
    for ri in range(len(ROWS)):
        row_figs = [f for f in figures if f['row'] == ri]
        big = ROWS[ri]['size'] == 'L'
        idle_bag = Bag(rng, IDLE_L if big else IDLE_S, 1)
        cheer_bag = Bag(rng, CHEER_L if big else CHEER_S, 1)
        for f in row_figs:
            _animate(rng, f, big, idle_bag.draw(), cheer_bag.draw())


def _animate(rng, f, big, idle_kind, ck):
    phase = rng.randrange(3)
    side = rng.choice(['L', 'R'])
    f['idle_kind'], f['cheer_kind'] = idle_kind, ck
    poses, dys, mouths = [], [], []
    for fr in range(N_IDLE):
        k = (fr + phase) % 3
        pose, dy, mouth = None, 0, False
        if idle_kind == 'hop':
            dy = -1 if k == 0 else 0
        elif idle_kind == 'pump':
            pose = ('up' + side) if k == 0 else None
            dy = -1 if k == 0 else 0
            mouth = k == 0
        elif idle_kind == 'wave':
            pose = ('v' + side) if k == 0 else ('up' + side)
        elif idle_kind == 'cup':
            pose = 'cupB'
            mouth = True
        elif idle_kind == 'point':
            pose = 'point' + side
            dy = -1 if k == 2 else 0
        elif idle_kind == 'raised':
            pose = 'up' + side
        poses.append(pose); dys.append(dy); mouths.append(mouth)
    cphase = rng.randrange(2)
    for fr in range(N_CHEER):
        k = (fr + cphase) % 2
        if ck == 'both':
            pose = 'vB' if k == 0 else 'upB'
            dy = -1 if k == 0 else 0
        elif ck == 'single':
            pose = ('v' + side) if k == 0 else ('up' + side)
            dy = -1 if k == 1 else 0
        elif ck == 'cup':
            pose = 'cupB'
            dy = -1 if k == 0 else 0
        elif ck == 'point':
            pose = 'point' + side
            dy = -1 if k == 0 else 0
        else:
            pose = None
            dy = -1 if k == 0 else 0
        poses.append(pose); dys.append(dy); mouths.append(True)
    f['poses'], f['dys'], f['mouths'] = poses, dys, mouths


def place_props(figures, plan):
    """plan: list of (row, approx x, prop, idle motion, colour)"""
    for row, ax, name, motion, colour in plan:
        cands = [f for f in figures if f['row'] == row]
        f = min(cands, key=lambda g: abs(g['fx'] - ax))
        f['sign'] = name
        if name == 'foam':
            f['acc'] = colour
            f['poses'] = ['foamL'] * NF
            f['dys'] = [0, -1, 0, -1, 0]
        else:
            f['poses'] = ['holdB'] * NF
            f['dys'] = {'bob': [0, -1, 0, -1, 0], 'bob2': [-1, 0, 0, 0, -1]}.get(motion, [0, 0, 0, -1, 0])
        f['mouths'] = [False, False, False, True, True]
        if f['head'] in ('cap', 'beanie', 'bun', 'mohawk', 'cat', 'afro', 'hood'):
            f['head'] = 'short'


# ---------------------------------------------------------------- render
def figure_colour(f, depth):
    d = DEPTHS[depth]
    mats = {
        'skin': SKINS[f['skin']], 'hair': HAIRS[f['hair']], 'cloth': CLOTH[f['cloth']],
        'hat': CLOTH[f['hat']], 'acc': FOAM_RAMPS[f['acc']], 'metal': METAL,
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


def rc(ramp_base, off, shift):
    ramp, base = ramp_base
    i = base + off + shift
    return ramp[max(0, min(len(ramp) - 1, i))]


def draw_figure(canvas, f, fr):
    depth = f['depth']
    d = DEPTHS[depth]
    big = f['size'] == 'L'
    out = d['outline']
    fx, fy = f['fx'], f['fy'] + f['dys'][fr]
    col = figure_colour(f, depth)
    centre2 = 5 if big else 4
    torso = L_TORSO if big else S_TORSO
    heads = L_HEADS if big else S_HEADS
    arms = L_ARMS if big else S_ARMS
    pose = f['poses'][fr]

    stamp(canvas, torso, fx, fy, col, out)

    parts = []
    if pose is not None:
        kind, side = pose[:-1], pose[-1]
        if not big and kind == 'point':
            kind = 'v'
        base = arms[kind]
        mc = 4 if kind == 'hold' else centre2
        if side in 'LB':
            parts.append(base)
        if side in 'RB':
            parts.append(mirror_part(base, mc))
    behind_head = pose is not None and pose[:-1] in ('up', 'v', 'point', 'hold', 'foam')
    if behind_head:
        for p in parts:
            stamp(canvas, p, fx, fy, col, out)
    stamp(canvas, heads[f['head']], fx, fy, col, out)
    if f['mouths'][fr] and d['mouth']:
        mx, my = L_MOUTH if big else S_MOUTH
        for i in range(2 if big else 1):
            x, y = fx + mx + i, fy + my
            if 0 <= x < FW and 0 <= y < FH:
                canvas[y][x] = col('m')
    if not behind_head:
        for p in parts:
            stamp(canvas, p, fx, fy, col, out)

    if f['sign'] == 'foam':
        stamp(canvas, FOAM, fx, fy, col, out)
    elif f['sign']:
        pal = PROP_COL[min(depth, 1)]
        part = SIGNS[f['sign']]
        stamp(canvas, part, fx, fy, lambda ch: pal[ch], out)
        ox, oy, rows = part
        by = fy + oy + len(rows) - 1
        for hx in (fx + ox, fx + ox + len(rows[0]) - 1):
            for y in (by, by + 1):
                if 0 <= hx < FW and 0 <= y < FH:
                    canvas[y][hx] = col('S')


def flashes(canvas, rng, n, avoid):
    placed = tries = 0
    while placed < n and tries < 500:
        tries += 1
        x = rng.randrange(6, FW - 6)
        y = rng.randrange(3, 30)
        if any(a0 <= x <= a1 and b0 <= y <= b1 for a0, b0, a1, b1 in avoid):
            continue
        canvas[y][x] = WHITE
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            canvas[y + dy][x + dx] = ICE
        placed += 1


DEFAULT_PROPS = [
    (3, 48, 'heart', 'bob', None),
    (2, 150, 'gg', 'bob2', None),
    (3, 208, 'foam', True, 'blurp'),
    (3, 452, 'bubble', 'bob', None),
    (2, 520, 'at', 'still', None),
    (3, 598, 'w', 'bob2', None),
]


def render(seed=7, props=DEFAULT_PROPS, flash_seed=11):
    rng, figures = make_crowd(seed)
    assign_animation(rng, figures)
    if props:
        place_props(figures, props)
    frames = []
    frng = random.Random(flash_seed)
    for fr in range(NF):
        cv = [[None] * FW for _ in range(FH)]
        for ri in range(len(ROWS)):
            row_figs = [f for f in figures if f['row'] == ri]
            row_figs.sort(key=lambda f: (f['poses'][fr] is not None, f['sign'] is not None))
            for f in row_figs:
                draw_figure(cv, f, fr)
        if fr >= N_IDLE:
            flashes(cv, frng, 5, avoid=[(245, 0, 395, 40)])
        fade_bottom(cv)
        frames.append(cv)
    return figures, frames


# one DB32 step darker; used to sink the lowest rows (only visible beside the ring posts)
DARKER = {
    PEACH: TAN, TAN: RUST, RUST: DBRN, DBRN: PLUM, PLUM: NAVY, NAVY: K0, K0: K0,
    ORNG: RUST, GOLD: MUD, MUD: SLATE, SLATE: NAVY, GREY1: GREY3, GREY2: GREY4, GREY3: GREY4,
    GREY4: SLATE, RED: DBRN, PINK: RED, PURP: PLUM, MAUVE: PURP, BLURP: INDIGO, SKY: BLURP,
    INDIGO: NAVY, STEEL: INDIGO, CYAN: STEEL, TEAL: OLIVE, OLIVE: SLATE, ICE: GREY1, WHITE: ICE,
    YEL: TAN, GRN: OLIVE, MOSS: MUD,
}


def fade_bottom(cv):
    # anything still empty in the band hidden behind the rope gets sealed dark
    for y in range(32, FH):
        for x in range(FW):
            if cv[y][x] is None:
                cv[y][x] = K0
    for y, steps in ((36, 1), (37, 1), (38, 2), (39, 2)):
        row = cv[y]
        for x in range(FW):
            c = row[x]
            if c is None:
                continue
            for _ in range(steps):
                c = DARKER[c]
            row[x] = c


def to_rgba(cv):
    return [[(c[0], c[1], c[2], 255) if c is not None else (0, 0, 0, 0) for c in row] for row in cv]


def write_strip(frames, out):
    strip = [[None] * (FW * len(frames)) for _ in range(FH)]
    for i, fr in enumerate(frames):
        for y in range(FH):
            strip[y][i * FW:(i + 1) * FW] = fr[y]
    write_png(out, FW * len(frames), FH, to_rgba(strip))


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'crowd_v2_draft.png')
    figures, frames = render()
    write_strip(frames, out)
    print('figures', len(figures), 'wrote', out)
