"""Shared bits for the Elemental Wheel approval pass (scratch only)."""
import os, sys, copy
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, 'liam_rig'), os.path.join(HERE, 'pup_rig')):
    if p not in sys.path:
        sys.path.insert(0, p)
sys.dont_write_bytecode = True
import guard  # noqa: F401  (refuses any write into the live project)
import numpy as np
from PIL import Image
import jp_core as C
import jp_palette as PAL
import jp_bosses as JB

PROJECT = r'C:/Users/theyi/OneDrive/Documents/new-game-project'
CHARS = PROJECT + '/Assets/Characters'
GE = os.path.dirname(HERE)
OUT = os.path.join(GE, 'approval')
LOOK = os.path.join(GE, 'look')
TAKE = 'B'
PUP = PAL.colours(TAKE)
HOT = (0xD2, 0xF6, 0xFF, 255)          # the strings' hot texel (JordanGodLayout.STRING_COLORS.hot)
G1, G2 = PUP['G1'], PUP['G2']


def hx(s):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


def shift_boss(b, dx, dy, name=None):
    """A copy of a recipe boss with every key-frame coordinate moved by (dx, dy): for a frame that holds
    his key figure padded into a bigger cell."""
    nb = copy.copy(b)
    nb.name = name or b.name
    nb.parts = {k: dict(v, box=(v['box'][0] + dx, v['box'][1] + dy, v['box'][2] + dx, v['box'][3] + dy))
                for k, v in b.parts.items()}
    nb.overlays = [dict(o, px={(x + dx, y + dy): c for (x, y), c in o['px'].items()}) for o in b.overlays]
    nb.hooks = {k: dict(v, at=(v['at'][0] + dx, v['at'][1] + dy)) for k, v in b.hooks.items()}
    nb.regions = [dict(r, boxes=[(x0 + dx, y0 + dy, x1 + dx, y1 + dy) for (x0, y0, x1, y1) in r['boxes']])
                  for r in b.regions]
    nb.tatter = []
    for t in b.tatter:
        t = dict(t, centre_x=t['centre_x'] + dx)
        if t.get('rows') is not None:
            t['rows'] = (t['rows'][0] + dy, t['rows'][1] + dy)
        if t.get('cols') is not None:
            t['cols'] = (t['cols'][0] + dx, t['cols'][1] + dx)
        nb.tatter.append(t)
    nb.fx_specks = {(x + dx, y + dy) for (x, y) in b.fx_specks}
    nb.frame_data = {}
    return nb


def pad(a, w, h, ox, oy):
    out = np.zeros((h, w, 4), np.uint8)
    out[oy:oy + a.shape[0], ox:ox + a.shape[1]] = a
    return out


def stats(a):
    op = a[:, :, 3] > 0
    semi = int(((a[:, :, 3] > 0) & (a[:, :, 3] < 255)).sum())
    black = int((op & (a[:, :, 0] == 0) & (a[:, :, 1] == 0) & (a[:, :, 2] == 0)).sum())
    cols = {tuple(c) for c in a[op].tolist()}
    return {'opaque': int(op.sum()), 'black': black / max(1, int(op.sum())), 'colours': len(cols), 'semi': semi,
            'cols': cols}


def up(im, s, bg=(46, 49, 58, 255)):
    b = Image.new('RGBA', im.size, bg)
    b.alpha_composite(im.convert('RGBA'))
    return b.resize((im.width * s, im.height * s), Image.NEAREST)


def strip(frames):
    fw, fh = frames[0].shape[1], frames[0].shape[0]
    out = np.zeros((fh, fw * len(frames), 4), np.uint8)
    for i, f in enumerate(frames):
        out[:, i * fw:(i + 1) * fw] = f
    return out
