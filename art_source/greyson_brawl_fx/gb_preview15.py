"""The brawl at close quarters, as PLAN_BRAWL.md stages it: zoom 1.5 at (960,402), the player at 2x right
in front of him. Mocks for the user's approval of the FX kit.

    python gb_preview15.py <sheet_dir> <out_dir>

World composed at 1920x1080 in the plan's 4 geometry, then the camera's view (x 320..1600, y 42..762)
cut out: 1:1 that is what a 1280x720 window shows at zoom 1.5, and scaled x1.5 (nearest) it is the
1920x1080 screen. Draw order is the plan's: floor; heaps and Greyson y-sorted at z 0; the ropes at z 1;
whooshes at z 2; the player at z 3; hit impacts at z 4; the tells over all.

PLACEHOLDERS, as the plan ships them until the brawl sheets land: Greyson is his approved ready frame
(crown 86, standing; the crouch will bring it down to 78, which is what the tell point allows for), and
the player is an exact nearest-neighbour x2 of the approved player_final_brawl.png, re-registered to the
2x contract (64x96 cells, soles on row 61, origin 13 texels above them).
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import gb_preview as gp        # noqa: E402  (arena, heaps, compositing)
import gb_punch as gpu         # noqa: E402

A, load, frame, blit, save = gp.A, gp.load, gp.frame, gp.blit, gp.save

# PLAN_BRAWL.md 4, world px
HOME = (960.0, 560.0)                  # his feet
PLAYER_ORIGIN = (960.0, 533.0)
PLAYER_SOLES = (960.0, 572.0)
HEAD = (960.0, 446.0)                  # the player's head centre at rest
PARRY_CONTACT = (957.0, 416.0)
TELL = (960.0, 308.0)                  # the arrow's pivot and the badge's anchor
CLEARING = (690.0, 400.0, 1230.0, 700.0)
ROPES_IN = (120.0, 120.0, 1800.0, 960.0)          # ROPES.grow(-20), approximated from ArenaScene's walls
VIEW = (320, 42, 1600, 762)
CYAN = (0x5F, 0xCD, 0xE4)

# heap heights in px (the kit's KINDS, x3)
HEAP_H = [120, 111, 114, 102, 108, 84, 78, 72, 48, 39]


def rubble(seed=11, rule='adopted'):
    """PLAN_BRAWL.md 4: a jittered ~150x100 grid over the ropes, clear of CLEARING.grow(30); big heaps far
    out; low ridges (7-9) along the front edge; no heap top above y 330 within 120 px of x 960"""
    rnd = random.Random(seed)
    x0, y0, x1, y1 = CLEARING
    gx0, gy0, gx1, gy1 = x0 - 30, y0 - 30, x1 + 30, y1 + 30
    out = []
    y = ROPES_IN[1] + 40
    row = 0
    while y <= ROPES_IN[3]:
        x = ROPES_IN[0] + 40 + (row % 2) * 75
        while x <= ROPES_IN[2]:
            bx, by = x + rnd.uniform(-40, 40), y + rnd.uniform(-25, 25)
            if not (gx0 < bx < gx1 and gy0 < by < gy1):
                dx = max(x0 - bx, 0, bx - x1)
                dy = max(y0 - by, 0, by - y1)
                far = math.hypot(dx, dy)
                if far > 260:
                    f = rnd.choice((0, 1)) if rnd.random() < 0.2 else rnd.choice((2, 3, 4))
                elif far > 90:
                    f = rnd.choice((2, 3, 4, 5, 6))
                else:
                    f = rnd.choice((5, 6, 7))
                top = by - HEAP_H[f]
                if rule == 'plan_literal':
                    # PLAN_BRAWL.md 4 as first written: no heap top above y 330 within 120 px of x 960.
                    # It empties a lane behind him to the top rope; kept only for comparison.
                    blocked = abs(bx - 960) < 120 and top < 330
                else:
                    # THE ADOPTED RULE (user approval 2026-09-24, PLAN_BRAWL.md coordinator amendments):
                    # no heap drawn over x 840-1080, y 225-560, where his silhouette and the tell stand
                    blocked = (bx - 90 < 1080 and bx + 90 > 840) and (top < 560 and by > 225)
                if not blocked:
                    out.append((f, bx, by, 'fill'))
            x += 150.0
        y += 100.0
        row += 1
    # the front edge: low ridges only, y 700-730
    x = x0 + 20
    while x <= x1 - 20:
        out.append((rnd.choice((7, 8, 9)), x + rnd.uniform(-12, 12), 715 + rnd.uniform(-12, 12), 'front'))
        x += 125.0
    return out


def player2x(img, col=0, at=PLAYER_ORIGIN, alpha=1.0, tint=None, dx=0):
    """the x2 placeholder: approved 32x32 frame, doubled, soles on the 2x cell's row 61"""
    sheet = load(A('Characters', 'MainPlayer', 'player_final_brawl.png'))
    fr = sheet[0:32, col * 32:(col + 1) * 32].repeat(2, 0).repeat(2, 1).copy()
    if tint is not None:
        m = fr[..., 3] > 0
        fr[m, :3] = np.array(tint, np.float32)
    cell_top = at[1] - 48 * 3                      # the 64x96 cell, centred on the origin
    cell_left = at[0] - 32 * 3
    blit(img, fr, int(round(cell_left + dx)), int(round(cell_top + 4 * 3)), alpha=alpha, scale=3)


def greyson(img, f=0):
    sheet = load(A('Characters', 'Greyson', 'greyson_redesign.png'))
    blit(img, frame(sheet, f, 112), int(HOME[0] - 168), int(HOME[1] - 336), scale=3)


def world(sheets, layout):
    img, ropes = gp.floor_and_ropes()
    items = [(by, 'heap', (f, bx, by)) for (f, bx, by, _) in layout]
    items.append((HOME[1], 'greyson', 0))
    items.sort(key=lambda t: t[0])
    for _, kind, arg in items:
        if kind == 'heap':
            gp.mound(img, sheets, *arg)
        else:
            greyson(img, arg)
    gp.over_ropes(img, ropes)                      # z 1: over the heaps and him, under the rest
    return img


def view(img):
    x0, y0, x1, y1 = VIEW
    return img[y0:y1, x0:x1]


def screen(img):
    """the 1920x1080 screen at zoom 1.5: the view scaled x1.5, nearest"""
    v = view(img)
    ys = np.floor((np.arange(1080) + 0.5) / 1.5).astype(int)
    xs = np.floor((np.arange(1920) + 0.5) / 1.5).astype(int)
    return v[ys][:, xs]


def arrow(img, sheets, direction, state):
    d = {'left': 0, 'right': 1}[direction]
    blit(img, frame(sheets['arrow'], d * 4 + state, 28), int(TELL[0] - 14 * 3), int(TELL[1] - 25 * 3), scale=3)


def badge(img, f=0):
    pt = load(A('Effects', 'parry_tell.png'))
    blit(img, frame(pt, f, 32), int(TELL[0] - 16 * 3), int(TELL[1] - 24 * 3), scale=3)


def hook(img, sheets, direction, step):
    d = {'left': 0, 'right': 1}[direction]
    px, py = gpu.hook_pivot(d == 1)
    blit(img, frame(sheets['hook'], d * 4 + step, 64), int(HEAD[0] - px * 3), int(HEAD[1] - py * 3), scale=3)


def straight(img, sheets, step):
    blit(img, frame(sheets['straight'], step, 32), int(PARRY_CONTACT[0] - 16 * 3),
         int(PARRY_CONTACT[1] - 16 * 3), scale=3)


def impact(img, sheets, f):
    blit(img, frame(sheets['impact'], f, 48), int(HEAD[0] - 24 * 3), int(HEAD[1] - 24 * 3), scale=3)


def afterimage(img, toward):
    """the plan's code afterimage: 3 copies of the player in the perfect-dodge cyan, 0.15 / 0.30 / 0.45,
    from the rest position toward the slip"""
    for i, a in enumerate((0.15, 0.30, 0.45)):
        player2x(img, 0, alpha=a, tint=CYAN, dx=toward * 10 * i)


# ----------------------------------------------------------------- beats

def beat_hook_tell(sheets, base):
    img = base.copy()
    player2x(img, 0)
    arrow(img, sheets, 'left', 1)
    return img


def beat_hook_dodged(sheets, base):
    img = base.copy()
    hook(img, sheets, 'left', 1)                   # z 2
    afterimage(img, -1)                            # z 3
    player2x(img, 3)                               # slip L, full
    arrow(img, sheets, 'left', 2)                  # answered
    return img


def beat_hook_landed(sheets, base):
    img = base.copy()
    hook(img, sheets, 'right', 1)
    player2x(img, 8)                               # hit
    impact(img, sheets, 0)                         # z 4
    arrow(img, sheets, 'right', 3)                 # missed
    return img


def beat_straight_parried(sheets, base):
    img = base.copy()
    straight(img, sheets, 1)                       # z 2: behind the gloves, its ring round them
    player2x(img, 7)                               # the parry snap, z 3
    badge(img, 2)
    return img


def gif(frames, path, durations):
    ims = [Image.fromarray(np.clip(f[..., :3], 0, 255).astype(np.uint8)) for f in frames]
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=durations, loop=0, disposal=1)
    print('  ', os.path.basename(path), len(ims), 'frames')


def fighters_crop(img):
    """1:1 around the two of them (world px = window px at zoom 1.5 in a 1280x720 window)"""
    return img[210:620, 700:1220]


def anim_hook(sheets, base, out):
    """LEFT hook, slipped: T1's lead of 0.46 s, the answer at +0.30, the resolve 0.06 s later"""
    seq = []
    seq.append(('pop', None, 0, 0, 50))
    seq.append(('live', None, 0, 0, 250))
    seq.append(('live', None, 2, 0, 60))           # the answer: slip half
    seq.append(('answered', 1, 3, 1, 40))          # resolve: his strike, the whoosh through the rest point
    seq.append(('answered', 2, 3, 1, 40))
    seq.append(('answered', 3, 3, 0, 40))
    seq.append((None, None, 3, 0, 120))
    seq.append((None, None, 0, 0, 400))
    frames, durs = [], []
    for (st, step, col, ghost, ms) in seq:
        img = base.copy()
        if step is not None:
            hook(img, sheets, 'left', step)
        if ghost:
            afterimage(img, -1)
        player2x(img, col)
        if st is not None:
            arrow(img, sheets, 'left', {'pop': 0, 'live': 1, 'answered': 2}[st])
        frames.append(fighters_crop(img))
        durs.append(ms)
    gif(frames, os.path.join(out, 'z15_anim_hook_slip.gif'), durs)


def anim_straight(sheets, base, out):
    """the straight, parried: the red badge, the parry snap, the burst on the contact"""
    seq = [(0, None, 0, 90), (1, None, 0, 90), (2, None, 0, 110), (3, None, 6, 50), (None, 0, 7, 40),
           (None, 1, 7, 40), (None, 2, 7, 40), (None, 3, 7, 40), (None, None, 0, 400)]
    frames, durs = [], []
    for (bf, step, col, ms) in seq:
        img = base.copy()
        if step is not None:
            straight(img, sheets, step)            # z 2, under the player
        player2x(img, col)
        if bf is not None:
            badge(img, bf)
        frames.append(fighters_crop(img))
        durs.append(ms)
    gif(frames, os.path.join(out, 'z15_anim_straight_parry.gif'), durs)


def main(sheet_dir, out):
    os.makedirs(out, exist_ok=True)
    names = ['debris', 'debris_shadow', 'debris_land', 'rubble_mound', 'rubble_bits', 'arrow', 'hook',
             'straight', 'impact']
    sheets = {n: load(os.path.join(sheet_dir, 'brawl_%s.png' % n)) for n in names}
    layout = rubble()
    base = world(sheets, layout)
    beats = [('z15_1_hook_tell', beat_hook_tell), ('z15_2_hook_slipped', beat_hook_dodged),
             ('z15_3_hook_landed', beat_hook_landed), ('z15_4_straight_parried', beat_straight_parried)]
    crops = []
    for name, fn in beats:
        img = fn(sheets, base)
        save(screen(img), os.path.join(out, name + '_1920.png'))
        save(view(img), os.path.join(out, name + '_1280.png'))
        crops.append(fighters_crop(img))
    save(gp.label_row(crops), os.path.join(out, 'z15_fighters_1to1.png'))
    # the settled ring at zoom 1.0, the frame before the camera cuts in
    whole = base.copy()
    player2x(whole, 0)
    save(whole, os.path.join(out, 'z10_settled_ring.png'))
    anim_hook(sheets, base, out)
    anim_straight(sheets, base, out)
    # the first-written layout rule, for comparison only
    old = world(sheets, rubble(rule='plan_literal'))
    whole = old.copy()
    player2x(whole, 0)
    save(whole, os.path.join(out, 'z10_plan_literal_layout_settled_ring.png'))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
