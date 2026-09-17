"""Upscale a PNG for viewing, and optionally dump a palette-indexed char grid."""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png, write_png, upscale

def main():
    src, dst, s = sys.argv[1], sys.argv[2], int(sys.argv[3])
    crop = None
    if len(sys.argv) > 4 and sys.argv[4] != '-':
        crop = tuple(int(v) for v in sys.argv[4].split(','))  # x,y,w,h
    w, h, pix = read_png(src)
    if crop:
        x0, y0, cw, ch = crop
        pix = [row[x0:x0 + cw] for row in pix[y0:y0 + ch]]
        w, h = cw, ch
    W, H, out = upscale(w, h, pix, s, bg='checker')
    write_png(dst, W, H, out)
    print('wrote', dst, W, H)
    if len(sys.argv) > 5 and sys.argv[5] == 'grid':
        cols = collections.Counter()
        for row in pix:
            for p in row:
                if p[3] > 0:
                    cols[p] += 1
        chars = '#ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789@$%&*+=?<>'
        m = {}
        order = sorted(cols, key=lambda c: -cols[c])
        # black always '#'
        i = 1
        for c in order:
            if c[:3] == (0, 0, 0) and c[3] == 255:
                m[c] = '#'
            else:
                m[c] = chars[i]; i += 1
        print('    ' + ''.join(str(x % 10) for x in range(w)))
        for y, row in enumerate(pix):
            print('%3d ' % y + ''.join(m[p] if p[3] > 0 else '.' for p in row))
        for c in order:
            print(m[c], '#%02X%02X%02X' % c[:3], 'a=%d' % c[3], cols[c])

main()
