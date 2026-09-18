"""Every number that moved when Carter was drawn smaller.

Renders the old size (scale 1.0) and the new one (carter_scale.SCALE) from the
same rig and prints both, so the derived work - the half-scale clones, the
punchable hitbox, the daze and parry-tell anchors, the menu tower crop and the
ladder icon - can be re-measured against real figures rather than a ratio.

    python measure_scale.py [scratch_dir]
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import lib
from pngio import read_png, write_png, crop
import carter_scale

A = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..', 'Assets', 'Characters', 'Carter'))
SCRATCH = sys.argv[1] if len(sys.argv) > 1 else '.'
W = H = 96
SCENE = 3          # boss Sprite2D scale in CarterAkumaScene.tscn

SHEETS = [('carter_akuma.png', 3), ('carter_idle.png', 4),
          ('carter_eye_flash.png', 4), ('carter_rush.png', 4),
          ('carter_rush_pass.png', 3), ('carter_spent.png', 4),
          ('carter_hit.png', 2), ('carter_defeat.png', 6),
          ('carter_victory.png', 7)]

BODY = None


def body_set():
    global BODY
    if BODY is None:
        from lib import RAMPS, hexc, GI_STEPS
        BODY = set(hexc(c) for r in ('skin', 'skinr', 'hair', 'gi', 'rope',
                                     'belt', 'bead', 'steel') for c in RAMPS[r])
        BODY |= set(c for s in GI_STEPS for c in s)
    return BODY


def skin_set():
    from lib import RAMPS, hexc
    return set(hexc(c) for c in RAMPS['skin'] + RAMPS['skinr'])


def bbox(f, pal=None):
    pts = [(x, y) for y in range(H) for x in range(W)
           if f[y][x][3] and (pal is None or tuple(f[y][x]) in pal)]
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def report():
    sk = skin_set()
    bd = body_set()
    print('sheet                    fr  content bbox        body bbox           '
          'skull top  head cx   drawn h  on screen')
    for name, n in SHEETS:
        w, h, px = read_png(os.path.join(A, name))
        for i in range(n):
            f = crop(px, i * W, 0, W, H)
            cb = bbox(f)
            bb = bbox(f, bd)
            skp = [(x, y) for y in range(H) for x in range(W)
                   if tuple(f[y][x]) in sk]
            top = min(y for _, y in skp)
            row = [x for x, y in skp if y <= top + 3]
            cx = (min(row) + max(row)) // 2
            print('%-24s f%d  x%2d..%-2d y%2d..%-2d  x%2d..%-2d y%2d..%-2d  '
                  '%3d       %3d      %3d      %3dpx'
                  % (name, i, cb[0], cb[2], cb[1], cb[3],
                     bb[0], bb[2], bb[1], bb[3], top, cx,
                     cb[3] - cb[1] + 1, (cb[3] - cb[1] + 1) * SCENE))
    # overlays, whose own canvases are derived from the sigil's bounding box
    for nm in ('carter_aura.png', 'carter_mark_glow.png',
               'carter_intro_flash.png', 'carter_intro.png'):
        w, h, px = read_png(os.path.join(A, nm))
        print('%-24s sheet %dx%d' % (nm, w, h))


def impacts():
    import combat_rush as CR
    print()
    print('rush strike contact, frame-local pixel and offset from feet-centre')
    for i, (dx, dy) in enumerate(CR.IMPACT):
        px, py = lib.Tp(dx, dy)
        print('   f%d  design (%2d,%2d) -> pixel (%2d,%2d)   offset (%+d,%+d) at 3x'
              % (i, dx, dy, px, py, (px - 47.5) * SCENE, (py - 95) * SCENE))


def anchors():
    import combat_rush as CR
    import combat_poses as CP
    print()
    print('light / badge anchor above the head, frame-local pixel')
    sets = [('carter_idle', [(0, 0), (0, -1), (0, -1), (0, 0)]),
            ('carter_eye_flash', [(0, s['dy']) for s in CP.FLASH]),
            ('carter_rush', [p['head'] for p in CR.RUSH]),
            ('carter_rush_pass', [p['head'] for p in CP.PASS]),
            ('carter_spent', [p['head'] for p in CP.SPENT]),
            ('carter_defeat', [p['head'] for p in CP.DEFEAT])]
    for nm, heads in sets:
        out = []
        for dx, dy in heads:
            x, y = lib.Tp(47.5 + dx, 11.0 + dy)
            out.append('(%d,%d)' % (x, max(0, y - 6)))
        print('   %-18s %s' % (nm, ' '.join(out)))


if __name__ == '__main__':
    carter_scale.apply()
    print('SCALE = %.2f about %s' % (lib.SCALE, lib.ANCHOR))
    print()
    report()
    impacts()
    anchors()
