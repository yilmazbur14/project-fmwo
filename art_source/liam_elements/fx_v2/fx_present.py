"""FX v2 presentation: the before/after GIFs (shipped left, v2 right, side by side at game scale on the real mat, each
timed the way the code plays it), the in-fight mocks and the contact sheet. Builds images in memory; fx_build writes
them (and only fx_build, under its guard).
"""
import math
import os
import sys

sys.dont_write_bytecode = True

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import fx_common as C
import fx_scene as SC

TICK = 0.02


def font(size):
    for name in ('arialbd.ttf', 'arial.ttf', 'segoeui.ttf'):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


# ------------------------------------------------------------------ clip timing
def loop_index(t, times):
    total = sum(times)
    t = t % total
    for i, d in enumerate(times):
        if t < d:
            return i
        t -= d
    return len(times) - 1


def once_index(t, times):
    """The frame of a one-shot clip at t, or None once it has played out (or before it starts)."""
    if t < 0:
        return None
    for i, d in enumerate(times):
        if t < d:
            return i
        t -= d
    return None


def even_index(t, total, n):
    """A clip spread evenly over `total` seconds (the wave collapse, the melt and shatter): None outside it."""
    if t < 0 or t >= total:
        return None
    return min(int(t / total * n), n - 1)


# ------------------------------------------------------------------ the GIF engine
def gif_frames(render, duration, labels, title, note=''):
    """render(t, variant) -> PIL image (both variants the same size). Returns frames and durations (ms), deduped."""
    fb = font(15)
    fs = font(12)
    frames, durs, last = [], [], None
    n = int(round(duration / TICK))
    for i in range(n):
        t = i * TICK
        a = render(t, 'before')
        b = render(t, 'after')
        w, h = a.size
        head = 62
        out = Image.new('RGB', (w * 2 + 12, h + head), (24, 26, 34))
        out.paste(a.convert('RGB'), (0, head))
        out.paste(b.convert('RGB'), (w + 12, head))
        d = ImageDraw.Draw(out)
        d.text((8, 4), title, fill=(255, 255, 255), font=fb)
        if note:
            d.text((8, 23), note, fill=(200, 200, 210), font=fs)
        d.text((8, 41), 'BEFORE (shipped): %s' % labels[0], fill=(255, 214, 120), font=fs)
        d.text((w + 20, 41), 'AFTER (fx_v2): %s' % labels[1], fill=(140, 235, 255), font=fs)
        key = out.tobytes()
        if key == last:
            durs[-1] += int(TICK * 1000)
            continue
        last = key
        frames.append(out)
        durs.append(int(TICK * 1000))
    return frames, durs


def save_gif(frames, durs, path):
    """One shared palette for every frame (no flicker), no dither, looping forever."""
    sample = frames[:: max(1, len(frames) // 8)][:8]
    w, h = frames[0].size
    mont = Image.new('RGB', (w, h * len(sample)))
    for i, f in enumerate(sample):
        mont.paste(f, (0, i * h))
    pal = mont.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    q[0].save(path, save_all=True, append_images=q[1:], duration=durs, loop=0, disposal=1, optimize=False)
    return path


# ------------------------------------------------------------------ the pieces
class Pieces:
    """Before (the shipped approval sheets) and after (v2) frames for everything the GIFs and mocks draw."""

    def __init__(self, v2, arena):
        F, sh = SC.Frames, SC.shipped_frames
        self.arena = arena
        self.v2 = {k: F(frames=v) for k, v in v2.items()}
        self.old = {
            'liam_wave_crest': sh('liam_wave_crest', 94), 'liam_wave_body': sh('liam_wave_body', 94),
            'liam_wave_tell': sh('liam_wave_tell', 282), 'liam_wave_collapse': sh('liam_wave_collapse', 282),
            'liam_wave_splash': sh('liam_wave_splash', 32), 'liam_gust_burst': sh('liam_gust_burst', 48),
            'liam_gust_trail': sh('liam_gust_trail', 24), 'liam_cold_breath': sh('liam_cold_breath', 40),
            'liam_flood': sh('liam_flood', 64), 'liam_ice': sh('liam_ice', 64),
            'liam_ice_melt': sh('liam_ice_melt', 64), 'liam_ice_shatter': sh('liam_ice_shatter', 64),
            'liam_freeze_front': sh('liam_freeze_front', 16), 'liam_tremor_block': sh('liam_tremor_block', 96),
            'liam_tremor_crack': sh('liam_tremor_crack', 16), 'liam_slam_burst': sh('liam_slam_burst', 32),
            'liam_pillar_dust': sh('liam_pillar_dust', 64),
        }
        self.pillar = SC.pillar_frames()
        self.draft_pivot = (10, 0)
        self.poses = {n: SC.pose_frames(n) for n in ('perch_idle', 'cast_left', 'cast_right', 'blast', 'breathe',
                                                        'slam')}

    def get(self, name, variant):
        if variant == 'after' and name in self.v2:
            return self.v2[name]
        return self.old[name]


def pose_frame(P, name, t, times, loop=False):
    fr = P.poses[name]
    i = loop_index(t, times) if loop else (once_index(t, times) if once_index(t, times) is not None else len(times) - 1)
    return fr.big(i)


def perch(shot, P, pose_big, pillar_i=5):
    SC.liam_on_pillar(shot, P.pillar.big(pillar_i), pose_big)


# ---- WATER
def gif_wave(P, contract):
    crop = (540, 150, 426, 380)
    front = 520
    ct = contract

    def render(t, v):
        s = SC.Shot(P.arena, crop)
        if v == 'before':
            body, crest = P.old['liam_wave_body'].small[0], P.old['liam_wave_crest'].small[int(t / 0.1) % 3]
        else:
            f = int(t / ct['wave_frame_time']) % ct['wave_crest_frames']
            body, crest = P.v2['liam_wave_body'].small[f], P.v2['liam_wave_crest'].small[f]
        big, pos = SC.band_left(body, crest, front)
        s.paste(big, pos)
        s.ropes()
        return s.result()
    return gif_frames(render, 1.44, ('crest 3 @0.1, body still', 'crest 12 + body shimmer 12 @0.06'),
                      'WAVE (crest + body)', 'left band at the seam end; the right wave is its mirror. v2 body shimmer '
                      'needs the body-tile hook.')


def gif_wave_tell(P, contract):
    crop = (540, 0, 426, 300)
    rope_top = 114

    def render(t, v):
        s = SC.Shot(P.arena, crop)
        tt = t % 0.9
        front = -156 + 600 * tt
        if v == 'before':
            body, crest = P.old['liam_wave_body'].small[0], P.old['liam_wave_crest'].small[int(tt / 0.1) % 3]
            tell = P.old['liam_wave_tell']
            ti = int(tt / 0.1) % len(tell)
        else:
            f = int(tt / 0.06) % 12
            body, crest = P.v2['liam_wave_body'].small[f], P.v2['liam_wave_crest'].small[f]
            tell = P.v2['liam_wave_tell']
            ti = int(tt / 0.06) % len(tell)
        big, pos = SC.band_left(body, crest, front)
        s.paste(big, pos)
        if front < rope_top:
            tb = tell.big(ti)
            s.paste(tb, (SC.WAVE_LEFT_X[1] - tb.width, rope_top - tb.height))
        s.ropes()
        return s.result()
    return gif_frames(render, 0.9, ('3 frames @0.1', '8 frames @0.06: rise 0-4, tremble 5-7'), 'WAVE TELL',
                      'a wave from spawn (front 0.45 s above the rope) to 0.45 s past it; the swell shows until the '
                      'front crosses the rope')


def gif_wave_collapse(P, contract):
    crop = (540, 150, 426, 380)
    front = 520

    def render(t, v):
        s = SC.Shot(P.arena, crop)
        tt = t % 1.2
        if tt < 0.42:
            if v == 'before':
                body, crest = P.old['liam_wave_body'].small[0], P.old['liam_wave_crest'].small[int(tt / 0.1) % 3]
            else:
                f = int(tt / 0.06) % 12
                body, crest = P.v2['liam_wave_body'].small[f], P.v2['liam_wave_crest'].small[f]
            big, pos = SC.band_left(body, crest, front)
            s.paste(big, pos)
        else:
            fr = P.get('liam_wave_collapse', v)
            i = even_index(tt - 0.42, 0.3, len(fr))
            if i is not None:
                cb = fr.big(i)
                s.paste(cb, (SC.WAVE_LEFT_X[1] - cb.width, front - cb.height))
        s.ropes()
        return s.result()
    return gif_frames(render, 1.2, ('3 frames over 0.3 s', '8 frames over 0.3 s'), 'WAVE COLLAPSE',
                      'wave_collapse_time 0.3: the frames spread evenly over it (LiamWave._show_collapse)')


def gif_splash(P, contract):
    crop = (740, 700, 440, 250)
    body = SC.PLAYER_CAPTURED

    def render(t, v):
        s = SC.Shot(P.arena, crop)
        s.player(body)
        tt = t % 0.8
        fr = P.get('liam_wave_splash', v)
        times = [0.05, 0.06, 0.07, 0.08] if v == 'before' else contract['wave_splash_times']
        i = once_index(tt - 0.1, times)
        if i is not None:
            s.at_pivot(fr.big(i), (body[0], body[1]), (16, 20))
        return s.result()
    return gif_frames(render, 0.8, ('4 frames, 0.26 s', '7 frames, 0.26 s'), 'PARRY SPLASH',
                      'on the player\'s hurtbox centre, pivot (16, 20)')


def gif_flood_ripple(P, contract):
    crop = (400, 480, 576, 384)

    def render(t, v):
        s = SC.Shot(P.arena, crop)
        cov = min(5, int(t / 0.45))
        water = s.tile(P.old['liam_flood'].small[cov])
        if v == 'after':
            k = int(t / contract['flood_ripple_time']) % len(P.v2['liam_flood_ripple'])
            s.tile(P.v2['liam_flood_ripple'].small[k], clip_to=water)
        return s.result()
    return gif_frames(render, 3.6, ('coverage frames only', 'same frames + ripple overlay 12 @0.1'), 'FLOOD RIPPLE',
                      'the six nested coverage frames are the shipped ones; the ripple is drawn clipped to the water '
                      '(new hook)')


# ---- AIR
def gif_gust_burst(P, contract):
    crop = (800, 0, 400, 330)
    tip = SC.pose_point((74, 70))

    def render(t, v):
        s = SC.Shot(P.arena, crop)
        tt = t % 1.2
        if tt < 0.6:
            pose = P.poses['blast'].big(once_index(tt, [0.15, 0.15, 0.3]) or 0)
        else:
            pose = P.poses['perch_idle'].big(loop_index(tt - 0.6, [0.2] * 4))
        perch(s, P, pose)
        fr = P.get('liam_gust_burst', v)
        times = [0.05, 0.06, 0.08, 0.1] if v == 'before' else contract['gust_burst_times']
        i = once_index(tt - 0.3, times)
        if i is not None:
            s.at_pivot(fr.big(i), tip, (24, 24))
        s.hud()
        return s.result()
    return gif_frames(render, 1.2, ('4 frames, 0.29 s', '7 frames, 0.29 s'), 'GUST BURST',
                      'on the blast pose\'s staff tip at blast_windup (0.3 s), opening down the ring')


def gif_gust_trail(P, contract):
    crop = (740, 330, 440, 640)

    def render(t, v):
        s = SC.Shot(P.arena, crop)
        tt = t % 0.9
        w = min(1.0, tt / 0.5)
        w = 1 - (1 - w) * (1 - w)
        y = 450 + (900 - 450) * w
        body = (960, round(y))
        s.player(body)
        if tt < 0.5:
            fr = P.get('liam_gust_trail', v)
            ft = 0.07 if v == 'before' else contract['gust_trail_time']
            s.at_pivot(fr.big(int(tt / ft)), (body[0], body[1] + 42), (12, 31))
        return s.result()
    return gif_frames(render, 0.9, ('3 frames @0.07', '6 frames @0.05'), 'LAUNCH TRAIL',
                      'on the launched player\'s feet for launch_time (0.5 s, ease-out) down to y 900')


def gif_cold_breath(P, contract):
    crop = (740, 0, 440, 420)
    mouth = SC.pose_point((43.5, 55))
    mouth = (round(mouth[0] + 0.5), round(mouth[1]))

    def render(t, v):
        s = SC.Shot(P.arena, crop)
        tt = t % 1.6
        if tt < 0.3:
            pose = P.poses['breathe'].big(0)
        elif tt < 1.3:
            pose = P.poses['breathe'].big(1 + int((tt - 0.3) / 0.1) % 2)
        else:
            pose = P.poses['breathe'].big(3)
        perch(s, P, pose)
        fr = P.get('liam_cold_breath', v)
        if v == 'before':
            if 0.3 <= tt < 1.3:
                k = int((tt - 0.3) / 0.1)
                i = 0 if k == 0 else (1 if k % 2 else 2)
                s.at_pivot(fr.big(i), mouth, (20, 2))
        else:
            n = contract['breath_frames']
            ft = contract['breath_time']
            if 0.3 <= tt < 1.3:
                k = int((tt - 0.3) / ft)
                i = 0 if k == 0 else 1 + (k - 1) % (n - 2)
                s.at_pivot(fr.big(i), mouth, (20, 2))
            elif 1.3 <= tt < 1.3 + ft:
                s.at_pivot(fr.big(n - 1), mouth, (20, 2))
        s.hud()
        return s.result()
    return gif_frames(render, 1.6, ('start 0, then 1/2 alternating', 'start 0, loop 1-6, end 7 @0.06'),
                      'COLD BREATH', 'held 1.0 s here to show the loop; in the fight it shows 0.3-0.6 s, then the '
                      'slam pose takes over (and v2 ends on its break-up frame)')


ROW_Y = 348
ROW_X = (105, 1815)
BOTTOM = 969


def draft_spawns(seconds, every=0.03, seed=3):
    """LiamElementFx.downdraft as addendum 3 plans it: one streak every 0.03 s at a random x on the row line."""
    rnd = np.random.RandomState(seed)
    out = []
    t = 0.0
    while t < seconds:
        out.append((t, rnd.uniform(*ROW_X), rnd.randint(0, 6)))
        t += every
    return out


def draw_downdraft(s, P, t, spawns, speed=1800.0, period=None):
    """Every streak alive at t: falling at downdraft_speed x 1.5 from the row's foot and fading as it goes (looped
    over `period` so the GIF runs on without a gap)."""
    fr = P.v2['liam_downdraft']
    n = len(fr)
    ft = 0.04
    pivot = P.draft_pivot
    for (t0, x, f0) in spawns:
        for rep in ((0.0,) if period is None else (0.0, -period)):
            age = t - (t0 + rep)
            if age < 0:
                continue
            y = ROW_Y + speed * age
            # gone by the time its head (80 texels under its tail) reaches the bottom rope, fading over the last 65 %
            end = BOTTOM - 80 * 3
            prog = (y - ROW_Y) / float(end - ROW_Y)
            if prog >= 1.0:
                continue
            fade = 1.0 if prog < 0.35 else 1.0 - (prog - 0.35) / 0.65
            big = fr.big(f0 + int(age / ft))
            if fade < 0.999:
                a = np.array(big)
                a[..., 3] = (a[..., 3] * fade).astype(np.uint8)
                big = Image.fromarray(a, 'RGBA')
            s.at_pivot(big, (round(x), round(y)), pivot)


def gif_downdraft(P, contract):
    crop = (560, 180, 800, 620)
    period = 1.2
    spawns = draft_spawns(period)

    def render(t, v):
        s = SC.Shot(P.arena, crop)
        s.tile(P.old['liam_flood'].small[5])
        s.tile(P.old['liam_ice'].small[0], mask=SC.ice_circle(560))
        SC.draw_row(s)
        s.paste(P.pillar.big(5), (SC.PERCH[0] - 32 * 3, SC.PERCH[1] - 72 * 3))
        s.paste(P.poses['breathe'].big(1 + int(t / 0.1) % 2), (SC.LIAM_FEET[0] - 48 * 3, SC.LIAM_FEET[1] - 96 * 3))
        body = (900, round(520 + 300 * ((t % period) / period)))
        s.player(body)
        if v == 'after':
            draw_downdraft(s, P, t % period, spawns, period=period)
        s.hud()
        return s.result()
    return gif_frames(render, period, ('no visual: the player just drifts', 'liam_downdraft, 6 @0.04, one every 0.03 s'),
                      'DOWNDRAFT (NEW)', 'streaks spawn on the row line (y 348), fall at 1800 px/s and fade, as '
                      'addendum 3 E.2.7 plans; the row is a STAND-IN (the approved pillar cut to 34 texels)')


# ---- ICE
def gif_freeze_front(P, contract):
    crop = (560, 114, 800, 520)

    def render(t, v):
        s = SC.Shot(P.arena, crop)
        tt = t % 1.2
        s.tile(P.old['liam_flood'].small[5])
        r = min(820.0, 1000.0 * tt)
        s.tile(P.old['liam_ice'].small[0], mask=SC.ice_circle(r))
        if tt < 0.82:
            fr = P.get('liam_freeze_front', v)
            ft = 0.12 if v == 'before' else contract['frost_time']
            i = int(tt / ft)
            for pos in SC.frost_positions(r):
                s.at_pivot(fr.big(i), pos, (8, 8))
        perch_big = P.pillar.big(5)
        s.paste(perch_big, (SC.PERCH[0] - 32 * 3, SC.PERCH[1] - 72 * 3))
        return s.result()
    return gif_frames(render, 1.2, ('3 frames @0.12', '6 frames @0.08'), 'FREEZE FRONT',
                      'the ice circle growing from the pillar\'s foot at freeze_speed (1000 px/s), frost every 48 px '
                      'round its edge')


def gif_ice_melt(P, contract):
    crop = (400, 480, 576, 384)

    def render(t, v):
        s = SC.Shot(P.arena, crop)
        tt = t % 2.2
        s.tile(P.old['liam_flood'].small[5])
        fr = P.get('liam_ice_melt', v)
        if tt < 0.5:
            s.tile(P.old['liam_ice'].small[0])
        else:
            i = even_index(tt - 0.5, 1.0, len(fr))
            if i is not None:
                s.tile(fr.small[i])
        return s.result()
    return gif_frames(render, 2.2, ('3 frames over melt_time', '6 frames over melt_time'), 'ICE MELT',
                      'melt_time 1.0 s, frames spread evenly; the last frame is the flood\'s full frame 5')


def gif_ice_shatter(P, contract):
    crop = (400, 480, 576, 384)

    def render(t, v):
        s = SC.Shot(P.arena, crop)
        tt = t % 1.6
        cov = 5 if tt < 0.5 else max(0, 5 - int((tt - 0.5) / 0.25))
        if tt < 1.5:
            s.tile(P.old['liam_flood'].small[cov])
        fr = P.get('liam_ice_shatter', v)
        if tt < 0.5:
            s.tile(P.old['liam_ice'].small[0])
        else:
            i = even_index(tt - 0.5, 0.4, len(fr))
            if i is not None:
                s.tile(fr.small[i])
        return s.result()
    return gif_frames(render, 1.6, ('4 frames over 0.4 s', '8 frames over 0.4 s'), 'ICE SHATTER',
                      'SHATTER_TIME 0.4 s; the water drains under it (drain_time) as in LiamRoundBlast')


# ---- EARTH
def block_timeline(contract, variant):
    """The ridge's life in the GIF: tell, heave, active, pulse, active, pulse, active, crumble, gone."""
    if variant == 'before':
        clips = {'tell': ([0, 1, 2, 3], [0.15] * 4), 'heave': ([4, 5, 6], [0.06, 0.08, 0.10]),
                 'active': ([7, 8, 9, 10], [0.12] * 4), 'pulse': ([11, 12], [0.06, 0.10]),
                 'crumble': ([13, 14, 15, 16], [0.08] * 4)}
    else:
        c = contract['tremor_clips']
        clips = {k: (c[k]['frames'], c[k]['times']) for k in c}
    seq = [('tell', 1), ('heave', 1), ('active', 2), ('pulse', 1), ('active', 1), ('pulse', 1), ('active', 1),
           ('crumble', 1)]
    out = []
    for name, reps in seq:
        frames, times = clips[name]
        if name == 'active':
            total = 0.0
            target = 0.6 * reps - 0.16
            while total < target:
                for f, d in zip(frames, times):
                    out.append((f, d))
                    total += d
                    if total >= target:
                        break
        else:
            out.extend(zip(frames, times))
    return out


def gif_tremor_block(P, contract):
    crop = (700, 440, 420, 200)
    rect = (760, 520, 288, 72)
    tls = {v: block_timeline(contract, v) for v in ('before', 'after')}

    def render(t, v):
        s = SC.Shot(P.arena, crop)
        s.tile(P.old['liam_flood'].small[5])
        s.tile(P.old['liam_ice'].small[0])
        tl = tls[v]
        total = sum(d for _, d in tl)
        tt = t % (total + 0.4)
        fr = P.get('liam_tremor_block', v)
        acc = 0.0
        for f, d in tl:
            if tt < acc + d:
                s.paste(fr.big(f), (rect[0], rect[1] - 8 * 3))
                break
            acc += d
        return s.result()
    total = max(sum(d for _, d in tls['before']), sum(d for _, d in tls['after'])) + 0.4
    return gif_frames(render, round(total * 50) / 50.0, ('17 frames, one sheet', '28 frames, per-clip strips'), 'TREMOR RIDGE',
                      'tell (crack slam) - heave - active - pulse on each slam - crumble; footprint rows 8..31 unchanged')


def gif_tremor_crack(P, contract):
    crop = (860, 250, 460, 400)
    rect = (1110, 560, 288, 72)

    def render(t, v):
        s = SC.Shot(P.arena, crop)
        s.tile(P.old['liam_flood'].small[5])
        s.tile(P.old['liam_ice'].small[0])
        tt = t % 1.2
        reach = 1400.0 * tt
        fr = P.get('liam_tremor_crack', v)
        ft = 0.08 if v == 'before' else contract['crack_time']
        k = int(tt / ft)
        for i, (pos, ang) in enumerate(crack_list(rect, reach)):
            SC.paste_crack(s, fr.small[k % len(fr)], pos, ang)
        blk = P.get('liam_tremor_block', v)
        bi = min(3, int(tt / 0.15)) if v == 'before' else min(5, int(tt / 0.1))
        s.paste(blk.big(bi), (rect[0], rect[1] - 8 * 3))
        s.paste(P.pillar.big(5), (SC.PERCH[0] - 32 * 3, SC.PERCH[1] - 72 * 3))
        return s.result()
    return gif_frames(render, 1.2, ('3 frames @0.08', '6 frames @0.06'), 'TREMOR CRACK',
                      'segments laid from the pillar\'s foot to a ridge as the crack races out (crack_time 0.3 s)')


def crack_list(rect, reach):
    return SC.crack_segments(rect, reach)


def gif_slam_burst(P, contract):
    crop = (820, 0, 400, 330)
    butt = SC.pose_point((65, 95))

    def render(t, v):
        s = SC.Shot(P.arena, crop)
        tt = t % 1.0
        i = once_index(tt, [0.1, 0.1, 0.15, 0.25])
        pose = P.poses['slam'].big(i if i is not None else 3)
        perch(s, P, pose)
        fr = P.get('liam_slam_burst', v)
        times = [0.05, 0.07, 0.1] if v == 'before' else contract['slam_burst_times']
        j = once_index(tt - 0.2, times)
        if j is not None:
            s.at_pivot(fr.big(j), (round(butt[0]), round(butt[1])), (16, 15))
        s.hud()
        return s.result()
    return gif_frames(render, 1.0, ('3 frames, 0.22 s', '6 frames, 0.22 s'), 'SLAM BURST',
                      'on the slam pose\'s staff butt at the impact (0.2 s into the pose)')


def gif_pillar_dust(P, contract):
    crop = (780, 60, 360, 360)

    def render(t, v):
        s = SC.Shot(P.arena, crop)
        tt = t % 2.4
        pil = P.pillar
        if tt < 0.6:
            w = tt / 0.6
            w = 1 - (1 - w) * (1 - w)
            pf = [0, 1, 2, 3, 4][min(4, int(w * 5))]
        elif tt < 1.3:
            pf = 5
        elif tt < 1.8:
            pf = [11, 12, 13, 14, 15, 16][min(5, int((tt - 1.3) / 0.5 * 6))]
        else:
            pf = None
        if pf is not None:
            s.paste(pil.big(pf), (SC.PERCH[0] - 32 * 3, SC.PERCH[1] - 72 * 3))
        fr = P.get('liam_pillar_dust', v)
        ft = 0.08 if v == 'before' else contract['pillar_dust_time']
        for t0 in (0.0, 1.3):
            i = once_index(tt - t0, [ft] * len(fr))
            if i is not None:
                s.paste(fr.big(i), (SC.PERCH[0] - 32 * 3, SC.PERCH[1] - 72 * 3))
        return s.result()
    return gif_frames(render, 2.4, ('3 frames @0.08', '7 frames @0.065'), 'PILLAR DUST',
                      'played at its foot on the rise (rise_time 0.6) and the crumble (crumble_time 0.5)')


GIFS = [
    ('ab_wave', gif_wave), ('ab_wave_tell', gif_wave_tell), ('ab_wave_collapse', gif_wave_collapse),
    ('ab_wave_splash', gif_splash), ('ab_flood_ripple', gif_flood_ripple),
    ('ab_gust_burst', gif_gust_burst), ('ab_gust_trail', gif_gust_trail), ('ab_cold_breath', gif_cold_breath),
    ('ab_downdraft', gif_downdraft),
    ('ab_freeze_front', gif_freeze_front), ('ab_ice_melt', gif_ice_melt), ('ab_ice_shatter', gif_ice_shatter),
    ('ab_tremor_block', gif_tremor_block), ('ab_tremor_crack', gif_tremor_crack), ('ab_slam_burst', gif_slam_burst),
    ('ab_pillar_dust', gif_pillar_dust),
]


# ------------------------------------------------------------------ the contact sheet
def contact(sheets, width=2400):
    """Every v2 sheet, frames numbered, on a checker (so transparency reads), with its cell, count, play and tags."""
    fb, fs = font(15), font(12)
    blocks = []
    for d in sheets:
        fw, fh = d['cell']
        s = 3 if fw * 3 <= 600 else 2
        per = max(1, (width - 40) // (fw * s + 6))
        n = len(d['frames'])
        rows = (n + per - 1) // per
        h = 44 + rows * (fh * s + 22)
        blocks.append((d, s, per, rows, h))
    total = sum(b[4] for b in blocks) + 60
    out = Image.new('RGB', (width, total), (26, 28, 38))
    dr = ImageDraw.Draw(out)
    dr.text((20, 16), 'LIAM FX v2 (approval pass) - every sheet at 2-3x; frames numbered; the checker shows transparency',
            fill=(255, 255, 255), font=fb)
    y = 50
    for (d, s, per, rows, h) in blocks:
        fw, fh = d['cell']
        shipped = d['shipped']
        was = ('shipped %d' % shipped[1]) if shipped else 'NEW'
        tags = '  '.join('%s %d-%d' % t for t in d['tags'])
        times = d['times']
        tt = ('%.3gs each' % times[0]) if len(set(times)) == 1 else ('times ' + ','.join('%.3g' % t for t in times))
        dr.text((20, y), '%s   %d frames of %dx%d (%s)   pivot %s   %s' % (d['name'], len(d['frames']), fw, fh, was,
                                                                         d['pivot'], d['play']),
                fill=(255, 214, 120), font=fb)
        dr.text((20, y + 20), 'tags: %s    %s    shown %dx' % (tags, tt, s), fill=(190, 200, 212), font=fs)
        yy = y + 40
        for i, f in enumerate(d['frames']):
            c, r = i % per, i // per
            x0, y0 = 20 + c * (fw * s + 6), yy + r * (fh * s + 22) + 14
            chk = np.zeros((fh * s, fw * s, 3), dtype=np.uint8)
            ys, xs = np.mgrid[0:fh * s, 0:fw * s]
            m = ((xs // 12 + ys // 12) % 2) == 0
            chk[m] = (86, 92, 108)
            chk[~m] = (70, 76, 92)
            tile = Image.fromarray(chk, 'RGB').convert('RGBA')
            tile.alpha_composite(SC.up(SC.img(f), s))
            out.paste(tile.convert('RGB'), (x0, y0))
            dr.text((x0, y0 - 14), str(i), fill=(255, 230, 120), font=fs)
        y += h
    return out
