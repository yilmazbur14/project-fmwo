"""Build sheets into the rider scratch folder (never Assets): python jr_build.py [--dry] mod1 mod2 ...
Prints each frame's numbers and any problem; with --dry nothing is written."""
import importlib
import json
import os
import sys
sys.dont_write_bytecode = True
import jr_common as C
import jr_sheet as S

OUT = C.RIDER


def run(names, write=True):
    entries, allp = {}, []
    for n in names:
        mod = importlib.import_module(n)
        entry, probs, frames = S.build_sheet(mod, OUT, write=write)
        entries[mod.NAME] = entry
        allp += probs
        print('%s  (%s, ref %.1f%%)' % (mod.NAME, mod.KIND, 100 * S.REF[mod.KIND]))
        for i, pf in enumerate(entry['per_frame']):
            nm = pf['numbers']
            print('  f%d black %.2f%% (%+.2f) col %d opq %d audit %s edge %d  %s' % (
                i, 100 * nm['black'], nm['black_vs_ref_pts'], nm['colours'], nm['opaque'], nm['audit'],
                nm['edge_px'], {k: v for k, v in pf['anchors'].items()}))
    for p in allp:
        print('PROBLEM', p)
    return entries, allp


if __name__ == '__main__':
    args = sys.argv[1:]
    dry = '--dry' in args
    args = [a for a in args if a != '--dry']
    run(args, write=not dry)
