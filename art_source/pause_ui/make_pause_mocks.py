"""Mock-ups of the in-fight pause screen, composed over real frames of Eric's and Carter's fights.

Nothing here ships. The point is to show the screen in the project's own kit before any final art
exists: every frame, button, slider and glyph below is an existing Assets/UI PNG nine-patched or
blitted the way Godot would, and every word is Pixelify Sans rendered at a multiple of its 11 px
design size and thresholded, which is exactly how Godot draws it (checked against a capture of the
main menu, whose button label came out two colours -- #AC3232 and pure white -- with no antialiasing
anywhere).

Every size and colour in the LAYOUT block is mirrored from Scripts/PauseArtLayout.gd, and the panel
is measured from its contents the way the real PanelContainer/VBoxContainer will be, so what is
approved here is what that scene already builds. When a number here disagrees with PauseArtLayout,
PauseArtLayout wins and this file is the thing that is wrong.

Run:  python art_source/pause_ui/make_pause_mocks.py <backdrop_eric.png> <backdrop_carter.png> <out>
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
UI = os.path.join(ROOT, "Assets", "UI")
FONT_PATH = os.path.join(ROOT, "fonts", "PixelifySans.ttf")

W, H = 1920, 1080

# DawnBringer tones lifted straight out of the existing UI PNGs.
BLACK = (0, 0, 0, 255)
GOLD = (251, 242, 54, 255)          # ui_button frame highlight, Victory! title
TAN = (217, 160, 102, 255)          # ControlsArtLayout.FOCUS_RING.color
DARK_GOLD = (138, 111, 48, 255)
NAVY = (34, 32, 52, 255)            # the kit's panel interior, and key_q.png's letters
WHITE = (255, 255, 255, 255)
CHAT_MUTED = (132, 126, 135, 255)   # victory/defeat timestamp

# ---------------------------------------------------------------- LAYOUT
# Mirrored from Scripts/PauseArtLayout.gd. Pixelify Sans is only crisp at multiples of 11.
DIM_ALPHA = 0.72
PANEL_MIN_WIDTH = 672
PANEL_MARGIN = 42
CONFIRM_MIN_WIDTH = 852
ROW_MIN = (576, 110)
ROW_SEPARATION = 14
TITLE_GAP = 30
FOOTER_GAP = 26
CONFIRM_BUTTON_MIN = (324, 110)
CONFIRM_BUTTON_SEPARATION = 36
SLIDER_MIN = (576, 54)
ROW_CONTENT = 24
F_TITLE = 99
F_ROW = 44
F_LABEL = 33
F_FOOTER = 33
F_FOOTER_KEY = 22
FOOTER_KEY_MIN = (64, 64)
TITLE_SHADOW = (20, 18, 33, 255)
TITLE_SHADOW_OFFSET = 3
LABEL_COLOR = (166, 173, 189, 255)   # PauseArtLayout LABEL_COLOR / FOOTER_COLOR
CONFIRM_MESSAGE_COLOR = WHITE

# The strings PauseMenu.gd already holds.
CONFIRM_QUIT = "LEAVE THE FIGHT AND GO BACK TO THE MAIN MENU?"

_fonts = {}


def font(size):
    if size not in _fonts:
        _fonts[size] = ImageFont.truetype(FONT_PATH, size)
    return _fonts[size]


# ---------------------------------------------------------------- text


def _ink(text, size):
    """The thresholded pixels of `text`, plus where they sit relative to the draw origin.

    Godot draws this font with no antialiasing at all, so a >=128 alpha cut reproduces it
    pixel for pixel rather than leaving PIL's grey fringe behind.
    """
    f = font(size)
    pad = size * 2
    lay = Image.new("L", (int(f.getlength(text)) + pad * 2, size * 3 + pad * 2), 0)
    ImageDraw.Draw(lay).text((pad, pad), text, font=f, fill=255)
    hard = lay.point(lambda v: 255 if v >= 128 else 0)
    box = hard.getbbox()
    if box is None:
        return None, 0, 0, 0, 0
    return hard.crop(box), box[0] - pad, box[1] - pad, box[2] - box[0], box[3] - box[1]


def line_height(size):
    ascent, descent = font(size).getmetrics()
    return ascent + descent


def text_width(text, size):
    return _ink(text, size)[3]


def draw_text_centered(img, text, size, color, box, shadow=None):
    """`box` is (x0, y0, x1, y1). Horizontal centring is on the ink and vertical on the line box,
    which is what a Godot Label or Button does."""
    if shadow:
        off = TITLE_SHADOW_OFFSET
        draw_text_centered(img, text, size, shadow,
                           (box[0] + off, box[1] + off, box[2] + off, box[3] + off))
    x0, y0, x1, y1 = box
    mask, dx, dy, w, _ = _ink(text, size)
    if mask is None:
        return
    ox = x0 + (x1 - x0 - w) // 2 - dx
    oy = y0 + (y1 - y0 - line_height(size)) // 2
    img.paste(Image.new("RGBA", mask.size, color), (ox + dx, oy + dy), mask)


# ---------------------------------------------------------------- nine-patch


def load(rel):
    return Image.open(os.path.join(UI, rel)).convert("RGBA")


def nine_patch(src, margin, w, h):
    """Godot's StyleBoxTexture/NinePatchRect in its default stretch mode. `margin` is one number
    because every texture the pause screen uses has the same margin on all four sides."""
    ml = mt = mr = mb = margin
    sw, sh = src.size
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    cols = [(0, ml, 0, ml), (ml, sw - mr, ml, w - mr), (sw - mr, sw, w - mr, w)]
    rows = [(0, mt, 0, mt), (mt, sh - mb, mt, h - mb), (sh - mb, sh, h - mb, h)]
    for sx0, sx1, dx0, dx1 in cols:
        for sy0, sy1, dy0, dy1 in rows:
            if dx1 <= dx0 or dy1 <= dy0:
                continue
            tile = src.crop((sx0, sy0, sx1, sy1))
            if tile.size != (dx1 - dx0, dy1 - dy0):
                tile = tile.resize((dx1 - dx0, dy1 - dy0), Image.NEAREST)
            out.paste(tile, (dx0, dy0))
    return out


def panel(img, rect):
    """PauseArtLayout.PLACEHOLDER_PANEL: the card the Controls table sits on, margins 24."""
    x0, y0, x1, y1 = rect
    img.alpha_composite(nine_patch(load("ui_card_frame_3x.png"), 24, x1 - x0, y1 - y0), (x0, y0))


def row_button(img, rect, label, state="normal", focused=False):
    """PauseArtLayout.PLACEHOLDER_ROW: the main menu's button, with the pause screen's own content
    margins of 24 all round rather than the menu's 30/29."""
    x0, y0, x1, y1 = rect
    art = load({"normal": "ui_button_3x.png",
                "hover": "ui_button_hover_3x.png",
                "pressed": "ui_button_pressed_3x.png"}[state])
    img.alpha_composite(nine_patch(art, 24, x1 - x0, y1 - y0), (x0, y0))
    draw_text_centered(img, label, F_ROW, WHITE,
                       (x0 + ROW_CONTENT, y0 + ROW_CONTENT, x1 - ROW_CONTENT, y1 - ROW_CONTENT))
    if focused:
        focus_ring(img, rect)


def focus_ring(img, rect):
    """ControlsArtLayout.focus_ring(): 6 px of TAN, expanded 6 px outside the control."""
    x0, y0, x1, y1 = rect
    expand = width = 6
    d = ImageDraw.Draw(img)
    for i in range(width):
        d.rectangle([x0 - expand + i, y0 - expand + i, x1 + expand - 1 - i, y1 + expand - 1 - i],
                    outline=TAN)


def slider(img, rect, value):
    """The main menu's volume slider, which the pause screen reuses: track nine-patch, red fill up
    to the grabber, gold grabber."""
    x0, y0, x1, y1 = rect
    track = load("Screens/menu_slider_track_3x.png")
    fill = load("Screens/menu_slider_fill_3x.png")
    grab = load("Screens/menu_slider_grabber_3x.png")
    by = y0 + (y1 - y0 - track.height) // 2
    img.alpha_composite(nine_patch(track, 9, x1 - x0, track.height), (x0, by))
    gx = x0 + int((x1 - x0 - grab.width) * value)
    fill_w = gx + grab.width // 2 - x0
    if fill_w > 20:
        img.alpha_composite(nine_patch(fill, 9, fill_w, track.height), (x0, by))
    img.alpha_composite(grab, (gx, y0 + (y1 - y0 - grab.height) // 2))


# ---------------------------------------------------------------- glyphs


def pad_glyph(column, scale=2, lit=False):
    """A cell of Assets/UI/Pad/pad_buttons.png. Row 1 is the lit version."""
    sheet = load("Pad/pad_buttons.png")
    cell = sheet.height // 2
    g = sheet.crop((column * cell, (1 if lit else 0) * cell,
                    (column + 1) * cell, (1 if lit else 0) * cell + cell))
    return g.resize((cell * scale, cell * scale), Image.NEAREST)


def dpad_glyph(scale=2):
    """The standalone d-pad, which reads better for "select" than two of the sheet's
    single-direction cells side by side."""
    g = load("Pad/pad_dpad.png")
    return g.resize((g.width * scale, g.height * scale), Image.NEAREST)


def arrow_key(which, scale=2):
    """One key out of the shipped key_arrows.png cluster."""
    box = {"up": (32, 0, 64, 32), "down": (32, 32, 64, 64),
           "left": (0, 32, 32, 64), "right": (64, 32, 96, 64)}[which]
    k = load("key_arrows.png").crop(box)
    return k.resize((k.width * scale, k.height * scale), Image.NEAREST)


def keycap(text, scale=2):
    """ControlsArtLayout.keycap() at FOOTER_KEY_MIN_SIZE: key_blank stretched to the name.
    FINAL_KEY_BLANK's margins are quoted at 3x, so they divide by three to get the 1x grid.

    One deliberate difference: the letters are #222034, the colour key_q.png and key_shift.png draw
    their own letters in, rather than ControlsArtLayout's white over a navy shadow. White on the
    pale #CBDBFC key face is near unreadable at 22 px -- see the SHIFT row on the Controls screen.
    """
    blank = load("Pad/key_blank.png")
    blank = blank.resize((blank.width * scale, blank.height * scale), Image.NEAREST)
    cl, ct, cr, cb = (7 * scale, 3 * scale, 7 * scale, 9 * scale)
    w = max(FOOTER_KEY_MIN[0], text_width(text, F_FOOTER_KEY) + cl + cr)
    h = FOOTER_KEY_MIN[1]
    cap = nine_patch(blank, 8 * scale, w, h)
    draw_text_centered(cap, text, F_FOOTER_KEY, NAVY, (cl, ct, w - cr, h - cb))
    return cap


def footer_hints(device, level="root"):
    """[(glyphs, label)] for the footer, swapped per device. Esc is both resume and back, so on the
    keyboard the same cap changes its word between the two levels."""
    if level == "confirm":
        # "CHOOSE", not "CONFIRM": A presses whichever button has focus, and on this dialog that is
        # BACK. Saying CONFIRM next to a button called CONFIRM reads as "A quits".
        if device == "pad":
            return [([pad_glyph(0)], "CHOOSE"), ([pad_glyph(1)], "BACK")]
        return [([keycap("ENTER")], "CHOOSE"), ([keycap("ESC")], "BACK")]
    if device == "pad":
        return [([pad_glyph(13)], "RESUME"), ([dpad_glyph()], "SELECT"),
                ([pad_glyph(0)], "CONFIRM")]
    return [([keycap("ESC")], "RESUME"), ([arrow_key("up"), arrow_key("down")], "SELECT"),
            ([keycap("ENTER")], "CONFIRM")]


HINT_GAP = 48
HINT_LABEL_GAP = 14


def hint_size(hints):
    widths = []
    for glyphs, label in hints:
        w = sum(g.width for g in glyphs) + (len(glyphs) - 1) * 4
        widths.append(w + HINT_LABEL_GAP + text_width(label, F_FOOTER))
    return sum(widths) + HINT_GAP * (len(hints) - 1), FOOTER_KEY_MIN[1], widths


def draw_hints(img, y, hints, centre=960):
    total, row_h, widths = hint_size(hints)
    x = centre - total // 2
    for (glyphs, label), w in zip(hints, widths):
        gx = x
        for g in glyphs:
            img.alpha_composite(g, (gx, y + (row_h - g.height) // 2))
            gx += g.width + 4
        gx += HINT_LABEL_GAP - 4
        draw_text_centered(img, label, F_FOOTER, LABEL_COLOR,
                           (gx, y, gx + text_width(label, F_FOOTER), y + row_h))
        x += w + HINT_GAP
    return row_h


def idle_badge(scale=3):
    """NEW ART. Discord's idle "moon" status dot in the kit's palette and grain: a 16x16 crescent,
    three gold tones lit from the upper left, 1 px pure-black outline, drawn at 1x and blown up 3x
    like everything else in Assets/UI."""
    s = 16
    disc = [[False] * s for _ in range(s)]
    for y in range(s):
        for x in range(s):
            near = ((x + 0.5 - 8.0) ** 2 + (y + 0.5 - 8.0) ** 2) ** 0.5
            bite = ((x + 0.5 - 11.6) ** 2 + (y + 0.5 - 4.4) ** 2) ** 0.5
            disc[y][x] = near <= 6.2 and bite > 5.9

    px = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = px.load()
    for y in range(s):
        for x in range(s):
            if not disc[y][x]:
                touching = any(0 <= y + dy < s and 0 <= x + dx < s and disc[y + dy][x + dx]
                               for dy in (-1, 0, 1) for dx in (-1, 0, 1))
                if touching:
                    d[x, y] = BLACK
                continue
            # Lit from the upper left. At 16 px the crescent is only ~5 px thick, so it carries one
            # shaded rim along its bottom edge and nothing more.
            near = ((x + 0.5 - 8.0) ** 2 + (y + 0.5 - 8.0) ** 2) ** 0.5
            lit = (y + 0.5 - 8.0) + 0.4 * (x + 0.5 - 8.0)
            if near > 5.2 and lit > 1.0:
                d[x, y] = DARK_GOLD
            elif near > 5.2 and lit > -1.0:
                d[x, y] = TAN
            else:
                d[x, y] = GOLD
    return px.resize((s * scale, s * scale), Image.NEAREST)


# ---------------------------------------------------------------- composition


def dim(backdrop, alpha=None):
    """PauseArtLayout.DIM_COLOR: one ColorRect of black over the whole screen. It is what makes the
    panel read over a bright arena and over Carter's near-black barrage alike."""
    out = backdrop.convert("RGBA").copy()
    a = DIM_ALPHA if alpha is None else alpha
    out.alpha_composite(Image.new("RGBA", out.size, (0, 0, 0, int(255 * a))))
    return out


def gold_rule(img, y, half_width=216, centre=960):
    """A 6 px rule under the title, in the kit's frame colours rather than a new texture."""
    d = ImageDraw.Draw(img)
    d.rectangle([centre - half_width, y, centre + half_width - 1, y + 1], fill=DARK_GOLD)
    d.rectangle([centre - half_width, y + 2, centre + half_width - 1, y + 3], fill=GOLD)
    d.rectangle([centre - half_width, y + 4, centre + half_width - 1, y + 5], fill=DARK_GOLD)


# The rows PauseMenuScene.tscn stacks, plus the CONTROLS row the brief asks for, which that scene
# does not have yet (it has an empty ControlsHost instead).
ROWS = [
    ("button", "RESUME"),
    ("button", "RESTART FIGHT"),
    ("button", "CONTROLS"),
    ("label", "VOLUME"),
    ("slider", 0.7),
    ("button", "QUIT TO MAIN MENU"),
]
STATUS_LINE = "@newcomer is idle in #arena-1"
STATUS_GAP = 8


def row_height(kind):
    return {"button": ROW_MIN[1], "label": line_height(F_LABEL), "slider": SLIDER_MIN[1]}[kind]


def pause_menu(backdrop, device="pad", discord=False, focus_style="ring", dim_alpha=None):
    """The root pause screen, measured from its contents exactly as the real containers will."""
    hints = footer_hints(device)
    _, footer_h, _ = hint_size(hints)
    # Sized from the WIDEST device, not the current one. The keyboard footer is 779 px against the
    # pad's 685, so measuring only the live device makes the whole panel jump wider the moment a
    # pad is unplugged mid-pause. The real screen wants the same trick, or one hint fewer.
    footer_w = max(hint_size(footer_hints(d))[0] for d in ("pad", "keyboard"))

    rows_h = sum(row_height(k) for k, _ in ROWS) + ROW_SEPARATION * (len(ROWS) - 1)
    title_h = line_height(F_TITLE)
    status_h = (line_height(F_LABEL) + STATUS_GAP) if discord else 0
    column_h = title_h + status_h + TITLE_GAP + rows_h + FOOTER_GAP + footer_h
    column_w = max(ROW_MIN[0], footer_w)
    panel_w = max(PANEL_MIN_WIDTH, column_w + PANEL_MARGIN * 2)
    panel_h = column_h + PANEL_MARGIN * 2

    px0, py0 = (W - panel_w) // 2, (H - panel_h) // 2
    prect = (px0, py0, px0 + panel_w, py0 + panel_h)
    # ROW_MIN and SLIDER_MIN are minimums. A VBoxContainer's children fill it horizontally, so the
    # rows come out as wide as the column, which the footer sets here.
    cx0, cx1 = 960 - column_w // 2, 960 + column_w // 2

    img = dim(backdrop, dim_alpha)
    panel(img, prect)

    y = py0 + PANEL_MARGIN
    title_box = (prect[0], y, prect[2], y + title_h)
    if discord:
        badge = idle_badge()
        block = badge.width + 24 + text_width("PAUSED", F_TITLE)
        bx = 960 - block // 2
        img.alpha_composite(badge, (bx, y + (title_h - badge.height) // 2))
        draw_text_centered(img, "PAUSED", F_TITLE, WHITE,
                           (bx + badge.width + 24, y, bx + block, y + title_h),
                           shadow=TITLE_SHADOW)
    else:
        draw_text_centered(img, "PAUSED", F_TITLE, WHITE, title_box, shadow=TITLE_SHADOW)
    y += title_h
    if discord:
        y += STATUS_GAP
        draw_text_centered(img, STATUS_LINE, F_LABEL, CHAT_MUTED,
                           (prect[0], y, prect[2], y + line_height(F_LABEL)))
        y += line_height(F_LABEL)

    gold_rule(img, y + TITLE_GAP // 2 - 3)
    y += TITLE_GAP

    for kind, value in ROWS:
        h = row_height(kind)
        if kind == "button":
            focused = value == "RESUME"
            row_button(img, (cx0, y, cx1, y + h), value, focused=focused,
                       state="hover" if focused and focus_style == "ring+face" else "normal")
        elif kind == "label":
            draw_text_centered(img, value, F_LABEL, LABEL_COLOR, (cx0, y, cx1, y + h))
        else:
            slider(img, (cx0, y, cx1, y + h), value)
        y += h + ROW_SEPARATION
    y += FOOTER_GAP - ROW_SEPARATION

    draw_hints(img, y, hints)
    return img


def quit_confirm(backdrop, device="pad"):
    """The confirm over the root screen, which takes a second dip so the dialog owns the frame.
    BACK holds focus, so a blind press of the pad's confirm button cannot throw a run away."""
    img = pause_menu(backdrop, device=device)
    img.alpha_composite(Image.new("RGBA", img.size, (0, 0, 0, 140)))

    hints = footer_hints(device, "confirm")
    footer_w, footer_h, _ = hint_size(hints)
    # PauseMenu.gd holds one long line; at 44 px it has to wrap, and it breaks after "GO".
    message = ["LEAVE THE FIGHT AND GO", "BACK TO THE MAIN MENU?"]
    msg_h = line_height(F_ROW) * len(message)
    buttons_w = CONFIRM_BUTTON_MIN[0] * 2 + CONFIRM_BUTTON_SEPARATION

    # Deliberately NOT PauseArtLayout.CONFIRM_MIN_WIDTH (852): the root panel comes out 863 wide,
    # so a 852 dialog lands within 11 px of it and the two frames read as one shape. Sized from its
    # own contents the dialog is 768, which is clearly inset and reads as sitting on top.
    column_w = max(buttons_w, footer_w, max(text_width(m, F_ROW) for m in message))
    panel_w = column_w + PANEL_MARGIN * 2
    column_h = msg_h + TITLE_GAP + CONFIRM_BUTTON_MIN[1] + FOOTER_GAP + footer_h
    panel_h = column_h + PANEL_MARGIN * 2
    px0, py0 = (W - panel_w) // 2, (H - panel_h) // 2
    panel(img, (px0, py0, px0 + panel_w, py0 + panel_h))

    y = py0 + PANEL_MARGIN
    for line in message:
        draw_text_centered(img, line, F_ROW, CONFIRM_MESSAGE_COLOR,
                           (px0, y, px0 + panel_w, y + line_height(F_ROW)))
        y += line_height(F_ROW)
    y += TITLE_GAP

    # Same as the rows: the HBox's two children fill it, so they are wider than the 324 minimum.
    bh = CONFIRM_BUTTON_MIN[1]
    bw = (column_w - CONFIRM_BUTTON_SEPARATION) // 2
    bx = 960 - column_w // 2
    row_button(img, (bx, y, bx + bw, y + bh), "BACK", focused=True)
    row_button(img, (bx + bw + CONFIRM_BUTTON_SEPARATION, y,
                     bx + bw * 2 + CONFIRM_BUTTON_SEPARATION, y + bh), "CONFIRM")
    y += bh + FOOTER_GAP

    draw_hints(img, y, hints)
    return img


def focus_options(backdrop, path):
    """One open question for the approval pass, side by side: the main menu's focus ring alone,
    versus the ring plus the brighter hover face. The ring is tan, and on a gold-framed row it
    lands right next to the row's own tan frame, which is a quieter cue than it is on the menu's
    dark sky."""
    shots = []
    for label, style in [("A   focus ring only, exactly as the main menu draws it", "ring"),
                         ("B   focus ring plus the brighter hover face", "ring+face")]:
        full = pause_menu(backdrop, "pad", focus_style=style)
        shots.append((label, full.crop((960 - ROW_MIN[0] // 2 - 42, 232,
                                        960 + ROW_MIN[0] // 2 + 42, 232 + ROW_MIN[1] + 36))))
    cap, pad = 44, 18
    w = shots[0][1].width + pad * 2
    h = pad + (cap + shots[0][1].height + pad) * 2
    sheet = Image.new("RGBA", (w, h), (18, 17, 27, 255))
    y = pad
    for label, shot in shots:
        draw_text_centered(sheet, label, F_FOOTER_KEY, WHITE, (0, y, w, y + cap))
        sheet.alpha_composite(shot, (pad, y + cap))
        y += cap + shot.height + pad
    sheet.convert("RGB").save(path)


def dim_options(eric, carter, path):
    """The second open question: DIM_COLOR is a flat black ColorRect, and Carter's barrage is
    already near black, so at 0.72 his fight disappears behind the panel entirely and the screen
    reads as a menu floating in a void. Eric's bright arena is what 0.72 was picked for. Same two
    backdrops at 0.72 and at 0.55, so one value can be chosen for both."""
    cells = []
    for name, backdrop in [("ERIC", eric), ("CARTER", carter)]:
        for alpha in (0.72, 0.55):
            cells.append(("%s   dim %.2f" % (name, alpha),
                          pause_menu(backdrop, "pad", dim_alpha=alpha)))
    tw, th, cap, pad = 760, 428, 40, 14
    sheet = Image.new("RGBA", (tw * 2 + pad * 3, (th + cap) * 2 + pad * 3), (18, 17, 27, 255))
    for n, (label, im) in enumerate(cells):
        x = pad + (n % 2) * (tw + pad)
        y = pad + (n // 2) * (th + cap + pad)
        draw_text_centered(sheet, label, F_FOOTER_KEY, WHITE, (x, y, x + tw, y + cap))
        sheet.alpha_composite(im.convert("RGBA").resize((tw, th), Image.LANCZOS), (x, y + cap))
    sheet.convert("RGB").save(path)


def contact(images, path, cols=3):
    tw, th = 640, 360
    rows = (len(images) + cols - 1) // cols
    sheet = Image.new("RGB", (tw * cols, th * rows), (12, 12, 16))
    for n, im in enumerate(images):
        sheet.paste(im.convert("RGB").resize((tw, th), Image.LANCZOS),
                    ((n % cols) * tw, (n // cols) * th))
    sheet.save(path)


def main():
    eric = Image.open(sys.argv[1])
    carter = Image.open(sys.argv[2])
    out = sys.argv[3]
    os.makedirs(out, exist_ok=True)

    shots = [
        ("pause_menu_pad", pause_menu(eric, "pad")),
        ("pause_menu_keyboard", pause_menu(eric, "keyboard")),
        ("pause_quit_confirm", quit_confirm(eric)),
        ("pause_menu_discord", pause_menu(eric, "pad", discord=True)),
        ("pause_menu_pad_carter", pause_menu(carter, "pad")),
        ("pause_quit_confirm_carter", quit_confirm(carter)),
    ]
    made = []
    for name, im in shots:
        p = os.path.join(out, name + ".png")
        im.convert("RGB").save(p)
        made.append(im)
        print("wrote", p)

    idle_badge(3).save(os.path.join(out, "new_art_idle_badge_3x.png"))
    idle_badge(1).save(os.path.join(out, "new_art_idle_badge.png"))
    focus_options(eric, os.path.join(out, "pause_focus_options.png"))
    dim_options(eric, carter, os.path.join(out, "pause_dim_options.png"))
    print("wrote", os.path.join(out, "pause_dim_options.png"))
    contact(made, os.path.join(out, "contact_sheet.png"))
    print("wrote", os.path.join(out, "pause_focus_options.png"))
    print("wrote", os.path.join(out, "contact_sheet.png"))


if __name__ == "__main__":
    main()
