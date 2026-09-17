"""Hand-painted body layer (tail, necks, collars, torso, legs). Writes parts/body.txt."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from canvas import save_rows

D = lambda n: '.' * n
rows = {}

def row(y, *segs):
    s = ''.join(segs)
    assert len(s) == 64, 'row %d has %d chars' % (y, len(s))
    rows[y] = s

for y in range(0, 8):
    row(y, D(64))

# ------------------------------------------------------------------ TAIL (white flag tip)
row(8,  D(10), 'KKKK', D(50))
row(9,  D(8), 'KKWWWwKK', D(48))
row(10, D(6), 'KKWWwwwwwvK', D(47))
row(11, D(5), 'KWWwvvKKKKKK', D(47))
row(12, D(4), 'KWwwvvK', D(53))
row(13, D(3), 'KWwwvvK', D(54))
row(14, D(3), 'KWwwvK', D(55))
row(15, D(2), 'KWwwvvK', D(55))
row(16, D(2), 'KWwwvK', D(56))
row(17, D(1), 'KWwwvvK', D(56))
row(18, D(1), 'KWwwvK', D(57))
row(19, D(1), 'KWwwvK', D(57))
# centre neck (hidden under chin) starts at y20
row(20, 'KWwwvvK', D(19), 'KuuuuuuuuuuK', D(26))
row(21, 'KWwwvK', D(20), 'KuuuuuuuuuuK', D(26))
row(22, 'KwwvuK', D(20), 'KuuuuuuuuuuK', D(26))
# black tail base begins (jagged white tuft at x3)
row(23, 'KBkwjK', D(20), 'KuuuuuuuuuuK', D(26))
# ------------------------------------------------------------------ CENTRE COLLAR (y24-29)
row(24, 'KBkkjK', D(20), 'KRRRRRRRRRrK', D(26))
row(25, 'KBkkjK', D(20), 'KRrrrrrrrrsK', D(26))
row(26, 'KBkkjK', D(20), 'KssssssssssK', D(26))
row(27, 'KBkkjK', D(20), 'KKxXyKKxXyKK', D(26))
row(28, 'KBkkjK', D(20), 'KuKXKuuKXKuK', D(26))
row(29, 'KBkkjK', D(20), 'KvuKuvvuKuuK', D(26))
# ------------------------------------------------------------------ NECKS
row(30, 'KBkkjK', D(4), 'KuuuuuuuuuuK', D(4), 'KWwwvwwwvvuK', D(4), 'KuuuuuuuuuuK', D(10))
row(31, 'KBkkjjK', D(3), 'KuuuuuuuuuuK', D(4), 'KWWwwwwwvvuK', D(4), 'KuuuuuuuuuuK', D(10))
row(32, 'KBkkkjK', D(3), 'KuuuuuvvvvvK', D(4), 'KWWwwwwwvvuK', D(4), 'KvvvvvuuuuuK', D(10))
row(33, 'KBkkkjK', D(3), 'KuuuuuuuuuuK', D(4), 'KWwwwwwwvvuK', D(4), 'KuuuuuuuuuuK', D(10))
row(34, 'KBBkkjjK', 'KvvuuuuuuuuuuK', D(4), 'KWWwwwwwvvuK', D(4), 'KuuuuuuuuuuvvK', D(8))
row(35, '.KBkkkjK', 'KwvuuuuuuuuuuK', D(4), 'KWwwwwwwvvuK', D(4), 'KuuuuuuuuuuvwK', D(8))
row(36, '.KBkkkjjK', 'kkkkkkkkkkkkkk', 'jjj', 'KWwwwwwvvvuK', 'jjj', 'kkkkkkkkkkkkkk', D(9))
row(37, '.KBBkkkjj', 'kkkkkkkkkkkkkk', 'jjk', 'vWWwwwwwvvu', 'j', 'jjj', 'kkkkkkkkkkkk', 'K', D(10))
# ------------------------------------------------------------------ TORSO
row(38, '.KBgBkkkkjjj', 'jjj', 'kk', 'jjj', 'jjjkkk', 'wWWwwwwwwvv', 'jkkj', 'jjjjjjjjjjjjK', D(10))
row(39, '.KBgBBkkkkkkkkk', 'jjjj', 'kkkkkkj', 'wWwwwwwwwvv', 'jkkkkkkj', 'jjjjjjjjjK', D(9))
row(40, '.KBBBkkBkkkkkk', 'kkkk', 'kkkjkkkj', 'wWWwwwwwwvvu', 'jkkkkjjjjjjjjjjjK', D(9))
row(41, '.KBBkkkkkkBkkk', 'Wwwv', 'kjkkkkjj', 'wWwwwwwwvvvu', 'jkkkjjjjjjjjjjjjK', D(9))
row(42, '.KBkkkkkkkkkkj', 'wwwv', 'jkkkjkjj', 'vwwwwwwvvvvu', 'jjkjjjjjkjjjjjjjK', D(9))
row(43, '.KBkkkBkkkkkj', 'Wwwv', 'jkkkkjjjj', 'vwwwwwvvvvuu', 'jjjjjjjjjjjjjjjK', D(10))
row(44, '.KBkkkkkkkjkj', 'wwwv', 'jjkjjjjjj', 'vwwwwvvvvuuu', 'jjjjjjjjjjjjjjjK', D(10))
row(45, '.Kkkkkkjkkjjj', 'wwvv', 'jjjjjjjjj', 'vwwwvvvvuuuu', 'jjjjjjjjjjjjjjK', D(11))
# tan hip edging with fur tufts, belly whites
row(46, '..Kkkj32j323j', 'wvv', 'jjjjjjjjju', 'vwwvvvvuuuuu', 'ujjjjjjjjjjjjK', D(12))
row(47, '..K3221223334', 'wwv', 'vuuuuuuuuu', 'vwwvvvuuuuuu', 'uujjujuuuuuuK', D(13))
row(48, '..K322334wwvvvvuu', 'uuuuuuuuu', 'uwwvvvuuuuuu', 'uuuuuuuuuuKK', D(14))
row(49, '..K234Wwwwwwvvvuu', 'KKKKKKKKK', 'uwwvvuuuuuuu', 'uuuuuuuuKK', D(16))
# ------------------------------------------------------------------ LEGS
row(50, '..K', 'wWWwwwwwvvvuu', 'K', 'uuuu', 'K', D(4), 'K', 'WWwwwvvuuuuuuuuuuuu', 'K', D(17))
row(51, D(3), 'KWwwwwwvvvuuuK', 'vuuuK', D(4), 'KWWwwwvuK', 'KKK', 'KvvvuuuK', D(18))
row(52, D(3), 'KWwwwwvvvuuuK', 'uvuuuK', D(4), 'KWwwwwvuK', D(3), 'KvvvuuuK', D(18))
row(53, D(3), 'KWwwwvvvuuuK', 'uuvvuuK', D(4), 'KWwwwvvuK', D(3), 'KvvuuuuK', D(18))
row(54, D(3), 'KWwwvvvuuuK', 'uuvvuuK', D(5), 'KWwwwvvuK', D(3), 'KvvuuuuK', D(18))
row(55, D(4), 'KWwvvuuuK', 'uvvuuuuK', D(5), 'KWwwvvvuK', D(3), 'KvvuuuuK', D(18))
row(56, D(4), 'KWwvvuuK', 'uvvuuuuK', D(6), 'KWwwvvuuK', D(3), 'KvvuuuuK', D(18))
row(57, D(4), 'KWwvvuuK', 'uvvuuuuK', D(6), 'KWwwvvuuK', D(3), 'KvvuuuuK', D(18))
row(58, D(4), 'KWwwvvuK', 'uvvvuuuuK', D(5), 'KWwwvvuuK', D(3), 'KwvvuuuK', D(18))
row(59, D(3), 'KWWwwvvuuK', 'vvvuuuuuK', D(3), 'KWWwwvvuuK', D(2), 'KwwvvuuuuK', D(17))
row(60, D(3), 'KWWwwwvvuuK', 'vvvuuuuuK', D(1), 'KWWwwwvvuuuK', D(1), 'KwwvvvuuuuK', D(16))
row(61, D(2), 'KWwwKwwKvuuuK', 'vKuuKuuuK', 'KWwwKwwKvuuuK', 'KwvKvuKuuuuK', D(15))
row(62, D(2), 'KwwwKwvKuuuuK', 'KKKKKKKKK', 'KwwwKwvKuuuuK', 'KKKKKKKKKKKK', D(15))
row(63, D(2), 'KKKKKKKKKKKKK', D(9), 'KKKKKKKKKKKKK', D(27))

grid = [rows[y] for y in range(64)]
save_rows(os.path.join(HERE, 'parts', 'body.txt'), grid)
print('ok')
