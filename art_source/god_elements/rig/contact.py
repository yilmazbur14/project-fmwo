"""The contact sheet: the new pieces beside the shipped puppet twins, every one at GAME SCALE (2 screen px a
texel, as the god fight's 2/3 view draws its 3x world), cropped to the figure, bottoms on one floor line."""
from ge_common import *
from PIL import ImageDraw
import liam_aura as LA

PUPS = PROJECT + '/Assets/Characters/Jordan/Puppets/'
S2 = 2
BG = (14, 10, 24, 255)
INK = (210, 205, 230, 255)


def frame_of(path, fw, f=0):
    im = Image.open(path).convert('RGBA')
    return im.crop((f * fw, 0, (f + 1) * fw, im.height))


def crop(im):
    b = im.getbbox()
    return im.crop((max(0, b[0] - 2), max(0, b[1] - 2), min(im.width, b[2] + 2), min(im.height, b[3] + 1)))


def row(items, title, floor_gap=26):
    tiles = [(crop(im), lab) for im, lab in items]
    H = max(t.height for t, _ in tiles) * S2
    W = sum(t.width * S2 for t, _ in tiles) + 24 * (len(tiles) + 1)
    out = Image.new('RGBA', (W, H + floor_gap + 40), BG)
    d = ImageDraw.Draw(out)
    d.text((10, 6), title, fill=(255, 220, 120, 255))
    x = 24
    for t, lab in tiles:
        big = t.resize((t.width * S2, t.height * S2), Image.NEAREST)
        out.alpha_composite(big, (x, 26 + H - big.height))
        d.text((x, 26 + H + 6), lab, fill=INK)
        x += big.width + 24
    d.line([(10, 26 + H), (W - 10, 26 + H)], fill=(60, 52, 84, 255))
    return out


def build():
    roster = [
        (frame_of(PUPS + 'greyson/greyson_idle.png', 112), 'greyson'),
        (frame_of(PUPS + 'matt/matt_idle.png', 96), 'matt'),
        (frame_of(PUPS + 'burak/burak_idle.png', 96), 'captain burak'),
        (frame_of(PUPS + 'mason/mason_sheet.png', 64), 'mason'),
        (frame_of(PUPS + 'josh/josh_idle.png', 80), 'josh'),
        (frame_of(PUPS + 'carter/carter_idle.png', 96), 'carter'),
        (frame_of(PROJECT + '/art_source/jordan_puppets/approval/liam/liam_idle_B.png', 64), 'liam (roster pass, unshipped)'),
        (frame_of(PUPS + 'danny/danny_sumo_idle.png', 176), 'danny (sumo)'),
        (frame_of(PUPS + 'eric/eric_entrance.png', 256, 3), 'eric'),
    ]
    lf = np.array(Image.open(OUT + '/liam_puppet_avatar.png').convert('RGBA'))
    ab = np.array(Image.open(OUT + '/liam_puppet_avatar_aura_back.png').convert('RGBA'))
    af = np.array(Image.open(OUT + '/liam_puppet_avatar_aura_front.png').convert('RGBA'))
    comps = [LA.composite(lf[:, f * 96:(f + 1) * 96], ab[:, f * 128:(f + 1) * 128], af[:, f * 128:(f + 1) * 128])
             for f in range(2)]
    new = [
        (frame_of(OUT + '/liam_puppet_avatar.png', 96, 0), 'NEW liam avatar f0 float'),
        (comps[0], '+ aura'),
        (comps[1], 'f1 surge + aura'),
        (frame_of(OUT + '/bixby_puppet.png', 192, 0), 'NEW bixby f0 (ash fur, recommended)'),
        (frame_of(OUT + '/bixby_puppet.png', 192, 1), 'bixby f1'),
        (frame_of(OUT + '/bixby_puppet_blood.png', 192, 0), 'alt: blood fur'),
    ]
    live = [
        (frame_of(CHARS + '/Liam/liam.png', 64), 'live liam.png'),
        (frame_of(CHARS + '/Bixby/bixby_beast_fly.png', 192, 0), 'live bixby_beast_fly f0'),
        (frame_of(OUT + '/element_wheel.png', 192, 0), 'NEW element wheel (rest)'),
        (frame_of(OUT + '/element_wheel.png', 192, 3), 'stopped on fire'),
    ]
    rows = [row(roster, 'THE SHIPPED PUPPET TWINS (take B), idle frame 0 - game scale, 2 px a texel'),
            row(new, 'THE ELEMENTAL WHEEL PASS - same scale'),
            row(live, 'THE SOURCES THEY CAME FROM, AND THE WHEEL - same scale')]
    W = max(r.width for r in rows)
    out = Image.new('RGBA', (W, sum(r.height for r in rows) + 12 * len(rows)), BG)
    y = 0
    for r in rows:
        out.alpha_composite(r, (0, y))
        y += r.height + 12
    out.save(os.path.join(OUT, 'contact_sheet.png'))
    print('contact', out.size)


if __name__ == '__main__':
    build()
