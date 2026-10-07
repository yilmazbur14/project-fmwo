"""STAGING STUDY (2026-09-28): make room between the puppet master and his puppets.

The user: "make jordan smaller so that the puppets appear below him, creating some distance.
alternatively we can zoom out the camera a little too". Two options, both attacks, 1920x1080 mocks:

  A  only Jordan drops to 2 px a texel (his 320x224 frame is 640x448 px); the world - floor, maze,
     kegs, puppets, player - stays at 3x, so its numbers stay in today's screen px.
  B  the whole view goes to 2 px a texel: a Camera2D zoom of 2/3, so the world keeps its 3x sprites
     and 96x60 blocks but the view shows 2880x1620 world px. The camera sits so that Jordan keeps the
     finale's world point (960, 600): world = screen * 1.5 + (-480, -6), view centre (960, 804).

Reads the shipped art (the god's puppeteer strips in approval/, the puppet twins in Assets/..../
Puppets/, their measured back hooks) and writes only into this folder. A bare run writes nothing:

    python jp_staging.py            # print this
    python jp_staging.py --write    # the mocks, the notes overlays, the zoom crop and staging.json
"""
import json
import math
import os
import random
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
PUPDIR = os.path.dirname(HERE)
sys.path.insert(0, PUPDIR)
import jp_rig as R  # noqa: E402,F401
import jp_strings as S  # noqa: E402
import jg_base as B  # noqa: E402
import jg_god as G  # noqa: E402
import jg_lord as L  # noqa: E402
import jg_runes as RU  # noqa: E402
import jg_void as V  # noqa: E402
from PIL import Image, ImageChops, ImageDraw  # noqa: E402

ROOT = B.ROOT
APPROVAL = os.path.join(PUPDIR, 'approval')
PUPPET_DIR = os.path.join(ROOT, 'Assets', 'Characters', 'Jordan', 'Puppets')
SCREEN = (1920, 1080)
FLOOR = (105, 105, 1815, 975)                         # today's walkable floor, world = screen px at 3x
HUD = [(720, 33, 480, 148), (10, 842, 406, 229), (1371, 946, 537, 126)]   # CarterArtLayout.HUD_KEEP_OUT
HUD_CLEAR = 12
TAKE = 'blue'
GOD_SCALE = 2
GOD_POINT = (960, 404)                                # screen px, both options: his wing tips clear the top

# the twins' idle frame 0, its feet texel and its measured back hook (Scripts/JordanPuppetHooks.gd)
PUPPETS = {
    'greyson': ('greyson/greyson_idle.png', (112, 112), (56, 111), (57, 57)),
    'matt': ('matt/matt_idle.png', (96, 96), (48, 95), (48, 58)),
    'burak': ('burak/burak_idle.png', (96, 96), (48, 95), (48, 58)),
    'danny': ('danny/danny_sumo_idle.png', (176, 144), (88, 143), (88, 60)),
}
PAIRS = {'greyson': (0, 1), 'matt': (2, 3), 'burak': (2, 3), 'danny': (2, 3)}
HAND = {'greyson': 'left', 'matt': 'right', 'burak': 'left', 'danny': 'right'}
DIGITS = ('index', 'middle', 'ring', 'little', 'thumb')

_cache = {}


def cached(key, fn):
    if key not in _cache:
        _cache[key] = fn()
    return _cache[key]


# ------------------------------------------------------------------ assets (read only)

def god_frame(anim='control', i=1):
    stem = 'jordan_god_puppeteer_' + anim if anim != 'hit' else 'jordan_god_hit'

    def make():
        im = Image.open(os.path.join(APPROVAL, stem + '.png')).convert('RGBA').crop((i * 320, 0, i * 320 + 320, 224))
        au = Image.open(os.path.join(APPROVAL, stem + '_aura.png')).convert('RGBA').crop((i * 336, 0, i * 336 + 336, 232))
        with open(os.path.join(APPROVAL, 'jordan_puppeteer_fingertips.json')) as f:
            tab = json.load(f)
        key = 'puppeteer_' + anim if anim != 'hit' else 'jordan_god_hit'
        tips = tab['anims'][key]['tips'][i]
        return im, au, tips
    return cached(('god', anim, i), make)


def puppet(name):
    def make():
        path, frame, feet, hook = PUPPETS[name]
        im = Image.open(os.path.join(PUPPET_DIR, path)).convert('RGBA').crop((0, 0, frame[0], frame[1]))
        return im, feet, hook
    return cached(('pup', name), make)


def player_up():
    return cached('player', lambda: Image.open(B.PLAYER_PNG).convert('RGBA').crop((0, 32, 32, 64)))


def keg():
    return cached('keg', lambda: Image.open(os.path.join(ROOT, 'Assets', 'Characters', 'BurakBoss', 'FX',
                                                           'burak_barrel.png')).convert('RGBA').crop((0, 0, 48, 56)))


def wall_block():
    return cached('wall', lambda: Image.open(os.path.join(PUPDIR, 'sketch_void_wall', 'void_wall_sketch.png'))
                  .convert('RGBA').crop((4 * 32, 0, 5 * 32, 36)))


def void(scale):
    """The void filling the screen at `scale` px a texel: the shipped 640x360 at 3x, or the same
    recipe re-run at 960x540 for 2x (its glow on his core)."""
    def make():
        if scale == 3:
            return V.backdrop()
        keep = (V.W, V.H, V.GLOW)
        try:
            V.W, V.H = 960, 540
            V.GLOW = (480, (GOD_POINT[1] + (124 - 223) * 2) // 2)
            return V.backdrop()
        finally:
            V.W, V.H, V.GLOW = keep
    return cached(('void', scale), make)


# ------------------------------------------------------------------ jordan's numbers (screen px at 2x)

def god_mask():
    """His opaque texels over every shipped frame of every anim, as a screen-px mask at 2x."""
    def make():
        m = Image.new('L', SCREEN, 0)
        tl = god_tl()
        for stem, n in (('jordan_god_puppeteer_control', 6), ('jordan_god_puppeteer_summon_both', 7),
                        ('jordan_god_puppeteer_summon_left', 7), ('jordan_god_puppeteer_summon_right', 7),
                        ('jordan_god_puppeteer_yank_right', 4), ('jordan_god_puppeteer_yank_left', 4),
                        ('jordan_god_hit', 2)):
            strip = Image.open(os.path.join(APPROVAL, stem + '.png')).convert('RGBA')
            for i in range(n):
                a = strip.crop((i * 320, 0, i * 320 + 320, 224)).getchannel('A')
                a = a.resize((640, 448), Image.NEAREST)
                m.paste(255, tl, a)
        return m
    return cached('godmask', make)


def god_tl(g=GOD_POINT, s=GOD_SCALE):
    return (g[0] - 160 * s, g[1] - 223 * s)


def texel_box(bbox, g=GOD_POINT, s=GOD_SCALE):
    """A frame-texel box (x0, y0, x1, y1 inclusive) in screen px (x0, y0, x1, y1 exclusive)."""
    tl = god_tl(g, s)
    return (tl[0] + bbox[0] * s, tl[1] + bbox[1] * s, tl[0] + (bbox[2] + 1) * s, tl[1] + (bbox[3] + 1) * s)


def jordan_numbers():
    mask = god_mask()
    box = mask.getbbox()
    face = L.face_mask(False)
    fx = [p[0] for p in face]
    fy = [p[1] for p in face]
    # the mask moves with the bob (0..3 rows up) and the hit's recoil: take its full sweep
    mask_box = texel_box((min(fx), min(fy) - 3, max(fx), max(fy)))
    cx, cy = L.CORE
    core_box = texel_box((int(cx - 7.5), int(cy - 7.5) - 3, int(cx + 7.5), int(cy + 7.5)))
    with open(os.path.join(APPROVAL, 'jordan_puppeteer_fingertips.json')) as f:
        tab = json.load(f)
    ys_work, ys_all = [], []
    for key, a in tab['anims'].items():
        for pose, t in zip(a['poses'], a['tips']):
            ys = [p[1] for s_ in ('left', 'right') for p in t[s_]]
            ys_all += ys
            if pose not in ('dip', 'grip', 'yank'):
                ys_work += ys
    tip_y = lambda r: GOD_POINT[1] + (r + 0.5 - 223) * GOD_SCALE  # noqa: E731
    return {
        'god_point': list(GOD_POINT), 'scale': GOD_SCALE,
        'box': list(box),
        'mask_box': [int(v) for v in mask_box],
        'core_box': [int(v) for v in core_box],
        'hand_tip_y_working': [tip_y(min(ys_work)), tip_y(max(ys_work))],
        'hand_tip_y_any': [tip_y(min(ys_all)), tip_y(max(ys_all))],
        'lowest_body_y': box[3],
    }


# ------------------------------------------------------------------ the canvas

class Canvas:
    def __init__(self, world_scale):
        self.s = world_scale
        self.im = Image.new('RGBA', SCREEN, (0, 0, 0, 255))

    def blit(self, img, scale, tl):
        big = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
        x, y = int(round(tl[0])), int(round(tl[1]))
        x0, y0 = max(0, -x), max(0, -y)
        if x0 >= big.width or y0 >= big.height:
            return
        self.im.alpha_composite(big.crop((x0, y0, big.width, big.height)), (x + x0, y + y0))

    def add(self, img, scale, tl):
        big = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
        layer = Image.new('RGB', SCREEN, (0, 0, 0))
        layer.paste(big.convert('RGB'), (int(round(tl[0])), int(round(tl[1]))), big)
        self.im = ImageChops.add(self.im.convert('RGB'), layer).convert('RGBA')

    def strings(self, strings_px, knots_px, grid):
        """Blue strings 1 texel wide on a `grid`-px texel grid: glow added, core opaque."""
        T = S.TAKES[TAKE]
        pts = [[(x / grid, y / grid) for x, y in s] for s in strings_px]
        core, glow = S.string_texels(pts)
        knots = {(int(x // grid), int(y // grid)) for x, y in knots_px}
        kglow = {(x + dx, y + dy) for (x, y) in knots for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
        add = Image.new('RGB', SCREEN, (0, 0, 0))
        d = ImageDraw.Draw(add)
        for (x, y) in glow | kglow:
            c = T['knot'] if (x, y) in kglow else T['glow']
            d.rectangle((x * grid, y * grid, x * grid + grid - 1, y * grid + grid - 1), fill=c[:3])
        self.im = ImageChops.add(self.im.convert('RGB'), add).convert('RGBA')
        d = ImageDraw.Draw(self.im)
        for (x, y) in core:
            d.rectangle((x * grid, y * grid, x * grid + grid - 1, y * grid + grid - 1), fill=T['core'])
        for (x, y) in knots:
            d.rectangle((x * grid, y * grid, x * grid + grid - 1, y * grid + grid - 1), fill=T['hot'])


def feet_tl(feet_px, feet_tex, s):
    """Top-left of a frame whose feet texel stands on feet_px (its left edge on x, bottom edge on y)."""
    return (feet_px[0] - feet_tex[0] * s, feet_px[1] - (feet_tex[1] + 1) * s)


def hook_px(name, feet_px, s):
    img, feet, hook = puppet(name)
    tl = feet_tl(feet_px, feet, s)
    return (tl[0] + (hook[0] + 0.5) * s, tl[1] + (hook[1] + 0.5) * s)


def puppet_box(name, feet_px, s):
    img, feet, hook = puppet(name)
    tl = feet_tl(feet_px, feet, s)
    bb = img.getbbox()
    return (tl[0] + bb[0] * s, tl[1] + bb[1] * s, tl[0] + bb[2] * s, tl[1] + bb[3] * s)


def _px(im):
    flat = getattr(im, 'get_flattened_data', None)
    return flat() if flat else im.getdata()


def puppet_overlap(name, feet_px, s):
    """Texels of the puppet over Jordan's silhouette (any shipped frame), and over his mask/core."""
    img, feet, hook = puppet(name)
    tl = feet_tl(feet_px, feet, s)
    big = img.getchannel('A').resize((img.width * s, img.height * s), Image.NEAREST)
    layer = Image.new('L', SCREEN, 0)
    layer.paste(big, (int(tl[0]), int(tl[1])))
    both = ImageChops.multiply(layer, god_mask())
    n = sum(1 for v in _px(both) if v) // (s * s)
    j = jordan_numbers()
    face = 0
    for bx in (j['mask_box'], j['core_box']):
        crop = layer.crop(tuple(bx))
        face += sum(1 for v in _px(crop) if v) // (s * s)
    return n, face


# ------------------------------------------------------------------ the maze route

def route(cols, rows, goal, keep_clear=(), steps=18, seed=0, budget=400000, no_route=()):
    """A random self-avoiding corridor of exactly `steps` unit steps from (0, 0) to `goal`, inside
    cols x rows (inclusive ranges), under the maze's rules: two cells of it that are not neighbours
    along it are never side by side, nor corner to corner except across one of its own turns; the goal
    only at the end; nothing of it 8-adjacent to a keep_clear cell."""
    rnd = random.Random(seed)
    goal = tuple(goal)
    path = [(0, 0)]
    seen = {(0, 0)}
    count = [0]
    moves = [(0, 1), (1, 0), (-1, 0), (0, -1)]

    def ok(n):
        if not (cols[0] <= n[0] <= cols[1] and rows[0] <= n[1] <= rows[1]) or n in seen or n in no_route:
            return False
        for kc in keep_clear:
            if abs(kc[0] - n[0]) <= 1 and abs(kc[1] - n[1]) <= 1:
                return False
        k = len(path)
        for i, p in enumerate(path[:-1]):
            dx, dy = abs(p[0] - n[0]), abs(p[1] - n[1])
            if dx + dy == 1:
                return False
            if dx == 1 and dy == 1 and i < k - 2:
                return False
        return True

    def go():
        count[0] += 1
        if count[0] > budget:
            return False
        cur = path[-1]
        left = steps - (len(path) - 1)
        if left == 0:
            return cur == goal
        order = moves[:]
        rnd.shuffle(order)
        for m in order:
            n = (cur[0] + m[0], cur[1] + m[1])
            if n == goal and left != 1:
                continue
            d = abs(goal[0] - n[0]) + abs(goal[1] - n[1])
            if d > left - 1 or (left - 1 - d) % 2:
                continue
            if not ok(n):
                continue
            path.append(n)
            seen.add(n)
            if go():
                return True
            path.pop()
            seen.discard(n)
        return False

    return list(path) if go() else None


def walls_for(path, greyson_cell, back_glass):
    ps = set(path)
    out = set()
    for (c, r) in path:
        for dc in (-1, 0, 1):
            for dr in (-1, 0, 1):
                q = (c + dc, r + dr)
                if q not in ps and q != tuple(greyson_cell) and q != tuple(back_glass):
                    out.add(q)
    return out


# ------------------------------------------------------------------ the two layouts (SCREEN px)

LAYOUTS = {
    'A': dict(
        label='Option A: Jordan at 2x, the world at 3x',
        world=3, to_world=(1.0, 0, 0),                          # world = screen * k + (dx, dy)
        floor=FLOOR,
        origin=(960, 896), block=(96, 60), rows=(0, 5), cols=(-4, 4),
        goal=(-3, 5), greyson_cell=(-3, 6), back_glass=(0, -1),
        no_route=[(3, 0), (4, 0)],                               # their walls would sit under the bottom-right HUD
        matt_feet=(1248, 536), matt_cells=[(2, 6), (3, 6), (4, 6)],
        centre=(960, 770), kegs={'n': (960, 580), 'e': (1520, 770), 's': (960, 960), 'w': (400, 770)},
        stations={'n': (960, 650), 'e': (1430, 770), 's': (960, 880), 'w': (490, 770)},
        slam=(150, 80), burak=(520, 560), danny=(1560, 590), player_kegs=(960, 770),
        route_seed=7,
    ),
    'B': dict(
        label='Option B: the whole view at 2x (camera zoom 2/3)',
        world=2, to_world=(1.5, -480, -6),
        floor=(70, 70, 1850, 1010),                              # in screen px; world (-375, 99)-(2295, 1509)
        origin=(960, 944), block=(64, 40), rows=(0, 8), cols=(-5, 4),
        goal=(-2, 8), greyson_cell=(-2, 9), back_glass=(0, -1),
        matt_feet=(1216, 584), matt_cells=[(3, 9), (4, 9), (5, 9)],
        centre=(960, 780), kegs={'n': (960, 627), 'e': (1333, 780), 's': (960, 947), 'w': (587, 780)},
        stations={'n': (960, 674), 'e': (1273, 780), 's': (960, 894), 'w': (647, 780)},
        slam=(100, 53), burak=(560, 640), danny=(1460, 640), player_kegs=(960, 780),
        route_seed=56,
    ),
}


def cell_px(lay, c, r):
    ox, oy = lay['origin']
    bw, bh = lay['block']
    return (ox + bw * c, oy - bh * r)


def to_world(lay, p):
    k, dx, dy = lay['to_world']
    return (p[0] * k + dx, p[1] * k + dy)


def lay_route(lay):
    for seed in range(lay['route_seed'], lay['route_seed'] + 200):
        p = route(lay['cols'], lay['rows'], lay['goal'], keep_clear=lay['matt_cells'], seed=seed,
                  no_route=set(map(tuple, lay.get('no_route', ()))))
        if p:
            return p, seed
    return None, None


def tips_px(tips, side, idx):
    tl = god_tl()
    return [(tl[0] + (tips[side][k][0] + 0.5) * GOD_SCALE, tl[1] + (tips[side][k][1] + 0.5) * GOD_SCALE) for k in idx]


def compose(opt, attack, notes=False, god=('control', 1), runes=5):
    lay = LAYOUTS[opt]
    s = lay['world']
    cv = Canvas(s)
    cv.blit(void(s), s, (0, 0))
    im, au, tips = god_frame(*god)
    tl = god_tl()
    core = (tl[0] + (L.CORE[0] + 0.5) * GOD_SCALE, tl[1] + (L.CORE[1] + 0.5) * GOD_SCALE)
    cv.blit(RU.frame_image(runes), GOD_SCALE, (core[0] - 96 * GOD_SCALE, core[1] - 96 * GOD_SCALE))
    cv.blit(im, GOD_SCALE, tl)
    cv.add(au, GOD_SCALE, (tl[0] - G.AURA_PAD * GOD_SCALE, tl[1]))
    info = {'puppets': {}}
    if attack == 1:
        pups = [('greyson', cell_px(lay, *lay['greyson_cell'])), ('matt', lay['matt_feet'])]
    else:
        pups = [('burak', lay['burak']), ('danny', lay['danny'])]
    # strings: two per puppet, from its hand's pair to its back hook, drawn behind the puppet
    strings, knots = [], []
    for name, feet in pups:
        hk = hook_px(name, feet, s)
        tp = tips_px(tips, HAND[name], PAIRS[name])
        lens = []
        for j, p0 in enumerate(tp):
            end = (hk[0] + (j - 0.5) * 2 * s, hk[1])
            strings.append(S.curve(p0, end, 0.7))
            knots.append(p0)
            lens.append(math.hypot(end[0] - p0[0], end[1] - p0[1]))
        n, face = puppet_overlap(name, feet, s)
        info['puppets'][name] = {
            'feet': list(feet), 'hook': [round(hk[0], 1), round(hk[1], 1)],
            'tips': [[round(v, 1) for v in p] for p in tp], 'string_px': [round(v) for v in lens],
            'over_jordan_texels': n, 'over_mask_core': face, 'box': [round(v) for v in puppet_box(name, feet, s)]}
    cv.strings(strings, knots, s)
    # the floor's things, back to front
    items = []
    if attack == 1:
        path, seed = lay_route(lay)
        info['route'] = path
        info['route_seed'] = seed
        walls = walls_for(path, lay['greyson_cell'], lay['back_glass'])
        info['walls'] = sorted(walls)
        for (c, r) in walls:
            x, y = cell_px(lay, c, r)
            items.append((y, 'wall', (x, y)))
        for (c, r) in path:
            x, y = cell_px(lay, c, r)
            items.append((y - 0.5, 'tile', (x, y, (c, r) == tuple(lay['goal']))))
        gx, gy = cell_px(lay, *lay['back_glass'])
        items.append((gy - 0.5, 'glass', (gx, gy, False)))
        items.append((cell_px(lay, 0, 0)[1] + 0.1, 'player', cell_px(lay, 0, 0)))
    else:
        for k, p in lay['kegs'].items():
            items.append((p[1], 'keg', p))
        items.append((lay['player_kegs'][1] + 0.1, 'player', lay['player_kegs']))
    for name, feet in pups:
        items.append((feet[1] + 0.2, 'puppet', (name, feet)))
    items.sort(key=lambda it: it[0])
    bw, bh = lay['block']
    for y, kind, data in items:
        if kind == 'wall':
            x, yy = data
            cv.blit(wall_block(), s, (x - 16 * s, yy + 10 * s - 36 * s))
        elif kind in ('tile', 'glass'):
            x, yy, goal = data
            d = ImageDraw.Draw(cv.im)
            if goal:
                col = S.TAKES[TAKE]['hot']
            elif kind == 'tile':
                col = (58, 110, 150, 255)
            else:
                col = (170, 200, 220, 255)
            d.rectangle((x - bw // 2, yy - bh // 2, x + bw // 2 - 1, yy + bh // 2 - 1), outline=col, width=s)
        elif kind == 'keg':
            x, yy = data
            cv.blit(keg(), s, (x - 24 * s, yy - 56 * s))
        elif kind == 'player':
            x, yy = data
            cv.blit(player_up(), s, (x - 16 * s, yy - 29 * s))
        elif kind == 'puppet':
            name, feet = data
            img, f, h = puppet(name)
            cv.blit(img, s, feet_tl(feet, f, s))
    if attack == 2:
        info['kegs'] = lay['kegs']
    if notes:
        annotate(cv, lay, attack, info)
    return cv.im, info


def annotate(cv, lay, attack, info):
    d = ImageDraw.Draw(cv.im)
    j = jordan_numbers()
    yel, mag, cya, grn, red, wht = (255, 220, 60), (255, 80, 220), (80, 230, 255), (90, 220, 120), (255, 70, 70), \
        (235, 235, 245)

    def box(b, col, w=2):
        d.rectangle((b[0], b[1], b[2] - 1, b[3] - 1), outline=col, width=w)

    def text(xy, s_, col=wht):
        x, y = xy
        d.rectangle((x - 2, y - 1, x + 6 * len(s_) + 2, y + 11), fill=(0, 0, 0))
        d.text((x, y), s_, fill=col)

    box(j['box'], yel)
    text((j['box'][0] + 4, j['box'][3] + 4), 'Jordan 2x: box %s' % (j['box'],), yel)
    box(j['mask_box'], mag)
    box(j['core_box'], mag)
    text((j['mask_box'][2] + 6, j['mask_box'][1]), 'mask %s' % (j['mask_box'],), mag)
    text((j['core_box'][2] + 6, j['core_box'][1] + 14), 'core %s' % (j['core_box'],), mag)
    for yv in j['hand_tip_y_working']:
        d.line((620, yv, 1300, yv), fill=cya, width=1)
    text((1300, j['hand_tip_y_working'][0] - 6), 'working claw tips y %d-%d' % tuple(j['hand_tip_y_working']), cya)
    fl = lay['floor']
    box(fl, grn)
    text((fl[0] + 4, fl[3] - 16), 'floor %s (screen px)' % (tuple(fl),), grn)
    for h in HUD:
        box((h[0], h[1], h[0] + h[2], h[1] + h[3]), red)
    text((HUD[1][0] + 4, HUD[1][1] + 4), 'HUD', red)
    text((HUD[2][0] + 4, HUD[2][1] + 4), 'HUD', red)
    text((HUD[0][0] + 4, HUD[0][1] + HUD[0][3] - 14), 'boss bar (fades during attacks)', red)
    for name, p in info['puppets'].items():
        hk = p['hook']
        d.ellipse((hk[0] - 5, hk[1] - 5, hk[0] + 5, hk[1] + 5), outline=cya, width=2)
        fx, fy = p['feet']
        d.line((fx - 8, fy, fx + 8, fy), fill=yel, width=2)
        text((p['box'][0], p['box'][3] + 4), '%s feet (%d,%d) hook (%d,%d) strings %s px' % (
            name, fx, fy, hk[0], hk[1], '/'.join(str(v) for v in p['string_px'])), cya)
    bw, bh = lay['block']
    if attack == 1:
        c0, c1 = lay['cols']
        r0, r1 = lay['rows']
        x0 = cell_px(lay, c0, 0)[0] - bw // 2
        x1 = cell_px(lay, c1, 0)[0] + bw // 2
        y0 = cell_px(lay, 0, r1)[1] - bh // 2
        y1 = cell_px(lay, 0, r0)[1] + bh // 2
        box((x0, y0, x1, y1), (150, 150, 170), 1)
        text((x1 + 6, y0), 'route band: cols %d..%d x rows %d..%d (%d rows), block %dx%d px' % (
            c0, c1, r0, r1, r1 - r0 + 1, bw, bh), wht)
        gx, gy = cell_px(lay, *lay['goal'])
        text((gx + bw // 2 + 4, gy - 6), 'goal %s' % (tuple(lay['goal']),), S.TAKES[TAKE]['hot'][:3])
        ox, oy = lay['origin']
        text((ox + bw // 2 + 4, oy - 6), 'start (0,0) = origin (%d,%d)' % (ox, oy), wht)
    else:
        cx, cy = lay['centre']
        rx, ry = lay['slam']
        d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), outline=red, width=2)
        text((cx + rx + 6, cy - 6), 'slam zone %dx%d' % (rx, ry), red)
        for k, (x, y) in lay['kegs'].items():
            text((x + 24 * lay['world'] + 4, y - 20), 'keg %s (%d,%d)' % (k.upper(), x, y), yel)


# ------------------------------------------------------------------ a non-integer zoom

def zoom_crop():
    """What a 0.85 camera zoom does to 3x art: 2.55 px a texel, so texels come out 2 or 3 px wide
    in a beat pattern. Jordan's mask and the player at 3x, 2x and 2.55x, then the 2.55x one blown
    up 4x so the uneven columns show."""
    im, au, tips = god_frame('control', 1)
    face = im.crop((126, 60, 194, 112))
    pc = player_up().crop((6, 2, 26, 31))
    tiles = []
    for label, k in (('3x (today)', 3.0), ('2x (option B)', 2.0), ('0.85 zoom = 2.55x', 2.55)):
        f = face.resize((int(round(face.width * k)), int(round(face.height * k))), Image.NEAREST)
        p = pc.resize((int(round(pc.width * k)), int(round(pc.height * k))), Image.NEAREST)
        t = Image.new('RGBA', (f.width + p.width + 24, max(f.height, p.height) + 20), (14, 10, 24, 255))
        t.alpha_composite(f, (4, 16))
        t.alpha_composite(p, (f.width + 16, 16))
        ImageDraw.Draw(t).text((4, 2), label, fill=(230, 230, 240, 255))
        tiles.append(t)
    blow = tiles[2].crop((4 + 60, 16 + 40, 4 + 150, 16 + 100)).resize((360, 240), Image.NEAREST)
    widths = [int(round((i + 1) * 2.55)) - int(round(i * 2.55)) for i in range(face.width)]
    W_ = max(sum(t.width for t in tiles) + 4 * 12, blow.width + 420)
    H_ = max(t.height for t in tiles) + blow.height + 60
    sheet = Image.new('RGBA', (W_, H_), (8, 6, 14, 255))
    x = 12
    for t in tiles:
        sheet.alpha_composite(t, (x, 12))
        x += t.width + 12
    y2 = max(t.height for t in tiles) + 28
    sheet.alpha_composite(blow, (12, y2))
    d = ImageDraw.Draw(sheet)
    lines = ['the 2.55x crop blown up 4x: every texel should be one even square,',
             'but at 2.55 px they come out %s px wide' % ','.join(str(w) for w in widths[:12]),
             '(3, 2, 3, 2, 3...): keylines thicken and thin from texel to texel,',
             'the eyes and claws change shape, and the pattern crawls as anything moves.',
             'Integer zooms only: 3x today, or 2x (a 2/3 camera zoom).']
    for i, ln in enumerate(lines):
        d.text((blow.width + 28, y2 + 14 * i), ln, fill=(230, 230, 240, 255))
    return sheet, widths


def install_guard():
    here = os.path.normcase(os.path.realpath(HERE))

    def inside(p):
        rp = os.path.normcase(os.path.realpath(os.fspath(p)))
        return rp == here or rp.startswith(here + os.sep)

    def hook(event, args):
        if event == 'open':
            path, mode, flags = args
            if path is None or isinstance(path, int):
                return
            writing = (mode is not None and any(c in str(mode) for c in 'wax+')) or \
                      (mode is None and isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT))
            if writing and not inside(path):
                raise PermissionError('guard: staging writes only into %s, not %s' % (HERE, path))
        elif event in ('os.remove', 'os.unlink', 'os.rename', 'os.replace', 'os.rmdir', 'os.mkdir',
                       'shutil.copyfile', 'shutil.move', 'shutil.rmtree'):
            for a in args:
                if isinstance(a, (str, bytes, os.PathLike)) and not inside(a):
                    raise PermissionError('guard: refusing %s on %s' % (event, a))
        elif event == 'subprocess.Popen':
            raise PermissionError('guard: staging launches nothing')

    sys.addaudithook(hook)


def main(argv):
    if not argv or argv[0] != '--write':
        print(__doc__)
        return 2
    install_guard()
    table = {'jordan': jordan_numbers(), 'hud_keep_out': HUD, 'hud_clearance': HUD_CLEAR, 'options': {}}
    for opt in ('A', 'B'):
        lay = LAYOUTS[opt]
        rec = {'label': lay['label'], 'world_px_per_texel_on_screen': lay['world'],
               'screen_to_world': 'world = screen * %s + (%d, %d)' % lay['to_world'],
               'floor_screen': lay['floor']}
        for atk in (1, 2):
            im, info = compose(opt, atk)
            im.save(os.path.join(HERE, 'staging_%s%d.png' % (opt, atk)))
            im2, _ = compose(opt, atk, notes=True)
            im2.save(os.path.join(HERE, 'staging_%s%d_notes.png' % (opt, atk)))
            rec['attack%d' % atk] = info
        rec['grid'] = {'origin': lay['origin'], 'block': lay['block'], 'rows': lay['rows'], 'cols': lay['cols'],
                       'goal': lay['goal'], 'greyson_cell': lay['greyson_cell'], 'back_glass': lay['back_glass'],
                       'matt_feet': lay['matt_feet'], 'matt_cells': lay['matt_cells']}
        rec['kegs'] = {'centre': lay['centre'], 'kegs': lay['kegs'], 'stations': lay['stations'],
                       'slam_radii': lay['slam'], 'burak_feet': lay['burak'], 'danny_rest': lay['danny']}
        table['options'][opt] = rec
        print('wrote staging_%s1.png, staging_%s2.png and their _notes' % (opt, opt))
    z, widths = zoom_crop()
    z.save(os.path.join(HERE, 'staging_zoom_085.png'))
    table['zoom_085_texel_widths'] = widths[:20]
    with open(os.path.join(HERE, 'staging.json'), 'w') as f:
        json.dump(table, f, indent=1, default=list)
    print('wrote staging_zoom_085.png and staging.json')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
