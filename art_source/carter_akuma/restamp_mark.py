"""Restamp Carter's back mark - Akuma's 天 since 2026-09-23, the trident before
it - onto every sheet that shows it, and prove that nothing else moved.

    python restamp_mark.py              # dry run: render, prove, report
    python restamp_mark.py --write      # ... and write the sheets, if all pass
    python restamp_mark.py --old DIR    # prove against copies of the old files
                                        # in DIR (Demon/ under it for the finish)

The same idea as resigil_approved.py, for every sheet at once.  For each one:

  1. the OLD mark (the trident, its bevelled paint at rest and its dark-edged
     burn) is rendered through the rig and must match the shipped file byte for
     byte.  That proves the rig still reproduces what shipped, so the only
     thing the new render can differ by is the mark;
  2. the NEW mark is rendered through exactly the same calls;
  3. every pixel that differs must lie inside that frame's MARK ZONE: the old
     mark and the new one as that frame draws them - after its own squeeze and
     shift - grown by how far that frame's bloom can reach.  A frame that never
     shows the mark must come back byte-identical.  The mark-glow overlay is the
     mark alone, so all of it is zone; its size, frame count and box are checked
     instead.

Nothing is written unless every sheet passes, and each PNG is written whole to
a side file and moved over the old one in one step, because the game is played
from this checkout.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import carter_scale
carter_scale.apply()
import lib
from lib import W, H, TH_HARD2, PALC, inter, union, grow, empty
from pngio import read_png, write_png, blank, paste

import intro_sigil
import poses as PO
import intro_lib as IL
import intro_frames as IF
import build
import build_intro as BI
import combat_poses as CP
import combat_rush as CR
import combat_victory as CVI
import combat_look as CLK

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.abspath(os.path.join(HERE, '..', '..', 'Assets', 'Characters', 'Carter'))
FX = os.path.abspath(os.path.join(HERE, '..', 'carter_demon_fx'))


# ---------------------------------------------------------------- the two marks

def _old_paint(cv, sg):
    """the trident's bevelled paint, exactly as poses and combat_rush had it"""
    cv.part(sg, 'ember', ('dist', 3.2), TH_HARD2, bias=1)
    cv.outline(sg, PALC['9'])


NEW_PAINT = intro_sigil.paint_rest
NEW_CLOTH = CR.mark_cloth
# (shape, paint at rest, the cloth the rush pass may paint it on, whether the
# burning paint darkens the strokes' own edge - see intro_lib.DARK_EDGE)
OLD = (intro_sigil.sigil_trident, _old_paint, lambda jk: jk, True)
NEW = (intro_sigil.sigil_ten, NEW_PAINT, NEW_CLOTH, False)


def use(mark):
    """bind the rig to one mark; clear every cache that holds the last one"""
    intro_sigil.sigil, intro_sigil.paint_rest, CR.mark_cloth, IL.DARK_EDGE = mark
    IF.SIGIL = None
    fin = sys.modules.get('finish')
    if fin is not None:
        fin.SIGIL = None


# ---------------------------------------------------------------- renders

def strip(frames, fw, fh):
    s = blank(fw * len(frames), fh)
    for i, f in enumerate(frames):
        paste(s, f, i * fw, 0)
    return s


class unscaled:
    """carter_demon_fx works at scale 1.0; the Carter rig at carter_scale"""
    def __enter__(self):
        lib.set_scale(1.0)

    def __exit__(self, *a):
        carter_scale.apply()


def finish_frames():
    if FX not in sys.path:
        sys.path.insert(0, FX)
    import finish
    finish.SIGIL = None
    with unscaled():
        return [finish.frame(i).rgba() for i in range(5)]


RENDER = {
    'carter_akuma.png': lambda: [build.frame0().rgba(), build.frame1().rgba(),
                                 build.frame2().rgba()],
    'carter_intro.png': lambda: BI.build_intro(),
    'carter_mark_glow.png': lambda: BI.build_mark_glow()[0],
    'carter_victory.png': lambda: [CVI.frame(i).rgba() for i in range(CVI.N)],
    'carter_look_back.png': lambda: [CLK.frame(i).rgba() for i in range(CLK.N)],
    'carter_rush_pass.png': lambda: [CP.rush_pass(i).rgba() for i in range(3)],
    'Demon/demon_finish.png': finish_frames,
}
FRAME = {'carter_mark_glow.png': (BI.MARK_BOX[2], BI.MARK_BOX[3]),
         'Demon/demon_finish.png': (224, 224)}


# ---------------------------------------------------------------- zones

def mark_union():
    """the old and the new mark as the back view clips them"""
    jk = PO.back_jacket()
    return union(inter(intro_sigil.sigil_trident(), jk),
                 inter(intro_sigil.sigil_ten(), jk))


def rings(level):
    """the outermost ring sigil_bloom can tint at this level (0 = no bloom)"""
    if level <= 0.02:
        return 0
    return 2 + int(round(level * 7)) + 1


def squeezed(m, sfun, dx=0):
    """where a mask lands after hsq_canvas: its forward scatter, plus every
    target pixel whose backward sample falls on it, shifted, grown by one"""
    out = IL.hsq_mask(m, sfun)
    for y in range(H):
        s = sfun(y)
        for x in range(W):
            u = IL.AXC + (x + 0.5 - IL.AXC) / s - 0.5
            for sx in (int(u), int(u) + 1):
                if 0 <= sx < W and m[y][sx]:
                    out[y][x] = True
    if dx:
        sh = empty()
        for y in range(H):
            for x in range(W):
                if out[y][x] and 0 <= x + dx < W:
                    sh[y][x + dx] = True
        out = sh
    return grow(out, 1)


def zones_akuma(M):
    return [None, None, M]


def zones_intro(M):
    z = [None]
    for k in range(1, 5):
        st = IF.MAT[k]
        m = M
        if st['sq'] and st['sq'] < 0.999:
            m = squeezed(M, IL.turn_scale(st['sq'], keep_head=False))
        z.append(grow(m, rings(0.25 * st['t'])))
    for lv in IF.FLARE_LV:
        z.append(grow(M, rings(lv)))
    # turn 0: 40 degrees, squeezed and shifted; turn 1: the edge-on pivot
    s = IF.sq_of(IF.TURN[0]['phi'])
    z.append(squeezed(grow(M, rings(IF.TURN[0]['mark'] * 0.8)), IL.turn_scale(s),
                      int(round(4.0 * (1.0 - s)))))
    z.append(squeezed(grow(M, rings(0.70)), IL.turn_scale(IF.sq_of(90.0))))
    return z + [None] * (BI.N_INTRO - len(z))


def zones_victory(M):
    z = [None, None]
    z.append(squeezed(grow(M, rings(0.60)), IL.turn_scale(IF.sq_of(90.0))))
    z.append(grow(M, rings(CVI.TURN[3]['mark'] * 0.8)))
    for lv in CVI.BURN_LV:
        z.append(grow(M, rings(lv)))
    return z


def zones_look(M):
    return [M] * CLK.N


def zones_rush_pass(M):
    """the fitted mark on each pitched back, both marks, plus its one-ring bloom"""
    seen = []
    real = CR.mark_m

    def spy(p, panel=None):
        m = real(p, panel)
        seen.append(m)
        return m
    CR.mark_m = spy
    z = []
    try:
        for i in range(3):
            fits = []
            for mark in (OLD, NEW):
                use(mark)
                seen.clear()
                CR.draw(CP.PASS[i])
                fits.append(seen[-1])
            z.append(grow(union(*fits), 1))
    finally:
        CR.mark_m = real
    return z


def zones_finish(_M):
    """the emblem is painted up to grow(3) round itself over the bloom"""
    if FX not in sys.path:
        sys.path.insert(0, FX)
    import finish
    got = []
    with unscaled():
        for mark in (OLD, NEW):
            use(mark)
            got.append(finish.sigil_mask(3))
    zone = (got[0] | got[1]).grow(4, diag=True)
    return [zone.g] * 5


ZONES = {
    'carter_akuma.png': zones_akuma,
    'carter_intro.png': zones_intro,
    'carter_mark_glow.png': lambda M: ['ALL'] * 6,
    'carter_victory.png': zones_victory,
    'carter_look_back.png': zones_look,
    'carter_rush_pass.png': zones_rush_pass,
    'Demon/demon_finish.png': zones_finish,
}


# ---------------------------------------------------------------- proof

def frames_of(px, fw, fh):
    n = len(px[0]) // fw
    return [[row[i * fw:(i + 1) * fw] for row in px[:fh]] for i in range(n)]


def prove(name, old_dir):
    fw, fh = FRAME.get(name, (W, H))
    w, h, shipped = read_png(os.path.join(old_dir, name))
    use(OLD)
    old = RENDER[name]()
    use(NEW)
    new = RENDER[name]()
    zones = ZONES[name](mark_union())
    use(NEW)
    ship_f = frames_of(shipped, fw, fh)
    ok = True
    lines = []
    if (w, h) != (fw * len(new), fh) or len(ship_f) != len(new):
        lines.append('   !! size or frame count changed: shipped %dx%d, new %d frames of %dx%d'
                     % (w, h, len(new), fw, fh))
        ok = False
    for i, (s, o, n, z) in enumerate(zip(ship_f, old, new, zones)):
        same_old = all(tuple(s[y][x]) == tuple(o[y][x]) for y in range(fh) for x in range(fw))
        diff = [(x, y) for y in range(fh) for x in range(fw)
                if tuple(s[y][x]) != tuple(n[y][x])]
        if z is None:
            out = diff
            zn = 0
        elif z == 'ALL':
            out = []
            zn = fw * fh
        else:
            out = [(x, y) for x, y in diff if not z[y][x]]
            zn = sum(1 for y in range(fh) for x in range(fw) if z[y][x])
        bb = ''
        if diff:
            xs = [x for x, _ in diff]
            ys = [y for _, y in diff]
            bb = 'x %2d..%-3d y %2d..%-3d' % (min(xs), max(xs), min(ys), max(ys))
        tag = ('no mark   ' if z is None else 'overlay   ' if z == 'ALL' else
               'zone %4dpx' % zn)
        lines.append('   f%-2d %s  old render == shipped: %-3s  changed %4d  %-22s outside zone: %d'
                     % (i, tag, 'yes' if same_old else 'NO', len(diff), bb, len(out)))
        if not same_old or out:
            ok = False
    return ok, lines, new, (fw, fh)


def write_whole(path, w, h, px):
    part = path + '.part'
    write_png(part, w, h, px)
    os.replace(part, path)


if __name__ == '__main__':
    args = sys.argv[1:]
    old_dir = A
    if '--old' in args:
        old_dir = os.path.abspath(args[args.index('--old') + 1])
    only = [a for a in args if a.endswith('.png')]
    names = [n for n in RENDER if not only or n in only or os.path.basename(n) in only]
    results = []
    all_ok = True
    for name in names:
        ok, lines, new, (fw, fh) = prove(name, old_dir)
        print('%s  %s' % (name, 'PASS' if ok else 'FAIL'))
        print('\n'.join(lines))
        all_ok &= ok
        results.append((name, new, fw, fh))
    print('\nALL SHEETS PASS' if all_ok else '\nFAILED - nothing written')
    if all_ok and '--write' in args:
        for name, new, fw, fh in results:
            path = os.path.join(A, name)
            write_whole(path, fw * len(new), fh, strip(new, fw, fh))
            print('wrote', path)
    sys.exit(0 if all_ok else 1)
