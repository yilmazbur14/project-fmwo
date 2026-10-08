"""Every sheet of each take, built in memory: {sheet name: [index grid per frame]} and its palette.

The sheet names are the file names the build writes (beam_<take>_<name>.png), and the contract
(mb_build.py) describes each one.
"""
import numpy as np

import mb_core as C
import mb_body as B
import mb_head as HD
import mb_bursts as X
import mb_diss as D
import mb_charge as Q
import mb_takeb as TB
import mb_takeb2 as TB2
import mb_overlay as OV

# name: (take A function, take B function, frames, uses the glow palette)
SHEETS = {
    'charge':         ('mb_charge:charge_a', 'mb_takeb2:charge_b', Q.CHARGE_FRAMES, False),
    'charge_glow':    ('mb_charge:charge_glow_a', 'mb_charge:charge_glow_a', Q.CHARGE_FRAMES, True),
    'release':        ('mb_charge:release_a', 'mb_takeb2:release_b', Q.RELEASE_FRAMES, False),
    'release_glow':   ('mb_charge:release_glow_a', 'mb_charge:release_glow_a', Q.RELEASE_FRAMES, True),
    'body':           ('mb_body:body_a', 'mb_takeb:body_b', B.FRAMES, False),
    'body_glow':      ('mb_body:glow_a', 'mb_takeb:glow_b', B.FRAMES, True),
    'head':           ('mb_head:head_a', 'mb_takeb:head_b', HD.HEAD_FRAMES, False),
    'head_glow':      ('mb_head:head_glow_a', 'mb_takeb:head_glow_b', HD.HEAD_FRAMES, True),
    'corner':         ('mb_bursts:corner_a', 'mb_takeb2:corner_b', X.CORNER_FRAMES, False),
    'corner_glow':    ('mb_bursts:corner_glow_a', 'mb_bursts:corner_glow_a', X.CORNER_FRAMES, True),
    'impact':         ('mb_bursts:impact_a', 'mb_takeb2:impact_b', X.IMPACT_FRAMES, False),
    'impact_glow':    ('mb_bursts:impact_glow_a', 'mb_takeb2:impact_glow_b', X.IMPACT_FRAMES, True),
    'ring':           ('mb_bursts:ring_a', 'mb_takeb2:ring_b', X.RING_FRAMES, False),
    'dissipate':      ('mb_diss:dissipate_a', 'mb_takeb2:dissipate_b', D.DISS_FRAMES, False),
    'ember':          ('mb_diss:ember_a', 'mb_takeb2:ember_b', D.EMBER_FRAMES, False),
    'smoke':          ('mb_diss:smoke_a', 'mb_takeb2:smoke_b', D.SMOKE_FRAMES, False),
    'scorch':         ('mb_diss:scorch_a', 'mb_takeb2:scorch_b', D.SCORCH_FRAMES, False),
    'overlay':        ('mb_overlay:overlay_a', 'mb_overlay:overlay_b', OV.OVERLAY_FRAMES, False),
}

MODULES = {'mb_body': B, 'mb_head': HD, 'mb_bursts': X, 'mb_diss': D, 'mb_charge': Q, 'mb_takeb': TB,
           'mb_takeb2': TB2, 'mb_overlay': OV}


def palettes(take):
    return (C.Pal(C.PAL_A if take == 'a' else C.PAL_B), C.Pal(C.GLOW_A if take == 'a' else C.GLOW_B))


def _fn(spec):
    mod, name = spec.split(':')
    return getattr(MODULES[mod], name)


def build(take, only=None):
    """{name: [grids]} for one take ('a' or 'b')."""
    pal, gpal = palettes(take)
    out = {}
    for name, (fa, fb, n, glow) in SHEETS.items():
        if only and name not in only:
            continue
        fn = _fn(fa if take == 'a' else fb)
        p = gpal if glow else pal
        out[name] = [fn(p, f) for f in range(n)]
    return out


def mock_art(take, sheets=None):
    """The art as the mock compositor wants it: PIL frames, and RGBA arrays for the lines."""
    pal, gpal = palettes(take)
    sheets = sheets or build(take)
    art = {}
    for name, grids in sheets.items():
        p = gpal if SHEETS[name][3] else pal
        art[name] = [p.image(g) for g in grids]
    for name in ('body', 'body_glow', 'dissipate', 'scorch'):
        art[name + '_np'] = [np.array(im).astype(np.int16) for im in art[name]]
    art['diss'] = art['dissipate']
    art['diss_np'] = art['dissipate_np']
    art['tile_w'], art['tile_h'] = B.W, B.H
    art['glow_h'] = B.GH
    art['scorch_w'], art['scorch_h'] = D.SW, D.SH
    art['attach'] = HD.ATTACH
    return art
