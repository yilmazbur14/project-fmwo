"""The approved mark rig (art_source/carter_akuma), run in its own process.

That rig and the polish rig both have a module called `lib`, so they never share an interpreter
(art_source/carter_polish/README.md). rig.py starts this file once per build and talks to it over
stdin/stdout, one JSON object per line. It imports the akuma rig read-only, applies its scale, writes
no bytecode and calls nothing that writes a file.

Canvases travel as [[x, y, "rrggbb"], ...] and masks as [[x, y], ...], in the 96x96 frame.

Requests ({"op": ..., ...}) and what they run:
  init        {pal: {key: hex}} -> the 天 mask and every timing/level constant the shipped frames
              used. `pal` is the polish palette: intro_lib's colour snapping is pointed at it, so
              the bloom and the rim light blend exactly as before but land on approved colours only.
  burn        sigil_bloom (host-limited) -> rim_light -> sigil_paint, the shipped order
  paint_mask  sigil_paint on a given (e.g. squeezed) mask
  bloom_mask  sigil_bloom on a given mask
  squeeze     hsq_canvas (+ shift_canvas)
  sq_mask     hsq_mask (+ shift)
  pivot       intro_profile.pivot_treatment
  ground      ground_glow
  rim_edge    rim_edge
  edge_shade  edge_shade
  reveal      the materialise field: the formed / half / shell / haze bands and the bright front, as
              intro_frames.frame_materialise draws them on a full body - except that the gathering
              motes are no longer keyed (see op_reveal)
  seed        intro_frames.seed_spark
  gather      intro_frames.gather_specs / gather_sparks, converted to pixel space
"""
import json
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
AKUMA = os.path.normpath(os.path.join(HERE, '..', 'carter_akuma'))
sys.path.insert(0, AKUMA)
os.chdir(AKUMA)

import carter_scale                                                           # noqa: E402
carter_scale.apply()
import lib                                                                    # noqa: E402
import intro_lib as IL                                                        # noqa: E402
import intro_frames as IF                                                     # noqa: E402
import intro_profile as IP                                                    # noqa: E402
import combat_victory as CVI                                                  # noqa: E402
import combat_look as CLK                                                     # noqa: E402

W = H = 96


def hexc(h):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def to_cv(px):
    cv = lib.Canvas()
    for x, y, h in px:
        if 0 <= x < W and 0 <= y < H:
            cv.px[y][x] = hexc(h)
    return cv


def from_cv(cv):
    out = []
    for y in range(H):
        for x in range(W):
            c = cv.px[y][x]
            if c is not None:
                out.append([x, y, '%02x%02x%02x' % (c[0], c[1], c[2])])
    return out


def to_mask(pts):
    m = lib.empty()
    for x, y in pts:
        if 0 <= x < W and 0 <= y < H:
            m[y][x] = True
    return m


def from_mask(m):
    return [[x, y] for y in range(H) for x in range(W) if m[y][x]]


def shift_mask(m, dx):
    if not dx:
        return m
    out = lib.empty()
    for y in range(H):
        for x in range(W):
            if m[y][x] and 0 <= x + dx < W:
                out[y][x + dx] = True
    return out


def op_init(req):
    IL._PAL_LIST = [(k, hexc(v)) for k, v in req['pal'].items()]
    IL._SNAP_CACHE.clear()
    sg = IF.sigil_mask()
    return {
        'mark': from_mask(sg),
        'mat': IF.MAT,
        'flare_lv': IF.FLARE_LV,
        'turn': IF.TURN,
        'settle_arm': IF.SETTLE_ARM,
        'vic_turn': CVI.TURN,
        'vic_burn': CVI.BURN_LV,
        'vic_ms': CVI.MS,
        'vic_ignite': CVI.IGNITE_FRAME,
        'look_mark': CLK.MARK_LV,
        'look_heads': CLK.HEADS,
        'look_ms': CLK.MS,
        'mark_c_px': list(lib.T(*IL.MARK_C)),
        'mark_c_design': list(IL.MARK_C),
        'scale': lib.SCALE,
        'sq': {str(p): IF.sq_of(p) for p in (0.0, 40.0, 90.0, 126.0, 132.0, 162.0, 180.0)},
        'dpx_vic1': __import__('combat_lib').dpx(5.0 * (1.0 - IF.sq_of(126.0))),
    }


def op_burn(req):
    cv = to_cv(req['px'])
    bm = cv.mask_of()
    sg = IF.sigil_mask()
    if req.get('bloom') is not None:
        host = to_mask(req['host']) if req.get('host') is not None else None
        IL.sigil_bloom(cv, sg, req['bloom'], host=host)
    if req.get('rim') is not None:
        IL.rim_light(cv, bm, req['rim'], reach=req['reach'])
    if req.get('paint') is not None:
        IL.sigil_paint(cv, sg, req['paint'])
    return {'px': from_cv(cv)}


def op_paint_mask(req):
    cv = to_cv(req['px'])
    IL.sigil_paint(cv, to_mask(req['mask']), req['level'])
    return {'px': from_cv(cv)}


def op_bloom_mask(req):
    cv = to_cv(req['px'])
    host = to_mask(req['host']) if req.get('host') is not None else None
    IL.sigil_bloom(cv, to_mask(req['mask']), req['level'], host=host)
    return {'px': from_cv(cv)}


def op_squeeze(req):
    cv = IL.hsq_canvas(to_cv(req['px']), req['s'], reoutline=req.get('reoutline', True),
                       keep_head=req.get('keep_head', True))
    if req.get('dx'):
        cv = IL.shift_canvas(cv, req['dx'])
    return {'px': from_cv(cv)}


def op_sq_mask(req):
    m = IL.hsq_mask(to_mask(req['mask']), req['s'], keep_head=req.get('keep_head', True))
    return {'mask': from_mask(shift_mask(m, req.get('dx', 0)))}


def op_pivot(req):
    return {'px': from_cv(IP.pivot_treatment(to_cv(req['px'])))}


def op_ground(req):
    cv = to_cv(req['px'])
    IL.ground_glow(cv, req['level'])
    return {'px': from_cv(cv)}


def op_rim_edge(req):
    cv = to_cv(req['px'])
    IL.rim_edge(cv, req['side'], req.get('col', 'X'), req.get('amt', 0.6))
    return {'px': from_cv(cv)}


def op_edge_shade(req):
    cv = to_cv(req['px'])
    IL.edge_shade(cv, req['side'], req.get('amt', 0.55))
    return {'px': from_cv(cv)}


def op_reveal(req):
    """intro_frames.frame_materialise's body treatment, line for line, on the given full body. It
    returns the treated body and the mark mask as this stage squeezes it."""
    k = req['k']
    st = IF.MAT[k]
    full = to_cv(req['px'])
    sg = IF.sigil_mask()
    if st['sq'] and st['sq'] < 0.999:
        full = IL.hsq_canvas(full, st['sq'], keep_head=False)
        sg = IL.hsq_mask(sg, st['sq'], keep_head=False)
    bm = full.mask_of()
    thr = st['thr']
    got = IL.field_mask(thr, bm)
    half = IL.field_band(thr, thr + 0.17, bm)
    shell = IL.field_band(thr + 0.17, thr + 0.32, bm)
    haze = IL.field_band(thr + 0.32, thr + 0.58, bm)
    body = lib.Canvas()
    for y in range(H):
        for x in range(W):
            if (got[y][x] or half[y][x]) and full.px[y][x] is not None:
                body.px[y][x] = full.px[y][x]
    P = lib.PALC
    if st['void'] > 0.01:
        IL.tint(body, got, P['T'], st['void'] * 0.74, skip_black=True)
    IL.tint(body, half, P['T'], 0.82)
    body.paint(shell, P['S'])
    body.paint(IL.field_band(thr - 0.020, thr + 0.016, bm), P['Q'])
    body.paint(IL.field_band(thr - 0.008, thr + 0.006, bm), P['P'])
    # The approved frame keyed the whole mask, the gathering motes included, and the loose 2x2 motes
    # at the edge turned into a black lattice. Here only the solid body is keyed (re-closing the
    # silhouette as before) and the motes are laid on after it, unkeyed: energy never takes black.
    body.outline(body.mask_of())
    motes_t = IL.block_dither(haze, 10, 2, k)
    motes_s = IL.block_dither(haze, 4, 2, k + 7)
    for y in range(H):
        for x in range(W):
            if body.px[y][x] is None:
                if motes_s[y][x]:
                    body.px[y][x] = P['S']
                elif motes_t[y][x]:
                    body.px[y][x] = P['T']
    return {'px': from_cv(body), 'mark': from_mask(sg),
            'bands': {'got': from_mask(got), 'half': from_mask(half), 'shell': from_mask(shell),
                      'haze': from_mask(haze)}}


def op_seed(req):
    cv = to_cv(req['px'])
    IF.seed_spark(cv, req['k'], req['level'])
    return {'px': from_cv(cv)}


def op_gather(req):
    t, k = req['t'], req['k']
    s = lib.SCALE
    specs = []
    for ctrl, w0, w1 in IF.gather_specs(t, k):
        specs.append([[list(lib.T(x, y)) for x, y in ctrl], w0 * s, w1 * s])
    sparks = [list(lib.T(x - 0.5, y - 0.5)) for x, y in IF.gather_sparks(t, k)]
    return {'specs': specs, 'sparks': sparks}


OPS = {n[3:]: f for n, f in globals().items() if n.startswith('op_')}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        req = json.loads(line)
        try:
            out = OPS[req['op']](req)
            out['ok'] = True
        except Exception as e:                                                # noqa: BLE001
            import traceback
            out = {'ok': False, 'error': '%s: %s' % (type(e).__name__, e),
                   'trace': traceback.format_exc()}
        sys.stdout.write(json.dumps(out) + '\n')
        sys.stdout.flush()


if __name__ == '__main__':
    main()
