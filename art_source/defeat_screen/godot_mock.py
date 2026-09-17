"""Render the 1920x1080 mockup with real Godot text/9-slice in a SCRATCH project
(never the game project).  python godot_mock.py bg.png banner_3x.png out.png [stars.png]"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
G = os.path.join(HERE, 'godot_mock')
GODOT = "C:/Users/theyi/Downloads/Godot_v4.6.3-stable_win64.exe/Godot.exe.exe"

# ---- layout (1920x1080 screen px) -- keep in sync with the report
TITLE = (0, 27, 1920, 119)
BANNER = (360, 741, 1200, 138)
BANNER_MARGINS = (102, 96, 12, 12)          # left, top, right, bottom (3x texture)
NAME_POS = (477, 757)
MSG_POS = (477, 808)
BUTTON = (636, 915, 648, 126)
STARS_POS = (0, 0)                           # set from args

TEXT = {
    'title': 'Defeat!',
    'name': 'SYSTEM',
    'time': 'Today at 11:59 PM',
    'msg': '@newcomer was knocked out and kicked from #arena-1.',
    'button': 'RETURN TO MAIN MENU',
}


def rect(x, y, w, h):
    return 'offset_left = %d.0\noffset_top = %d.0\noffset_right = %d.0\noffset_bottom = %d.0\n' % (x, y, x + w, y + h)


def write_scene(stars):
    ml, mt, mr, mb = BANNER_MARGINS
    s = []
    s.append('[gd_scene format=3]\n')
    s.append('[ext_resource type="Script" path="res://capture.gd" id="1"]')
    s.append('[ext_resource type="Theme" path="res://theme.tres" id="2"]')
    s.append('[ext_resource type="Texture2D" path="res://art/bg.png" id="3"]')
    s.append('[ext_resource type="Texture2D" path="res://art/banner_3x.png" id="4"]')
    s.append('[ext_resource type="Texture2D" path="res://art/ui_button_3x.png" id="5"]')
    if stars:
        s.append('[ext_resource type="Texture2D" path="res://art/stars.png" id="6"]')
    s.append('')
    s.append('[sub_resource type="StyleBoxTexture" id="btn"]\ncontent_margin_left = 24.0\ncontent_margin_top = 30.0\n'
             'content_margin_right = 24.0\ncontent_margin_bottom = 29.0\ntexture = ExtResource("5")\n'
             'texture_margin_left = 24.0\ntexture_margin_top = 24.0\ntexture_margin_right = 24.0\ntexture_margin_bottom = 24.0\n')
    s.append('[node name="Mock" type="Control"]\nlayout_mode = 3\nanchors_preset = 15\nanchor_right = 1.0\n'
             'anchor_bottom = 1.0\ntheme = ExtResource("2")\nscript = ExtResource("1")\n')
    s.append('[node name="Background" type="TextureRect" parent="."]\nlayout_mode = 1\nanchors_preset = 15\n'
             'anchor_right = 1.0\nanchor_bottom = 1.0\ntexture = ExtResource("3")\nexpand_mode = 1\n')
    if stars:
        sx, sy, frames = stars
        s.append('[node name="Stars" type="Sprite2D" parent="."]\nposition = Vector2(%d, %d)\nscale = Vector2(3, 3)\n'
                 'texture = ExtResource("6")\ncentered = false\nhframes = %d\n' % (sx, sy, frames))
    s.append('[node name="DefeatText" type="Label" parent="."]\nlayout_mode = 0\n' + rect(*TITLE) +
             'theme_type_variation = &"TitleLabel"\n'
             'theme_override_colors/font_color = Color(0.851, 0.341, 0.388, 1)\n'
             'theme_override_colors/font_outline_color = Color(0, 0, 0, 1)\n'
             'theme_override_constants/outline_size = 27\n'
             'text = "%s"\nhorizontal_alignment = 1\nvertical_alignment = 1\n' % TEXT['title'])
    s.append('[node name="SystemMessage" type="NinePatchRect" parent="."]\nlayout_mode = 0\n' + rect(*BANNER) +
             'texture = ExtResource("4")\npatch_margin_left = %d\npatch_margin_top = %d\npatch_margin_right = %d\n'
             'patch_margin_bottom = %d\n' % (ml, mt, mr, mb))
    s.append('[node name="Name" type="Label" parent="."]\nlayout_mode = 0\n' + rect(NAME_POS[0], NAME_POS[1], 200, 40) +
             'theme_override_colors/font_color = Color(0.851, 0.341, 0.388, 1)\ntext = "%s"\n' % TEXT['name'])
    s.append('[node name="Time" type="Label" parent="."]\nlayout_mode = 0\n' + rect(NAME_POS[0] + 141, NAME_POS[1], 400, 40) +
             'theme_override_colors/font_color = Color(0.518, 0.494, 0.529, 1)\ntext = "%s"\n' % TEXT['time'])
    s.append('[node name="Message" type="Label" parent="."]\nlayout_mode = 0\n' + rect(MSG_POS[0], MSG_POS[1], 1060, 40) +
             'theme_override_colors/font_color = Color(0.796, 0.859, 0.988, 1)\ntext = "%s"\n' % TEXT['msg'])
    s.append('[node name="ReturnToMenuButton" type="Button" parent="."]\nlayout_mode = 0\n' + rect(*BUTTON) +
             'theme_type_variation = &"LargeButton"\n'
             'theme_override_colors/font_color = Color(1, 1, 1, 1)\n'
             'theme_override_styles/normal = SubResource("btn")\n'
             'text = "%s"\n' % TEXT['button'])
    with open(os.path.join(G, 'mock.tscn'), 'w', newline='\n') as f:
        f.write('\n'.join(s))


def main():
    bg, banner3, out = sys.argv[1:4]
    stars = None
    shutil.copy(bg, os.path.join(G, 'art', 'bg.png'))
    shutil.copy(banner3, os.path.join(G, 'art', 'banner_3x.png'))
    if len(sys.argv) > 4:
        shutil.copy(sys.argv[4], os.path.join(G, 'art', 'stars.png'))
        stars = (int(sys.argv[5]), int(sys.argv[6]), int(sys.argv[7]))
    write_scene(stars)
    r = subprocess.run([GODOT, '--headless', '--path', G, '--import'], capture_output=True, text=True, timeout=300)
    env = dict(os.environ, MOCK_OUT=os.path.abspath(out).replace('\\', '/'))
    r = subprocess.run([GODOT, '--path', G, '--resolution', '1920x1080', '--position', '0,0'],
                       capture_output=True, text=True, timeout=120, env=env)
    tail = (r.stdout + r.stderr).strip().splitlines()[-8:]
    print('\n'.join(tail))
    print('exists:', os.path.exists(out))


if __name__ == '__main__':
    main()
