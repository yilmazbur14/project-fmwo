"""Write the demon-god Jordan approval pass (the user's reference direction): two variants of the
idle sprite, the two separate effect layers, the void backdrop, the comparison sheet and one
1920x1080 mock per variant. Every file goes into art_source/jordan_god/ and nowhere else; nothing
is wired into the game.

A bare run writes nothing:

    python jg_export.py                  # print this and exit
    python jg_export.py --check          # build, audit and measure everything, write nothing
    python jg_export.py --write          # write the files into art_source/jordan_god/

Each sprite PNG is saved with an .aseprite beside it (Aseprite CLI, batch mode), and the .aseprite
is re-exported and compared pixel for pixel with the PNG (imgdiff.pixel_diff: alpha everywhere,
colour wherever a pixel shows). Nothing is written unless the god sprites pass the audit (no
keyline gaps, stray specks, pinholes or semi-alpha).
"""
import os
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jg_base as B  # noqa: E402
import jg_column as CO  # noqa: E402
import jg_lord as L  # noqa: E402
import jg_present as PR  # noqa: E402
import jg_runes as RU  # noqa: E402
import jg_void as V  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

OUT = HERE
SPRITES = ('jordan_god_A1', 'jordan_god_A2', 'jordan_god_runes', 'jordan_god_column', 'void_bg')


def _under(path, root):
    p, r = os.path.normcase(os.path.realpath(path)), os.path.normcase(os.path.realpath(root))
    return p == r or p.startswith(r + os.sep)


def build_all():
    ims = {
        'jordan_god_A1': L.image('A1'),
        'jordan_god_A2': L.image('A2'),
        'jordan_god_runes': RU.image(),
        'jordan_god_column': CO.image(),
        'void_bg': V.backdrop(),
    }
    return ims


def audit_god(variant):
    px = L.build(variant)
    a = B.audit(px)
    return a


def report(ims):
    lines = []
    ok = True
    for name, im in ims.items():
        st = B.stats(im)
        bb = im.getbbox()
        line = '%-18s %dx%d  opaque %5d  colours %2d  black %5.1f%%  semi %d  bbox %s' % (
            name, im.width, im.height, st['opaque'], st['colours'], 100 * st['black'], st['semi'], bb)
        if name.startswith('jordan_god_A'):
            a = audit_god(name[-2:])
            line += '  gaps %d lone %d holes %d' % (len(a['gaps']), len(a['lone']), len(a['holes']))
            if a['gaps'] or a['lone'] or a['holes'] or st['semi']:
                ok = False
            if bb[3] != im.height:
                line += '  (lowest texel not on the last row!)'
                ok = False
        if st['semi']:
            ok = False
        lines.append(line)
    return ok, lines


# ------------------------------------------------------------------ presentation

def _text(draw, xy, s, col=(226, 222, 240, 255)):
    draw.text(xy, s, fill=col)


def comparison(ims):
    """A1 and A2 side by side: at 3x (the game's scale) over the void, then at 1:1 with the two
    effect layers and the void backdrop they will hang in."""
    bgn = ims['void_bg']
    pad = 8
    panels3 = []
    for v in ('A1', 'A2'):
        god = ims['jordan_god_' + v]
        w, h = god.width + 2 * pad, god.height + 2 * pad
        patch = bgn.crop((320 - w // 2, 0, 320 - w // 2 + w, h)).copy()
        patch.alpha_composite(god, (pad, pad))
        panels3.append(patch.resize((w * 3, h * 3), Image.NEAREST))
    gap = 24
    top = 56
    sheet_w = panels3[0].width * 2 + gap * 3
    row2_h = 360 + 40
    sheet_h = top + panels3[0].height + 36 + row2_h + 20
    sheet = Image.new('RGBA', (sheet_w, sheet_h), (10, 8, 16, 255))
    d = ImageDraw.Draw(sheet)
    _text(d, (gap, 12), 'Demon-god Jordan, the reference direction: A1 shows his face, A2 is a full mask.')
    _text(d, (gap, 30), 'Top row: 3x (the game scale; one texel = 3 screen px). Bottom row: 1:1 texels, '
                        'with the rune circle and fire column layers and the void_bg they hang in.')
    x = gap
    labels = ('A1  his face: v2 shout face turned frontal, eyes and mouth burning',
              'A2  full mask: brow plate, burning slits, beard as glowing jaw cracks')
    for p, lab in zip(panels3, labels):
        sheet.paste(p, (x, top))
        _text(d, (x + 4, top + p.height + 8), lab)
        x += p.width + gap
    # bottom row at 1:1
    y2 = top + panels3[0].height + 36
    x = gap
    for v in ('A1', 'A2'):
        god = ims['jordan_god_' + v]
        tile = Image.new('RGBA', (god.width + 16, god.height + 16), (10, 8, 16, 255))
        tile.alpha_composite(bgn.crop((160, 0, 160 + god.width + 16, god.height + 16)), (0, 0))
        tile.alpha_composite(god, (8, 8))
        sheet.paste(tile, (x, y2))
        _text(d, (x, y2 + tile.height + 4), v + ' at 1:1')
        x += tile.width + gap
    for name, lab in (('jordan_god_runes', 'rune circle layer'), ('jordan_god_column', 'fire column layer')):
        im = ims[name]
        tile = Image.new('RGBA', (im.width + 16, im.height + 16), (4, 3, 10, 255))
        tile.alpha_composite(im, (8, 8))
        sheet.paste(tile, (x, y2))
        _text(d, (x, y2 + tile.height + 4), lab)
        x += tile.width + gap
    small = PR.compose(ims['jordan_god_A1'], L.ANCHOR, runes=ims['jordan_god_runes'], runes_centre=L.CORE,
                       column=ims['jordan_god_column'], column_pivot=CO.PIVOT, backdrop=bgn)
    if x + small.width <= sheet_w:
        sheet.paste(small, (x, y2))
        _text(d, (x, y2 + small.height + 4), 'A1 in the void, 1:1 (the whole screen, 640x360)')
    return sheet


def mocks(ims):
    out = {}
    for v in ('A1', 'A2'):
        out[v] = PR.mock(ims['jordan_god_' + v], L.ANCHOR, runes=ims['jordan_god_runes'], runes_centre=L.CORE,
                         column=ims['jordan_god_column'], column_pivot=CO.PIVOT, backdrop=ims['void_bg'])
    return out


# ------------------------------------------------------------------ files

def aseprite(*args):
    subprocess.run([B.ASEPRITE, '-b'] + list(args), check=True, capture_output=True)


def write(ims):
    if _under(OUT, os.path.join(B.ROOT, 'Assets')):
        raise SystemExit('refusing: %s is inside Assets' % OUT)
    if not _under(OUT, os.path.join(B.ROOT, 'art_source', 'jordan_god')):
        raise SystemExit('refusing: %s is not art_source/jordan_god' % OUT)
    tmp = tempfile.mkdtemp(prefix='jgod_')
    results = []
    for name in SPRITES:
        im = ims[name]
        tpng = os.path.join(tmp, name + '.png')
        tase = os.path.join(tmp, name + '.aseprite')
        im.save(tpng)
        aseprite(tpng, '--save-as', tase)
        back = os.path.join(tmp, name + '_rt.png')
        aseprite(tase, '--save-as', back)
        d = pixel_diff(Image.open(tpng), Image.open(back))
        if d:
            raise SystemExit('%s: the .aseprite does not round-trip: %s' % (name, d))
        os.replace(tpng, os.path.join(OUT, name + '.png'))
        os.replace(tase, os.path.join(OUT, name + '.aseprite'))
        results.append('wrote %s.png + .aseprite (round trip identical)' % name)
    comparison(ims).save(os.path.join(OUT, 'jordan_god_compare.png'))
    results.append('wrote jordan_god_compare.png')
    for v, m in mocks(ims).items():
        m.save(os.path.join(OUT, 'jordan_god_mock_%s.png' % v))
        results.append('wrote jordan_god_mock_%s.png %s' % (v, m.size))
    return results


def main(argv):
    if not argv or argv[0] not in ('--check', '--write'):
        print(__doc__)
        return 2
    ims = build_all()
    ok, lines = report(ims)
    for ln in lines:
        print(ln)
    god = ims['jordan_god_A1']
    print('A1 on screen (anchor at 960,600):', PR.screen_box(god, L.ANCHOR))
    if not ok:
        print('audit FAILED: nothing written')
        return 1
    if argv[0] == '--write':
        for r in write(ims):
            print(r)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
