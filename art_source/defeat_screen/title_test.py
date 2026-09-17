import os
import subprocess
from lib import *

G = 'godot_mock'
GODOT = "C:/Users/theyi/Downloads/Godot_v4.6.3-stable_win64.exe/Godot.exe.exe"
bg = Img(640, 360, GREY_M)
for y in range(120, 240):
    for x in range(640):
        bg.set(x, y, BROWN)
for y in range(240, 360):
    for x in range(640):
        bg.set(x, y, K)
bg.save(G + '/art/bg.png')
variants = [
    # (y, color, outline_size, outline_col, shadow_off, shadow_col, shadow_outline)
    (0, 'd95763', 18, '000000', 0, None, 0),
    (130, 'd95763', 18, '000000', 9, 'ac3232', 18),
    (260, 'd95763', 18, '000000', 9, '45283c', 0),
    (380, 'ffffff', 18, '000000', 9, 'ac3232', 18),
    (500, 'd95763', 27, '000000', 0, None, 0),
    (630, 'ffffff', 18, 'ac3232', 0, None, 0),
    (760, 'd95763', 36, '000000', 12, '45283c', 36),
    (890, 'eec39a', 18, '000000', 9, 'ac3232', 18),
]


def col(h):
    return 'Color(%.3f, %.3f, %.3f, 1)' % (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255)


s = ['[gd_scene format=3]\n', '[ext_resource type="Script" path="res://capture.gd" id="1"]',
     '[ext_resource type="Theme" path="res://theme.tres" id="2"]',
     '[ext_resource type="Texture2D" path="res://art/bg.png" id="3"]', '',
     '[node name="Mock" type="Control"]\nlayout_mode = 3\nanchors_preset = 15\nanchor_right = 1.0\n'
     'anchor_bottom = 1.0\ntheme = ExtResource("2")\nscript = ExtResource("1")\n',
     '[node name="Background" type="TextureRect" parent="."]\nlayout_mode = 1\nanchors_preset = 15\n'
     'anchor_right = 1.0\nanchor_bottom = 1.0\ntexture = ExtResource("3")\nexpand_mode = 1\n']
for i, (y, c, os_, oc, so, sc, sos) in enumerate(variants):
    for j, xoff in enumerate([0, 960]):
        n = ('[node name="T%d_%d" type="Label" parent="."]\nlayout_mode = 0\noffset_left = %d.0\noffset_top = %d.0\n'
             'offset_right = %d.0\noffset_bottom = %d.0\n' % (i, j, xoff + 20, y, xoff + 940, y + 119))
        n += 'theme_type_variation = &"TitleLabel"\ntheme_override_colors/font_color = %s\n' % col(c)
        n += 'theme_override_colors/font_outline_color = %s\ntheme_override_constants/outline_size = %d\n' % (col(oc), os_)
        if sc:
            n += ('theme_override_colors/font_shadow_color = %s\ntheme_override_constants/shadow_offset_x = 0\n'
                  'theme_override_constants/shadow_offset_y = %d\ntheme_override_constants/shadow_outline_size = %d\n'
                  % (col(sc), so, sos))
        n += 'text = "Defeat! v%d"\n' % i
        s.append(n)
with open(G + '/mock.tscn', 'w', newline='\n') as f:
    f.write('\n'.join(s))
subprocess.run([GODOT, '--headless', '--path', G, '--import'], capture_output=True, timeout=300)
out = os.path.abspath('out/title_variants.png').replace(os.sep, '/')
env = dict(os.environ, MOCK_OUT=out)
subprocess.run([GODOT, '--path', G, '--resolution', '1920x1080'], capture_output=True, timeout=120, env=env)
print(os.path.exists(out))
