"""Measure every anchor on Greyson's attack sheets, per frame, in texels on the frame (origin top left,
112x112, feet (56, 111)). Writes nothing unless given a folder for the marked-up check images
(refused inside Assets):

    python -B gan_measure.py                 # prints the table
    python -B gan_measure.py <scratch_dir>   # also writes anchors_<sheet>.png there (4x, marked)

  crown    the top of his head over its middle column: the mane's top keyline row, at the centre of
           that row (the parting). Daze stars and badges stand over it (the code's DAZE_GAP, TELL_GAP).
  body     the punchable box, drawn as the approved idle's is (GreysonArtLayout BODY_BOXES idle,
           Rect2(34, 26, 44, 86)): the 44-texel column of his head and torso, arms and weapons left
           out, from the crown to the soles' bottom edge (y 112), moved with his torso.
  muzzle   the cannon's bore: the centre of its dark opening as drawn (the recorded muzzle end when
           the bore is hidden).
  hand     the centre of his right fist (the barbell hand).
  plate    the barbell plate's centre while it is on the bar.
  release  throw, the RELEASE frame: where the plate leaves the bar's end.
  impact   slam, the IMPACT frame: where the plate meets the mat (its lowest keyline texel).
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gan_base as B  # noqa: E402
import gan_preview as P  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

BODY_W = 44
BODY_X0 = 34
BORE = ('z', 'Z')


def _centre(pts):
    pts = list(pts)
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def _r(p):
    return (int(round(p[0])), int(round(p[1])))


def crown(head):
    top = min(y for (_x, y) in head)
    xs = [x for (x, y) in head if y == top]
    return (int(round((min(xs) + max(xs)) / 2.0)), top)


def muzzle(px, info):
    cannon = info.get('cannon')
    if not cannon:
        return None
    bore = [q for q, k in cannon.items() if k in BORE and px.get(q) == k]
    if bore:
        return _r(_centre(bore))
    return _r(info['muzzle'])


def lowest_of(part, px):
    """The lowest drawn texel of a part with its keyline (the part's pixels plus the keyline the
    stamp laid round them), as (x centre of that row, row)."""
    area = set(part)
    for (x, y) in list(part):
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if px.get(q) == 'k':
                area.add(q)
    low = max(y for (_x, y) in area if (_x, y) in px)
    xs = [x for (x, y) in area if y == low and (x, y) in px]
    return (int(round((min(xs) + max(xs)) / 2.0)), low)


def measure(mod):
    rows = []
    for i, (px, fx, info) in enumerate(mod.frames_info()):
        c = crown(info['head'])
        dx = info.get('base', (0, 0))[0]
        row = {'frame': i, 'crown': c, 'body': (BODY_X0 + dx, c[1], BODY_W, 112 - c[1]),
               'muzzle': muzzle(px, info), 'bbox': B.bbox(px)}
        if 'hand' in info:
            row['hand'] = _r(_centre(info['hand']))
        if 'plate_c' in info:
            row['plate'] = _r(info['plate_c'])
        if i == getattr(mod, 'RELEASE_FRAME', None):
            row['release'] = _r(info['release'])
        if i == getattr(mod, 'IMPACT_FRAME', None):
            row['impact'] = lowest_of(info['plate'], px)
            row['impact_design'] = _r(info['impact'])
        rows.append(row)
    return rows


MARKS = {'crown': (0, 255, 255, 255), 'muzzle': (255, 0, 255, 255), 'hand': (255, 230, 0, 255),
         'plate': (255, 140, 0, 255), 'release': (255, 40, 40, 255), 'impact': (255, 40, 40, 255)}


def marked(mod, rows, s=4):
    fr = [B.image(px) for px, _fx in mod.frames()]
    out = Image.new('RGBA', (len(fr) * (112 * s + 6) + 6, 112 * s + 12), (16, 17, 22, 255))
    d = ImageDraw.Draw(out)
    for i, (im, row) in enumerate(zip(fr, rows)):
        x0 = 6 + i * (112 * s + 6)
        out.alpha_composite(P.up(P.on_bg(im), s), (x0, 6))
        bx, by, bw, bh = row['body']
        d.rectangle((x0 + bx * s, 6 + by * s, x0 + (bx + bw) * s - 1, 6 + (by + bh) * s - 1),
                    outline=(60, 255, 90, 255))
        for name, col in MARKS.items():
            if row.get(name):
                px_, py_ = row[name]
                d.rectangle((x0 + px_ * s, 6 + py_ * s, x0 + px_ * s + s - 1, 6 + py_ * s + s - 1),
                            outline=col, width=2)
        fx, fy = B.FEET
        d.rectangle((x0 + fx * s, 6 + fy * s, x0 + fx * s + s - 1, 6 + fy * s + s - 1),
                    outline=(255, 255, 255, 255), width=2)
    return out


def main(argv):
    out = None
    if argv:
        out = os.path.abspath(argv[0])
        if P._under(out, os.path.join(B.ROOT, 'Assets')):
            raise SystemExit('refusing %s: check images never go into Assets' % out)
        os.makedirs(out, exist_ok=True)
    for mod in P.modules():
        rows = measure(mod)
        print('%s  (%d frames; times %s%s)' % (mod.NAME, len(rows), mod.TIMES, ', loops' if mod.LOOP else ', once'))
        for r in rows:
            extra = ''.join('  %s %s' % (k, r[k]) for k in ('hand', 'plate', 'release', 'impact',
                                                           'impact_design') if k in r)
            print('  f%d  crown %s  body Rect2%s  muzzle %s%s' % (r['frame'], r['crown'], r['body'],
                                                                 r['muzzle'], extra))
        if out:
            marked(mod, rows).save(os.path.join(out, 'anchors_%s.png' % mod.NAME))
    if out:
        print('marked images in', out)


if __name__ == '__main__':
    main(sys.argv[1:])
