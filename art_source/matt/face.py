"""Matt's faces, drawn pixel by pixel. Each map covers x 31-65 (35 columns, ruled in fives), one row
per y, and carries its own keylines. '.' is transparent (whatever is under stays).

Likeness from the photo: a broad round face with full cheeks and a wide rounded jaw, straight dark
brows that dip at their outer ends, narrow relaxed dark eyes, a broad nose with a rounded tip, and
short cropped sides. Light from the upper left: forehead and left cheek lit, right cheek and jaw in
shade, the right ear darker than the left.
"""
X0 = 31

IDLE_Y0 = 29
IDLE = [
    # x: 31-35 36-40 41-45 46-50 51-55 56-60 61-65      y
    ".kiii iiikk kkkkk kkkkk kkkkk kkiii iiik.",       # 29  hairline
    ".kiii iik11 11222 22222 22222 23kii iiik.",       # 30
    ".kiii ik112 22222 22222 22222 233ki iiik.",       # 31
    ".kiii k1122 22222 22222 2hhhh hh33k iiik.",       # 32  right brow raised: the cheek
    ".kiii k12hh hhhh2 22222 22hhh hhh3k iiik.",       # 33
    ".kiii k1hhh hhh22 22222 22222 2223k iiik.",       # 34
    ".kkik 1kkkk kkk22 22222 22kkk kkkk3 kikk.",       # 35  lashes
    "k323k 12kWh hXk22 21222 22kWh hXk33 k434k",       # 36  eyes
    "k343k 123kj hk322 21232 223kj hk333 k454k",       # 37
    "k343k 12233 33222 21232 22333 33233 k454k",       # 38
    "k353k 12222 22222 21232 22222 22233 k464k",       # 39  ear canals
    "k333k 12222 22222 21132 22222 22233 k444k",       # 40
    ".k44k 12222 22222 32123 22222 22233 k55k.",       # 41  nose tip
    "..kkk 12222 22223 46364 32222 22233 kkk..",       # 42  nostrils
    "..... k1222 22222 23332 22222 2233k .....",       # 43
    "..... k1222 22222 22222 2222k k233k .....",       # 44  grin corner curls up
    "..... k1222 kkkkk kkkkk kkkkW k323k .....",       # 45  upper lip
    "..... k1222 2kWWW WWWWW WWWWk 2333k .....",       # 46  teeth
    "..... .k122 22knq rrqmn nnXk2 333k. .....",       # 47  tongue tip
    "..... .k122 222kk kkkkk kkk33 333k. .....",       # 48  lower lip line
    "..... ..k12 22223 11113 32333 34k.. .....",       # 49
    "..... ...kk 22222 23332 33344 kk... .....",       # 50
    "..... ..... kk332 22333 444kk ..... .....",       # 51
    "..... ..... ..kkk kkkkk kkk.. ..... .....",       # 52  chin
]


def halves(rows):
    """(left x 31-48, right x 49-65) row pairs -> full rows."""
    out = []
    for l, r in rows:
        assert len(l) == 18, (l, len(l))
        assert len(r) == 17, (r, len(r))
        out.append(l + r)
    return out


# The roar: the jaw dropped impossibly far (chin from row 51 to row 61), a mouth 19 wide and 15
# tall with fangs top and bottom, a dark throat, pink walls and a big lit tongue with a centre
# groove; a heavy V of brow over a furrow, glowing Exploud-red eyes, a snarling nose, cheeks
# pushed up. Unshifted coordinates: the frame lowers the whole head as he leans in.
ROAR_Y0 = 29
ROAR = halves([
    # left x 31-48          right x 49-65             y
    (".kiiiiiikkkkkkkkkk", "kkkkkkkkkiiiiiik."),   # 29  hairline
    (".kiiiiik1111222222", "222222223kiiiiik."),   # 30
    (".kiiiikhh112222234", "32222223hhkiiiik."),   # 31  brows: outer ends high
    (".kiiik1hhhhh222334", "33222hhhhh3kiiik."),   # 32
    (".kiiik1222hhhhh335", "33hhhhh2333kiiik."),   # 33  furrow between them
    (".kiiik1kkkkkhhhh34", "3hhhhkkkkk3kiiik."),   # 34  inner ends low, lashes
    (".kkik12kQPOPQk3222", "223kQPOPQk33kikk."),   # 35  red eyes
    ("k323k122kTQQTk3222", "223kTQQTk333k434k"),   # 36
    ("k343k1223kkkk32413", "4423kkkk3333k454k"),   # 37  snarl creases
    ("k343k1112223322212", "322233222223k454k"),   # 38  cheeks pushed up
    ("k353k1122222223412", "343222222233k464k"),   # 39  ear canals
    ("k334k1222222222311", "232222222233k544k"),   # 40
    (".k44k1222222334633", "364332222233k55k."),   # 41  nostrils flared
    ("..kkk1222422233444", "443322242233kkk.."),   # 42
    ("....k12234kkkkkkkk", "kkkkkkk43233k...."),   # 43  upper lip
    ("...k1223kkWWWWWWWW", "WWWWWXXkk3334k..."),   # 44  upper teeth; the jaw widens
    ("...k122kWWWXnnmmmm", "mmmnnWWWXk334k..."),   # 45  fangs
    ("..k122kqqWXnnmmkkk", "kkmmnnWXppk334k.."),   # 46  the throat drops to black
    ("..k12kqqpWnnmkkkkk", "kkkkmnnXpppk34k.."),   # 47  throat
    ("..k12kqqpnnmmmkkkk", "kkkmmmnnpppk34k.."),   # 48
    ("..k12kqpnnmmmmqrrr", "rrqmmmmnnppk34k.."),   # 49  tongue
    ("..k12kqpnmnqrRRrrq", "rrrrrqnmnppk34k.."),   # 50
    ("..k12kqpnqrRRrrrrq", "rrrrrrrqnppk34k.."),   # 51
    ("..k12kpnqrRRrrrrrq", "rrrrrrrrqnpk34k.."),   # 52
    ("..k12kpqWrrrrrrrrq", "rrrrrrrrWqpk34k.."),   # 53  lower fangs
    ("..k12kpWWqrrrrrrrq", "rrrrrrqqWXpk34k.."),   # 54
    ("..k122kWWXkkkkkkkk", "kkkkkkkWWXk334k.."),   # 55  tongue sits behind the teeth
    ("..k1223kWWWWWWWWWW", "WWWWWXXXXk3344k.."),   # 56  lower teeth
    ("...k2233kkXXXXXXXX", "XXXXxxxkk3444k..."),   # 57
    ("....k22333kkkkkkkk", "kkkkkkk34444k...."),   # 58  lower lip
    (".....k222111112222", "23333344444k....."),   # 59
    ("......kk2223332223", "333344445kk......"),   # 60
    ("........kk33333334", "4444455kk........"),   # 61
    ("..........kk444444", "44555kk.........."),   # 62
    ("............kkkkkk", "kkkkk............"),   # 63  chin
])


def check(rows, name):
    """Row widths, and which rows have their keylines off-mirror (x' = 96 - x)."""
    bad = []
    for i, r in enumerate(rows):
        s = r.replace(' ', '')
        if len(s) != 35:
            bad.append('%s row %d: width %d' % (name, i, len(s)))
            continue
        ks = {X0 + j for j, ch in enumerate(s) if ch == 'k'}
        off = sorted(x for x in ks if (96 - x) not in ks)
        if off:
            bad.append('%s row %d: unmirrored k at %s' % (name, i, off))
    return bad


if __name__ == '__main__':
    for line in check(IDLE, 'idle'):
        print(line)
    for line in check(ROAR, 'roar'):
        print(line)
