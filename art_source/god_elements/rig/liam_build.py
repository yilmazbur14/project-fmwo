"""Liam's full puppet set: the sheets (treated), their Avatar strips, the aura loop and the hooks. Pure: returns
images and data; export_full.py writes them (into the scratch stage only)."""
import math
from ge_common import *
import le_rig as R
import le_poses as P
import liam_full as LF
import liam_puppet as LP
import bixby_puppet as BP          # detached(): the in-cell FX motes and arcs

FW = FH = 96
SHEET_REL = 'Liam/Elements/liam_%s.png'


def rot_point(p, deg, pivot, out_pivot):
    """Where le_parts.rotsprite puts source texel p (its inverse map, solved forward)."""
    a = math.radians(deg)
    c, s_ = math.cos(a), math.sin(a)
    dx, dy = p[0] + 0.5 - pivot[0], p[1] + 0.5 - pivot[1]
    return (int(math.floor(c * dx + s_ * dy + out_pivot[0])), int(math.floor(-s_ * dx + c * dy + out_pivot[1])))


STAND_BACK = (47, 68)          # the standing rig's back (key (31, 36) + body (16, 32))
# the tumbling frames the tracker cannot read: their back carried through the same rotation the rig draws them with
BACK_BY_HAND = {
    'fall': {0: rot_point(STAND_BACK, -18, (48, 90), (50, 92)), 1: rot_point(STAND_BACK, -110, (48, 62), (48, 58)),
             2: rot_point(STAND_BACK, -90, (48, 64), (48, 78))},
    'defeat': {3: rot_point(STAND_BACK, -45, (48, 70), (48, 76)), 4: rot_point(STAND_BACK, -90, (48, 64), (48, 78))},
}


def boss_at(bx, by, name, radius=16):
    b = shift_boss(JB.BOSSES['liam'], bx, by, name)
    # his dazed swirl lenses and sweat glints are his blue: the puppet's blue is the rune glow
    b.table = dict(b.table)
    b.table['8FB3E8'] = ('eye', 'G1')
    b.table['3D6FD6'] = ('eye', 'G2')
    for p in b.parts.values():
        p['radius'] = max(p.get('radius', 10), radius)
    return b


def key_at(bx, by, w=FW, h=FH):
    return pad(C.frame('Liam/liam.png', 64, 64, 0), w, h, bx, by)


def _edge(sil):
    air = np.pad(~sil, 1, constant_values=True)
    return sil & (air[:-2, 1:-1] | air[2:, 1:-1] | air[1:-1, :-2] | air[1:-1, 2:])


def _dilate(m, n=1):
    for _ in range(n):
        p = np.pad(m, 1)
        m = p[1:-1, 1:-1] | p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
    return m


def avatar_target(body, src_cv, info):
    """The approved Avatar State painted on a treated frame (a copy): blazing lenses, the arrow on his crown and
    brow, a burning line down each forearm wrap, and an open mouth glowing. Never on the silhouette edge."""
    a = body.copy()
    sil = a[:, :, 3] > 0
    edge = _edge(sil)
    hdy = info['head_dy']

    def put(x, y, c):
        if 0 <= x < FW and 0 <= y < FH and sil[y, x] and not edge[y, x]:
            a[y, x] = c

    def Bh(x, y):
        return (int(x + LF.AV_BX), int(y + LF.AV_BY + hdy))
    for lens in (P.LENS_FAR, P.LENS_NEAR):
        xs = sorted({x for x, y in lens})
        for (x, y) in lens:
            put(*Bh(x, y), HOT if (y == 15 and xs[0] < x < xs[-1]) else G1)
    for y in range(2, 9):
        put(*Bh(25, y), G1)
    for (x, y, c) in ((23, 9, G2), (24, 9, G1), (25, 9, HOT), (26, 9, G1), (27, 9, G2),
                      (24, 10, G1), (25, 10, HOT), (26, 10, G1), (25, 11, G1), (25, 12, G1)):
        put(*Bh(x, y), c)
    for side in ('far', 'near'):
        (ex, ey), (wx, wy) = info['fore'][side]
        p0 = (ex + 0.12 * (wx - ex) + LF.AV_BX, ey + 0.12 * (wy - ey) + LF.AV_BY)
        p1 = (ex + 0.98 * (wx - ex) + LF.AV_BX, ey + 0.98 * (wy - ey) + LF.AV_BY)
        pts = [p for p in LP.line_px(p0, p1) if 0 <= p[0] < FW and 0 <= p[1] < FH and sil[p[1], p[0]] and not edge[p[1], p[0]]]
        for (x, y) in pts:
            put(x, y, G1)
        if pts:
            put(*pts[-1], HOT)
    if isinstance(info['mouth'], str) and info['mouth'] in ('shout', 'big', 'blow'):
        for y in range(19, 28):
            for x in range(15, 41):
                fx, fy = Bh(x, y)
                if 0 <= fy < FH:
                    ch = src_cv[fy, fx]
                    if ch == 'N':
                        put(fx, fy, G2)
                    elif ch == 'n':
                        put(fx, fy, G1)
    return a


def avatar_strip(body, target):
    """ADDITIVE: what the glow adds over the body to reach the approved look (target - body, per channel, never
    below 0), plus a 2-texel rim of light outside his silhouette (G1 against him, G2 beyond)."""
    s = np.zeros_like(body)
    diff = target[:, :, :3].astype(int) - body[:, :, :3].astype(int)
    changed = (target != body).any(axis=2)
    add = np.clip(diff, 0, 255).astype(np.uint8)
    s[changed, :3] = add[changed]
    s[changed, 3] = 255
    sil = body[:, :, 3] > 0
    r1 = _dilate(sil, 1) & ~sil
    r2 = _dilate(sil, 2) & ~_dilate(sil, 1)
    s[r2] = G2
    s[r1] = G1
    s[(s[:, :, :3] == 0).all(axis=2)] = 0
    return s


def build_avatar_sheet(name, fn):
    b = boss_at(LF.AV_BX, LF.AV_BY, 'liam_avatar')
    for t in b.tatter:
        t['rows'] = (LF.AV_BY + 56, LF.AV_BY + 68)
    key = key_at(LF.AV_BX, LF.AV_BY)
    frames = fn()
    rel = SHEET_REL % name
    hooks = {}
    for f, (cv, fb, ff, info) in enumerate(frames):
        dy = info['head_dy'] - 0
        h = {}
        for side, hname in (('far', 'wrist_l'), ('near', 'wrist_r')):
            (ex, ey), (wx, wy) = info['fore'][side]
            h[hname] = ((int(round(ex + 0.78 * (wx - ex) + LF.AV_BX)), int(round(ey + 0.78 * (wy - ey) + LF.AV_BY))), None)
        h['knee_l'] = ((37, 76 + info['dy']), JB.RING_S)
        h['knee_r'] = ((57, 77 + info['dy']), JB.RING_S)
        hooks[f] = h
    b.frame_data = {rel: {'hooks': hooks}}
    out, strips, infos = [], [], []
    for f, (cv, fb, ff, info) in enumerate(frames):
        src = R.to_rgba(cv)
        im, tinfo = C.treat(b, src, TAKE, key_src=key, sheet_rel=rel, frame_no=f)
        body = np.array(im)
        target = avatar_target(body, cv, info)
        strip_ = avatar_strip(body, target)
        full = Image.new('RGBA', (FW, FH), (0, 0, 0, 0))
        full.alpha_composite(Image.fromarray(R.to_rgba(fb), 'RGBA'))
        full.alpha_composite(Image.fromarray(body, 'RGBA'))
        full.alpha_composite(Image.fromarray(R.to_rgba(ff), 'RGBA'))
        tinfo['src'] = src
        tinfo['body'] = body
        tinfo['fx_px'] = int(((R.to_rgba(fb)[:, :, 3] > 0) | (R.to_rgba(ff)[:, :, 3] > 0)).sum())
        tinfo['frame_info'] = info
        out.append(np.array(full))
        strips.append(strip_)
        infos.append(tinfo)
    return out, strips, infos


def build_plain_sheet(name):
    frames, jinfo = LF.plain_frames(name)
    rel = SHEET_REL % name
    if name == 'juggle':
        b = boss_at(32, 32, 'liam_juggle')
        b.parts, b.overlays, b.hooks, b.tatter, b.regions = {}, [], {}, [], []
        key = key_at(32, 32, 128, 96)
    else:
        b = boss_at(LF.ST_BX, LF.ST_BY, 'liam_plain')
        key = key_at(LF.ST_BX, LF.ST_BY)
        if name in BACK_BY_HAND:
            b.frame_data = {rel: {'hooks': {f: {'back': (p, None)} for f, p in BACK_BY_HAND[name].items()}}}
    out, infos = [], []
    for f, cv in enumerate(frames):
        src = R.to_rgba(cv)
        fx = BP.detached(src) if (src[:, :, 3] > 0).any() else set()
        b.fx_specks = fx
        im, tinfo = C.treat(b, src, TAKE, key_src=key, sheet_rel=rel, frame_no=f)
        tinfo['src'] = src
        tinfo['fx'] = fx
        out.append(np.array(im))
        infos.append(tinfo)
    # the roster's all-or-nothing rule: a ring only where the tracker placed it on every frame of the sheet
    if name != 'juggle':
        everywhere = set.intersection(*[set(i.get('rings_drawn', [])) for i in infos]) if infos else set()
        if any(set(i.get('rings_drawn', [])) != everywhere for i in infos):
            out, infos2 = [], []
            for f, cv in enumerate(frames):
                src = R.to_rgba(cv)
                b.fx_specks = infos[f]['fx']
                skip = set(infos[f].get('rings_drawn', [])) - everywhere
                im, tinfo = C.treat(b, src, TAKE, key_src=key, sheet_rel=rel, frame_no=f, skip_rings=tuple(skip))
                tinfo['src'], tinfo['fx'] = src, infos[f]['fx']
                tinfo['rings_left_off_sheet'] = sorted(skip)
                out.append(np.array(im))
                infos2.append(tinfo)
            infos = infos2
    return out, infos, jinfo


def audit(frames, infos, kind):
    probs = []
    pal = {tuple(v) for v in PUP.values()}
    for f, (a, info) in enumerate(zip(frames, infos)):
        body = info.get('body', a)
        src = info['src']
        if ((body[:, :, 3] > 0) != (src[:, :, 3] > 0)).any():
            probs.append('f%d silhouette differs from its source pose' % f)
        if ((a[:, :, 3] > 0) & (a[:, :, 3] < 255)).any():
            probs.append('f%d semi-alpha' % f)
        fx = info.get('fx', set())
        cols = {tuple(body[y, x]) for y, x in zip(*np.nonzero(body[:, :, 3] > 0)) if (x, y) not in fx}
        if cols - pal:
            probs.append('f%d off-palette %s' % (f, sorted(cols - pal)[:3]))
        for k in ('gaps', 'lone', 'holes', 'bad_keys'):
            if info['lint'][k]:
                probs.append('f%d lint %s %d %s' % (f, k, len(info['lint'][k]), info['lint'][k][:3]))
        if info['unknown']:
            probs.append('f%d unmapped %s' % (f, info['unknown']))
    return probs


def back_points(infos):
    return [None if i['hooks'].get('back') is None else tuple(int(v) for v in i['hooks']['back']) for i in infos]


# ------------------------------------------------------------------ the aura loop (6 frames, silhouette-free)
AURA = 128


def aura_loop(n=6):
    """The orbit round his waist, independent of his pose: the wind band and the four element motes, a sixth of
    a turn a frame. back = the far half, front = the near half. Cell 128x128; its centre corner (64, 64) is his
    float pivot, body corner (48, 56) of the Avatar sheets: the body cell's top-left is aura (16, 8)."""
    import liam_aura as LA2
    backs, fronts = [], []
    rx, ry, tilt = 50, 13, -0.10
    for k in range(n):
        back = np.zeros((AURA, AURA, 4), np.uint8)
        front = np.zeros((AURA, AURA, 4), np.uint8)
        cy = 64 + 6
        phase = k / n
        for band in range(2):
            for i in range(900):
                t = 2 * math.pi * i / 900
                if math.sin(t * 3 + phase * 2 * math.pi) < -0.82:
                    continue
                ex, ey = (rx - band) * math.cos(t), (ry - band * 0.5) * math.sin(t)
                x = int(math.floor(64 + ex * math.cos(tilt) - ey * math.sin(tilt) + 0.5))
                y = int(math.floor(cy + ex * math.sin(tilt) + ey * math.cos(tilt) + 0.5))
                glint = math.sin(t * 5 - phase * 2 * math.pi * 1.25) > 0.8
                if math.sin(t) > 0:
                    front[y, x] = LA2.E.AIR['W'] if (glint or band == 1) else LA2.E.AIR['s']
                else:
                    back[y, x] = LA2.E.AIR['p'] if glint else (LA2.E.AIR['s'] if band == 1 else LA2.E.AIR['v'])
        th0 = math.radians(25) + 2 * math.pi * phase / 4      # a quarter turn per loop: the 4 motes trade places
        for i, name in enumerate(LA2.ORDER):
            t = th0 + i * math.pi / 2
            ex, ey = (rx + 2) * math.cos(t), (ry + 2) * math.sin(t)
            x = 64 + ex * math.cos(tilt) - ey * math.sin(tilt)
            y = cy + ex * math.sin(tilt) + ey * math.cos(tilt) - 2
            LA2.blit(front if math.sin(t) > 0 else back, LA2.mote(name), x, y)
        backs.append(back)
        fronts.append(front)
    return backs, fronts


# ------------------------------------------------------------------ soft extras: the Avatar State flaring on / off
def _scaled(strip_, k):
    s = strip_.copy()
    s[:, :, :3] = (s[:, :, :3].astype(float) * k).astype(np.uint8)
    s[(s[:, :, :3] == 0).all(axis=2)] = 0
    return s


def _ring(body, n, c, dither=False):
    sil = body[:, :, 3] > 0
    r = _dilate(sil, n) & ~_dilate(sil, n - 1)
    out = np.zeros_like(body)
    if dither:
        yy, xx = np.mgrid[0:body.shape[0], 0:body.shape[1]]
        r &= (xx + yy) % 2 == 0
    out[r] = c
    return out


def _over(a, b):
    out = a.copy()
    m = b[:, :, 3] > 0
    out[m] = b[m]
    return out


def avatar_on_off(body0, strip0, eye_px):
    """On channel frame 0's body: ON (5) - a faint rim, the eyes catch, a flash burst, the eyes snapped white, the
    held glow; OFF (4) - the burst, the glow at half, the eyes guttering, a last dim rim. Additive, like the strips."""
    eyes = np.zeros_like(strip0)
    for (x, y) in eye_px:
        eyes[y, x] = strip0[y, x]
    white = eyes.copy()
    white[(eyes[:, :, 3] > 0)] = (255, 255, 255, 255)
    burst = _over(_over(strip0, _ring(body0, 3, HOT)), _ring(body0, 4, G1, dither=True))
    on = [_scaled(_ring(body0, 1, G2), 1.0), _over(_scaled(_ring(body0, 1, G2), 1.0), eyes), burst,
          _over(strip0, white), strip0]
    off = [burst, _scaled(strip0, 0.5), _over(_scaled(_ring(body0, 1, G2), 0.6), _scaled(eyes, 0.6)),
           _scaled(_ring(body0, 1, G2, dither=True), 0.5)]
    return on, off


def lens_pixels(info):
    hdy = info['head_dy']
    return [(int(x + LF.AV_BX), int(y + LF.AV_BY + hdy)) for (x, y) in (P.LENS_FAR + P.LENS_NEAR)]
