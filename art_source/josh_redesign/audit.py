"""Keyline audit: body-colour pixels that touch transparency (a missing keyline), and lone pixels."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import josh3, lib
BODY = set('abcdehijlmwxyzZvVRTnNsStp5678') | set('9')   # '0' excluded: cream highlights sit on edges inside keylines only
FX = set('WYOorGg')

def audit(px, label=''):
    gaps = []
    lone = []
    for (x, y), k in px.items():
        n4 = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        if k in BODY and any(q not in px for q in n4):
            gaps.append((x, y, k))
        n8 = [(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
        if not any(q in px for q in n8):
            lone.append((x, y, k))
    return gaps, lone

if __name__ == '__main__':
    for sig in (False, True):
        g, l = audit(josh3.build_frame(sig).px)
        print('approved', int(sig), 'gaps', len(g), g[:12], 'lone', len(l))
    import anims_ground as ag
    for name, (fn, n, t) in ag.SHEETS.items():
        for i in range(n):
            g, l = audit(ag.frame(name, i))
            if g or l:
                print(name, i, 'gaps', len(g), g[:10], 'lone', len(l), l[:6])


def holes(px):
    """Transparent pixels boxed in by drawn ones on all four sides: a hole the floor would show through."""
    out = []
    xs = [q[0] for q in px]
    ys = [q[1] for q in px]
    for y in range(min(ys), max(ys) + 1):
        for x in range(min(xs), max(xs) + 1):
            if (x, y) not in px and all(q in px for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
                out.append((x, y))
    return out


if __name__ == '__main__':
    import anims_ground as ag
    for name, (fn, n, t) in ag.SHEETS.items():
        for i in range(n):
            h = holes(ag.frame(name, i))
            if h:
                print('HOLES', name, i, h)
    for sig in (False, True):
        print('approved', int(sig), 'holes', holes(josh3.build_frame(sig).px))
