"""Head builder for the idle: rows over x 17..47 (31 cols), y 0..28.
Rows are assembled from segments so widths are exact; face interiors are x 23..43 (21 chars).
usage: python mkhead.py [variant] -> writes head_<variant>.txt"""
import sys, os

HERE = os.path.dirname(os.path.abspath(__file__))


def J(*segs):
    return ''.join(segs)


HAIR = {
    0: J('.' * 15, '#' * 8, '.' * 8),
    1: J('.' * 11, '####', 'JJjjjHhh', '##', '.' * 6),
    2: J('.' * 8, '###', 'JJjjjHHjjjHHhh', '#', '.' * 5),
    3: J('.' * 6, '##', 'JjjjHHhkjjjHHhkjHh', '#', '.' * 4),
    4: J('.' * 4, '#', 'j', '#' * 7, 'hHhh', '#' * 7, 'hhk', '#', '.' * 3),
    5: J('.' * 3, '#', 'j', '#', 'CcBBBbb', '#', '##', '#', 'cBBBbbb', '#', 'hhk', '#', '..'),
    6: J('.' * 3, '#', 'h', '#', 'cBBbbbb', '#', 'kk', '#', 'Bbbbbbb', '#', 'hkh', '#', '..'),
    7: J('.' * 3, '#', 'hh', '#' * 7, 'hHhh', '#' * 7, 'hhkhh', '#', '.'),
    8: J('..', '#', 'hjjHhhkHjjHhhkHjjHhhkhhkhk', '#', '.'),
    9: J('..', '#', 'hHhhk', 'hddddddddddddddkh', 'khhk', '#', '.'),
}


def frame_row(y, inner):
    """Wrap a face interior with the head outline / ear for row y."""
    n = len(inner)
    if 10 <= y <= 22:
        assert n == 21, (y, n, inner)
    pre_suf = {
        10: ('..#hhk', 'hk#.'),
        11: ('..#hkk', 'k#..'),
        12: ('...##k', 'h#..'),
        13: ('..#sd#', '#...'),
        14: ('..#af#', '#...'),
        15: ('..#sf#', '#...'),
        16: ('..#df#', '#...'),
        17: ('..#dd#', '#...'),
        18: ('...#d#', '#...'),
        19: ('....##', '#...'),
        20: ('.....#', '#...'),
        21: ('.....#', '#...'),
        22: ('.....#', '#...'),
    }
    if y in pre_suf:
        p, s = pre_suf[y]
        return p + inner + s
    lower = {  # y: (lead dots, inner width, trail dots) with outline on both sides
        23: (6, 19, 4), 24: (6, 19, 4), 25: (7, 17, 5), 26: (8, 15, 6), 27: (10, 11, 8),
    }
    if y in lower:
        a, w, b = lower[y]
        assert n == w, (y, n, w, inner)
        return '.' * a + '#' + inner + '#' + '.' * b
    raise ValueError(y)


# ---------------------------------------------------------------- eye / brow variants (rows 11..15, x23..43)
VARIANTS = {
    'A': {  # thick brows, outer ends drop; open-ish squint with glint
        10: J('saaaassssssssssssdddf'),
        11: J('ss', 'hkkkkh', 'sssss', 'hkkkkh', 'dd'),
        12: J('s', 'kkkkkkk', 'sssss', 'kkkkkkk', 'd'),
        13: J('k', 'ss####', 'ssass', '####sd', 'k'),
        14: J('ss', '#eewe#', 'sssas', '#ewe#', 'ddd'),
        15: J('sa', 'sdssd', 'sssadss', 'dssd', 'sdd'),
    },
    'B': {  # arched brows lifted off the eyes; lidded crescent eyes, iris + glint, cheek crinkle
        10: J('saaahkkhssssshkkhsddf'),
        11: J('sahkkkkkkhssshkkkkkhd'),
        12: J('skh', 'ssss', 'hkssskh', 'sss', 'hkd'),
        13: J('sss', '####', 'ssassss', '###', 'ddd'),
        14: J('ss', '#ewee#', 'ssass', '#ewe#', 'dd'),
        15: J('sas', 'dsssd', 'ssadss', 'dssd', 'sd'),
    },
    'C': {  # arched brows; happy closed crescents (^ ^) with lash corners
        10: J('saaahkkhssssshkkhsddf'),
        11: J('sahkkkkkkhssshkkkkkhd'),
        12: J('skh', 'ssss', 'hkssskh', 'sss', 'hkd'),
        13: J('sss', '.##.', 'ssassss', '.##', 'ddd').replace('.', 's'),
        14: J('ss', '#eeee#', 'ssass', '#eee#', 'dd'),
        15: J('sa', '#dssd#', 'sadss', '#dsd#', 'dd'),
    },
    'D': {  # thick straight-ish brows raised 1px; big warm eyes: lid, iris w/ glint, lower lash dots
        10: J('sahkkkkkhsssshkkkkhdf'),
        11: J('skkkkkkkksssskkkkkkkd'),
        12: J('khssssssskssssssssshk').replace('ssssssskssss', 'ssssssssssss')[:21],
        13: J('ss', '.####.', 'sssss', '.###.', 'ddd').replace('.', 's'),
        14: J('ss', '#eewe#', 'ssass', '#ewe#', 'ddd'),
        15: J('sas', 'd##d', 'ssadss', 'd##', 'dsd'),
    },
}

LOWER = {
    16: J('srrrssssssasdsssrrsdd'),   # blush, nose tip
    17: J('srrsssssdfasfdsssrsdd'),   # nostrils
    18: J('sssssshkkkkdkkkkhssdd'),   # pencil mustache (philtrum gap)
    19: J('ssssssssssdsdssssssdd'),   # upper lip
    20: J('ssss', '#' * 15, 'sd'),    # grin top
    21: J('sss', '#wwwWwwwWwwwWwww#', 'd'),
    22: J('tsss', '#Wwwwwwwwwwwww#', 'sd'),
    23: J('tss', '#' * 13, 'dsd'),   # grin bottom (19 wide)
    24: J('tstsdddhkhdddsstd'[:0] + 'tssddddhkhddddstT'[:0] + 'tsssddddhkhdddsstd'[:19].ljust(19, 'd')),
    25: J('tstsssskkksssstdT'),       # 17
    26: J('TtdsdhkhdddstT'[:0] + 'TtdsddhkhddstTd'[:15]),   # 15
    27: J('TdfdhkhdfTd'[:11]),        # 11
}


def build_rows(v):
    rows = {}
    rows.update(HAIR)
    var = VARIANTS[v]
    for y in range(10, 16):
        rows[y] = frame_row(y, var[y])
    for y in range(16, 28):
        rows[y] = frame_row(y, LOWER[y])
    rows[28] = J('.' * 12, '#' * 9, '.' * 10)
    for y in range(29):
        assert len(rows[y]) == 31, (y, len(rows[y]), rows[y])
    return [rows[y] for y in range(29)]


if __name__ == '__main__':
    vs = sys.argv[1:] or list(VARIANTS)
    for v in vs:
        rows = build_rows(v)
        with open(os.path.join(HERE, 'head_%s.txt' % v), 'w') as f:
            f.write('@17,0\n' + '\n'.join(rows) + '\n')
        print(v, 'ok')
