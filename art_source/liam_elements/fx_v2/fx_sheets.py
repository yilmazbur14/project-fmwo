"""FX v2: every sheet this pass delivers, with the numbers the code needs (the contract) - cell, pivot, frames, times,
tags/phase map, how the code plays it, and which approved palette it may use. Nothing here writes a file.

Addendum 3 E.1/E.2 (the hooks a coder is landing first): frame counts come off each sheet's width; a one-shot keeps
its shipped length (extra frames split it, `spread`); a loop keeps its frame time unless this contract gives a new one;
the breath plays frame 0 once, loops 1..n-2 and ends on n-1; the ridge may ship as per-clip strips.
"""
import sys

sys.dont_write_bytecode = True

import fx_common as C
import fx_water as W
import fx_air as A
import fx_ice as I
import fx_earth as E

# The shipped cells (approval/anchors.json) and frame counts, which only frame counts may grow from.
SHIPPED = {
    'liam_wave_crest': ((94, 40), 3), 'liam_wave_body': ((94, 80), 1), 'liam_wave_tell': ((282, 24), 3),
    'liam_wave_collapse': ((282, 120), 3), 'liam_wave_splash': ((32, 32), 4),
    'liam_gust_burst': ((48, 48), 4), 'liam_gust_trail': ((24, 32), 3), 'liam_cold_breath': ((40, 100), 4),
    'liam_ice_melt': ((64, 64), 3), 'liam_ice_shatter': ((64, 64), 4), 'liam_freeze_front': ((16, 16), 3),
    'liam_tremor_block': ((96, 32), 17), 'liam_tremor_crack': ((16, 8), 3), 'liam_slam_burst': ((32, 16), 3),
    'liam_pillar_dust': ((64, 80), 3),
}


def all_sheets():
    """Every v2 sheet: name, frames (key canvases), per-frame times (s), tags, layer, palette group, contract."""
    S = []

    def add(name, frames, times, tags, group, play, pivot=None, notes='', code='', layer=None, extra=None):
        d = dict(name=name, frames=frames, times=times, tags=tags, group=group, play=play, pivot=pivot,
                 notes=notes, code=code, layer=layer or name.replace('liam_', ''))
        if extra:
            d.update(extra)
        S.append(d)

    # ---------------------------------------------------------------- WATER (attack 1)
    add('liam_wave_crest', [W.crest_strip(f) for f in range(W.NF)], [W.FRAME_TIME] * W.NF,
        [('crest', 0, W.NF - 1)], 'water', 'loop',
        notes='three barrels a tile peeling toward the rope end one barrel a loop; the lip rolls forward, the '
              'whitewater tumbles and boils, spray fountains off every plunge point; row 39 is the band\'s front edge '
              'in every frame; seamless left-right',
        code='frames off the sheet (94x40 cells); WAVE_FRAME_TIME 0.1 -> 0.06 (shared with the tell)')
    add('liam_wave_body', [W.body_tile(f) for f in range(W.NF)], [W.FRAME_TIME] * W.NF,
        [('body', 0, W.NF - 1)], 'water', 'loop (optional hook)',
        notes='frame 0 is a drop-in static body (the code reads only the first 94 columns today); frames 1-11 are a '
              'subtle shimmer that lines up with the crest frame for frame',
        code='OPTIONAL HOOK (not in addendum 3): step the body tiles\' region x by frame*94 with the crest\'s frame')
    add('liam_wave_tell', [W.tell_swell(k) for k in range(W.TELL_FRAMES)], [W.FRAME_TIME] * W.TELL_FRAMES,
        [('rise', 0, W.TELL_RISE - 1), ('tremble', W.TELL_RISE, W.TELL_FRAMES - 1)], 'water',
        'loop at WAVE_FRAME_TIME (as built)',
        notes='rises over 0-4 and trembles at full height 5-7, its humps curling into small lips; at 0.06 s a frame '
              'the default 0.45 s tell plays 0..7 once',
        code='frames off the sheet width (as built); optional: after the first pass loop 5-7 only, if wave_tell ever '
             'exceeds 0.48 s')
    add('liam_wave_collapse', [W.collapse(k) for k in range(W.COLLAPSE_FRAMES)],
        [0.3 / W.COLLAPSE_FRAMES] * W.COLLAPSE_FRAMES, [('collapse', 0, W.COLLAPSE_FRAMES - 1)], 'water',
        'one-shot spread over wave_collapse_time (0.3 s, as built)',
        notes='0 barrels cave in and a crown of spray bursts up; 1 it towers; 2 it tears into droplets; 3-4 they rain '
              'down and ring out on the floor; 5-7 the last foam; stays inside its 282x120 band',
        code='frames off the sheet width (as built)')
    add('liam_wave_splash', [W.splash(k) for k in range(W.SPLASH_FRAMES)], W.SPLASH_TIMES,
        [('splash', 0, W.SPLASH_FRAMES - 1)], 'water', 'one-shot, 0.26 s (shipped length)', pivot=W.SPLASH_PIVOT,
        notes='0 flash; 1 a crown of jets off a ring; 2 jets at height, tips breaking; 3-4 droplets arc out; '
              '5 they land in tiny rings; 6 the last ripple',
        code='WAVE_SPLASH_TIMES = these (or spread over 0.26 s)')
    add('liam_flood_ripple', [W.flood_ripple(k) for k in range(W.RIPPLE_FRAMES)], [W.RIPPLE_TIME] * W.RIPPLE_FRAMES,
        [('ripple', 0, W.RIPPLE_FRAMES - 1)], 'floor', 'loop (optional hook)',
        notes='NEW, optional: rings and glints over the standing water, drawn clipped to the flood so the six '
              'nested coverage frames stay exactly as shipped; seamless 64x64 tile, semi-transparent (^ and ")',
        code='OPTIONAL HOOK: LiamFlood - a tiled sprite of this sheet as a child of water_sheet with '
             'water_sheet.clip_children = CLIP_CHILDREN_AND_DRAW, stepping its frames every 0.1 s')

    # ---------------------------------------------------------------- AIR
    add('liam_gust_burst', [A.gust_burst(k) for k in range(A.BURST_FRAMES)], A.BURST_TIMES,
        [('burst', 0, A.BURST_FRAMES - 1)], 'air_debris', 'one-shot, 0.29 s (shipped length)', pivot=A.BURST_PIVOT,
        notes='0 air sucked in to a vortex on the tip; 1 a lit puff and a pressure crescent burst down the ring, '
              'speed lines fanning; 2-3 fronts roll out, air curling back off their ends in open hooks, slate chips '
              'kicked up; 4-6 fronts thin and break',
        code='GUST_BURST_TIMES = these (or spread over 0.29 s)')
    add('liam_gust_trail', [A.gust_trail(k) for k in range(A.TRAIL_FRAMES)], [A.TRAIL_TIME] * A.TRAIL_FRAMES,
        [('trail', 0, A.TRAIL_FRAMES - 1)], 'air_debris', 'loop', pivot=A.TRAIL_PIVOT,
        notes='streaks rushing down past both sides of the launched player 5 texels a frame, an eddy tumbling down '
              'each side, grit in the flow; the middle stays light so the player reads',
        code='GUST_TRAIL_FRAME_TIME 0.07 -> 0.05')
    add('liam_cold_breath', [A.cold_breath(k) for k in range(A.BREATH_FRAMES)], [A.BREATH_TIME] * A.BREATH_FRAMES,
        [('start', 0, 0), ('loop', 1, A.BREATH_FRAMES - 2), ('end', A.BREATH_FRAMES - 1, A.BREATH_FRAMES - 1)],
        'air', 'frame 0 once, loop 1..n-2, last frame on stop (addendum 3 E.2.4)', pivot=A.BREATH_PIVOT,
        notes='0 a frosty jet bursting out of his lips; 1-6 the plume at full length (97 texels to the pillar\'s '
              'foot): three streams fanning, swirls rolling down them, a frost veil between, ice crystals glinting; '
              '7 it lets go and breaks up',
        code='BREATH_FRAME_TIME 0.1 -> 0.06')
    add('liam_downdraft', [A.downdraft(k) for k in range(A.DRAFT_FRAMES)], [A.DRAFT_TIME] * A.DRAFT_FRAMES,
        [('gust', 0, A.DRAFT_FRAMES - 1)], 'air', 'loop in place while the code drops it', pivot=A.DRAFT_PIVOT,
        notes='NEW: one gust of the downdraft - a long wavy line and a shorter one beside it, snaking, the long one\'s '
              'head curling over; cold cyan edge so it reads on ice and water; pivot = its top centre (its tail), '
              'so it pours out of the row\'s foot',
        code='LiamElementFx.downdraft (addendum 3 E.2.7): spawn every 0.03 s at a random x on the row line (y 348), '
             'fall at downdraft_speed x 1.5 (1800 px/s), fade; FxLayer; start each on a random frame')

    # ---------------------------------------------------------------- ICE
    add('liam_freeze_front', [I.freeze_front(k) for k in range(I.FRONT_FRAMES)], [I.FRONT_TIME] * I.FRONT_FRAMES,
        [('front', 0, I.FRONT_FRAMES - 1)], 'floor', 'loop', pivot=(8, 8),
        notes='0 a seed; 1-3 six arms shooting out and branching; 4 it glints; 5 it sets into the sheet as the next '
              'seed forms; the pieces ride the growing edge, so the rim reads as crystals sprouting all along it',
        code='FROST_FRAME_TIME 0.12 -> 0.08')
    add('liam_ice_melt', [I.ice_melt(k) for k in range(I.MELT_FRAMES)], [1.0 / I.MELT_FRAMES] * I.MELT_FRAMES,
        [('melt', 0, I.MELT_FRAMES - 1)], 'floor', 'spread over melt_time (as built)',
        notes='0 the sheet sweats, beads along its seams; 1 beads run in drips, wet patches open; 2 puddles between '
              'floes, drips off their edges; 3 slush, drips ringing as they land; 4 the last slush; 5 = flood frame 5 '
              'texel for texel',
        code='frames off the sheet width (addendum 3 E.2.3)')
    add('liam_ice_shatter', [I.ice_shatter(k) for k in range(I.SHATTER_FRAMES)],
        [0.4 / I.SHATTER_FRAMES] * I.SHATTER_FRAMES, [('shatter', 0, I.SHATTER_FRAMES - 1)], 'floor',
        'spread over SHATTER_TIME (0.4 s, as built)',
        notes='0 cracks race across; 1 the web closes into plates; 2 plates heave, lit rims and tilted faces, shards '
              'spitting from the seams; 3 they part; 4 they break smaller; 5-7 the last pieces and glinting shards',
        code='frames off the sheet width (addendum 3 E.2.3)')

    # ---------------------------------------------------------------- EARTH
    base = 0
    for clip in E.CLIPS:
        fr = E.clip_frames(clip)
        times = E.CLIP_TIMES[clip]
        play = 'loop, 0.12 s a frame' if clip == 'active' else 'one-shot, %.2f s (shipped length)' % sum(times)
        add('liam_tremor_block_%s' % clip, fr, times, [(clip, 0, len(fr) - 1)], 'earth', play,
            notes={'tell': 'the footprint\'s cracks spreading and lighting earth green, the white core racing through '
                           'them last; dust shivering out of the cracks, pebbles hopping',
                   'heave': '0 ice plates break, chips spit up; 1-2 the rock punches up (a third, two thirds) with '
                            'chunks flung above it and dust bursting at its foot; 3 full height, debris raining '
                            'back; 4 it settles, pebbles bouncing down its slopes; 5 dust thinning',
                   'active': 'the standing ridge trembling a texel, crevices flickering, a pebble trickling down a '
                             'slope and a wisp of dust off its foot',
                   'pulse': 'each slam flares the crevices green-white, pebbles jump off the summits, dust kicks off '
                            'its foot, then it settles',
                   'crumble': '0 splits along dark seams; 1 slabs break apart, chunks flying; 2 sinks to half in '
                              'dust; 3 a heap, chunks bouncing; 4 scattered stones; 5 the last pebbles'}[clip],
            code='per-clip strip (addendum 3 E.2.6): 96x32 cells, footprint rows 8..31 as shipped',
            extra=dict(preview_base=base, clip=clip))
        base += len(fr)
    comb = E.combined_frames()
    add('liam_tremor_block', comb,
        [0.15] * 4 + [0.06, 0.08, 0.10] + [0.12] * 4 + [0.06, 0.10] + [0.08] * 4,
        [('tell', 0, 3), ('heave', 4, 6), ('active', 7, 10), ('pulse', 11, 12), ('crumble', 13, 16)], 'earth',
        'the shipped 17-frame layout and TREMOR_CLIPS (fallback only)',
        notes='cut from the v2 clips (tell %s, heave %s, active %s, pulse %s, crumble %s) for the code\'s fallback '
              'path; the per-clip strips win when they exist' % tuple(E.COMBINED_PICK[c] for c in E.CLIPS),
        code='none: today\'s combined-sheet path, unchanged')
    add('liam_tremor_crack', [E.crack_segment(k) for k in range(E.CRACK_FRAMES)], [E.CRACK_TIME] * E.CRACK_FRAMES,
        [('crack', 0, E.CRACK_FRAMES - 1)], 'earth', 'loop', pivot=(0, 4),
        notes='the full crack glowing along the shipped path every frame (never shorter), a white pulse running '
              'along it, dust puffs and pebbles spat out one side then the other',
        code='TREMOR_CRACK_FRAME_TIME 0.08 -> 0.06; optional: segment i shows frame (frame - i) mod n so the spit '
             'travels out along the crack')
    add('liam_slam_burst', [E.slam_burst(k) for k in range(E.SLAM_FRAMES)], E.SLAM_TIMES,
        [('burst', 0, E.SLAM_FRAMES - 1)], 'earth', 'one-shot, 0.22 s (shipped length)', pivot=E.SLAM_PIVOT,
        notes='0 green flash ring, white core; 1 rocks launched, dust bursting; 2 rocks at the top of their arc; '
              '3 falling, dust rolling out; 4 landed, dust spreading; 5 dust thinning',
        code='SLAM_BURST_TIMES = these (or spread over 0.22 s)')
    add('liam_pillar_dust', [E.pillar_dust(k) for k in range(E.DUST_FRAMES)], [E.DUST_TIME] * E.DUST_FRAMES,
        [('dust', 0, E.DUST_FRAMES - 1)], 'dust', 'one-shot, every frame PILLAR_DUST_FRAME_TIME', pivot=(32, 72),
        notes='0 dust bursting out both sides of the foot, pebbles kicked; 1-2 billows rolling out and up, pebbles '
              'arcing; 3 they spread, pebbles land; 4-6 they thin and drift away',
        code='PILLAR_DUST_FRAME_TIME 0.08 -> 0.065: 0.455 s (shipped 0.24 s) - a deliberate lengthening of a '
             'cosmetic one-shot, so the dust lingers through the 0.6 s rise; 0.034 keeps 0.24 s if preferred')
    for d in S:
        d['cell'] = (int(d['frames'][0].shape[1]), int(d['frames'][0].shape[0]))
        d['shipped'] = SHIPPED.get(d['name'])
        d['allowed'] = C.ALLOWED[d['group']]
    return S


def gif_numbers(sheets):
    """The few numbers the GIFs time the v2 frames with (read off the sheets above)."""
    by = {d['name']: d for d in sheets}
    clips = {}
    for d in sheets:
        if d.get('clip'):
            n = len(d['frames'])
            clips[d['clip']] = {'frames': list(range(d['preview_base'], d['preview_base'] + n)), 'times': d['times']}
    return {
        'wave_frame_time': W.FRAME_TIME, 'wave_crest_frames': W.NF,
        'wave_splash_times': by['liam_wave_splash']['times'],
        'flood_ripple_time': W.RIPPLE_TIME,
        'gust_burst_times': by['liam_gust_burst']['times'], 'gust_trail_time': A.TRAIL_TIME,
        'breath_time': A.BREATH_TIME, 'breath_frames': A.BREATH_FRAMES,
        'downdraft_time': A.DRAFT_TIME,
        'frost_time': I.FRONT_TIME, 'crack_time': E.CRACK_TIME,
        'slam_burst_times': by['liam_slam_burst']['times'], 'pillar_dust_time': E.DUST_TIME,
        'tremor_clips': clips,
    }
