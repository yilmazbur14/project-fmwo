"""Big spiked red collars (Bixby's red studded collars grown into iron-spiked ones)."""
import math
import lib
from lib import *
from pal import PALC, RAMPC, BLACK


def spike(cv, base, direction, length, width):
    dx, dy = direction
    n = math.hypot(dx, dy) or 1
    dx, dy = dx / n, dy / n
    tip = (base[0] + dx * length, base[1] + dy * length)
    m = tube([base, (base[0] + dx * length * 0.55, base[1] + dy * length * 0.55), tip], [width, width * 0.6, 0.35])
    cv.part(m, 'iron', ('cyl', (base[0] - 0.8, base[1] - 0.8), (tip[0] - 0.8, tip[1] - 0.8), width + 0.8), [0.9, 0.6, 0.2])
    return m


def band_pts(a, b, sag, down):
    """quadratic curve from a to b sagging toward unit vector `down`"""
    mid = ((a[0] + b[0]) / 2 + down[0] * sag * 2, (a[1] + b[1]) / 2 + down[1] * sag * 2)
    pts = []
    for i in range(17):
        t = i / 16
        pts.append(((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * mid[0] + t * t * b[0],
                    (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * mid[1] + t * t * b[1]))
    return pts


def collar(cv, a, b, thick, sag, n_spikes=3, spike_len=5.5, spike_w=2.4, studs=2, light_c=None):
    """band from a to b (upper edge), thickness along the 'down' normal"""
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    down = (-math.sin(ang), math.cos(ang))
    if down[1] < 0:
        down = (-down[0], -down[1])
    upper = band_pts(a, b, sag, down)
    lower = [(x + down[0] * thick, y + down[1] * thick) for x, y in upper]
    band = poly(upper + list(reversed(lower)))
    # spikes along the lower edge, fanning outward
    for k in range(n_spikes):
        t = (k + 0.5) / n_spikes
        i = int(round(t * 16))
        bx, by = lower[i]
        bx -= down[0] * 1.2
        by -= down[1] * 1.2
        tang = (math.cos(ang), math.sin(ang))
        fan = (t - 0.5) * 1.1
        d = (down[0] + tang[0] * fan, down[1] + tang[1] * fan)
        spike(cv, (bx, by), d, spike_len, spike_w)
    # cylinder shading across the band thickness: lit top edge, red body, dark underside
    rp = RAMPC['collar']
    for (x, y) in band:
        # position across the band: project onto the down vector relative to the nearest upper point
        best = min(upper, key=lambda p: (p[0] - x - 0.5) ** 2 + (p[1] - y - 0.5) ** 2)
        u = ((x + 0.5 - best[0]) * down[0] + (y + 0.5 - best[1]) * down[1]) / thick
        idx = 0 if u < 0.22 else (1 if u < 0.62 else (2 if u < 0.86 else 3))
        cv.put(x, y, rp[idx])
    cv.outline(band)
    inner = erode(band, 1)
    for k in range(studs):
        t = (k + 1) / (studs + 1)
        i = int(round(t * 16))
        x = int(upper[i][0] + down[0] * thick * 0.5)
        y = int(upper[i][1] + down[1] * thick * 0.5)
        for (dx, dy, ch) in ((0, 0, 'x'), (1, 0, 'X'), (0, 1, 'X'), (1, 1, 'y')):
            if (x + dx, y + dy) in inner:
                cv.put(x + dx, y + dy, PALC[ch])
    return band
