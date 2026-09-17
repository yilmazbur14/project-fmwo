import math

def arc_pixels(cx, cy, R, a0, a1):
    """1px pixel-perfect arc, angles in degrees (screen: cw positive, y down). a0<a1."""
    pts = []
    n = max(8, int(abs(a1 - a0) * R * math.pi / 180 * 4))
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        p = (math.floor(cx + R * math.cos(a)), math.floor(cy + R * math.sin(a)))
        if not pts or pts[-1] != p:
            pts.append(p)
    # pixel-perfect: drop L-corner pixels
    out = []
    i = 0
    while i < len(pts):
        if 0 < i < len(pts) - 1 and out:
            a, b, c = out[-1], pts[i], pts[i + 1]
            if (a[0] == b[0] or a[1] == b[1]) and (b[0] == c[0] or b[1] == c[1]) and a[0] != c[0] and a[1] != c[1]:
                i += 1
                continue
        out.append(pts[i])
        i += 1
    return out

def put(g, pts, ch, only_empty=True):
    for x, y in pts:
        if 0 <= y < len(g) and 0 <= x < len(g[0]):
            if not only_empty or g[y][x] == '.':
                g[y][x] = ch

def overlay(base, top):
    """top chars over base where top != '.'"""
    return [''.join(t if t != '.' else b for b, t in zip(br, tr)) for br, tr in zip(base, top)]

def band_pixels(cx, cy, r0, r1, a0, a1, W=96, H=96):
    """pixels whose centre lies in the annulus sector r0<=r<r1, a0<=angle<=a1 (deg, cw, y down)"""
    out = []
    for y in range(H):
        for x in range(W):
            dx = x + 0.5 - cx; dy = y + 0.5 - cy
            r = math.hypot(dx, dy)
            if not (r0 <= r < r1): continue
            a = math.degrees(math.atan2(dy, dx))
            for k in (-360, 0, 360):
                if a0 <= a + k <= a1:
                    out.append((x, y)); break
    return out
