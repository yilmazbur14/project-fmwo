"""Writes the whole Assets/UI/Pad set. Run from anywhere.

PAD_DEST overrides the output folder (used to stage a build for review).
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from glyphs import *
from PIL import Image

PROJ = 'C:/Users/theyi/OneDrive/Documents/new-game-project'
DEST = os.environ.get('PAD_DEST', PROJ + '/Assets/UI/Pad')
os.makedirs(DEST, exist_ok=True)

FILES = [
    # --- face buttons: Xbox letters, colour per position --------------------
    ('pad_face_down',      lambda: face_button('A', RAMP_GREEN)),
    ('pad_face_right',     lambda: face_button('B', RAMP_RED)),
    ('pad_face_left',      lambda: face_button('X', RAMP_BLUE)),
    ('pad_face_up',        lambda: face_button('Y', RAMP_YELLOW)),
    ('pad_face_all',       face_diamond),
    # --- d-pad ---------------------------------------------------------------
    ('pad_dpad',           lambda: dpad(None)),
    ('pad_dpad_up',        lambda: dpad('U')),
    ('pad_dpad_down',      lambda: dpad('D')),
    ('pad_dpad_left',      lambda: dpad('L')),
    ('pad_dpad_right',     lambda: dpad('R')),
    # --- left stick ----------------------------------------------------------
    ('pad_stick_left',         lambda: stick(32, False)),
    ('pad_stick_left_push',    lambda: stick(32, True)),
    ('pad_stick_left_64',      lambda: stick(64, False)),
    ('pad_stick_left_push_64', lambda: stick(64, True)),
    # --- shoulders and triggers ----------------------------------------------
    ('pad_bumper_l',       lambda: bumper('L')),
    ('pad_bumper_r',       lambda: bumper('R')),
    ('pad_trigger_l',      lambda: trigger('L')),
    ('pad_trigger_r',      lambda: trigger('R')),
    # --- start / menu --------------------------------------------------------
    ('pad_start',          start_button),
    # --- movement card composite ---------------------------------------------
    ('pad_move',           move_card),
]

# The controller agent's atlas contract (Scripts/ControlsArtLayout.gd,
# FINAL_PAD_GLYPHS): 14 columns x 2 rows, row 0 at rest, row 1 lit, column
# order = InputSettings.PAD_BUTTON_FRAMES / PAD_AXIS_FRAMES, with Start
# appended as column 13 so no earlier column moves.
ATLAS_COLUMNS = [
    ('A  bottom face',  lambda lit: face_button('A', RAMP_GREEN, lit)),
    ('B  right face',   lambda lit: face_button('B', RAMP_RED, lit)),
    ('X  left face',    lambda lit: face_button('X', RAMP_BLUE, lit)),
    ('Y  top face',     lambda lit: face_button('Y', RAMP_YELLOW, lit)),
    ('LB',              lambda lit: bumper('L', lit)),
    ('RB',              lambda lit: bumper('R', lit)),
    ('LT (axis)',       lambda lit: trigger('L', lit)),
    ('RT (axis)',       lambda lit: trigger('R', lit)),
    ('D-pad up',        lambda lit: dpad('U', lit=True) if lit else dpad('U', mark_only=True)),
    ('D-pad down',      lambda lit: dpad('D', lit=True) if lit else dpad('D', mark_only=True)),
    ('D-pad left',      lambda lit: dpad('L', lit=True) if lit else dpad('L', mark_only=True)),
    ('D-pad right',     lambda lit: dpad('R', lit=True) if lit else dpad('R', mark_only=True)),
    ('fallback ?',      lambda lit: fallback_button(lit)),
    ('Start',           lambda lit: start_button(lit)),
]

# DB32 is the project's palette; anything outside it is a bug.
DB32 = {
    (0,0,0),(34,32,52),(69,40,60),(102,57,49),(143,86,59),(223,113,38),
    (217,160,102),(238,195,154),(251,242,54),(153,229,80),(106,190,48),
    (55,148,110),(75,105,47),(82,75,36),(50,60,57),(63,63,116),(48,96,130),
    (91,110,225),(99,155,255),(95,205,228),(203,219,252),(155,173,183),
    (132,126,135),(105,106,106),(89,86,82),(118,66,138),(172,50,50),
    (217,87,99),(215,123,186),(143,151,74),(138,111,48),(255,255,255),
}
SPARKLE = (251, 242, 54)


def check(name, c):
    """Palette + 'outline is the outermost ring' checks."""
    ok = True
    bad = {col for col in c.px.values() if col not in DB32}
    if bad:
        print('  ! %s: off-palette %s' % (name, bad)); ok = False
    for (x, y), col in c.px.items():
        on_edge = x in (0, c.w - 1) or y in (0, c.h - 1)
        if on_edge and col not in (BLACK, SPARKLE):
            print('  ! %s: %s at edge pixel %s' % (name, col, (x, y))); ok = False
            break
    return ok


def build_atlas():
    n = len(ATLAS_COLUMNS)
    sheet = C(32 * n, 64)
    for i, (label, fn) in enumerate(ATLAS_COLUMNS):
        for row, lit in enumerate((False, True)):
            g = fn(lit)
            check('atlas col %d %s %s' % (i, label, 'lit' if lit else 'rest'), g)
            sheet.blit(g, 32 * i, 32 * row)
    return sheet


def build_inline():
    """One resting row of 11x11 cells, same column order as the atlas."""
    sheet = C(11 * len(INLINE_COLUMNS), 11)
    for i, (label, fn) in enumerate(INLINE_COLUMNS):
        g = fn()
        check('inline col %d %s' % (i, label), g)
        sheet.blit(g, 11 * i, 0)
    return sheet


def key_blank():
    """key_q.png's body with the Q wiped, for ControlsArtLayout's 9-slice
    (texture_margin 24 at 3x = 8px here; every stretched row/column of the
    keycap is uniform once the letter is gone)."""
    src = Image.open(PROJ + '/Assets/UI/key_q.png').convert('RGBA')
    c = C(src.width, src.height)
    for y in range(src.height):
        for x in range(src.width):
            p = src.getpixel((x, y))
            if p[3]:
                c.px[(x, y)] = PL_FACE if p[:3] == NAVY else p[:3]
    return c


def save_3x(c, path):
    c.image().resize((c.w * 3, c.h * 3), Image.NEAREST).save(path)


# --- .aseprite step ----------------------------------------------------------
# Opens each PNG in Aseprite (batch mode) and saves the editable .aseprite
# beside it, layer named "art"; the atlas gets a 32px grid so its cells show.
ASEPRITE_LUA = r'''
local dir = app.params["dir"]
for n in string.gmatch(app.params["names"], "[^,]+") do
  local spr = app.open(dir .. "/" .. n .. ".png")
  if spr == nil then
    print("FAILED to open " .. n)
  else
    spr.layers[1].name = "art"
    if n == "pad_buttons" then spr.gridBounds = Rectangle(0, 0, 32, 32) end
    if n == "pad_buttons_inline" then spr.gridBounds = Rectangle(0, 0, 11, 11) end
    spr:saveAs(dir .. "/" .. n .. ".aseprite")
    print(string.format("saved %s.aseprite %dx%d", n, spr.width, spr.height))
    spr:close()
  end
end
'''


def aseprite_exe():
    """The same binary the pixel-mcp plugin is configured with."""
    import json
    cfg = os.path.expanduser('~/.config/pixel-mcp/config.json')
    if os.path.exists(cfg):
        with open(cfg, encoding='utf-8') as f:
            p = json.load(f).get('aseprite_path')
        if p and os.path.exists(p):
            return p
    p = 'C:/Program Files (x86)/Steam/steamapps/common/Aseprite/Aseprite.exe'
    return p if os.path.exists(p) else None


def write_aseprite(names):
    import subprocess, tempfile
    exe = aseprite_exe()
    if not exe:
        print('  ! Aseprite not found: .aseprite files NOT updated')
        return
    lua = os.path.join(tempfile.gettempdir(), 'pad_glyphs_to_aseprite.lua')
    with open(lua, 'w', encoding='utf-8') as f:
        f.write(ASEPRITE_LUA)
    out = subprocess.run([exe, '-b', '--script-param', 'dir=' + DEST,
                          '--script-param', 'names=' + ','.join(names),
                          '--script', lua], capture_output=True, text=True)
    print(out.stdout.strip() or out.stderr.strip())


if __name__ == '__main__':
    for name, fn in FILES:
        c = fn()
        check(name, c)
        c.save(os.path.join(DEST, name + '.png'))
        print('%-24s %dx%d' % (name, c.w, c.h))
    atlas = build_atlas()
    atlas.save(os.path.join(DEST, 'pad_buttons.png'))
    save_3x(atlas, os.path.join(DEST, 'pad_buttons_3x.png'))
    print('%-24s %dx%d  (+ _3x %dx%d)' % ('pad_buttons', atlas.w, atlas.h, atlas.w * 3, atlas.h * 3))
    inl = build_inline()
    inl.save(os.path.join(DEST, 'pad_buttons_inline.png'))
    save_3x(inl, os.path.join(DEST, 'pad_buttons_inline_3x.png'))
    print('%-24s %dx%d  (+ _3x %dx%d)' % ('pad_buttons_inline', inl.w, inl.h, inl.w * 3, inl.h * 3))
    kb = key_blank()
    check('key_blank', kb)
    kb.save(os.path.join(DEST, 'key_blank.png'))
    save_3x(kb, os.path.join(DEST, 'key_blank_3x.png'))
    print('%-24s %dx%d  (+ _3x %dx%d)' % ('key_blank', kb.w, kb.h, kb.w * 3, kb.h * 3))
    print('-> ' + DEST)
    if '--no-aseprite' not in sys.argv:
        write_aseprite([n for n, _ in FILES] + ['pad_buttons', 'pad_buttons_inline', 'key_blank'])
