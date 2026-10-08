"""Every approval sheet as an image with its contract numbers, the numbers the code copies into
JoshHandsLayout, and the audit (palette, keyline, alpha, strays, footprint, empties)."""
import math

import jh_lib as H
import jh_hand as HD
import jh_anims as A
import jh_portal as P
import jh_fx as FX
import jh_josh as J

HAND_TAG = {'form': 'form', 'hover': 'hover', 'windup': 'windup', 'drop': 'drop', 'impact': 'impact',
            'shatter': 'shatter'}


def hand_images(clip, take='A'):
    HD.TAKE['backs'] = (take == 'B')
    try:
        frames = A.clip_frames(clip)
        mains, glows = [], []
        for fr in frames:
            px, gl = A.render_frame(fr)
            mains.append(H.to_image(px, A.FW, A.FH))
            glows.append(H.to_image(gl, A.FW, A.FH, H.GLOW))
        return H.strip(mains), H.strip(glows), len(frames)
    finally:
        HD.TAKE['backs'] = False


def portal_images(seq):
    fr = P.seq_frames(seq)
    backs = [H.to_image(b, P.PW, P.PH) for b, g in fr]
    glows = [H.to_image(g, P.PW, P.PH, H.GLOW) for b, g in fr]
    return H.strip(backs), H.strip(glows), len(fr)


def josh_image(sheet):
    return H.strip([H.to_image(J.frame(sheet, i), 80, 80) for i in range(4)])


def all_sheets():
    out = []
    for take in ('A', 'B'):
        for clip in A.ORDER:
            main, glow, n = hand_images(clip, take)
            times = A.CLIPS[clip]
            out.append(dict(take=take, name='josh_hand_%s' % clip, image=main, frames=n, fw=A.FW, times=times,
                            tag=HAND_TAG[clip], layer='hand'))
            out.append(dict(take=take, name='josh_hand_%s_glow' % clip, image=glow, frames=n, fw=A.FW, times=times,
                            tag=HAND_TAG[clip], layer='glow (additive, optional)'))
    out.append(dict(take='A', name='josh_hand_mark', image=H.strip([H.to_image(f, FX.MW, FX.MH) for f in FX.mark_frames()]),
                    frames=6, fw=FX.MW, times=FX.MARK_TIMES, tag='mark', layer='mark'))
    out.append(dict(take='A', name='josh_hand_impact_fx',
                    image=H.strip([H.to_image(f, FX.IW, FX.IH) for f in FX.impact_frames()]),
                    frames=4, fw=FX.IW, times=FX.IMPACT_FX_TIMES, tag='impact_fx', layer='floor fx'))
    for seq in P.ORDER:
        back, glow, n = portal_images(seq)
        out.append(dict(take='A', name='josh_portal_%s_back' % seq, image=back, frames=n, fw=P.PW,
                        times=P.SEQS[seq], tag=seq, layer='back'))
        out.append(dict(take='A', name='josh_portal_%s_glow' % seq, image=glow, frames=n, fw=P.PW,
                        times=P.SEQS[seq], tag=seq, layer='glow (additive)'))
    out.append(dict(take='A', name='josh_summon', image=josh_image('summon'), frames=4, fw=80,
                    times=J.SUMMON_TIMES, tag='summon', layer='josh'))
    out.append(dict(take='A', name='josh_command', image=josh_image('command'), frames=4, fw=80,
                    times=J.COMMAND_TIMES, tag='command', layer='josh'))
    return out


# ------------------------------------------------------------------ numbers

def air_extents():
    """How far the air clips (hover, windup, drop) reach from the pivot, in texels, glow excluded."""
    l = r = u = d = 0.0
    cx, cy = A.PX - 0.5, A.PY - 0.5
    for clip in ('hover', 'windup', 'drop'):
        for fr in A.clip_frames(clip):
            px, _ = A.render_frame(fr)
            for (x, y) in px:
                l = max(l, cx - x + 0.5)
                r = max(r, x - cx + 0.5)
                u = max(u, cy - y + 0.5)
                d = max(d, y - cy + 0.5)
    return dict(left=l, right=r, up=u, down=d)


HUD_KEEP_OUT = (708, 21, 1212, 193)       # Rect2(720, 33, 480, 148) grown by 12 px: x0, y0, x1, y1
GATES = {'left': (575, 270), 'right': (1345, 270)}
REST_OFFSET = (0, 170)


def _reach(frames_px, cx, cy):
    l = r = u = d = 0.0
    for px in frames_px:
        for (x, y) in px:
            l = max(l, cx - x + 0.5)
            r = max(r, x - cx + 0.5)
            u = max(u, cy - y + 0.5)
            d = max(d, y - cy + 0.5)
    return l, r, u, d


def keepout_check():
    """The drawn rect (world px, glow included) of every gate frame and every resting-hand frame at the
    plan's positions, against the boss bar block grown by its clearance."""
    out = {}
    gate_px = []
    for seq in P.ORDER:
        for b, g in P.seq_frames(seq):
            gate_px.append(set(b) | set(g))
    gl, gr, gu, gd = _reach(gate_px, P.PIVOT[0] - 0.5, P.PIVOT[1] - 0.5)
    hand_px = []
    for clip in ('form', 'hover'):
        for fr in A.clip_frames(clip):
            px, g = A.render_frame(fr)
            hand_px.append(set(px) | set(g))
    hl, hr, hu, hd = _reach(hand_px, A.PX - 0.5, A.PY - 0.5)
    for side, (gx, gy) in GATES.items():
        # the left gate and hand are mirrored: their left reach is the drawn right reach
        L, R = (gr, gl) if side == 'left' else (gl, gr)
        rect = (gx - L * 3, gy - gu * 3, gx + R * 3, gy + gd * 3)
        out['gate_' + side] = dict(rect=[round(v) for v in rect], hits_hud=_hits(rect))
        L, R = (hr, hl) if side == 'left' else (hl, hr)
        rx, ry = gx + REST_OFFSET[0], gy + REST_OFFSET[1]
        rect = (rx - L * 3, ry - hu * 3, rx + R * 3, ry + hd * 3)
        out['rest_hand_' + side] = dict(rect=[round(v) for v in rect], hits_hud=_hits(rect))
    return out


def _hits(rect):
    x0, y0, x1, y1 = HUD_KEEP_OUT
    return not (rect[2] <= x0 or rect[0] >= x1 or rect[3] <= y0 or rect[1] >= y1)


def contract():
    fp = A.best_footprint()
    ax = air_extents()
    # the cuff's centre relative to the pivot, texels (y up is negative)
    cuff = [f for f in A.hand_at(A.hover_pose(0)) if f.part == 'cuff'][0].centre()
    J.frame('summon', 2)
    J.frame('summon', 3)
    return {
        'scale': 3,
        'drawn_as': 'the RIGHT portal (its hand is the giant\'s left hand, thumb toward Josh); the left is the code\'s mirror (flip_h)',
        'pivot_convention': 'corner coordinates, Josh\'s convention: sprite.offset = frame_size / 2 - pivot',
        'hand': {
            'frame': [A.FW, A.FH], 'pivot': [A.PX, A.PY], 'mirror_axis_column': A.PX,
            'clips': {c: {'frames': len(A.CLIPS[c]), 'times': A.CLIPS[c], 'total': round(sum(A.CLIPS[c]), 3),
                          'loop': c in A.LOOPS} for c in A.ORDER},
            'impact_contact_frame': 0, 'impact_hold_frame': 3,
            'footprint_radii_texels': [fp['rx'], fp['ry']],
            'footprint_radii_px': [fp['rx'] * 3, fp['ry'] * 3],
            'contact_fill': round(fp['fill'], 3),
            'contact_reach_texels_lrud': list(fp['reach']),
            'air_extents_texels': ax,
            'air_box_px': [-ax['left'] * 3, -ax['up'] * 3, (ax['left'] + ax['right']) * 3, (ax['up'] + ax['down']) * 3],
            'cuff_centre_from_pivot_texels': [round(-cuff[0] if A.MIRROR else cuff[0], 1), round(cuff[1], 1)],
            'glow_layers': 'optional: josh_hand_<clip>_glow.png, same frames, drawn additive',
        },
        'mark': {'frame': [FX.MW, FX.MH], 'pivot': [FX.MPX, FX.MPY], 'frames': 6, 'times': FX.MARK_TIMES,
                 'hover_frames': [0, 1], 'height_frames': [2, 3, 4], 'land_frame': 5,
                 'rim': 'exactly the footprint ellipse on every frame (pixel centres inside ((x+0.5-px)/rx)^2 + ((y+0.5-py)/ry)^2 <= 1, its edge ring)'},
        'impact_fx': {'file': 'josh_hand_impact_fx.png', 'frame': [FX.IW, FX.IH], 'pivot': [FX.IPX, FX.IPY],
                      'frames': 4, 'times': FX.IMPACT_FX_TIMES, 'layer': 'floor, under the hand',
                      'note': 'named _fx: the plan listed the optional FX as josh_hand_impact.png, the same name as the impact clip'},
        'portal': {'frame': [P.PW, P.PH], 'pivot': list(P.PIVOT), 'opening_radius_texels': P.R_VORTEX,
                   'rim_outer_radius_texels': P.R_VORTEX + P.RIM_W, 'ring_outer_radius_texels': P.R_VORTEX + P.RIM_W - 3 + P.CARD_L,
                   'sequences': {s: {'frames': len(P.SEQS[s]), 'times': P.SEQS[s], 'total': round(sum(P.SEQS[s]), 3),
                                     'loop': s in P.LOOPS} for s in P.ORDER},
                   'layers': ['back (normal)', 'glow (additive)']},
        'josh': {'frame': [80, 80], 'feet_row': 79, 'axis_x': 40, 'facing': 'right',
                 'summon': {'frames': 4, 'times': J.SUMMON_TIMES, 'loop': [2, 3],
                            'card_origins_texels': {str(k): v for k, v in J.CARD_ORIGINS.items()}},
                 'command': {'frames': 4, 'times': J.COMMAND_TIMES, 'loop': [2, 3]}},
        'rest_offset_px': list(REST_OFFSET),
        'keepout_check_world_px': keepout_check(),
        'palette': {k: H.hexs(k) for k in sorted(H.PAL)},
        'glow_palette': {k: '#%02X%02X%02X' % v[:3] for k, v in H.GLOW.items()},
    }


# ------------------------------------------------------------------ the audit

def audit(spec):
    im = spec['image'].convert('RGBA')
    px = list(im.get_flattened_data())
    opaque = [p for p in px if p[3]]
    semi = sum(1 for p in opaque if p[3] != 255)
    glow = 'glow' in spec['name']
    pal = set(v[:3] for v in (H.GLOW if glow else H.PAL).values())
    off = sum(1 for p in opaque if p[:3] not in pal)
    black = sum(1 for p in opaque if p[:3] == (0, 0, 0))
    cols = len(set(p[:3] for p in opaque))
    # strays: an opaque pixel with no opaque 8-neighbour, in each frame (sparkle cores never are)
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
                n = 0
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        if dx or dy:
                            X, Y = x + dx, y + dy
                            if f0 <= X < f0 + fw and 0 <= Y < Hh and a[X, Y]:
                                n += 1
                if n == 0:
                    strays += 1
    empties = []
    for i in range(spec['frames']):
        fr = im.crop((i * fw, 0, (i + 1) * fw, Hh))
        if fr.getbbox() is None:
            empties.append(i)
    return dict(opaque=len(opaque), semi_alpha=semi, off_palette=off, colours=cols,
                black=round(black / float(max(1, len(opaque))), 3), strays=strays, empty_frames=empties)
