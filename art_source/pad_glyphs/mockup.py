"""Previews for the pad glyph set - nothing here writes into the project.

  python mockup.py        # renders + composes everything into PAD_PREVIEW_OUT

Outputs (PAD_PREVIEW_OUT, default <temp>/pad_glyphs_preview):
  controls_keyboard_1920.png  the real ControlsScene as shipped (keyboard)
  controls_pad_1920.png       the same scene with the final pad art swapped in
                              memory, mirroring ControlsSceneScript._art() with
                              ControlsArtLayout's USE_FINAL_* flags on
  controls_compare.png        the two side by side
  inline_strip.png            the 11px inline set in dialogue text at 3x, with the
                              32px glyphs at 1x and 2x underneath for comparison

Both renders use Godot's movie writer with a SceneTree script that lives in
the preview folder, so run/main_scene and every project file stay untouched.
"""
import os, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFont

PROJ = 'C:/Users/theyi/OneDrive/Documents/new-game-project'
GODOT = 'C:/Users/theyi/Downloads/Godot_v4.6.3-stable_win64.exe/Godot.exe.exe'
FONT = PROJ + '/fonts/PixelifySans.ttf'
OUT = os.environ.get('PAD_PREVIEW_OUT', os.path.join(tempfile.gettempdir(), 'pad_glyphs_preview'))

MOCK_CONTROLS_GD = 'extends SceneTree\n## Renders the real ControlsScene as the game will show it on a gamepad once\n## ControlsArtLayout\'s USE_FINAL_PAD_MOVE / USE_FINAL_PAD_GLYPHS flags are on.\n## Everything is swapped IN MEMORY: this file lives outside the project and\n## writes nothing to it. PAD_MOCK=kbd -> untouched scene, PAD_MOCK=pad -> pad.\n##\n## It mirrors ControlsSceneScript._show_controls() + _art() with the flags on:\n## the Move card gets pad_move.png, every other card gets its atlas cell from\n## pad_buttons_3x.png at column InputSettings.pad_frame_for(action), row 0.\n\nconst PAD_DIR := "C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/UI/Pad/"\nconst HFRAMES := 14\nconst VFRAMES := 2\n\nfunc _file_tex(file_name: String) -> Texture2D:\n\t# read the PNG straight off disk so the render always shows the current art\n\treturn ImageTexture.create_from_image(Image.load_from_file(PAD_DIR + file_name))\n\nfunc _initialize() -> void:\n\tvar inst: Node = (load("res://Scenes/Core/ControlsScene.tscn") as PackedScene).instantiate()\n\t# `ready` is emitted after the scene\'s own _ready()/_show_controls(), so\n\t# whatever is done below lands on top of the scene\'s first paint\n\tinst.ready.connect(_apply_mode.bind(inst, OS.get_environment("PAD_MOCK")), CONNECT_ONE_SHOT)\n\troot.add_child(inst)\n\n\n# InputSettings picks the device from whether a pad is plugged in, so force it\n# either way; _set_device() only sets the var and emits device_changed (which\n# the scene repaints from) - it saves nothing.\nvar _kbd_scene: Node = null\n\n\nfunc _apply_mode(inst: Node, mode: String) -> void:\n\tvar input_settings: Node = root.get_node("InputSettings")\n\tif mode != "pad":\n\t\t_kbd_scene = inst\n\t\t_force_keyboard()\n\t\treturn\n\tinput_settings._set_device(input_settings.Device.GAMEPAD)\n\t_swap_to_pad(inst)\n\n\n# A plugged-in pad is reported through joy_connection_changed a frame or two\n# after boot, which flips InputSettings back to GAMEPAD and repaints the\n# cards; re-assert the keyboard every frame so the keyboard render stays one.\nfunc _force_keyboard() -> void:\n\tvar input_settings: Node = root.get_node("InputSettings")\n\tif input_settings.device != input_settings.Device.KEYBOARD:\n\t\tinput_settings._set_device(input_settings.Device.KEYBOARD)\n\t\tprint("MOCK forced keyboard at frame %d" % Engine.get_process_frames())\n\n\nfunc _process(_delta: float) -> bool:\n\tif _kbd_scene != null:\n\t\t_force_keyboard()\n\treturn false\n\n\nfunc _swap_to_pad(inst: Node) -> void:\n\tvar sheet := _file_tex("pad_buttons_3x.png")\n\tvar cell := Vector2(sheet.get_width() / float(HFRAMES), sheet.get_height() / float(VFRAMES))\n\tvar input_settings: Node = root.get_node("InputSettings")\n\tvar row := int(OS.get_environment("PAD_ROW")) if OS.get_environment("PAD_ROW") != "" else 0\n\tfor action in inst.glyphs:\n\t\tvar glyph: TextureRect = inst.glyphs[action]\n\t\tvar keycap: Control = inst.keycaps[action]\n\t\tif action == input_settings.MOVE:\n\t\t\tglyph.texture = _file_tex("pad_move.png")\n\t\telse:\n\t\t\tvar frame: int = input_settings.pad_frame_for(action)\n\t\t\tvar atlas := AtlasTexture.new()\n\t\t\tatlas.atlas = sheet\n\t\t\tatlas.region = Rect2(Vector2(frame, row) * cell, cell)\n\t\t\tglyph.texture = atlas\n\t\t\tprint("MOCK %s -> atlas column %d" % [action, frame])\n\t\tglyph.visible = true\n\t\tkeycap.visible = false\n\tinst.move_title.text = inst.MOVE_TITLE_PAD\n'

MOCK_INLINE_GD = 'extends SceneTree\n## Dialogue-style lines with pad glyphs inline, in the game\'s own theme\n## (Pixelify Sans 33, the dialogue size). The inline set is drawn from\n## pad_buttons_inline_3x.png at 1:1 (33px cells = the text\'s 3px grain); the\n## 32px set is shown underneath at 1x and 2x for comparison. Lives outside the\n## project and writes nothing to it; textures are read from the PNGs on disk.\n\nconst PAD_DIR := "C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/UI/Pad/"\n# pad_buttons_inline column order (= the atlas order, plus Start)\nconst A := 0\nconst B := 1\nconst X := 2\nconst Y := 3\nconst LB := 4\nconst RB := 5\nconst LT := 6\nconst RT := 7\nconst UP := 8\nconst DOWN := 9\nconst LEFT := 10\nconst RIGHT := 11\nconst UNKNOWN := 12\nconst START := 13\nvar _cache := {}\n\nfunc _tex(file_name: String) -> Texture2D:\n\tif not _cache.has(file_name):\n\t\t_cache[file_name] = ImageTexture.create_from_image(Image.load_from_file(PAD_DIR + file_name + ".png"))\n\treturn _cache[file_name]\n\nfunc _inline(col: int) -> Texture2D:\n\tvar a := AtlasTexture.new()\n\ta.atlas = _tex("pad_buttons_inline_3x")\n\ta.region = Rect2(col * 33, 0, 33, 33)\n\treturn a\n\n# A line is an Array of Strings (text) and Textures (glyphs); `scale` is\n# applied to each texture\'s own size (1 for the 3x inline sheet).\nfunc _line(parent: Control, parts: Array, scale := 1.0) -> void:\n\tvar rtl := RichTextLabel.new()\n\trtl.theme = load("res://Assets/UI/ui_theme.tres")\n\trtl.fit_content = true\n\trtl.autowrap_mode = TextServer.AUTOWRAP_OFF\n\trtl.scroll_active = false\n\trtl.custom_minimum_size = Vector2(1840, 0)\n\trtl.add_theme_font_size_override("normal_font_size", 33)\n\trtl.add_theme_color_override("default_color", Color(1, 1, 1))\n\tfor p in parts:\n\t\tif p is Texture2D:\n\t\t\trtl.add_image(p, int(p.get_width() * scale), int(p.get_height() * scale))\n\t\telse:\n\t\t\trtl.add_text(p)\n\tparent.add_child(rtl)\n\nfunc _heading(parent: Control, text: String) -> void:\n\tvar l := Label.new()\n\tl.theme = load("res://Assets/UI/ui_theme.tres")\n\tl.text = text\n\tl.add_theme_font_size_override("font_size", 22)\n\tl.add_theme_color_override("font_color", Color(0.984, 0.949, 0.212))\n\tparent.add_child(l)\n\nfunc _initialize() -> void:\n\tvar bg := ColorRect.new()\n\tbg.color = Color(0.1333, 0.1255, 0.2039)          # #222034, the dialogue box interior\n\tbg.size = Vector2(1920, 1080)\n\troot.add_child(bg)\n\tvar box := VBoxContainer.new()\n\tbox.position = Vector2(40, 24)\n\tbox.add_theme_constant_override("separation", 10)\n\troot.add_child(box)\n\n\t_heading(box, "INLINE SET  pad_buttons_inline_3x.png  (11px cells at 3x = 33px, the dialogue font\'s own pixel size)")\n\t_line(box, ["Punch with ", _inline(X), ", dash with ", _inline(RB), " and block with ", _inline(LB), "."])\n\t_line(box, ["Move with ", _inline(UP), _inline(DOWN), _inline(LEFT), _inline(RIGHT), ". Press ", _inline(START), " to keep going."])\n\t_line(box, ["When he\'s dazed, MASH ", _inline(X), " and ", _inline(RB), "!"])\n\t_line(box, ["All 14:  ", _inline(A), _inline(B), _inline(X), _inline(Y), "  ", _inline(LB), _inline(RB), "  ", _inline(LT), _inline(RT), "  ", _inline(UP), _inline(DOWN), _inline(LEFT), _inline(RIGHT), "  ", _inline(UNKNOWN), "  ", _inline(START)])\n\n\t_heading(box, "FOR COMPARISON  the 32px glyphs at 1x (pixels a third of the text\'s) and 2x (taller than the line)")\n\t_line(box, ["Punch with ", _tex("pad_face_left"), ", dash with ", _tex("pad_bumper_r"), " and block with ", _tex("pad_bumper_l"), "."], 1.0)\n\t_line(box, ["Punch with ", _tex("pad_face_left"), ", dash with ", _tex("pad_bumper_r"), " and block with ", _tex("pad_bumper_l"), "."], 2.0)\n'


def _godot(script_name, source, frames_dir, env_extra=None):
    os.makedirs(frames_dir, exist_ok=True)
    for f in os.listdir(frames_dir):
        os.remove(os.path.join(frames_dir, f))
    script = os.path.join(OUT, script_name)
    with open(script, 'w', encoding='utf-8', newline='\n') as f:
        f.write(source)
    env = dict(os.environ, **(env_extra or {}))
    run = subprocess.run([GODOT, '--path', PROJ, '--script', script,
                          '--write-movie', os.path.join(frames_dir, 'frame.png'),
                          '--fixed-fps', '30', '--quit-after', '3'],
                         capture_output=True, text=True, env=env)
    for line in (run.stdout + run.stderr).splitlines():
        if 'MOCK' in line or 'SCRIPT ERROR' in line or 'Parse Error' in line:
            print('  ' + line.strip())
    return Image.open(os.path.join(frames_dir, 'frame00000002.png')).convert('RGB')


def _labelled(im, text, h=64):
    out = Image.new('RGB', (im.width, im.height + h), (16, 14, 26))
    out.paste(im, (0, h))
    ImageDraw.Draw(out).text((24, 10), text, font=ImageFont.truetype(FONT, 42),
                             fill=(251, 242, 54))
    return out


def controls():
    kbd = _godot('mock_controls.gd', MOCK_CONTROLS_GD, os.path.join(OUT, 'render_kbd'), {'PAD_MOCK': 'kbd'})
    pad = _godot('mock_controls.gd', MOCK_CONTROLS_GD, os.path.join(OUT, 'render_pad'), {'PAD_MOCK': 'pad'})
    kbd.save(os.path.join(OUT, 'controls_keyboard_1920.png'))
    pad.save(os.path.join(OUT, 'controls_pad_1920.png'))
    a = _labelled(kbd, 'CURRENT  -  keyboard keycaps')
    b = _labelled(pad, 'NEW  -  gamepad glyphs (same scene, textures swapped in memory)')
    cmp_ = Image.new('RGB', (a.width * 2 + 24, a.height), (16, 14, 26))
    cmp_.paste(a, (0, 0))
    cmp_.paste(b, (a.width + 24, 0))
    cmp_.save(os.path.join(OUT, 'controls_compare.png'))


def inline():
    im = _godot('mock_inline.gd', MOCK_INLINE_GD, os.path.join(OUT, 'render_inline'))
    px, (W, H), bg = im.load(), im.size, (34, 32, 52)
    ys = [y for y in range(H) if any(px[x, y] != bg for x in range(0, W, 2))]
    xs = [x for x in range(W) if any(px[x, y] != bg for y in range(0, H, 2))]
    box = (max(0, min(xs) - 24), max(0, min(ys) - 24), min(W, max(xs) + 24), min(H, max(ys) + 24))
    im.crop(box).save(os.path.join(OUT, 'inline_strip.png'))


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    controls()
    inline()
    print('previews -> ' + OUT)
