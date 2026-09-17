"""Burak intro cutscene: full 23-frame strip.  python prod.py"""
import math, os
from blib import *
import rig, parts, heads, arms
from lace import draw_lace
from pngio import write_png, scale as pscale
import gif

GROUND = 63


def foot(mode, x, ang_deg=0.0, lift=0):
    a = math.radians(ang_deg)
    if mode == 'flat':
        return (x, 59 - lift), a, lift
    px, py = (-3.0, 5.0) if mode == 'heel' else (7.6, 5.0)
    rx, ry = rig.rot(px, py, a)
    return (x - rx, 64 - lift - ry), a, lift


def lowest_row(L):
    for y in range(H - 1, -1, -1):
        if any(c != '.' for c in L[y]):
            return y
    return None


def grounded_leg(hip, spec, shade):
    (ax, ay), ang, lift = spec
    S = rig.build_shoe2((ax, ay), ang, dark=(shade == 'far'))
    dy = (63 - lift) - lowest_row(S)
    LG, _ = rig.build_leg2(hip, (ax, ay + dy), shade=shade)
    if dy:
        S = rig.build_shoe2((ax, ay + dy), ang, dark=(shade == 'far'))
    return LG, S


def cleanup(cv):
    """Fill enclosed 1px transparent holes; remove 1px black spurs sticking into transparency."""
    out = copy(cv)
    for y in range(H):
        for x in range(W):
            if out[y][x] == '.':
                nb = [(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
                if all(0 <= a < W and 0 <= b < H and out[b][a] != '.' for a, b in nb):
                    out[y][x] = '#'
    changed = True
    while changed:
        changed = False
        for y in range(H):
            for x in range(W):
                if out[y][x] != '#':
                    continue
                n8 = [out[b][a] for a in range(x - 1, x + 2) for b in range(y - 1, y + 2)
                      if (a, b) != (x, y) and 0 <= a < W and 0 <= b < H]
                fill = [c for c in n8 if c not in '.#']
                blacks4 = sum(1 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                              if 0 <= x + dx < W and 0 <= y + dy < H and out[y + dy][x + dx] == '#')
                if not fill and blacks4 <= 1:
                    out[y][x] = '.'
                    changed = True
    return out


def stamp(L, part, dx=0, dy=0):
    x0, y0, r = parts.rows_of(part)
    blk(L, x0 + dx, y0 + dy, r)


def glove(mirror=False):
    r = blk_rows(parts.GLOVE2)
    return [s[::-1] for s in r] if mirror else r


# ------------------------------------------------------------------ FX
def fx_star(L, cx, cy, arm=3):
    pts = {(cx, cy): 'W'}
    for i in range(1, arm + 1):
        c = 'W' if i < arm else 'y'
        for dx, dy in ((i, 0), (-i, 0), (0, i), (0, -i)):
            pts[(cx + dx, cy + dy)] = c
    ol = set()
    for (x, y) in pts:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in pts:
                ol.add(q)
    for (x, y) in ol:
        if 0 <= x < W and 0 <= y < H:
            L[y][x] = '#'
    for (x, y), c in pts.items():
        if 0 <= x < W and 0 <= y < H:
            L[y][x] = c


def fx_rows(L, x0, y0, text):
    blk(L, x0, y0, blk_rows(text))


SWEAT = """
.##.
#SS#
#ST#
.##.
"""
SWEAT_BIG = """
..#..
.#S#.
#SST#
#STT#
.###.
"""


# ------------------------------------------------------------------ frame builder
DARKER = {'A': 'B', 'B': 'C', 'C': 'D', 'D': 'E', 'E': 'E'}


def cast_shadow(cv, part):
    """Darken cloth one step just right of / below a near part (light comes from upper-left)."""
    m = [[part[y][x] != '.' for x in range(W)] for y in range(H)]
    hits = set()
    for y in range(H):
        for x in range(W):
            if m[y][x]:
                continue
            if (x - 1 >= 0 and m[y][x - 1]) or (y - 1 >= 0 and m[y - 1][x]) or (x - 1 >= 0 and y - 1 >= 0 and m[y - 1][x - 1]):
                hits.add((x, y))
    for (x, y) in hits:
        if cv[y][x] in DARKER:
            cv[y][x] = DARKER[cv[y][x]]


def build(p):
    hx, hy = 30, 47
    bob = p.get('bob', 0)
    L_far_arm = layer()
    if p.get('far_arm'):
        sh, el, wr, hk = p['far_arm']
        arms.sleeve(L_far_arm, (sh[0], sh[1] + bob), (el[0], el[1] + bob), (wr[0], wr[1] + bob), dark=True)
        arms.hand(L_far_arm, wr[0] + 0.5, wr[1] + bob + 1.5, kind=hk, dark=True)
    FL, FS = grounded_leg((hx + 1.0, hy + bob), p['far'], 'far')
    NL, NS = grounded_leg((hx - 1.0, hy + bob), p['near'], 'near')
    cv = compose([L_far_arm, FL, FS, NL, NS])
    T = layer()
    stamp(T, parts.TORSO_SLOUCH2 if p['torso'] == 'slouch' else parts.TORSO_UP, 0, bob - 1 + p.get('torso_dy', 0))
    cv = compose([cv, T])
    gbx, gby = p['gb']
    gfx, gfy = p['gf']
    gby += bob
    gfy += bob
    gb = glove(mirror=True)
    GBL = layer()
    blk(GBL, gbx, gby, gb)
    cast_shadow(cv, GBL)
    cv = compose([cv, GBL])
    if p['near_arm'] == 'pocket':
        A = layer()
        stamp(A, parts.ARM_POCKET2, 0, bob - 1 + p.get('torso_dy', 0))
        cast_shadow(cv, A)
        cv = compose([cv, A])
    Hd = layer()
    hxo, hyo = p['head_at']
    blk(Hd, hxo, hyo + bob + p.get('head_dy', 0), p['head'])
    cast_shadow(cv, Hd)
    cv = compose([cv, Hd])
    sx, sy = p['lace_top']
    sy += bob
    draw_lace(cv, [(gbx + 4, gby + 1), (gbx + 5, gby), (sx - 4, sy - 2), (sx, sy), (sx + 4, sy + 2),
                   (gfx + 3, gfy), (gfx + 4, gfy + 1)])
    GFL = layer()
    blk(GFL, gfx, gfy, glove())
    cast_shadow(cv, GFL)
    cv = compose([cv, GFL])
    blk(cv, gbx, gby, gb[:3])
    if p['near_arm'] != 'pocket':
        sh, el, wr, hk = p['near_arm']
        A = layer()
        arms.sleeve(A, (sh[0], sh[1] + bob), (el[0], el[1] + bob), (wr[0], wr[1] + bob))
        hp = p.get('hand_at', (wr[0] + 0.5, wr[1] + 1.5))
        arms.hand(A, hp[0], hp[1] + bob, kind=hk)
        cast_shadow(cv, A)
        cv = compose([cv, A])
    FX = layer()
    for f in p.get('fx', []):
        if f[0] == 'star':
            fx_star(FX, f[1], f[2], f[3])
        elif f[0] == 'rows':
            fx_rows(FX, f[1], f[2], f[3])
    cv = compose([cv, FX])
    return cleanup(outer_outline(cv))


# ------------------------------------------------------------------ poses
SLOUCH_G = dict(gb=(16, 28), gf=(35, 36), lace_top=(28, 31))
UP_G = dict(gb=(15, 26), gf=(35, 34), lace_top=(28, 29))


def walk_gloomy():
    hd = heads.side_head('gloom')
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
    out = []
    for near, far, bob, hdy, gdy in spec:
        out.append(build(dict(torso='slouch', near_arm='pocket', head=hd, head_at=(24, 14), head_dy=hdy,
                              near=near, far=far, bob=bob, gb=(16, 28 + gdy), gf=(35, 36 + gdy), lace_top=(28, 31))))
    return out


def stop():
    hd = heads.side_head('gloom')
    f0 = build(dict(torso='slouch', near_arm='pocket', head=hd, head_at=(25, 14), head_dy=0,
                    near=foot('flat', 33), far=foot('toe', 31, 32), bob=0,
                    gb=(17, 27), gf=(36, 35), lace_top=(28, 31)))
    f1 = build(dict(torso='slouch', near_arm='pocket', head=hd, head_at=(24, 14), head_dy=0,
                    near=foot('flat', 33), far=foot('flat', 28), bob=1,
                    gb=(16, 29), gf=(35, 37), lace_top=(28, 31)))
    return [f0, f1]


STAND = dict(near=foot('flat', 33), far=foot('flat', 28))


def notice():
    f0 = build(dict(STAND, torso='slouch', near_arm='pocket', head=heads.side_head('level'), head_at=(24, 13),
                    bob=0, **SLOUCH_G))
    f1 = build(dict(STAND, torso='slouch', near_arm='pocket', head=heads.turn_head('wide', heads.TURN_MOUTHS['o']),
                    head_at=(24, 13), bob=0, gb=(16, 27), gf=(35, 35), lace_top=(28, 31)))
    return [f0, f1]


def read():
    f0 = build(dict(STAND, torso='slouch', near_arm='pocket', head=heads.turn_head('open'), head_at=(24, 13),
                    bob=0, **SLOUCH_G))
    f1 = build(dict(STAND, torso='slouch', near_arm='pocket', head=heads.turn_head('blink'), head_at=(24, 13),
                    bob=0, **SLOUCH_G))
    return [f0, f1]


def resolve():
    f0 = build(dict(STAND, torso='slouch', head=heads.turn_head('det', heads.TURN_MOUTHS['set']), head_at=(24, 13), bob=0,
                    near_arm=((29, 35), (24.5, 41), (30.5, 45), 'open'), hand_at=(33, 46),
                    gb=(16, 28), gf=(37, 35), lace_top=(28, 31)))
    f1 = build(dict(STAND, torso='up', torso_dy=1, head=heads.side_head('det', heads.SIDE_MOUTHS['set']), head_at=(23, 13),
                    bob=0, near_arm=((29, 35), (29, 42), (35, 37.5), 'fist'), hand_at=(36.5, 36),
                    gb=(15, 27), gf=(34, 36), lace_top=(28, 30),
                    fx=[('rows', 42, 12, SWEAT)]))
    f2 = build(dict(STAND, torso='up', head=heads.side_head('det2', heads.SIDE_MOUTHS['set']), head_at=(23, 11), bob=0,
                    near_arm=((29, 33), (32.5, 41.5), (40, 36), 'fist_big'), hand_at=(42.5, 34),
                    gb=(15, 25), gf=(33, 34), lace_top=(28, 29),
                    fx=[('star', 49, 29, 3)]))
    return [f0, f1, f2]


ARM_N = {  # near arm (shoulder, elbow, wrist)
    'back': ((29, 33), (24.5, 38.5), (19.5, 42)),
    'mback': ((29, 33), (27, 39.5), (24.5, 44.5)),
    'mfwd': ((29, 33), (31, 39.5), (34.5, 44)),
    'fwd': ((29, 33), (34, 38), (39.5, 40)),
}
ARM_F = {k: ((v[0][0] + 2, v[0][1]), (v[1][0] + 2, v[1][1]), (v[2][0] + 2, v[2][1])) for k, v in ARM_N.items()}


def walk_purpose():
    hd = heads.side_head('det2', heads.SIDE_MOUTHS['set'])
    spec = [  # near foot, far foot, bob, near arm, far arm, glove dy
        (foot('heel', 33, -16), foot('toe', 31, 30), 0, 'back', 'fwd', -2),
        (foot('flat', 32), foot('toe', 29, 48, lift=4), 1, 'mback', 'mfwd', 0),
        (foot('toe', 35, 8), foot('flat', 34, -12, lift=3), -1, 'mfwd', 'mback', 2),
        (foot('toe', 31, 30), foot('heel', 33, -16), 0, 'fwd', 'back', -2),
        (foot('toe', 29, 48, lift=4), foot('flat', 32), 1, 'mfwd', 'mback', 0),
        (foot('flat', 34, -12, lift=3), foot('toe', 35, 8), -1, 'mback', 'mfwd', 2),
    ]
    out = []
    for near, far, bob, na_, fa_, gdy in spec:
        n = ARM_N[na_]
        f = ARM_F[fa_]
        out.append(build(dict(torso='up', head=hd, head_at=(24, 11), near=near, far=far, bob=bob,
                              near_arm=(n[0], n[1], n[2], 'fist'), far_arm=(f[0], f[1], f[2], 'fist'),
                              gb=(15, 26 + gdy), gf=(35, 34 + gdy), lace_top=(28, 29))))
    return out


ANIMS = [('walk_gloomy', walk_gloomy), ('stop', stop), ('notice', notice), ('read', read), ('resolve', resolve),
         ('walk_purpose', walk_purpose)]


def all_frames():
    frames, ranges = [], []
    for name, fn in ANIMS:
        fr = fn()
        ranges.append((name, len(frames), len(frames) + len(fr) - 1))
        frames.extend(fr)
    return frames, ranges


def save_strip(frames, path, s=1):
    w, h, img = rgba_strip(frames)
    if s > 1:
        w, h, img = pscale(w, h, img, s)
    write_png(path, w, h, img)


def gif_frames(frames, s=4, bg=(92, 98, 116)):
    out = []
    for c in frames:
        rg = to_rgba(c)
        rg = [[p[:3] if p[3] == 255 else bg for p in row] for row in rg]
        _, _, big = pscale(W, H, rg, s)
        out.append(big)
    return out


if __name__ == '__main__':
    os.makedirs('out', exist_ok=True)
    frames, ranges = all_frames()
    for r in ranges:
        print(r)
    save_strip(frames, 'out/burak_cutscene_1x.png')
    open('out/frames.txt', 'w').write('\n\n'.join(to_text(c) for c in frames))
    print('frames', len(frames))
