import sys
from lib import Canvas
from compose import frame
from street import FEET

sky = Canvas.load('out/street_sky.png')
st = Canvas.load('out/street_buildings.png')
fg = Canvas.load('out/street_fg.png')


def placeholder(x_center, feet=FEET, w=18, h=48):
    """Scale stand-in for Burak: plain box, 48 art px tall, feet on the line."""
    c = Canvas(640 * 2, 360)
    return (x_center - w // 2, feet - h + 1, x_center + w // 2 - 1, feet)


def shot(cam, burak_x, name, scale=2):
    f = frame([(sky, 0.25, 0), (st, 1.0, 0)], cam)
    x0, y0, x1, y1 = placeholder(burak_x - cam)
    f.rect(x0, y0, x1, y1, 'F')
    f.box(x0, y0, x1, y1, 'K')
    f.line(x0, y0, x1, y1, 'K')
    f.line(x1, y0, x0, y1, 'K')
    g = frame([(fg, 1.0, 0)], cam)
    for y in range(360):
        for x in range(640):
            if fg.get(x + cam, y) is not None:
                f.p[y][x] = fg.get(x + cam, y)
    f.save(name, scale)
    return f


if __name__ == '__main__':
    shot(0, 150, 'view/walk_start_2x.png')
    shot(640, 922, 'view/walk_poster_2x.png')
