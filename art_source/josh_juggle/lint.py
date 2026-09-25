"""python lint.py  - craft, palette and shading checks on Josh's juggle frames.

Measured against his APPROVED sheets (josh_cards, idle, hit, defeat, recovery, throw, intro):

  palette    every colour must be one of his (no new colour, no semi-alpha);
  craft      no pinholes (a transparent pixel walled in on four sides), no orphan specks on his body,
             no fill pixel of his body touching transparency (a keyline gap);
  numbers    black share and colour count per frame, beside his sheets' per-frame range;
  ramps      per family, the share of the darker half of the ramp ("deep"), frame by frame, on his
             body alone (cards, dust and the flying hat left out), against the same share over his
             approved sheets. This is the measurement the contract asks for:
             a relight that goes wrong drowns a frame in its deep tones (one pass measured 31% deep
             against a 14% source). The relight here is rank-preserving, so a turned frame carries
             exactly the tones of the same pose unturned; the band still fails the build if a pose
             itself drifts.

Effects (cards, dust, arcs, glints) are drawn without their own keyline on purpose where they are
single-pixel streaks; the gap check runs on his body's colours only.
"""
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import poses as PZ              # noqa: E402
import jparts as P              # noqa: E402
import jkit as K                # noqa: E402
from PIL import Image           # noqa: E402

ASSETS = os.path.normpath(os.path.join(HERE, '..', '..', 'Assets', 'Characters', 'Josh'))
SOURCES = ('josh_cards', 'josh_idle', 'josh_hit', 'josh_defeat', 'josh_recovery', 'josh_throw',
           'josh_intro')
MAIN = ('cream', 'skin', 'hair', 'indigo', 'wine')
DEEP_TOL = 0.10            # a frame's deep share may sit this far either side of his sheets'
BODY_FILL = set('abcdehijlmwxyzZvVRTnNsSt56789gGoOY')


def rgb(k):
    return P.PAL[k][:3]


def deep_shares(counter_rgb):
    out = {}
    for fam, keys in P.FAMILIES.items():
        tones = [counter_rgb.get(rgb(k), 0) for k in keys]
        n = sum(tones)
        if n < 20:
            continue
        half = (len(keys) - 1) / 2.0
        out[fam] = (n, sum(t for i, t in enumerate(tones) if i < half) / n)
    return out


def source_stats():
    frames = []
    for name in SOURCES:
        im = Image.open(os.path.join(ASSETS, name + '.png')).convert('RGBA')
        for i in range(im.width // 80):
            f = im.crop((80 * i, 0, 80 * i + 80, 80))
            px = [p for p in (f.get_flattened_data() if hasattr(f, 'get_flattened_data') else f.getdata())
                  if p[3]]
            frames.append(px)
    allpx = [p for fr in frames for p in fr]
    palette = {p[:3] for p in allpx}
    semi = sum(1 for p in allpx if p[3] < 255)
    black = [sum(1 for p in fr if p[:3] == (0, 0, 0)) / len(fr) for fr in frames]
    cols = [len({p[:3] for p in fr}) for fr in frames]
    deep = deep_shares(Counter(p[:3] for p in allpx))
    return dict(palette=palette, semi=semi, black=(min(black), max(black)), colours=(min(cols), max(cols)),
                deep=deep, n=len(frames))


def craft(px):
    """Pinholes anywhere; keyline gaps on his body and on the keylined props (hat, cards, dust),
    measured on each as drawn into the finished frame; lone specks anywhere (reported, not fatal:
    a glint or a streak end is one pixel by design)."""
    bad = Counter()
    bad['pinhole'] = len(K.pinholes(px))
    for part in (PZ.REC['body'], PZ.REC['props']):
        shown = {q: px[q] for q in part if px.get(q) == part[q]}
        bad['keyline gap'] += len([q for q in K.gaps(shown, BODY_FILL) if q in shown
                                   and any((q[0] + dx, q[1] + dy) not in px for dx, dy in K.N4)])
    bad['orphan'] = len(K.orphans(px))
    return +bad


def frame_numbers(px):
    c = Counter(rgb(k) for k in px.values())
    n = sum(c.values())
    return dict(black=c.get((0, 0, 0), 0) / n, colours=len(c), deep=deep_shares(c), counter=c)


def main(verbose=True):
    src = source_stats()
    if verbose:
        print('his approved sheets: %d frames, black %.1f-%.1f%%, %d-%d colours, %d semi-alpha px'
              % (src['n'], 100 * src['black'][0], 100 * src['black'][1], src['colours'][0],
                 src['colours'][1], src['semi']))
        print('  deep share by family: ' + '  '.join('%s %.1f%%' % (f, 100 * src['deep'][f][1])
                                                     for f in MAIN if f in src['deep']))
        print()
        print('%-3s %-15s %6s %4s  %-52s %s' % ('#', 'frame', 'black', 'col', 'deep share (vs sheets)', 'findings'))
    fatal = 0
    for i, (name, fn, _) in enumerate(PZ.FRAMES):
        px = fn()
        fails = []
        off = {rgb(k) for k in px.values()} - src['palette']
        if off:
            fails.append('off-palette %s' % sorted('#%02X%02X%02X' % c for c in off))
        cr = craft(px)
        if cr.get('pinhole'):
            fails.append('%d pinholes' % cr['pinhole'])
        if cr.get('keyline gap'):
            fails.append('%d keyline gaps' % cr['keyline gap'])
        nums = frame_numbers(px)
        # the ramps are measured on HIM: his body's pixels as they show, not the cards or the dust
        # (both drawn in his cream) nor the flying hat
        body = Counter(rgb(px[q]) for q in PZ.REC['body'] if px.get(q) == PZ.REC['body'][q])
        body_deep = deep_shares(body)
        deep = []
        for fam in MAIN:
            if fam not in body_deep or fam not in src['deep']:
                continue
            n, d = body_deep[fam]
            ref = src['deep'][fam][1]
            flag = abs(d - ref) > DEEP_TOL and n >= 60
            deep.append('%s %4.1f%s' % (fam[:5], 100 * d, '!' if flag else ''))
            if flag:
                fails.append('%s deep %.1f%% vs %.1f%%' % (fam, 100 * d, 100 * ref))
        fatal += len(fails)
        notes = []
        if cr.get('orphan'):
            notes.append('%d lone specks (effects)' % cr['orphan'])
        if verbose:
            print('%-3d %-15s %5.1f%% %4d  %-52s %s' % (i, name, 100 * nums['black'], nums['colours'],
                                                       ' '.join(deep), '; '.join(fails + notes) or 'clean'))
    if verbose:
        print('\n%d fatal findings (palette, pinholes, keyline gaps, ramp band)' % fatal)
    return fatal


if __name__ == '__main__':
    sys.exit(1 if main() else 0)
