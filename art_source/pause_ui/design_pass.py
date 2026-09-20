"""The final pause art composited over a real paused fight frame, at 1920x1080.

This is the approval render, not a mock: every texture it draws is a PNG out of build_pause_art.py,
nine-patched the way Godot's StyleBoxTexture nine-patches it, and every size comes from
Scripts/PauseArtLayout.gd rather than from make_pause_mocks.py, whose LAYOUT block has drifted
(ROW_MIN 110 vs the layout's 96, PANEL_MARGIN 42 vs 36, three footer hints vs PauseMenu.gd's two).
Where this file and PauseArtLayout disagree, PauseArtLayout wins and this file is the bug.

  python art_source/pause_ui/design_pass.py <art_dir> <backdrop.png> <out_dir>

Text is Pixelify Sans thresholded, which is how Godot draws it - no antialiasing anywhere.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from PIL import Image, ImageDraw  # noqa: E402
import make_pause_mocks as M  # noqa: E402

W, H = 1920, 1080

# ---------------------------------------------------------------- PauseArtLayout.gd, verbatim
DIM_ALPHA = 0.55                 # the settled value; the shipped const still says 0.72
PANEL_MIN_WIDTH = 672
PANEL_MARGIN = 36
CONFIRM_MIN_WIDTH = 852
ROW_MIN = (576, 96)
ROW_SEPARATION = 14
COLUMN_SEPARATION = 30
FOOTER_SEPARATION = 54
FOOTER_HINT_SEPARATION = 12
CONFIRM_BUTTON_MIN = (324, 96)
CONFIRM_BUTTON_SEPARATION = 36
SLIDER_MIN = (576, 54)
ROW_CONTENT = 24
F_ROW = 44
F_LABEL = 33
F_FOOTER = 33
F_FOOTER_KEY = 22
FOOTER_KEY_MIN = (64, 64)
LABEL_COLOR = (166, 173, 189, 255)
WHITE = (255, 255, 255, 255)
# ControlsArtLayout.FOCUS_RING
RING_COLOR = (217, 160, 102, 255)
RING_WIDTH = 6
RING_EXPAND = 6

# A StyleBoxTexture whose content margins are left at -1 falls back to its texture margins, and
# PauseArtLayout sets content margins on the row but not on either panel. So a panel insets its
# child by 24 on every side before MarginContainer's 36 - 60 in total, which is the number that
# actually decides how big this screen is.
PANEL_TEXTURE_MARGIN = 24
ART_MARGIN = 24                  # the 9-slice margin of every _3x texture in the set

# PauseMenu.gd FOOTER_HINTS: two, and the pad columns they draw.
FOOTER_HINTS = [("RESUME", 13), ("BACK", 1)]
ROWS = [
    ("button", "RESUME"),
    ("button", "RESTART FIGHT"),
    ("button", "CONTROLS"),
    ("label", "VOLUME"),
    ("slider", 0.7),
    ("button", "QUIT TO MAIN MENU"),
]
CONFIRM_MESSAGE = ["LEAVE THE FIGHT AND GO", "BACK TO THE MAIN MENU?"]

_art_dir = None
_cache = {}


def art(name):
    if name not in _cache:
        _cache[name] = Image.open(os.path.join(_art_dir, name + ".png")).convert("RGBA")
    return _cache[name]


def patch(img, name, rect, margin=ART_MARGIN):
    x0, y0, x1, y1 = rect
    img.alpha_composite(M.nine_patch(art(name), margin, x1 - x0, y1 - y0), (x0, y0))


def focus_ring(img, rect):
    x0, y0, x1, y1 = rect
    d = ImageDraw.Draw(img)
    for i in range(RING_WIDTH):
        d.rectangle([x0 - RING_EXPAND + i, y0 - RING_EXPAND + i,
                     x1 + RING_EXPAND - 1 - i, y1 + RING_EXPAND - 1 - i], outline=RING_COLOR)


def row(img, rect, label, selected=False, ring=True):
    """A pause row. Decision 2: the selected row takes the lit face AND the ring - the ring alone
    is too quiet to find on a pad, and the face alone has no hard edge."""
    patch(img, "pause_row_focus_3x" if selected else "pause_row_3x", rect)
    x0, y0, x1, y1 = rect
    M.draw_text_centered(img, label, F_ROW, WHITE,
                         (x0 + ROW_CONTENT, y0 + ROW_CONTENT, x1 - ROW_CONTENT, y1 - ROW_CONTENT))
    if selected and ring:
        focus_ring(img, rect)


# ---------------------------------------------------------------- footer


def hint_parts(device):
    """[(label, glyph_image)] - the drawn pad glyph, or the written key the keyboard shows."""
    out = []
    for label, column in FOOTER_HINTS:
        if device == "pad":
            out.append((label, M.pad_glyph(column, scale=2)))
        else:
            out.append((label, M.keycap("ESC", scale=2)))
    return out


def footer_size(device):
    parts = hint_parts(device)
    widths = [M.text_width(lbl, F_FOOTER) + FOOTER_HINT_SEPARATION + g.width for lbl, g in parts]
    return sum(widths) + FOOTER_SEPARATION * (len(parts) - 1), FOOTER_KEY_MIN[1], widths


def draw_footer(img, y, device, centre=W // 2):
    total, row_h, widths = footer_size(device)
    parts = hint_parts(device)
    x = centre - total // 2
    for (label, glyph), w in zip(parts, widths):
        lw = M.text_width(label, F_FOOTER)
        M.draw_text_centered(img, label, F_FOOTER, LABEL_COLOR, (x, y, x + lw, y + row_h))
        img.alpha_composite(glyph, (x + lw + FOOTER_HINT_SEPARATION, y + (row_h - glyph.height) // 2))
        x += w + FOOTER_SEPARATION
    return row_h


# ---------------------------------------------------------------- the screen


# A row is NOT ROW_MIN_SIZE.y tall. ROW_MIN_SIZE is a minimum, and a Button's own minimum is its
# label's line box plus the stylebox's content margins: 54 + 24 + 24 = 102. Checked against a live
# 1920x1080 capture of the screen (capture_ref.gd CAP_MODE=pause), where the rows measure exactly
# 102 with a 116 pitch, the panel 696x937 and the column inset 60 a side.
ROW_H = max(ROW_MIN[1], M.line_height(F_ROW) + ROW_CONTENT * 2)
CONFIRM_BUTTON_H = max(CONFIRM_BUTTON_MIN[1], M.line_height(F_ROW) + ROW_CONTENT * 2)


def row_height(kind):
    return {"button": ROW_H, "label": M.line_height(F_LABEL), "slider": SLIDER_MIN[1]}[kind]


def pause_menu(backdrop, device="pad", dim_alpha=DIM_ALPHA, selected="RESUME", ring=True,
               title_name="pause_title_3x"):
    title = art(title_name)
    # Sized from the widest device, not the live one, or the panel jumps width when a pad is
    # unplugged mid-pause.
    footer_w = max(footer_size(d)[0] for d in ("pad", "keyboard"))
    footer_h = FOOTER_KEY_MIN[1]

    rows_h = sum(row_height(k) for k, _ in ROWS) + ROW_SEPARATION * (len(ROWS) - 1)
    column_h = title.height + COLUMN_SEPARATION + rows_h + COLUMN_SEPARATION + footer_h
    column_w = max(ROW_MIN[0], footer_w, title.width)
    inset = PANEL_TEXTURE_MARGIN + PANEL_MARGIN
    panel_w = max(PANEL_MIN_WIDTH, column_w + inset * 2)
    panel_h = column_h + inset * 2

    px0, py0 = (W - panel_w) // 2, (H - panel_h) // 2
    img = M.dim(backdrop, dim_alpha)
    patch(img, "pause_panel_3x", (px0, py0, px0 + panel_w, py0 + panel_h))

    # A VBoxContainer's children fill it, so the rows are as wide as the column, not their 576 min.
    cx0 = px0 + inset
    cx1 = px0 + panel_w - inset
    y = py0 + inset

    img.alpha_composite(title, (cx0 + (cx1 - cx0 - title.width) // 2, y))
    y += title.height + COLUMN_SEPARATION

    for kind, value in ROWS:
        h = row_height(kind)
        if kind == "button":
            row(img, (cx0, y, cx1, y + h), value, selected=(value == selected), ring=ring)
        elif kind == "label":
            M.draw_text_centered(img, value, F_LABEL, LABEL_COLOR, (cx0, y, cx1, y + h))
        else:
            M.slider(img, (cx0, y, cx1, y + h), value)
        y += h + ROW_SEPARATION
    y += COLUMN_SEPARATION - ROW_SEPARATION

    draw_footer(img, y, device)
    return img


def quit_confirm(backdrop, device="pad"):
    """The confirm screen. PauseMenu._ask() hides Root outright, so the navy panel is NOT behind
    this - the dialog is alone on the dim, and Confirm's column holds only the message and the two
    buttons, no footer. BACK takes focus: a blind press of the pad's accept button must not throw
    a fight away.
    """
    img = M.dim(backdrop, DIM_ALPHA)

    msg_h = M.line_height(F_ROW) * len(CONFIRM_MESSAGE)
    buttons_w = CONFIRM_BUTTON_MIN[0] * 2 + CONFIRM_BUTTON_SEPARATION
    inset = PANEL_TEXTURE_MARGIN + PANEL_MARGIN
    column_w = max(buttons_w, max(M.text_width(m, F_ROW) for m in CONFIRM_MESSAGE))
    panel_w = max(CONFIRM_MIN_WIDTH, column_w + inset * 2)
    column_h = msg_h + COLUMN_SEPARATION + CONFIRM_BUTTON_H
    panel_h = column_h + inset * 2
    px0, py0 = (W - panel_w) // 2, (H - panel_h) // 2
    patch(img, "pause_confirm_panel_3x", (px0, py0, px0 + panel_w, py0 + panel_h))

    cx0, cx1 = px0 + inset, px0 + panel_w - inset
    y = py0 + inset
    for line in CONFIRM_MESSAGE:
        M.draw_text_centered(img, line, F_ROW, WHITE, (cx0, y, cx1, y + M.line_height(F_ROW)))
        y += M.line_height(F_ROW)
    y += COLUMN_SEPARATION

    # The buttons carry a custom minimum and no expand flag in an HBox aligned centre, so they
    # come out at exactly 324 rather than filling the column.
    bw, bh = CONFIRM_BUTTON_MIN[0], CONFIRM_BUTTON_H
    bx = (W - buttons_w) // 2
    row(img, (bx, y, bx + bw, y + bh), "BACK", selected=True)
    row(img, (bx + bw + CONFIRM_BUTTON_SEPARATION, y, bx + buttons_w, y + bh), "CONFIRM")
    return img


# ---------------------------------------------------------------- review sheets


def crop_rows(img, path, label):
    """The selected row and its neighbours, at 1:1, which is how the selection actually gets read."""
    shot = img.crop((W // 2 - 380, 272, W // 2 + 380, 272 + ROW_H * 2 + ROW_SEPARATION + 40))
    cap, pad = 44, 16
    sheet = Image.new("RGBA", (shot.width + pad * 2, shot.height + cap + pad), (18, 17, 27, 255))
    M.draw_text_centered(sheet, label, F_FOOTER_KEY, WHITE, (0, 0, sheet.width, cap))
    sheet.alpha_composite(shot, (pad, cap))
    sheet.convert("RGB").save(path)


def dim_compare(backdrop, path):
    """The settled 0.55 against the shipped 0.72, so the call can be seen rather than argued."""
    cells = [("DIM 0.55   the settled value", pause_menu(backdrop, dim_alpha=0.55)),
             ("DIM 0.72   what PauseArtLayout still says", pause_menu(backdrop, dim_alpha=0.72))]
    tw, th, cap, pad = 880, 495, 40, 14
    sheet = Image.new("RGBA", (tw * 2 + pad * 3, th + cap + pad * 2), (18, 17, 27, 255))
    for n, (label, im) in enumerate(cells):
        x = pad + n * (tw + pad)
        M.draw_text_centered(sheet, label, F_FOOTER_KEY, WHITE, (x, pad, x + tw, pad + cap))
        sheet.alpha_composite(im.convert("RGBA").resize((tw, th), Image.LANCZOS), (x, pad + cap))
    sheet.convert("RGB").save(path)


def selection_compare(backdrop, path):
    """Decision 2, shown: the ring on its own, then the lit row plus the ring."""
    cells = [("A   ring only, as the screen draws focus today", pause_menu(backdrop, selected=None)),
             ("B   lit row plus the ring   (the settled call)", pause_menu(backdrop))]
    shots = []
    for label, im in cells:
        shots.append((label, im.crop((W // 2 - 400, 268, W // 2 + 400, 268 + ROW_H + 36))))
    cap, pad = 44, 16
    w = shots[0][1].width + pad * 2
    sheet = Image.new("RGBA", (w, pad + (cap + shots[0][1].height + pad) * 2), (18, 17, 27, 255))
    y = pad
    for label, shot in shots:
        M.draw_text_centered(sheet, label, F_FOOTER_KEY, WHITE, (0, y, w, y + cap))
        sheet.alpha_composite(shot, (pad, y + cap))
        y += cap + shot.height + pad
    sheet.convert("RGB").save(path)


def main():
    global _art_dir
    _art_dir, backdrop_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(out, exist_ok=True)
    backdrop = Image.open(backdrop_path).convert("RGBA")
    if backdrop.size != (W, H):
        raise SystemExit("backdrop is %s, need %dx%d" % (backdrop.size, W, H))

    shots = [
        ("design_pause_pad", pause_menu(backdrop, "pad")),
        ("design_pause_keyboard", pause_menu(backdrop, "keyboard")),
        ("design_pause_confirm", quit_confirm(backdrop)),
    ]
    for name, im in shots:
        p = os.path.join(out, name + ".png")
        im.convert("RGB").save(p)
        print("wrote", p)
    dim_compare(backdrop, os.path.join(out, "design_dim_compare.png"))
    selection_compare(backdrop, os.path.join(out, "design_selection_compare.png"))
    crop_rows(shots[0][1], os.path.join(out, "design_rows_1to1.png"),
              "rows at 1:1   selected / resting")
    print("wrote the three compare sheets")


if __name__ == "__main__":
    main()
