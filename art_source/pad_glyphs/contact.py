"""6x contact sheet of every pad glyph, labelled, on the card navy, with the
existing keycaps in the first row for the family comparison."""
import os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = 'C:/Users/theyi/OneDrive/Documents/new-game-project'
SRC = os.environ.get('PAD_SRC', PROJ + '/Assets/UI/Pad')
FONT = PROJ + '/fonts/PixelifySans.ttf'
S = 6
BG = (34, 32, 52)
INK = (203, 219, 252)
DIM = (155, 173, 183)
GOLD = (251, 242, 54)

ROWS = [
    ('Existing keycaps (reference)', [('../key_q', 'key_q'), ('../key_w', 'key_w'),
                                      ('../key_shift', 'key_shift'), ('../key_arrows', 'key_arrows')]),
    ('Face buttons', ['pad_face_down', 'pad_face_right', 'pad_face_left', 'pad_face_up', 'pad_face_all']),
    ('D-pad', ['pad_dpad', 'pad_dpad_up', 'pad_dpad_down', 'pad_dpad_left', 'pad_dpad_right']),
    ('Left stick', ['pad_stick_left', 'pad_stick_left_push', 'pad_stick_left_64', 'pad_stick_left_push_64']),
    ('Shoulders, triggers, start', ['pad_bumper_l', 'pad_bumper_r', 'pad_trigger_l', 'pad_trigger_r', 'pad_start']),
    ('Movement card (drop-in for key_arrows.png)', ['pad_move']),
    ('Button atlas for ControlsArtLayout: 14 columns (PAD_BUTTON_FRAMES order + Start), row 0 rest, row 1 lit',
     ['pad_buttons']),
    ('Inline set for dialogue: 11x11 cells, same order, shown at 3x (pad_buttons_inline_3x.png)',
     ['pad_buttons_inline']),
    ('Blank keycap for rebound keys (9-slice, margin 8px / 24px at 3x)', ['key_blank']),
]


def load(entry):
    if isinstance(entry, tuple):
        rel, label = entry
        p = os.path.normpath(os.path.join(PROJ + '/Assets/UI/Pad', rel + '.png'))
    else:
        label = entry
        p = os.path.join(SRC, entry + '.png')
    return label, Image.open(p).convert('RGBA')


if __name__ == '__main__':
    f_head = ImageFont.truetype(FONT, 30)
    f_lab = ImageFont.truetype(FONT, 20)
    pad, gap, head_h, lab_h = 28, 36, 46, 30
    rows = [(t, [load(e) for e in es]) for t, es in ROWS]
    probe = ImageDraw.Draw(Image.new('RGB', (1, 1)))

    def cell_w(label, im):
        lw = probe.textlength('%s  %dx%d' % (label, im.width, im.height), font=f_lab)
        return max(im.width * S, int(lw)) + gap

    W = max(sum(cell_w(l, im) for l, im in r) for _, r in rows) + pad * 2
    H = pad + sum(head_h + max(im.height for _, im in r) * S + lab_h + 20 for _, r in rows) + pad
    sheet = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(sheet)
    y = pad
    for title, r in rows:
        d.text((pad, y), title, font=f_head, fill=GOLD)
        y += head_h
        x = pad
        rh = max(im.height for _, im in r) * S
        for label, im in r:
            big = im.resize((im.width * S, im.height * S), Image.NEAREST)
            sheet.paste(big, (x, y + (rh - big.height)), big)
            d.text((x, y + rh + 6), '%s  %dx%d' % (label, im.width, im.height),
                   font=f_lab, fill=INK if not label.startswith('key') else DIM)
            x += cell_w(label, im)
        y += rh + lab_h + 20
    import tempfile
    out = os.environ.get('PAD_OUT', os.path.join(
        os.environ.get('PAD_PREVIEW_OUT', os.path.join(tempfile.gettempdir(), 'pad_glyphs_preview')),
        'contact_sheet_6x.png'))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sheet.save(out)
    print(out, sheet.size)
