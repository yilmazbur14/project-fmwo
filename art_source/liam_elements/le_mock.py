"""1920x1080 mocks of Liam's elements phase, built on real captures of the Liam fight
(capture_liam_arena.gd -> scratchpad cap/arena_nohud.png, arena_hud.png, arena_player.png), composed in
the game's draw order: FloorLayer, WaveLayer (under the ropes), the y-sorted pillar + Liam + player,
FxLayer, then the boss HUD re-blended at modulate.a 0.30 (PLAN 3: `pillar_hud_fade_alpha`).
Every sprite is placed by the contract's anchors at scale 3.
"""
import os

import numpy as np
from PIL import Image, ImageDraw

import le_rig as R
import le_view as V

S3 = 3
CAP = os.path.join(V.SCRATCH, 'cap')
PILLAR_FLOOR = (960, 348)            # pillar anchor (floor-line centre)
LIAM_FEET = (960, 198)               # Liam's anchor point while on the pillar
PLAYER_BODY_CAPTURED = (960, 858)    # where the capture stood the player (CharacterBody2D)


def img(cv):
    return Image.fromarray(R.to_rgba(cv), 'RGBA')


def up(im, s=S3):
    return im.resize((im.width * s, im.height * s), Image.NEAREST)


def load_caps():
    nohud = Image.open(os.path.join(CAP, 'arena_nohud.png')).convert('RGBA')
    hud = Image.open(os.path.join(CAP, 'arena_hud.png')).convert('RGBA')
    pl = Image.open(os.path.join(CAP, 'arena_hud.png')).convert('RGBA')
    withp = Image.open(os.path.join(CAP, 'arena_player.png')).convert('RGBA')
    return nohud, hud, withp


def hud_mask(nohud, hud):
    a, b = np.array(nohud)[..., :3].astype(int), np.array(hud)[..., :3].astype(int)
    return np.abs(a - b).sum(axis=2) > 0


def rope_mask(nohud):
    """Pixels of the ring's ropes and posts (which draw over the WaveLayer)."""
    a = np.array(nohud)[..., :3].astype(int)
    h, w = a.shape[:2]
    m = np.zeros((h, w), dtype=bool)
    pure = ((a == 0).all(axis=2)) | ((a == 255).all(axis=2))
    band = np.zeros((h, w), dtype=bool)
    band[86:116, :] = True                 # the top rope
    band[:, 86:122] = True                 # left rope + posts
    band[:, 1798:1836] = True              # right rope + posts
    m |= pure & band
    # the gold corner posts
    for (x0, y0, x1, y1) in ((86, 60, 136, 175), (1776, 60, 1836, 175), (86, 920, 136, 990), (1776, 920, 1836, 990)):
        sub = a[y0:y1, x0:x1]
        gold = (sub[..., 0] > 120) & (sub[..., 1] > 90) & (sub[..., 2] < 90)
        m[y0:y1, x0:x1] |= gold
    return m


def player_sprite(nohud, withp):
    """Cut the captured player out (pixels that differ from the empty arena around him)."""
    x0, y0 = PLAYER_BODY_CAPTURED[0] - 60, PLAYER_BODY_CAPTURED[1] - 70
    box = (x0, y0, x0 + 120, y0 + 130)
    a = np.array(nohud.crop(box)).astype(int)
    b = np.array(withp.crop(box))
    diff = np.abs(a[..., :3] - b[..., :3].astype(int)).sum(axis=2) > 0
    out = np.zeros_like(b)
    out[diff] = b[diff]
    return Image.fromarray(out, 'RGBA'), (x0, y0)


def paste_at(base, sprite, xy):
    base.alpha_composite(sprite, (int(xy[0]), int(xy[1])))


def caption(base, text):
    d = ImageDraw.Draw(base)
    w = 9 + 7 * len(text)
    bar = Image.new('RGBA', (w, 20), (0, 0, 0, 170))
    base.alpha_composite(bar, (0, 0))
    d.text((6, 4), text, fill=(255, 255, 255, 255))


def finish(scene, nohud, hud, alpha=0.30):
    """Re-blend the boss HUD over the finished scene at modulate.a alpha."""
    m = hud_mask(nohud, hud)
    s = np.array(scene).astype(float)
    h = np.array(hud).astype(float)
    s[m, :3] = s[m, :3] * (1 - alpha) + h[m, :3] * alpha
    return Image.fromarray(s.astype(np.uint8), 'RGBA')


def liam_on_pillar(scene, liam_cv, pillar_cv):
    import le_pillar as PL
    pil = up(img(pillar_cv))
    paste_at(scene, pil, (PILLAR_FLOOR[0] - PL.ANCHOR[0] * S3, PILLAR_FLOOR[1] - PL.ANCHOR[1] * S3))
    li = up(img(liam_cv))
    paste_at(scene, li, (LIAM_FEET[0] - 48 * S3, LIAM_FEET[1] - 96 * S3))


def mock_attack1(out_path):
    """Liam on his pillar casting, a right wave just rolled in from off screen, the older left wave
    lower down, the player at the bottom centre; HUD at 0.30."""
    import le_water as W
    import le_pillar as PL
    import le_posedefs as D
    nohud, hud, withp = load_caps()
    ropes = rope_mask(nohud)
    scene = nohud.copy()
    # WaveLayer: left wave (older) front at y 690, right wave front at y 330 (zero gap: 690 - 360)
    wave = up(img(W.full_wave(1)))
    wave_r = wave.transpose(Image.FLIP_LEFT_RIGHT)
    edge = up(img(W.wave_edge()))
    edge_r = edge.transpose(Image.FLIP_LEFT_RIGHT)
    paste_at(scene, wave, (113, 690 - 360))
    paste_at(scene, edge, (113 + W.WW * S3 - W.EDGE_AT * S3, 690 - 360))
    paste_at(scene, wave_r, (961, 330 - 360))
    paste_at(scene, edge_r, (961 - (W.EDGE_W - W.EDGE_AT) * S3, 330 - 360))
    # ropes and posts draw over the waves
    s = np.array(scene)
    s[ropes] = np.array(nohud)[ropes]
    scene = Image.fromarray(s, 'RGBA')
    liam, meta = D.pose_b_cast()
    liam_on_pillar(scene, liam, PL.stand_frame(1))
    pl, xy = player_sprite(nohud, withp)
    paste_at(scene, pl, (xy[0], xy[1] + 40))
    scene = finish(scene, nohud, hud)
    caption(scene, 'LIAM ELEMENTS - ATTACK 1 MOCK: pillar at (960,348), Liam feet (960,198), waves 846x360 on WaveLayer under the ropes, HUD at 0.30')
    scene.convert('RGB').save(out_path)
    return out_path


def mock_attack2(out_path):
    """The iced ring with pattern B (the switchback, 38.png) standing, Liam slamming on his pillar, the
    player at the bottom starting the route; HUD at 0.30."""
    import le_ice as I
    import le_earth as E
    import le_pillar as PL
    import le_posedefs as D
    nohud, hud, withp = load_caps()
    ropes = rope_mask(nohud)
    scene = nohud.copy()
    # FloorLayer: the ice sheet over Rect2(113, 114, 1692, 855)
    tile = up(img(I.ice()))
    tile_g = up(img(I.ice(True)))
    ice = Image.new('RGBA', (1692, 855))
    for j, y in enumerate(range(0, 855, 192)):
        for i, x in enumerate(range(0, 1692, 192)):
            ice.alpha_composite(tile_g if (i + j) % 3 == 0 else tile, (x, y))
    scene.alpha_composite(ice, (113, 114))
    # tremor ridges: pattern B (PLAN 6.5), footprint Rect2(x, y, 288, 72) = sprite rows 8..31
    upper = [(1517, 262), (1277, 310), (1108, 358), (868, 406), (628, 406), (388, 430)]
    lower = [(113, 662), (353, 686), (593, 710), (833, 734), (1073, 734)]
    frames = E.block_frames()
    blocks = sorted(upper + lower, key=lambda p: p[1])     # y-sort: the ones further up first
    for i, (x, y) in enumerate(blocks):
        f = frames[7 + (i % 4)] if i % 5 else frames[11]
        paste_at(scene, up(img(f)), (x, y - 8 * S3))
    s = np.array(scene)
    s[ropes] = np.array(nohud)[ropes]
    scene = Image.fromarray(s, 'RGBA')
    liam, meta = D.pose_j_tremor()
    liam_on_pillar(scene, liam, PL.stand_frame(3))
    # the slam burst on the staff butt (FxLayer)
    bx, by = meta['impact']
    burst = up(img(E.slam_burst(0)))
    paste_at(scene, burst, (LIAM_FEET[0] + (bx - 48) * S3 - 16 * S3, LIAM_FEET[1] + (by - 96) * S3 - 15 * S3 + 3))
    pl, xy = player_sprite(nohud, withp)
    paste_at(scene, pl, (xy[0] - 380, xy[1] + 40))
    scene = finish(scene, nohud, hud)
    caption(scene, 'LIAM ELEMENTS - ATTACK 2 MOCK: iced ring, pattern B switchback (PLAN 6.5), ridges 288x72 footprints, Liam tremor-slamming, HUD at 0.30')
    scene.convert('RGB').save(out_path)
    return out_path
