"""Keyline, black ratio and colour count for a sheet, measured per frame and over the whole sheet.

The keyline is the colour that most often sits on the silhouette edge (an opaque pixel with a
transparent 4-neighbour). black% counts pure #000000 over opaque pixels; key% counts the measured
keyline colour, which is the same thing when the keyline is pure black.

  python measure.py <png> [frame_w frame_h] ...
"""
import os
import sys
from collections import Counter

from PIL import Image


def flat(im):
    f = getattr(im, 'get_flattened_data', None)
    return list(f() if f else im.getdata())


def measure(im):
    im = im.convert('RGBA')
    w, h = im.size
    px = flat(im)
    op = [c for c in px if c[3] > 0]
    edge = Counter()
    for y in range(h):
        for x in range(w):
            c = px[y * w + x]
            if c[3] == 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                qx, qy = x + dx, y + dy
                if not (0 <= qx < w and 0 <= qy < h) or px[qy * w + qx][3] == 0:
                    edge[c[:3]] += 1
                    break
    key = edge.most_common(1)[0][0] if edge else None
    black = sum(1 for c in op if c[:3] == (0, 0, 0))
    keyn = sum(1 for c in op if c[:3] == key)
    semi = sum(1 for c in op if c[3] < 255)
    return dict(opaque=len(op), colours=len(set(op)), black=black / max(1, len(op)),
                key=key, key_ratio=keyn / max(1, len(op)),
                edge_key_share=(edge[key] / max(1, sum(edge.values()))) if key else 0, semi=semi)


def fmt(name, m):
    k = '#%02X%02X%02X' % m['key'] if m['key'] else '-'
    return '%-34s opaque %6d  colours %3d  black %5.1f%%  keyline %s (%5.1f%% of px, %5.1f%% of edge)%s' % (
        name, m['opaque'], m['colours'], 100 * m['black'], k, 100 * m['key_ratio'],
        100 * m['edge_key_share'], ('  semi-alpha px %d' % m['semi']) if m['semi'] else '')


if __name__ == '__main__':
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        path = args[i]
        fw = fh = None
        if i + 2 < len(args) and args[i + 1].isdigit():
            fw, fh = int(args[i + 1]), int(args[i + 2])
            i += 3
        else:
            i += 1
        im = Image.open(path).convert('RGBA')
        name = os.path.basename(path)
        print(fmt(name + ' (sheet)', measure(im)))
        if fw:
            for n in range(im.width // fw):
                print(fmt('   frame %d' % n, measure(im.crop((n * fw, 0, n * fw + fw, fh)))))
