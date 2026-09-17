"""Chat-style SYSTEM MESSAGE banner, 9-sliceable with non-uniform margins.
The avatar (round server icon + red do-not-disturb dot) lives entirely inside
the top-left corner patch, so it never stretches: the message grows right and
down like a chat row.  python banner.py [variant]"""
import sys
from lib import *
import props

# margins at 1x
ML, MT, MR, MB = 34, 32, 4, 4
BW, BH = ML + 4 + MR, MT + 4 + MB     # 42 x 40


def build(variant='a'):
    img = Img(BW, BH)
    body = NAVY if variant in ('a', 'c') else PLUM
    hi = INDIGO if body == NAVY else BROWN_D
    # frame
    img.rect(0, 0, BW - 1, BH - 1, K)
    img.rect(1, 1, BW - 2, BH - 2, body)
    img.hline(1, BW - 2, 1, hi)                 # top inner highlight
    img.hline(1, BW - 2, BH - 2, K if body == NAVY else NAVY)   # bottom inner shade
    # crimson accent bar on the left (mention/alert highlight)
    img.vline(1, 1, BH - 2, RED_L)
    img.vline(2, 1, BH - 2, RED)
    img.vline(3, 1, BH - 2, RED)
    img.vline(4, 1, BH - 2, K)
    img.set(1, BH - 2, RED)
    img.set(2, BH - 2, BROWN_D); img.set(3, BH - 2, BROWN_D)
    # avatar: round server icon with the chat mascot, DND dot bottom-right
    props.server_icon_house(img, 7, 4, dot_ring=body)
    if variant == 'c':
        # brass rivets on the right corners to tie in with the UI kit
        for (x, y) in [(BW - 3, 2), (BW - 3, BH - 3)]:
            img.set(x, y, YELLOW)
    return img


def nine_slice_ok(img, l, t, r, b):
    """edges must be constant along their stretch axis and centre flat."""
    probs = []
    w, h = img.w, img.h
    for y in list(range(0, t)) + list(range(h - b, h)):
        ref = img.p[y][l]
        if any(img.p[y][x] != ref for x in range(l, w - r)):
            probs.append('top/bottom row %d varies' % y)
    for x in list(range(0, l)) + list(range(w - r, w)):
        ref = img.p[t][x]
        if any(img.p[y][x] != ref for y in range(t, h - b)):
            probs.append('left/right col %d varies' % x)
    ref = img.p[t][l]
    if any(img.p[y][x] != ref for y in range(t, h - b) for x in range(l, w - r)):
        probs.append('centre not flat')
    # bleed: corner pixels next to stretched edges must match the edge
    for y in list(range(0, t)) + list(range(h - b, h)):
        if img.p[y][l - 1] != img.p[y][l] and y not in range(0, t):
            probs.append('bleed row %d left' % y)
        if img.p[y][w - r] != img.p[y][w - r - 1]:
            probs.append('bleed row %d right' % y)
    return probs


def nine_slice(img, l, t, r, b, W, H):
    w, h = img.w, img.h
    cw, ch = w - l - r, h - t - b
    CW, CH = W - l - r, H - t - b

    def mp(D, lo, hi_src, dst_c, src_c, total_src):
        if D < lo:
            return D
        if D >= lo + dst_c:
            return D - (lo + dst_c) + (lo + src_c)
        return lo + min(src_c - 1, int((D - lo) * src_c / dst_c))

    xs = [mp(X, l, r, CW, cw, w) for X in range(W)]
    ys = [mp(Y, t, b, CH, ch, h) for Y in range(H)]
    o = Img(W, H)
    for Y in range(H):
        for X in range(W):
            o.p[Y][X] = img.p[ys[Y]][xs[X]]
    return o


if __name__ == '__main__':
    v = sys.argv[1] if len(sys.argv) > 1 else 'a'
    b = build(v)
    print('9-slice problems:', nine_slice_ok(b, ML, MT, MR, MB))
    b.save('out/banner_%s.png' % v)
    zoom_save(b, 'out/banner_%s_12x.png' % v, 12)
    big = nine_slice(b, ML, MT, MR, MB, 400, 46)
    zoom_save(big, 'out/banner_%s_stretch_3x.png' % v, 3)
