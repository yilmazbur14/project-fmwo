"""Writes contract.json: sizes, anchors, frame order + timings, the drop frame, and per-frame
trophy rects / hand points - all computed from the same modules that drew the art, and checked
against the built PNGs (every hand point must land on a glove pixel of that frame)."""
import json
import os
import sys
sys.dont_write_bytecode = True
from PIL import Image
from common import OUT, BURAK
import trophy as T
import burak as BK
import champion as C
import build as BD

# glove boxes (2x2, top-left, BODY coords) per frame: left glove, right glove
GLOVES = {
    'arrive': ((11, 8), (18, 9)),
    'take_in': ((8, 16), (21, 16)),
    'reach': ((5, 22), (24, 22)),
    'grab': ((7, 31), (22, 31)),
    'gather_a': ((7, 31), (22, 31)),
    'gather_b': ((7, 30), (22, 30)),
    'lift': ((7, -1), (22, -1)),
    'settle': ((7, 0), (22, 0)),
    'hold_1': ((6, -1), (21, -1)),
    'hold_2': ((7, 1), (22, 1)),
    'hold_3': ((8, -1), (23, -1)),
    'hold_4': ((7, 1), (22, 1)),
}
DUR = {'arrive': 0.30, 'take_in': 0.40, 'reach': 0.15, 'grab': 0.25, 'gather_a': 0.10,
       'gather_b': 0.10, 'lift': 0.10, 'settle': 0.10, 'hold_1': 0.20, 'hold_2': 0.20,
       'hold_3': 0.20, 'hold_4': 0.20}
GLOVE_RGB = {BURAK[k][:3] for k in 'bcB'}


def cell(pt):
    return [pt[0] + C.BODY_AT[0], pt[1] + C.BODY_AT[1]]


def main():
    sheets = {t: Image.open(os.path.join(OUT, 'champion', f'champion_lift_{t}.png')).convert('RGBA')
              for t in 'AB'}
    frames = []
    problems = []
    for i, n in enumerate(BK.ORDER):
        (lx, ly), (rx, ry) = GLOVES[n]
        hl, hr = cell((lx + 1, ly + 1)), cell((rx + 1, ry + 1))
        for t in 'AB':
            px = sheets[t].load()
            for gx, gy in ((lx, ly), (rx, ry)):
                X, Y = cell((gx, gy))
                if px[i * 40 + X, Y][:3] not in GLOVE_RGB:
                    problems.append(f'{t} {n}: glove box at body ({gx},{gy}) is not glove-blue')
        tro = {}
        for t in 'AB':
            x, y, w, h = C.trophy_rect(t, n)
            tro[t] = {'rect': [x, y, w, h], 'bottom_centre': [x + T.spec(t)['CX'], y + h - 1],
                      'on_stand': BK.TROPHY_AT[n][1] >= BK.SEAT_Y - 1,
                      'from_hands_midpoint': [x + T.spec(t)['CX'] - (hl[0] + hr[0]) / 2,
                                              y + h - 1 - (hl[1] + hr[1]) / 2]}
        frames.append({'index': i, 'name': n, 'seconds': DUR[n],
                       'hand_left': hl, 'hand_right': hr, 'trophy': tro})
    if problems:
        raise SystemExit('\n'.join(problems))

    texel = 3
    mark_texel = (320, 165)            # body origin (the player's sprite centre) at the mark
    contract = {
        'what': 'Champion ending cutscene - APPROVAL PASS art contract (nothing ships yet)',
        'date': '2026-10-06',
        'recommended_take': 'A',
        'units': 'All art is authored in texels and drawn at scale 3 (1 texel = 3 screen px), '
                 'like every arena sprite. Cell coords are texels inside one frame.',
        'player': {
            'source': 'Assets/Characters/MainPlayer/player_4dir_sheet.png (32x32 cells, 7 colours, no keyline)',
            'walk_in': 'use his own sheet: row 0 (down) cols 0-4, 0.1667 s a frame (the "walking" '
                       'animation). Recommended entry: the TOP rope doorway (screen x 852..1068), '
                       'walking straight down to the mark, so he faces the camera all the way and '
                       'arrives behind the stand. (Bottom-gate entry also works but must path round '
                       'the stand; the art is the same.)',
            'mark_screen_px': [mark_texel[0] * texel, mark_texel[1] * texel],
            'walk_from_screen_px': [960, (10 + 16) * texel],
            'walk_seconds_in_mock': 2.3,
        },
        'cell': {
            'size': list(C.CELL),
            'body_box_origin': list(C.BODY_AT),
            'body_box_note': 'the player 32x32 cell sits at cell (4,21)-(35,52) in EVERY frame of '
                             'every 40x64 sheet here; his sprite centre (4dir cell 16,16) = cell (20,37); '
                             'shoe soles on cell row 49.',
            'godot_sprite2d': 'centered=true, scale=(3,3), offset=Vector2(0,-5), node at the player '
                              'mark (his CharacterBody2D position). Or centered=false at mark - (60,111) px.',
            'stand_rect': [C.BODY_AT[0] + C.STAND_AT[0], C.BODY_AT[1] + C.STAND_AT[1], T.S['W'], T.S['H']],
            'stand_seat_row': C.BODY_AT[1] + BK.SEAT_Y,
            'stand_floor_contact_centre': [C.BODY_AT[0] + 15, C.BODY_AT[1] + C.STAND_AT[1] + T.S['H'] - 1],
        },
        'files': {
            'trophy/trophy_stand_idle_{A,B}.png': {
                'frames': len(BD.IDLE), 'cell': list(C.CELL),
                'what': 'the stand with the cup waiting on it, shine + sparkle loop. Same 40x64 '
                        'registration as the champion sheet: put it at the player mark with the same '
                        'Sprite2D settings. Draw it ABOVE the player while he walks in (he is always '
                        'north of it).',
                'seconds_per_frame': [d for _, _, d in BD.IDLE], 'loop': True,
            },
            'trophy/stand_empty.png': {'frames': 1, 'cell': list(C.CELL),
                                       'what': 'the stand alone, same registration (for after the '
                                               'cutscene if the stand should stay).'},
            'trophy/trophy_{A,B}.png': {'what': 'the cup alone (A 17x16, B 17x20), bottom row = '
                                                'plinth outline, centre column x=8.'},
            'champion/champion_lift_{A,B}.png': {
                'frames': len(BK.ORDER), 'cell': list(C.CELL), 'hframes': len(BK.ORDER), 'vframes': 1,
                'baked': 'stand + Burak + cup + his grip + effects, layered correctly per frame '
                         '(Burak < stand < cup < grip < fx). The .aseprite keeps those 5 layers and '
                         'champion/layers_{A,B}/*.png are the same layers as strips if the cup is '
                         'ever wanted as its own sprite.',
                'swap_in': 'when he reaches the mark showing idle_down, hide the player sprite AND '
                           'trophy_stand_idle, show this sheet at frame 0. Frame 0 is pixel-identical '
                           'to that pair (checked), so the swap is invisible.',
            },
            'fx/lift_flash.png': {'frames': 3, 'size': [640, 360], 'seconds_per_frame': 0.05,
                                  'place': 'full screen, centered=false at (0,0), scale 3',
                                  'z': 'BELOW the champion sprite, above the arena (the cup stays '
                                       'readable on the drop)',
                                  'centre_texel': [319, 140]},
            'fx/confetti_burst.png': {'frames': 28, 'size': [640, 360], 'seconds_per_frame': 0.05,
                                      'loop': False, 'place': 'full screen, over everything',
                                      'pop_texel': [319, 140],
                                      'cannons': 'the four ring corners, two streamers each'},
            'fx/confetti_rain.png': {'frames': 4, 'size': [640, 360], 'seconds_per_frame': 0.12,
                                     'loop': True, 'place': 'full screen, over everything',
                                     'note': 'victory_confetti.png rhythm and piece style, denser, '
                                             'with the cup gold weighted x3.'},
            'fx/spot_sweep.png': {'frames': 10, 'size': [640, 360],
                                  'one_shot': {'frames': [0, 7], 'seconds_per_frame': 0.06},
                                  'loop': {'frames': [8, 9], 'seconds_per_frame': 0.15},
                                  'alpha': 'semi-alpha in 4 fixed steps (30/56/80/100 of 255), normal blend',
                                  'target_texel': [320, 180]},
            'crowd/crowd_v3_roar.png': {'frames': 11, 'size_per_frame': [640, 40],
                                        'replaces': 'Assets/Environment/crowd_v3.png (frames 0-6 '
                                                    'pixel-identical, checked)'},
            'crowd/arena_ringside_crowd_roar.png': {'frames': 11, 'size_per_frame': [640, 360],
                                                    'replaces': 'Assets/Environment/arena_ringside_crowd.png '
                                                                '(frames 0-6 pixel-identical, checked)'},
            'crowd/ROAR': {'frames': [7, 8, 9, 10], 'seconds_per_frame': 0.10, 'loop': True,
                           'note': 'needs hframes 7 -> 11 on both crowd sprites and a roar() mood in '
                                   'ArenaCrowdScript (code, not art)'},
            'credits/credits_still_{A,B}.png': {'size': [640, 360], 'optional': True,
                                                'what': 'champion from behind (the approved victory '
                                                        'sprite), cup raised, backlit, roaring crowd '
                                                        'in silhouette'},
        },
        'champion_frames': frames,
        'the_drop': {
            'frame_index': BK.ORDER.index('lift'),
            'frame_name': 'lift',
            'rule': 'frame 6 (lift) must be the frame on screen at DROP_TIME (the song beat drop, '
                    '~9-10 s in - measure it from the file). Everything that hits on the drop starts '
                    'on that same tick: lift frame, lift_flash, confetti_burst, spot_sweep, crowd ROAR.',
            'lead_in': 'arrive 0.30 + take_in 0.40 + reach 0.15 + grab 0.25 = 1.10 s, then gather_a/'
                       'gather_b loop (0.10 s each) until the drop; the gather loop absorbs any '
                       'difference, so arrive at the mark >= 1.3 s before the drop.',
            'announcer': 'his line plays over the gather loop; the crowd ROAR starts on the drop and '
                         'covers the name.',
        },
        'after_the_drop': {
            'settle': 'frame 7 for 0.10 s',
            'hold_loop': 'frames 8-11 looping; 8 and 10 are the cup-up shout frames, 9 and 11 the '
                         'pumps down. Default 0.20 s a frame; to pump on the beat use (60/BPM)/2 s.',
            'confetti_rain_from': 'drop + 1.0 s (over the tail of the burst)',
            'house_lights': 'optional dim of the arena to ~35% darker over 0.3 s from the drop, so '
                            'the spotlights read (the mock uses rgba(8,6,20,90/255) over the arena only)',
            'fade': 'slow fade to black (mock: 2.5 s starting 4 s after the drop) while the hold loop '
                    'keeps playing; then credits on black.',
        },
        'mock_timeline_seconds (compressed - the drop is at 6.5 here)': {
            'fade_in': [0.0, 0.5], 'walk_in': [0.5, 2.8], 'arrive': 2.8, 'take_in': 3.1,
            'reach': 3.5, 'grab': 3.65, 'gather_loop': [3.9, 6.5], 'announcer': [3.0, 6.4],
            'DROP_lift': 6.5, 'settle': 6.6, 'hold_loop_from': 6.7, 'fade': [10.5, 13.0],
            'credits_still_fades_in': [13.6, 14.4],
        },
        'measured': {
            'burak_pixels': 'exactly his 7 sheet colours, no keyline (the source has none: black is '
                            'only hair + shoes), 0 semi-alpha',
        },
    }
    path = os.path.join(OUT, 'contract.json')
    with open(path, 'w') as f:
        json.dump(contract, f, indent=2)
    print('wrote', path, '| hand points verified on glove pixels for', len(frames), 'frames x 2 takes')


if __name__ == '__main__':
    main()
