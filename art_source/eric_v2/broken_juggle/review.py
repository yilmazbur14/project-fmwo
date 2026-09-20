"""Approval-pass deliverables: renders every key frame + the settled crater, a labelled review sheet and
the game-scale mocks.

    python review.py <out_dir> <arena_capture.png>

<out_dir>/keys/<name>.png        native 256x192 key frames (+ _4x previews), crater_settle.png (128x48),
                                 planted_sword.png (the sword alone in his frame space), broken_head_pixel.txt
<out_dir>/keyframes_review.png   all key frames at 3x on the mat green, labelled with their sheet slots
<out_dir>/mock_*.png             game-scale mocks in the captured arena frame
"""
import os
import sys
import subprocess
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SLOTS = [
    ('reel', 'eric_broken 1: reel'), ('kneel', 'eric_broken 4: kneel'), ('slumped', 'eric_broken 5: slumped (loop)'),
    ('winded', 'eric_winded 0'), ('tumble', 'eric_juggle 3: tumble (loop)'), ('crash', 'eric_juggle 6: crash'),
    ('lying', 'eric_juggle 9: lying'),
]
MAT = (0x7e, 0xa8, 0x5b, 255)


def run(*args):
    subprocess.run([sys.executable] + list(args), cwd=HERE, check=True)


def main():
    out, arena = sys.argv[1], sys.argv[2]
    keys = os.path.join(out, 'keys')
    os.makedirs(keys, exist_ok=True)
    run('keys.py', keys)
    run('crater.py', keys)
    run('mock.py', keys, arena, out)
    try:
        font = ImageFont.load_default(size=22)
    except TypeError:
        font = ImageFont.load_default()
    s, pad, head = 3, 12, 30
    fw, fh = 256 * s, 192 * s
    cols = 4
    rows = 2
    W = cols * (fw + pad) + pad
    H = rows * (fh + pad + head) + pad
    sheet = Image.new('RGBA', (W, H), (34, 34, 38, 255))
    d = ImageDraw.Draw(sheet)
    items = SLOTS + [('crater_settle', 'eric_crash_crater 2: settle (128x48)')]
    for i, (name, title) in enumerate(items):
        im = Image.open(os.path.join(keys, name + '.png')).convert('RGBA')
        bg = Image.new('RGBA', im.size, MAT)
        bg.alpha_composite(im)
        big = bg.resize((im.size[0] * s, im.size[1] * s), Image.NEAREST)
        x = pad + (i % cols) * (fw + pad)
        y = pad + (i // cols) * (fh + pad + head)
        d.text((x, y), title, fill=(255, 235, 120, 255), font=font)
        if name == 'crater_settle':
            sheet.paste(big, (x + (fw - big.size[0]) // 2, y + head + (fh - big.size[1]) // 2))
        else:
            sheet.paste(big, (x, y + head))
    sheet.save(os.path.join(out, 'keyframes_review.png'))
    print('review sheet', os.path.join(out, 'keyframes_review.png'), sheet.size)


if __name__ == '__main__':
    main()
