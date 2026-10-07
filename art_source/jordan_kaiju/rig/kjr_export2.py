"""Write kaiju wave 2 into scratch (scratchpad/jordan_kaiju/wave2/), never into the project. Same files
as wave 1: strips, animated layered .aseprite (round-trip checked), 3x previews, GIFs, contact sheet,
contract.json.   python kjr_export2.py"""
import json
import os
import shutil
import sys
import tempfile
import time

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kj_common as K  # noqa: E402
import kjr as R  # noqa: E402
import kjr_export as X  # noqa: E402
import kjr_build2 as B2  # noqa: E402
from PIL import Image  # noqa: E402

X.OUT = os.path.join(K.SCRATCH, 'wave2')
ORDER = ['kaiju_roar', 'kaiju_roar_spines', 'kaiju_bow', 'kaiju_hit', 'kaiju_tail_windup', 'kaiju_tail_spin',
         'kaiju_tail_arc', 'kaiju_collapse', 'kaiju_down', 'kaiju_puff']
BODY_LIKE = {'kaiju_roar', 'kaiju_bow', 'kaiju_hit', 'kaiju_tail_windup', 'kaiju_tail_spin', 'kaiju_collapse',
             'kaiju_down'}


def gifs(S):
    gdir = X.guard(os.path.join(X.OUT, 'gifs'))
    os.makedirs(gdir, exist_ok=True)
    bw, bh = R.FW, R.FH

    def seq(names, reps=1):
        fr, du = [], []
        for name in names:
            s = S[name]
            for _ in range(reps):
                for i in range(len(s['frames'])):
                    im = Image.new('RGBA', (bw, bh), (0, 0, 0, 0))
                    im.alpha_composite(X.frame_img(s, i), (0, 0))
                    fr.append(X.on_mat(im))
                    t = s['times'][i] if s['times'] and s['times'][i] else 0.5
                    du.append(1000 * t)
        return fr, du
    out = {}
    fr, du = seq(['kaiju_roar'])
    du[-1] = 500
    X.gif(os.path.join(gdir, 'roar.gif'), fr, du)
    out['roar'] = len(fr)
    # roar with the Phase B overlay
    fr, du = [], []
    for i in range(6):
        im = Image.new('RGBA', (bw, bh), (0, 0, 0, 0))
        im.alpha_composite(X.frame_img(S['kaiju_roar'], i))
        im.alpha_composite(X.frame_img(S['kaiju_roar_spines'], i))
        fr.append(X.on_mat(im))
        du.append(1000 * S['kaiju_roar']['times'][i])
    X.gif(os.path.join(gdir, 'roar_phase_b_spines.gif'), fr, du)
    out['roar_phase_b_spines'] = len(fr)
    fr, du = seq(['kaiju_bow'])
    du[-1] = 600
    X.gif(os.path.join(gdir, 'bow.gif'), fr, du)
    out['bow'] = len(fr)
    # tail: windup, then the spin with its swoosh round the feet, on a wider canvas
    W2, H2 = 420, 300
    fx_, fy_ = 210, 230                       # where FEET sits on this canvas
    fr, du = [], []
    for i in range(3):
        im = Image.new('RGBA', (W2, H2), (0, 0, 0, 0))
        im.alpha_composite(X.frame_img(S['kaiju_tail_windup'], i), (fx_ - R.FEET[0], fy_ - R.FEET[1]))
        fr.append(X.on_mat(im))
        du.append(130)
    arc = S['kaiju_tail_arc']
    for i in range(8):
        im = Image.new('RGBA', (W2, H2), (0, 0, 0, 0))
        k = (2 * i + 8) % 16                  # the swoosh leads round the feet with the turn
        piv = arc['frames'][k]['anchors']['PIVOT_FEET']
        im.alpha_composite(X.frame_img(arc, k), (fx_ - piv[0], fy_ - piv[1]))
        im.alpha_composite(X.frame_img(S['kaiju_tail_spin'], i), (fx_ - R.FEET[0], fy_ - R.FEET[1]))
        fr.append(X.on_mat(im))
        du.append(88)
    du[-1] = 400
    X.gif(os.path.join(gdir, 'tail_windup_spin_arc.gif'), fr, du)
    out['tail_windup_spin_arc'] = len(fr)
    fr, du = seq(['kaiju_collapse'])
    du[-1] = 120
    f2, d2 = seq(['kaiju_down'], reps=3)
    X.gif(os.path.join(gdir, 'collapse_down.gif'), fr + f2, du + d2)
    out['collapse_down'] = len(fr) + len(f2)
    fr, du = seq(['kaiju_hit'])
    X.gif(os.path.join(gdir, 'hit.gif'), fr, du)
    out['hit'] = len(fr)
    return out


def main():
    X.guard(X.OUT)
    os.makedirs(X.OUT, exist_ok=True)
    t0 = time.time()
    S = B2.build()
    print('built in %.1fs' % (time.time() - t0))
    tmp = tempfile.mkdtemp(prefix='kjr2_')
    contract = {
        'wave': 2, 'scale': X.SCALE, 'keyline': '#000000', 'home_screen': list(X.HOME),
        'body_frame': [R.FW, R.FH], 'body_pivot_FEET': list(R.FEET),
        'body_frame_top_left_at_home': X.frame_screen_top_left(R.FEET),
        'pivot_convention': 'as wave 1: texels from the frame\'s top-left; Sprite2D centered: offset = '
                            'frame_size / 2 - pivot',
        'audit_note': 'gaps / holes are checked on body frames; overlays and additive FX are partial or '
                      'dithered by design',
        'sheets': {},
    }
    for name in ORDER:
        s = S[name]
        png, ase = X.write_sheet(s, tmp)
        nums = X.numbers(s)
        entry = {'file': os.path.basename(png), 'aseprite': os.path.basename(ase), 'frame': s['frame'],
                 'frames': len(s['frames']), 'times': s['times'], 'loop': s['loop'], 'pivot': s['pivot'],
                 'kind': s['kind'], 'note': s['note'], 'anchors': [f['anchors'] for f in s['frames']],
                 'numbers': nums}
        if name in BODY_LIKE:
            tl = X.frame_screen_top_left(s['pivot'])
            entry['anchors_screen_at_home_f0'] = {k: X.screen(v, tl) for k, v in s['frames'][0]['anchors'].items()
                                                  if isinstance(v, list) and len(v) == 2 and
                                                  all(isinstance(c, (int, float)) for c in v)}
        contract['sheets'][name] = entry
        print('%-20s %s %2d frames  black %s' % (name, s['frame'], len(s['frames']),
                                                 ' '.join('%.1f' % (100 * r['black']) for r in nums)))
    contract['gifs'] = gifs(S)
    contract['contact_sheet'] = X.contact(S, ORDER)
    keys = set()
    for name in ORDER:
        for f in S[name]['frames']:
            keys |= set(f['px'].values())
    contract['keys_used'] = ''.join(sorted(keys))
    contract['keys_outside_palette'] = sorted(keys - K.JORDAN_KEYS - set(K.KAIJU_PAL))
    with open(X.guard(os.path.join(X.OUT, 'contract.json')), 'w') as f:
        json.dump(contract, f, indent=1)
    shutil.rmtree(tmp, ignore_errors=True)
    print('keys outside the palette:', contract['keys_outside_palette'])
    print('done in %.1fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
