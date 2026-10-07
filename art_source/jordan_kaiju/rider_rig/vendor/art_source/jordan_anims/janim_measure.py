"""Layout numbers for Jordan's fight sheets, measured off the parts each frame was built from (the
head, the box, the hands, the fist, the pop), not guessed from the finished pixels.

    python janim_measure.py

Texels are on one 96x96 frame, origin top-left. The anchor texel is (48, 95): the body's centre
column and the row his soles stand on. "px" offsets are (texel - anchor) * 3, the game's scale, the
same convention as JoshArtLayout (e.g. its TELL_ANCHOR). Writes nothing.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import janim_base as B  # noqa: E402
import janim_export  # noqa: E402

ANCHOR = (48, 95)
SCALE = 3


def px_off(p):
    return (int(round((p[0] - ANCHOR[0]) * SCALE)), int(round((p[1] - ANCHOR[1]) * SCALE)))


def rect(bb):
    return 'Rect2(%d, %d, %d, %d)' % (bb[0], bb[1], bb[2] - bb[0] + 1, bb[3] - bb[1] + 1)


def centre(pts):
    x0, y0, x1, y1 = B.bbox(pts)
    return ((x0 + x1 + 1) / 2.0, (y0 + y1 + 1) / 2.0)


def top_of(pts):
    """The highest texel of a part (the middle one if its top row has several)."""
    y = min(yy for (_x, yy) in pts)
    xs = sorted(x for (x, yy) in pts if yy == y)
    return (xs[len(xs) // 2], y)


def body_pixels(px, fx, info):
    """The figure alone: everything drawn minus the box, the pop, its star and any sparkles; the
    hands are put back (they lie over the box)."""
    drop = set(fx)
    for key in ('box', 'pop', 'star', 'glint'):
        if key in info:
            drop |= set(info[key])
    keep = {q for q in px if q not in drop}
    for key in ('hand_near', 'hand_far', 'fist'):
        if key in info:
            keep |= {q for q in info[key] if q in px}
    return keep


def report():
    lines = []
    for mod in janim_export.MODULES:
        fr = mod.frames_info()
        lines.append('%s  (%d frames, times %s, %s)' % (mod.NAME, len(fr), mod.TIMES,
                                                      'loops' if mod.LOOP else 'once'))
        ub, ud = None, None
        for i, (px, fx, info) in enumerate(fr):
            body = body_pixels(px, fx, info)
            bb = B.bbox(body)
            db = B.bbox(px)
            ub = bb if ub is None else (min(ub[0], bb[0]), min(ub[1], bb[1]), max(ub[2], bb[2]), max(ub[3], bb[3]))
            ud = db if ud is None else (min(ud[0], db[0]), min(ud[1], db[1]), max(ud[2], db[2]), max(ud[3], db[3]))
            head = set(info['head'])
            ht = top_of(head)
            hb = B.bbox(head)
            hc = ((hb[0] + hb[2] + 1) / 2.0, ht[1])
            crown = (int(hc[0] + 0.5), ht[1])   # JordanArtLayout's CROWN: head's centre column, quiff-tip row
            s = '  f%d  body %s  drawn %s  head %s  quiff tip %s  crown %s' % (i, rect(bb), rect(db), rect(hb), ht,
                                                                            crown)
            lines.append(s)
            extras = []
            if 'box' in info:
                bc = centre(info['box'])
                extras.append('box centre (%.1f, %.1f) px %s, box %s' % (bc[0], bc[1], px_off(bc), rect(B.bbox(info['box']))))
            for key in ('hand_near', 'hand_far', 'fist'):
                if key in info:
                    c = centre(info[key])
                    extras.append('%s (%.1f, %.1f) px %s' % (key, c[0], c[1], px_off(c)))
            if 'fist' in info:
                t = top_of(info['fist'])
                extras.append('fist top %s px %s' % (t, px_off(t)))
            if 'pop' in info:
                c = centre(info['pop'])
                extras.append('pop centre (%.1f, %.1f) px %s, pop %s' % (c[0], c[1], px_off(c), rect(B.bbox(info['pop']))))
            if 'star' in info:
                c = centre(info['star'])
                extras.append('star centre (%.1f, %.1f) px %s' % (c[0], c[1], px_off(c)))
            if 'glint' in info:
                c = centre(info['glint'])
                extras.append('glint (%.1f, %.1f)' % c)
            for e in extras:
                lines.append('        ' + e)
        lines.append('  union: body %s  drawn %s' % (rect(ub), rect(ud)))
        lines.append('')
    return '\n'.join(lines)


if __name__ == '__main__':
    print(report())
