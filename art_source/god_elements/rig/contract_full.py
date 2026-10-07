"""full/contract.json: what the coder builds against (data)."""
import json
from ge_common import *
import wheel2 as W2
import bixby_bite as BB

STAGE = os.path.join(GE, 'full')
num = json.load(open(os.path.join(STAGE, 'numbers.json')))
liam = {k.split('/')[-1]: v for k, v in num.items() if k.startswith('Puppets/liam/')}
bix = {k.split('/')[-1]: v for k, v in num.items() if k.startswith('Puppets/bixby/')}

c = {
    'pass': "Elemental Wheel FULL SET, 2026-10-06 (approved: 'approve all, ash fur, keep liam's size'). "
            "Staged in scratchpad/god_elements/full/; nothing shipped.",
    'scale': "3x world (2 screen px a texel under the god fight's 2/3 view). Texels from each frame's top-left; "
             "a 'corner' is a texel's top-left corner.",
    'staging': {
        'finding': "At the plan's WHEEL_HUB (960, 820) the 192x192 wheel (radius 90.5 texels + 4 of lit glow = 284 world "
                   "px) overlaps Jordan's lower body by ~30 screen px (stills/still_3_double_fire_air_plan.png); the plan "
                   "sized the hub for a 144 wheel.",
        'recommended': {
            'WHEEL_HUB': [960, 924], 'liam_anchor_world': [960, 1044], 'icon_point_world': [960, 780],
            'why': "clears his lowest texel by >= 12 screen px, and Liam's float pivot (body corner 48, 56) lands on the "
                   "hub: e.g. LIAM_FEET (960, 1194) with LIAM_LIFT 150, or keep LIAM_FEET and lift 28"},
        'stills': ['stills/still_1_cast_water_stop_fixed.png', 'stills/still_2_bite_snap_fixed.png',
                   'stills/still_3_double_fire_air_fixed.png', 'stills/still_3_double_fire_air_plan.png (the overlap)'],
    },
    'liam': {
        'dir': 'Assets/Characters/Jordan/Puppets/liam/', 'cell': [96, 96], 'anchor': [48, 96],
        'juggle': {'cell': [128, 96], 'feet': [64, 95]},
        'no_staff': "every sheet is staff-less (the approved Avatar look); his fists stay where they gripped it",
        'avatar_sheets': {n: {'frames': liam['liam_' + n]['frames'], 'times': liam['liam_' + n]['times'],
                              'back': liam['liam_' + n]['back'],
                              'wrists_recorded_no_ring': liam['liam_' + n]['wrists_recorded'],
                              'glow_strip': 'liam_%s_avatar.png' % n}
                          for n in ('channel', 'blow', 'ignite', 'cast_left', 'cast_right', 'slam_rise')},
        'avatar_body': "the float: his figure drawn 12 texels HIGHER in the cell than his standing rig (body (16, 20), not "
                       "(16, 32)), legs hanging, toes down to row ~93. Float pivot corner (48, 56); head ring (46, 24) "
                       "(+ the frame's bob); back (47, 56) (+ bob); drawn box at channel f0 Rect2(6, 21, 79, 73); his "
                       "body without the arms about Rect2(28, 21, 40, 73); top 21.",
        'pop_note': "switching from a standing sheet (wobble) to a float sheet (channel) moves his drawing up 36 world px: "
                    "it hides inside the AVATAR lift; if it shows, lift 36 px less on the float sheets.",
        'plain_sheets': {n: {'frames': liam['liam_' + n]['frames'], 'times': liam['liam_' + n]['times'],
                             'back': liam['liam_' + n]['back'], 'anchor': liam['liam_' + n]['anchor']}
                         for n in ('wobble', 'fall', 'downed', 'defeat', 'juggle')},
        'glow_strips': "liam_<sheet>_avatar.png: ADDITIVE (BLEND_MODE_ADD; transparent adds nothing), the same grid and "
                       "frame count, frame-synced: blazing lenses (white-hot core, rune-blue rim), the arrow down his crown "
                       "onto the plate and brow, a burning line down each forearm wrap to the hand, the open mouth glowing "
                       "(shout / big / blow frames), and a 2-texel rim of light outside his silhouette (G1 then G2). At "
                       "full strength body + strip = the approved Avatar look; fade the strip for the State's on/off.",
        'aura': {'files': ['liam_avatar_aura_back.png (behind him)', 'liam_avatar_aura_front.png (in front of him)'],
                 'cell': [128, 128], 'frames': 6, 'times': [0.12],
                 'place': "aura texel corner (64, 104) on his anchor (= aura (16, 8) on the body cell's top-left); the "
                          "orbit's centre (64, 64) is his float pivot",
                 'pose_free': "the orbit (the wind band and the 4 element motes) loops on its own over any Avatar sheet"},
        'extras': {'liam_avatar_on.png': {'frames': 5, 'times': [0.06, 0.06, 0.08, 0.08, 0.12], 'blend': 'add',
                                          'over': 'channel frame 0'},
                   'liam_avatar_off.png': {'frames': 4, 'times': [0.08, 0.1, 0.12, 0.14], 'blend': 'add',
                                           'over': 'channel frame 0'}},
    },
    'bixby': {
        'dir': 'Assets/Characters/Jordan/Puppets/bixby/', 'cell': [192, 160], 'anchor': [96, 151],
        'juggle': {'cell': [256, 256], 'feet': [128, 200], 'offset': [0, -72]},
        'fur': 'ash (approved)',
        'fire': "fire in or from his mouths keeps its own ember colours and no keyline; on the frames where he breathes or "
                "holds fire his eyes burn ember (#FFD55C / #FF7A2E, the roster's take-A glow); elsewhere rune blue",
        'sheets': {n: {'frames': v['frames'], 'back': v['back'], 'rings': v.get('rings'),
                       'ember_eye_frames': v.get('ember_eye_frames', [])} for n, v in bix.items()},
        'back_rule': "between the wing roots on his middle head's axis: 59 rows under his headband plate's top edge "
                     "(hover (95, 71)); the side-view flyby (82, 60) by hand; the juggle null",
        'bite': {'file': 'bixby_bite.png', 'frames': 5, 'times': BB.TIMES,
                 'order': ['rear', 'lunge start', 'lunge (jaws wide)', 'SNAP (contact)', 'recoil'],
                 'jaws': bix['bixby_bite']['jaws'], 'snap_frame': 3, 'back': bix['bixby_bite']['back'],
                 'note': "facing down the screen; his upper body moves as one ([-4, +3, +8, +10, -2] rows) over planted "
                         "legs; frame 3 clamps the middle head's jaws shut; JAWS = the middle head's jaw centre"},
        'swim': 'not drawn (optional): the fallback (hover clipped at row 100) stands',
    },
    'wheel': {
        'dir': 'Assets/Characters/Jordan/Wheel/',
        'layout_at_rest': {'TL': 'water', 'TR': 'earth', 'BR': 'fire', 'BL': 'air'},
        'element_wheel.png': {'frames': 8, 'cell': [192, 192], 'angles_cw_deg': W2.SUB, 'pivot_corner': [96, 96],
                              'use': "angle t (clockwise deg): quarters = floor(t / 90) mod 4 as a code rotation "
                                     "(pixel-exact), frame = round((t mod 90) / 11.25); a frame 8 carries into the next "
                                     "quarter"},
        'stop': {'pointer': "TOP-RIGHT; the element under it after k clockwise quarter turns from rest: k0 earth, k1 "
                            "water, k2 air, k3 fire",
                 'quarters_for': {'earth': 0, 'water': 1, 'air': 2, 'fire': 3},
                 'second_pointer': "BOTTOM-RIGHT = the first turned 90 deg clockwise about the hub; it then sits on the "
                                   "primary's clockwise neighbour (k3 fire+air, k2 air+water, k1 water+earth, k0 "
                                   "earth+fire)"},
        'element_wheel_lit.png': {'frames': 8, 'order': W2.LIT_NAMES,
                                  'single_frame': {'water': 0, 'earth': 1, 'fire': 2, 'air': 3},
                                  'double_frame_by_primary': {'fire': 4, 'air': 5, 'water': 6, 'earth': 7},
                                  'drawn': 'at REST orientation: turn it by the same quarters as the stop'},
        'element_wheel_pointer.png': {'frames': 3, 'order': ['rest', 'bump (a peg passing, 0.04 s)', 'lit'],
                                      'cell': [40, 40], 'frame_top_left_in_wheel_texels': list(W2.PTR_TL),
                                      'pivot': [-54, 94],
                                      'pivot_meaning': "the wheel's centre corner in pointer texels: turn the pointer "
                                                       "about it (90 deg clockwise) for the second pointer",
                                      'tip': num['Wheel/element_wheel_pointer']['tip']},
        'pegs': "the four bone studs where the spokes meet the rim (on the axes at rest): one passes a pointer every 90 deg",
        'element_icons.png': {'frames': 8, 'cell': [32, 32], 'pivot': [16, 16],
                              'order': ['fire_pop', 'fire', 'air_pop', 'air', 'water_pop', 'water', 'earth_pop', 'earth']},
        'soft': {'element_wheel_blur.png': "4 x 192, the disc at speed in 22.5-deg phases (with the quarter turns: 16 "
                                           "positions), drawn OVER the disc",
                 'element_wheel_form.png': "6 x 192, the wheel drawing itself in runes; backward = the dissolve",
                 'element_wheel_shatter.png': "6 x 208x208, pivot corner (104, 104)"},
        'light': "everything that turns with the disc and has volume (rim, studs, spokes, hub) is lit symmetrically, so "
                 "neither the 11.25-deg frames nor the code's quarter turns make the light jump; the icons are painted "
                 "RADIALLY (each one's top points out along its diagonal), so whichever element stops under the "
                 "top-right pointer reads the same, tilted 45 deg toward it; the pointer (which does not turn with the "
                 "disc) is lit from the upper left",
    },
    'hooks': "Scripts/JordanPuppetHooks.gd: an additive regeneration (liam and bixby BACK lines added inside const BACK; "
             "no live line changed) - see hooks.diff",
    'ship': "manifest.json (stage path -> exact project path, sha256); ship_check.py --check (read-only)",
}
with open(os.path.join(STAGE, 'contract.json'), 'w') as f:
    json.dump(c, f, indent=1)
print('ok')
