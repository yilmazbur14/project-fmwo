"""Lint the frames: detached islands (tiny connected groups of opaque pixels), keyline-less colour
touching transparency (a coloured pixel on the silhouette edge with no keyline outside it), and the
frame margin."""
import frame

POSES = ['up', 'down', 'sig']


def islands(px):
    seen = set()
    out = []
    for p in px:
        if p in seen:
            continue
        comp = []
        stack = [p]
        seen.add(p)
        while stack:
            q = stack.pop()
            comp.append(q)
            x, y = q
            for d in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                r = (x + d[0], y + d[1])
                if r in px and r not in seen:
                    seen.add(r)
                    stack.append(r)
        out.append(comp)
    return out


def bare_edges(px, allow=''):
    """Coloured pixels with a transparent 4-neighbour: the silhouette should be keylined."""
    bad = []
    for (x, y), k in px.items():
        if k == 'k' or k in allow:
            continue
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + d[0], y + d[1]) not in px:
                bad.append(((x, y), k))
                break
    return bad


if __name__ == '__main__':
    for pose in POSES:
        cv = frame.build(pose, frame.BOB[pose])
        comps = islands(cv.px)
        small = [c for c in comps if len(c) < 6]
        print('%-5s components %d, small islands (<6px): %s' % (pose, len(comps),
              [(min(c), len(c), sorted({cv.px[q] for q in c})) for c in small][:30]))
        be = bare_edges(cv.px, allow='uvPY' if pose == 'sig' else '')
        print('      unkeylined edge pixels: %d  %s' % (len(be), be[:40]))
        xs = [p[0] for p in cv.px]
        ys = [p[1] for p in cv.px]
        print('      extent x %d..%d  y %d..%d' % (min(xs), max(xs), min(ys), max(ys)))
