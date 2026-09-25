"""Every frame of carter_intro (17), carter_look_back (6) and carter_victory (7), on the polish body.

Frame order, count, size and timing are the shipped sheets' (CarterArtLayout reads them). Each frame
is built the way the approved one was - intro_frames.py, combat_look.py and combat_victory.py in
art_source/carter_akuma - with the polish body in place of the old one and the polish flames in place
of the old wisps; the 天 is repainted every frame by the mark rig at the level that frame shipped
with (rig.K holds that rig's own constants, so nothing here restates a level).

INTRO   0..4   materialise  the gathering, then the back view knitting together out of the mark
        5..8   mark flare   levels 0.14 / 0.55 / 1.00 / 0.48, bloom, rim light, floor, peak spokes
        9..13  turn         40 deg back, edge-on pivot, 132 deg, 162 deg, front - arms rising
        14     frame1.build()  the signature pose, verbatim (carter_akuma frame 1)
        15     arms dropping
        16     frame0.build()  verbatim: carter_idle frame 0, so the fight cuts to idle with no blend
LOOK    0      the back view, head forward (look_back_ready holds this)
        1..3   the head comes round over his RIGHT shoulder; 3 arrives
        3..5   the hold: body stone, the aura alive
VICTORY 0      front      1  pivot (126 deg)      2  edge-on      3  back, mark nearly out
        4      IGNITION (full burn, the bell lands here)      5..6  the burn, looping with 4
"""
import math

import rig
from rig import fx, K, sq
import flames
import front
import backview
import frame0
import frame1

W = H = 96
MARK_C_RAW = tuple(K.mark_c_design)      # intro_frames centres its peak spokes on this, unscaled
MARK_C_PX = tuple(K.mark_c_px)           # combat_victory centres its spokes on lib.T(MARK_C)


# ------------------------------------------------------------------ shared pieces

def spokes(px, body, centre, r0, r1, split):
    """Light bursting off the peak: 12 dotted rays, every third step, never over his body."""
    out = dict(px)
    cx, cy = centre
    for n in range(12):
        a = n * math.pi / 6 + 0.26
        for r in range(r0, r1):
            x = int(round(cx + math.cos(a) * r * 0.95))
            y = int(round(cy + math.sin(a) * r * 1.05))
            if not (0 <= x < W and 0 <= y < H):
                break
            if (x, y) in body or (r + n) % 3:
                continue
            out[(x, y)] = 'X' if r < split else 'y'
    return out


def embers_from(sparks, k):
    return [(int(round(x)), int(round(y)), (i + k) % 2 == 0) for i, (x, y) in enumerate(sparks)
            if 1 <= x < W - 1 and 1 <= y < H - 2]


def turned(px, phi, lean_sign, lead_side, lit_amt):
    """The turn's edge light: the leading edge catches it, the trailing edge rolls into shadow."""
    if phi < 175.0:
        px = fx.rim_edge(px, lead_side, 'X', lit_amt)
        px = fx.edge_shade(px, -lead_side, 0.5)
    return px


# ------------------------------------------------------------------ intro: materialise

def materialise(k):
    st = K.mat[k]
    t = st['t']
    if st['thr'] is None:
        px, sg = {}, None
    else:
        px, sg, _ = fx.reveal(backview.body().px, k)
    specs, sparks = flames.gather(t, k)
    order = list(range(len(specs)))
    if st['crown'] > 0.01:
        cs, co = flames.idle(k)
        cs = flames.grow_in(cs, st['crown'])
        order += [len(specs) + j for j in co]
        specs = specs + cs
    px = flames.stamp(px, specs, order, embers=embers_from(sparks, k))
    if sg is None:
        return fx.seed(px, k, 0.45)
    sg = sg & set(px)
    px = fx.paint_mask(px, sg, 0.20 + 0.25 * t)
    return fx.bloom_mask(px, sg, 0.25 * t)


# ------------------------------------------------------------------ intro: flare

def flare(i):
    lv = K.flare_lv[i]
    k = i + 5
    body = backview.body().px
    px = fx.burn(body, lv, bloom=lv, host=backview.host(), rim=lv, reach=34.0 + 12.0 * lv)
    specs, order = flames.between(lv, k)
    px = flames.stamp(px, specs, order, heat=lv,
                      embers=flames.drift(flames.AU.FLARE_EMBERS if lv > 0.5 else flames.AU.IDLE_EMBERS, i))
    px = fx.ground(px, lv)
    if lv >= 0.95:
        px = spokes(px, set(body), MARK_C_RAW, 14, 40, 24)
    return px


# ------------------------------------------------------------------ intro: turn

def _lean(phi, sign):
    return sign * 10.0 * math.sin(math.radians(phi)) * (1.0 if phi < 90 else -1.0)


def turn_body(i):
    """The body for turn beat i: turns.py says which drawn pose, head and eyes it wears."""
    import turns
    return turns.intro_body(i)


def turn(i):
    st = K.turn[i]
    phi, k = st['phi'], 9 + i
    s = sq(phi)
    px = turn_body(i)
    px = turned(px, phi, 1, -1, 0.55 if phi > 90 else 0.35)
    base, order = flames.idle(k)
    br = st['bridge']
    if br > 0.01:
        base, order = flames.between(br, k)
    specs = flames.sweep(flames.squeeze(base, 0.55 + 0.45 * s), _lean(phi, 1), droop=1.8)
    return flames.stamp(px, specs, order, heat=0.30 + 0.45 * st['mark'])


def settle():
    """Frame 15: the arms dropping out of the fold, the flare dying back toward idle."""
    import turns
    px = turns.arms_dropping()
    specs, order = flames.between(0.55, 15)
    return flames.stamp(px, specs, order, embers=flames.AU.FLARE_EMBERS)


def intro(i):
    if i <= 4:
        return materialise(i)
    if i <= 8:
        return flare(i - 5)
    if i <= 13:
        return turn(i - 9)
    if i == 14:
        return dict(frame1.build().px)
    if i == 15:
        return settle()
    return dict(frame0.build().px)


# ------------------------------------------------------------------ look-back

def look_back(i):
    import turns
    k = K.look_heads[i]
    px = turns.look_body(k)
    px = fx.burn(px, K.look_mark)                  # crisp, no bloom: the overlay brings the glow
    hold = i >= 3
    specs, order = flames.idle(i - 3 if hold else 40 + i, amp=1.2, loop=3 if hold else None)
    return flames.stamp(px, specs, order, heat=0.22,
                        embers=flames.drift(flames.AU.IDLE_EMBERS, (i - 3) if hold else i))


# ------------------------------------------------------------------ victory

def victory(i):
    import turns
    if i < 4:
        st = K.vic_turn[i]
        phi, k = st['phi'], 20 + i
        s = sq(phi)
        if abs(phi - 90.0) < 1.0:
            px = fx.burn(backview.body().px, 0.72, bloom=0.60, host=backview.host())
            px = fx.pivot(fx.squeeze(px, s))
        elif phi > 90.0:
            px = turns.victory_front(i)
        else:
            m = st['mark']
            px = fx.burn(backview.body().px, m, bloom=m * 0.8, host=backview.host(), rim=m * 0.8,
                         reach=32.0)
        px = turned(px, phi, -1, 1, 0.55 if phi > 90 else 0.35)
        base, order = flames.idle(k)
        specs = flames.sweep(flames.squeeze(base, 0.55 + 0.45 * s), _lean(phi, -1), droop=1.8)
        return flames.stamp(px, specs, order, heat=0.28 + 0.40 * st['mark'],
                            embers=flames.drift(flames.AU.IDLE_EMBERS, i))
    j = i - 4
    lv = K.vic_burn[j]
    body = backview.body().px
    px = fx.burn(body, lv, bloom=lv, host=backview.host(), rim=lv, reach=34.0 + 12.0 * lv)
    specs, order = flames.between(0.6 + 0.4 * lv, j, loop=3)
    px = flames.stamp(px, specs, order, heat=lv, embers=flames.AU.FLARE_EMBERS)
    px = fx.ground(px, lv)
    if lv >= 0.98:
        px = spokes(px, set(body), MARK_C_PX, int(13 * K.scale), int(40 * K.scale), 24 * K.scale)
    return px


SHEETS = {
    'carter_intro': (intro, 17),
    'carter_look_back': (look_back, 6),
    'carter_victory': (victory, 7),
}
