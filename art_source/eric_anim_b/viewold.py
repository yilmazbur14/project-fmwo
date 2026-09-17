from pngio import *
C = "C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/"
FL = (136, 180, 99, 255)
w, h, px = read_png(C + "Eric/EricTopDownRevised.png")
print(w, h)
def strip(idxs, s, out, cols=4):
    rows = (len(idxs) + cols - 1) // cols
    o = blank(cols * 128 * s + (cols + 1) * 4, rows * 128 * s + (rows + 1) * 4, (40, 40, 40, 255))
    for k, i in enumerate(idxs):
        fr = crop(px, i * 128, 0, 128, 128)
        paste(o, scale(fr, s, FL), 4 + (k % cols) * (128 * s + 4), 4 + (k // cols) * (128 * s + 4))
    write_png(out, len(o[0]), len(o), o)
strip(list(range(13, 21)), 3, '../ref_old_whirl_3x.png')
strip([0, 3, 5, 7, 9, 21, 25, 27], 2, '../ref_old_misc_2x.png')
