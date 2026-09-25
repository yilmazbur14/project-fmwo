"""The three mouth points (middle, left, right) of every perch frame, and the breath cone's apex, in
texels on a 192x160 frame (x right, y down, origin top-left; the frame's anchor is (96, 151)).

    python mouths.py        # prints the table and draws them on the frames (scratch only)
"""
import poses
import sheet


def table():
    Ps = poses.frames()
    rows = [tuple(tuple(int(v) for v in pt) for pt in P['mouths']) for P in Ps]
    rows.append(poses.RELEASE_MOUTHS)
    apex = {i: P['apex'] for i, P in enumerate(Ps) if 'apex' in P}
    return rows, apex


if __name__ == '__main__':
    from PIL import Image, ImageDraw
    from common import SCRATCH, on_bg, up, FW
    rows, apex = table()
    names = []
    for name, n in sheet.NAMES:
        names += ['%s %d' % (name, i) for i in range(n)]
    for i, r in enumerate(rows):
        print('%2d %-15s middle %-10s left %-10s right %-10s %s' % (i, names[i], r[0], r[1], r[2],
                                                              ('apex %s' % (apex[i],)) if i in apex else ''))
    ims = sheet.frames()
    s = 3
    cells = []
    for i, im in enumerate(ims):
        big = up(on_bg(im), s)
        d = ImageDraw.Draw(big)
        for pt, col in zip(rows[i], ((255, 255, 0), (0, 255, 255), (255, 0, 255))):
            x, y = pt[0] * s + 1, pt[1] * s + 1
            d.line((x - 7, y, x + 7, y), fill=col + (255,), width=2)
            d.line((x, y - 7, x, y + 7), fill=col + (255,), width=2)
        if i in apex:
            x, y = apex[i][0] * s + 1, apex[i][1] * s + 1
            d.ellipse((x - 5, y - 5, x + 5, y + 5), outline=(255, 255, 255, 255), width=2)
        d.text((4, 4), '%d %s' % (i, names[i]), fill=(255, 255, 255, 255))
        cells.append(big)
    W = Image.new('RGBA', (8 * (FW * s + 4), 2 * (160 * s + 4)), (10, 10, 10, 255))
    for i, c in enumerate(cells):
        W.alpha_composite(c, ((i % 8) * (FW * s + 4), (i // 8) * (160 * s + 4)))
    W.save(SCRATCH + 'mouths_check.png')
