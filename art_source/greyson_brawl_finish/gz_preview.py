"""Previews of the finishing half, written ONLY to the scratch folder (never into Assets):

    python -B gz_preview.py [SHEET ...]        # 4x strips (plain + anchors marked), for each sheet
    python -B gz_preview.py --gif SHEET ms     # an animated GIF at 3x on the mat colour

The anchors are drawn as small crosses: crown cyan, chin magenta, fist amber, gauntlet green.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gz_base as Z  # noqa: E402
import gz_sheets as S  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

K = Z.K
OUT = Z.SCRATCH
BG = (46, 49, 58, 255)
MAT = (133, 171, 102, 255)
MARK = {'crown': (0, 255, 255), 'chin': (255, 0, 255), 'fist': (255, 200, 0),
        'gauntlet': (0, 255, 0), 'contact': (255, 255, 255)}


def up(im, s, bg=BG):
    b = Image.new('RGBA', im.size, bg)
    b.alpha_composite(im)
    return b.resize((im.width * s, im.height * s), Image.NEAREST)


def marked(im, anc, s=4):
    big = up(im, s)
    d = ImageDraw.Draw(big)
    for k, col in MARK.items():
        p = anc.get(k)
        if not p:
            continue
        cx, cy = p[0] * s + s // 2, p[1] * s + s // 2
        d.line([(cx - 5, cy), (cx + 5, cy)], fill=col)
        d.line([(cx, cy - 5), (cx, cy + 5)], fill=col)
    return big


def strip(name, s=4, marks=False):
    frames = S.build_sheet(name)
    tiles = []
    for label, cv, anc in frames:
        im = cv.image()
        t = marked(im, anc, s) if marks else up(im, s)
        head = Image.new('RGBA', (t.width, 28), (20, 20, 26, 255))
        st = K.stats(im)
        dr = ImageDraw.Draw(head)
        dr.text((4, 2), '%s f%d %s' % (name, len(tiles), label), fill=(230, 230, 230))
        dr.text((4, 14), 'black %.1f%% col %d  crown %s chin %s' % (
            100 * st['black'], st['colours'], anc.get('crown'), anc.get('chin')), fill=(170, 170, 180))
        col = Image.new('RGBA', (t.width, t.height + 28), (20, 20, 26, 255))
        col.paste(head, (0, 0))
        col.paste(t, (0, 28))
        tiles.append(col)
    out = Image.new('RGBA', (sum(t.width for t in tiles) + 4 * (len(tiles) - 1), tiles[0].height),
                    (10, 10, 14, 255))
    x = 0
    for t in tiles:
        out.paste(t, (x, 0))
        x += t.width + 4
    return out


def gif(name, ms, s=3, bg=MAT):
    frames = [up(cv.image(), s, bg).convert('P', palette=Image.ADAPTIVE)
              for _, cv, _ in S.build_sheet(name)]
    path = os.path.join(OUT, '%s_%dx.gif' % (name, s))
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=ms, loop=0,
                   disposal=2)
    return path


def main(argv):
    os.makedirs(OUT, exist_ok=True)
    if argv and argv[0] == '--gif':
        print(gif(argv[1], int(argv[2]) if len(argv) > 2 else 120))
        return
    names = argv or list(S.SHEETS)
    for n in names:
        strip(n).save(os.path.join(OUT, '%s_4x.png' % n))
        strip(n, marks=True).save(os.path.join(OUT, '%s_4x_marked.png' % n))
        print('wrote', n)


if __name__ == '__main__':
    main(sys.argv[1:])
