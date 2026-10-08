"""PORTAL MONTE previews: 1920x1080 mocks on a real capture of Josh's own fight (the arena, ropes and HUD
after the summon; Josh, his hands, his gates and the player's sprite hidden, so all of them are drawn
here and can move) and a GIF of the dive, the deal, a fake's burst and the real one's burst, parried.

Everything is placed by the Monte plan's numbers (scratchpad PLAN_portal_monte.md): the gates by its
placement rules (three at 120 degrees round the locked player, radius 320/280/240, 24 rotations, the
fairness checks), the beats on its clock (DIVE 0.50, DEAL 0.25, OPEN 0.30, SHOW 0.36, DASH 0.18, the
0.62 cadence), the reused art from Assets (the strong parry badge, Carter's pale X, the deal card, the
parry flash, his idle / hit / recovery / shadow), read only.
"""
import math
import os

from PIL import Image, ImageDraw

import jh_lib as H
import jh_anims as A
import jh_portal as PT
import jh_small_gate as SG
import jh_monte_josh as M
import jh_gun_previews as GP

ROOT = H.ROOT
CAP = os.path.join(H.SCRATCH, 'cap_monte')
S3 = 3
PLAYER = (900, 800)                  # the locked player's body (drawn here; the capture has no player)
HURT = (PLAYER[0], PLAYER[1] + 1.5)  # the player's hurtbox centre
JOSH_HOME = (959, 700)
BIG = {'left': (575, 270), 'right': (1345, 270)}
REST = {s: (p[0], p[1] + 170) for s, p in BIG.items()}
ROPES = (113, 114, 1692, 853)
HUD = [(720, 33, 480, 148), (10, 842, 406, 229), (1371, 946, 537, 126)]
VIEW = (1920, 1080)
FLOOR_DROP_PX = SG.CFG['FLOOR_DROP'] * S3
GATE_REACH = 21                      # the small gate's drawn radius, texels (card tips + keyline)
BADGE_GAP = 6                        # px between the gate's top and the badge's tip

_cache = {}


def load(rel):
    if rel not in _cache:
        _cache[rel] = Image.open(os.path.join(ROOT, rel)).convert('RGBA')
    return _cache[rel]


def strip_frames(rel, fw, fh=None):
    key = ('strip', rel, fw)
    if key not in _cache:
        im = load(rel)
        fh = fh or im.height
        _cache[key] = [im.crop((i * fw, 0, i * fw + fw, fh)) for i in range(im.width // fw)]
    return _cache[key]


def bg():
    if 'bg' not in _cache:
        _cache['bg'] = Image.open(os.path.join(CAP, 'monte_bg.png')).convert('RGBA')
    return _cache['bg']


def _at(times, t, loop=False):
    return GP._at(times, t, loop)


# ------------------------------------------------------------------ art as images (built here, from the rigs)

def small_gate(seq):
    key = ('small', seq)
    if key not in _cache:
        fw, fh = SG.CFG['FW'], SG.CFG['FH']
        _cache[key] = [(H.to_image(b, fw, fh), H.to_image(g, fw, fh, H.GLOW)) for b, g in SG.seq_frames(seq)]
    return _cache[key]


def big_gate(seq):
    key = ('big', seq)
    if key not in _cache:
        _cache[key] = [(H.to_image(b, PT.PW, PT.PH), H.to_image(g, PT.PW, PT.PH, H.GLOW)) for b, g in PT.seq_frames(seq)]
    return _cache[key]


def hand(clip):
    key = ('hand', clip)
    if key not in _cache:
        out = []
        for fr in A.clip_frames(clip):
            px, gl = A.render_frame(fr)
            out.append((H.to_image(px, A.FW, A.FH), H.to_image(gl, A.FW, A.FH, H.GLOW)))
        _cache[key] = out
    return _cache[key]


def josh_sheet(name):
    key = ('josh', name)
    if key not in _cache:
        if name == 'slash':
            _cache[key] = [H.to_image(M.slash_frame(i), M.SLASH_FW, M.SLASH_FH) for i in range(4)]
        elif name == 'dive':
            _cache[key] = [H.to_image(M.dive_frame(i), 80, 80) for i in range(5)]
        elif name == 'emerge':
            _cache[key] = [H.to_image(M.emerge_frame(i), 80, 80) for i in range(len(M.EMERGE_TIMES))]
        elif name == 'scatter':
            _cache[key] = [H.to_image(M.scatter_frame(i), 96, 96) for i in range(6)]
        else:
            _cache[key] = strip_frames('Assets/Characters/Josh/josh_%s.png' % name, 80)
    return _cache[key]


# ------------------------------------------------------------------ placement (the plan's rules)

def _rect_clear(r, pad):
    x, y, w, h = r
    for (hx, hy, hw, hh) in HUD:
        if x < hx + hw + pad and x + w > hx - pad and y < hy + hh + pad and y + h > hy - pad:
            return False
    return True


def gate_rect(floor):
    """The drawn gate plus its mark, in px: the frame round the opening and the tallest badge over it."""
    ox, oy = floor[0], floor[1] - FLOOR_DROP_PX
    half = SG.CFG['FW'] * S3 / 2.0
    top = oy - GATE_REACH * S3 - BADGE_GAP - 36 * S3
    return (ox - half, top, 2 * half, oy + half - top)


def fits(floor, player):
    if math.hypot(floor[0] - player[0], floor[1] - player[1]) < 220:
        return False
    rx, ry, rw, rh = ROPES
    if not (rx + 40 <= floor[0] <= rx + rw - 40 and ry + 40 <= floor[1] <= ry + rh - 40):
        return False
    x, y, w, h = gate_rect(floor)
    if x < 8 or y < 8 or x + w > VIEW[0] - 8 or y + h > VIEW[1] - 8:
        return False
    return _rect_clear((x, y, w, h), 12)


def place(player, prev=None):
    """Three floor points round the player: the first rotation (from straight up, 15 degree steps) and
    radius (320, 280, 240) where all three fit and stand 150 px apart; a new round's rotation at least
    40 degrees from the last whenever one fits. Returns (rotation, [floor points])."""
    for radius in (320, 280, 240):
        for step in range(24):
            rot = -90 + 15 * step
            if prev is not None and abs(((rot - prev + 180) % 360) - 180) < 40:
                continue
            pts = [(player[0] + radius * math.cos(math.radians(rot + 120 * k)),
                    player[1] + radius * math.sin(math.radians(rot + 120 * k))) for k in range(3)]
            if all(fits(p, player) for p in pts) and all(
                    math.hypot(a[0] - b[0], a[1] - b[1]) >= 150 for i, a in enumerate(pts) for b in pts[i + 1:]):
                return rot, pts
    raise RuntimeError('no placement')


# ------------------------------------------------------------------ drawing

def draw(canvas, im, pivot, at, flip=False, glow=None, alpha=1.0, scale=S3):
    if scale == S3:
        return GP.draw_at(canvas, im, pivot, at, flip=flip, glow=glow, alpha=alpha)
    # a code-scaled sprite (the dive's shrink): nearest-neighbour at any size, about the pivot
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
        pivot = (im.width - pivot[0], pivot[1])
    w, h = max(1, int(round(im.width * scale))), max(1, int(round(im.height * scale)))
    b = im.resize((w, h), Image.NEAREST)
    if alpha < 1.0:
        b.putalpha(b.getchannel('A').point(lambda v: int(v * alpha)))
    GP.paste(canvas, b, at[0] - pivot[0] * scale, at[1] - pivot[1] * scale)
    return canvas


def draw_small_gate(canvas, seq, i, floor):
    back, glow = small_gate(seq)[i]
    at = (floor[0], floor[1] - FLOOR_DROP_PX)
    return draw(canvas, back, SG.CFG['PIVOT'], at, glow=glow)


def draw_big_gate(canvas, side, seq, i):
    back, glow = big_gate(seq)[i]
    return draw(canvas, back, PT.PIVOT, BIG[side], flip=(side == 'left'), glow=glow)


def draw_hand(canvas, side, pair, at=None):
    im, gl = pair
    return draw(canvas, im, (A.PX, A.PY), at or REST[side], flip=(side == 'left'), glow=gl)


def player_frame(col, row):
    sheet = load('Assets/Characters/MainPlayer/player_4dir_sheet.png')
    return sheet.crop((col * 32, row * 32, col * 32 + 32, row * 32 + 32))


def facing_row(toward, frm=PLAYER):
    dx, dy = toward[0] - frm[0], toward[1] - frm[1]
    if abs(dx) >= abs(dy):
        return 3 if dx > 0 else 2
    return 0 if dy > 0 else 1


def draw_player(canvas, row, col=0):
    return draw(canvas, player_frame(col, row), (16, 16), PLAYER)


def red_badge(t):
    frames = strip_frames('Assets/Effects/parry_tell_strong.png', 48)
    return frames[_at([0.07, 0.07, 0.08, 0.08, 0.07, 0.07], t, loop=True)]


def pale_x(t):
    frames = strip_frames('Assets/Characters/Carter/Demon/demon_feint.png', 24)
    if t < 0.05:
        return frames[0]
    if t < 0.09:
        return frames[1]
    return frames[2]                       # held steady for the whole read


def draw_mark(canvas, kind, floor, t, alpha=1.0):
    top = floor[1] - FLOOR_DROP_PX - GATE_REACH * S3 - BADGE_GAP
    if kind == 'red':
        return draw(canvas, red_badge(t), (24, 36), (floor[0], top), alpha=alpha)
    return draw(canvas, pale_x(t), (12, 12), (floor[0], top - 12 * S3), alpha=alpha)


def figure_path(floor, hurt=HURT):
    """Where the figure's feet start (the gate's floor point) and stop (its blade's contact point on the
    player's hurtbox centre), and which way it faces."""
    face_right = hurt[0] >= floor[0]
    cx, cy = M.SLASH_CONTACT
    dx = cx * S3 if face_right else -cx * S3
    stop = (hurt[0] - dx, hurt[1] - cy * S3)
    return floor, stop, face_right


def draw_figure(canvas, i, feet, face_right, alpha=1.0):
    im = josh_sheet('slash')[i]
    return draw(canvas, im, M.SLASH_FEET, feet, flip=not face_right, alpha=alpha)


def draw_josh(canvas, name, i, feet, flip=False, scale=S3, alpha=1.0):
    im = josh_sheet(name)[i]
    return draw(canvas, im, (40, 79), feet, flip=flip, scale=scale, alpha=alpha)


def draw_shadow(canvas, floor, height_px, alpha=0.38):
    frames = strip_frames('Assets/Characters/Josh/Cards/josh_shadow.png', 80)
    k = min(3, int(height_px / 60.0))
    im = frames[k]
    return draw(canvas, im, (40, 12), (floor[0], floor[1] - 9), alpha=alpha)


def draw_deal_card(canvas, t, frm, to):
    frames = strip_frames('Assets/Characters/Josh/Cards/card_projectile.png', 24)
    u = max(0.0, min(1.0, t))
    x = frm[0] + (to[0] - frm[0]) * u
    y = frm[1] + (to[1] - frm[1]) * u - 150 * math.sin(math.pi * u)
    return draw(canvas, frames[int(t / 0.05) % len(frames)], (12, 12), (x, y))


def label(canvas, text, xy=(14, 6)):
    GP.label(canvas, text, xy)


# ------------------------------------------------------------------ the mocks

ROT, FLOORS = None, None


def layout():
    global ROT, FLOORS
    if FLOORS is None:
        ROT, FLOORS = place(PLAYER)
    return ROT, FLOORS


def base_scene(canvas=None, hand_frame=0, gates=((0, 'loop', 0), (1, 'loop', 3), (2, 'loop', 6))):
    """The fight during the Monte: big gates looping, hands resting, Josh gone, three small gates open."""
    c = (canvas or bg()).copy()
    for side in ('left', 'right'):
        c = draw_big_gate(c, side, 'loop', (hand_frame * 2) % 12)
        c = draw_hand(c, side, hand('hover')[hand_frame % 6])
    return c


def sorted_draw(c, items):
    """items: (sort y, fn(canvas) -> canvas), drawn back to front."""
    for _, fn in sorted(items, key=lambda t: t[0]):
        c = fn(c)
    return c


def mock_mark(kind, which):
    rot, floors = layout()
    c = base_scene()
    items = []
    for k, fl in enumerate(floors):
        items.append((fl[1], lambda cv, fl=fl, k=k: draw_small_gate(cv, 'loop', (k * 3) % 8, fl)))
    row = facing_row(floors[which])
    items.append((PLAYER[1] + 42, lambda cv: draw_player(cv, row)))
    c = sorted_draw(c, items)
    c = draw_mark(c, kind, floors[which], 0.2)
    return c


def mock_contact():
    """The real one at its CONTACT frame on the player, the red badge still up (it clears on contact),
    the player's guard up for the parry."""
    rot, floors = layout()
    c = base_scene(hand_frame=2)
    red = REAL
    start, stop, face_right = figure_path(floors[red])
    items = []
    for k, fl in enumerate(floors):
        seq, i = ('loop', (k * 3) % 8) if k != red else ('burst', 2)
        items.append((fl[1], lambda cv, fl=fl, seq=seq, i=i: draw_small_gate(cv, seq, i, fl)))
    row = facing_row(floors[red])
    items.append((PLAYER[1] + 42, lambda cv: draw_player(cv, row, col=9)))
    items.append((stop[1], lambda cv: draw_figure(cv, 2, stop, face_right)))
    c = sorted_draw(c, items)
    c = draw_mark(c, 'red', floors[red], 0.3)
    return c


# ------------------------------------------------------------------ the GIF: dive, deal, a fake, the real one parried

T_LEAD = 0.45                     # Josh idling before the Monte starts
T_DIVE = sum(M.DIVE_TIMES)        # 0.50
T_DEAL = 0.25
T_OPEN = sum(SG.SEQS['open'])     # 0.30
T_SHOW, T_DASH, CADENCE = 0.36, 0.18, 0.62
T_STAGGER = 0.25                  # knocked back 150 px toward his gate
PARRY_HOLD = 0.08                 # the hit-stop on the parry
FAKE, REAL, SPARE = 1, 0, 2       # the gates: the fake bursts first, then the real one; the third is left
ORDER = (FAKE, REAL)              # the bursts in time


def _smooth(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def dive_side():
    """The big gate nearer to Josh by x, the left one on a tie (the plan)."""
    dl, dr = abs(BIG['left'][0] - JOSH_HOME[0]), abs(BIG['right'][0] - JOSH_HOME[0])
    return 'left' if dl <= dr else 'right'


def beats():
    t_dive = T_LEAD
    t_deal = t_dive + T_DIVE
    t_open = t_deal + T_DEAL
    marks = {g: t_deal + 0.55 + n * CADENCE for n, g in enumerate(ORDER)}
    contact = {g: marks[g] + T_SHOW + T_DASH for g in ORDER}
    return dict(dive=t_dive, deal=t_deal, open=t_open, marks=marks, contact=contact,
                parry=contact[REAL], after=contact[REAL] + PARRY_HOLD)


def _dive_draw(t, b, side):
    """Josh in the air on his way into the big gate, as the plan moves him: his floor point slides to
    under the gate, his height rises so his body's middle meets the opening, and over the last 0.15 s
    he shrinks to 0.3 and fades out."""
    u = (t - b['dive']) / T_DIVE
    e = _smooth(u)
    target = (BIG[side][0], BIG[side][1] + 200)
    floor = (JOSH_HOME[0] + (target[0] - JOSH_HOME[0]) * e, JOSH_HOME[1] + (target[1] - JOSH_HOME[1]) * e)
    k = _at(M.DIVE_TIMES, t - b['dive'])
    shrink = min(1.0, max(0.0, (t - (b['dive'] + T_DIVE - 0.15)) / 0.15))
    sc = S3 * (1.0 - 0.7 * shrink)
    cy = M.DIVE_CENTRE[1]
    rise = (floor[1] - BIG[side][1]) - (79 - cy) * sc
    height = max(0.0, rise * _smooth((u - 0.2) / 0.8))
    feet = (floor[0], floor[1] - height)

    def fn(cv):
        cv = draw_shadow(cv, floor, height, alpha=0.38 * (1.0 - 0.45 * min(1.0, height / 180.0)))
        return draw_josh(cv, 'dive', k, feet, flip=(side == 'left'), scale=sc, alpha=1.0 - shrink)
    return floor[1], fn


def scene(t):
    rot, floors = layout()
    side = dive_side()
    b = beats()
    kinds = {FAKE: 'x', REAL: 'red'}
    c = bg().copy()
    # the backdrop: the big gates (the dive's gate feeds as he goes in) and the resting hands
    for s_ in ('left', 'right'):
        seq, i = 'loop', int(t / 0.1) % 12
        t_feed = b['dive'] + T_DIVE - 0.12
        if s_ == side and t_feed <= t < t_feed + 0.10:
            seq, i = 'feed', _at(PT.SEQS['feed'], t - t_feed)
        c = draw_big_gate(c, s_, seq, i)
    for s_ in ('left', 'right'):
        if b['deal'] <= t < b['deal'] + 0.15:
            pair = hand('windup')[_at(A.CLIPS['windup'], t - b['deal'])]
        else:
            pair = hand('hover')[_at(A.CLIPS['hover'], t, loop=True)]
        c = draw_hand(c, s_, pair)
    items = []
    if t < b['dive']:
        i = _at([0.15] * 4, t, loop=True)
        items.append((JOSH_HOME[1], lambda cv: draw_josh(draw_shadow(cv, JOSH_HOME, 0), 'idle', i, JOSH_HOME)))
    elif t < b['deal']:
        items.append(_dive_draw(t, b, side))
    # the deal: three cards flicked from the hands, one to each spot, on raised arcs
    if b['deal'] + 0.1 <= t < b['open']:
        u = (t - b['deal'] - 0.1) / (T_DEAL - 0.1)
        for fl in floors:
            hs = 'left' if fl[0] < 960 else 'right'
            c = draw_deal_card(c, u, (REST[hs][0], REST[hs][1] - 40), (fl[0], fl[1] - FLOOR_DROP_PX))
    # the small gates
    close_from = {FAKE: b['contact'][FAKE], REAL: b['after'], SPARE: b['after']}
    for k, fl in enumerate(floors):
        if t < b['open']:
            continue
        seq, i = 'loop', _at(SG.SEQS['loop'], t - b['open'] - T_OPEN + k * 0.3, loop=True)
        if t < b['open'] + T_OPEN:
            seq, i = 'open', _at(SG.SEQS['open'], t - b['open'])
        elif t >= close_from[k]:
            tc = t - close_from[k]
            if tc >= sum(SG.SEQS['close']):
                continue
            seq, i = 'close', _at(SG.SEQS['close'], tc)
        elif k in kinds and b['marks'][k] + T_SHOW <= t < b['marks'][k] + T_SHOW + sum(SG.SEQS['burst']):
            seq, i = 'burst', _at(SG.SEQS['burst'], t - b['marks'][k] - T_SHOW)
        items.append((fl[1], lambda cv, seq=seq, i=i, fl=fl: draw_small_gate(cv, seq, i, fl)))
    # the figures: the fake bursts out and comes apart at its contact; the real one is parried
    for k in (FAKE, REAL):
        start, stop, fr = figure_path(floors[k])
        t0 = b['marks'][k] + T_SHOW
        if t0 <= t < b['contact'][k]:
            u = (t - t0) / T_DASH
            e = u * u
            feet = (start[0] + (stop[0] - start[0]) * e, start[1] + (stop[1] - start[1]) * e)
            i = 0 if t - t0 < M.SLASH_TIMES[0] else 1
            items.append((feet[1], lambda cv, i=i, feet=feet, fr=fr: draw_figure(cv, i, feet, fr)))
        elif k == FAKE and b['contact'][k] <= t < b['contact'][k] + sum(M.SCATTER_TIMES):
            i = _at(M.SCATTER_TIMES, t - b['contact'][k])
            cx, cy = M.SLASH_CENTRE
            at = (stop[0] + (cx if fr else -cx) * S3, stop[1] + cy * S3)
            items.append((stop[1], lambda cv, i=i, at=at: draw(cv, josh_sheet('scatter')[i], M.SCATTER_PIVOT, at)))
        elif k == REAL and b['contact'][k] <= t < b['after']:
            items.append((stop[1], lambda cv, fr=fr, stop=stop: draw_figure(cv, 2, stop, fr)))
        elif k == REAL and t >= b['after']:
            gx, gy = floors[k][0] - stop[0], floors[k][1] - stop[1]
            gl = math.hypot(gx, gy) or 1.0
            u = _smooth((t - b['after']) / T_STAGGER)
            feet = (stop[0] + gx / gl * 150 * u, stop[1] + gy / gl * 150 * u)
            tt = t - b['after']
            if tt < 0.19:
                name, i = 'hit', _at([0.07, 0.12], tt)
            else:
                name, i = 'recovery', _at([0.19] * 4, tt - 0.19, loop=True)
            items.append((feet[1], lambda cv, name=name, i=i, feet=feet, fr=fr:
                          draw_josh(draw_shadow(cv, feet, 0), name, i, feet, flip=not fr)))
    # the player, locked, turned to each gate as it lights, the guard up for the parry
    look = None
    for k in (FAKE, REAL):
        if t >= b['marks'][k]:
            look = floors[k]
    row = facing_row(look) if look else 0
    col = 9 if b['parry'] - 0.12 <= t < b['after'] + 0.25 else 0
    items.append((PLAYER[1] + 42, lambda cv: draw_player(cv, row, col)))
    c = sorted_draw(c, items)
    # the marks, over everything: up from the SHOW to the contact, then a 0.05 s fade
    for k in (FAKE, REAL):
        if b['marks'][k] <= t < b['contact'][k] + 0.05:
            a = 1.0 if t < b['contact'][k] else max(0.0, 1.0 - (t - b['contact'][k]) / 0.05)
            c = draw_mark(c, kinds[k], floors[k], t - b['marks'][k], alpha=a)
    # the strong parry flash on the contact point
    if b['parry'] <= t < b['parry'] + 0.48:
        frames = strip_frames('Assets/Effects/parry_flash_strong.png', 96)
        c = draw(c, frames[_at([0.03, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10], t - b['parry'])], (48, 48), HURT)
    return c


def gif(path, dt=1.0 / 30, downscale=True, t_end=None):
    b = beats()
    t_end = t_end or (b['after'] + T_STAGGER + 0.95)
    frames, durs = [], []
    n = int(round(t_end / dt))
    for k in range(n + 1):
        c = scene(k * dt)
        if downscale:
            c = c.resize((1280, 720), Image.NEAREST)
        frames.append(c.convert('RGB'))
        durs.append(int(round(dt * 1000)))
    durs[-1] = 700
    picks = [frames[int(len(frames) * f)] for f in (0.15, 0.45, 0.6, 0.8)]
    mont = Image.new('RGB', (picks[0].width, picks[0].height * len(picks)))
    for i, p in enumerate(picks):
        mont.paste(p, (0, i * p.height))
    pal = mont.quantize(colors=255, method=Image.MEDIANCUT, dither=Image.NONE)
    q = [f.quantize(palette=pal, dither=Image.NONE) for f in frames]
    q[0].save(path, save_all=True, append_images=q[1:], duration=durs, loop=0, disposal=1, optimize=True)
    return path


# ------------------------------------------------------------------ the contact sheet and the files

GREEN = (104, 150, 76, 255)


def _tile(im, glow=None, bg_=GREEN):
    t = Image.new('RGBA', im.size, bg_)
    if glow is not None:
        t = H.add_glow(t, glow)
    t.alpha_composite(im)
    return t


def contact_sheet(path, scale=3):
    rows = []
    for seq in SG.ORDER:
        tiles = [_tile(b, g) for b, g in small_gate(seq)]
        rows.append(('small gate  %s  %s (back + additive glow)' % (seq, SG.SEQS[seq]), tiles))
    for name, times in (('dive', M.DIVE_TIMES), ('emerge', M.EMERGE_TIMES), ('slash', M.SLASH_TIMES),
                        ('scatter', M.SCATTER_TIMES)):
        rows.append(('josh_%s  %s' % (name if name != 'slash' and name != 'scatter' else 'monte_' + name, times),
                     [_tile(im) for im in josh_sheet(name)]))
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
    out.save(path)
    return path


def build_all(out_dir):
    paths = [contact_sheet(os.path.join(out_dir, 'josh_monte_sheet.png'))]
    for fn, name, text in ((lambda: mock_mark('red', REAL), 'mock_monte_1_red.png',
                            'SHOW: the real one - the strong parry badge over its gate'),
                           (lambda: mock_mark('x', FAKE), 'mock_monte_2_feint.png',
                            'SHOW: a fake - Carter\'s pale X over its gate'),
                           (mock_contact, 'mock_monte_3_contact.png',
                            'CONTACT: the real one\'s cut on the locked player, guard up for the parry')):
        c = fn()
        label(c, text)
        p = os.path.join(out_dir, name)
        c.convert('RGB').save(p)
        paths.append(p)
    paths.append(gif(os.path.join(out_dir, 'gif_monte_dive_deal_burst_parry.gif')))
    return paths
