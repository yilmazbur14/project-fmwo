"""FX v2: a small compositor for the before/after GIFs and the in-fight mocks, on real captures of the Liam fight
(capture_liam_arena.gd -> the scratchpad's liam_elements/cap/: arena_nohud.png, arena_hud.png, arena_player.png; point
FX_V2_CAP at another copy). It follows the game's draw order - FloorLayer (flood, ice, frost, ridges, cracks, the
downdraft), WaveLayer (waves and their tells) under the ropes, the y-sorted pillar, Liam and player, FxLayer (gust,
breath, slam bursts, splashes, lone gusts), then the boss HUD re-blended at 0.30 (pillar_hud_fade_alpha) - and places
every sprite by LiamArtLayout's numbers at scale 3. It reads the approved sheets from approval/ and writes nothing.
"""
import math
import os
import sys

sys.dont_write_bytecode = True

import numpy as np
from PIL import Image

import fx_common as C

S = 3
CAP_DEFAULT = os.path.join(r'C:\Users\theyi\AppData\Local\Temp\claude\C--Users-theyi-OneDrive-Documents-new-game-project',
                           r'a7fc2846-afef-472d-979b-e17143793a0f\scratchpad\liam_elements\cap')
PERCH = (960, 348)                  # the pillar's floor-line centre (LiamStateMachine.PERCH)
LIAM_FEET = (960, 198)              # his feet on the pillar: PERCH - STAND_HEIGHT
ROPES = (113, 114, 1692, 855)       # LiamStateMachine.ROPES = LiamArtLayout.FLOOD_RECT
WAVE_LEFT_X = (105, 966)
WAVE_RIGHT_X = (954, 1815)
PLAYER_CAPTURED = (960, 858)        # where the capture stood the player (CharacterBody2D)
HUD_ALPHA = 0.30


def cap_dir():
    return os.environ.get('FX_V2_CAP', CAP_DEFAULT)


_cache = {}


def _load(path):
    if path not in _cache:
        _cache[path] = Image.open(path).convert('RGBA')
    return _cache[path]


def img(cv):
    return Image.fromarray(C.rgba(cv), 'RGBA')


def up(im, s=S):
    return im.resize((im.width * s, im.height * s), Image.NEAREST)


class Frames:
    """A strip's frames as upscaled PIL images, from key canvases (new) or a shipped PNG (approval/)."""

    def __init__(self, frames=None, png=None, fw=None):
        if frames is not None:
            self.small = [img(f) for f in frames]
        else:
            strip = _load(png)
            n = strip.width // fw
            self.small = [strip.crop((i * fw, 0, (i + 1) * fw, strip.height)) for i in range(n)]
        self._big = {}

    def __len__(self):
        return len(self.small)

    def big(self, i):
        i = int(i) % len(self.small)
        if i not in self._big:
            self._big[i] = up(self.small[i])
        return self._big[i]


def shipped_frames(name, fw):
    return Frames(png=os.path.join(C.APPROVAL, name + '.png'), fw=fw)


def pose_frames(name):
    return Frames(png=os.path.join(C.APPROVAL_FULL, 'liam_%s.png' % name), fw=96)


def pillar_frames():
    return Frames(png=os.path.join(C.APPROVAL, 'liam_pillar.png'), fw=64)


class Arena:
    """The captured arena and what the compositor needs from it."""

    def __init__(self):
        d = cap_dir()
        for n in ('arena_nohud.png', 'arena_hud.png', 'arena_player.png'):
            if not os.path.exists(os.path.join(d, n)):
                raise SystemExit('fx_scene: no arena capture %s in %s (set FX_V2_CAP)' % (n, d))
        self.nohud = _load(os.path.join(d, 'arena_nohud.png'))
        self.hud = _load(os.path.join(d, 'arena_hud.png'))
        self.withp = _load(os.path.join(d, 'arena_player.png'))
        a = np.array(self.nohud)[..., :3].astype(int)
        b = np.array(self.hud)[..., :3].astype(int)
        self.hud_mask = np.abs(a - b).sum(axis=2) > 0
        self.ropes = self._rope_mask(a)
        self.player, self.player_off = self._player()

    @staticmethod
    def _rope_mask(a):
        """The ring's ropes and posts, which draw over the WaveLayer (le_mock's rule, re-derived here)."""
        h, w = a.shape[:2]
        m = np.zeros((h, w), dtype=bool)
        pure = ((a == 0).all(axis=2)) | ((a == 255).all(axis=2))
        band = np.zeros((h, w), dtype=bool)
        band[86:116, :] = True
        band[:, 86:122] = True
        band[:, 1798:1836] = True
        m |= pure & band
        for (x0, y0, x1, y1) in ((86, 60, 136, 175), (1776, 60, 1836, 175), (86, 920, 136, 990), (1776, 920, 1836, 990)):
            sub = a[y0:y1, x0:x1]
            gold = (sub[..., 0] > 120) & (sub[..., 1] > 90) & (sub[..., 2] < 90)
            m[y0:y1, x0:x1] |= gold
        return m

    def _player(self):
        x0, y0 = PLAYER_CAPTURED[0] - 60, PLAYER_CAPTURED[1] - 70
        box = (x0, y0, x0 + 120, y0 + 130)
        a = np.array(self.nohud.crop(box)).astype(int)
        b = np.array(self.withp.crop(box))
        diff = np.abs(a[..., :3] - b[..., :3].astype(int)).sum(axis=2) > 0
        out = np.zeros_like(b)
        out[diff] = b[diff]
        return Image.fromarray(out, 'RGBA'), (x0 - PLAYER_CAPTURED[0], y0 - PLAYER_CAPTURED[1])


class Shot:
    """One frame of a scene over a crop (x, y, w, h) of the 1920 x 1080 screen, built layer by layer."""

    def __init__(self, arena, crop):
        self.arena = arena
        self.crop = crop
        x, y, w, h = crop
        self.im = arena.nohud.crop((x, y, x + w, y + h)).copy()

    def paste(self, sprite, xy):
        x, y = int(round(xy[0])) - self.crop[0], int(round(xy[1])) - self.crop[1]
        if x >= self.crop[2] or y >= self.crop[3] or x + sprite.width <= 0 or y + sprite.height <= 0:
            return
        self.im.alpha_composite(sprite, (max(0, x), max(0, y)),
                                (max(0, -x), max(0, -y)))

    def at_pivot(self, sprite, pos, pivot):
        """A Sprite2D standing its pivot texel on `pos` (centered, offset = frame/2 - pivot)."""
        self.paste(sprite, (pos[0] - pivot[0] * S, pos[1] - pivot[1] * S))

    def tile(self, tile_small, rect=ROPES, mask=None, clip_to=None):
        """A tile repeated over `rect` from its top-left (LiamFlood._tiled), optionally cut by a boolean screen mask
        and/or clipped to another layer's alpha (clip_children)."""
        x, y, w, h = self.crop
        rx, ry, rw, rh = rect
        big = up(tile_small)
        tw, th = big.size
        layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        x0 = rx + ((x - rx) // tw) * tw if x > rx else rx
        y0 = ry + ((y - ry) // th) * th if y > ry else ry
        for ty in range(y0, min(ry + rh, y + h), th):
            for tx in range(x0, min(rx + rw, x + w), tw):
                layer.alpha_composite(big, (max(0, tx - x), max(0, ty - y)),
                                      (max(0, x - tx), max(0, y - ty)))
        a = np.array(layer)
        # cut to the rect
        ys, xs = np.mgrid[y:y + h, x:x + w]
        inside = (xs >= rx) & (xs < rx + rw) & (ys >= ry) & (ys < ry + rh)
        if mask is not None:
            inside &= mask(xs, ys)
        if clip_to is not None:
            inside &= clip_to
        a[~inside] = 0
        self.im.alpha_composite(Image.fromarray(a, 'RGBA'))
        return a[..., 3] > 0

    def ropes(self):
        x, y, w, h = self.crop
        m = self.arena.ropes[y:y + h, x:x + w]
        s = np.array(self.im)
        s[m] = np.array(self.arena.nohud)[y:y + h, x:x + w][m]
        self.im = Image.fromarray(s, 'RGBA')

    def player(self, body_pos):
        off = self.arena.player_off
        self.paste(self.arena.player, (body_pos[0] + off[0], body_pos[1] + off[1]))

    def hud(self, alpha=HUD_ALPHA):
        x, y, w, h = self.crop
        m = self.arena.hud_mask[y:y + h, x:x + w]
        s = np.array(self.im).astype(float)
        hh = np.array(self.arena.hud)[y:y + h, x:x + w].astype(float)
        s[m, :3] = s[m, :3] * (1 - alpha) + hh[m, :3] * alpha
        self.im = Image.fromarray(s.astype(np.uint8), 'RGBA')

    def result(self):
        return self.im


# ------------------------------------------------------------------ the pillar row (addendum 3 A.1), a STAND-IN
# The row's own art is another pass's (liam_row_pillar_*); for context only, its 16 neighbours are drawn here as the
# approved pillar cut down to the row's 34-texel stand, without runes: centres 960 +- 108 k (k 1..8) on floor line 348.
ROW_SPACING = 108
ROW_PER_SIDE = 8
ROW_STAND = 34
_row = {}


def row_neighbour(seed):
    if seed not in _row:
        import le_pillar as PL                      # read only
        R = C.R
        m = PL.silhouette()
        L = PL.paint_rock(m, seed=seed)
        PL.fissures(L, m)
        PL.moss(L, m, seed=seed)
        PL.keyline(L, m)
        body = L.copy()
        body[PL.BASE_Y - 1:, :] = '.'
        sunk = R.shift(body, 0, 50 - ROW_STAND)
        sunk[PL.BASE_Y:, :] = '.'
        out = PL.blank()
        R.composite(out, sunk)
        PL.rubble(out, seed)
        _row[seed] = up(img(PL.clip(out)))
    return _row[seed]


def draw_row(shot):
    for k in range(1, ROW_PER_SIDE + 1):
        for side in (-1, 1):
            x = PERCH[0] + side * ROW_SPACING * k
            shot.paste(row_neighbour(7 + (k * 3 + (side > 0)) % 5), (x - 32 * S, PERCH[1] - 72 * S))


# ------------------------------------------------------------------ placing each piece (LiamArtLayout's numbers)
def liam_on_pillar(shot, pillar_big, liam_big, row=False):
    if row:
        draw_row(shot)
    shot.paste(pillar_big, (PERCH[0] - 32 * S, PERCH[1] - 72 * S))
    shot.paste(liam_big, (LIAM_FEET[0] - 48 * S, LIAM_FEET[1] - 96 * S))


def pose_point(texel):
    return (LIAM_FEET[0] + (texel[0] - 48) * S, LIAM_FEET[1] + (texel[1] - 96) * S)


def band_left(body_small, crest_small, front_y, height_px=360):
    """The left wave's art as LiamWave._build_final lays it: whole tiles from the seam end, the rest at the rope end.
    Returns (image, top-left screen position)."""
    width = WAVE_LEFT_X[1] - WAVE_LEFT_X[0]
    tex_w = int(round(width / S))
    out = Image.new('RGBA', (tex_w, 120), (0, 0, 0, 0))
    covered = 0
    while covered < tex_w:
        texels = min(94, tex_w - covered)
        fx = 94 - texels
        x = tex_w - covered - texels
        out.alpha_composite(body_small.crop((fx, 0, 94, 80)), (x, 0))
        out.alpha_composite(crest_small.crop((fx, 0, 94, 40)), (x, 80))
        covered += texels
    big = up(out)
    return big, (WAVE_LEFT_X[1] - big.width, front_y - height_px)


def band_right(body_small, crest_small, front_y, height_px=360):
    big, _ = band_left(body_small, crest_small, front_y, height_px)
    return big.transpose(Image.FLIP_LEFT_RIGHT), (WAVE_RIGHT_X[0], front_y - height_px)


def ice_circle(radius):
    def m(xs, ys):
        return (xs - PERCH[0]) ** 2 + (ys - PERCH[1]) ** 2 <= radius * radius
    return m


def frost_positions(radius, spacing=48.0):
    """LiamFlood._place_frost: every FROST_SPACING px round the growing edge, only over the flood."""
    count = max(int(math.ceil(2 * math.pi * radius / spacing)), 1)
    rx, ry, rw, rh = ROPES
    out = []
    for i in range(count):
        a = 2 * math.pi * i / count
        x, y = PERCH[0] + math.cos(a) * radius, PERCH[1] + math.sin(a) * radius
        if rx <= x < rx + rw and ry <= y < ry + rh:
            out.append((round(x), round(y)))
    return out


def crack_segments(block_rect, reach_px):
    """LiamTremorBlock._step_crack: 16x8 segments (48 px) from the pillar's foot toward the block's nearest point,
    each shown once the crack's head has passed its start. Returns [(position, angle_deg)]."""
    bx, by, bw, bh = block_rect
    px, py = PERCH
    tx = min(max(px, bx), bx + bw)
    ty = min(max(py, by), by + bh)
    d = math.hypot(tx - px, ty - py)
    if d < 1:
        return []
    ux, uy = (tx - px) / d, (ty - py) / d
    length = 16 * S
    n = int(math.ceil(d / length))
    out = []
    for i in range(n):
        if length * i < min(reach_px, d):
            out.append(((round(px + ux * length * i), round(py + uy * length * i)), math.degrees(math.atan2(uy, ux))))
    return out


def paste_crack(shot, seg_small, pos, angle):
    """A crack segment rotated about its pivot (0, 4) onto pos."""
    big = up(seg_small)                           # 48 x 24, pivot at (0, 12)
    pad = Image.new('RGBA', (160, 160), (0, 0, 0, 0))
    pad.alpha_composite(big, (80, 80 - 12))
    rot = pad.rotate(-angle, resample=Image.NEAREST, center=(80, 80))
    shot.paste(rot, (pos[0] - 80, pos[1] - 80))
