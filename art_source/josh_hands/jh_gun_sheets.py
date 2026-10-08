"""The gun-hand approval sheets with their numbers (contract.json) and the audit."""
import math

import jh_lib as H
import jh_gun as GN
import jh_beam as B

VIEW_W, VIEW_H = 1920, 1080
EDGE_IN = 8                                  # the gun box's outer edge sits this far inside the view
HUD_LEFT_TOP, HUD_RIGHT_TOP = 830, 934       # the player-HUD corners' tops, grown by their clearance
ROPE_OUTER = {'left': 100, 'right': 1820}
TELEGRAPH = {'fill': '#C2283A', 'rims': '#E8605A', 'flash': '#FFF3B0'}


def gun_images(clip):
    mains, glows = [], []
    for i, fr in enumerate(GN.clip_frames(clip)):
        px, gl = GN.render_any(clip, fr, i)
        mains.append(H.to_image(px, GN.FW, GN.FH))
        glows.append(H.to_image(gl, GN.FW, GN.FH, H.GLOW))
    return H.strip(mains), H.strip(glows), len(mains)


def all_sheets():
    out = []
    for clip in GN.GUN_ORDER:
        main, glow, n = gun_images(clip)
        times = GN.GUN_CLIPS[clip]
        out.append(dict(name='josh_hand_%s' % clip, image=main, frames=n, fw=GN.FW, times=times, tag=clip,
                        layer='hand'))
        out.append(dict(name='josh_hand_%s_glow' % clip, image=glow, frames=n, fw=GN.FW, times=times, tag=clip,
                        layer='glow (additive, optional)'))
    for name, frames, w, h, times, pal in (
            ('josh_gun_beam_start', B.start_frames(), 16, 20, B.BEAM_TIMES, None),
            ('josh_gun_beam_tile', B.tile_frames(), 16, 20, B.BEAM_TIMES, None),
            ('josh_gun_beam_end', B.end_frames(), 16, 20, B.BEAM_TIMES, None),
            ('josh_gun_beam_glow', B.glow_frames(), 16, 32, B.BEAM_TIMES, H.GLOW),
            ('josh_gun_flash', B.flash_frames(), 48, 48, B.FLASH_TIMES, None),
            ('josh_gun_charge_fx', B.charge_frames(), 32, 32, B.CHARGE_TIMES, None)):
        img = H.strip([H.to_image(f, w, h, pal) for f in frames])
        out.append(dict(name=name, image=img, frames=len(frames), fw=w, times=times, tag=name.replace('josh_gun_', ''),
                        layer='glow (additive, optional)' if pal else 'fx'))
    return out


def gun_box():
    """The drawn box (glow included) of every idle, charge and fire frame (gun_form's last frame is idle
    frame 0), in frame texels, inclusive."""
    x0 = y0 = 999
    x1 = y1 = -999
    for clip in ('gun_idle', 'gun_charge', 'gun_fire'):
        for i, fr in enumerate(GN.clip_frames(clip)):
            px, gl = GN.render_any(clip, fr, i)
            for (x, y) in list(px) + list(gl):
                x0, y0, x1, y1 = min(x0, x), min(y0, y), max(x1, x), max(y1, y)
    return x0, y0, x1, y1


def form_box():
    x0 = y0 = 999
    x1 = y1 = -999
    for i, fr in enumerate(GN.clip_frames('gun_form')):
        px, gl = GN.render_any('gun_form', fr, i)
        for (x, y) in list(px) + list(gl):
            x0, y0, x1, y1 = min(x0, x), min(y0, y), max(x1, x), max(y1, y)
    return x0, y0, x1, y1


def muzzle_checks():
    """The fingertips' leftmost column and the barrel's rows on idle, charge and fire frame 0 (cards only,
    the charge's glow bead left out), to show GUN_MUZZLE holds on all three."""
    out = {}
    for clip in ('gun_idle', 'gun_charge', 'gun_fire'):
        fr = GN.clip_frames(clip)[0]
        bare = GN.A.Frame(fr.cards, dy=fr.dy, tone=fr.tone)
        px, _ = GN.render(bare)
        barrel_rows = [y for (x, y) in px if x <= GN.MUZZLE[0] + 3]
        out[clip] = dict(tip_column=min(x for (x, y) in px), barrel_rows=[min(barrel_rows), max(barrel_rows)])
    return out


def posts_and_ranges(box):
    """Where the code will put the guns (the plan's rule), for the mocks and the report."""
    x0, y0, x1, y1 = box
    right_reach = (x1 + 1 - GN.PX) * 3            # px from the node to the box's outer (cuff) edge
    up = (GN.PY - y0) * 3
    down = (y1 + 1 - GN.PY) * 3
    node_r = VIEW_W - EDGE_IN - right_reach
    node_l = EDGE_IN + right_reach
    mdx = (GN.MUZZLE[0] - GN.PX) * 3
    rows_top = EDGE_IN + up
    return dict(
        node={'left': node_l, 'right': node_r},
        muzzle_x={'left': node_l - mdx, 'right': node_r + mdx},
        row_range={'left': [rows_top, HUD_LEFT_TOP - down], 'right': [rows_top, HUD_RIGHT_TOP - down]},
        beam={'left': [node_l - mdx, ROPE_OUTER['right']], 'right': [ROPE_OUTER['left'], node_r + mdx]},
    )


def contract():
    box = gun_box()
    fb = form_box()
    x0, y0, x1, y1 = box
    rel = [x0 - GN.PX, y0 - GN.PY, x1 + 1 - x0, y1 + 1 - y0]
    pr = posts_and_ranges(box)
    return {
        'scale': 3,
        'drawn_as': "the RIGHT side's hand pointing LEFT (the giant's left hand, the approved handedness); the left is the code's mirror (flip_h about the pivot column)",
        'frame': [GN.FW, GN.FH], 'pivot': [GN.PX, GN.PY],
        'GUN_MUZZLE': list(GN.MUZZLE),
        'GUN_MUZZLE_note': 'corner point: the beam centre line is row 70 (the pivot row, so the beam row is the node y); '
                           'the fingertips end at column 30, the same on idle, charge and fire frame 0',
        'GUN_BOX_TEXELS': rel,
        'GUN_BOX_note': 'Rect2 around the pivot (x, y, w, h) of every idle/charge/fire frame, glow included',
        'box_vs_muzzle_row': {'above': GN.PY - y0, 'below': y1 + 1 - GN.PY,
                              'muzzle_to_cuff_edge': x1 + 1 - GN.MUZZLE[0]},
        'gun_form_box_texels': [fb[0] - GN.PX, fb[1] - GN.PY, fb[2] + 1 - fb[0], fb[3] + 1 - fb[1]],
        'clips': {c: {'frames': len(GN.GUN_CLIPS[c]), 'times': GN.GUN_CLIPS[c],
                      'total': round(sum(GN.GUN_CLIPS[c]), 3), 'loop': c in GN.GUN_LOOPS,
                      'hold_last': c in GN.GUN_HOLD} for c in GN.GUN_ORDER},
        'muzzle_checks': muzzle_checks(),
        'beam': {
            'pieces': {'start': 'josh_gun_beam_start.png 16x20: its right edge on the muzzle column, centre line on the muzzle row',
                       'tile': 'josh_gun_beam_tile.png 16x20: seamless left-right, repeated from the start piece to the end piece',
                       'end': 'josh_gun_beam_end.png 16x20: its left edge on the far rope (x 100 for the right hand)',
                       'glow': 'josh_gun_beam_glow.png 16x32 (optional, additive): the halo, 6 texels past each edge'},
            'frames': 3, 'times': B.BEAM_TIMES, 'height_texels': 20, 'BEAM_HALF_px': 30,
            'pivots_corner': {'start': [16, 10], 'tile': [0, 10], 'end': [0, 10], 'glow': [0, 16]},
            'colours': 'white core, cream, salmon #E8605A, crimson #C2283A, dark crimson #861826, wine edge #4D1420',
        },
        'flash': {'file': 'josh_gun_flash.png', 'frame': [48, 48], 'pivot': [24, 24], 'times': B.FLASH_TIMES},
        'charge_fx': {'file': 'josh_gun_charge_fx.png', 'frame': [32, 32], 'pivot': [16, 16], 'times': B.CHARGE_TIMES,
                      'loop': True},
        'telegraph_colours': TELEGRAPH,
        'posts_px_from_this_box': pr,
    }


def audit(spec):
    im = spec['image'].convert('RGBA')
    px = list(im.get_flattened_data())
    opaque = [p for p in px if p[3]]
    semi = sum(1 for p in opaque if p[3] != 255)
    glow = 'glow' in spec['layer']
    pal = set(v[:3] for v in (H.GLOW if glow else H.PAL).values())
    off = sum(1 for p in opaque if p[:3] not in pal)
    lanes_gold = sum(1 for p in opaque if p[:3] == (255, 217, 38))
    W, Hh = im.size
    fw = spec['fw']
    a = im.getchannel('A').load()
    strays = 0
    if not glow:
        for y in range(Hh):
            for x in range(W):
                if not a[x, y]:
                    continue
                f0 = (x // fw) * fw
                if not any(a[X, Y] for X in (x - 1, x, x + 1) for Y in (y - 1, y, y + 1)
                           if (X, Y) != (x, y) and f0 <= X < f0 + fw and 0 <= Y < Hh):
                    strays += 1
    empties = [i for i in range(spec['frames']) if im.crop((i * fw, 0, (i + 1) * fw, Hh)).getbbox() is None]
    return dict(opaque=len(opaque), semi_alpha=semi, off_palette=off, lanes_gold=lanes_gold,
                colours=len(set(p[:3] for p in opaque)), strays=strays, empty_frames=empties)
