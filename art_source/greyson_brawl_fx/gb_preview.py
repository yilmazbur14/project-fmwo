"""The first-pass approval sheets for Greyson's FINAL BRAWL effects (zoom 1.0), composited the way the
scene draws them. The brawl as PLAN_BRAWL.md stages it - zoom 1.5, the player at 2x - is gb_preview15.py.

    python gb_preview.py <sheet_dir> <out_dir>

At the game's 1920x1080, 3 px to a texel, from ArenaScene's own node transforms (the Carter FX rig's
arena compositor, imported). Draw order follows the engine: ringside, crowd, mat; then everything that
stands on the floor - the rubble, Greyson, the player - y-sorted by its base; then the effects; then the
ropes, which the fight scenes draw at z 1 over all of it. Light-free: every sheet here is painted.
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.abspath(os.path.join(_HERE, '..', '..'))
sys.path.insert(0, os.path.join(PROJ, 'art_source', 'carter_messatsu_fx'))
import previews as cp          # noqa: E402  (blit, blit_rot, load, frame, to_720, save, draw_player)

A = cp.A
load, frame, blit, save, to_720 = cp.load, cp.frame, cp.blit, cp.save, cp.to_720

GREYSON_FEET = (960.0, 610.0)
PLAYER_AT = (960.0, 745.0)                 # the player's body (sprite centre)
HEAD_TOP = GREYSON_FEET[1] - 258           # his hair's top row
TELL_ANCHOR = (960.0, HEAD_TOP - 20)       # ParryTell's anchor: DefenseHypeArtLayout.PARRY_TELL_OFFSET
# the clearing the rubble leaves, as mound BASES may not enter it (the architect's to set)
BOX = (690.0, 430.0, 1230.0, 870.0)


# ------------------------------------------------------------------ arena

def floor_and_ropes():
    """ArenaScene split in two: what is under the fighters, and the ropes and posts over them"""
    floor = np.zeros((1080, 1920, 4), np.float32)
    floor[..., 3] = 255
    blit(floor, load(A('Environment', 'arena_ringside.png')), 0, 0, scale=3)
    crowd = load(A('Environment', 'crowd_v2.png'))
    blit(floor, crowd[:, 0:640], 0, 0, scale=3)
    blit(floor, load(A('Environment', 'arena_mat.png')), 111, 114, scale=3)
    ropes = np.zeros((1080, 1920, 4), np.float32)
    rope = Image.open(A('Environment', 'boundaries.png')).convert('RGBA')
    pole = Image.open(A('Environment', 'pole.png')).convert('RGBA')

    def sprite(im, pos, sc, region=None, rot=False, fh=False, fv=False):
        if region:
            im = im.crop((int(region[0]), 0, int(region[0] + region[2]), 32))
        im = im.resize((max(1, int(round(im.width * sc[0]))), max(1, int(round(im.height * sc[1])))),
                       Image.NEAREST)
        if fh:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        if fv:
            im = im.transpose(Image.FLIP_TOP_BOTTOM)
        if rot:
            im = im.transpose(Image.ROTATE_270)
        a = np.asarray(im, dtype=np.float32)
        x, y = int(round(pos[0] - a.shape[1] / 2)), int(round(pos[1] - a.shape[0] / 2))
        H, W = ropes.shape[:2]
        x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + a.shape[1]), min(H, y + a.shape[0])
        sub = a[y0 - y:y1 - y, x0 - x:x1 - x]
        m = sub[..., 3] > 0
        ropes[y0:y1, x0:x1][m] = sub[m]

    k = (7.783335, 6.9375)
    sprite(rope, (960 - 608, 100 + 14), k, (0, 0, 128.47955, 32))
    sprite(rope, (960 + 667.5, 100 + 14), k, (156.22682, 0, 143.77318, 32))
    sprite(rope, (100 - 8, 540 + 31.4), (3.9833364, 6.9375), rot=True)
    sprite(rope, (1820 - 15, 540 + 27.5), (3.9273026, 6.9375), rot=True)
    sprite(rope, (960 - 609.25, 980 + 8), k, (0, 0, 128.80088, 32))
    sprite(rope, (960 + 666.25, 980 + 8), k, (156.54815, 0, 143.45185, 32))
    sprite(pole, (960 - 855, 107), (1.5859377, 2.03125))
    sprite(pole, (960 + 847, 109), (1.5859377, 2.03125), fh=True)
    sprite(pole, (960 - 847, 964), (1.5859377, 1.1875007), fv=True)
    sprite(pole, (960 + 846, 965), (1.5859377, 1.1875007), fh=True, fv=True)
    return floor, ropes


def over_ropes(img, ropes):
    m = ropes[..., 3] > 0
    img[m, :3] = ropes[m, :3]


# ------------------------------------------------------------ the rubble

def rubble_layout(seed=5, share=1.0):
    """mounds as (frame, base x, base y): walls round BOX, the rest of the ring filled. `share` of the
    fill is placed (the cutscene shows it filling up); the walls come last."""
    rnd = random.Random(seed)
    x0, y0, x1, y1 = BOX
    out = []
    # the fill: a jittered grid over the ring, keeping clear of the box and its walls
    y = 190.0
    row = 0
    while y < 975.0:
        x = 150.0 + (row % 2) * 70.0
        while x < 1790.0:
            bx, by = x + rnd.uniform(-30, 30), y + rnd.uniform(-14, 14)
            clear = (x0 - 150 < bx < x1 + 150) and (y0 - 60 < by < y1 + 110)
            if not clear:
                r = rnd.random()
                f = rnd.choice((0, 1)) if r < 0.18 else (rnd.choice((5, 6, 7)) if r < 0.45 else rnd.choice((2, 3, 4)))
                out.append((f, bx, by, 'fill'))
            x += rnd.uniform(110.0, 170.0)
        y += rnd.uniform(52.0, 72.0)
        row += 1
    rnd.shuffle(out)
    out = out[:int(len(out) * share)]
    walls = []
    # the wall behind Greyson: big heaps
    x = x0 - 40
    while x <= x1 + 40:
        walls.append((rnd.choice((2, 3, 4, 0)), x + rnd.uniform(-10, 10), y0 - 20 + rnd.uniform(-8, 8), 'top'))
        x += 132.0
    # the side walls: medium heaps, stepping down the box's sides
    y = y0 + 20
    while y <= y1 + 30:
        for side, bx in ((-1, x0 - 70), (1, x1 + 70)):
            walls.append((rnd.choice((5, 6, 7)), bx + rnd.uniform(-12, 12), y + rnd.uniform(-6, 6), 'side'))
        y += 76.0
    # the wall in front of the player: low ridges only
    x = x0 + 10
    while x <= x1 - 10:
        walls.append((rnd.choice((8, 9)), x + rnd.uniform(-10, 10), y1 + 60 + rnd.uniform(-6, 6), 'front'))
        x += 150.0
    if share >= 1.0:
        out += walls
    else:
        out += [w for w in walls if rnd.random() < share]
    return out


def bits_layout(seed=9):
    rnd = random.Random(seed)
    x0, y0, x1, y1 = BOX
    out = []
    for i in range(10):
        side = i % 4
        if side == 0:
            bx, by = rnd.uniform(x0 + 30, x1 - 30), y0 + rnd.uniform(0, 25)
        elif side == 1:
            bx, by = rnd.uniform(x0 + 30, x1 - 30), y1 + rnd.uniform(-10, 10)
        elif side == 2:
            bx, by = x0 + rnd.uniform(-5, 30), rnd.uniform(y0 + 30, y1 - 30)
        else:
            bx, by = x1 + rnd.uniform(-30, 5), rnd.uniform(y0 + 30, y1 - 30)
        # none inside the fighters' own footprints
        if abs(bx - GREYSON_FEET[0]) < 150 and abs(by - GREYSON_FEET[1]) < 40:
            continue
        if abs(bx - PLAYER_AT[0]) < 70 and abs(by - (PLAYER_AT[1] + 40)) < 30:
            continue
        out.append((rnd.randrange(8), bx, by))
    return out


# ------------------------------------------------------------- drawing

def mound(img, sheets, f, bx, by):
    fr = frame(sheets['rubble_mound'], f, 64)
    blit(img, fr, int(round(bx - 32 * 3)), int(round(by - 46 * 3)), scale=3)


def bit(img, sheets, f, bx, by):
    fr = frame(sheets['rubble_bits'], f, 16)
    blit(img, fr, int(round(bx - 8 * 3)), int(round(by - 11 * 3)), scale=3)


def greyson(img, f=0):
    sheet = load(A('Characters', 'Greyson', 'greyson_redesign.png'))
    blit(img, frame(sheet, f, 112), int(GREYSON_FEET[0] - 168), int(GREYSON_FEET[1] - 336), scale=3)


def player(img, at=PLAYER_AT, fi=10, alpha=1.0, tint=None):
    sheet = load(A('Characters', 'MainPlayer', 'player_4dir_sheet.png'))
    col, row = fi % 10, fi // 10
    fr = sheet[row * 32:(row + 1) * 32, col * 32:(col + 1) * 32].copy()
    if tint is not None:
        m = fr[..., 3] > 0
        fr[m, :3] = np.array(tint, np.float32)
    blit(img, fr, int(at[0] - 48), int(at[1] - 48), alpha=alpha, scale=3)


def standing(img, sheets, layout, bits=(), with_greyson=True, with_player=True, greyson_f=0,
             player_at=PLAYER_AT):
    """everything on the floor, y-sorted by its base, as the fight's y-sort draws it"""
    items = [(by, 'mound', (f, bx, by)) for (f, bx, by, _) in layout]
    items += [(by, 'bit', (f, bx, by)) for (f, bx, by) in bits]
    if with_greyson:
        items.append((GREYSON_FEET[1], 'greyson', greyson_f))
    if with_player:
        items.append((player_at[1] + 40, 'player', player_at))
    items.sort(key=lambda t: t[0])
    for _, kind, arg in items:
        if kind == 'mound':
            mound(img, sheets, *arg)
        elif kind == 'bit':
            bit(img, sheets, *arg)
        elif kind == 'greyson':
            greyson(img, arg)
        else:
            player(img, arg)


def tell(img, sheets, which, state=1):
    """the tell over his head, its pivot on ParryTell's anchor"""
    ax, ay = TELL_ANCHOR
    if which == 'parry':
        pt = load(A('Effects', 'parry_tell.png'))
        blit(img, frame(pt, 0, 32), int(ax - 16 * 3), int(ay - 24 * 3), scale=3)
    else:
        d = {'left': 0, 'right': 1}[which]
        fr = frame(sheets['arrow'], d * 4 + state, 28)
        blit(img, fr, int(ax - 14 * 3), int(ay - 25 * 3), scale=3)


# --------------------------------------------------------------- scenes

def scene_cutscene(sheets):
    """the slams bringing the roof in: the rubble half built, chunks caught mid-fall over their shadows,
    three landings"""
    img, ropes = floor_and_ropes()
    layout = rubble_layout(share=0.45)
    # (landing x, landing y, height still to fall in px, frame): heights as the ease-in fall leaves them
    falls = [(330, 560, 300, 0), (575, 330, 170, 2), (1335, 470, 240, 4), (1570, 760, 110, 7),
             (430, 880, 60, 1), (1185, 300, 380, 3), (1520, 330, 150, 5), (770, 905, 330, 6)]
    shadow = frame(sheets['debris_shadow'], 0, 36)
    for (lx, ly, hgt, fi) in falls:
        prog = 1.0 - min(1.0, hgt / 420.0)
        blit_scaled_shadow(img, shadow, lx, ly, 0.3 + 0.7 * prog, 0.15 + 0.35 * prog)
    standing(img, sheets, layout)
    for (lx, ly, hgt, fi) in falls:
        fr = frame(sheets['debris'], fi, 32)
        blit(img, fr, int(round(lx - 16 * 3)), int(round(ly - hgt - 56 * 3)), scale=3)
    for (lx, ly, lf) in ((700, 330, 1), (1240, 560, 2), (520, 700, 3)):
        fr = frame(sheets['debris_land'], lf, 80)
        blit(img, fr, int(round(lx - 40 * 3)), int(round(ly - 40 * 3)), scale=3)
    over_ropes(img, ropes)
    return img


def blit_scaled_shadow(img, shadow, cx, cy, s, alpha):
    """the black spot, grown by the code: nearest-sampled at scale 3*s about its centre"""
    cp.blit_rot(img, shadow, (cx, cy), 0.0, 3.0 * s, (18, 6), alpha=alpha)


def scene_hook(sheets, hook_step=1, arrow_state=1):
    """a LEFT hook: the arrow up, his left fist sweeping in from the screen's right, the player
    slipping left with the afterimage left behind"""
    img, ropes = floor_and_ropes()
    layout = rubble_layout()
    dodge_to = (PLAYER_AT[0] - 84, PLAYER_AT[1])
    standing(img, sheets, layout, bits_layout(), player_at=dodge_to)
    # the afterimage: the player's own frame where he was, in the perfect-dodge cyan, 3 alpha steps
    for i, a in enumerate((56 / 255.0, 112 / 255.0, 176 / 255.0)):
        gx = PLAYER_AT[0] - 84 * (2 - i) / 3.0 * 0.0 - 84 * (i / 3.0)
        player(img, (PLAYER_AT[0] - 28 * i, PLAYER_AT[1]), alpha=a, tint=(0x5F, 0xCD, 0xE4))
    player(img, dodge_to)
    # the whoosh: its pivot (the strike point) on the head the player just took out of the way
    hx, hy = 16, 64
    fr = frame(sheets['hook'], 0 * 4 + hook_step, 60)
    blit(img, fr, int(round(PLAYER_AT[0] - hx * 3)), int(round(PLAYER_AT[1] - 42 - hy * 3)), scale=3)
    tell(img, sheets, 'left', arrow_state)
    over_ropes(img, ropes)
    return img


def scene_straight(sheets):
    """the straight: the red badge up, the fist driven down at the player; this one landed"""
    img, ropes = floor_and_ropes()
    layout = rubble_layout()
    standing(img, sheets, layout, bits_layout())
    fr = frame(sheets['straight'], 1, 32)
    blit(img, fr, int(round(PLAYER_AT[0] - 16 * 3)), int(round(PLAYER_AT[1] - 40 - 50 * 3)), scale=3)
    fr = frame(sheets['impact'], 0, 48)
    blit(img, fr, int(round(PLAYER_AT[0] - 24 * 3)), int(round(PLAYER_AT[1] - 20 - 24 * 3)), scale=3)
    tell(img, sheets, 'parry')
    over_ropes(img, ropes)
    return img


def crop(img, box):
    x0, y0, x1, y1 = box
    return img[y0:y1, x0:x1]


def label_row(images, gap=12, bg=(12, 12, 16)):
    h = max(i.shape[0] for i in images)
    w = sum(i.shape[1] for i in images) + gap * (len(images) + 1)
    out = np.zeros((h + 2 * gap, w, 4), np.float32)
    out[..., :3] = bg
    out[..., 3] = 255
    x = gap
    for i in images:
        out[gap:gap + i.shape[0], x:x + i.shape[1]] = i
        x += i.shape[1] + gap
    return out


def kit(sheets, out):
    """every frame of every sheet at game scale (3x), on the mat and on the dark ringside, labelled"""
    from PIL import ImageDraw
    spec = [('debris', 32, 'brawl_debris 32x56 x8: shape*2+spin, pivot (16,56)'),
            ('debris_shadow', 36, 'brawl_debris_shadow 36x12, pivot (18,6), code-scaled'),
            ('debris_land', 80, 'brawl_debris_land 80x48 x6 @0.05s, pivot (40,40)'),
            ('rubble_mound', 64, 'brawl_rubble_mound 64x48 x10, pivot (32,46)'),
            ('rubble_bits', 16, 'brawl_rubble_bits 16x12 x8, pivot (8,11)'),
            ('arrow', 28, 'brawl_arrow 28x28 x8: LEFT pop/live/answered/missed, RIGHT ..., pivot (14,25)'),
            ('hook', 64, 'brawl_hook 64x32 x8 @0.04s: LEFT hook 0-3, RIGHT hook 4-7, pivot (22,19)/(42,19) = the head rest point'),
            ('straight', 32, 'brawl_straight 32x32 x4 @0.04s, pivot (16,16) = the parry contact'),
            ('impact', 48, 'brawl_impact 48x48 x5 @0.04s, pivot (24,24)')]
    blocks = []
    for name, fw, label in spec:
        s = sheets[name]
        h, w = s.shape[:2]
        n = w // fw
        gap = 18
        bw = n * (fw * 3 + gap) + gap
        rows = []
        for bg in ((126, 168, 91), (25, 23, 37)):
            r = np.zeros((h * 3 + gap, bw, 4), np.float32)
            r[..., :3] = bg
            r[..., 3] = 255
            for i in range(n):
                blit(r, frame(s, i, fw), gap + i * (fw * 3 + gap), gap // 2, scale=3)
            rows.append(r)
        head = np.zeros((26, bw, 4), np.float32)
        head[..., :3] = 12
        head[..., 3] = 255
        blocks.append((label, np.concatenate([head] + rows, 0)))
    W = max(b.shape[1] for _, b in blocks)
    Hh = sum(b.shape[0] for _, b in blocks)
    img = np.zeros((Hh, W, 4), np.float32)
    img[..., :3] = 12
    img[..., 3] = 255
    y = 0
    marks = []
    for label, b in blocks:
        img[y:y + b.shape[0], :b.shape[1]] = b
        marks.append((y, label))
        y += b.shape[0]
    im = Image.fromarray(np.clip(img[..., :3], 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    for y, label in marks:
        d.text((10, y + 7), label, fill=(235, 235, 240))
    im.save(os.path.join(out, 'kit_game_scale.png'))
    print('   kit_game_scale.png', im.size[0], 'x', im.size[1])


def _split(layout, bits, cut_y):
    back = [m for m in layout if m[2] < cut_y]
    front = [m for m in layout if m[2] >= cut_y]
    return back, front, [b for b in bits if b[2] < cut_y], [b for b in bits if b[2] >= cut_y]


def _gif(frames, path, durations):
    ims = [Image.fromarray(np.clip(f[..., :3], 0, 255).astype(np.uint8)) for f in frames]
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=durations, loop=0, disposal=1)
    print('  ', os.path.basename(path), len(ims), 'frames')


def anim_hook(sheets, out, box=(600, 200, 1320, 900)):
    """a LEFT hook read at 1:1: the badge pops, holds while the fist comes round, the player slips
    left as it lands and the badge answers. The hold is illustrative: the architect sets the window."""
    floor, ropes = floor_and_ropes()
    layout, bits = rubble_layout(), bits_layout()
    cut = PLAYER_AT[1] + 40
    back, front, bback, bfront = _split(layout, bits, cut)
    base = floor.copy()
    standing(base, sheets, back, bback, with_player=False)
    seq = []            # (arrow state, hook step or None, player dx, ghosts, duration ms)
    seq.append((0, None, 0, 0, 50))
    seq.append((1, None, 0, 0, 250))
    seq.append((1, 0, 0, 0, 40))
    seq.append((1, 1, -84, 3, 40))
    seq.append((2, 2, -84, 3, 40))
    seq.append((2, 3, -84, 2, 60))
    seq.append((2, None, -84, 1, 60))
    seq.append((None, None, -84, 0, 400))
    frames, durs = [], []
    for (st, step, dx, ghosts, ms) in seq:
        img = base.copy()
        at = (PLAYER_AT[0] + dx, PLAYER_AT[1])
        for i in range(ghosts):
            a = (56, 112, 176)[3 - ghosts + i] / 255.0
            player(img, (PLAYER_AT[0] - 28 * (i + 3 - ghosts), PLAYER_AT[1]), alpha=a, tint=(0x5F, 0xCD, 0xE4))
        player(img, at)
        standing(img, sheets, front, bfront, with_greyson=False, with_player=False)
        if step is not None:
            fr = frame(sheets['hook'], step, 60)
            blit(img, fr, int(round(PLAYER_AT[0] - 16 * 3)), int(round(PLAYER_AT[1] - 42 - 64 * 3)), scale=3)
        if st is not None:
            tell(img, sheets, 'left', st)
        over_ropes(img, ropes)
        frames.append(crop(img, box))
        durs.append(ms)
    _gif(frames, os.path.join(out, 'anim_hook_1to1.gif'), durs)


def anim_straight(sheets, out, box=(600, 200, 1320, 900)):
    """the straight read at 1:1: the red badge, the thrust, and here it lands"""
    floor, ropes = floor_and_ropes()
    layout, bits = rubble_layout(), bits_layout()
    base = floor.copy()
    standing(base, sheets, layout, bits)
    pt = load(A('Effects', 'parry_tell.png'))
    seq = [(0, None, None, 90), (1, None, None, 90), (2, None, None, 110), (2, 0, None, 40), (3, 1, 0, 40),
           (None, 2, 1, 40), (None, 3, 2, 40), (None, None, 3, 40), (None, None, 4, 40), (None, None, None, 300)]
    frames, durs = [], []
    for (bf, step, imp, ms) in seq:
        img = base.copy()
        if step is not None:
            fr = frame(sheets['straight'], step, 32)
            blit(img, fr, int(round(PLAYER_AT[0] - 16 * 3)), int(round(PLAYER_AT[1] - 40 - 50 * 3)), scale=3)
        if imp is not None:
            fr = frame(sheets['impact'], imp, 48)
            blit(img, fr, int(round(PLAYER_AT[0] - 24 * 3)), int(round(PLAYER_AT[1] - 20 - 24 * 3)), scale=3)
        if bf is not None:
            ax, ay = TELL_ANCHOR
            blit(img, frame(pt, bf, 32), int(ax - 16 * 3), int(ay - 24 * 3), scale=3)
        over_ropes(img, ropes)
        frames.append(crop(img, box))
        durs.append(ms)
    _gif(frames, os.path.join(out, 'anim_straight_1to1.gif'), durs)


def anim_debris(sheets, out, box=(150, 60, 870, 760)):
    """one chunk from the roof at 1:1: 0.40 s ease-in fall, tumbling every 0.06 s, its shadow growing,
    then the landing - Matt's shard timing (MattStateMachine.glass_shard_fall)"""
    floor, ropes = floor_and_ropes()
    lx, ly = 520.0, 520.0
    # clear floor where this one comes down, so the heap it leaves is seen forming
    layout = [m for m in rubble_layout(share=0.45) if math.hypot(m[1] - lx, (m[2] - ly) * 1.6) > 190]
    base = floor.copy()
    standing(base, sheets, layout)
    drop = ly + 200.0
    shadow = frame(sheets['debris_shadow'], 0, 36)
    frames, durs = [], []
    fps = 30
    for i in range(int(0.40 * fps) + 1):
        t = i / float(fps)
        p = min(1.0, t / 0.40)
        img = base.copy()
        blit_scaled_shadow(img, shadow, lx, ly, 0.3 + 0.7 * p, 0.15 + 0.35 * p)
        y = ly - drop * (1.0 - p * p)
        spin = int(t / 0.06) % 2
        blit(img, frame(sheets['debris'], 0 * 2 + spin, 32), int(round(lx - 16 * 3)), int(round(y - 56 * 3)), scale=3)
        over_ropes(img, ropes)
        frames.append(crop(img, box))
        durs.append(int(1000 / fps))
    for f in range(6):
        img = base.copy()
        if f >= 2:
            mound(img, sheets, 6, lx, ly + 6)
        blit(img, frame(sheets['debris_land'], f, 80), int(round(lx - 40 * 3)), int(round(ly - 40 * 3)), scale=3)
        over_ropes(img, ropes)
        frames.append(crop(img, box))
        durs.append(50)
    img = base.copy()
    mound(img, sheets, 6, lx, ly + 6)
    over_ropes(img, ropes)
    frames.append(crop(img, box))
    durs.append(500)
    _gif(frames, os.path.join(out, 'anim_debris_1to1.gif'), durs)


def main(sheet_dir, out):
    os.makedirs(out, exist_ok=True)
    names = ['debris', 'debris_shadow', 'debris_land', 'rubble_mound', 'rubble_bits', 'arrow', 'hook',
             'straight', 'impact']
    sheets = {n: load(os.path.join(sheet_dir, 'brawl_%s.png' % n)) for n in names}
    cut = scene_cutscene(sheets)
    hook = scene_hook(sheets)
    straight = scene_straight(sheets)
    for name, img in (('approval_1_cutscene', cut), ('approval_2_hook', hook), ('approval_3_straight', straight)):
        save(img, os.path.join(out, name + '.png'))
        save(to_720(img), os.path.join(out, name + '_720.png'))
    # 1:1 crops at game scale
    save(crop(hook, (600, 200, 1320, 900)), os.path.join(out, 'crop_hook_box_1to1.png'))
    save(crop(straight, (600, 200, 1320, 900)), os.path.join(out, 'crop_straight_box_1to1.png'))
    save(crop(cut, (150, 150, 870, 850)), os.path.join(out, 'crop_debris_1to1.png'))
    # the tells side by side over his head, 1:1: LEFT pop/live, RIGHT pop/live, the red badge
    heads = []
    for which, st in (('left', 0), ('left', 1), ('right', 0), ('right', 1), ('parry', 0)):
        img, ropes = floor_and_ropes()
        standing(img, sheets, rubble_layout(), with_player=False)
        tell(img, sheets, which, st)
        heads.append(crop(img, (800, 180, 1120, 560)))
    save(label_row(heads), os.path.join(out, 'crop_tells_1to1.png'))
    kit(sheets, out)
    anim_hook(sheets, out)
    anim_straight(sheets, out)
    anim_debris(sheets, out)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
