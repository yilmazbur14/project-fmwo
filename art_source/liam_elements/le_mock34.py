"""Mocks for attacks 3 and 4 on the real Liam-fight captures (1920x1080, scale 3).

Layering proposed here (bottom to top): the mat; the floor chain (ice/slush/water); the fire rings; the
pillar row and the tornados (y-sorted); THE STEAM FOG; then the player, the red tell and the HUD. The fog
covers the hazards and Liam but never the player or the tell, so 'very hard to see' stays fair.
"""
import math
import os

import numpy as np
from PIL import Image

import le_rig as R
import le_mock as M
import le_pillar as PL
import le_ice as I
import le_a34 as A
import le_a34poses as Q
import le_full as F

S3 = 3
PILLAR_X = 960
FLOOR_Y = 348
ROW_STEP = 108                      # one column (36 texels) per pillar, edge to edge
FLOOD = (113, 114, 1692, 855)


def up(cv):
    return M.up(M.img(cv))


def tile_floor(scene, cv, rect=FLOOD):
    t = up(cv)
    x0, y0, w, h = rect
    layer = Image.new('RGBA', (w, h))
    for y in range(0, h, t.height):
        for x in range(0, w, t.width):
            layer.alpha_composite(t, (x, y))
    scene.alpha_composite(layer, (x0, y0))


def tile_fog(scene, cv, offset=(0, 0)):
    t = up(cv)
    layer = Image.new('RGBA', (1920 + t.width, 1080 + t.height))
    for y in range(0, layer.height, t.height):
        for x in range(0, layer.width, t.width):
            layer.alpha_composite(t, (x, y))
    scene.alpha_composite(layer.crop((offset[0], offset[1], offset[0] + 1920, offset[1] + 1080)), (0, 0))


def pillar_row(scene, centre_frame, centre_sunk=False):
    """Side pillars edge to edge across the top of the ring, his centre pillar in the middle."""
    pieces = []
    for k in range(1, 9):
        for side in (-1, 1):
            x = PILLAR_X + side * k * ROW_STEP
            if 60 < x < 1860:
                pieces.append((x, A.side_pillar((k + (side > 0)) % 3)))
    pieces.sort(key=lambda p: -abs(p[0] - PILLAR_X))
    for x, cv in pieces:
        M.paste_at(scene, up(cv), (x - PL.ANCHOR[0] * S3, FLOOR_Y - PL.ANCHOR[1] * S3))
    if centre_frame is not None:
        M.paste_at(scene, up(centre_frame), (PILLAR_X - PL.ANCHOR[0] * S3, FLOOR_Y - PL.ANCHOR[1] * S3))
    elif centre_sunk:
        dust = PL.blank()
        PL.rubble(dust, 9, spread=1.1)
        PL.dust(dust, [(20, 70, 4), (44, 70, 4)])
        M.paste_at(scene, up(dust), (PILLAR_X - PL.ANCHOR[0] * S3, FLOOR_Y - PL.ANCHOR[1] * S3))


def ring(scene, cx, cy, rx, frame=0):
    """A fire ring of radius rx (ry = 0.55 rx) from quake-ring segments laid round the ellipse, the row
    picked by the screen tangent and mirrored for the other quadrants (Bixby's placement idea)."""
    ry = rx * 0.55
    sheet = A.ring_sheet()
    n = max(10, int(2 * math.pi * rx / 66))
    for i in range(n):
        t = 2 * math.pi * i / n
        x, y = cx + rx * math.cos(t), cy + ry * math.sin(t)
        tx, ty = -rx * math.sin(t), ry * math.cos(t)
        ang = math.degrees(math.atan2(abs(ty), abs(tx)))
        row = min(6, int(round(ang / 15)))
        seg = up(sheet[row][(frame + i) % 4])
        if (tx * ty) < 0:
            seg = seg.transpose(Image.FLIP_LEFT_RIGHT)
        scene.alpha_composite(seg, (int(x - 20 * S3), int(y - 20 * S3)))


def tornado(scene, x, y, cv):
    M.paste_at(scene, up(cv), (x - A.T_PIVOT[0] * S3, y - A.T_PIVOT[1] * S3))


def puffs(scene, pts, k=2):
    for i, (x, y) in enumerate(pts):
        M.paste_at(scene, up(A.steam_puff((k + i) % 5)), (x - 12 * S3, y - 30 * S3))


def liam_on_pillar(scene, cv):
    M.paste_at(scene, up(cv), (PILLAR_X - 48 * S3, 198 - 96 * S3))


TORNADOS = [(380, 520), (1540, 500), (660, 800), (1270, 820), (1720, 860)]
PLAYER_A3 = (1010, 640)


def mock_a3(out_path, end=False):
    nohud, hud, withp = M.load_caps()
    ropes = M.rope_mask(nohud)
    scene = nohud.copy()
    tile_floor(scene, I.ice_melt(0) if not end else I.flood(2))
    for j, (x, y) in enumerate(TORNADOS):
        ring(scene, x, y, (170, 260, 120, 210, 150)[j], frame=j)
    s = np.array(scene)
    s[ropes] = np.array(nohud)[ropes]
    scene = Image.fromarray(s, 'RGBA')
    ig = Q.ignite()[1][0]
    pillar_row(scene, PL.stand_frame(2))
    liam_on_pillar(scene, ig)
    for j, (x, y) in enumerate(TORNADOS):
        tornado(scene, x, y, A.tornado_fire(j % 4))
    puffs(scene, [(250, 700), (820, 560), (1140, 430), (1400, 690), (560, 940), (1650, 700), (900, 900)],
          k=1 if not end else 3)
    tile_fog(scene, A.fog(0 if not end else 2), offset=(40, 70))
    pl, xy = M.player_sprite(nohud, withp)
    M.paste_at(scene, pl, (xy[0] + (PLAYER_A3[0] - 960), xy[1] + (PLAYER_A3[1] - 858)))
    scene = M.finish(scene, nohud, hud)
    M.caption(scene, 'LIAM ATTACK 3 %s: pillar row, fire tornados + fire rings, %s, %s steam over the hazards (not the '
                     'player), HUD 0.30' % ('END' if end else 'MID', 'ice melting to water' if not end else 'water '
                     'boiling off', 'light' if not end else 'heavy'))
    scene.convert('RGB').save(out_path)
    return out_path


PLAYER_A4 = (980, 640)


def mock_a4_tell(out_path):
    nohud, hud, withp = M.load_caps()
    ropes = M.rope_mask(nohud)
    scene = nohud.copy()
    tile_floor(scene, I.flood(1))
    s = np.array(scene)
    s[ropes] = np.array(nohud)[ropes]
    scene = Image.fromarray(s, 'RGBA')
    pillar_row(scene, None, centre_sunk=True)
    puffs(scene, [(300, 600), (700, 480), (1250, 520), (1500, 800), (620, 880)], k=3)
    tile_fog(scene, A.fog(2), offset=(90, 20))
    pl, xy = M.player_sprite(nohud, withp)
    M.paste_at(scene, pl, (xy[0] + (PLAYER_A4[0] - 960), xy[1] + (PLAYER_A4[1] - 858)))
    tri = up(A.triangle(2))
    tx, ty = PLAYER_A4[0] - 190, PLAYER_A4[1] - 40
    M.paste_at(scene, tri, (tx - 13 * S3, ty - 13 * S3))
    scene = M.finish(scene, nohud, hud, alpha=1.0)
    M.caption(scene, 'LIAM ATTACK 4 - THE TELL: heavy steam, his pillar sunk into the row, Liam invisible; the red '
                     'triangle 190 px from the player, aimed at him, drawn above the fog')
    scene.convert('RGB').save(out_path)
    return out_path


def mock_a4_impale(out_path):
    nohud, hud, withp = M.load_caps()
    ropes = M.rope_mask(nohud)
    scene = nohud.copy()
    tile_floor(scene, I.flood(1))
    s = np.array(scene)
    s[ropes] = np.array(nohud)[ropes]
    scene = Image.fromarray(s, 'RGBA')
    pillar_row(scene, None, centre_sunk=True)
    liam_at = (860, 760)
    cv, pts = Q.impale()[2]
    M.paste_at(scene, up(cv), (liam_at[0] - 48 * S3, liam_at[1] - 96 * S3))
    hang = (liam_at[0] + (pts['hang'][0] - 48) * S3, liam_at[1] + (pts['hang'][1] - 96) * S3)
    # the player hangs on the staff's crown: his own sprite, centred on the hang point
    pl, xy = M.player_sprite(nohud, withp)
    px, py = int(hang[0] - 60), int(hang[1] - 62)
    # Bixby's fire from above: the approved flyby curtain stacked from off screen down to the player
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cur = Image.open(os.path.join(root, 'Assets', 'Characters', 'Bixby', 'bixby_flyby_curtain.png')).convert('RGBA')
    tile = cur.crop((0, 0, 32, 48)).resize((96, 144), Image.NEAREST)
    col = Image.new('RGBA', (96, int(hang[1]) + 20))
    for y in range(-144 + (int(hang[1]) + 20) % 144, col.height, 144):
        col.alpha_composite(tile, (0, y)) if y >= 0 else col.alpha_composite(tile.crop((0, -y, 96, 144)), (0, 0))
    scene.alpha_composite(col, (int(hang[0] - 48), 0))
    M.paste_at(scene, pl, (px, py))
    M.paste_at(scene, up(A.flame_overlay(1)), (int(hang[0] - 12 * S3), int(hang[1] + 40 - 34 * S3)))
    M.paste_at(scene, up(A.fire_hit(2)), (int(hang[0] - 24 * S3), int(hang[1] - 30 - 16 * S3)))
    puffs(scene, [(560, 640), (1280, 700), (1100, 900), (420, 860)], k=2)
    tile_fog(scene, A.fog(1), offset=(10, 50))
    scene = M.finish(scene, nohud, hud, alpha=1.0)
    M.caption(scene, 'LIAM ATTACK 4 - IMPALED: Liam bellowing for Bixby, the player hung on the staff crown, Bixby\'s '
                     'fire (bixby_flyby_curtain stacked from off screen) pouring onto him, flames on him')
    scene.convert('RGB').save(out_path)
    return out_path
