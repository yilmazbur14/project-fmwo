"""BIXBY'S BITE (new): 5 frames of 192x160, anchor (96, 151), facing down the screen as hover and perch are.
f0 rears back, f1 starts the lunge, f2 the lunge (jaws wide, the whole front thrown down at the player),
f3 SNAP (the contact frame: the middle head's jaws clamped shut), f4 recoils.

Built in his OWN palette from his approved hover frame (bixby_beast f0), then through the puppet recipe like
every sheet of his: his upper body (heads, wings, collar, chest - every row above the legs) moves as one,
down for the lunge and up for the rear (the legs' tops stretched to meet it), so his feet stay planted on the
anchor and nothing tears. The SNAP's closed jaws are a hand-drawn patch over his middle head's mouth: the
upper fangs biting down over a closed lower jaw, the tongue gone, his throat fur and collar under the chin.
"""
from ge_common import *
import bixby_full as BF
import bixby_puppet as BP

SRC = 'Bixby/bixby_beast.png'
FW, FH = 192, 160
SPLIT = 114                      # the first row that stays: his legs below it are planted
# per frame: how far his upper body moves (+ down), and the JAWS point's offset from its hover spot
SHIFTS = [-4, 3, 8, 10, -2]
JAWS_HOVER = (96, 65)            # hover f0: the middle head's jaw centre (between the fangs, in the throat)
JAWS_SNAP = (96, 63)             # on the closed patch: the bite line
TIMES = [0.15, 0.10, 0.15, 0.06, 0.20]

LEG = {'#': '000000', 'a': '87151F', 'b': '570C18', 'c': 'DE4E2C', 'd': 'B42424', 'e': 'E3D2BC', 'f': 'FFF6E6',
       'h': 'B09A8E', 't': '74606E', 's': '6E1230', 'u': '3E0A1E', 'g': '2C0610'}

LEG.update({'r': 'A4203E', 'v': 'FFE488', 'w': 'A66C1A', 'x': 'E0A632', 'j': '120D16'})


def apply_patch(src):
    """The SNAP's clamped jaws, drawn over the hover frame's open mouth (x 78..113, rows 56..101):
    1. the open mouth and the hanging tongue repainted as his throat fur (his jowl fur's own strands) down to
       his collar, and the collar carried on across under the chin with its gold studs;
    2. the closed muzzle traced on top: the upper muzzle, a band of clenched teeth between black lips that
       curl down at the corners (a snarl), the long upper fangs over the lower lip, the chin tucked under."""
    import le_rig as R
    H_, W_ = src.shape[:2]
    cv = R.blank(W_, H_)
    X_, Y_ = R.centres(W_, H_)
    mouth = R.poly_mask([(81, 57), (111, 57), (113, 70), (112, 86), (106, 93), (98, 101), (86, 101), (80, 92), (79, 72)], W_, H_)
    # 1. throat fur: base, a darker strand every third column, a black strand now and then; shadow under the chin
    XX_, YY_ = np.floor(X_).astype(int), np.floor(Y_).astype(int)
    wig = (XX_ + (YY_ // 4) + (XX_ // 5)) % 4
    lit = ((X_ - 96) / 13.0) ** 2 + ((Y_ - 80) / 7.0) ** 2 < 1.0
    fur = np.where(wig == 0, 'b', np.where(lit & (wig == 2), 'd', 'a'))
    strand = ((XX_ * 7 + (YY_ // 6) * 3) % 11 == 0) & (YY_ % 6 != 5)
    fur = np.where(strand, '#', fur)
    fur = np.where((Y_ < 74) | (Y_ > 85), np.where(fur == '#', '#', 'b'), fur)
    cv[mouth] = fur[mouth]
    collar = mouth & (Y_ > 87)
    cv[collar] = 's'
    cv[mouth & (Y_ > 87) & (Y_ < 89)] = '#'
    cv[mouth & (Y_ > 89) & (Y_ < 90)] = 'r'
    cv[mouth & (Y_ > 97)] = 'u'
    for sx in (84, 92, 100):                                   # gold studs on the collar
        for (dx, dy, c) in ((0, 0, 'x'), (1, 0, 'v'), (0, 1, 'w'), (1, 1, 'x'), (0, 2, 'w')):
            if mouth[93 + dy, sx + dx]:
                cv[93 + dy, sx + dx] = c
    # 2. the closed muzzle
    up = R.ellipse_mask(96, 59.5, 13.0, 5.5, W_, H_) & (Y_ > 56)
    nx, ny, nz = R.sphere_normal(X_, Y_, 94.5, 57.0, 15.0, 9.0)
    sh = R.quant(R.lambert((nx, ny, nz), wrap=0.3), 'thef', [0.25, 0.55, 0.9])
    R.paint_part(cv, up, sh)
    chin = R.ellipse_mask(96, 67.5, 9.5, 4.0, W_, H_) & (Y_ > 64)
    nx, ny, nz = R.sphere_normal(X_, Y_, 95.0, 65.0, 11.0, 6.0)
    R.paint_part(cv, chin, R.quant(R.lambert((nx, ny, nz), wrap=0.2), 'the', [0.3, 0.6]))
    # the teeth band between the lips: upper teeth, the bite, lower teeth; the lips curl down at the corners
    for y, row in ((62, '###################'), (63, '#ffhffhffhffhffhff#'), (64, '#hfffhfffhfffhfffh#'),
                   (65, '###################'), (66, '#ffhffhffhffhffhff#'), (67, '###################')):
        for i, ch in enumerate(row):
            cv[y, 87 + i] = ch
    for (x, y) in ((86, 62), (85, 63), (85, 64), (106, 62), (107, 63), (107, 64)):
        cv[y, x] = '#'
    # the long upper fangs, hanging over the lower lip at each corner
    for fx in (88, 104):
        for y, w in ((63, 2), (64, 2), (65, 2), (66, 2), (67, 2), (68, 1)):
            for i in range(w):
                cv[y, fx + i] = 'f' if i == 0 or y < 66 else 'h'
        cv[69, fx] = '#'
        cv[68, fx + 1] = '#'
        cv[68, fx - 1] = '#'
        for y in range(63, 69):
            if cv[y, fx - 1] not in 'f':
                cv[y, fx - 1] = '#'
            if cv[y, fx + 2] not in 'f':
                cv[y, fx + 2] = '#'
    a = src.copy()
    for y, x in zip(*np.nonzero(cv != '.')):
        h = LEG[cv[y, x]]
        a[y, x] = (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)
    return a


def move_upper(src, k):
    """His upper body (rows < SPLIT) moved k rows (+ down); his planted legs stay. Down: the body covers the
    legs' tops. Up: the legs' top row is repeated to meet it."""
    out = np.zeros_like(src)
    lower = src.copy()
    lower[:SPLIT] = 0
    upper = src.copy()
    upper[SPLIT:] = 0
    out[:] = lower
    if k < 0:
        for j in range(-k):
            out[SPLIT - 1 - j] = np.where(src[SPLIT, :, 3:4] > 0, src[SPLIT], out[SPLIT - 1 - j])
    sh = np.zeros_like(src)
    if k >= 0:
        sh[k:] = upper[:FH - k]
    else:
        sh[:FH + k] = upper[-k:]
    m = sh[:, :, 3] > 0
    out[m] = sh[m]
    return out


def speed_lines(a, k):
    """Lunge streaks: short vertical motion lines over his crown, in his own pale cream (FX: no keyline)."""
    c = (0xFF, 0xF6, 0xE6, 255)
    for x, y0, n in ((70, 2, 5), (84, 0, 4), (110, 0, 4), (124, 2, 5), (60, 10, 3), (134, 10, 3)):
        for j in range(n):
            y = y0 + j + max(0, k - 8)
            if 0 <= y < FH and a[y, x, 3] == 0:
                a[y, x] = c
    return a


def snap_ticks(a, jaws):
    """The SNAP: three short impact ticks either side of the clamped jaws (FX, his cream)."""
    c = (0xFF, 0xF6, 0xE6, 255)
    jx, jy = jaws
    for (dx, dy) in ((-17, -4), (-18, 0), (-17, 4), (17, -4), (18, 0), (17, 4)):
        for t in range(3):
            x = jx + dx + (t if dx > 0 else -t)
            y = jy + dy
            if 0 <= x < FW and 0 <= y < FH and a[y, x, 3] == 0:
                a[y, x] = c
    return a


def sources():
    hover = C.frame(SRC, FW, FH, 0)
    out, jaws = [], []
    for f, k in enumerate(SHIFTS):
        base = apply_patch(hover) if f == 3 else hover
        a = move_upper(base, k)
        j = (JAWS_SNAP[0], JAWS_SNAP[1] + k) if f == 3 else (JAWS_HOVER[0], JAWS_HOVER[1] + k)
        if f == 2:
            a = speed_lines(a, k)
        if f == 3:
            a = snap_ticks(a, j)
        out.append(a)
        jaws.append(j)
    return out, jaws


def build():
    srcs, jaws = sources()
    saved = {k: dict(v) for k, v in BP.PARTS.items()}
    for v in BP.PARTS.values():
        v['radius'] = 14
    try:
        key = C.frame(BP.SHEET, 192, 160, 0)
        first = [BF.treat_frame('bixby_bite', s, f, key) for f, s in enumerate(srcs)]
        everywhere = set.intersection(*[set(i.get('rings_drawn', [])) for _a, i in first])
        out, infos = [], []
        for f, s in enumerate(srcs):
            skip = tuple(sorted(set(first[f][1].get('rings_drawn', [])) - everywhere))
            back = BF.plate_back(s)
            a, info = BF.treat_frame('bixby_bite', s, f, key, skip_rings=skip, back_by_hand=back)
            info['rings_left_off_sheet'] = list(skip)
            info['ember'] = False
            info['jaws'] = jaws[f]
            out.append(a)
            infos.append(info)
    finally:
        for k, v in saved.items():
            BP.PARTS[k].update(v)
    return out, infos, srcs


if __name__ == '__main__':
    frames, infos, srcs = build()
    print('problems', BF.audit(frames, infos))
    print('back', BF.back_points(infos, 'bixby_bite'), 'jaws', [i['jaws'] for i in infos],
          'rings', [i.get('rings_drawn') for i in infos][0])
    up(Image.fromarray(strip(srcs), 'RGBA'), 3, (14, 10, 24, 255)).save(os.path.join(LOOK, 'bite_src_3x.png'))
    up(Image.fromarray(strip(frames), 'RGBA'), 3, (14, 10, 24, 255)).save(os.path.join(LOOK, 'bite_3x.png'))
