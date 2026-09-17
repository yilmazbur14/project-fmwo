"""Preview only: composite a 9-slice of the UI dialogue frame over the art to check the covered band."""
from pngio import read_png, write_png, scale, crop

w, h, art = read_png('stage3.png')
fw, fh, fr = read_png("C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/UI/ui_dialogue_frame.png")
M = 9
x0, y0, x1, y1 = 12, 272, 627, 354      # inclusive box in art coords
bw, bh = x1 - x0 + 1, y1 - y0 + 1


def src_coord(i, n, fsize):
    if i < M:
        return i
    if i >= n - M:
        return fsize - (n - i)
    return M + (i - M) % (fsize - 2 * M)


out = [list(r) for r in art]
for j in range(bh):
    sy = src_coord(j, bh, fh)
    for i in range(bw):
        sx = src_coord(i, bw, fw)
        p = fr[sy][sx]
        if p[3] > 0:
            out[y0 + j][x0 + i] = p
write_png('preview_dialogue_2x.png', scale(out, 2))
write_png('preview_dialogue_bottom_3x.png', scale(crop(out, 150, 200, 490, 360), 3))
