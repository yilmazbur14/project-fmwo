"""Write the approval pass into scratchpad/god_elements/approval/ (ONLY there: guard.py refuses the project).

    python export.py          every sheet (.png + .aseprite, round-trip checked), the 3x previews, contract.json
"""
import json
import shutil
import subprocess
import tempfile
from ge_common import *
import le_build as LB
from imgdiff import pixel_diff
import liam_puppet as LP
import liam_aura as LA
import bixby_puppet as BP
import wheel as WH

ASE = C.ASEPRITE
VOID_BG = (14, 10, 24, 255)


def save_sheet(name, frames, durs, tags, layer, tmp):
    """frames: list of RGBA numpy frames (same size). Writes NAME.png (horizontal strip) and NAME.aseprite (one
    frame per cell, durations and tags), and checks the .aseprite exports back to the same pixels."""
    a = strip(frames)
    png = os.path.join(OUT, name + '.png')
    Image.fromarray(a, 'RGBA').save(png)
    ase = os.path.join(OUT, name + '.aseprite')
    lua = os.path.join(tmp, 'mk.lua')
    if not os.path.exists(lua):
        with open(lua, 'w') as f:
            f.write(LB.LUA)
    fw = frames[0].shape[1]
    tg = ';'.join('%s:%d:%d' % (t, i + 1, j + 1) for (t, i, j) in tags)
    subprocess.run([ASE, '-b', '--script-param', 'src=' + png, '--script-param', 'out=' + ase,
                    '--script-param', 'n=%d' % len(frames), '--script-param', 'fw=%d' % fw,
                    '--script-param', 'durs=' + ','.join('%d' % round(d * 1000) for d in durs),
                    '--script-param', 'layer=' + layer, '--script-param', 'tags=' + tg, '--script', lua],
                   check=True, capture_output=True)
    back = os.path.join(tmp, name + '_rt.png')
    subprocess.run([ASE, '-b', ase, '--sheet', back, '--sheet-type', 'horizontal'], check=True, capture_output=True)
    d = pixel_diff(Image.open(png), Image.open(back))
    if d:
        raise SystemExit('%s: the .aseprite does not round-trip: %s' % (name, d))
    return png


def preview(name, im, s=3, bg=VOID_BG):
    up(im if isinstance(im, Image.Image) else Image.fromarray(im, 'RGBA'), s, bg).save(os.path.join(OUT, name))


def numbers(a):
    s = stats(a)
    return {'black_pct': round(100 * s['black'], 1), 'colours': s['colours'], 'semi_alpha_px': s['semi'],
            'opaque_px': s['opaque']}


def main():
    os.makedirs(OUT, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix='ge_export_')
    report = {}
    try:
        # ---------------- Liam
        lf, linfo, lav = LP.build()
        probs = LP.audit(lf, linfo)
        if probs:
            raise SystemExit('liam: %s' % probs)
        save_sheet('liam_puppet_avatar', lf, [0.5, 0.5], [('float', 0, 0), ('surge', 1, 1)], 'liam_puppet', tmp)
        backs, fronts = LA.build(lf)
        save_sheet('liam_puppet_avatar_aura_back', backs, [0.5, 0.5], [('float', 0, 0), ('surge', 1, 1)], 'aura_back', tmp)
        save_sheet('liam_puppet_avatar_aura_front', fronts, [0.5, 0.5], [('float', 0, 0), ('surge', 1, 1)], 'aura_front', tmp)
        preview('liam_puppet_avatar_3x.png', strip(lf))
        comps = [np.array(LA.composite(lf[f], backs[f], fronts[f])) for f in range(2)]
        preview('liam_puppet_avatar_with_aura_3x.png', strip(comps))
        src_liam = np.array(Image.open(CHARS + '/Liam/liam.png').convert('RGBA'))
        src_liam_b = np.array(Image.open(PROJECT + '/art_source/jordan_puppets/approval/liam/liam_idle_B.png').convert('RGBA'))
        report['liam_puppet_avatar'] = {
            'frames': [numbers(f) for f in lf],
            'source liam.png': numbers(src_liam),
            'roster liam puppet (approval take B, unshipped)': numbers(src_liam_b),
            'hooks': [{k: list(v) for k, v in i['hooks'].items()} for i in linfo],
            'rings drawn': [i.get('rings_drawn', []) for i in linfo],
            'avatar pixels': [len(a) for a in lav],
        }
        # ---------------- Bixby
        for take, name in (('ash', 'bixby_puppet'), ('blood', 'bixby_puppet_blood')):
            bf, binfo = BP.build(take)
            probs = BP.audit(bf, binfo)
            if probs:
                raise SystemExit('bixby %s: %s' % (take, probs))
            save_sheet(name, bf, [0.12, 0.12], [('fly', 0, 1)], name, tmp)
            preview(name + '_3x.png', strip(bf))
            report[name] = {'frames': [numbers(f) for f in bf],
                            'hooks': [{k: list(v) for k, v in i['hooks'].items()} for i in binfo],
                            'rings drawn': [i.get('rings_drawn', []) for i in binfo]}
        src_bix = np.array(Image.open(CHARS + '/Bixby/bixby_beast_fly.png').convert('RGBA'))
        report['source bixby_beast_fly.png (frames 0-1)'] = numbers(src_bix[:, :384])
        # ---------------- the wheel
        wf = WH.build()
        names = [n for n, _ in WH.STATES]
        save_sheet('element_wheel', wf, [0.1] * len(wf), [(n, i, i) for i, n in enumerate(names)], 'wheel', tmp)
        preview('element_wheel_3x.png', strip(wf))
        report['element_wheel'] = {'frames': {n: numbers(f) for n, f in zip(names, wf)}}
        with open(os.path.join(OUT, 'numbers.json'), 'w') as f:
            json.dump(report, f, indent=1)
        print(json.dumps(report, indent=1)[:4000])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
