"""gridview.py in.png out.png fw fh cols scale [bg r,g,b] -> frames laid out in a grid, labelled with index"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png, write_png
DIG = {
 '0': ["111","101","101","101","111"], '1': ["010","110","010","010","111"],
 '2': ["111","001","111","100","111"], '3': ["111","001","111","001","111"],
 '4': ["101","101","111","001","001"], '5': ["111","100","111","001","111"],
 '6': ["111","100","111","101","111"], '7': ["111","001","001","001","001"],
 '8': ["111","101","111","101","111"], '9': ["111","101","111","001","111"],
}
def label(img, x, y, text, s=3, col=(255,255,255,255)):
    for i, ch in enumerate(text):
        g = DIG[ch]
        for r in range(5):
            for c in range(3):
                if g[r][c] == '1':
                    for yy in range(s):
                        for xx in range(s):
                            img[y + r*s + yy][x + (i*4 + c)*s + xx] = col
def main():
    src, dst = sys.argv[1], sys.argv[2]
    fw, fh, cols, s = int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
    bg = tuple(int(v) for v in sys.argv[7].split(',')) + (255,) if len(sys.argv) > 7 else (136,180,99,255)
    w, h, px = read_png(src)
    n = (w // fw) * (h // fh)
    rows = (n + cols - 1) // cols
    pad = 24
    W = cols * (fw * s + 4) + 4
    H = rows * (fh * s + pad + 4) + 4
    img = [[(40,40,40,255)] * W for _ in range(H)]
    for i in range(n):
        fx, fy = (i % (w // fw)) * fw, (i // (w // fw)) * fh
        cx, cy = 4 + (i % cols) * (fw * s + 4), 4 + (i // cols) * (fh * s + pad + 4)
        label(img, cx, cy + 2, str(i))
        oy = cy + pad
        for y in range(fh):
            for x in range(fw):
                p = px[fy + y][fx + x]
                if p[3] == 0:
                    q = bg
                elif p[3] < 255:
                    k = p[3] / 255
                    q = tuple(int(p[j]*k + bg[j]*(1-k)) for j in range(3)) + (255,)
                else:
                    q = p
                for yy in range(s):
                    row = img[oy + y*s + yy]
                    for xx in range(s):
                        row[cx + x*s + xx] = q
    write_png(dst, W, H, img)
    print('wrote', dst, W, H)
main()
