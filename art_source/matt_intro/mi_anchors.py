"""Anchor points for the coder, in frame texels (x right, y down, the frame's top-left is 0,0; his
feet are on row 95 and his centre column is 48).

    crest_top   the highest drawn texel (the tip of the centre spike): where to hang anything
                above his head
    crown       the top of the hair dome under the crest, centred on the head
    mouth       the centre of the mouth: of the open mouth's interior and teeth, or of the lip line
                when it is shut
    doll_hand   the centre of the fist holding Hong (doll frames), set by the frame builders

    python mi_anchors.py      # print every sheet's anchors
"""
import mi_base as B
import mi_fig as F

MOUTH_KEYS = set('mnpqrRWXx')


def face_pixels(f):
    P = f.pose()
    hx, hy = f.head
    rows, x0, y0 = f.face if f.face is not None else (B.rig_face.IDLE, B.rig_face.X0, B.rig_face.IDLE_Y0)
    part = B.amap(rows, x0, y0)
    return {(x + hx, y + hy + P.head_dy): k for (x, y), k in part.items()}, (hx, hy + P.head_dy)


def mouth(f):
    fp, (dx, dy) = face_pixels(f)
    low = 43 + dy
    pts = [p for p, k in fp.items() if k in MOUTH_KEYS and p[1] >= low]
    if not pts:
        pts = [p for p, k in fp.items() if k == 'k' and low <= p[1] <= 48 + dy and 40 + dx <= p[0] <= 57 + dx]
    xs = [x for x, y in pts]
    ys = [y for x, y in pts]
    return ((min(xs) + max(xs)) // 2, (min(ys) + max(ys)) // 2)


def anchors(f, px):
    P = f.pose()
    hx, hy = f.head
    top = min(y for (x, y) in px)
    tx = sorted(x for (x, y) in px if y == top)
    out = {
        'crest_top': (tx[len(tx) // 2], top),
        'crown': (48 + hx, 16 + hy + P.head_dy),
        'mouth': mouth(f),
    }
    out.update(f.anchors)
    return out


def sheet_anchors(mod):
    res = []
    for f in mod.figs():
        res.append(anchors(f, F.px_of(f)))
    return res


if __name__ == '__main__':
    import mi_walk
    import mi_talk
    import mi_doll
    import mi_roar
    for mod in (mi_walk, mi_talk, mi_doll, mi_roar):
        print(mod.NAME)
        for i, a in enumerate(sheet_anchors(mod)):
            print('  f%-2d %s' % (i, '  '.join('%s %s' % (k, v) for k, v in a.items())))
