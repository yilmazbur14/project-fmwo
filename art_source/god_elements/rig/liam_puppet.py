"""Liam's puppet in the AVATAR STATE: the two float frames (liam_avatar, his own palette and rig) through the
approved puppet treatment (the scratch copy of jp_core / jp_bosses, take B), then the Avatar State on top:
blazing lenses, Aang-style arrow markings burning rune-blue on his head and forearms, and (the surge) a
glowing mouth. Every Avatar pixel recolours a pixel INSIDE the silhouette (the twin rule)."""
import math
from ge_common import *
import le_rig as R
import le_poses as P
import liam_avatar as LA

BX, BY = LA.BX, LA.BY
FW = FH = 96
SHEET = 'Liam/liam_puppet_avatar.png'      # a virtual sheet name: the hand-set hooks are keyed on it

# the arms' geometry, per frame (body coords): (elbow, wrist) for each forearm, as liam_avatar draws them
FORE = {0: {'far': ((4, 39), (-2.5, 43.5)), 'near': ((56, 39), (62.5, 43.5))},
        1: {'far': ((5, 23), (0.5, 15)), 'near': ((56, 23), (60.5, 15))}}


def B(x, y):
    return (int(round(x + BX)), int(round(y + BY)))


def boss():
    b = shift_boss(JB.BOSSES['liam'], BX, BY, 'liam_avatar')
    # the hanging legs' hems sit lower than his standing ones: fray them where they are now
    for t in b.tatter:
        t['rows'] = (58 + BY, 63 + BY)
    hooks = {}
    for f, arms in FORE.items():
        h = {}
        for side, name in (('far', 'wrist_l'), ('near', 'wrist_r')):
            (ex, ey), (wx, wy) = arms[side]
            # the point is recorded, the ring left off: the Avatar's arm arrows run down these forearms
            h[name] = (B(ex + 0.78 * (wx - ex), ey + 0.78 * (wy - ey)), None)
        h['knee_l'] = (B(21, 56), JB.RING_S)
        h['knee_r'] = (B(41, 57), JB.RING_S)
        hooks[f] = h
    b.frame_data = {SHEET: {'hooks': hooks}}
    return b


def key_src():
    return pad(C.frame('Liam/liam.png', 64, 64, 0), FW, FH, BX, BY)


def line_px(a, b):
    n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])) * 2) + 1
    out = []
    for i in range(n + 1):
        t = i / n
        p = (int(math.floor(a[0] + (b[0] - a[0]) * t + 0.5)), int(math.floor(a[1] + (b[1] - a[1]) * t + 0.5)))
        if not out or out[-1] != p:
            out.append(p)
    return out


def avatar(img, src_cv, f, sil):
    """The Avatar State over the treated frame (RGBA numpy, edited in place). Returns the pixels touched."""
    touched = {}
    air = np.pad(~sil, 1, constant_values=True)
    edge = sil & (air[:-2, 1:-1] | air[2:, 1:-1] | air[1:-1, :-2] | air[1:-1, 2:])

    def put(x, y, c):
        if 0 <= x < FW and 0 <= y < FH and sil[y, x] and not edge[y, x]:
            img[y, x] = c
            touched[(x, y)] = c
    # 1. the lenses blaze: rune blue with a white-hot core along their middle row
    for lens in (P.LENS_FAR, P.LENS_NEAR):
        xs = sorted({x for x, y in lens})
        for (x, y) in lens:
            fx, fy = B(x, y)
            core = y == 15 and xs[0] < x < xs[-1]
            put(fx, fy, HOT if core else G1)
    # 2. the arrow on his head: down the middle of his crown, over the band's plate, its head on his brow
    for y in range(2, 9):
        put(*B(25, y), G1)
    for (x, y, c) in ((23, 9, G2), (24, 9, G1), (25, 9, HOT), (26, 9, G1), (27, 9, G2),
                      (24, 10, G1), (25, 10, HOT), (26, 10, G1), (25, 11, G1), (25, 12, G1)):
        put(*B(x, y), c)
    # 3. the arrows down his forearms: a burning line along each wrap, white-hot where it reaches his hand
    for side in ('far', 'near'):
        (ex, ey), (wx, wy) = FORE[f][side]
        a = (ex + 0.12 * (wx - ex) + BX, ey + 0.12 * (wy - ey) + BY)
        b_ = (ex + 0.98 * (wx - ex) + BX, ey + 0.98 * (wy - ey) + BY)
        pts = [p for p in line_px(a, b_) if sil[p[1], p[0]] and not edge[p[1], p[0]]]
        for (x, y) in pts:
            put(x, y, G1)
        if pts:
            put(*pts[-1], HOT)
    # 4. the surge: his shout glows from inside (the mouth's dark and tongue, inside the beard's box)
    if f == 1:
        for y in range(20, 27):
            for x in range(16, 40):
                ch = src_cv[y + BY, x + BX]
                if ch == 'N':
                    put(x + BX, y + BY, G2)
                elif ch == 'n':
                    put(x + BX, y + BY, G1)
    return touched


def build():
    b = boss()
    key = key_src()
    cvs = LA.frames()
    frames, infos, avatar_px = [], [], []
    for f, cv in enumerate(cvs):
        src = R.to_rgba(cv)
        im, info = C.treat(b, src, TAKE, key_src=key, sheet_rel=SHEET, frame_no=f)
        a = np.array(im)
        sil = a[:, :, 3] > 0
        avatar_px.append(avatar(a, cv, f, sil))
        frames.append(a)
        info['src'] = src
        infos.append(info)
    return frames, infos, avatar_px


def audit(frames, infos):
    probs = []
    pal = {tuple(v) for v in PUP.values()} | {HOT}
    for f, (a, info) in enumerate(zip(frames, infos)):
        src = info['src']
        if ((a[:, :, 3] > 0) != (src[:, :, 3] > 0)).any():
            probs.append('f%d silhouette differs from its source pose' % f)
        if ((a[:, :, 3] > 0) & (a[:, :, 3] < 255)).any():
            probs.append('f%d semi-alpha' % f)
        cols = {tuple(c) for c in a[a[:, :, 3] > 0].tolist()}
        if cols - pal:
            probs.append('f%d off-palette %s' % (f, sorted(cols - pal)[:4]))
        op = a[:, :, 3] > 0
        air = np.pad(~op, 1, constant_values=True)
        edge = op & (air[:-2, 1:-1] | air[2:, 1:-1] | air[1:-1, :-2] | air[1:-1, 2:])
        nonblack = edge & ((a[:, :, 0] != 0) | (a[:, :, 1] != 0) | (a[:, :, 2] != 0))
        if nonblack.any():
            probs.append('f%d %d keyline px not black' % (f, int(nonblack.sum())))
        for k in ('gaps', 'lone', 'holes', 'bad_keys'):
            if info['lint'][k]:
                probs.append('f%d lint %s %s' % (f, k, info['lint'][k][:4]))
        if info['unknown']:
            probs.append('f%d unmapped %s' % (f, info['unknown']))
    return probs


if __name__ == '__main__':
    frames, infos, av = build()
    for f, info in enumerate(infos):
        print('f%d parts' % f, {k: v for k, v in info['parts'].items()})
        print('   hooks', info['hooks'], 'skipped', info['skipped'], 'tatter', info.get('tatter'), 'nudged', info.get('nudged'))
        print('   stats', {k: v for k, v in stats(frames[f]).items() if k != 'cols'}, 'avatar px', len(av[f]))
    print('PROBLEMS', audit(frames, infos))
    im = Image.fromarray(strip(frames), 'RGBA')
    im.save(os.path.join(LOOK, 'liam_puppet_avatar_draft.png'))
    up(im, 6).save(os.path.join(LOOK, 'liam_puppet_avatar_draft_6x.png'))
