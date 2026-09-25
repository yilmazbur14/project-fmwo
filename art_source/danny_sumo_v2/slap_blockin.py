"""STUDY, not part of the build. Silhouette tests for frame 1's arms on the idle's body (A: a W with
both palms up, B: tsuppari palms at the shoulders, C: one palm cocked high, one driving forward).
C was chosen and drawn in slap.py. Flat fills + keylines."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sumo_lib import Canvas, spoly, capsule, ellipse, view, mirror_pts, mirror_set, MIR  # noqa: E402
import torso as T  # noqa: E402
import danny_v2 as D  # noqa: E402
import limbs as LB  # noqa: E402
from PIL import Image  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else '.'


def palm(cx, cy, s=1.0, thumb=-1):
    """An open palm facing the viewer, fingers up; thumb=-1 puts the thumb on the viewer's left."""
    body = spoly([(cx - 9 * s, cy + 8 * s), (cx - 10 * s, cy), (cx - 8 * s, cy - 6 * s), (cx + 8 * s, cy - 6 * s),
                  (cx + 10 * s, cy), (cx + 8 * s, cy + 8 * s)])
    fingers = [capsule((cx + dx * s, cy - 6 * s), (cx + (dx + lean) * s, cy - (6 + ln) * s), 2.3 * s, 2.1 * s)
               for dx, lean, ln in ((-6, -1.5, 10), (-2, -0.5, 12.5), (2.5, 0.5, 11.5), (6.5, 1.5, 8.5))]
    th = capsule((cx + thumb * 8 * s, cy + 3 * s), (cx + thumb * 14 * s, cy - 5 * s), 2.5 * s, 2.2 * s)
    return [body] + fingers + [th]


def arms_A(cv, flat):
    for side in (1, -1):
        m = (lambda s: s) if side > 0 else mirror_set
        up = m(spoly([(40, 50), (31, 47.5), (22, 44.5), (13, 46), (6, 52), (4, 60), (6.5, 67), (13, 69),
                      (22, 66), (32, 65), (41, 64)]))
        fo = m(spoly([(4.5, 58), (3.5, 48), (5, 40), (9.5, 34), (16, 33.5), (19.5, 38), (19, 47), (16.5, 57),
                      (12.5, 65)]))
        cv.stamp(flat(up, '4'))
        cv.stamp(flat(spoly(LB.DELT if side > 0 else mirror_pts(LB.DELT)), '6'))
        cv.stamp(flat(fo, '5'))
        for p in palm(12.5 if side > 0 else MIR - 12.5, 22, 0.95, thumb=-1 if side > 0 else 1):
            cv.stamp(flat(p, '6'))


def arms_B(cv, flat):
    for side in (1, -1):
        m = (lambda s: s) if side > 0 else mirror_set
        up = m(capsule((30, 58), (16, 84), 11, 9.5))
        fo = m(spoly([(10, 86), (12, 76), (17, 66), (24, 58), (32, 56), (35, 61), (30, 70), (24, 80), (20, 90)]))
        cv.stamp(flat(up, '4'))
        cv.stamp(flat(spoly(LB.DELT if side > 0 else mirror_pts(LB.DELT)), '6'))
        cv.stamp(flat(fo, '5'))
        for p in palm(34 if side > 0 else MIR - 34, 50, 1.0, thumb=-1 if side > 0 else 1):
            cv.stamp(flat(p, '6'))


def arms_C(cv, flat):
    # viewer's left: cocked high beside the head; viewer's right: thrust low towards the viewer
    up = spoly([(40, 50), (31, 47.5), (22, 44.5), (13, 46), (6, 52), (4, 60), (6.5, 67), (13, 69), (22, 66),
                (32, 65), (41, 64)])
    fo = spoly([(4.5, 58), (3.5, 48), (5, 40), (9.5, 34), (16, 33.5), (19.5, 38), (19, 47), (16.5, 57), (12.5, 65)])
    cv.stamp(flat(up, '4'))
    cv.stamp(flat(spoly(LB.DELT), '6'))
    cv.stamp(flat(fo, '5'))
    for p in palm(12.5, 22, 0.95, thumb=-1):
        cv.stamp(flat(p, '6'))
    up = mirror_set(capsule((30, 58), (18, 80), 11, 9.5))
    cv.stamp(flat(up, '4'))
    cv.stamp(flat(spoly(mirror_pts(LB.DELT)), '6'))
    fo = spoly([(150, 78), (140, 82), (130, 84), (124, 80), (130, 74), (142, 72)])
    cv.stamp(flat(fo, '5'))
    for p in palm(120, 78, 1.35, thumb=-1):
        cv.stamp(flat(p, '6'))


def build(arms):
    cv = Canvas()
    flat = lambda s, k: {p: k for p in s}  # noqa: E731
    for side in (1, -1):
        cv.stamp(flat(spoly(LB.CALF if side > 0 else mirror_pts(LB.CALF)), '4'))
        cv.stamp(flat(spoly(LB.THIGH if side > 0 else mirror_pts(LB.THIGH)), '5'))
        cv.stamp(flat(spoly(LB.FOOT if side > 0 else mirror_pts(LB.FOOT)), '6'))
    cv.stamp(flat(spoly(D.sym(D.BELT)), 'w'))
    cv.stamp(flat(T.mask(), '6'))
    arms(cv, flat)
    cv.stamp(flat(spoly(D.sym(D.FACE)), '6'))
    cv.stamp(flat(spoly(D.sym(D.CROWN)), 'w'))
    cv.stamp(flat(spoly(D.sym(D.CUFF), 1), 'B'))
    return cv.image()


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    tiles = []
    for a in (arms_A, arms_B, arms_C):
        im = build(a)
        sil = Image.new('RGBA', im.size, (200, 200, 205, 255))
        sil.paste((20, 20, 20, 255), (0, 0), im.getchannel('A'))
        tiles += [im, sil]
    sheet = Image.new('RGBA', (3 * 180, 2 * 148), (46, 49, 58, 255))
    for i, t in enumerate(tiles):
        sheet.alpha_composite(t, ((i // 2) * 180, (i % 2) * 148))
    view(sheet, 2, os.path.join(OUT, 'slap_options.png'))
