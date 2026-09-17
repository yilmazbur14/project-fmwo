"""Block-in of a slouched standing Burak to fix proportions."""
import math, sys
from blib import *

HOOD = 'ABCDE'
HOOD_TH = [0.18, 0.42, 0.66, 0.86]
PANTS = 'zQqp'
PANTS_TH = [0.2, 0.5, 0.8]


def torso_poly(hx, hy, slouch=0.0):
    pts = [(-7, 2), (-7.5, -5), (-7.2, -11), (-5.8, -15.5), (-3, -18), (2, -18.5), (5.5, -15), (7, -10),
           (7.2, -4), (7.6, -1), (7, 2)]
    out = []
    for x, y in pts:
        k = max(0.0, -y / 18.0) ** 2
        out.append((hx + x + slouch * 3.0 * k, hy + y + slouch * 1.5 * k))
    return out


def build(slouch=1.0):
    hipx, hipy = 30, 47
    L = layer()
    # far leg
    far = layer()
    m = m_or(tcapsule_mask(hipx + 1, hipy, hipx + 3, hipy + 7, 3.4, 3.0), tcapsule_mask(hipx + 3, hipy + 7, hipx + 2, hipy + 13, 3.0, 2.8))
    paint_part(far, m, lambda x, y: 'Q')
    near = layer()
    m = m_or(tcapsule_mask(hipx - 1, hipy, hipx - 2, hipy + 7, 3.4, 3.0), tcapsule_mask(hipx - 2, hipy + 7, hipx - 3, hipy + 13, 3.0, 2.8))
    paint_part(near, m, lambda x, y: 'q')
    # shoes
    shoes = layer()
    paint_part(shoes, poly_mask([(hipx - 6, 59), (hipx + 1, 59), (hipx + 4, 61), (hipx + 4, 64), (hipx - 6, 64)]), lambda x, y: 'O')
    shoes2 = layer()
    paint_part(shoes2, poly_mask([(hipx - 1, 59), (hipx + 6, 59), (hipx + 9, 61), (hipx + 9, 64), (hipx - 1, 64)]), lambda x, y: 'x')
    # torso
    T = layer()
    tp = torso_poly(hipx, hipy, slouch)
    tm = poly_mask(tp)
    paint_part(T, tm, lambda x, y: 'C')
    # head
    Hd = layer()
    cx, cy = hipx + 3 + slouch * 3, hipy - 27 + slouch * 1.5
    hm = ellipse_mask(cx, cy, 10.5, 10)
    paint_part(Hd, hm, shade_fn(lambda x, y: sphere_normal(x, y, cx, cy, 10.5, 10), HOOD, HOOD_TH))
    om = m_and(ellipse_mask(cx + 5, cy + 2, 6.5, 7.5), hm)
    paint_part(Hd, om, lambda x, y: 'F', outline=False)
    fm = ellipse_mask(cx + 6, cy + 2.5, 5, 6)
    paint_part(Hd, fm, lambda x, y: 'd')
    # arm in pocket
    A = layer()
    sx, sy = hipx + slouch * 2.5, hipy - 15 + slouch * 1
    am = m_or(tcapsule_mask(sx, sy, sx - 1, sy + 8, 3.2, 2.8), tcapsule_mask(sx - 1, sy + 8, sx + 5, sy + 12, 2.8, 2.6))
    paint_part(A, am, lambda x, y: 'B')
    cv = compose([shoes2, far, shoes, near, T, A, Hd])
    return cv


if __name__ == '__main__':
    a = build(1.0)
    b = build(0.0)
    preview([a, b], 'blockin_8x.png', s=8)
    print('ok')
