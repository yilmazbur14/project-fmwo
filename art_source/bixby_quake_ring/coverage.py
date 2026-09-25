"""Checks the ring has no holes at any radius: renders the ring alone (placement.py, the sheet) and tests that
every pixel of the band's middle (|r - R| <= CORE floor px) is covered by art, wherever a segment is drawn.
Writes only into the scratchpad.

  python coverage.py [sheet.png FRAME_W FRAME_H py0 py1 ...]
"""
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mock  # noqa: E402
import placement as P  # noqa: E402

CORE = 18.0          # floor px either side of the ring's centre line that must be covered (the band is 36)


def ring_alone(sheet, radius, beat, centre):
    w = int(2 * (radius + 120)) + 60
    h = int(2 * P.K * (radius + 120)) + 300
    canvas = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ox, oy = w // 2 - centre[0], h // 2 + 40 - centre[1]
    drawn = []
    for i, theta, (x, y), phi, row, flip in P.segments(radius, centre):
        img = sheet.frame(row, (beat + i) % sheet.cols, flip)
        at = (int(x - sheet.fw // 2 * mock.SCALE) + ox, int(y - sheet.py[row] * mock.SCALE) + oy)
        canvas.alpha_composite(img, at)
        drawn.append((theta, x, y))
    return canvas, (ox, oy)


def holes(sheet, radius, beat=0, centre=(960, 540)):
    canvas, (ox, oy) = ring_alone(sheet, radius, beat, centre)
    a = canvas.getchannel('A').load()
    bad = []
    # walk the band's middle in floor polar coordinates, finely enough to hit every screen pixel
    steps = int(2 * math.pi * (radius + CORE) / 1.0)
    for k in range(steps):
        th = 2 * math.pi * k / steps
        for dr in range(-int(CORE), int(CORE) + 1, 2):
            r = radius + dr
            x = centre[0] + r * math.cos(th) + ox
            y = centre[1] + P.K * r * math.sin(th) + oy
            if not a[int(x), int(y)]:
                bad.append((round(x - ox), round(y - oy), round(math.degrees(th) % 360, 1), dr))
    return bad, canvas


if __name__ == '__main__':
    im, fw, fh, pys = mock.build_sheet()
    sheet = mock.Sheet(im, fw, fh, pys)
    worst = 0
    report = []
    for radius in [187.0 + 13.0 * i for i in range(94)]:
        for beat in (0, 1):
            bad, canvas = holes(sheet, radius, beat)
            if bad:
                report.append((radius, beat, len(bad), bad[:4]))
                if len(bad) > worst:
                    worst = len(bad)
                    canvas.save(mock.PREV + 'coverage_worst.png')
    for r in report[:30]:
        print('R %6.1f beat %d: %4d uncovered, e.g. %s' % r)
    print('radii checked: 94 x 2 beats; with holes: %d; worst %d px' % (len(report), worst))
