import sys
from lib import *
def zoom_region(canvas_txt_path, x0, y0, w, h, s, out):
    cv = from_text(open(canvas_txt_path).read())
    rgba = to_rgba(cv)
    rgba = checker_bg(64, 64, rgba, cell=1, c1=(200, 210, 220, 255), c2=(170, 180, 192, 255))
    sub = [row[x0:x0 + w] for row in rgba[y0:y0 + h]]
    _, _, big = scale(w, h, sub, s)
    M = 22
    TW, TH = w * s + M, h * s + M
    img = [[(40, 40, 48, 255)] * TW for _ in range(TH)]
    for y in range(h * s):
        img[y + M][M:] = big[y]
    for i in range(w):
        if (x0 + i) % 2 == 0:
            draw_text(img, M + i * s + 1, 3, str(x0 + i), (255, 230, 120, 255), sc=2 if s >= 14 else 1)
    for j in range(h):
        if (y0 + j) % 2 == 0:
            draw_text(img, 1, M + j * s + 2, str(y0 + j), (255, 230, 120, 255), sc=2 if s >= 14 else 1)
    write_png(out, TW, TH, img)
if __name__ == '__main__':
    a = sys.argv
    zoom_region(a[1], int(a[2]), int(a[3]), int(a[4]), int(a[5]), int(a[6]), a[7])
