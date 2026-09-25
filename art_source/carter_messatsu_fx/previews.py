"""Previews for the MESSATSU effects: the approval still, a dark-phase still,
a parry-burst legibility check, zoomed contact sheets and GIFs.

    python previews.py <sheet_dir> <output_dir>

Everything is composited for real, the way the scene draws it: the arena from
ArenaScene's own node transforms, the beam, head and surges painted on the
floor layer UNDER the fighters, Carter and the player over them, and the ball,
eyes, lock and flare as light on the clone layer OVER everything.  A preview
that pastes opaque pixels would answer none of the questions these exist to
answer (does the violet survive the mat, does the burst read on the core, does
the flare bury him).

Composed at the game's 1920x1080 and taken down to 1280x720 by nearest
neighbour, which is what the canvas_items stretch does to a 3x sprite: 2/3 of a
3 px texel is exactly 2 px, so nothing is lost or smeared.
"""
import math
import os
import sys

import numpy as np
from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.abspath(os.path.join(_HERE, '..', '..'))
sys.path.insert(0, _HERE)
import beam as B                      # noqa: E402  (pivots and the beam's start)


def A(*parts):
    return os.path.join(PROJ, 'Assets', *parts)


def load(path):
    return np.asarray(Image.open(path).convert('RGBA'), dtype=np.float32)


def frame(sheet, i, fw):
    return sheet[:, i * fw:(i + 1) * fw]


# ------------------------------------------------------------- compositing

def blit(dst, src, x, y, mode='mix', alpha=1.0, scale=1, flip=False):
    """axis-aligned sprite, top-left at (x, y), integer scale"""
    if flip:
        src = src[:, ::-1]
    if scale != 1:
        src = src.repeat(scale, 0).repeat(scale, 1)
    H, W = dst.shape[:2]
    h, w = src.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x0 >= x1 or y0 >= y1:
        return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]
    d = dst[y0:y1, x0:x1]
    a = s[..., 3:4] / 255.0 * alpha
    if mode == 'add':
        d[..., :3] = np.minimum(255.0, d[..., :3] + s[..., :3] * a)
    else:
        d[..., :3] = s[..., :3] * a + d[..., :3] * (1.0 - a)


def blit_rot(dst, tex, origin, angle, scale, pivot, mode='mix', alpha=1.0):
    """a Sprite2D: `pivot` texel on `origin`, rotated by `angle`, sampled
    nearest at each pixel centre - what the GPU does with a filter-less 2D
    texture"""
    H, W = dst.shape[:2]
    th, tw = tex.shape[:2]
    c, s = math.cos(angle), math.sin(angle)
    # bounding box of the transformed texture
    corners = []
    for u, v in ((0, 0), (tw, 0), (0, th), (tw, th)):
        lx, ly = (u - pivot[0]) * scale, (v - pivot[1]) * scale
        corners.append((origin[0] + c * lx - s * ly, origin[1] + s * lx + c * ly))
    xs = [p[0] for p in corners]
    ys = [p[1] for p in corners]
    x0, x1 = max(0, int(min(xs)) - 1), min(W, int(max(xs)) + 2)
    y0, y1 = max(0, int(min(ys)) - 1), min(H, int(max(ys)) + 2)
    if x0 >= x1 or y0 >= y1:
        return
    gy, gx = np.mgrid[y0:y1, x0:x1].astype(np.float64)
    wx, wy = gx + 0.5 - origin[0], gy + 0.5 - origin[1]
    lx = c * wx + s * wy
    ly = -s * wx + c * wy
    u = np.floor(lx / scale + pivot[0]).astype(int)
    v = np.floor(ly / scale + pivot[1]).astype(int)
    ok = (u >= 0) & (u < tw) & (v >= 0) & (v < th)
    samp = np.zeros((y1 - y0, x1 - x0, 4), np.float32)
    samp[ok] = tex[v[ok], u[ok]]
    d = dst[y0:y1, x0:x1]
    a = samp[..., 3:4] / 255.0 * alpha
    if mode == 'add':
        d[..., :3] = np.minimum(255.0, d[..., :3] + samp[..., :3] * a)
    else:
        d[..., :3] = samp[..., :3] * a + d[..., :3] * (1.0 - a)


def line(dst, p0, p1, width, color, alpha):
    """a Line2D: a flat quad `width` px across from p0 to p1"""
    H, W = dst.shape[:2]
    x0 = max(0, int(min(p0[0], p1[0]) - width))
    x1 = min(W, int(max(p0[0], p1[0]) + width) + 1)
    y0 = max(0, int(min(p0[1], p1[1]) - width))
    y1 = min(H, int(max(p0[1], p1[1]) + width) + 1)
    gy, gx = np.mgrid[y0:y1, x0:x1].astype(np.float64)
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    rx, ry = gx + 0.5 - p0[0], gy + 0.5 - p0[1]
    along = rx * ux + ry * uy
    across = np.abs(-rx * uy + ry * ux)
    m = (along >= 0) & (along <= L) & (across <= width / 2.0)
    d = dst[y0:y1, x0:x1]
    col = np.array(color[:3], np.float32)
    d[m, :3] = col * alpha + d[m, :3] * (1.0 - alpha)


def to_720(img):
    """nearest 2/3 downscale: pixel j samples floor(1.5 j + 0.75)"""
    ys = np.floor(np.arange(720) * 1.5 + 0.75).astype(int)
    xs = np.floor(np.arange(1280) * 1.5 + 0.75).astype(int)
    return img[ys][:, xs]


def save(img, path):
    Image.fromarray(np.clip(img[..., :3], 0, 255).astype(np.uint8)).save(path)
    print('  ', os.path.basename(path), img.shape[1], 'x', img.shape[0])


# ------------------------------------------------------------------ arena

def arena():
    """ArenaScene's own layers: black, ringside, crowd, mat, ropes, posts"""
    img = np.zeros((1080, 1920, 4), np.float32)
    img[..., 3] = 255
    blit(img, load(A('Environment', 'arena_ringside.png')), 0, 0, scale=3)
    crowd = load(A('Environment', 'crowd_v2.png'))
    cf = crowd[:, 0:640]                                   # hframes 5
    blit(img, cf, 960 - 960, 60 - 60, scale=3)
    blit(img, load(A('Environment', 'arena_mat.png')), 111, 114, scale=3)

    rope = Image.open(A('Environment', 'boundaries.png')).convert('RGBA')
    pole = Image.open(A('Environment', 'pole.png')).convert('RGBA')

    def sprite(im, pos, sc, region=None, rot=False, fh=False, fv=False):
        if region:
            im = im.crop((int(region[0]), 0, int(region[0] + region[2]), 32))
        w = max(1, int(round(im.width * sc[0])))
        h = max(1, int(round(im.height * sc[1])))
        im = im.resize((w, h), Image.NEAREST)
        if fh:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        if fv:
            im = im.transpose(Image.FLIP_TOP_BOTTOM)
        if rot:
            im = im.transpose(Image.ROTATE_270)
        a = np.asarray(im, dtype=np.float32)
        blit(img, a, int(round(pos[0] - a.shape[1] / 2)), int(round(pos[1] - a.shape[0] / 2)))

    k = (7.783335, 6.9375)
    sprite(rope, (960 - 608, 100 + 14), k, (0, 0, 128.47955, 32))
    sprite(rope, (960 + 667.5, 100 + 14), k, (156.22682, 0, 143.77318, 32))
    sprite(rope, (100 - 8, 540 + 31.4), (3.9833364, 6.9375), rot=True)
    sprite(rope, (1820 - 15, 540 + 27.5), (3.9273026, 6.9375), rot=True)
    sprite(rope, (960 - 609.25, 980 + 8), k, (0, 0, 128.80088, 32))
    sprite(rope, (960 + 666.25, 980 + 8), k, (156.54815, 0, 143.45185, 32))
    sprite(pole, (960 - 855, 107), (1.5859377, 2.03125))
    sprite(pole, (960 + 847, 109), (1.5859377, 2.03125), fh=True)
    sprite(pole, (960 - 847, 964), (1.5859377, 1.1875007), fv=True)
    sprite(pole, (960 + 846, 965), (1.5859377, 1.1875007), fh=True, fv=True)
    return img


# ----------------------------------------------------------------- actors

def carter_frame():
    """carter_rush.png frame 3, the placeholder fire pose"""
    return frame(load(A('Characters', 'Carter', 'carter_rush.png')), 3, 96)


def local(tx, ty, flipped):
    """CarterArtLayout.local: px from his feet of texel (tx, ty)"""
    col = (95 - tx) if flipped else tx
    return ((col - 48) * 3.0, (ty - 95) * 3.0)


def draw_carter(img, feet, flipped, alpha=1.0, with_aura=True):
    fx, fy = feet
    if with_aura:
        aura = frame(load(A('Characters', 'Carter', 'carter_aura.png')), 0, 96)
        blit(img, aura, int(fx - 144), int(fy - 285), alpha=0.75 * alpha, scale=3, flip=flipped)
    blit(img, carter_frame(), int(fx - 144), int(fy - 285), alpha=alpha, scale=3, flip=flipped)


def draw_player(img, pos, fi=30):
    sheet = load(A('Characters', 'MainPlayer', 'player_4dir_sheet.png'))
    col, row = fi % 10, fi // 10
    fr = sheet[row * 32:(row + 1) * 32, col * 32:(col + 1) * 32]
    blit(img, fr, int(pos[0] - 48), int(pos[1] - 48), scale=3)


# ------------------------------------------------------------------- beam

def beam_texture(beam_sheet, f, length_px, start_px=0.0):
    """the tile repeated out to the beam's reach, as a region-repeat sprite
    would draw it.  Its texture column is its distance from his palms in
    texels (region_rect.position.x = start), so the flare's fanned pattern
    flows straight on into it."""
    tile = frame(beam_sheet, f, 32)
    s0 = int(round(start_px / 3.0))
    n = int(math.ceil(length_px / 3.0 / 32.0)) + 2
    long = np.concatenate([tile] * n, axis=1)
    return long[:, s0:int(length_px / 3.0)]


# ------------------------------------------------------------------ scenes

class Scene:
    """Carter on the right, firing down-left at 22.5 degrees, the player in
    the band.  Numbers are game px."""
    FEET = (1545.0, 610.0)
    FLIP = True                                   # facing left
    MUZZLE_TEXEL = (84, 66)                        # the front of his fist, rush frame 3
    ANGLE = math.radians(180.0 - 22.5)
    PLAYER_ALONG, PLAYER_ACROSS = 820.0, 40.0
    SURGE_ALONG = 480.0

    def __init__(self):
        lx, ly = local(*self.MUZZLE_TEXEL, self.FLIP)
        self.muzzle = (self.FEET[0] + lx + 1.5, self.FEET[1] + ly + 1.5)
        self.dir = (math.cos(self.ANGLE), math.sin(self.ANGLE))
        self.n = (-self.dir[1], self.dir[0])

    def along(self, a, across=0.0):
        return (self.muzzle[0] + self.dir[0] * a + self.n[0] * across,
                self.muzzle[1] + self.dir[1] * a + self.n[1] * across)


BEAM_START_PX = B.BEAM_START * 3.0


def lit_scene(sheets, f, surge_along=None, reach=None, ball=True, head_f=None):
    """the lights-on beam.  Floor layer (under the fighters, drawn in the order
    it is added): the beam body from BEAM_START, the flare over its start, the
    head on its reach while it travels, the surges.  Then the fighters, then
    the ball as light on the clone layer."""
    sc = Scene()
    img = arena()
    length = 2240.0 if reach is None else reach
    if length > BEAM_START_PX:
        tex = beam_texture(sheets['beam'], f, length, start_px=BEAM_START_PX)
        blit_rot(img, tex, sc.along(BEAM_START_PX), sc.ANGLE, 3.0, (0, 68))
    blit_rot(img, frame(sheets['flare'], f % 4, 64), sc.muzzle, sc.ANGLE, 3.0, B.FLARE_PIVOT)
    if reach is not None:
        blit_rot(img, frame(sheets['head'], f % 3 if head_f is None else head_f, 24),
                 sc.along(reach), sc.ANGLE, 3.0, B.HEAD_PIVOT)
    if surge_along is not None:
        blit_rot(img, frame(sheets['pulse'], f % 3, 20), sc.along(surge_along),
                 sc.ANGLE, 3.0, B.PULSE_PIVOT)
    # fighters, y-sorted: the player is lower on screen, so drawn after him
    draw_carter(img, sc.FEET, sc.FLIP)
    ppos = sc.along(sc.PLAYER_ALONG, -sc.PLAYER_ACROSS)
    draw_player(img, (ppos[0], ppos[1] - 1.5))
    if ball:
        b = frame(sheets['ball'], 3, 32)
        blit(img, b, int(round(sc.muzzle[0] - 48)), int(round(sc.muzzle[1] - 48)),
             mode='add', scale=3)
    return img


def approval(sheets, out, f=1):
    img = lit_scene(sheets, f, surge_along=Scene.SURGE_ALONG)
    save(to_720(img), os.path.join(out, 'approval.png'))
    save(img, os.path.join(out, 'approval_1080.png'))
    return img


def travel(sheets, out, f=0):
    """0.05 s after the fire: the head halfway to the player"""
    img = lit_scene(sheets, f, reach=Scene.PLAYER_ALONG * 0.5, ball=False)
    save(to_720(img), os.path.join(out, 'travel.png'))


def dark_charge(sheets, out, f=2, lock_f=4):
    """mid-charge in the dark: curtain down, his body at ~7%, eyes, ball,
    aim line and lock on the lifted player"""
    sc = Scene()
    img = arena()
    draw_carter(img, sc.FEET, sc.FLIP, with_aura=False)
    dark = load(A('Characters', 'Carter', 'Demon', 'demon_darkness.png'))
    blit(img, dark, 0, 0, scale=3)
    ppos = sc.along(sc.PLAYER_ALONG, -sc.PLAYER_ACROSS)
    draw_player(img, (ppos[0], ppos[1] - 1.5))
    # clone layer
    line(img, sc.muzzle, ppos, 6.0, (0.72 * 255, 0.4 * 255, 255), 0.55)
    lock = frame(sheets['lock'], lock_f, 32)
    k = 1.0 + 0.8 * (1.0 - (lock_f + 0.5) / 6.0)          # the code's squeeze
    blit_rot(img, lock, ppos, 0.0, 3.0 * k, (16, 16), mode='add')
    ball = frame(sheets['ball'], f, 32)
    g = 0.3 + 0.7 * (lock_f + 0.5) / 6.0
    blit_rot(img, ball, sc.muzzle, 0.0, 3.0 * g, (16, 16), mode='add')
    ex, ey = local(52, 40, sc.FLIP)                          # between his eyes
    eyes = frame(sheets['eyes'], 0, 16)
    blit(img, eyes[:, ::-1] if sc.FLIP else eyes,
         int(round(sc.FEET[0] + ex - 24)), int(round(sc.FEET[1] + ey - 12 + 1.5)),
         mode='add', scale=3)
    save(to_720(img), os.path.join(out, 'dark_charge.png'))
    return img


def burst_check(sheets, out):
    """the parry break at its peak frame, dropped on the core, the body and
    the edge of the beam - the placeholder's white core swallowed it"""
    brk = load(A('Characters', 'Carter', 'Demon', 'demon_parry_break.png'))
    mat = load(A('Environment', 'arena_mat.png'))
    rows = []
    for bf in (0, 1, 2):
        W, H = 1200, 460
        img = np.zeros((H, W, 4), np.float32)
        img[..., 3] = 255
        blit(img, mat[40:200, 20:430], 0, 0, scale=3)
        tex = beam_texture(sheets['beam'], 1, W + 10)
        blit(img, tex, 0, 26, scale=3)
        b = frame(brk, bf, 96)
        for cx, cy in ((180, 230), (600, 230 - 96), (1020, 230 - 162)):
            blit(img, b, cx - 144, cy - 144, mode='add', scale=3)
        rows.append(img)
    img = np.concatenate(rows, 0)
    save(img, os.path.join(out, 'burst_check.png'))


def contact(sheets, out):
    """every sheet at 6x on the arena's darkness colour, frames in a row"""
    order = ['ball', 'eyes', 'lock', 'beam', 'flare', 'head', 'pulse']
    fws = {'ball': 32, 'eyes': 16, 'lock': 32, 'beam': 32, 'flare': 64,
           'head': 24, 'pulse': 20}
    z = 4
    gap = 12
    blocks = []
    for name in order:
        s = sheets[name]
        h, w = s.shape[:2]
        n = w // fws[name]
        zz = z * (3 if name == 'eyes' else 1)
        bw = n * (fws[name] * zz + gap) + gap
        bh = h * zz + 2 * gap
        blk = np.zeros((bh, bw, 4), np.float32)
        blk[..., :3] = (23, 23, 24)
        blk[..., 3] = 255
        for i in range(n):
            blit(blk, frame(s, i, fws[name]), gap + i * (fws[name] * zz + gap), gap,
                 mode='add', scale=zz)
        blocks.append(blk)
    W = max(b.shape[1] for b in blocks)
    H = sum(b.shape[0] for b in blocks)
    img = np.zeros((H, W, 4), np.float32)
    img[..., :3] = 10
    img[..., 3] = 255
    y = 0
    for b in blocks:
        img[y:y + b.shape[0], :b.shape[1]] = b
        y += b.shape[0]
    save(img, os.path.join(out, 'contact_x4.png'))


def _gif(frames, path, ms):
    ims = [Image.fromarray(np.clip(f[..., :3], 0, 255).astype(np.uint8)) for f in frames]
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=ms, loop=0,
                optimize=False, disposal=1)
    print('  ', os.path.basename(path), len(ims), 'frames')


def anim_charge(sheets, out, fps=30):
    """the 1.2 s charge in the dark, the way CarterMessatsu._draw_charge drives
    it: the ball grown 0.3 -> 1.0, the lock frame picked by progress and
    squeezed 1.8 -> 1.0, the aim line flickering every 0.05 s"""
    sc = Scene()
    base = arena()
    draw_carter(base, sc.FEET, sc.FLIP, with_aura=False)
    blit(base, load(A('Characters', 'Carter', 'Demon', 'demon_darkness.png')), 0, 0, scale=3)
    ppos = sc.along(sc.PLAYER_ALONG, -sc.PLAYER_ACROSS)
    draw_player(base, (ppos[0], ppos[1] - 1.5))
    ex, ey = local(52, 40, sc.FLIP)
    frames = []
    n = int(1.2 * fps)
    for i in range(n):
        t = i / float(fps)
        g = t / 1.2
        img = base.copy()
        dim = int(t / 0.05) % 2 == 1
        line(img, sc.muzzle, ppos, 6.0, (0.72 * 255, 0.4 * 255, 255), 0.3 if dim else 0.55)
        lf = min(5, int(g * 6))
        blit_rot(img, frame(sheets['lock'], lf, 32), ppos, 0.0, 3.0 * (1.8 - 0.8 * g),
                 (16, 16), mode='add')
        bf = int(t / 0.06) % 6
        blit_rot(img, frame(sheets['ball'], bf, 32), sc.muzzle, 0.0, 3.0 * (0.3 + 0.7 * g),
                 (16, 16), mode='add')
        ef = 1 if (t % 0.42) >= 0.36 else 0
        eyes = frame(sheets['eyes'], ef, 16)
        blit(img, eyes[:, ::-1] if sc.FLIP else eyes,
             int(round(sc.FEET[0] + ex - 24)), int(round(sc.FEET[1] + ey - 12 + 1.5)),
             mode='add', scale=3)
        frames.append(to_720(img))
    _gif(frames, os.path.join(out, 'anim_charge.gif'), int(1000 / fps))


def anim_fire(sheets, out, fps=30):
    """the fire: the head crossing in messatsu_travel (0.10 s), the beam
    flowing, surge 1 leaving his palms at 0.30 s and landing at 0.60 s, and a
    parry break on the player as it lands"""
    sc = Scene()
    brk = load(A('Characters', 'Carter', 'Demon', 'demon_parry_break.png'))
    brk_times = [0.04, 0.04, 0.033, 0.033, 0.033, 0.066]
    D = sc.PLAYER_ALONG
    ppos = sc.along(sc.PLAYER_ALONG, -sc.PLAYER_ACROSS)
    frames = []
    for i in range(int(0.95 * fps)):
        t = i / float(fps)
        f = int(t / 0.05) % 4
        reach = None if t >= 0.1 - 1e-6 else max(1.0, D * t / 0.1)
        surge = None
        if 0.3 <= t < 0.6:
            surge = D * (1.0 - (0.6 - t) / 0.3)
        img = lit_scene(sheets, f, surge_along=surge, reach=reach, ball=False,
                        head_f=int(t / 0.034) % 3)
        if t >= 0.6:
            k, acc = 0, 0.6
            while k < 5 and t >= acc + brk_times[k]:
                acc += brk_times[k]
                k += 1
            if t < 0.6 + sum(brk_times):
                blit(img, frame(brk, k, 96), int(ppos[0] - 144), int(ppos[1] - 144),
                     mode='add', scale=3)
        frames.append(to_720(img))
    _gif(frames, os.path.join(out, 'anim_fire.gif'), int(1000 / fps))


def main(sheet_dir, out):
    if not os.path.isdir(out):
        os.makedirs(out)
    names = ['ball', 'eyes', 'lock', 'beam', 'flare', 'head', 'pulse']
    sheets = {n: load(os.path.join(sheet_dir, 'messatsu_%s.png' % n)) for n in names}
    approval(sheets, out)
    travel(sheets, out)
    dark_charge(sheets, out)
    burst_check(sheets, out)
    contact(sheets, out)
    if '--gifs' in sys.argv:
        anim_charge(sheets, out)
        anim_fire(sheets, out)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
