"""PORTAL MONTE approval sheets, their numbers (contract.json) and the audit.

Ship names are the plan's (scratchpad josh_hands/PLAN_portal_monte.md, "Art contract"); each spec says
where its file would go under Assets/Characters/Josh once the user approves (nothing ships from here).
"""
import math

import jh_lib as H
import jh_small_gate as SG
import jh_monte_josh as M

SHIP = {
    'gate': 'Assets/Characters/Josh/Portals/',
    'josh': 'Assets/Characters/Josh/',
    'cards': 'Assets/Characters/Josh/Cards/',
}


def gate_images(seq):
    fw, fh = SG.CFG['FW'], SG.CFG['FH']
    backs, glows = [], []
    for b, g in SG.seq_frames(seq):
        backs.append(H.to_image(b, fw, fh))
        glows.append(H.to_image(g, fw, fh, H.GLOW))
    return H.strip(backs), H.strip(glows), len(backs)


def all_sheets():
    out = []
    fw = SG.CFG['FW']
    for seq in SG.ORDER:
        back, glow, n = gate_images(seq)
        times = SG.SEQS[seq]
        out.append(dict(name='josh_small_portal_%s_back' % seq, image=back, frames=n, fw=fw, times=times,
                        tag=seq, layer='back', ship=SHIP['gate']))
        out.append(dict(name='josh_small_portal_%s_glow' % seq, image=glow, frames=n, fw=fw, times=times,
                        tag=seq, layer='glow (additive)', ship=SHIP['gate']))
    for name, fn, n, w, h, times, tag, ship in (
            ('josh_dive', M.dive_frame, 5, 80, 80, M.DIVE_TIMES, 'dive', SHIP['josh']),
            ('josh_emerge', M.emerge_frame, len(M.EMERGE_TIMES), 80, 80, M.EMERGE_TIMES, 'emerge', SHIP['josh']),
            ('josh_monte_slash', M.slash_frame, 4, M.SLASH_FW, M.SLASH_FH, M.SLASH_TIMES, 'slash', SHIP['josh']),
            ('josh_monte_scatter', M.scatter_frame, 6, M.SCATTER_FW, M.SCATTER_FH, M.SCATTER_TIMES, 'scatter',
             SHIP['cards'])):
        img = H.strip([H.to_image(fn(i), w, h) for i in range(n)])
        out.append(dict(name=name, image=img, frames=n, fw=w, times=times, tag=tag, layer='body', ship=ship))
    return out


# ------------------------------------------------------------------ measurements

def bbox(px):
    xs = [q[0] for q in px]
    ys = [q[1] for q in px]
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def gate_drawn():
    """The small gate's drawn box over its loop (glow included and not), in frame texels, inclusive; its
    widest reach from the pivot."""
    boxes, reach = [], 0.0
    cx, cy = SG.centre()
    for b, g in SG.seq_frames('loop'):
        boxes.append((bbox(b), bbox({**b, **g})))
        for (x, y) in b:
            reach = max(reach, math.hypot(x - cx, y - cy))
    body = (min(b[0][0] for b in boxes), min(b[0][1] for b in boxes), max(b[0][2] for b in boxes),
            max(b[0][3] for b in boxes))
    withglow = (min(b[1][0] for b in boxes), min(b[1][1] for b in boxes), max(b[1][2] for b in boxes),
                max(b[1][3] for b in boxes))
    return body, withglow, round(reach, 1)


def loop_seam():
    """Frame 8 of the loop (one past its last) drawn by the same rule, against frame 0: identical when seamless."""
    n = len(SG.SEQS['loop'])
    ph, tn = SG.loop_state(n)
    a = SG.gate(1.0, ph, tn, 1.0, 0, sparks=0, seed=0)[0]
    b = SG.gate(1.0, 0.0, 0.0, 1.0, 0, sparks=0, seed=0)[0]
    return a == b


def body_centre(px, keys=None):
    pts = [q for q, k in px.items() if k not in ('W', 'Y') and (keys is None or k in keys)]
    if not pts:
        return None
    return (round(sum(q[0] for q in pts) / len(pts), 1), round(sum(q[1] for q in pts) / len(pts), 1))


def contract():
    gate_body, gate_glow, reach = gate_drawn()
    fw, fh = SG.CFG['FW'], SG.CFG['FH']
    slash = [M.slash_frame(i) for i in range(4)]
    dive = [M.dive_frame(i) for i in range(5)]
    emerge = [M.emerge_frame(i) for i in range(len(M.EMERGE_TIMES))]
    tip = M.blade_line(M.CONTACT_HILT, M.CONTACT_DEG, M.CONTACT_LEN, 2.5)(1.0)[0]
    return {
        'palette': {k: H.hexs(k) for k in sorted(H.PAL)},
        'glow_palette_additive': {k: '#%02X%02X%02X' % v[:3] for k, v in sorted(H.GLOW.items())},
        'small_portal': {
            'files': ['josh_small_portal_%s_%s.png' % (s, l) for s in SG.ORDER for l in ('back', 'glow')],
            'ship_to': SHIP['gate'],
            'frame': [fw, fh],
            'pivot': list(SG.CFG['PIVOT']),
            'pivot_is': 'the opening centre (corner convention, offset = frame/2 - pivot; the pivot is the frame centre, so flip_h is free)',
            'FLOOR_DROP_texels': SG.CFG['FLOOR_DROP'],
            'FLOOR_DROP_px_at_3x': SG.CFG['FLOOR_DROP'] * 3,
            'scale': 3,
            'layers': {'back': 'normal blend, drawn behind whatever comes out', 'glow': 'additive (blend ADD)'},
            'sequences': {s: {'frames': len(SG.SEQS[s]), 'times': SG.SEQS[s], 'total': round(sum(SG.SEQS[s]), 3),
                              'loops': s in SG.LOOPS} for s in SG.ORDER},
            'sequence_notes': {
                'open': 'frame 0 is the dealt card flipping open at the pivot; runs into loop frame 0',
                'loop': 'seamless (the card ring turns back two slots while the vortex turns two arms)',
                'burst': 'the flare as the figure comes out: vortex white-hot, the ring blown out; back into the loop',
                'close': 'ends on an empty frame; free the node after it',
            },
            'drawn_box_texels': {'back': list(gate_body), 'with_glow': list(gate_glow)},
            'drawn_size_texels': [gate_body[2] - gate_body[0] + 1, gate_body[3] - gate_body[1] + 1],
            'drawn_size_px_at_3x': [3 * (gate_body[2] - gate_body[0] + 1), 3 * (gate_body[3] - gate_body[1] + 1)],
            'reach_from_pivot_texels': reach,
            'opening_radius_texels': SG.CFG['R_VORTEX'],
            'rim_outer_radius_texels': SG.CFG['R_VORTEX'] + SG.CFG['RIM_W'],
            'neutral': 'one look for every small gate: the marks (strong parry badge / pale X) are the only difference',
            'badge_anchor_suggestion_px': 'badge tip %d px over the gate top: pivot.y - %d px' % (6, 21 * 3 + 6),
        },
        'josh_dive': {
            'file': 'josh_dive.png', 'ship_to': SHIP['josh'],
            'frame': [80, 80], 'feet': [40, 79], 'facing': 'right (flip_h for the left gate)',
            'frames': 5, 'times': M.DIVE_TIMES, 'total': round(sum(M.DIVE_TIMES), 3),
            'beats': ['crouch', 'leap (the deck flung ahead)', 'dive (a card leading him in)',
                      'dive (folding into cards, head and hat first)', 'vanish (a twist of cards)'],
            'heading_deg_above_horizontal': 40,
            'body_centre_texels_per_frame': [body_centre(p) for p in dive],
            'dive_centre': list(M.DIVE_CENTRE),
            'aim_note': 'raise him until DIVE_CENTRE (his middle on the airborne frames, texels in the cell) meets '
                        'the opening, not his feet: it sits %d px over the feet anchor at 3x' % ((79 - M.DIVE_CENTRE[1]) * 3),
            'vanish_at': list(M.VANISH_AT),
        },
        'josh_emerge': {
            'file': 'josh_emerge.png', 'ship_to': SHIP['josh'], 'optional': True,
            'frame': [80, 80], 'feet': [40, 79], 'facing': 'right',
            'frames': len(M.EMERGE_TIMES), 'times': M.EMERGE_TIMES, 'total': round(sum(M.EMERGE_TIMES), 3),
            'beats': ['cards pour out of the gate', 'dropping out feet first, winded',
                      'THUD: squat, arms out, cards burst round his boots', 'josh_recovery frame 0 (hands off to recover)'],
            'body_centre_texels_per_frame': [body_centre(p) for p in emerge],
            'on_floor_from_frame': 2,
        },
        'josh_monte_slash': {
            'file': 'josh_monte_slash.png', 'ship_to': SHIP['josh'],
            'frame': [M.SLASH_FW, M.SLASH_FH], 'feet': list(M.SLASH_FEET),
            'facing': 'right, blade reaching right; flip_h mirrors about the feet (column 64 = frame centre)',
            'frames': 4, 'times': M.SLASH_TIMES,
            'dash_frames_0_1_total': round(M.SLASH_TIMES[0] + M.SLASH_TIMES[1], 3),
            'contact_frame': 2, 'follow_through_frame': 3,
            'beats': ['burst out: low launch, sabre trailing, cards peeling off behind',
                      'the draw: dashing, sabre held back flat at his hip',
                      'CONTACT: rising cut across the player\'s middle, smear from the floor to the blade',
                      'follow-through: the cut carried up and away'],
            'blade': 'five of his gold cards laid end to end (dark-gold seams, a black spade on each), one keyline, '
                     'the last card tapering to the point, a cream-card cross-guard',
            'contact_point_from_feet_texels': list(M.SLASH_CONTACT),
            'contact_point_from_feet_px_at_3x': [round(M.SLASH_CONTACT[0] * 3, 1), round(M.SLASH_CONTACT[1] * 3, 1)],
            'blade_tip_on_contact_from_feet_texels': [round(tip[0] - 40, 1), round(tip[1] - 79, 1)],
            'figure_centre_from_feet_texels': list(M.SLASH_CENTRE),
            'placement_note': 'to land the cut on the hurtbox centre H: feet = H - contact_point*3 (x mirrored when flipped)',
            'drawn_box_per_frame': [list(bbox(p)) for p in slash],
        },
        'josh_monte_scatter': {
            'file': 'josh_monte_scatter.png', 'ship_to': SHIP['cards'], 'optional': True,
            'frame': [M.SCATTER_FW, M.SCATTER_FH], 'pivot': list(M.SCATTER_PIVOT),
            'pivot_is': 'the figure\'s centre: put it on feet + figure_centre_from_feet (x mirrored when flipped)',
            'frames': 6, 'times': M.SCATTER_TIMES, 'total': round(sum(M.SCATTER_TIMES), 3),
            'beats': ['the pop: the pack flashed white and gold in his shape',
                      'the cards flung out all round, spinning, thinning out, the last six falling'],
        },
        'loop_seamless': loop_seam(),
    }


def audit(spec):
    im = spec['image'].convert('RGBA')
    px = list(im.get_flattened_data()) if hasattr(im, 'get_flattened_data') else list(im.getdata())
    opaque = [p for p in px if p[3]]
    semi = sum(1 for p in opaque if p[3] != 255)
    glow = 'glow' in spec['layer']
    pal = set(v[:3] for v in (H.GLOW if glow else H.PAL).values())
    off = sum(1 for p in opaque if p[:3] not in pal)
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
    # pixels on a frame's border (a sole's keyline on the bottom row of a floor frame is expected)
    border = 0
    for i in range(spec['frames']):
        for y in range(Hh):
            for x in (i * fw, i * fw + fw - 1):
                border += 1 if a[x, y] else 0
        for x in range(i * fw, i * fw + fw):
            border += 1 if a[x, 0] else 0
    empties = [i for i in range(spec['frames']) if im.crop((i * fw, 0, (i + 1) * fw, Hh)).getbbox() is None]
    black = sum(1 for p in opaque if p[:3] == (0, 0, 0))
    return dict(opaque=len(opaque), semi_alpha=semi, off_palette=off, colours=len(set(p[:3] for p in opaque)),
                strays=strays, border_pixels_top_left_right=border, empty_frames=empties,
                black_ratio=round(black / max(1, len(opaque)), 3))
