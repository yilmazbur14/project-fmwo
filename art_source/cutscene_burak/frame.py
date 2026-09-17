"""Frame assembly for Burak cutscene."""
import math
from blib import *
import rig, parts, heads
from heads import rows


def stamp(L, part, dx=0, dy=0):
    x0, y0, r = parts.rows_of(part)
    blk(L, x0 + dx, y0 + dy, r)


def glove_rows(mirror=False):
    r = blk_rows(parts.GLOVE_R)
    if mirror:
        r = [s[::-1] for s in r]
    return r


def lace(L, pts):
    """1px lace polyline (Bresenham) in 'L'; ends are hidden under other parts."""
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        x, y = x0, y0
        while True:
            if 0 <= x < W and 0 <= y < H:
                L[y][x] = 'L'
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy; x += sx
            if e2 <= dx:
                err += dx; y += sy


def build(pose):
    hx, hy = pose.get('hip', (30, 47))
    bob = pose.get('bob', 0)
    fa, na = pose['far_ankle'], pose['near_ankle']
    FL, _ = rig.build_leg((hx + 0.5, hy + bob), fa, shade='far', l1=6.2, l2=6.2)
    FS = rig.build_shoe(fa, pose.get('far_foot', 0.0), dark=True)
    NL, _ = rig.build_leg((hx - 0.5, hy + bob), na, shade='near', l1=6.2, l2=6.2)
    NS = rig.build_shoe(na, pose.get('near_foot', 0.0))
    T = layer(); stamp(T, pose['torso'], 0, bob - 1)
    G = layer()
    gb = pose.get('glove_back', (16, 35))
    gf = pose.get('glove_front', (35, 35))
    lace(G, [(gb[0] + 4, gb[1] + bob), (26, 33 + bob)])
    lace(G, [(gf[0] + 4, gf[1] + bob), (35, 32 + bob)])
    blk(G, gb[0], gb[1] + bob, glove_rows(mirror=True))
    blk(G, gf[0], gf[1] + bob, glove_rows())
    A = layer(); stamp(A, pose['arm'], 0, bob - 1)
    Hd = layer()
    hxo, hyo = pose.get('head_at', (24, 14))
    blk(Hd, hxo, hyo + bob + pose.get('head_bob', 0), rows(pose['head']))
    cv = compose([FL, FS, NL, NS, T, G, A, Hd])
    return outer_outline(cv)


if __name__ == '__main__':
    from pngio import write_png
    p = dict(torso=parts.TORSO_SLOUCH2, arm=parts.ARM_POCKET2, head=heads.HEAD_GLOOM_S,
             far_ankle=(33, 59), near_ankle=(27, 59), hip=(30, 47))
    c = build(p)
    preview(c, 'frame_8x.png', s=8)
    w, h, img = rgba_strip([c]); write_png('frame_1x.png', w, h, img)
