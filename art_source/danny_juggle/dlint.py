"""python lint.py  - craft, palette and shading checks on Danny's juggle frames.

Measured against his APPROVED evolved-form sheets (Assets/Characters/Danny/Sumo/danny_sumo_*):

  palette    every colour one of his 26 (no new colour, no semi-alpha);
  craft      no pinholes; no keyline gaps on his body or on the keylined props (dust, the bubble);
  numbers    black share and colour count per frame, beside his sheets' per-frame range (his VS card
             measured the slap frame at 16.3% / 26 colours);
  ramps      per family, the share of the darker half of the ramp ("deep"), frame by frame, against
             his sheets, measured on his body alone (effects left out). His skin and his two knits are
             most of him. The contract's trap is a relight that drowns a turned frame in shadow; this
             measures it.
"""
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dposes as PZ             # noqa: E402
import dparts as D              # noqa: E402
K = D.K
from PIL import Image           # noqa: E402

SUMO = os.path.normpath(os.path.join(HERE, '..', '..', 'Assets', 'Characters', 'Danny', 'Sumo'))
SOURCES = ('danny_sumo_idle', 'danny_sumo_wake', 'danny_sumo_slap', 'danny_sumo_step', 'danny_sumo_hit',
           'danny_sumo_defeat')
MAIN = ('skin', 'lknit', 'dknit')
DEEP_TOL = 0.10
FILL = set(D.BODY_KEYS)


def rgb(k):
    return D.PAL[k][:3]


# by colour: the two knits share 5B6EE1, so on a finished image the families are told apart by
# the colours only one of them uses; 5B6EE1 counts to both (as the idle's own measurement does).
FAM_RGB = {fam: [rgb(k) for k in keys] for fam, keys in D.FAMILIES.items()}


def deep_shares(c):
    out = {}
    for fam, cols in FAM_RGB.items():
        tones = [c.get(v, 0) for v in cols]
        n = sum(tones)
        if n < 40:
            continue
        half = (len(cols) - 1) / 2.0
        out[fam] = (n, sum(t for i, t in enumerate(tones) if i < half) / n)
    return out


def source_stats():
    frames = []
    for name in SOURCES:
        im = Image.open(os.path.join(SUMO, name + '.png')).convert('RGBA')
        for i in range(im.width // D.FW):
            f = im.crop((D.FW * i, 0, D.FW * i + D.FW, D.FH))
            flat = f.get_flattened_data() if hasattr(f, 'get_flattened_data') else f.getdata()
            frames.append([p for p in flat if p[3]])
    allpx = [p for fr in frames for p in fr]
    black = [sum(1 for p in fr if p[:3] == (0, 0, 0)) / len(fr) for fr in frames]
    cols = [len({p[:3] for p in fr}) for fr in frames]
    return dict(palette={p[:3] for p in allpx}, semi=sum(1 for p in allpx if p[3] < 255),
                black=(min(black), max(black)), colours=(min(cols), max(cols)),
                deep=deep_shares(Counter(p[:3] for p in allpx)), n=len(frames))


def craft(px):
    bad = Counter()
    bad['pinhole'] = len(K.pinholes(px))
    for part in (PZ.REC['body'], PZ.REC['props']):
        shown = {q: px[q] for q in part if px.get(q) == part[q]}
        bad['keyline gap'] += len([q for q in K.gaps(shown, FILL)
                                   if any((q[0] + dx, q[1] + dy) not in px for dx, dy in K.N4)])
    bad['orphan'] = len(K.orphans(px))
    return +bad


def main(verbose=True):
    src = source_stats()
    if verbose:
        print('his approved sheets: %d frames, black %.1f-%.1f%%, %d-%d colours, %d semi-alpha px'
              % (src['n'], 100 * src['black'][0], 100 * src['black'][1], src['colours'][0],
                 src['colours'][1], src['semi']))
        print('  deep share by family: ' + '  '.join('%s %.1f%%' % (f, 100 * src['deep'][f][1])
                                                     for f in MAIN if f in src['deep']))
        print()
        print('%-3s %-15s %6s %4s  %-40s %s' % ('#', 'frame', 'black', 'col', 'deep share', 'findings'))
    fatal = 0
    for i, (name, fn, _) in enumerate(PZ.FRAMES):
        px = fn()
        fails = []
        c = Counter(rgb(k) for k in px.values())
        off = set(c) - src['palette']
        if off:
            fails.append('off-palette %s' % sorted('#%02X%02X%02X' % v for v in off))
        cr = craft(px)
        if cr.get('pinhole'):
            fails.append('%d pinholes' % cr['pinhole'])
        if cr.get('keyline gap'):
            fails.append('%d keyline gaps' % cr['keyline gap'])
        n = sum(c.values())
        # the ramps are measured on HIM: his body's pixels as they show in the frame, not the dust or
        # the flash (the dust's pale blue is the knit's own CBDBFC and would pass for knit)
        body = Counter(rgb(px[q]) for q in PZ.REC['body'] if px.get(q) == PZ.REC['body'][q])
        deep = deep_shares(body)
        cells = []
        for fam in MAIN:
            if fam in deep and fam in src['deep']:
                d, ref = deep[fam][1], src['deep'][fam][1]
                flag = abs(d - ref) > DEEP_TOL
                cells.append('%s %4.1f%s' % (fam, 100 * d, '!' if flag else ''))
                if flag:
                    fails.append('%s deep %.1f%% vs %.1f%%' % (fam, 100 * d, 100 * ref))
        fatal += len(fails)
        notes = ['%d lone specks' % cr['orphan']] if cr.get('orphan') else []
        if verbose:
            print('%-3d %-15s %5.1f%% %4d  %-40s %s' % (i, name, 100 * c.get((0, 0, 0), 0) / n, len(c),
                                                       ' '.join(cells), '; '.join(fails + notes) or 'clean'))
    if verbose:
        print('\n%d fatal findings (palette, pinholes, keyline gaps, ramp band)' % fatal)
    return fatal


if __name__ == '__main__':
    sys.exit(1 if main() else 0)
