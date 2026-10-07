"""FX v2: 1920 x 1080 in-fight mocks, one moment of attack 1 and two of attack 2, composed on the real arena capture in
the game's draw order with the v2 sheets, placed by LiamArtLayout / LiamStateMachine / addendum 3's numbers:
the pillar row along y 348 (a stand-in: the approved pillar cut to the row's 34 texels), wave_gap 60, maze B re-laid
under the row (A.5), downdraft streaks every 0.03 s from the row line at 1800 px/s. Builds images; writes nothing.
"""
import math
import sys

sys.dont_write_bytecode = True

import numpy as np
from PIL import Image, ImageDraw

import fx_common as C
import fx_scene as SC
import fx_present as FP

FULL = (0, 0, 1920, 1080)
# maze B under the row (addendum 3 A.5): footprint top-lefts, 288 x 72 each
B_UPPER = [(1517, 388), (1277, 424), (1060, 460), (820, 498), (580, 498), (340, 498)]
B_LOWER = [(113, 720), (353, 720), (593, 726), (833, 732), (1073, 734)]
BLOCKS = [(x, y, 288, 72) for (x, y) in B_UPPER + B_LOWER]


def caption(im, lines):
    d = ImageDraw.Draw(im)
    fb, fs = FP.font(16), FP.font(13)
    h = 26 + 18 * (len(lines) - 1)
    bar = Image.new('RGBA', (1920, h), (0, 0, 0, 185))
    im.alpha_composite(bar, (0, 1080 - h))
    d.text((10, 1080 - h + 4), lines[0], fill=(255, 255, 255), font=fb)
    for i, t in enumerate(lines[1:]):
        d.text((10, 1080 - h + 24 + 18 * i), t, fill=(205, 215, 225), font=fs)


def _block_frame(P, clip, t_into):
    """The v2 ridge's frame t_into seconds into a clip (one-shots hold their last frame)."""
    fr = P.v2['liam_tremor_block']
    c = FP_CLIPS[clip]
    frames, times = c['frames'], c['times']
    if clip == 'active':
        return fr.big(frames[FP.loop_index(t_into, times)])
    i = FP.once_index(t_into, times)
    return fr.big(frames[i if i is not None else len(frames) - 1])


FP_CLIPS = {}


def mock_attack1(P, nums):
    """Mid-tsunami: the left wave rolling on the player's half, the right wave coming out of the row's foot 420 px behind
    it (wave_gap 60), the next left wave's swell rising over the rope, the flood a third full with ripples, Liam casting."""
    s = SC.Shot(P.arena, FULL)
    water = s.tile(P.old['liam_flood'].small[2])
    s.tile(P.v2['liam_flood_ripple'].small[3], clip_to=water)
    ft = nums['wave_frame_time']
    n = nums['wave_crest_frames']
    for (side, front, clock) in (('left', 820, 1.62), ('right', 400, 0.92)):
        f = int(clock / ft) % n
        body = P.v2['liam_wave_body'].small[f]
        crest = P.v2['liam_wave_crest'].small[f]
        big, pos = (SC.band_left if side == 'left' else SC.band_right)(body, crest, front)
        s.paste(big, pos)
    tell = P.v2['liam_wave_tell']
    tb = tell.big(int(0.22 / ft) % len(tell))
    s.paste(tb, (SC.WAVE_LEFT_X[1] - tb.width, 114 - tb.height))
    s.ropes()
    SC.liam_on_pillar(s, P.pillar.big(5), P.poses['cast_left'].big(1), row=True)
    s.player((1330, 880))
    s.hud()
    im = s.result()
    caption(im, ['LIAM FX v2 - ATTACK 1 MOCK (mid-tsunami)',
                 'waves 846 x 360 on the WaveLayer under the ropes and the row: crest 12 frames of rolling barrels with '
                 'spray fountains, body shimmer, the next swell rising and trembling over the rope (left), the flood a '
                 'third full with the optional ripple overlay',
                 'the row is a STAND-IN (the approved pillar cut to 34 texels, 108 px apart) for context only; waves '
                 'spaced by addendum 3\'s wave_gap 60; HUD at 0.30'])
    return im


def _floor_attack2(s, P, t, ice_radius):
    water = s.tile(P.old['liam_flood'].small[5])
    s.tile(P.v2['liam_flood_ripple'].small[int(t / 0.1) % 12], clip_to=water)
    s.tile(P.old['liam_ice'].small[0], mask=SC.ice_circle(ice_radius))


def mock_attack2_build(P, nums):
    """0.95 s into attack 2: the crack slam 0.15 s ago - the cracks halfway out to every ridge, every footprint glowing;
    the ice 650 px out from the pillar's foot, frost sprouting on its rim; the downdraft pouring out of the row's foot
    and blowing the player down the ring."""
    t = 0.95
    s = SC.Shot(P.arena, FULL)
    r = 1000.0 * (t - 0.3)
    _floor_attack2(s, P, t, r)
    fr = P.v2['liam_freeze_front']
    for pos in SC.frost_positions(r):
        s.at_pivot(fr.big(int((t - 0.3) / nums['frost_time'])), pos, (8, 8))
    # the maze's tell: cracks racing from the pillar's foot, footprints glowing
    reach_all = max(math.hypot(min(max(960, bx), bx + bw) - 960, min(max(348, by), by + bh) - 348)
                    for (bx, by, bw, bh) in BLOCKS)
    reach = reach_all / 0.3 * (t - 0.8)
    crack = P.v2['liam_tremor_crack']
    k = int((t - 0.8) / nums['crack_time'])
    for rect in sorted(BLOCKS, key=lambda b: b[1]):
        for i, (pos, ang) in enumerate(SC.crack_segments(rect, reach)):
            SC.paste_crack(s, crack.small[(k + i) % len(crack)], pos, ang)
    for rect in sorted(BLOCKS, key=lambda b: b[1]):
        s.paste(_block_frame(P, 'tell', t - 0.8), (rect[0], rect[1] - 24))
    SC.liam_on_pillar(s, P.pillar.big(5), P.poses['slam'].big(3), row=True)
    butt = SC.pose_point((65, 95))
    sb = P.v2['liam_slam_burst']
    i = FP.once_index(t - 0.8, nums['slam_burst_times'])
    if i is not None:
        s.at_pivot(sb.big(i), (round(butt[0]), round(butt[1])), (16, 15))
    s.player((430, 655))
    spawns = FP.draft_spawns(t - 0.3)
    FP.draw_downdraft(s, P, t - 0.3, spawns)
    s.hud()
    im = s.result()
    caption(im, ['LIAM FX v2 - ATTACK 2 MOCK (the downdraft build, 0.95 s in)',
                 'NEW downdraft gusts pouring out of the row\'s foot (one every 0.03 s, 1800 px/s, fading); ice spreading '
                 'at 1000 px/s with frost crystals sprouting on its rim; the crack slam 0.15 s ago: cracks spitting dust '
                 'on their way out to maze B (re-laid under the row), footprints glowing earth green',
                 'the row is a STAND-IN for context only; slam burst at the staff butt; the flood\'s ripple is the '
                 'optional overlay; HUD at 0.30'])
    return im


def mock_attack2_heave(P, nums):
    """1.5 s in: the heave slam 0.1 s ago - every ridge punching up out of the ice with debris flying, dust bursting at
    their feet; the last downdraft gusts fading out; the player in the bottom lane."""
    t = 1.5
    s = SC.Shot(P.arena, FULL)
    _floor_attack2(s, P, t, 1200.0)
    crack = P.v2['liam_tremor_crack']
    k = int((t - 0.8) / nums['crack_time'])
    for rect in sorted(BLOCKS, key=lambda b: b[1]):
        for i, (pos, ang) in enumerate(SC.crack_segments(rect, 5000)):
            SC.paste_crack(s, crack.small[(k + i) % len(crack)], pos, ang)
    for j, rect in enumerate(sorted(BLOCKS, key=lambda b: b[1])):
        s.paste(_block_frame(P, 'heave', t - 1.4 + 0.01 * (j % 3)), (rect[0], rect[1] - 24))
    SC.liam_on_pillar(s, P.pillar.big(5), P.poses['slam'].big(3), row=True)
    butt = SC.pose_point((65, 95))
    sb = P.v2['liam_slam_burst']
    i = FP.once_index(t - 1.4, nums['slam_burst_times'])
    if i is not None:
        s.at_pivot(sb.big(i), (round(butt[0]), round(butt[1])), (16, 15))
    s.player((1650, 890))
    spawns = [sp for sp in FP.draft_spawns(1.1) if sp[0] > 0.85]
    FP.draw_downdraft(s, P, t - 0.3, spawns)
    s.hud()
    im = s.result()
    caption(im, ['LIAM FX v2 - ATTACK 2 MOCK (just after the heave, 1.5 s in)',
                 'every ridge of maze B punching up out of the ice 0.1 s after the heave slam: chunks flung above it, '
                 'dust bursting at its foot (per-clip strip liam_tremor_block_heave); the cracks still glowing; the last '
                 'downdraft gusts fading as it stops at the heave',
                 'the row is a STAND-IN for context only; ice full; slam burst at the staff butt; HUD at 0.30'])
    return im


MOCKS = [('mock_attack1', mock_attack1), ('mock_attack2_downdraft', mock_attack2_build),
         ('mock_attack2_heave', mock_attack2_heave)]


def build(P, nums):
    FP_CLIPS.clear()
    FP_CLIPS.update(nums['tremor_clips'])
    return [(name, fn(P, nums)) for name, fn in MOCKS]
