"""out/contact_3x.png: every new frame at 3x (game scale) on the mat green, labelled, with the live idle for
reference, plus out/contact_6x_pitch.png at 6x for detail."""
import json
import os
import sys
sys.dont_write_bytecode = True
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.realpath(os.path.join(HERE, '..', 'out'))
PROJ = 'C:/Users/theyi/OneDrive/Documents/new-game-project/'
ASSETS = os.path.realpath(PROJ + 'Assets')
MAT = (122, 167, 88, 255)
BG = (52, 56, 66, 255)
C = json.load(open(os.path.join(OUT, 'contract.json')))


def guard(p):
    assert not os.path.realpath(p).lower().startswith(ASSETS.lower()), p
    return p


def frames(path, fw, fh):
    im = Image.open(path).convert('RGBA')
    return [im.crop((i * fw, 0, (i + 1) * fw, fh)) for i in range(im.width // fw)]


def font(sz):
    try:
        return ImageFont.load_default(size=sz)
    except TypeError:
        return ImageFont.load_default()


def tile(im, z, marks=()):
    b = Image.new('RGBA', im.size, MAT)
    b.alpha_composite(im)
    b = b.resize((im.width * z, im.height * z), Image.NEAREST)
    d = ImageDraw.Draw(b)
    for (x, y, col) in marks:
        X, Y = (x) * z, (y) * z
        if -20 <= Y:
            d.line((X - 9, Y, X + 9, Y), fill=col, width=3)
            d.line((X, Y - 9, X, Y + 9), fill=col, width=3)
    return b


def build(z, rows, path):
    GAP, LBL = 8, 18
    W = max(sum(t.width for t, _ in r) + GAP * (len(r) + 1) for r in rows)
    H = sum(max(t.height for t, _ in r) + LBL + GAP for r in rows) + GAP
    out = Image.new('RGBA', (W, H), BG)
    d = ImageDraw.Draw(out)
    y = GAP
    for r in rows:
        x = GAP
        for t, name in r:
            d.text((x, y), name, fill=(235, 235, 235), font=font(13))
            out.alpha_composite(t, (x, y + LBL))
            x += t.width + GAP
        y += max(t.height for t, _ in r) + LBL + GAP
    out.convert('RGB').save(guard(path))
    print('wrote', path, out.size)


def pitch_rows(z, marks):
    pf = frames(os.path.join(OUT, 'mason_pitch.png'), 64, 64)
    live = frames(PROJ + 'Assets/Characters/Mason/mason_sheet.png', 64, 64)
    meta = C['mason_pitch']['frames']
    rows = []
    for a, b in ((0, 5), (5, 10), (10, 15)):
        r = []
        for i in range(a, b):
            m = []
            if marks:
                e = meta[i]
                m.append((e['head_hit'][0], e['head_hit'][1], (255, 60, 60)))
                for k, col in (('release_hand', (60, 160, 255)), ('hand', (60, 220, 255)),
                               ('tell_over_comb', (255, 0, 255))):
                    if k in e:
                        m.append((e[k][0], e[k][1], col))
            r.append((tile(pf[i], z, m), '%d %s' % (i, meta[i]['name'])))
        rows.append(r)
    return rows, live


if __name__ == '__main__':
    rows, live = pitch_rows(3, False)
    rows[0].insert(0, (tile(live[0], 3), 'live: idle'))
    bf = frames(os.path.join(OUT, 'mason_broken.png'), 64, 64)
    bm = C['mason_broken']['frames']
    rows.append([(tile(live[14], 3), 'live: KO (defeat)')] +
                [(tile(bf[i], 3), '%d %s' % (i, bm[i]['name'])) for i in range(7)])
    spin = frames(os.path.join(OUT, 'nugget_fastball.png'), 32, 32)
    st = frames(os.path.join(OUT, 'nugget_fastball_streaks.png'), 48, 48)
    ch = frames(os.path.join(OUT, 'nugget_changeup_trail.png'), 48, 48)
    r = []
    for d, name in ((2, 'S'), (3, 'SW'), (6, 'N')):
        w = Image.new('RGBA', (48, 48), (0, 0, 0, 0)); w.alpha_composite(st[d * 2]); w.alpha_composite(spin[d % 4], (8, 8))
        r.append((tile(w, 3), 'fastball %s' % name))
    for d, name in ((2, 'S'), (3, 'SW')):
        w = Image.new('RGBA', (48, 48), (0, 0, 0, 0)); w.alpha_composite(ch[d * 2 + 1]); w.alpha_composite(spin[(d + 1) % 4], (8, 8))
        r.append((tile(w, 3), 'changeup %s' % name))
    bonk = frames(os.path.join(OUT, 'nugget_bonk.png'), 32, 32)
    r += [(tile(b, 3), 'bonk %d' % i) for i, b in enumerate(bonk)]
    rows.append(r)
    hr = frames(os.path.join(OUT, 'home_run.png'), 128, 40)
    rows.append([(tile(h, 3), 'home_run %d' % i) for i, h in enumerate(hr[:3])])
    rows.append([(tile(h, 3), 'home_run %d' % (i + 3)) for i, h in enumerate(hr[3:])])
    pips = frames(os.path.join(OUT, 'home_run_pips.png'), 12, 12)
    puff = frames(os.path.join(OUT, 'nugget_puff.png'), 8, 8)
    rows.append([(tile(p, 3), 'pip %s' % n) for p, n in zip(pips, ('empty', 'filled'))] +
                [(tile(p, 3), 'puff %d' % i) for i, p in enumerate(puff)])
    build(3, rows, os.path.join(OUT, 'contact_3x.png'))
    rows6, _ = pitch_rows(6, True)
    build(6, rows6, os.path.join(OUT, 'contact_6x_pitch_anchors.png'))
