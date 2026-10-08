"""Mocks of the new beam on a real capture of the dark maze (mb_capture.gd's frames and frames.json).

The art goes on each captured frame through that frame's own canvas transform (the god fight's 2/3
view and any shake the game was playing), at the game's scale: a texel is 3 world px, 2 screen px.
The body and the dissipation are laid the way a Line2D lays a tiled texture: one tile every 288
world px from the line's first point, the texture's top row on the line's left (so it turns upside
down on runs going left), the joints mitred. Glows add. The new beat's timing is TIMELINE; the
background frames are re-timed to it, beat by beat, from the capture's own beats.

Pure functions: nothing here writes a file.
"""
import json
import math
import os

import numpy as np
from PIL import Image

TEX = 3.0          # world px a texel
SC = 2.0 / 3.0     # the god fight's view: world px to screen px

# The new beat, seconds. The coder's hit-stop is mocked as a freeze of HITSTOP on the impact's
# first frame; the coder's flash as a white wash over FLASH_TIME.
TIMELINE = {
    'pre': 0.50,
    'charge': 0.72,
    'stage_times': (0.24, 0.24, 0.24),
    'charge_frame': 0.04,
    'release_frame': 0.03,
    'trace': 0.18,
    'hitstop': 0.067,
    'hold': 0.30,
    'body_frame': 0.04,
    'head_frame': 0.03,
    'corner_frame': 0.03,
    'impact_frame': 0.04,
    'ring_frame': 0.035,
    'dissipate': 0.40,
    'diss_frame': 0.05,
    'lights': 0.40,
    'tail': 0.35,
    'flash_time': 0.05,
    'flash_alpha': 0.45,
    'scorch_times': (0.0, 0.15, 0.35, 0.60),
}
FPS = 50


# ----------------------------------------------------------------------------------------------- capture

class Capture:
    def __init__(self, folder):
        self.folder = folder
        with open(os.path.join(folder, 'frames.json'), encoding='utf-8') as fh:
            self.meta = json.load(fh)
        self.frames = self.meta['frames']
        self.route = None
        for e in self.frames:
            if 'route' in e:
                self.route = [tuple(p) for p in e['route']]
        self.beats = {}
        for e in self.frames:
            self.beats.setdefault(e['beat'], []).append(e['i'])
        self._cache = {}
        charge = self.beats['CHARGE']
        self.charge0 = charge[0]
        self.spirit_muzzle = tuple(self.frames[charge[0]]['muzzle'])
        self.throw_muzzle = tuple(self.frames[self.beats['TRACE'][0]]['muzzle'])
        self.player = tuple(self.frames[charge[0]]['player'])
        self.soles_over_origin = self.meta['soles_over_origin']
        self.beam_height = self.meta['beam_height']

    def image(self, i):
        if i not in self._cache:
            im = Image.open(os.path.join(self.folder, 'f%04d.png' % i)).convert('RGB')
            self._cache[i] = np.array(im).astype(np.int16)
        return self._cache[i].copy()

    def xf(self, i):
        c = self.frames[i]['canvas']
        return (c[0], c[4], c[5])          # scale, origin x, origin y

    def pick(self, beat, share, stretch_from=0, count=None):
        """The captured frame `share` (0-1) of the way through `beat` (optionally its first `count`)."""
        idx = self.beats[beat]
        if count is not None:
            idx = idx[:count]
        k = min(len(idx) - 1, int(share * len(idx)))
        return idx[k]


# ----------------------------------------------------------------------------------------------- sprites

def to_rgba_2x(img):
    """An art frame (PIL RGBA, 1 texel a px) at screen scale: 2 px a texel."""
    return np.array(img.resize((img.width * 2, img.height * 2), Image.NEAREST)).astype(np.int16)


def world_to_screen(p, xf):
    s, ox, oy = xf
    return (p[0] * s + ox, p[1] * s + oy)


def blit(canvas, spr, x0, y0, additive=False, alpha=1.0):
    """Draw spr (h, w, 4 int16) with its top-left at (x0, y0) on canvas (H, W, 3 int16)."""
    H, W = canvas.shape[:2]
    h, w = spr.shape[:2]
    x0, y0 = int(round(x0)), int(round(y0))
    xa, ya = max(0, x0), max(0, y0)
    xb, yb = min(W, x0 + w), min(H, y0 + h)
    if xa >= xb or ya >= yb:
        return
    sub = spr[ya - y0:yb - y0, xa - x0:xb - x0]
    dst = canvas[ya:yb, xa:xb]
    m = sub[..., 3] > 0
    if additive:
        dst[m] = np.minimum(255, dst[m] + (sub[..., :3][m] * alpha).astype(np.int16))
    elif alpha >= 1.0:
        dst[m] = sub[..., :3][m]
    else:
        dst[m] = (dst[m] * (1 - alpha) + sub[..., :3][m] * alpha).astype(np.int16)


def place(canvas, img, pivot, at_screen, rot=0.0, flip_h=False, flip_v=False, additive=False, alpha=1.0):
    """A sprite (PIL RGBA at 1 texel a px) with its pivot texel on a screen point, rotated `rot`
    radians clockwise (Godot's sense) after flipping, the way a Sprite2D would draw it."""
    im = img
    px, py = pivot
    if flip_h:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
        px = img.width - px
    if flip_v:
        im = im.transpose(Image.FLIP_TOP_BOTTOM)
        py = img.height - py
    im2 = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
    px2, py2 = px * 2, py * 2
    if abs(rot) > 1e-6:
        # pad so the pivot is the centre, then rotate about it
        R = int(math.ceil(math.hypot(max(px2, im2.width - px2), max(py2, im2.height - py2)))) + 2
        pad = Image.new('RGBA', (2 * R, 2 * R), (0, 0, 0, 0))
        pad.paste(im2, (int(R - px2), int(R - py2)))
        q = round(math.degrees(rot) / 90.0)
        if abs(math.degrees(rot) - 90 * q) < 0.01:
            arr = np.array(pad)
            arr = np.rot90(arr, k=-q % 4)       # clockwise on screen
            pad = Image.fromarray(np.ascontiguousarray(arr))
        else:
            pad = pad.rotate(-math.degrees(rot), resample=Image.NEAREST)
        im2, px2, py2 = pad, R, R
    spr = np.array(im2).astype(np.int16)
    blit(canvas, spr, at_screen[0] - px2, at_screen[1] - py2, additive, alpha)


# ----------------------------------------------------------------------------------------------- line

def route_lengths(route):
    along = [0.0]
    for a, b in zip(route, route[1:]):
        along.append(along[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    return along


def partial_route(route, reach):
    """The route cut `reach` world px along."""
    along = route_lengths(route)
    pts = [route[0]]
    for i in range(1, len(route)):
        if along[i] <= reach:
            pts.append(route[i])
            continue
        span = along[i] - along[i - 1]
        w = (reach - along[i - 1]) / span if span > 0 else 1.0
        a, b = route[i - 1], route[i]
        pts.append((a[0] + (b[0] - a[0]) * w, a[1] + (b[1] - a[1]) * w))
        break
    if len(pts) < 2:
        pts.append(pts[0])
    return pts


def draw_line(canvas, pts, tex, tex_w, tex_h, xf, additive=False, alpha=1.0):
    """Lay `tex` (RGBA numpy, tex_h x tex_w texels) along the world polyline pts as a Line2D in
    LINE_TEXTURE_TILE mode with sharp joints: width tex_h * 3 world px, a tile every tex_w * 3."""
    s, ox, oy = xf
    H, W = canvas.shape[:2]
    half = tex_h * TEX / 2.0
    along = route_lengths(pts)
    n = len(pts)
    segs = []
    for i in range(n - 1):
        a, b = np.array(pts[i], float), np.array(pts[i + 1], float)
        L = np.linalg.norm(b - a)
        if L < 1e-6:
            continue
        d = (b - a) / L
        up = np.array([d[1], -d[0]])            # Godot: forward.orthogonal(), the texture's top row
        segs.append((i, a, b, d, up, L))
    for k, (i, a, b, d, up, L) in enumerate(segs):
        prev = segs[k - 1] if k > 0 else None
        nxt = segs[k + 1] if k + 1 < len(segs) else None
        corners = [a + up * half * 1.5, a - up * half * 1.5, b + up * half * 1.5, b - up * half * 1.5]
        if prev is not None:
            corners += [a - d * half * 1.5]
        if nxt is not None:
            corners += [b + d * half * 1.5]
        xs = [c[0] * s + ox for c in corners]
        ys = [c[1] * s + oy for c in corners]
        x0, x1 = max(0, int(math.floor(min(xs))) - 2), min(W, int(math.ceil(max(xs))) + 2)
        y0, y1 = max(0, int(math.floor(min(ys))) - 2), min(H, int(math.ceil(max(ys))) + 2)
        if x0 >= x1 or y0 >= y1:
            continue
        gy, gx = np.mgrid[y0:y1, x0:x1]
        wx = (gx + 0.5 - ox) / s
        wy = (gy + 0.5 - oy) / s
        rx, ry = wx - a[0], wy - a[1]
        along_i = rx * d[0] + ry * d[1]
        across = rx * up[0] + ry * up[1]
        inside = np.abs(across) < half
        if prev is not None:
            m = d + prev[3]
            inside &= (wx - a[0]) * m[0] + (wy - a[1]) * m[1] >= 0
        else:
            inside &= along_i >= 0
        if nxt is not None:
            m = d + nxt[3]
            inside &= (wx - b[0]) * m[0] + (wy - b[1]) * m[1] < 0
        else:
            inside &= along_i <= L
        if not inside.any():
            continue
        u = (along[i] + along_i) / TEX
        tx = np.floor(np.mod(u, tex_w)).astype(int)
        ty = np.floor(tex_h / 2.0 - across / TEX).astype(int)
        ok = inside & (ty >= 0) & (ty < tex_h)
        if not ok.any():
            continue
        px = tex[ty[ok], tx[ok]]
        vis = px[:, 3] > 0
        yy, xx = gy[ok][vis], gx[ok][vis]
        col = px[vis][:, :3]
        if additive:
            canvas[yy, xx] = np.minimum(255, canvas[yy, xx] + (col * alpha).astype(np.int16))
        elif alpha >= 1.0:
            canvas[yy, xx] = col
        else:
            canvas[yy, xx] = (canvas[yy, xx] * (1 - alpha) + col * alpha).astype(np.int16)


# ----------------------------------------------------------------------------------------------- the sequence

def _unit(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    return (dx / L, dy / L) if L else (1.0, 0.0)


def corners_of(route):
    """Every joint of the beam's line (not its ends): (point, incoming unit, outgoing unit)."""
    out = []
    for i in range(1, len(route) - 1):
        out.append((route[i], _unit(route[i - 1], route[i]), _unit(route[i], route[i + 1])))
    return out


def scorch_route(cap):
    """The floor line under the route: every point but the muzzle, dropped back to the soles."""
    lift = cap.beam_height
    return [(p[0], p[1] + lift) for p in cap.route[1:]]


class Sequence:
    """The whole beat on the capture, one output frame at a time."""

    def __init__(self, cap, art, tl=TIMELINE):
        self.cap = cap
        self.art = art
        self.tl = tl
        self.route = cap.route
        self.along = route_lengths(self.route)
        self.total = self.along[-1]
        t = 0.0
        self.t_charge = tl['pre']
        self.t_release = self.t_charge + tl['charge']
        self.t_hit = self.t_release + tl['trace']
        self.t_hold = self.t_hit + tl['hitstop']
        self.t_diss = self.t_hold + tl['hold']
        self.t_lights = self.t_diss + tl['dissipate']
        self.t_tail = self.t_lights + tl['lights']
        self.t_end = self.t_tail + tl['tail']
        self.corner_list = corners_of(self.route)
        self.corner_times = []
        for k, (p, din, dout) in enumerate(self.corner_list):
            self.corner_times.append(self.t_release + tl['trace'] * self.along[k + 1] / self.total)
        self.embers = self._spawn_particles()

    # which captured frame shows under time t
    def background(self, t):
        cap = self.cap
        if t < self.t_charge:
            back = self.t_charge - t
            return max(0, cap.charge0 - 1 - int(back * 60))
        if t < self.t_release:
            return cap.pick('CHARGE', (t - self.t_charge) / self.tl['charge'])
        if t < self.t_hit:
            k = int((t - self.t_release) * 60)
            return cap.beats['TRACE'][min(k, len(cap.beats['TRACE']) - 1)]
        if t < self.t_hold:
            return cap.beats['HOLD'][0]
        if t < self.t_diss:
            return cap.pick('HOLD', (t - self.t_hold) / self.tl['hold'])
        if t < self.t_lights:
            return cap.pick('FADE', (t - self.t_diss) / self.tl['dissipate'])
        if t < self.t_tail:
            return cap.pick('LIGHTS', (t - self.t_lights) / self.tl['lights'])
        return cap.pick('OFF', min(0.999, (t - self.t_tail) / self.tl['tail']))

    def _overlay_frame(self, t, bi):
        e = self.cap.frames[bi]
        anim, fr = e.get('greyson_anim'), e.get('greyson_frame')
        tl = self.tl
        if self.t_charge <= t < self.t_release and anim == 'spirit' and fr in (0, 1):
            ct = t - self.t_charge
            st = tl['stage_times']
            stage = 0 if ct < st[0] else 1 if ct < st[0] + st[1] else 2
            return (0 if fr == 0 else 3) + stage
        if self.t_release <= t < self.t_diss and anim == 'spirit_throw':
            return 6 + int((t - self.t_release) / 0.05) % 2
        return None

    def _spawn_particles(self):
        """Embers and smoke the code would emit along the line as it breaks up: rising up the screen,
        drifting, each playing its sheet once over its life."""
        rng = np.random.default_rng(4242)
        out = []
        reach = 0.0
        while reach < self.total:
            p = partial_route(self.route, reach)[-1]
            for k in range(2):
                out.append({'kind': 'ember', 'x': p[0] + rng.uniform(-30, 30), 'y': p[1] + rng.uniform(-30, 30),
                            'vx': rng.uniform(-40, 40), 'vy': -rng.uniform(90, 200),
                            'born': rng.uniform(0.0, 0.25), 'life': rng.uniform(0.30, 0.55)})
            if rng.random() < 0.55:
                out.append({'kind': 'smoke', 'x': p[0] + rng.uniform(-24, 24), 'y': p[1] + rng.uniform(-24, 24),
                            'vx': rng.uniform(-15, 15), 'vy': -rng.uniform(40, 80),
                            'born': rng.uniform(0.0, 0.2), 'life': rng.uniform(0.45, 0.7)})
            reach += 26.0
        return out

    def frame(self, t, flash=True):
        tl = self.tl
        art = self.art
        cap = self.cap
        bi = self.background(t)
        canvas = cap.image(bi)
        xf = cap.xf(bi)
        S = lambda p: world_to_screen(p, xf)
        route = self.route

        # Greyson's overlay: eyes and cannon blazing through the charge, the levelled muzzle glowing
        # while the beam pours out of it
        ov = self._overlay_frame(t, bi)
        if ov is not None and 'overlay' in art:
            e = cap.frames[bi]
            a, b_, c_, d_, tx, ty = e['greyson_sprite']
            rx, ry = e['greyson_rect'][0], e['greyson_rect'][1]
            wx, wy = a * rx + c_ * ry + tx, b_ * rx + d_ * ry + ty
            sx, sy = world_to_screen((wx, wy), xf)
            place(canvas, art['overlay'][ov], (0, 0), (sx, sy), flip_h=e.get('greyson_flip', False))

        # the charge at the raised muzzle
        if self.t_charge <= t < self.t_release:
            ct = t - self.t_charge
            st = tl['stage_times']
            stage = 0 if ct < st[0] else 1 if ct < st[0] + st[1] else 2
            k = int(ct / tl['charge_frame']) % 4
            f = stage * 4 + k
            place(canvas, art['charge_glow'][f], (40, 40), S(cap.spirit_muzzle), additive=True)
            place(canvas, art['charge'][f], (40, 40), S(cap.spirit_muzzle))

        # the beam: traced, held, then broken up
        if self.t_release <= t < self.t_lights:
            if t < self.t_hit:
                share = (t - self.t_release) / tl['trace']
                pts = partial_route(route, self.total * share)
            else:
                pts = route
            if t < self.t_diss:
                fb = int((min(t, self.t_hit) if self.t_hit <= t < self.t_hold else t) / tl['body_frame']) % len(art['body'])
                draw_line(canvas, pts, art['body_glow_np'][fb], art['tile_w'], art['glow_h'], xf, additive=True)
                draw_line(canvas, pts, art['body_np'][fb], art['tile_w'], art['tile_h'], xf)
            else:
                fd = min(len(art['diss']) - 1, int((t - self.t_diss) / tl['diss_frame']))
                draw_line(canvas, pts, art['diss_np'][fd], art['tile_w'], art['tile_h'], xf)

        # the scorch on the floor, from the break-up until the lights are up
        if self.t_diss <= t < self.t_end:
            st = t - self.t_diss
            fs = max(i for i, s0 in enumerate(tl['scorch_times']) if st >= s0)
            a = 1.0
            if t >= self.t_lights:
                a = max(0.0, 1.0 - (t - self.t_lights) / (tl['lights'] + tl['tail'] * 0.5))
            if a > 0:
                draw_line(canvas, scorch_route(cap), art['scorch_np'][fs], art['scorch_w'], art['scorch_h'], xf,
                          alpha=a)

        # corner bursts as the head passes each joint
        for (p, din, dout), tc in zip(self.corner_list, self.corner_times):
            if tc <= t:
                ft = t - tc
                if self.t_hit <= t < self.t_hold:
                    ft = min(ft, self.t_hit - tc)
                fc = int(ft / tl['corner_frame'])
                if fc < len(art['corner']):
                    outer = (din[0] - dout[0], din[1] - dout[1])
                    fh, fv = outer[0] < -1e-6, outer[1] > 1e-6
                    place(canvas, art['corner_glow'][fc], (32, 32), S(p), flip_h=fh, flip_v=fv, additive=True)
                    place(canvas, art['corner'][fc], (32, 32), S(p), flip_h=fh, flip_v=fv)

        # the head racing the line
        if self.t_release <= t < self.t_hit:
            share = (t - self.t_release) / tl['trace']
            pts = partial_route(route, self.total * share)
            end = pts[-1]
            d = _unit(pts[-2], pts[-1]) if len(pts) > 1 and pts[-2] != pts[-1] else _unit(route[0], route[1])
            ang = math.atan2(d[1], d[0])
            fv = math.cos(ang) < -1e-6
            fh = int((t - self.t_release) / tl['head_frame']) % len(art['head'])
            place(canvas, art['head_glow'][fh], art['attach'], S(end), rot=ang, flip_v=fv, additive=True)
            place(canvas, art['head'][fh], art['attach'], S(end), rot=ang, flip_v=fv)

        # the release burst on the thrown muzzle
        if self.t_release <= t < self.t_release + tl['release_frame'] * len(art['release']):
            fr = int((t - self.t_release) / tl['release_frame'])
            place(canvas, art['release_glow'][fr], (40, 40), S(cap.throw_muzzle), additive=True)
            place(canvas, art['release'][fr], (40, 40), S(cap.throw_muzzle))

        # the impact on the player, and its shockwave along the floor
        if t >= self.t_hit:
            it = 0.0 if t < self.t_hold else t - self.t_hold
            end = route[-1]
            soles = (end[0], end[1] + cap.beam_height)
            fr = int(it / tl['ring_frame'])
            if fr < len(art['ring']):
                place(canvas, art['ring'][fr], (64, 24), S(soles))
            fi = int(it / tl['impact_frame'])
            if fi < len(art['impact']):
                place(canvas, art['impact_glow'][fi], (56, 56), S(end), additive=True)
                place(canvas, art['impact'][fi], (56, 56), S(end))

        # embers and smoke rising off the line as it breaks up
        if t >= self.t_diss:
            pt = t - self.t_diss
            for e in self.embers:
                age = pt - e['born']
                if age < 0 or age >= e['life']:
                    continue
                x = e['x'] + e['vx'] * age
                y = e['y'] + e['vy'] * age
                sheet = art['ember'] if e['kind'] == 'ember' else art['smoke']
                k = min(len(sheet) - 1, int(age / e['life'] * len(sheet)))
                piv = (4, 4) if e['kind'] == 'ember' else (8, 8)
                place(canvas, sheet[k], piv, S((x, y)))

        # the coder's flash on the hit
        if flash and self.t_hit <= t < self.t_hit + tl['flash_time']:
            a = tl['flash_alpha']
            canvas[:] = (canvas * (1 - a) + 255 * a).astype(np.int16)
        return np.clip(canvas, 0, 255).astype(np.uint8)

    def times(self, fps=FPS, slow=1.0):
        n = int(math.ceil(self.t_end * fps * slow))
        return [i / (fps * slow) for i in range(n)]


# ----------------------------------------------------------------------------------------------- output

CROP = (560, 60, 1360, 1050)       # the action and its context: Jordan's body, both puppets, the maze


def to_gif_frames(rgb_frames):
    """RGB arrays to palette images for a GIF: each frame its own palette, no dithering, so the
    pixel art stays crisp."""
    out = []
    for fr in rgb_frames:
        im = Image.fromarray(fr, 'RGB')
        out.append(im.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
    return out


def sequence_frames(seq, fps=FPS, slow=1.0, t0=0.0, t1=None, crop=CROP):
    t1 = seq.t_end if t1 is None else t1
    frames = []
    n = int(math.ceil((t1 - t0) * fps * slow))
    for i in range(n):
        t = t0 + i / (fps * slow)
        frames.append(np.array(Image.fromarray(seq.frame(t)).crop(crop)))
    return frames


def before_frames(cap_show, seq, fps=FPS, crop=CROP):
    """Today's beam, from a capture that kept it, on the same clock: the same pre-roll before its
    charge, then everything at the game's own pace."""
    frames = []
    charge0 = cap_show.charge0
    pre = seq.tl['pre']
    last = len(cap_show.frames) - 1
    t = 0.0
    while True:
        i = int(round(charge0 + (t - pre) * 60))
        if i > last:
            break
        frames.append(np.array(Image.fromarray(cap_show.image(max(0, i)).astype(np.uint8)).crop(crop)))
        t += 1.0 / fps
    return frames
