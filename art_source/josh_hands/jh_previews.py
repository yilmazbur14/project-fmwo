"""The approval previews: the in-fight mocks (1920x1080, on a real capture of his arena with the HUD) and
the GIFs, composed at the game's 3x from the same frames the sheets are cut from, placed by the plan's
numbers (PLAN.md): Josh (959, 700), gates (575, 270) / (1345, 270), resting hands' pivots at gate +
(0, 170), a hand over a player at (960, 760), the other on deck at feet + 240 px, badge at
(spot.x, max(spot.y - 150, 84)), hover 210 px, lock rise 36 px.
"""
import math
import os

from PIL import Image, ImageDraw

import jh_lib as H
import jh_hand as HD
import jh_anims as A
import jh_portal as P
import jh_fx as FX
import jh_josh as J

ROOT = H.ROOT
CAP = os.path.join(H.SCRATCH, 'cap')
S3 = 3

JOSH_AT = (959, 700)
GATES = {'left': (575, 270), 'right': (1345, 270)}
REST_OFFSET = (0, 170)
SPOT = (960, 760)
DECK = 240
HOVER_H = 210
LOCK_RISE = 36
PLAYER_BODY = (960, 718)             # the capture's player: its feet (hurtbox bottom) are at SPOT


# ------------------------------------------------------------------ assets

_cache = {}


def asset(name):
    if name in _cache:
        return _cache[name]
    if name == 'bg':
        im = Image.open(os.path.join(CAP, 'arena_bg.png')).convert('RGBA')
    elif name == 'player':
        bg = Image.open(os.path.join(CAP, 'arena_bg.png')).convert('RGBA')
        pl = Image.open(os.path.join(CAP, 'arena_player.png')).convert('RGBA')
        box = (PLAYER_BODY[0] - 60, PLAYER_BODY[1] - 60, PLAYER_BODY[0] + 60, PLAYER_BODY[1] + 60)
        a, b = bg.crop(box), pl.crop(box)
        out = Image.new('RGBA', a.size, (0, 0, 0, 0))
        pa, pb, po = a.load(), b.load(), out.load()
        for y in range(a.height):
            for x in range(a.width):
                if pa[x, y][:3] != pb[x, y][:3]:
                    po[x, y] = pb[x, y]
        im = (out, (box[0], box[1]))
    elif name == 'tell':
        t = Image.open(os.path.join(ROOT, 'Assets', 'Effects', 'parry_tell.png')).convert('RGBA')
        im = [t.crop((i * 32, 0, i * 32 + 32, 24)) for i in range(t.width // 32)]
    elif name == 'card':
        t = Image.open(os.path.join(ROOT, 'Assets', 'Characters', 'Josh', 'Cards', 'card_projectile.png')).convert('RGBA')
        im = [t.crop((i * 24, 0, i * 24 + 24, 24)) for i in range(4)]
    elif name == 'idle':
        t = Image.open(os.path.join(ROOT, 'Assets', 'Characters', 'Josh', 'josh_idle.png')).convert('RGBA')
        im = [t.crop((i * 80, 0, i * 80 + 80, 80)) for i in range(4)]
    else:
        raise KeyError(name)
    _cache[name] = im
    return im


def hand_frames(clip, take='A'):
    key = ('hand', clip, take)
    if key not in _cache:
        HD.TAKE['backs'] = (take == 'B')
        try:
            out = []
            for fr in A.clip_frames(clip):
                px, gl = A.render_frame(fr)
                out.append((H.to_image(px, A.FW, A.FH), H.to_image(gl, A.FW, A.FH, H.GLOW)))
        finally:
            HD.TAKE['backs'] = False
        _cache[key] = out
    return _cache[key]


def portal_frames(seq):
    key = ('portal', seq)
    if key not in _cache:
        _cache[key] = [(H.to_image(b, P.PW, P.PH), H.to_image(g, P.PW, P.PH, H.GLOW)) for b, g in P.seq_frames(seq)]
    return _cache[key]


def josh_frames(sheet):
    key = ('josh', sheet)
    if key not in _cache:
        _cache[key] = [H.to_image(J.frame(sheet, i), 80, 80) for i in range(4)]
    return _cache[key]


def mark_frames():
    if 'mark' not in _cache:
        _cache['mark'] = [H.to_image(f, FX.MW, FX.MH) for f in FX.mark_frames()]
    return _cache['mark']


def impact_fx_frames():
    if 'ifx' not in _cache:
        _cache['ifx'] = [H.to_image(f, FX.IW, FX.IH) for f in FX.impact_frames()]
    return _cache['ifx']


# ------------------------------------------------------------------ drawing

def big(im, flip=False):
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    return im.resize((im.width * S3, im.height * S3), Image.NEAREST)


def draw(canvas, im, pivot, at, flip=False, glow=None):
    """A frame placed with its pivot (corner texels) on the world point `at`; flipped about the pivot
    column (which is the frame's centre column for every sheet here)."""
    x0 = int(round(at[0] - pivot[0] * S3))
    y0 = int(round(at[1] - pivot[1] * S3))
    if glow is not None:
        canvas = H.add_glow(canvas, big(glow, flip), (x0, y0))
    canvas.alpha_composite(big(im, flip), (x0, y0)) if 0 <= x0 and 0 <= y0 else _paste_clip(canvas, big(im, flip), x0, y0)
    return canvas


def _paste_clip(canvas, im, x0, y0):
    cx0, cy0 = max(0, -x0), max(0, -y0)
    sub = im.crop((cx0, cy0, im.width, im.height))
    canvas.alpha_composite(sub, (x0 + cx0, y0 + cy0))


def draw_player(canvas, feet=SPOT):
    """The captured player (standing, facing up the ring), with its feet (hurtbox bottom) on `feet`."""
    cut, xy = asset('player')
    dx, dy = feet[0] - SPOT[0], feet[1] - SPOT[1]
    _paste_clip(canvas, cut, xy[0] + dx, xy[1] + dy)
    return canvas


def draw_josh(canvas, im, at=JOSH_AT, flip=False):
    return draw(canvas, im, (40, 79), at, flip)


def draw_card(canvas, at, angle, frame, scale=1.0):
    """card_projectile.png (the flurry, per the plan) at `at`, turned along its path, shrunk by scale."""
    im = asset('card')[frame % 4]
    s = max(1, int(round(S3 * scale)))
    im = im.resize((24 * s, 24 * s), Image.NEAREST).rotate(-angle, resample=Image.NEAREST, expand=True)
    x0 = int(round(at[0] - im.width / 2.0))
    y0 = int(round(at[1] - im.height / 2.0))
    _paste_clip(canvas, im, x0, y0)
    return canvas


def draw_badge(canvas, anchor, t):
    frames = asset('tell')
    im = frames[int(t / 0.06) % len(frames)]
    x0 = int(round(anchor[0] - 48))
    y0 = int(round(anchor[1] - 72))
    _paste_clip(canvas, im.resize((96, 72), Image.NEAREST), x0, y0)
    return canvas


def rest_point(side):
    g = GATES[side]
    return (g[0] + REST_OFFSET[0], g[1] + REST_OFFSET[1])


# ------------------------------------------------------------------ the mocks

def label(canvas, text, xy=(14, 6)):
    d = ImageDraw.Draw(canvas)
    d.rectangle((xy[0] - 6, xy[1] - 4, xy[0] + 8 * len(text) + 6, xy[1] + 16), fill=(0, 0, 0, 200))
    d.text(xy, text, fill=(255, 255, 255, 255))
    return canvas


def mock_rest(take='A'):
    c = asset('bg').copy()
    for side, g in GATES.items():
        b, gl = portal_frames('loop')[2 if side == 'left' else 4]
        c = draw(c, b, P.PIVOT, g, flip=(side == 'left'), glow=gl)
    for side in GATES:
        im, gl = hand_frames('hover', take)[1 if side == 'left' else 4]
        c = draw(c, im, (A.PX, A.PY), rest_point(side), flip=(side == 'left'), glow=gl)
    c = draw_josh(c, josh_frames('summon')[3])
    c = draw_player(c, (960, 900))
    return label(c, 'MOCK 1 (take %s): Josh at (959,700) on the summon loop, gates at (575,270)/(1345,270), hands resting at gate + (0,170), player at (960,900)' % take)


def mock_brief(take='A'):
    """The brief's picture: Josh at home pointing, both gates, the left hand resting at its gate, the
    right hand locked over the player with its mark and the red badge."""
    feet = (1250, 820)
    c = asset('bg').copy()
    for side, g in GATES.items():
        b, gl = portal_frames('loop')[0 if side == 'left' else 3]
        c = draw(c, b, P.PIVOT, g, flip=(side == 'left'), glow=gl)
    im, gl = hand_frames('hover', take)[3]
    c = draw(c, im, (A.PX, A.PY), rest_point('left'), flip=True, glow=gl)
    c = draw(c, mark_frames()[1], (FX.MPX, FX.MPY), feet)
    c = draw_josh(c, josh_frames('command')[2])
    c = draw_player(c, feet)
    im, gl = hand_frames('windup', take)[1]
    c = draw(c, im, (A.PX, A.PY), (feet[0], feet[1] - HOVER_H - LOCK_RISE), glow=gl)
    c = draw_badge(c, (feet[0], max(feet[1] - 150, 84)), 0.0)
    return label(c, 'MOCK 3 (take %s): the brief - Josh pointing, left hand at rest at its gate, right hand locked over the player at (1250,820) with its mark and the red badge' % take)


def mock_attack(take='A'):
    """The left hand locked over the player at (960, 760) (a tie on distance goes to the left), the
    right one on deck at feet + 240 px, the mark under the player, the red badge up; Josh pointing."""
    c = asset('bg').copy()
    for side, g in GATES.items():
        b, gl = portal_frames('loop')[1 if side == 'left' else 3]
        c = draw(c, b, P.PIVOT, g, flip=(side == 'left'), glow=gl)
    # floor: the mark under the player (the hover flicker's bright frame)
    c = draw(c, mark_frames()[1], (FX.MPX, FX.MPY), SPOT, flip=True)
    # characters, y-sorted: Josh (700) then the player (760)
    c = draw_josh(c, josh_frames('command')[2])
    c = draw_player(c)
    # air: the deck hand at its spot, hovering; the active hand at the lock (windup, risen)
    im, gl = hand_frames('hover', take)[2]
    c = draw(c, im, (A.PX, A.PY), (SPOT[0] + DECK, SPOT[1] - HOVER_H), flip=False, glow=gl)
    im, gl = hand_frames('windup', take)[1]
    c = draw(c, im, (A.PX, A.PY), (SPOT[0], SPOT[1] - HOVER_H - LOCK_RISE), flip=True, glow=gl)
    c = draw_badge(c, (SPOT[0], max(SPOT[1] - 150, 84)), 0.0)
    return label(c, 'MOCK 2 (take %s): left hand locked over a player at (960,760) with its mark and the red badge; right hand on deck at +240 px' % take)


# ------------------------------------------------------------------ GIFs

def save_gif(path, frames, durs):
    pal = [f.convert('RGB').quantize(colors=255, method=Image.MEDIANCUT, dither=Image.NONE) for f in frames]
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=[max(20, int(round(d * 1000))) for d in durs],
                loop=0, disposal=1, optimize=False)
    return path


def at_time(seq_times, t, loop=False):
    """The frame index of a clip `t` seconds in (holding the last frame if not looping)."""
    total = sum(seq_times)
    if loop:
        t = t % total
    acc = 0.0
    for i, d in enumerate(seq_times):
        acc += d
        if t < acc - 1e-9:
            return i
    return len(seq_times) - 1


def gif_portal(out_path):
    """One gate, close up: open, the loop twice, a feed, the loop, close."""
    box = (1345 - 170, 270 - 170, 1345 + 170, 270 + 170)
    bg = asset('bg').crop(box)
    seq = [('open', P.SEQS['open'], False)] + [('loop', P.SEQS['loop'], True)] * 2 + [('feed', P.SEQS['feed'], False)] + \
          [('loop', P.SEQS['loop'], True), ('close', P.SEQS['close'], False)]
    frames, durs = [], []
    for name, times, _ in seq:
        for i, d in enumerate(times):
            b, g = portal_frames(name)[i]
            c = draw(bg.copy(), b, P.PIVOT, (170, 170), glow=g)
            frames.append(c)
            durs.append(d)
    frames.append(bg.copy())
    durs.append(0.5)
    return save_gif(out_path, frames, durs)


def _flurry_card_pos(k, t0, t, origin, target):
    """The plan's flurry: 0.40 s along a quadratic arc whose control point is 160 px above the chord's
    middle; shrinks to 0.4 over the last 30% (the fade over the last 15% is the code's)."""
    u = (t - t0) / 0.40
    if u < 0 or u > 1:
        return None
    mx, my = (origin[0] + target[0]) / 2.0, (origin[1] + target[1]) / 2.0 - 160.0
    x = (1 - u) ** 2 * origin[0] + 2 * (1 - u) * u * mx + u * u * target[0]
    y = (1 - u) ** 2 * origin[1] + 2 * (1 - u) * u * my + u * u * target[1]
    dx = 2 * (1 - u) * (mx - origin[0]) + 2 * u * (target[0] - mx)
    dy = 2 * (1 - u) * (my - origin[1]) + 2 * u * (target[1] - my)
    ang = math.degrees(math.atan2(dy, dx))
    sc = 1.0 if u < 0.7 else 1.0 - 0.6 * (u - 0.7) / 0.3
    return (x, y), ang, sc


def gif_summon(out_path, take='A'):
    """The plan's summon, second by second: RAISE 0, OPEN 0.20, FLURRY 0.55-1.30, FORM 1.70, IDLE 2.30."""
    box = (390, 96, 1530, 760)
    bg = asset('bg').crop(box)
    ox, oy = box[0], box[1]
    J.frame('summon', 2)
    origin = {}
    for side, texel in (('left', J.CARD_ORIGINS[2]['left']), ('right', J.CARD_ORIGINS[2]['right'])):
        origin[side] = (JOSH_AT[0] - 40 * S3 + texel[0] * S3 + 1, JOSH_AT[1] - 79 * S3 + texel[1] * S3 + 1)
    frames, durs = [], []
    dt = 0.05
    n = int(round(3.4 / dt))
    feeds = {'left': [], 'right': []}
    for k in range(16):
        side = 'left' if k % 2 == 0 else 'right'
        feeds[side].append(0.55 + 0.05 * k + 0.40)
    for f in range(n):
        t = f * dt
        c = bg.copy()

        def W(p):
            return (p[0] - ox, p[1] - oy)

        # gates
        for side, g in GATES.items():
            if t < 0.20:
                continue
            tt = t - 0.20
            fed = [a for a in feeds[side] if a <= t < a + sum(P.SEQS['feed'])]
            if tt < sum(P.SEQS['open']):
                b, gl = portal_frames('open')[at_time(P.SEQS['open'], tt)]
            elif fed:
                b, gl = portal_frames('feed')[at_time(P.SEQS['feed'], t - fed[0])]
            else:
                b, gl = portal_frames('loop')[at_time(P.SEQS['loop'], tt - sum(P.SEQS['open']), loop=True)]
            c = draw(c, b, P.PIVOT, W(g), flip=(side == 'left'), glow=gl)
        # hands forming at their rest points, then hovering
        for side in GATES:
            if t < 1.70:
                continue
            tt = t - 1.70
            if tt < sum(A.CLIPS['form']):
                im, gl = hand_frames('form', take)[at_time(A.CLIPS['form'], tt)]
            else:
                im, gl = hand_frames('hover', take)[at_time(A.CLIPS['hover'], tt - sum(A.CLIPS['form']), loop=True)]
            c = draw(c, im, (A.PX, A.PY), W(rest_point(side)), flip=(side == 'left'), glow=gl)
        # Josh
        if t < 2.30:
            if t < 0.30:
                im = josh_frames('summon')[0 if t < 0.15 else 1]
            else:
                im = josh_frames('summon')[2 + int((t - 0.30) / 0.10) % 2]
        else:
            im = asset('idle')[int((t - 2.30) / 0.15) % 4]
        c = draw_josh(c, im, W(JOSH_AT))
        # the flurry
        for k in range(16):
            side = 'left' if k % 2 == 0 else 'right'
            r = _flurry_card_pos(k, 0.55 + 0.05 * k, t, origin[side], GATES[side])
            if r:
                (x, y), ang, sc = r
                c = draw_card(c, W((x, y)), ang, int(t / 0.055), sc)
        frames.append(c)
        durs.append(dt)
    durs[-1] = 0.6
    return save_gif(out_path, frames, durs)


def _slam_timeline(parry=False):
    """One slam on the plan's clock, from the start of TRACK: (t, what) steps at 0.05 s."""
    return None


def gif_slam(out_path, take='A', parry=False):
    """TRACK (0.6 s, hover, the mark flickering) -> LOCK (windup 0.15, rise 36 px, badge) -> DROP (0.25)
    -> IMPACT (contact, pin 0.15) -> the rise (drop reversed, 0.25) -> hover. With parry: IMPACT ->
    shatter (0.30) -> the re-form on deck at 1.33x (0.45) -> hover there."""
    box = (960 - 420, 330, 960 + 330, 900)
    bg = asset('bg').crop(box)
    ox, oy = box[0], box[1]

    def W(p):
        return (p[0] - ox, p[1] - oy)

    dt = 0.025
    t_track, t_lock, t_drop = 0.6, 0.15, 0.25
    t_imp = t_track + t_lock + t_drop
    end = t_imp + (1.3 if parry else 0.9)
    frames, durs = [], []
    n = int(round(end / dt))
    deck = (SPOT[0] - DECK, SPOT[1])
    for f in range(n + 1):
        t = f * dt
        c = bg.copy()
        hand = None
        mark = None
        badge = False
        fx = None
        if t < t_track:
            h = HOVER_H
            im, gl = hand_frames('hover', take)[at_time(A.CLIPS['hover'], t, loop=True)]
            hand = (im, gl, (SPOT[0], SPOT[1] - h))
            mark = mark_frames()[int(t / 0.1) % 2]
        elif t < t_track + t_lock:
            u = (t - t_track) / t_lock
            h = HOVER_H + LOCK_RISE * (1 - (1 - u) ** 2)
            im, gl = hand_frames('windup', take)[at_time(A.CLIPS['windup'], t - t_track)]
            hand = (im, gl, (SPOT[0], SPOT[1] - h))
            mark = mark_frames()[2]
            badge = True
        elif t < t_imp:
            p = (t - t_track - t_lock) / t_drop
            h = (HOVER_H + LOCK_RISE) * (1 - p * p)
            im, gl = hand_frames('drop', take)[at_time(A.CLIPS['drop'], t - t_track - t_lock)]
            hand = (im, gl, (SPOT[0], SPOT[1] - h))
            mark = mark_frames()[2 if h > 0.75 * 246 else (3 if h > 0.45 * 246 else (4 if h > 0.12 * 246 else 5))]
            badge = True
        else:
            tt = t - t_imp
            if tt < 0.2:
                fx = impact_fx_frames()[min(3, at_time(FX.IMPACT_FX_TIMES, tt))]
            if not parry:
                if tt < 0.15:
                    im, gl = hand_frames('impact', take)[at_time(A.CLIPS['impact'], tt)]
                    hand = (im, gl, SPOT)
                    mark = mark_frames()[5]
                elif tt < 0.40:
                    u = (tt - 0.15) / 0.25
                    h = HOVER_H * (1 - (1 - u) ** 2)
                    rev = list(reversed(hand_frames('drop', take)))
                    im, gl = rev[at_time(list(reversed(A.CLIPS['drop'])), tt - 0.15)]
                    hand = (im, gl, (SPOT[0], SPOT[1] - h))
                else:
                    im, gl = hand_frames('hover', take)[at_time(A.CLIPS['hover'], tt - 0.40, loop=True)]
                    hand = (im, gl, (SPOT[0], SPOT[1] - HOVER_H))
            else:
                if tt < 0.30:
                    im, gl = hand_frames('shatter', take)[at_time(A.CLIPS['shatter'], tt)]
                    hand = (im, gl, SPOT)
                elif tt < 0.30 + 0.45:
                    form_t = (tt - 0.30) * (sum(A.CLIPS['form']) / 0.45)
                    im, gl = hand_frames('form', take)[at_time(A.CLIPS['form'], form_t)]
                    hand = (im, gl, (deck[0], deck[1] - HOVER_H))
                else:
                    im, gl = hand_frames('hover', take)[at_time(A.CLIPS['hover'], tt - 0.75, loop=True)]
                    hand = (im, gl, (deck[0], deck[1] - HOVER_H))
        if mark is not None:
            c = draw(c, mark, (FX.MPX, FX.MPY), W(SPOT), flip=True)
        if fx is not None:
            c = draw(c, fx, (FX.IPX, FX.IPY), W(SPOT), flip=True)
        landed = hand is not None and hand[2] in (SPOT,)
        if landed:
            c = draw(c, hand[0], (A.PX, A.PY), W(hand[2]), flip=True, glow=hand[1])
        cut, xy = asset('player')
        c.alpha_composite(cut, (xy[0] - ox, xy[1] - oy))
        if hand is not None and not landed:
            c = draw(c, hand[0], (A.PX, A.PY), W(hand[2]), flip=True, glow=hand[1])
        if badge:
            c = draw_badge(c, W((SPOT[0], max(SPOT[1] - 150, 84))), t)
        frames.append(c)
        durs.append(dt)
    durs[-1] = 0.6
    return save_gif(out_path, frames, durs)


# ------------------------------------------------------------------ the contact sheet

def contact_sheet(out_path, scale=3):
    rows = []
    for take in ('A', 'B'):
        for clip in A.ORDER:
            rows.append(('hand %s  take %s  %s' % (clip, take, A.CLIPS[clip]),
                         [H.add_glow(_on(im, (86, 128, 72, 255)), gl) for im, gl in hand_frames(clip, take)]))
    for seq in P.ORDER:
        rows.append(('portal %s  %s' % (seq, P.SEQS[seq]),
                     [H.add_glow(_on(b, (86, 128, 72, 255)), g) for b, g in portal_frames(seq)]))
    rows.append(('mark  %s (rim = the footprint ellipse, %dx%d texels)' % (FX.MARK_TIMES, FX.RX, FX.RY),
                 [_on(m, (86, 128, 72, 255)) for m in mark_frames()]))
    rows.append(('impact fx  %s' % FX.IMPACT_FX_TIMES, [_on(m, (86, 128, 72, 255)) for m in impact_fx_frames()]))
    rows.append(('josh_summon  %s' % J.SUMMON_TIMES, [_on(m, (96, 100, 110, 255)) for m in josh_frames('summon')]))
    rows.append(('josh_command  %s' % J.COMMAND_TIMES, [_on(m, (96, 100, 110, 255)) for m in josh_frames('command')]))
    pad = 4
    W = max(sum(t.width + pad for t in tiles) for _, tiles in rows) * scale
    Hh = sum((max(t.height for t in tiles) + 12) for _, tiles in rows) * scale
    out = Image.new('RGBA', (W, Hh), (20, 20, 24, 255))
    d = ImageDraw.Draw(out)
    y = 0
    for name, tiles in rows:
        d.text((4, y + 2), name, fill=(235, 235, 235, 255))
        x = 0
        for t in tiles:
            out.alpha_composite(t.resize((t.width * scale, t.height * scale), Image.NEAREST), (x, y + 12 * scale))
            x += (t.width + pad) * scale
        y += (max(t.height for t in tiles) + 12) * scale
    out.save(out_path)
    return out_path


def _on(im, bg):
    t = Image.new('RGBA', im.size, bg)
    t.alpha_composite(im)
    return t


def build_all(out_dir):
    paths = []
    paths.append(contact_sheet(os.path.join(out_dir, 'josh_hands_sheet.png')))
    m = mock_rest('A')
    p = os.path.join(out_dir, 'mock_1_rest.png'); m.save(p); paths.append(p)
    m = mock_attack('A')
    p = os.path.join(out_dir, 'mock_2_attack.png'); m.save(p); paths.append(p)
    m = mock_brief('A')
    p = os.path.join(out_dir, 'mock_3_brief.png'); m.save(p); paths.append(p)
    for fn, name in ((mock_rest, 'mock_1_rest_takeB.png'), (mock_brief, 'mock_3_brief_takeB.png')):
        m = fn('B')
        p = os.path.join(out_dir, 'takeB', name); m.save(p); paths.append(p)
    paths.append(gif_portal(os.path.join(out_dir, 'gif_1_portal_open_loop.gif')))
    paths.append(gif_summon(os.path.join(out_dir, 'gif_2_summon_flurry_form.gif')))
    paths.append(gif_slam(os.path.join(out_dir, 'gif_3_hover_windup_drop_impact.gif')))
    paths.append(gif_slam(os.path.join(out_dir, 'gif_4_parry_shatter_reform.gif'), parry=True))
    return paths
