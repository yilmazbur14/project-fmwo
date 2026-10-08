"""Attacks 3-4 mocks, v3, on the real Liam-fight captures (1920x1080, scale 3), laid out by ADDENDUM3:
the row (16 neighbours at 960 +- 108k on y 348, his pillar in the middle), the four tornado spots,
Bixby's ring placement (BixbyCombinedArtLayout.ring_segments: 48 px of screen arc apart, rows by the
screen tangent, flips, neighbours a frame apart), the parry badge (parry_tell.png, pivot (16, 24) at
3x, 220 px over the lunge origin), and the steam shader simulated as B.6 writes it:

    alpha = density * tile * smoothstep(bubble, bubble + feather, dist to the player) * (1 - 0.85 warm)
    warm(c) = clamp((c.r - c.b - 0.25) * 3, 0, 1) * smoothstep(0.45, 0.8, max(c.r, c.g))

(the tile sampled twice at two drift offsets, snapped to 3 px blocks). Draw order: floor, rings, the
y-sorted row / tornados / Liam / player, the steam (z 2), FxLayer (sky fire, flames), the badge, the HUD.
"""
import math
import os

import numpy as np
from PIL import Image

import le_rig as R
import le_mock as M
import le_pillar as PL
import le_row as RW
import le_ice as I
import le_a34fx as X
import le_tornado as TN
import le_a34poses3 as Q
import le_full as F

S3 = 3
PILLAR_X, FLOOR_Y = 960, 348
LIAM_FEET = (960, 198)
TORNADO_SPOTS = [(520, 520), (1400, 520), (760, 820), (1160, 820)]
FLOOD = (113, 114, 1692, 855)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def up(cv):
    return M.up(M.img(cv))


def paste(scene, cv_or_img, at, pivot):
    im = up(cv_or_img) if not isinstance(cv_or_img, Image.Image) else cv_or_img
    scene.alpha_composite(im, (int(round(at[0] - pivot[0] * S3)), int(round(at[1] - pivot[1] * S3))))


# ------------------------------------------------------------------ the floor
def tiled(cv, rect=FLOOD):
    t = up(cv)
    x0, y0, w, h = rect
    layer = Image.new('RGBA', (1920, 1080))
    for y in range(y0, y0 + h, t.height):
        for x in range(x0, x0 + w, t.width):
            layer.alpha_composite(t, (x, y))
    m = np.zeros((1080, 1920), bool)
    m[y0:y0 + h, x0:x0 + w] = True
    a = np.array(layer)
    a[~m] = 0
    return Image.fromarray(a, 'RGBA')


def floor(scene, water_k=3, ice_r=None, rims=True):
    """Water (flood coverage frame water_k) where the ice has melted: circles of radius ice_r round the
    tornado spots (None = all melted); ice elsewhere with melt-rim stamps on each circle."""
    water = tiled(I.flood(water_k))
    if ice_r is None:
        scene.alpha_composite(water)
        return
    ice = np.array(tiled(I.ice(0)))
    w = np.array(water)
    ys, xs = np.mgrid[0:1080, 0:1920]
    melted = np.zeros((1080, 1920), bool)
    for (x, y) in TORNADO_SPOTS:
        melted |= (xs - x) ** 2 + (ys - y) ** 2 <= ice_r ** 2
    out = np.where(melted[..., None], w, ice)
    scene.alpha_composite(Image.fromarray(out.astype(np.uint8), 'RGBA'))
    if rims:
        rim = up(X.melt_rim(1))
        for (x, y) in TORNADO_SPOTS:
            n = int(2 * math.pi * ice_r / 60)
            for i in range(n):
                a = 2 * math.pi * i / n
                px, py = x + ice_r * math.cos(a), y + ice_r * math.sin(a)
                if FLOOD[0] + 20 < px < FLOOD[0] + FLOOD[2] - 20 and FLOOD[1] + 20 < py < FLOOD[1] + FLOOD[3] - 20:
                    inside_other = any((px - ox) ** 2 + (py - oy) ** 2 < (ice_r - 8) ** 2 for (ox, oy) in TORNADO_SPOTS
                                       if (ox, oy) != (x, y))
                    if not inside_other:
                        scene.alpha_composite(rim, (int(px) - 24, int(py) - 24))


# ------------------------------------------------------------------ Bixby's ring placement
FLOOR_FLATTEN = 0.36
SEG_ARC = 48.0
ROW_TANGENTS = [7.0, 20.3, 35.8, 54.2, 69.7, 83.0]
GROUND = [[45, -15, 15], [57, -27, 24], [60, -24, 24], [60, -36, 30], [51, -42, 39], [45, -48, 45], [39, -45, 42]]
CREST = [-45, -48, -48, -48, -48, -48, -48]
SHOWN = (92, 348, 1734, 640)
_ARC = None


def _arc():
    global _ARC
    if _ARC is None:
        n = 4096
        th = math.pi / 2 + np.arange(n + 1) * (2 * math.pi / n)
        sp = np.sqrt(np.sin(th) ** 2 + (FLOOR_FLATTEN * np.cos(th)) ** 2)
        ln = np.concatenate([[0], np.cumsum(0.5 * (sp[1:] + sp[:-1]) * (2 * math.pi / n))])
        _ARC = (th, ln)
    return _ARC


def ring_segments(radius):
    th, ln = _arc()
    per = ln[-1]
    count = 4 * max(1, int(round(radius * per / (4 * SEG_ARC))))
    out = []
    for i in range(count):
        theta = float(np.interp(per * i / count, ln, th))
        tangent = math.degrees(math.atan2(FLOOR_FLATTEN * abs(math.cos(theta)), abs(math.sin(theta))))
        row = len(ROW_TANGENTS)
        for b, lim in enumerate(ROW_TANGENTS):
            if tangent < lim:
                row = b
                break
        flip = 1 <= row <= 5 and math.sin(theta) * math.cos(theta) < 0
        out.append((theta, row, flip))
    return out


_RING = None


def ring(scene, centre, radius, beat=0, dying=None):
    """One quake ring round `centre` at `radius` px of floor (its sheet's frames; dying = frame k of the
    dying rows)."""
    global _RING
    if _RING is None:
        _RING = X.ring_sheet(8, dying=True)
    segs = ring_segments(radius)
    placed = []
    for i, (theta, row, flip) in enumerate(segs):
        x = centre[0] + radius * math.cos(theta)
        y = centre[1] + radius * FLOOR_FLATTEN * math.sin(theta)
        x, y = round(x / 3) * 3, round(y / 3) * 3
        g = GROUND[row]
        if not (x - g[0] >= SHOWN[0] and x + g[0] <= SHOWN[0] + SHOWN[2] and y + g[2] <= SHOWN[1] + SHOWN[3]
                and y + CREST[row] >= SHOWN[1]):
            continue
        cv = _RING[row + 7][dying] if dying is not None else _RING[row][(beat + i) % 8]
        im = up(cv)
        if flip:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        placed.append((y, x, im))
    for y, x, im in sorted(placed, key=lambda p: p[0]):
        scene.alpha_composite(im, (int(x - X.RING_PIVOT[0] * S3), int(y - X.RING_PIVOT[1] * S3)))


# ------------------------------------------------------------------ the row, Liam, the player
def row_and_pillar(scene, liam_cv=None, stump=None, crumble=None):
    """The 16 neighbours (variants by distance, as LiamRow does) and his pillar (stand, or the stump at
    risen `stump`), with Liam's frame on his pillar's stand point."""
    for k in range(8, 0, -1):
        for side in (-1, 1):
            x = PILLAR_X + side * 108 * k
            v = k % 3
            cv = RW.stand(v) if crumble is None else RW.crumble(crumble, v)
            paste(scene, cv, (x, FLOOR_Y), PL.ANCHOR)
    if stump is not None:
        cv = PL.column_at(int(round(50 * stump)))
        paste(scene, cv, (PILLAR_X, FLOOR_Y), PL.ANCHOR)
    else:
        paste(scene, PL.stand_frame(0), (PILLAR_X, FLOOR_Y), PL.ANCHOR)
    if liam_cv is not None:
        paste(scene, liam_cv, LIAM_FEET, (48, 96))


def player(scene, nohud, withp, centre):
    """The captured player with his body (CharacterBody2D) at `centre` (his feet 38 px below it)."""
    pl, xy = M.player_sprite(nohud, withp)
    dx, dy = centre[0] - M.PLAYER_BODY_CAPTURED[0], centre[1] - M.PLAYER_BODY_CAPTURED[1]
    scene.alpha_composite(pl, (int(round(xy[0] + dx)), int(round(xy[1] + dy))))


# ------------------------------------------------------------------ the steam (B.6 simulated)
_TILES = None
HUD_RECTS = [(0, 945, 285, 1080), (1530, 955, 1920, 1080)]   # the player HUD (baked into the capture)


def steam(scene, density, bubble_at, bubble_r=150.0, feather=70.0, drift=((0, 0), (37, 53)), glow=0.85):
    global _TILES
    if _TILES is None:
        _TILES = [R.to_rgba(X.steam_tile(0)), R.to_rgba(X.steam_tile(1))]
    s = np.array(scene).astype(float) / 255.0
    ys, xs = np.mgrid[0:1080, 0:1920]
    tx, ty = xs // 3, ys // 3                             # 3 px blocks
    a0 = _TILES[0][(ty + drift[0][1]) % 128, (tx + drift[0][0]) % 128, 3] / 255.0
    a1 = _TILES[1][(ty + drift[1][1]) % 128, (tx + drift[1][0]) % 128, 3] / 255.0
    tile = np.maximum(a0, a1 * 0.9)
    d = np.hypot(xs - bubble_at[0], ys - bubble_at[1])
    t = np.clip((d - bubble_r) / feather, 0, 1)
    bub = t * t * (3 - 2 * t)
    c = s[..., :3]
    warm = np.clip((c[..., 0] - c[..., 2] - 0.25) * 3, 0, 1)
    mx = np.maximum(c[..., 0], c[..., 1])
    k = np.clip((mx - 0.45) / 0.35, 0, 1)
    warm = warm * k * k * (3 - 2 * k)
    alpha = density * tile * bub * (1 - glow * warm)
    for (x0, y0, x1, y1) in HUD_RECTS:              # the HUD is a CanvasLayer over the steam
        alpha[y0:y1, x0:x1] = 0
    col = np.array([244, 247, 250]) / 255.0
    s[..., :3] = c * (1 - alpha[..., None]) + col * alpha[..., None]
    return Image.fromarray((s * 255).astype(np.uint8), 'RGBA')


def badge(scene, origin, frame=0):
    im = Image.open(os.path.join(ROOT, 'Assets', 'Effects', 'parry_tell.png')).convert('RGBA')
    fr = im.crop((frame * 32, 0, frame * 32 + 32, 24)).resize((96, 72), Image.NEAREST)
    ax, ay = origin[0], origin[1] - 186 - 34
    scene.alpha_composite(fr, (int(ax - 16 * 3), int(ay - 24 * 3)))
    return (ax, ay)


def sky_fire_column(scene, x, bottom, frame=0, use_curtain=False):
    """The column from the screen top to `bottom` (the player's head): Bixby's curtain stacked (the
    default) or liam_sky_fire (optional)."""
    if use_curtain:
        cur = Image.open(os.path.join(ROOT, 'Assets', 'Characters', 'Bixby', 'bixby_flyby_curtain.png')).convert('RGBA')
        tile = cur.crop((frame % 4 * 32, 0, frame % 4 * 32 + 32, 48)).resize((96, 144), Image.NEAREST)
    else:
        tile = up(X.sky_fire(frame % 6))
    y = bottom - 144
    while y > -144:
        scene.alpha_composite(tile, (int(x - 48), int(y)))
        y -= 144


# ------------------------------------------------------------------ the four mocks
PLAYER_A3 = (972, 660)


def mock_firestorm(out_path, late=False):
    """Attack 3: the four fire tornados with their burning base rings and pull swirls, quake rings out
    at their radii, the floor melted to water (mid: ice lingering at the far corners with melt rims;
    late: evaporating, puddles), the steam thickening (0.3 mid / 0.85 late) with the clear bubble round
    the player and the fire glowing through it, Liam channelling on his pillar in the row."""
    nohud, hud, withp = M.load_caps()
    ropes = M.rope_mask(nohud)
    scene = nohud.copy()
    if late:
        floor(scene, water_k=1)
    else:
        floor(scene, water_k=4, ice_r=560)
    # pull swirls on the floor under each tornado
    for i, (x, y) in enumerate(TORNADO_SPOTS):
        paste(scene, X.pull_swirl(i * 2 % 8, kind='water'), (x, y), X.SWIRL_PIVOT)
    # the rings (WaveLayer-like, under the ropes and the fighters): radii per tornado
    radii = [(120, 300), (200,), (90, 330), (240,)] if not late else [(150, 340), (250,), (100,), (200, 355)]
    for i, (c, rs) in enumerate(zip(TORNADO_SPOTS, radii)):
        for j, r in enumerate(rs):
            ring(scene, c, r, beat=i + j * 3, dying=(4 if (late and r > 340) else None))
    s = np.array(scene)
    s[ropes] = np.array(nohud)[ropes]
    scene = Image.fromarray(s, 'RGBA')
    # the y-sorted layer: row + Liam (y 348), tornados (520, 820), the player
    ch = Q.fitted(Q.channel)()[2][0]
    row_and_pillar(scene, ch)
    frames = [2, 5, 0, 7] if not late else [3, 6, 1, 4]
    items = [(y, ('t', x, y, frames[i])) for i, (x, y) in enumerate(TORNADO_SPOTS)]
    items.append((PLAYER_A3[1] + 38, ('p',)))
    for _, it in sorted(items, key=lambda p: p[0]):
        if it[0] == 't':
            _, x, y, fr = it
            cv = TN.tornado_spew(1) if (fr == 5 and not late) else TN.tornado_fire(fr)
            paste(scene, cv, (x, y), TN.PIVOT)
        else:
            player(scene, nohud, withp, PLAYER_A3)
    # steam over all of it but the player's bubble; fire glows through
    scene = steam(scene, 0.85 if late else 0.3, (PLAYER_A3[0], PLAYER_A3[1]))
    scene = M.finish(scene, nohud, hud)
    M.caption(scene, 'LIAM ATTACK 3 - FIRESTORM %s: 4 fire tornados (spots 520/1400,520 760/1160,820), quake rings in '
                     "Bixby's format, %s, steam %.2f with the player's bubble, fire glowing through; HUD 0.30"
              % ('LATE' if late else 'MID', 'water evaporating' if late else 'ice melting from each tornado',
                 0.85 if late else 0.3))
    scene.convert('RGB').save(out_path)
    return out_path


PLAYER_A4 = (1100, 660)


def mock_lunge_badge(out_path, side=-1):
    """Attack 4, the tell: steam at 0.85, his pillar sunk to the stump in the row, Liam invisible, the
    player in his bubble, the red parry badge over the lunge origin 300 px beside him."""
    nohud, hud, withp = M.load_caps()
    ropes = M.rope_mask(nohud)
    scene = nohud.copy()
    s = np.array(scene)
    s[ropes] = np.array(nohud)[ropes]
    scene = Image.fromarray(s, 'RGBA')
    row_and_pillar(scene, None, stump=0.3)
    player(scene, nohud, withp, PLAYER_A4)
    scene = steam(scene, 0.85, PLAYER_A4)
    origin = (PLAYER_A4[0] + side * 300, PLAYER_A4[1] + 38)
    badge(scene, origin, frame=0)
    scene = M.finish(scene, nohud, hud, alpha=1.0)
    M.caption(scene, 'LIAM ATTACK 4 - THE TELL: steam 0.85, his pillar sunk to the stump, Liam invisible; the red '
                     'parry badge over the lunge origin 300 px beside the player (0.40 s to impact)')
    scene.convert('RGB').save(out_path)
    return out_path


LIAM_A4 = (820, 760)


def mock_impale(out_path, call_frame=0, fire_frame=2):
    """Attack 4, the impale: the bubble opened to 340 so both read, Liam bellowing for Bixby with the
    player high on his staff, Bixby's fire pouring down from off screen onto him, splashing off his
    head, flames all over him."""
    nohud, hud, withp = M.load_caps()
    ropes = M.rope_mask(nohud)
    scene = nohud.copy()
    s = np.array(scene)
    s[ropes] = np.array(nohud)[ropes]
    scene = Image.fromarray(s, 'RGBA')
    row_and_pillar(scene, None, stump=0.3)
    cv, pts = Q.fitted(Q.impale_call)()[call_frame]
    tip = pts['staff_tip']
    feet = LIAM_A4
    paste(scene, cv, feet, (48, 144))
    held = (feet[0] + (tip[0] - 48) * S3, feet[1] + (tip[1] - 144) * S3)
    player(scene, nohud, withp, held)
    scene = steam(scene, 0.85, held, bubble_r=340.0)
    # FxLayer: sky fire from the top down to his head, the splash, flames on him
    head_top = (held[0], held[1] - 37)
    sky_fire_column(scene, head_top[0], head_top[1] + 6, frame=fire_frame)
    paste(scene, X.sky_fire_splash(fire_frame), head_top, (24, 28))
    paste(scene, X.player_flames(fire_frame), (held[0], held[1] + 38), (12, 30))
    scene = M.finish(scene, nohud, hud, alpha=1.0)
    M.caption(scene, 'LIAM ATTACK 4 - IMPALED: the bubble opened to 340 px, Liam calling for Bixby with the player '
                     'on the staff tip (%d px above his feet), sky fire + splash + flames on FxLayer over the steam'
              % int(round((144 - tip[1]) * S3)))
    scene.convert('RGB').save(out_path)
    return out_path
