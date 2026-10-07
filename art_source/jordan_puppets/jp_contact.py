"""Jordan's puppets: review contact sheets of SHIPPED puppet sheets, at 2x.

Reads the shipped twins (res://Assets/Characters/Jordan/Puppets/<key>/) and their back hooks
(res://Scripts/JordanPuppetHooks.gd: BACK, OVER), never writes there. A bare run writes nothing:

    python jp_contact.py                         # print this
    python jp_contact.py OUT_DIR key [key ...]   # contact_2x_<key>.png into OUT_DIR, one per key
    ... --from DIR                                # read a --check build in DIR instead of the shipped files

Every sheet of a key, its frames at 2x in rows (cropped to the whole sheet's drawn box, so its frames
stay aligned), each labelled with its index; a magenta box marks the BACK point, a cyan one on the
OVER frames (the back views, where the ring is drawn on his back and the strings run over the sprite);
"null" where the point is not placed (the juggles).
"""
import os
import re
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jp_ship as S  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

ROOT = S.C.ROOT
BG = (46, 49, 58, 255)
PANEL = (20, 18, 26, 255)
MAG = (255, 60, 220, 255)
CYAN = (90, 220, 255, 255)


def font(size, bold=False):
    try:
        return ImageFont.truetype(os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts',
                                               'consolab.ttf' if bold else 'consola.ttf'), size)
    except OSError:
        return ImageFont.load_default()


def read_hooks(gd_path):
    """BACK {key: {sheet: [point or None]}} and OVER {sheet: [frames]} out of the generated table."""
    with open(gd_path, encoding='utf-8') as fh:
        text = fh.read()
    back, key = {}, None
    over = {}
    section = None
    for ln in text.split('\n'):
        if ln.startswith('const BACK'):
            section = 'back'
            continue
        if ln.startswith('const OVER'):
            section = 'over'
            continue
        if section == 'back':
            m = re.match(r'\t&"(\w+)": \{$', ln)
            if m:
                key = m.group(1)
                back[key] = {}
                continue
            m = re.match(r'\t\t&"(\w+)": \[(.*)\],$', ln)
            if m:
                pts = []
                for item in re.finditer(r'Vector2\((\d+), (\d+)\)|null', m.group(2)):
                    pts.append(None if item.group(0) == 'null' else (int(item.group(1)), int(item.group(2))))
                back[key][m.group(1)] = pts
        elif section == 'over':
            m = re.match(r'\t"(\w+)": \[(.*)\],$', ln)
            if m:
                over[m.group(1)] = [int(v) for v in m.group(2).split(',') if v.strip()]
    return back, over


def contact(key, back, over, src_dir, s=2, max_w=2600):
    bname, sheets = S.SHIP[key]
    blocks = []
    ft, fl = font(18, True), font(13, True)
    for rel, fw in sheets:
        name = os.path.basename(rel)
        stem = os.path.splitext(name)[0]
        im = Image.open(os.path.join(src_dir, key, name)).convert('RGBA')
        n = im.width // fw
        fh = im.height
        frames = [im.crop((f * fw, 0, (f + 1) * fw, fh)) for f in range(n)]
        box = None
        for fr in frames:
            b = fr.getbbox()
            if b:
                box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
        box = (max(0, box[0] - 2), max(0, box[1] - 2), min(fw, box[2] + 2), min(fh, box[3] + 2))
        pts = back.get(key, {}).get(stem)
        views = set(over.get(stem, []))
        tiles = []
        for f, fr in enumerate(frames):
            c = fr.crop(box)
            base = Image.new('RGBA', c.size, BG)
            base.alpha_composite(c)
            big = base.resize((c.width * s, c.height * s), Image.NEAREST)
            d = ImageDraw.Draw(big)
            label = str(f)
            if pts is not None:
                p = pts[f] if f < len(pts) else None
                if p is None:
                    label += ' null'
                else:
                    x, y = (p[0] - box[0]) * s + s // 2, (p[1] - box[1]) * s + s // 2
                    col = CYAN if f in views else MAG
                    r = 4 * s if f in views else 2 * s
                    d.rectangle((x - r, y - r, x + r, y + r), outline=col, width=2)
                    if f in views:
                        label += ' OVER'
            d.text((3, 2), label, fill=(255, 255, 110, 255), font=fl)
            tiles.append(big)
        tw, th = tiles[0].size
        cols = max(1, min(n, (max_w - 16) // (tw + 6)))
        rows = (n + cols - 1) // cols
        what = '%d frames of %dx%d' % (n, fw, fh)
        if rel in S.FX:
            what += ' | an effect: recoloured by table, authored alpha kept, no strings, no hooks'
        elif views:
            what += ' | back views (OVER): %s' % sorted(views)
        title = '%s/%s   %s' % (key, name, what)
        tlen = int(ImageDraw.Draw(Image.new('RGBA', (4, 4))).textlength(title, font=ft)) + 24
        blk = Image.new('RGBA', (max(tlen, 16 + cols * (tw + 6)), 34 + rows * (th + 6)), PANEL)
        d = ImageDraw.Draw(blk)
        d.text((10, 8), title, fill=(236, 233, 244, 255), font=ft)
        for i, t in enumerate(tiles):
            blk.alpha_composite(t, (10 + (i % cols) * (tw + 6), 34 + (i // cols) * (th + 6)))
        blocks.append(blk)
    W = max(b.width for b in blocks)
    H = 44 + sum(b.height + 8 for b in blocks)
    out = Image.new('RGBA', (W, H), PANEL)
    ImageDraw.Draw(out).text((10, 10), '%s: every shipped puppet sheet at 2x (take B). Magenta: the BACK point; '
                                       'cyan + OVER: a back view, the ring on his back, strings over the sprite.'
                             % key, fill=(236, 233, 244, 255), font=font(18, True))
    y = 44
    for b in blocks:
        out.alpha_composite(b, (0, y))
        y += b.height + 8
    return out


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    out_dir = os.path.abspath(argv[0])
    real = lambda p: os.path.normcase(os.path.realpath(p))  # noqa: E731
    if real(out_dir).startswith(real(os.path.join(ROOT, 'Assets'))):
        raise SystemExit('refusing: %s is inside Assets' % out_dir)
    src_dir, gd = S.DEST, S.HOOKS_GD
    if '--from' in argv:
        i = argv.index('--from')
        src_dir = os.path.abspath(argv[i + 1])
        gd = os.path.join(src_dir, 'JordanPuppetHooks.gd')
        argv = argv[:i] + argv[i + 2:]
    back, over = read_hooks(gd)
    for key in argv[1:]:
        im = contact(key, back, over, src_dir)
        path = os.path.join(out_dir, 'contact_2x_%s.png' % key)
        im.save(path)
        print('wrote', path, im.size)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
