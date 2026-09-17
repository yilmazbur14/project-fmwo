"""RotSprite-style pixel-art rotation: Scale2x three times (8x), rotate by nearest-neighbour sampling of the
8x image, then re-close the 1px black outline. Keeps the palette (no new colours) and alpha 0/255."""
import math
from lib import Canvas, close_outline, lone_black_cleanup
from pal import BLACK


def scale2x(px, w, h):
    out = [[None] * (w * 2) for _ in range(h * 2)]
    for y in range(h):
        row = px[y]
        up = px[y - 1] if y > 0 else row
        dn = px[y + 1] if y < h - 1 else row
        for x in range(w):
            P = row[x]
            A = up[x]
            D = dn[x]
            C = row[x - 1] if x > 0 else P
            B = row[x + 1] if x < w - 1 else P
            e0 = e1 = e2 = e3 = P
            if C == A and C != D and A != B:
                e0 = A
            if A == B and A != C and B != D:
                e1 = B
            if D == C and D != B and C != A:
                e2 = C
            if B == D and B != A and D != C:
                e3 = D
            o0 = out[2 * y]
            o1 = out[2 * y + 1]
            o0[2 * x] = e0
            o0[2 * x + 1] = e1
            o1[2 * x] = e2
            o1[2 * x + 1] = e3
    return out, w * 2, h * 2


def rotate(cv, ang_deg, pivot, out_w=None, out_h=None, reclose=True):
    """rotate canvas cv by ang_deg (screen coords, + = clockwise) about pivot (continuous coords)"""
    x0, y0, x1, y1 = cv.w, cv.h, -1, -1
    for y in range(cv.h):
        for x in range(cv.w):
            if cv.px[y][x] is not None:
                x0, y0, x1, y1 = min(x0, x), min(y0, y), max(x1, x), max(y1, y)
    W = out_w or cv.w
    Hh = out_h or cv.h
    out = Canvas(W, Hh)
    if x1 < 0:
        return out
    # crop with a 1px margin to keep the upscale cheap
    cx0, cy0 = max(0, x0 - 1), max(0, y0 - 1)
    cw, ch = min(cv.w, x1 + 2) - cx0, min(cv.h, y1 + 2) - cy0
    px = [cv.px[cy0 + y][cx0:cx0 + cw] for y in range(ch)]
    w, h = cw, ch
    for _ in range(3):
        px, w, h = scale2x(px, w, h)
    a = math.radians(ang_deg)
    ca, sa = math.cos(a), math.sin(a)
    px0, py0 = pivot
    for y in range(Hh):
        for x in range(W):
            dx, dy = x + 0.5 - px0, y + 0.5 - py0
            # inverse rotation
            sx = dx * ca + dy * sa + px0
            sy = -dx * sa + dy * ca + py0
            ix = int(math.floor((sx - cx0) * 8))
            iy = int(math.floor((sy - cy0) * 8))
            if 0 <= ix < w and 0 <= iy < h:
                c = px[iy][ix]
                if c is not None:
                    out.px[y][x] = c
    if reclose:
        close_outline(out)
        lone_black_cleanup(out)
    return out


def rot_pt(p, ang_deg, pivot):
    a = math.radians(ang_deg)
    ca, sa = math.cos(a), math.sin(a)
    dx, dy = p[0] - pivot[0], p[1] - pivot[1]
    return (pivot[0] + dx * ca - dy * sa, pivot[1] + dx * sa + dy * ca)
