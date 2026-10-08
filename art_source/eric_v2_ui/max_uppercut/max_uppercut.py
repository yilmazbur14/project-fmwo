"""MAX. UPPERCUT! in KNIGHT BREAKER!'s exact recipe (art_source/eric_v2_ui/tier_stamps.py: the kit's 11-row
italic glyphs, the 'knight' scheme, the same 160x20 canvas and two frames), with X and '.' drawn in the same
construction. Writes ONLY into this scratch folder."""
import os, sys
sys.dont_write_bytecode = True
OUT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.realpath("C:/Users/theyi/OneDrive/Documents/new-game-project/art_source/eric_v2_ui"))
from ev2_common import *
import tier_stamps as T
from PIL import Image
OUT = os.path.realpath(os.path.dirname(os.path.abspath(__file__)))
assert "Assets" not in OUT, OUT

WORD = 'MAX. UPPERCUT!'
GLYPHS = dict(T.GLYPHS)
GLYPHS['X'] = ["XXX....XXX",
               "XXX....XXX",
               ".XXX..XXX.",
               "..XXXXXX..",
               "...XXXX...",
               "...XXXX...",
               "...XXXX...",
               "..XXXXXX..",
               ".XXX..XXX.",
               "XXX....XXX",
               "XXX....XXX"]
GLYPHS['.'] = ["..."] * 9 + ["XXX", "XXX"]

def frames():
    out = []
    for bright in (False, True):
        c = LT.word_canvas(WORD, T.SCHEMES['knight'][1 if bright else 0], bright, T.KB_W, T.KB_H, glyphs=GLYPHS)
        bb = bbox(c)
        x0, x1 = bb[0], bb[2]
        mid = (x0 + x1) // 2
        spots = [(x0 + 2, 4, 1), (x1 - 3, 3, 1), (mid, 1, 0)] if bright else [(x0 + 2, 4, 0), (x1 - 3, 3, 0)]
        for (x, y, s) in spots:
            if c.get(x, y) is None:
                sparkle(c, x, y, s, 'W', 'Y')
        out.append(c)
    return out

def to_img(c):
    im = Image.new('RGBA', (c.w, c.h), (0, 0, 0, 0))
    for y in range(c.h):
        for x in range(c.w):
            v = c.get(x, y)
            if v is not None:
                rgb = hex2rgb(v) if isinstance(v, str) and v.startswith('#') else (C[v] if isinstance(v, str) and v in C else v)
                if isinstance(rgb, str): rgb = hex2rgb(rgb)
                im.putpixel((x, y), tuple(rgb[:3]) + (255,))
    return im

if __name__ == '__main__':
    print('width', LT.word_width(WORD, GLYPHS), 'of', T.KB_W, '; KNIGHT BREAKER! was', LT.word_width('KNIGHT BREAKER!', T.GLYPHS))
    fs = frames()
    s = strip(fs)
    check_db32(s, 'max_uppercut')
    print('bbox', bbox(fs[0]), bbox(fs[1]))
    sheet = Image.new('RGBA', (T.KB_W * 2, T.KB_H), (0, 0, 0, 0))
    for i, f in enumerate(fs):
        sheet.paste(to_img(f), (i * T.KB_W, 0))
    sheet.save(os.path.join(OUT, 'max_uppercut.png'))
    sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(os.path.join(OUT, 'max_uppercut_3x.png'))
    print("wrote", OUT)
