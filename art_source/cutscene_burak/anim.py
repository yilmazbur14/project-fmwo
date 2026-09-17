"""Burak cutscene animation builder."""
import math, os, sys
from blib import *
import rig, parts, heads
from heads import rows
from lace import draw_lace
from pngio import write_png
import gif

GROUND = 63
FOOT_HEEL = (-3.0, 4.0)
FOOT_TOE = (7.0, 4.0)


def foot(mode, x, ang_deg=0.0, lift=0):
    """Return (ankle_xy, angle_rad).  mode: flat (x = ankle x), heel (x = heel contact x), toe (x = toe contact x)."""
    a = math.radians(ang_deg)
    gy = GROUND - lift
    if mode == 'flat':
        return (x, 59 - lift), a
    px, py = FOOT_HEEL if mode == 'heel' else FOOT_TOE
    rx, ry = rig.rot(px, py, a)
    return (x - rx, gy + 0.49 - ry), a


def stamp(L, part, dx=0, dy=0):
    x0, y0, r = parts.rows_of(part)
    blk(L, x0 + dx, y0 + dy, r)


def glove(mirror=False):
    r = blk_rows(parts.GLOVE2)
    return [s[::-1] for s in r] if mirror else r


def build(p):
    hx, hy = p.get('hip', (30, 47))
    bob = p.get('bob', 0)
    (fa, fang), (na, nang) = p['far'], p['near']
    FL, _ = rig.build_leg2((hx + 1.0, hy + bob), fa, shade="far")
    FS = rig.build_shoe2(fa, fang, dark=True)
    NL, _ = rig.build_leg2((hx - 1.0, hy + bob), na, shade="near")
    NS = rig.build_shoe2(na, nang)
    cv = compose([FL, FS, NL, NS])
    T = layer(); stamp(T, p['torso'], 0, bob - 1)
    cv = compose([cv, T])
    gbx, gby = p['gb']
    gfx, gfy = p['gf']
    gb = glove(mirror=True)
    blk(cv, gbx, gby + bob, gb)
    A = layer(); stamp(A, p['arm'], 0, bob - 1)
    Hd = layer()
    hxo, hyo = p.get('head_at', (24, 14))
    blk(Hd, hxo, hyo + bob + p.get('head_dy', 0), rows(p['head']))
    cv = compose([cv, A, Hd])
    sx, sy = p.get('lace_top', (28, 31))
    lp = [(gbx + 4, gby + bob + 1), (gbx + 5, gby + bob), (sx - 4, sy + bob - 2), (sx, sy + bob), (sx + 4, sy + bob + 2),
          (gfx + 3, gfy + bob), (gfx + 4, gfy + bob + 1)]
    draw_lace(cv, lp)
    blk(cv, gfx, gfy + bob, glove())
    blk(cv, gbx, gby + bob, gb[:3])
    return outer_outline(cv)


# ------------------------------------------------------------------ gloomy walk (8 frames)
def walk_gloomy():
    T, A, Hd = parts.TORSO_SLOUCH2, parts.ARM_POCKET2, heads.HEAD_GLOOM_S
    # (near foot), (far foot), bob, head_dy, glove dy
    spec = [
        (foot('heel', 33, -14), foot('toe', 31, 28), 0, 0, -1),
        (foot('flat', 33), foot('toe', 29, 42, lift=2), 1, 0, 0),
        (foot('flat', 30), foot('flat', 30, 18, lift=3), 1, 1, 1),
        (foot('toe', 34, 10), foot('flat', 33, -6, lift=1), 0, 0, 0),
        (foot('toe', 31, 28), foot('heel', 33, -14), 0, 0, -1),
        (foot('toe', 29, 42, lift=2), foot('flat', 33), 1, 0, 0),
        (foot('flat', 30, 18, lift=3), foot('flat', 30), 1, 1, 1),
        (foot('flat', 33, -6, lift=1), foot('toe', 34, 10), 0, 0, 0),
    ]
    frames = []
    for near, far, bob, hdy, gdy in spec:
        p = dict(torso=T, arm=A, head=Hd, near=near, far=far, bob=bob, head_dy=hdy,
                 gb=(16, 28 + gdy), gf=(35, 36 + gdy))
        frames.append(build(p))
    return frames


def save_strip(frames, path, scale=1):
    w, h, img = rgba_strip(frames)
    if scale > 1:
        from pngio import scale as sc
        w, h, img = sc(w, h, img, scale)
    write_png(path, w, h, img)


def save_gif(frames, path, delays_ms, s=4, bg=(118, 124, 140, 255)):
    out = []
    for c in frames:
        rg = to_rgba(c)
        rg = [[p if p[3] == 255 else bg for p in row] for row in rg]
        from pngio import scale as sc
        _, _, big = sc(W, H, rg, s)
        out.append([[px[:3] for px in row] for row in big])
    gif.write_gif(path, out, delays_ms)


if __name__ == '__main__':
    os.makedirs('out', exist_ok=True)
    fr = walk_gloomy()
    preview(fr, 'out/walk_gloomy_8x.png', s=5)
    save_strip(fr, 'out/walk_gloomy_1x.png')
    save_gif(fr, 'out/walk_gloomy.gif', [150] * 8)
    print('ok')
