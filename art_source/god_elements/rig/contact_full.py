"""Contact sheets of the full set at GAME SCALE (2 px a texel, as the god fight draws its 3x world at 2/3), every
new sheet beside its live source, frames wrapped 8 to a row. Avatar sheets show three rows: the live sheet, the
puppet body, and the body with its additive glow strip over the void colour."""
import json
from ge_common import *
from PIL import ImageDraw

STAGE = os.path.join(GE, 'full')
OUTD = os.path.join(STAGE, 'contact')
VOID = (14, 10, 24)
S2 = 2
PER_ROW = 8


def frames_of(path, fw):
    a = np.array(Image.open(path).convert('RGBA'))
    return [a[:, i * fw:(i + 1) * fw] for i in range(a.shape[1] // fw)]


def on_void(f, add=None):
    base = np.zeros(f.shape[:2] + (3,), float) + VOID
    al = f[:, :, 3:4] / 255.0
    base = base * (1 - al) + f[:, :, :3] * al
    if add is not None:
        base = base + add[:, :, :3] * (add[:, :, 3:4] / 255.0)
    out = np.clip(base, 0, 255).astype(np.uint8)
    return np.dstack([out, np.full(f.shape[:2], 255, np.uint8)])


def tiles_row(frames, label, gap=6):
    big = [Image.fromarray(on_void(f) if f.shape[2] == 4 and (f[:, :, 3] < 255).any() else f, 'RGBA').resize(
        (f.shape[1] * S2, f.shape[0] * S2), Image.NEAREST) for f in frames]
    rows = [big[i:i + PER_ROW] for i in range(0, len(big), PER_ROW)]
    W = max(sum(t.width for t in r) + gap * (len(r) - 1) for r in rows) + 8
    H = sum(max(t.height for t in r) for r in rows) + gap * (len(rows) - 1) + 18
    out = Image.new('RGBA', (W, H), (30, 26, 40, 255))
    ImageDraw.Draw(out).text((4, 3), label, fill=(255, 220, 120, 255))
    y = 18
    for r in rows:
        x = 4
        for t in r:
            out.paste(t, (x, y))
            x += t.width + gap
        y += max(t.height for t in r) + gap
    return out


def stack(ims, gap=10):
    W = max(i.width for i in ims)
    H = sum(i.height for i in ims) + gap * (len(ims) - 1)
    out = Image.new('RGBA', (W, H), (18, 15, 26, 255))
    y = 0
    for i in ims:
        out.paste(i, (0, y))
        y += i.height + gap
    return out


def main():
    os.makedirs(OUTD, exist_ok=True)
    nums = json.load(open(os.path.join(STAGE, 'numbers.json')))
    # Liam
    blocks = []
    for name in ('channel', 'blow', 'ignite', 'cast_left', 'cast_right', 'slam_rise'):
        live = frames_of(CHARS + '/Liam/Elements/liam_%s.png' % name, 96)
        body = frames_of(os.path.join(STAGE, 'Puppets/liam/liam_%s.png' % name), 96)
        glow = frames_of(os.path.join(STAGE, 'Puppets/liam/liam_%s_avatar.png' % name), 96)
        n = nums['Puppets/liam/liam_' + name]
        blocks.append(stack([tiles_row(live, 'LIVE Liam/Elements/liam_%s.png  (%d frames)' % (name, len(live))),
                             tiles_row(body, 'PUPPET liam_%s.png  black %s%%  colours %s' % (
                                 name, [x['black_pct'] for x in n['body_numbers']][0], n['body_numbers'][0]['colours'])),
                             tiles_row([on_void(b, g) for b, g in zip(body, glow)], '+ liam_%s_avatar.png (additive)' % name)], 2))
    for name, fw in (('wobble', 96), ('fall', 96), ('downed', 96), ('defeat', 96), ('juggle', 128)):
        live = frames_of(CHARS + '/Liam/Elements/liam_%s.png' % name, fw)
        pup = frames_of(os.path.join(STAGE, 'Puppets/liam/liam_%s.png' % name), fw)
        n = nums['Puppets/liam/liam_' + name]
        blocks.append(stack([tiles_row(live, 'LIVE liam_%s.png' % name),
                             tiles_row(pup, 'PUPPET liam_%s.png (staff-less)  black %s%%  colours %s' % (
                                 name, n['numbers'][0]['black_pct'], n['numbers'][0]['colours']))], 2))
        ab = frames_of(os.path.join(STAGE, 'Puppets/liam/liam_avatar_aura_back.png'), 128)
    af = frames_of(os.path.join(STAGE, 'Puppets/liam/liam_avatar_aura_front.png'), 128)
    on = frames_of(os.path.join(STAGE, 'Puppets/liam/liam_avatar_on.png'), 96)
    off = frames_of(os.path.join(STAGE, 'Puppets/liam/liam_avatar_off.png'), 96)
    body0 = frames_of(os.path.join(STAGE, 'Puppets/liam/liam_channel.png'), 96)[0]
    comps = []
    for b_, f_ in zip(ab, af):
        c = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
        c.alpha_composite(Image.fromarray(b_, 'RGBA'))
        c.alpha_composite(Image.fromarray(body0, 'RGBA'), (16, 8))
        c.alpha_composite(Image.fromarray(f_, 'RGBA'))
        comps.append(np.array(c))
    blocks.append(stack([tiles_row(comps, 'liam_avatar_aura_back/front (6-frame loop) round channel f0'),
                         tiles_row([on_void(body0, g) for g in on], 'liam_avatar_on (additive, on channel f0)'),
                         tiles_row([on_void(body0, g) for g in off], 'liam_avatar_off')], 2))
    stack(blocks[:6]).save(os.path.join(OUTD, 'contact_liam_avatar.png'))
    stack(blocks[6:]).save(os.path.join(OUTD, 'contact_liam_rest.png'))
    # Bixby
    blocks = []
    for sheet, fw in (('bixby_beast', 192), ('bixby_beast_fly', 192), ('bixby_beast_flyby', 192), ('bixby_perch', 192),
                      ('bixby_pound', 192), ('bixby_beast_land', 192), ('bixby_beast_recover', 192),
                      ('bixby_beast_hit', 192), ('bixby_juggle', 256)):
        live = frames_of(CHARS + '/Bixby/%s.png' % sheet, fw)
        pup = frames_of(os.path.join(STAGE, 'Puppets/bixby/%s.png' % sheet), fw)
        n = nums['Puppets/bixby/' + sheet]
        blocks.append(stack([tiles_row(live, 'LIVE Bixby/%s.png' % sheet),
                             tiles_row(pup, 'PUPPET %s.png  black %s%%  colours %s  (ember eyes on %s)' % (
                                 sheet, n['numbers'][0]['black_pct'], n['numbers'][0]['colours'], n['ember_eye_frames']))], 2))
    hover = frames_of(CHARS + '/Bixby/bixby_beast.png', 192)[:1]
    bite = frames_of(os.path.join(STAGE, 'Puppets/bixby/bixby_bite.png'), 192)
    blocks.append(stack([tiles_row(hover, 'LIVE bixby_beast f0 (the bite is built on it)'),
                         tiles_row(bite, 'NEW bixby_bite.png: rear, lunge start, lunge, SNAP (contact), recoil')], 2))
    stack(blocks[:4]).save(os.path.join(OUTD, 'contact_bixby_a.png'))
    stack(blocks[4:]).save(os.path.join(OUTD, 'contact_bixby_b.png'))
    # the wheel
    def fr(name, fw):
        return frames_of(os.path.join(STAGE, 'Wheel/%s.png' % name), fw)
    stack([tiles_row(fr('element_wheel', 192), 'element_wheel.png: 0, 11.25 ... 78.75 deg clockwise'),
           tiles_row(fr('element_wheel_lit', 192), 'element_wheel_lit.png: water, earth, fire, air, fire+air, air+water, water+earth, earth+fire'),
           tiles_row(fr('element_wheel_pointer', 40) + fr('element_icons', 32), 'pointer (rest, bump, lit) + element_icons (pop/hold: fire, air, water, earth)'),
           tiles_row(fr('element_wheel_blur', 192), 'element_wheel_blur.png (soft)'),
           tiles_row(fr('element_wheel_form', 192), 'element_wheel_form.png (soft)'),
           tiles_row(fr('element_wheel_shatter', 208), 'element_wheel_shatter.png (soft)')]).save(
        os.path.join(OUTD, 'contact_wheel.png'))
    print('ok', os.listdir(OUTD))


if __name__ == '__main__':
    main()
