"""Carter's victory pose: he kills you, turns his back, and the mark burns.

This is the entrance played backwards as a statement.  He arrives back-turned
with the emblem flaring; when he puts you down he turns away and does it again,
except this time he is not materialising, he is just standing there not watching
you.  The whole point is the contempt, so nothing in it is hurried except the
turn itself.

    f0      front, facing the player who has just dropped
    f1      the pivot starts
    f2      edge-on, the back-lit beat the entrance uses for 90 degrees
    f3      settled into the back view, mark nearly out - the held breath
    f4      IGNITION.  The mark snaps to full burn.  <- the sound lands here
    f5..f6  the burn, pulsing, looping with f4 so the defeat screen can fade
            over him while he stands in it

The jump from f3 (0.12) to f4 (1.00) is deliberately a snap rather than a ramp:
the ignition IS the moment, and a two-frame fade in front of it would steal it.

Everything is reused: the body is poses.draw_back (the approved back view that
ships as carter_akuma frame 2), the burn is intro_lib's sigil_paint/sigil_bloom
at the levels the entrance's flare cycle already uses, and the edge-on frame is
intro_profile.pivot_treatment.
"""
import math
from lib import Canvas, union, grow, PALC, W, H
import aura as AU
import poses as PO
import render as R
import intro_lib as IL
import intro_frames as IF
import intro_profile as IP
import combat_lib as CL
from intro_lib import (compose, sigil_paint, sigil_bloom, rim_light,
                       ground_glow, aura_heat, hsq_canvas, edge_shade, rim_edge)

# phi: 180 = facing the player, 90 = edge on, 0 = back turned.  He pivots the
# opposite way round from the entrance, so the lit edge and the drag on the
# aura are mirrored - screen-RIGHT leads here, screen-LEFT leads on the way in.
TURN = [
    dict(phi=180.0, mark=0.00),
    dict(phi=126.0, mark=0.00),
    dict(phi=90.0, mark=0.26),
    dict(phi=0.0, mark=0.12),
]

# f4 is the peak.  Everything after it pulses without ever dropping out of a
# full burn, so the loop reads as something sustained rather than flickering.
BURN_LV = [1.00, 0.72, 0.86]

N = len(TURN) + len(BURN_LV)          # 7
IGNITE_FRAME = len(TURN)              # 4

MS = [90, 70, 70, 140, 110, 130, 130]
IGNITE_MS = sum(MS[:IGNITE_FRAME])    # 370
LOOP_FROM = IGNITE_FRAME


def _turn(i):
    st = TURN[i]
    phi, k = st['phi'], 20 + i
    s = IF.sq_of(phi)
    bm_src = None
    if abs(phi - 90.0) < 1.0:
        body = IF.back_body()
        sg = IF.sigil_mask()
        sigil_bloom(body, sg, 0.60, host=PO.back_jacket())
        sigil_paint(body, sg, 0.72)
        body = IP.pivot_treatment(hsq_canvas(body, s))
    elif phi > 90.0:
        body = Canvas()
        R.body(body)
        IL.wrap_bands_both(body, union(PO.P.wraps_wrist(), PO.P.wraps_fist()),
                           (22.0, 64.0), (19.8, 78.2))
        if phi < 179.0:
            body = hsq_canvas(body, s)
            body = IL.shift_canvas(body, CL.dpx(5.0 * (1.0 - s)))
    else:
        body = IF.back_body()
        sg = IF.sigil_mask()
        sigil_bloom(body, sg, st['mark'] * 0.8, host=PO.back_jacket())
        rim_light(body, body.mask_of(), st['mark'] * 0.8, reach=32.0)
        sigil_paint(body, sg, st['mark'])
        if s < 0.999:
            body = hsq_canvas(body, s)
            body = IL.shift_canvas(body, -CL.dpx(4.0 * (1.0 - s)))
    # the leading edge is on the right going this way
    if phi < 175.0:
        rim_edge(body, 1, 'X', 0.55 if phi > 90 else 0.35)
        edge_shade(body, -1, 0.5)

    lean = -10.0 * math.sin(math.radians(phi)) * (1.0 if phi < 90 else -1.0)
    specs = IL.sweep(IL.squeeze_specs(IL.entr_specs(k, 0.94, 0.96),
                                      0.55 + 0.45 * s), lean, droop=1.8)
    cv = compose(body, specs, IL.entr_sparks(k), haze_in=8, haze_out=3, off=k)
    aura_heat(cv, grow(body.mask_of(), 1), 0.28 + 0.40 * st['mark'])
    IL.soften(cv, grow(body.mask_of(), 1), near=9, far=28, seed=k)
    return cv


def _burn(i):
    """The flare cycle the entrance already uses, standing still."""
    lv = BURN_LV[i]
    k = 30 + i
    body = IF.back_body()
    bm = body.mask_of()
    sg = IF.sigil_mask()
    # bloom first, emblem last, or the flare swallows the shape at its peak
    sigil_bloom(body, sg, lv, host=PO.back_jacket())
    rim_light(body, bm, lv, reach=34.0 + 12.0 * lv)
    sigil_paint(body, sg, lv)

    specs = IL.entr_specs(k, scale=0.84 + 0.34 * lv, reach=0.86 + 0.24 * lv)
    cv = compose(body, specs, IL.entr_sparks(k),
                 haze_in=6 + int(6 * lv), haze_out=int(5 * lv), off=k)
    aura_heat(cv, grow(bm, 1), lv)
    IL.soften(cv, grow(bm, 1), near=9 + int(4 * lv), far=30, seed=k)
    ground_glow(cv, lv)
    if lv >= 0.98:
        # spokes bursting off the ignition, kept off his silhouette
        cx, cy = IL.MARK_C
        px, py = IL.T(cx, cy) if hasattr(IL, 'T') else (cx, cy)
        import lib
        px, py = lib.T(cx, cy)
        for n in range(12):
            a = n * math.pi / 6 + 0.26
            for r in range(int(13 * lib.SCALE), int(40 * lib.SCALE)):
                x = int(round(px + math.cos(a) * r * 0.95))
                y = int(round(py + math.sin(a) * r * 1.05))
                if not (0 <= x < W and 0 <= y < H):
                    break
                if bm[y][x] or (r + n) % 3:
                    continue
                cv.px[y][x] = PALC['X'] if r < 24 * lib.SCALE else PALC['y']
    return cv


def frame(i):
    return _turn(i) if i < len(TURN) else _burn(i - len(TURN))
