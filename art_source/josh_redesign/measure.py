"""Layout numbers for JoshArtLayout.gd, measured off the finished ground frames."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anims_ground as ag
import ground_kit as gk
import josh3, rig


def blobs(px):
    seen, out = set(), []
    for p in px:
        if p in seen:
            continue
        stack, blob = [p], []
        seen.add(p)
        while stack:
            q = stack.pop()
            blob.append(q)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    r = (q[0] + dx, q[1] + dy)
                    if r in px and r not in seen:
                        seen.add(r)
                        stack.append(r)
        out.append(blob)
    return out


def bbox(pts):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def solid(px, min_blob=12):
    keep = [q for b in blobs(px) if len(b) >= min_blob for q in b]
    return bbox(keep)


def rect2(b):
    return 'Rect2(%d, %d, %d, %d)' % (b[0], b[1], b[2] - b[0] + 1, b[3] - b[1] + 1)


if __name__ == '__main__':
    # TELL_ANCHOR: the crown of the hat on the throw wind-up (the frame the tell stands over)
    f0 = ag.frame('josh_throw', 0)
    hat_rows = [y for (x, y), k in f0.items() if y < 16 and 30 <= x <= 50]
    crown_top = min(hat_rows)
    xs = [x for (x, y) in f0 if y == crown_top and 30 <= x <= 50]
    print('TELL_ANCHOR: throw f0 crown top row %d, x %d..%d' % (crown_top, min(xs), max(xs)))
    for i in range(4):
        fr = ag.frame('josh_throw', i)
        print('   throw f%d top row %d' % (i, min(y for (x, y) in fr)))
    # DAZE_ANCHOR: the crown of the hat on the recovery frames
    for i in range(4):
        fr = ag.frame('josh_recovery', i)
        top = min(y for (x, y) in fr if 25 <= x <= 70)
        xs = sorted(x for (x, y) in fr if y == top and 25 <= x <= 70)
        # the crown's own top keyline: the hat part's highest run
        print('   recovery f%d top row %d at x %s' % (i, top, xs))
    # RECOVER_BODY_BOX: the hunched mass (largest connected piece) over the four frames
    boxes = []
    for i in range(4):
        fr = ag.frame('josh_recovery', i)
        big = max(blobs(fr), key=len)
        boxes.append(bbox(big))
    u = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
    print('RECOVER_BODY_BOX: per frame', boxes, ' union', rect2(u))
    # HAND_THROW
    f1 = ag.frame('josh_throw', 1)
    print('HAND_THROW check: (70,45)=%s (71,45)=%s (72,45)=%s (73,45)=%s  (71,44)=%s (72,44)=%s' % tuple(
        f1.get(q, '.') for q in ((70, 45), (71, 45), (72, 45), (73, 45), (71, 44), (72, 44))))
    # BODY_DRAWN over every ground and ride sheet frame
    allb, raw = [], []
    for name, (fn, n, t) in ag.SHEETS.items():
        for i in range(n):
            fr = ag.frame(name, i)
            allb.append(solid(fr))
            raw.append(bbox(list(fr)))
            print('   %-15s f%d solid %s raw %s' % (name, i, solid(fr), bbox(list(fr))))
    u = (min(b[0] for b in allb), min(b[1] for b in allb), max(b[2] for b in allb), max(b[3] for b in allb))
    r = (min(b[0] for b in raw), min(b[1] for b in raw), max(b[2] for b in raw), max(b[3] for b in raw))
    print('BODY_DRAWN (solid, blobs >= 12 px):', rect2(u), '  raw:', rect2(r))
