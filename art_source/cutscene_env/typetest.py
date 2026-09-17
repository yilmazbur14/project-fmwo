from lib import Canvas
from fonts import F57
from type import bitmap, epx, nearest, pixels, paint_text, size

c = Canvas(560, 300, 'W')
c.rect(0, 0, 559, 299, 'U')
y = 8
x = 8
for name, fn in (('epx4', lambda b: epx(epx(b))), ('near4', lambda b: nearest(b, 4)), ('epx2n2', lambda b: nearest(epx(b), 2))):
    for word in ('MEMBERS', 'WANTED'):
        bm = fn(bitmap(word, F57))
        paint_text(c, pixels(bm, x, y), 'W', outline='N', shadow='I', shadow_off=(0, 3))
        x += size(bm)[0] + 16
    x = 8
    y += 40
for name, fn in (('epx2', lambda b: epx(b)), ('near2', lambda b: nearest(b, 2))):
    bm = fn(bitmap('TRYOUTS AT ARENA #1', F57))
    paint_text(c, pixels(bm, x, y), 'W', shadow='I', shadow_off=(0, 2))
    y += 24
bm = bitmap('Earn your invite  @everyone', F57)
paint_text(c, pixels(bm, x, y), 'W')
y += 16
bm = epx(bitmap('Earn your invite  @everyone', F57))
paint_text(c, pixels(bm, x, y), 'W')
c.save('view/typetest_2x.png', 2)
