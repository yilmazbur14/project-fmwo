"""Crowd reactions for the arena's top band: the shipped crowd plus a BOO loop -> crowd_v3.png.

Built on art_source/crowd/crowd.py without changing it: the same seed gives the same 280 people,
and their own parts, palette and auto-outline draw the new poses. The strip (7 frames of 640x40):

  frames 0-2 : idle loop   - identical to crowd_v2.png (0.35 s a frame)
  frames 3-4 : cheer loop  - identical to crowd_v2.png (0.15 s a frame)
  frames 5-6 : boo loop    - new                       (0.20 s a frame)

Boo body language, chosen to read as the opposite of the cheer at a glance: no arm goes above the
heads (the cheer is a forest of raised arms), fists shake at head height, thumbs go down at
shoulder height, hands cup round mouths, and on the other beat they bob DOWN a pixel (the cheer
hops up). The sign-holders turn their signs: W -> L, heart -> broken heart, GG -> a sad face, the
chat bubble frowns, @ -> a red X, and the blurple foam finger becomes a thumbs-down foam hand.
Three spectators who hold nothing otherwise lift a red BOO board. No camera flashes.

Approved 2026-09-24. Writes only where it's told, and never into Assets - build_ship.py ships.
    python crowd_react.py --out <dir>        -> <dir>/crowd_v3.png
"""
import argparse
import os
import random
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "crowd"))
import crowd as C  # noqa: E402

NAME = "crowd_v3.png"
BOO_FRAMES = (5, 6)
NF = C.NF + len(BOO_FRAMES)       # 7

P = C.P

# ---------------------------------------------------------------- new arm parts
# LARGE figures: head interior x0..5, y0..5; torso from y6; left shoulder at x-3..-2, y7..8.
L_BOO_ARMS = {
    # fist at head height, swung out one pixel on the other beat; the shoulder stays put
    'fist': P(-4, -1,
        'LSs.',
        'SSs.',
        '.Ss.',
        '.Ss.',
        '.KC.',
        '.KC.',
        '.KC.',
        '.KCC',
        '.KCC'),
    'fist2': P(-5, 0,
        'LSs..',
        'SSs..',
        '.Ss..',
        '..KC.',
        '..KC.',
        '..KC.',
        '..KCC',
        '..KCC'),
    # arm straight out at shoulder height, a two-pixel thumb down under the fist; jabs down a pixel
    'thumb': P(-8, 3,
        'LSs......',
        'SSsKKC...',
        '.S...KC..',
        '.S....KC.',
        '.......KC'),
    'thumb2': P(-8, 4,
        'LSs......',
        'SSsKKC...',
        '.S...KC..',
        '.S....KC.',
        '.......KC'),
}
# SMALL figures: head interior x0..4, y0..3; torso from y5.
S_BOO_ARMS = {
    'fist': P(-4, -1,
        'SS.',
        'Ss.',
        '.S.',
        '.C.',
        '.CC',
        '.CC'),
    'fist2': P(-5, 0,
        'SS..',
        'Ss..',
        '..S.',
        '..C.',
        '..CC'),
}
C.L_ARMS.update(L_BOO_ARMS)
C.S_ARMS.update(S_BOO_ARMS)

# ---------------------------------------------------------------- boo signs (PROP_COL letters)
BOO_SIGNS = {
    'heart_broken': P(-2, -9,
        'bBBBBBBBb',
        'BRrBBBRrB',
        'BRRRBRRRB',
        'BBRRBRRBB',
        'BBBRBRBBB',
        'bbbbbbbbb'),
    'sad': P(-2, -10,
        'bBBBBBBBb',
        'BBPBBBPBB',
        'BBPBBBPBB',
        'BBBBBBBBB',
        'BBBPPPBBB',
        'BBPBBBPBB',
        'bbbbbbbbb'),
    'x': P(-2, -11,
        'bBBBBBBBb',
        'BRBBBBBRB',
        'BBRBBBRBB',
        'BBBRBRBBB',
        'BBBBRBBBB',
        'BBBRBRBBB',
        'BBRBBBRBB',
        'bbbbbbbbb'),
    'bubble_frown': P(-2, -9,
        '.PPPPPPP.',
        'PPPPPPPPP',
        'PPWPPPWPP',
        'PPPGGGPPP',
        'PPGPPPGPP',
        '.PPPPPPp.',
        '.Pp......'),
    # a red BOO in a 3x5 font; wider than the other boards, so it sits on its own spectators
    'boo': P(-4, -10,
        'bBBBBBBBBBBBb',
        'BRRBBBRBBBRBB',
        'BRBRBRBRBRBRB',
        'BRRBBRBRBRBRB',
        'BRBRBRBRBRBRB',
        'BRRBBBRBBBRBB',
        'bbbbbbbbbbbbb'),
    'l': P(-2, -9,
        'bBBBBBBBb',
        'BBBRBBBBB',
        'BBBRBBBBB',
        'BBBRBBBBB',
        'BBBRRRRBB',
        'bbbbbbbbb'),
}
C.SIGNS.update(BOO_SIGNS)
SIGN_FLIP = {'heart': 'heart_broken', 'gg': 'sad', 'at': 'x', 'bubble': 'bubble_frown', 'w': 'l'}

# the foam finger's fan turns it into a thumbs-down foam hand; the cuff sits where the finger's did
FOAM_DOWN = P(-7, -8,
    '.XYYYYYy.',
    'XYYYYYYYy',
    'XYYYYYYYy',
    'XYYYYYYYy',
    '.XYYYYYy.',
    'XY.yyyy..',
    'XY.yyyy..',
    'XY.......',
    '.y.......')

# ---------------------------------------------------------------- who does what
# (row, approx x, sign): spectators who hold nothing in idle or cheer and lift a board to boo
BOO_ONLY_SIGNS = [(3, 100, 'boo'), (2, 410, 'boo'), (3, 555, 'boo')]
BOO_L = {'fist': 8, 'thumb': 8, 'cup': 5, 'fists': 4, 'slump': 2}
BOO_S = {'fist': 10, 'cup': 6, 'slump': 5}


def assign_boo(rng, figures):
    for ri in range(len(C.ROWS)):
        big = C.ROWS[ri]['size'] == 'L'
        bag = C.Bag(rng, BOO_L if big else BOO_S, 1)
        for f in [g for g in figures if g['row'] == ri]:
            side = rng.choice(['L', 'R'])
            ph = rng.randrange(2)
            if f['sign'] == 'foam':
                poses, dys = ['foamL', 'foamL'], [0, 1]
            elif f['sign']:
                poses, dys = ['holdB', 'holdB'], [0, 1]
            else:
                kind = bag.draw()
                f['boo_kind'] = kind
                if kind == 'fist':
                    poses, dys = ['fist' + side, 'fist2' + side], [0, 1]
                elif kind == 'fists':
                    poses, dys = ['fistB', 'fist2B'], [0, 1]
                elif kind == 'thumb':
                    poses, dys = ['thumb' + side, 'thumb2' + side], [0, 1]
                elif kind == 'cup':
                    poses, dys = ['cupB', 'cupB'], [1, 0]
                else:
                    poses, dys = [None, None], [1, 1]
                if ph:
                    poses, dys = poses[::-1], dys[::-1]
            f['poses'] = f['poses'][:C.NF] + poses
            f['dys'] = f['dys'][:C.NF] + dys
            f['mouths'] = f['mouths'][:C.NF] + [f.get('boo_kind') != 'slump'] * 2
    for row, ax, name in BOO_ONLY_SIGNS:
        cands = [g for g in figures if g['row'] == row and not g['sign']]
        f = min(cands, key=lambda g: abs(g['fx'] - ax))
        f['boo_sign'] = name
        f['poses'] = f['poses'][:C.NF] + ['holdB', 'holdB']
        f['dys'] = f['dys'][:C.NF] + [0, 1]
        f['mouths'] = f['mouths'][:C.NF] + [True, True]


def sign_on(f, fr):
    return f['sign'] or (f.get('boo_sign') if fr in BOO_FRAMES else None)


def boo_mouth(cv, f, fr):
    """Large figures shout: the two-pixel mouth opens to a 2x2 'O' on the boo frames."""
    d = C.DEPTHS[f['depth']]
    if f['size'] != 'L' or not f['mouths'][fr] or not d['mouth']:
        return
    col = C.figure_colour(f, f['depth'])
    mx, my = C.L_MOUTH
    fx, fy = f['fx'], f['fy'] + f['dys'][fr]
    for i in range(2):
        x, y = fx + mx + i, fy + my - 1
        if 0 <= x < C.FW and 0 <= y < C.FH:
            cv[y][x] = col('m')


def draw(cv, f, fr):
    if fr in BOO_FRAMES and f.get('boo_sign'):
        f['sign'] = f['boo_sign']
        try:
            C.draw_figure(cv, f, fr)
        finally:
            f['sign'] = None
        return
    if fr not in BOO_FRAMES or not f['sign']:
        C.draw_figure(cv, f, fr)
        if fr in BOO_FRAMES and f['poses'][fr] not in ('cupB',):
            boo_mouth(cv, f, fr)
        return
    if f['sign'] == 'foam':
        keep = C.FOAM
        C.FOAM = FOAM_DOWN
        try:
            C.draw_figure(cv, f, fr)
        finally:
            C.FOAM = keep
        return
    keep = f['sign']
    f['sign'] = SIGN_FLIP[keep]
    try:
        C.draw_figure(cv, f, fr)
    finally:
        f['sign'] = keep


def render(seed=7, props=C.DEFAULT_PROPS, flash_seed=11, boo_seed=1007):
    rng, figures = C.make_crowd(seed)
    C.assign_animation(rng, figures)
    if props:
        C.place_props(figures, props)
    assign_boo(random.Random(boo_seed), figures)
    frames = []
    frng = random.Random(flash_seed)
    for fr in range(NF):
        cv = [[None] * C.FW for _ in range(C.FH)]
        for ri in range(len(C.ROWS)):
            row_figs = [f for f in figures if f['row'] == ri]
            row_figs.sort(key=lambda f: (f['poses'][fr] is not None, sign_on(f, fr) is not None))
            for f in row_figs:
                draw(cv, f, fr)
        if C.N_IDLE <= fr < C.NF:          # camera flashes on the cheer only
            C.flashes(cv, frng, 5, avoid=[(245, 0, 395, 40)])
        C.fade_bottom(cv)
        frames.append(cv)
    return figures, frames


def to_image(frames):
    from PIL import Image
    im = Image.new("RGBA", (C.FW * len(frames), C.FH))
    px = []
    for y in range(C.FH):
        for fr in frames:
            px.extend((c[0], c[1], c[2], 255) if c is not None else (0, 0, 0, 0) for c in fr[y])
    im.putdata(px)
    return im


def refuse_assets(path):
    assets = os.path.realpath(os.path.join(HERE, "..", "..", "Assets"))
    p = os.path.realpath(path)
    if p == assets or p.startswith(assets + os.sep):
        raise SystemExit(f"refusing to write into Assets ({path}); build_ship.py --ship ships")


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="folder to write crowd_v3.png into")
    args = ap.parse_args()
    refuse_assets(args.out)
    os.makedirs(args.out, exist_ok=True)
    figures, frames = render()
    to_image(frames).save(os.path.join(args.out, NAME))
    print('figures', len(figures), 'frames', len(frames), 'wrote', os.path.join(args.out, NAME))
