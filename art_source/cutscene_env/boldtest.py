from lib import Canvas
from bold import word, word_width
from type import paint_text

c = Canvas(300, 120, 'U')
y = 6
for s in ('MEMBERS', 'WANTED', 'TRYOUTS', 'ARENA #1'):
    pts = word(s, 6, y)
    paint_text(c, pts, 'W', outline='N', shadow='I', shadow_off=(0, 3))
    print(s, word_width(s))
    y += 28
c2 = Canvas(300, 120, 'W')
y = 6
for s in ('MEMBERS', 'WANTED', 'ARENA #1'):
    pts = word(s, 6, y)
    paint_text(c2, pts, 'R', outline='K', shadow='M', shadow_off=(0, 2))
    y += 28
big = Canvas(600, 120, 'N')
big.blit(c, 0, 0)
big.blit(c2, 300, 0)
big.save('view/boldtest_4x.png', 4)
