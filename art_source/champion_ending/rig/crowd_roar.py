"""The crowd's ROAR for the champion lift: four new frames on both arena crowd sheets.

Built on the shipped generators (art_source/crowd_react, which builds on art_source/crowd and
art_source/arena) imported as libraries - nothing of theirs is run or changed, and this script
writes only into the approval folder. Same seeds, so the same 280 + 240 people.

  crowd_v3_roar.png              11 frames of 640x40   (frames 0-6 pixel-identical to crowd_v3.png)
  arena_ringside_crowd_roar.png  11 frames of 640x360  (frames 0-6 pixel-identical to the shipped one)

  frames 7-10: roar loop (0.10 s a frame). Everyone is on their feet with both arms up, and JUMPS:
  a 4-beat hop (0, -1, -2, -1 px) phased per spectator, so the stands ripple instead of bouncing
  in lockstep (the cheer only ever hops one pixel). Every mouth is open. The sign holders turn
  their boards to the champion: @ becomes a trophy, the chat bubble shouts '!!', and three more
  spectators lift '#1' boards. Camera flashes triple (15 a frame against the cheer's 5).
"""
import os
import random
import sys

sys.dont_write_bytecode = True
from common import PROJECT, save

SRC = os.path.join(PROJECT, 'art_source', 'crowd_react')
sys.path.insert(0, SRC)
import crowd_react as R       # noqa: E402  (imports crowd.py as R.C; defines, never writes)
import ringside_react as RR   # noqa: E402
from PIL import Image         # noqa: E402

C = R.C
P = C.P
ROAR = (7, 8, 9, 10)
NF = 11
HOP = [0, -1, -2, -1]

ROAR_SIGNS = {
    'cup': P(-2, -11,
        'bBBBBBBBb',
        'BOBOOOBOB',
        'BOOOOOOOB',
        'BBOOOOOBB',
        'BBBOOOBBB',
        'BBBBOBBBB',
        'BBBOOOBBB',
        'bbbbbbbbb'),
    'bubble_hype': P(-2, -9,
        '.PPPPPPP.',
        'PPPWPWPPP',
        'PPPWPWPPP',
        'PPPWPWPPP',
        'PPPPPPPPP',
        '.PPWPWPp.',
        '.Pp......'),
    'num1': P(-3, -10,
        'bBBBBBBBBBb',
        'BBRBRBBBRBB',
        'BRRRRRBRRBB',
        'BBRBRBBBRBB',
        'BRRRRRBBRBB',
        'BBRBRBBRRRB',
        'bbbbbbbbbbb'),
}
C.SIGNS.update(ROAR_SIGNS)
ROAR_FLIP = {'at': 'cup', 'bubble': 'bubble_hype'}
ROAR_ONLY_SIGNS = [(3, 100, 'num1'), (2, 300, 'num1'), (3, 555, 'num1')]


def assign_roar(rng, figures):
    for f in figures:
        ph = rng.randrange(4)
        side = rng.choice('LR')
        poses, dys = [], []
        for k in range(4):
            hop = HOP[(k + ph) % 4]
            dys.append(hop)
            if f['sign'] == 'foam':
                poses.append('foamL')
            elif f['sign']:
                poses.append('holdB')
            else:
                # both arms up in the air at the top of the jump, a V on the way
                poses.append('upB' if hop == -2 else ('vB' if hop == -1 else 'up' + side))
        f['poses'] = f['poses'][:7] + poses
        f['dys'] = f['dys'][:7] + dys
        f['mouths'] = f['mouths'][:7] + [True] * 4
    for row, ax, name in ROAR_ONLY_SIGNS:
        cands = [g for g in figures if g['row'] == row and not g['sign'] and not g.get('boo_sign')]
        f = min(cands, key=lambda g: abs(g['fx'] - ax))
        f['roar_sign'] = name
        f['poses'] = f['poses'][:7] + ['holdB'] * 4


def draw_roar(cv, f, fr):
    keep = f['sign']
    if f.get('roar_sign'):
        f['sign'] = f['roar_sign']
    elif keep in ROAR_FLIP:
        f['sign'] = ROAR_FLIP[keep]
    try:
        C.draw_figure(cv, f, fr)
    finally:
        f['sign'] = keep
    if f['size'] == 'L' and not f['sign'] and not f.get('roar_sign'):
        R.boo_mouth(cv, f, fr)         # the two-pixel mouth opens to an 'O': shouting


def band_frames():
    figures, frames = R.render()                       # frames 0-6, exactly the shipped strip
    assign_roar(random.Random(2026), figures)
    frng = random.Random(1006)
    for fr in ROAR:
        cv = [[None] * C.FW for _ in range(C.FH)]
        for ri in range(len(C.ROWS)):
            row_figs = [f for f in figures if f['row'] == ri]
            row_figs.sort(key=lambda f: (f['poses'][fr] is not None,
                                         bool(f['sign'] or f.get('roar_sign'))))
            for f in row_figs:
                draw_roar(cv, f, fr)
        C.flashes(cv, frng, 15, avoid=[])
        C.fade_bottom(cv)
        frames.append(cv)
    return figures, frames


# ---------------------------------------------------------------- the ringside spectators
def ringside_frames():
    figs, frames = RR.render()                         # frames 0-6, exactly the shipped sheet
    rng = random.Random(77)
    for f in figs:
        f['rph'] = rng.randrange(4)
    base = RR.backdrop()
    for fr in ROAR:
        canvas = dict(base)
        k0 = fr - ROAR[0]
        for f in figs:
            cx, feet, skin, shirt = f['cx'], f['feet'], f['skin'], f['shirt']
            hop = HOP[(k0 + f['rph']) % 4]
            top = feet - 7 + hop
            for y in range(top + 3, feet + hop + 1):
                for x in range(cx - 1, cx + 2):
                    if RR.in_zone(x, y):
                        canvas[(x, y)] = shirt
            for y in range(top, top + 3):
                for x in range(cx - 1, cx + 2):
                    if RR.in_zone(x, y):
                        canvas[(x, y)] = skin
            # both arms straight up at the top of the hop, a V otherwise
            if hop == -2:
                arms = [(cx - 2, 3, 3), (cx - 3, -2, 2), (cx + 2, 3, 3), (cx + 3, -2, 2)]
            else:
                arms = [(cx - 2, 3, 3), (cx - 3, 0, 2), (cx - 4, -2, -1),
                        (cx + 2, 3, 3), (cx + 3, 0, 2), (cx + 4, -2, -1)]
            for ax, r0, r1 in arms:
                for r in range(r0, r1 + 1):
                    if RR.arm_ok(ax, top + r):
                        canvas[(ax, top + r)] = skin
        im = Image.new('RGBA', (RR.W, RR.H), (0, 0, 0, 0))
        px = im.load()
        for (x, y), c in canvas.items():
            px[x, y] = c + (255,)
        frames.append(im)
    return figs, frames


def build():
    from common import ASSETS
    _, bf = band_frames()
    band = R.to_image(bf)
    ship = Image.open(os.path.join(ASSETS, 'Environment', 'crowd_v3.png')).convert('RGBA')
    same_band = band.crop((0, 0, ship.width, ship.height)).tobytes() == ship.tobytes()
    _, rf = ringside_frames()
    ring = RR.sheet(rf)
    ship2 = Image.open(os.path.join(ASSETS, 'Environment', 'arena_ringside_crowd.png')).convert('RGBA')
    a, b = ring.crop((0, 0, ship2.width, ship2.height)).load(), ship2.load()
    bad = sum(1 for y in range(ship2.height) for x in range(ship2.width)
              if a[x, y][3] != b[x, y][3] or (a[x, y][3] and a[x, y] != b[x, y]))
    if not same_band or bad:
        raise SystemExit(f'frames 0-6 drifted from the shipped sheets (band same={same_band}, '
                         f'ringside differing px={bad}); nothing written')
    p1 = save(band, 'crowd/crowd_v3_roar.png')
    p2 = save(ring, 'crowd/arena_ringside_crowd_roar.png')
    print('crowd band', band.size, 'frames 0-6 identical to shipped:', same_band, '->', p1)
    print('ringside  ', ring.size, 'frames 0-6 identical to shipped: True ->', p2)
    return band, ring


if __name__ == '__main__':
    build()
