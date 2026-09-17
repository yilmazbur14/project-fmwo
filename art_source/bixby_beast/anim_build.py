"""Build every beast Bixby combat sheet into ../final_anims/:
  bixby_beast_<name>.png            composite horizontal strip (what the game loads)
  layer_<name>_<layer>.png          one strip per layer (imported into the .aseprite as named layers)
  bixby_beast_shadow_ground.png     grounded contact shadows
and lint every output (alpha 0/255 only, colours from the approved palettes only)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from lib import *
from pal import PALC
from pngio import read_png
import anim_common as AC
import anim_sheets as S
import anim_defeat as D
import anim_shadows as SHD
import faces2 as F2
import small_art as SA

OUT = AC.FINAL

SHEETS = [
    ('fly', S.fly, S.LAYERS),
    ('land', S.land, S.LAYERS),
    ('recover', S.recover, S.LAYERS),
    ('hit', S.hit, S.LAYERS),
    ('takeoff', S.takeoff, S.LAYERS),
    ('roar', S.roar, S.LAYERS),
    ('defeat', D.frames, D.LAYERS),
]

import fx2 as FX2
ALLOWED = set(PALC.values()) | set(F2.EXTRA.values()) | set(SA.BPAL.values()) | set(SA.LPAL.values()) | set(FX2.FX_PAL.values())


def lint(path):
    w, h, px = read_png(path)
    alphas, off = set(), {}
    for row in px:
        for p in row:
            p = tuple(p)
            alphas.add(p[3])
            if p[3] and p not in ALLOWED:
                off[p] = off.get(p, 0) + 1
    ok = alphas <= {0, 255} and not off
    print('  lint %-44s %dx%d alphas=%s off-palette=%s %s' % (os.path.basename(path), w, h, sorted(alphas), len(off), 'OK' if ok else 'FAIL'))
    return ok


def build(names=None):
    ok = True
    for name, fn, layers in SHEETS:
        if names and name not in names:
            continue
        frs = fn()
        n = len(frs)
        comp = Canvas(192 * n, 160)
        for i, fr in enumerate(frs):
            for L in layers:
                if fr.get(L) is not None:
                    comp.blit(fr[L], 192 * i, 0)
        path = os.path.join(OUT, 'bixby_beast_%s.png' % name)
        comp.save(path)
        ok &= lint(path)
        for L in layers:
            ls = Canvas(192 * n, 160)
            for i, fr in enumerate(frs):
                if fr.get(L) is not None:
                    ls.blit(fr[L], 192 * i, 0)
            ls.save(os.path.join(OUT, 'layer_%s_%s.png' % (name, L)))
        print('built', name, n, 'frames')
    if not names or 'shadow' in names:
        fr = SHD.frames()
        s = Canvas(192 * len(fr), 48)
        for i, f in enumerate(fr):
            s.blit(f, 192 * i, 0)
        path = os.path.join(OUT, 'bixby_beast_shadow_ground.png')
        s.save(path)
        ok &= lint(path)
    print('BUILD', 'OK' if ok else 'LINT FAILURES')
    return ok


if __name__ == '__main__':
    build(sys.argv[1:] or None)
