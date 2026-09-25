"""The numbers a juggle frame has to hit, measured the same way on the approved beast sheets.

  keyline   share of drawn texels that are pure #000000
  colours   distinct colours drawn
  ramps     for each material ramp (fur, charcoal, bone, membrane) the share of each tone, dark to light
  light     for each ramp, the mean tone (0 darkest .. 1 lightest) of texels whose upper neighbour is
            outline or empty, minus the same for texels whose lower neighbour is: positive means lit
            from above. A body turned without relighting goes negative here, which is the trap.
"""
import os
from collections import Counter

import numpy as np
from PIL import Image

import jcommon as C
from pal import PAL

# the approved sheets built from the same rig (Assets/Characters/Bixby), and their frame size
APPROVED = [('bixby_beast.png', 192, 160), ('bixby_beast_hit.png', 192, 160),
            ('bixby_beast_recover.png', 192, 160), ('bixby_dizzy.png', 192, 160),
            ('bixby_beast_land.png', 192, 160), ('bixby_beast_takeoff.png', 192, 160),
            ('bixby_beast_roar.png', 192, 160), ('bixby_beast_fly.png', 192, 160),
            ('bixby_pound.png', 192, 160)]

RAMPS = {
    'fur': 'qrstu',
    'charcoal': 'abcd',
    'bone': 'zyxw',
    'membrane': 'ABC',
}
BLACK = (0, 0, 0)
RGB = {k: v[:3] for k, v in PAL.items()}
TONE = {}
for name, keys in RAMPS.items():
    for i, k in enumerate(keys):
        TONE[RGB[k]] = (name, i / (len(keys) - 1))


def frames_of(path, fw, fh):
    im = Image.open(path).convert('RGBA')
    return [im.crop((i * fw, 0, (i + 1) * fw, fh)) for i in range(im.width // fw)]


def measure(im):
    a = np.array(im.convert('RGBA'))
    op = a[:, :, 3] > 0
    n = int(op.sum())
    cols = Counter(tuple(int(v) for v in a[y, x, :3]) for y, x in zip(*np.nonzero(op)))
    semi = int(((a[:, :, 3] > 0) & (a[:, :, 3] < 255)).sum())
    black = cols.get(BLACK, 0)
    ramps = {}
    for name, keys in RAMPS.items():
        counts = [cols.get(RGB[k], 0) for k in keys]
        tot = sum(counts)
        ramps[name] = [c / tot if tot else 0.0 for c in counts]
    # light: tone of texels facing up vs facing down (their neighbour above/below is black or empty)
    h, w = op.shape
    up_t, dn_t = {k: [] for k in RAMPS}, {k: [] for k in RAMPS}
    for y in range(h):
        for x in range(w):
            if not op[y, x]:
                continue
            t = TONE.get(tuple(int(v) for v in a[y, x, :3]))
            if t is None:
                continue
            name, v = t

            def outline(yy):
                return not (0 <= yy < h) or not op[yy, x] or tuple(int(c) for c in a[yy, x, :3]) == BLACK
            if outline(y - 1) and not outline(y + 1):
                up_t[name].append(v)
            elif outline(y + 1) and not outline(y - 1):
                dn_t[name].append(v)
    light = {}
    for name in RAMPS:
        if len(up_t[name]) > 20 and len(dn_t[name]) > 20:
            light[name] = float(np.mean(up_t[name]) - np.mean(dn_t[name]))
        else:
            light[name] = None
    return dict(opaque=n, colours=len(cols), keyline=black / max(1, n), semi=semi, ramps=ramps, light=light,
                palette=set(cols))


def approved_frames():
    out = []
    for name, fw, fh in APPROVED:
        p = os.path.join(C.BIXBY, name)
        for i, f in enumerate(frames_of(p, fw, fh)):
            out.append(('%s[%d]' % (name.replace('.png', ''), i), f))
    return out


def baseline():
    """Per-frame ranges over the approved sheets, and their union palette."""
    rows = [(n, measure(f)) for n, f in approved_frames()]
    pal = set()
    for _, m in rows:
        pal |= m['palette']
    return rows, pal


def fmt(m):
    r = m['ramps']
    lt = m['light']
    return ('key %5.2f%%  col %2d  fur %s  char %s  bone %s  mem %s  light fur %+.2f char %+.2f bone %+.2f'
            % (100 * m['keyline'], m['colours'],
               '/'.join('%2d' % round(100 * v) for v in r['fur']),
               '/'.join('%2d' % round(100 * v) for v in r['charcoal']),
               '/'.join('%2d' % round(100 * v) for v in r['bone']),
               '/'.join('%2d' % round(100 * v) for v in r['membrane']),
               lt['fur'] or 0, lt['charcoal'] or 0, lt['bone'] or 0))


if __name__ == '__main__':
    rows, pal = baseline()
    for n, m in rows:
        print('%-28s %s' % (n, fmt(m)))
    print('approved palette: %d colours' % len(pal))
