"""Mockups: impact + ring of shockwave segments on the arena green, at 3x."""
import math, sys
from pngio import read_png, write_png, blank, scale, crop
from gifw import write_gif

FLOOR = (136, 180, 99, 255)
SEG_W = SEG_H = 24
IMP_W, IMP_H = 128, 64

def frames_of(path, fw, fh):
    w, h, px = read_png(path)
    return [crop(px, i * fw, 0, fw, fh) for i in range(w // fw)]

def blit(dst, src, ox, oy):
    H, W = len(dst), len(dst[0])
    for y, row in enumerate(src):
        yy = oy + y
        if not 0 <= yy < H:
            continue
        for x, p in enumerate(row):
            if p[3] == 0:
                continue
            xx = ox + x
            if 0 <= xx < W:
                dst[yy][xx] = p

def ring_points(rx, ry, spacing):
    # walk the ellipse by arc length so segments are evenly spaced
    n = 720
    pts = [(rx * math.cos(2 * math.pi * i / n), ry * math.sin(2 * math.pi * i / n)) for i in range(n + 1)]
    out = [pts[0]]
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        acc += math.hypot(b[0] - a[0], b[1] - a[1])
        if acc >= spacing:
            out.append(b)
            acc = 0.0
    if math.hypot(out[-1][0] - out[0][0], out[-1][1] - out[0][1]) < spacing * 0.5:
        out.pop()
    return out

def compose(cw, ch, cx, cy, impact=None, rings=(), seg_frames=None, seg_frame=0):
    """cx, cy = slam point in canvas pixels (1x)."""
    cv = blank(cw, ch, FLOOR)
    items = []
    for rx, ry, spacing in rings:
        for i, (px, py) in enumerate(ring_points(rx, ry, spacing)):
            fr = seg_frames[(seg_frame) % len(seg_frames)]
            # anchor: bottom-centre of the 24x24 segment on the ring point
            items.append((cy + py, fr, int(round(cx + px - SEG_W / 2)), int(round(cy + py - SEG_H))))
    if impact is not None:
        items.append((cy, impact, int(round(cx - IMP_W / 2)), int(round(cy - IMP_H))))
    for _, img, ox, oy in sorted(items, key=lambda t: t[0]):
        blit(cv, img, ox, oy)
    return cv

if __name__ == '__main__':
    imp = frames_of('impact_strip.png', IMP_W, IMP_H)
    seg = frames_of('segment_strip.png', SEG_W, SEG_H)
    # still mockup: impact frame 2 with the ring expanding (two radii shown side by side)
    W, H = 300, 170
    a = compose(W, H, 150, 110, impact=imp[2], rings=[(60, 24, 18)], seg_frames=seg, seg_frame=0)
    b = compose(W, H, 150, 110, impact=imp[4], rings=[(125, 52, 18)], seg_frames=seg, seg_frame=2)
    out = blank(W, H * 2 + 4, (40, 40, 40, 255))
    blit(out, a, 0, 0)
    blit(out, b, 0, H + 4)
    write_png('mockup_ring_3x.png', W * 3, (H * 2 + 4) * 3, scale(out, 3))
    # tiling test: rows at spacing 24, 20, 16 (1x) and a vertical stack
    T = blank(200, 120, FLOOR)
    for row, sp in enumerate((24, 20, 16)):
        for i in range(8):
            blit(T, seg[(i * 0) % 4], 4 + i * sp, 4 + row * 30)
    for i in range(5):
        blit(T, seg[0], 176, 4 + i * 16 - 0)
    write_png('segment_tiling_4x.png', 200 * 4, 120 * 4, scale(T, 4))
    # animated mockup GIF of the whole slam: impact frames + ring expanding
    frames = []
    durs = []
    for k in range(10):
        rx = 20 + k * 13
        ry = rx * 0.42
        img = imp[k] if k < len(imp) else None
        cv = compose(W, H, 150, 110, impact=img, rings=[(rx, ry, 18)] if k >= 1 else [], seg_frames=seg, seg_frame=k)
        frames.append(scale(cv, 2))
        durs.append(70)
    write_gif('mockup_slam_2x.gif', frames, durs)
    print('ok')
