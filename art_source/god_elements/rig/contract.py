"""contract.json: the numbers the architect / coder need for the approval pass (sizes, anchors, layering, palette,
measured ratios, what was invented). Data, not a report."""
import json
from ge_common import *
import elements_pal as E
import wheel as WH


def hexs(c):
    return '#%02X%02X%02X' % tuple(c[:3])


def main():
    num = json.load(open(os.path.join(OUT, 'numbers.json')))
    c = {
        'pass': 'Elemental Wheel (Liam + Bixby puppets) - APPROVAL PASS, 2026-10-06. Scratch only; nothing shipped.',
        'scale': 'every sheet is drawn for the 3x world (JordanPuppetLayout.SCALE): 2 screen px a texel under the god '
                 "fight's 2/3 view. Points are TEXELS, origin the frame's top-left; a 'corner' is a texel's top-left corner.",
        'liam_puppet_avatar': {
            'file': 'liam_puppet_avatar.png', 'frame': [96, 96], 'frames': {'0': 'float (Avatar State hold)', '1': 'surge (arms up, shout glowing)'},
            'cell_matches': "Liam's own elements sheets (96x96, the approved 64x64 figure at 1:1), raised 12 rows to float",
            'float_pivot_corner': [48, 56],
            'hooks': {
                'back': [47, 56], 'head_ring': [46, 24],
                'wrist_l': {'f0': num['liam_puppet_avatar']['hooks'][0]['wrist_l'],
                            'f1': num['liam_puppet_avatar']['hooks'][1]['wrist_l'], 'ring': False},
                'wrist_r': {'f0': num['liam_puppet_avatar']['hooks'][0]['wrist_r'],
                            'f1': num['liam_puppet_avatar']['hooks'][1]['wrist_r'], 'ring': False},
                'knee_l': [37, 76], 'knee_r': [57, 77],
                'note': "back = between the shoulder blades, recorded not drawn (strings run in UNDER him, the user's "
                        "'strings on back only'); wrist rings left off so the Avatar arm arrows own the forearms",
            },
            'layers_bottom_to_top': ['liam_puppet_avatar_aura_back.png (128x128)', 'liam_puppet_avatar.png (96x96)',
                                     'liam_puppet_avatar_aura_front.png (128x128)'],
            'aura_cell': [128, 128], 'aura_centre_corner': [64, 64], 'body_frame_top_left_in_aura': [16, 8],
            'aura_blend': 'normal (opaque texels, no semi-alpha); ADD also reads if the coder prefers',
        },
        'bixby_puppet': {
            'file': 'bixby_puppet.png (ash fur, recommended); bixby_puppet_blood.png (alt take)',
            'frame': [192, 160], 'frames': {'0': 'bixby_beast_fly f0 twin (wings up)', '1': 'bixby_beast_fly f1 twin (wings down)'},
            'twin_rule': 'same size, grid, anchors and silhouette as Bixby/bixby_beast_fly.png frames 0-1',
            'anchor': [96, 151], 'anchor_note': 'his live sheet\'s own (BixbyBeastArtLayout.ANCHOR, x=96 axis, HOVER_HEIGHT 40)',
            'hooks': num['bixby_puppet']['hooks'],
            'rings_drawn': num['bixby_puppet']['rings drawn'][0],
            'rings_left_off': ['wing_l', 'wing_r (the down-stroke frame cannot place them: the roster\'s all-or-nothing rule)'],
            'carry_check_other_beast_sheets': {
                'clean (every colour mapped)': ['bixby_beast.png', 'bixby_beast_land.png', 'bixby_beast_takeoff.png',
                                                'bixby_beast_recover.png'],
                'only fire-FX colours unmapped (FFF2B0 / FFFFFF: keep their own or decide per attack)':
                    ['bixby_beast_flyby.png', 'bixby_beast_hit.png', 'bixby_beast_roar.png', 'bixby_beast_firebreath.png'],
                'needs its own table (smoke + small Bixby + Liam, 63 colours)': ['bixby_beast_defeat.png'],
                'note': 'the side-view flyby recolours cleanly but its rings need hand-set points (the tracker is keyed to the front view)',
            },
        },
        'element_wheel': {
            'file': 'element_wheel.png', 'frame': [192, 192],
            'frames': {str(i): n for i, (n, _kw) in enumerate(WH.STATES)},
            'centre_corner': [96, 96], 'centre_on': "Liam's float pivot (body corner 48,56): body top-left = wheel (48, 40); aura top-left = wheel (32, 32)",
            'radii_texels': {'outer': WH.R_OUT, 'rim_inner': WH.R_RIM, 'hub': WH.R_HUB, 'lit_glow_reaches': WH.R_OUT + 4.2,
                             'icon_centres_at': WH.ICON_R},
            'segments_clockwise_from_top_left': WH.SEG,
            'icon_centres': {k: [round(v[0], 1), round(v[1], 1)] for k, v in WH.ICON_AT.items()},
            'spokes': 'along the axes, hidden behind his cross-shaped body; the icons sit in the clear corners',
            'rotation': 'square, even size, centre on a corner: a 90-degree code rotation is pixel-exact. Spin options: '
                        '(a) show frame 5 (spin) rotating in code while fast - the blur hides rotation jaggies - then snap '
                        'to rest at a 90-degree step and swap to the lit frame; (b) full set: 8 pre-drawn sub-angles of the '
                        'disc (11.25 deg) x 4 code quarter-turns = 32 clean positions. Icons rotate with the disc in (a)/(b) '
                        'unless the full set splits them out to stay upright.',
            'layering': "UNDER the strings (z below JordanStrings' -2, e.g. the floor layer) so his strings visibly run over it to his back",
        },
        'placement_used_in_the_mockup_world_px': {
            'liam_float_pivot': [960, 924], 'wheel_top_left': [672, 636], 'liam_body_top_left': [816, 756],
            'aura_top_left': [768, 732], 'bixby_frame_top_left': [1437, 654], 'player': [960, 1330],
            'screen_from_world': 'screen = (world + (480, 6)) / 1.5',
            'strings': 'Liam: left hand, inner pair (index, middle). Bixby: right hand, outer pair (ring, little). Both to the back hook.',
        },
        'measured': num,
        'palette': {
            'puppets': 'the roster take B, 16 colours (art_source/jordan_puppets/jp_palette.py), unchanged',
            'added_for_the_avatar_state': {'HOT': hexs(HOT) + " (JordanGodLayout.STRING_COLORS.hot: the strings' hot texel)"},
            'avatar_glow': {'G1': hexs(PUP['G1']), 'G2': hexs(PUP['G2']), 'HOT': hexs(HOT)},
            'elements (Liam\'s own ramps: le_rig.ADD + his shipped wave / fire-tornado / gust sheets)': {
                'fire': {k: hexs(v) for k, v in E.FIRE.items()}, 'water': {k: hexs(v) for k, v in E.WATER.items()},
                'earth': {k: hexs(v) for k, v in E.EARTH.items()}, 'air': {k: hexs(v) for k, v in E.AIR.items()}},
            'invented colours': {'earth D (dark moss) ': '#1E5A2A', 'air d (deep teal)': '#2E7A80', 'air t (teal)': '#5FC8C0',
                                 'note': "earth browns are Liam's own vest ramp (his pillar is grey stone; the brief asked brown/green)"},
            'wheel_rim_spokes_hub': 'the puppets\' iron (P1 I2 I3), bone (B1 A5) and rune blues (G1 G2, HOT when lit)',
        },
        'keyline': 'pure black #000000 everywhere (the puppets\' and Liam\'s and Bixby\'s own); the aura glow and wind carry none '
                   '(house FX rule), the four aura motes do (they are objects that must read against the wheel)',
        'invented_or_guessed': [
            "Liam has NO tattoos in his design: the Avatar-State markings are invented - Aang's arrow down his crown onto the "
            "band's plate, and a burning line down each forearm wrap",
            'the Avatar float pose itself (arms spread / arms up, legs hanging, toe-down shoes) is new; built from his approved rig parts',
            "the set (closed) mouth on the float frame is a new mouth; the surge uses his rig's existing 'shout'",
            'no staff: the Avatar float is staff-less (his elements-phase staff is a rig part and can be added)',
            'Bixby fur: two takes (ash = recommended, blood = alt); his gold collar spikes go bone, the headband plate iron, '
            'the band and tails bone - as Liam\'s puppet\'s',
            'wheel layout: water TL, earth TR, fire BR, air BL (opposites across the hub); every icon and the rim design',
        ],
    }
    with open(os.path.join(OUT, 'contract.json'), 'w') as f:
        json.dump(c, f, indent=1)
    print('ok')


if __name__ == '__main__':
    main()
