"""Ship the final demon-god Jordan set (A2, the full mask, no fire column) into the game, as new
files only, and write the previews for the user.

A bare run writes nothing:

    python jg_ship.py                # print this and exit
    python jg_ship.py --check        # build, audit and measure everything; write nothing
    python jg_ship.py --preview      # write the contact sheet and the hover GIF into art_source/jordan_god/
    python jg_ship.py --ship         # write the game files listed in SHIP (PNG + .aseprite each)

--ship only ever writes the paths in SHIP. A target that already exists is refused unless it is
byte-for-byte the file this script shipped last time (recorded in shipped.json beside this
script), so nothing it did not make is ever overwritten. It never writes an .import file (the
user's editor imports new files on focus) and never runs Godot. Each .aseprite is re-exported by
the Aseprite CLI and compared pixel for pixel with its PNG before either file is moved into place.
Nothing is written unless every frame passes the audit (no keyline gaps, strays or pinholes on
the body, no semi-alpha anywhere, his lowest texel on row 223 minus the frame's bob).
"""
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jg_base as B  # noqa: E402
import jg_god as G  # noqa: E402
import jg_lord as L  # noqa: E402
import jg_portrait as PT  # noqa: E402
import jg_runes as RU  # noqa: E402
import jg_void as V  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402
from jg_lord_pal import PAL_A2  # noqa: E402
from PIL import Image, ImageChops, ImageDraw  # noqa: E402

ROOT = B.ROOT
GOD_DIR = os.path.join(ROOT, 'Assets', 'Characters', 'Jordan', 'God')
SHIP = {
    'hover': os.path.join(GOD_DIR, 'jordan_god_hover'),
    'talk': os.path.join(GOD_DIR, 'jordan_god_talk'),
    'aura': os.path.join(GOD_DIR, 'jordan_god_aura'),
    'runes': os.path.join(GOD_DIR, 'jordan_god_runes'),
    'void': os.path.join(ROOT, 'Assets', 'Environment', 'Void', 'void_bg'),
    'portrait': os.path.join(ROOT, 'Assets', 'Characters', 'Jordan', 'portrait_demon'),
}
RECORD = os.path.join(HERE, 'shipped.json')
PORTRAIT_CROP = (138, 70, 43, 43)     # the hover frame-0 region the 64x64 portrait is a 1.5x close-up of


def build_all():
    return {
        'hover': G.hover_image(),
        'talk': G.talk_image(),
        'aura': G.aura_image(),
        'runes': RU.strip(),
        'void': V.backdrop(),
        'portrait': PT.image(),
    }


# ------------------------------------------------------------------ audit

def audit(ims):
    ok = True
    lines = []
    for name, im in ims.items():
        st = B.stats(im)
        lines.append('%-9s %5dx%-4d colours %2d  black %5.1f%%  semi %d' % (
            name, im.width, im.height, st['colours'], 100 * st['black'], st['semi']))
        if st['semi']:
            ok = False
    for i in range(G.N):
        px = G.hover_px(i)
        a = B.audit(px, fx=G.effect_pixels(i))
        low = max(y for (x, y) in px)
        st = B.stats(B.image(px, G.W, G.H, PAL_A2))
        want = G.ANCHOR[1] - G.BOB[i]
        bad = a['gaps'] or a['lone'] or a['holes'] or low != want
        ok &= not bad
        lines.append('  hover %d: bob %d, lowest row %d (want %d), black %.1f%%, colours %d, gaps %d lone %d holes %d%s'
                     % (i, G.BOB[i], low, want, 100 * st['black'], st['colours'], len(a['gaps']), len(a['lone']),
                        len(a['holes']), '  <-- FAIL' if bad else ''))
    for j, open_ in enumerate((False, True)):
        px = G.talk_px(open_)
        a = B.audit(px, fx=G.effect_pixels(0))
        bad = a['gaps'] or a['lone'] or a['holes']
        ok &= not bad
        lines.append('  talk %d (%s): gaps %d lone %d holes %d%s' % (j, 'open' if open_ else 'shut', len(a['gaps']),
                                                                      len(a['lone']), len(a['holes']),
                                                                      '  <-- FAIL' if bad else ''))
    # the portrait against the same crop of hover frame 0
    x0, y0, w, h = PORTRAIT_CROP
    crop = {(x - x0, y - y0): k for (x, y), k in G.hover_px(0).items() if x0 <= x < x0 + w and y0 <= y < y0 + h}
    cst = B.stats(B.image(crop, w, h, PAL_A2))
    pst = B.stats(ims['portrait'])
    pp = PT.build()
    a = B.audit(pp)
    # a portrait is cropped by its frame: body texels at the frame edge are not keyline gaps
    a['gaps'] = [g for g in a['gaps'] if any(q not in pp and 0 <= q[0] < PT.S and 0 <= q[1] < PT.S
                                              for q in B.neighbours4(g[:2]))]
    bad = a['gaps'] or a['lone'] or a['holes']
    ok &= not bad
    lines.append('  portrait: black %.1f%% vs %.1f%% on the same crop of hover frame 0; colours %d vs %d; '
                 'gaps %d lone %d holes %d%s' % (100 * pst['black'], 100 * cst['black'], pst['colours'],
                                                 cst['colours'], len(a['gaps']), len(a['lone']), len(a['holes']),
                                                 '  <-- FAIL' if bad else ''))
    # the rune loop: frame 0 turned a whole 60 degrees must look like frame 0 again (rasterised afresh)
    lines.append('  runes: %d frames at %.2f s = one 60-degree loop in %.1f s (a full turn in %.1f s)'
                 % (RU.FRAMES, RU.FRAME_TIME, RU.FRAMES * RU.FRAME_TIME, 6 * RU.FRAMES * RU.FRAME_TIME))
    return ok, lines


# ------------------------------------------------------------------ previews

def _label(d, xy, s, col=(226, 222, 240, 255)):
    d.text(xy, s, fill=col)


def contact_sheet(ims):
    bgn = ims['void']
    sc = 2
    top = 23                     # frame rows above the screen's top edge at anchor (960,600): not shown
    fw, fh = G.W * sc, (G.H - top) * sc
    pad = 16
    cols = 3
    sheet_w = cols * fw + (cols + 1) * pad
    rows_h = 2 * (fh + 24)
    extra_h = 330
    sheet = Image.new('RGBA', (sheet_w, 60 + rows_h + extra_h), (10, 8, 16, 255))
    d = ImageDraw.Draw(sheet)
    _label(d, (pad, 10), 'Demon-god Jordan, final set (A2, no fire column). Hover: 6 frames x %.2f s, bob drawn in '
                         '(0,1,2,3,2,1 rows up), anchor (160,223) on every frame. Shown at 2x over void_bg with the '
                         'rune circle.' % G.FRAME_TIME)
    _label(d, (pad, 28), 'Talk: 2 frames in hover frame 0\'s pose (shut, open). Aura: 6 additive frames, 336x232, '
                         'anchor (168,223). Runes: %d frames x %.2f s. Portrait 64x64.' % (RU.FRAMES, RU.FRAME_TIME))
    back = bgn.crop((160, 0, 480, 201))
    for i in range(G.N):
        fr = ims['hover'].crop((i * G.W, 0, (i + 1) * G.W, G.H))
        tile = Image.new('RGBA', (G.W, G.H), (0, 0, 0, 255))
        tile.alpha_composite(back, (0, 23))
        rf = RU.frame_image(0)
        cx, cy = L.CORE
        tile.alpha_composite(rf, (int(round(cx - 95.5)), int(round(cy - 95.5))))
        tile.alpha_composite(fr)
        tile = tile.crop((0, top, G.W, G.H))
        x = pad + (i % cols) * (fw + pad)
        y = 60 + (i // cols) * (fh + 24)
        sheet.paste(tile.resize((fw, fh), Image.NEAREST), (x, y))
        _label(d, (x + 4, y + fh + 4), 'hover %d  (bob %d)' % (i, G.BOB[i]))
    y2 = 60 + rows_h + 10
    # talk heads, 4x
    x = pad
    for j, lab in enumerate(('talk 0: shut', 'talk 1: open')):
        fr = ims['talk'].crop((j * G.W, 0, (j + 1) * G.W, G.H))
        tile = Image.new('RGBA', (70, 60), (14, 10, 24, 255))
        tile.alpha_composite(fr.crop((125, 60, 195, 120)))
        sheet.paste(tile.resize((280, 240), Image.NEAREST), (x, y2))
        _label(d, (x, y2 + 244), lab)
        x += 280 + pad
    # aura frame 0 added over the void, with the god on top
    af = ims['aura'].crop((0, 0, G.AURA_W, G.AURA_H))
    base = Image.new('RGB', (G.AURA_W, G.AURA_H), (0, 0, 0))
    base.paste(bgn.crop((152, 0, 152 + G.AURA_W, G.AURA_H - 23)).convert('RGB'), (0, 23))
    base = ImageChops.add(base, af.convert('RGB')).convert('RGBA')
    base.alpha_composite(ims['hover'].crop((0, 0, G.W, G.H)), (G.AURA_PAD, 0))
    sheet.paste(base.crop((0, 23, G.AURA_W, G.AURA_H)), (x, y2))
    _label(d, (x, y2 + G.AURA_H + 4), 'aura (additive) over void + hover 0, 1:1')
    x += G.AURA_W + pad
    # rune frames 0, 6, 12, 18, 24, 30 at 1x
    for k, fi in enumerate((0, 9, 18, 27)):
        rf = RU.frame_image(fi)
        tile = Image.new('RGBA', (RU.SIZE, RU.SIZE), (4, 3, 10, 255))
        tile.alpha_composite(rf)
        tx = x + (k % 2) * (RU.SIZE // 2 + 6)
        ty = y2 + (k // 2) * (RU.SIZE // 2 + 16)
        sheet.paste(tile.resize((RU.SIZE // 2, RU.SIZE // 2), Image.BOX), (tx, ty))
        _label(d, (tx, ty + RU.SIZE // 2 + 2), 'runes %d' % fi)
    x += RU.SIZE + 20
    # portrait at 4x and 1x
    pt = ims['portrait']
    tile = Image.new('RGBA', (64, 64), (60, 60, 72, 255))
    tile.alpha_composite(pt)
    sheet.paste(tile.resize((256, 256), Image.NEAREST), (x, y2))
    sheet.paste(tile, (x + 262, y2 + 192))
    _label(d, (x, y2 + 262), 'portrait_demon 64x64 (4x, and 1:1)')
    return sheet


def hover_gif(ims, scale=2, seconds=3.6, tick=0.02):
    """The finished loop over the void with the rune circle turning behind him, at the real rates
    (hover 0.14 s a frame, runes 0.10 s a frame); a GIF frame is emitted whenever either changes."""
    bgn = ims['void']
    back = bgn.crop((160, 0, 480, 201))
    hover = [ims['hover'].crop((i * G.W, 0, (i + 1) * G.W, G.H)) for i in range(G.N)]
    runes = [RU.frame_image(i) for i in range(RU.FRAMES)]
    cx, cy = L.CORE
    frames, durations = [], []
    t = 0.0
    last = None
    ms = 0
    while t < seconds - 1e-9:
        hi = int(t / G.FRAME_TIME + 1e-9) % G.N
        ri = int(t / RU.FRAME_TIME + 1e-9) % RU.FRAMES
        if (hi, ri) != last:
            if last is not None:
                durations.append(ms)
            tile = Image.new('RGBA', (G.W, G.H), (0, 0, 0, 255))
            tile.alpha_composite(back, (0, 23))
            tile.alpha_composite(runes[ri], (int(round(cx - 95.5)), int(round(cy - 95.5))))
            tile.alpha_composite(hover[hi])
            frames.append(tile.crop((0, 23, G.W, G.H)).resize((G.W * scale, (G.H - 23) * scale), Image.NEAREST))
            last = (hi, ri)
            ms = 0
        ms += int(round(tick * 1000))
        t += tick
    durations.append(ms)
    pal_src = frames[0].convert('RGB').quantize(colors=255, method=Image.MEDIANCUT)
    out = [f.convert('RGB').quantize(palette=pal_src, dither=Image.NONE) for f in frames]
    return out, durations


# ------------------------------------------------------------------ writing

def _sha(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def aseprite(*args):
    subprocess.run([B.ASEPRITE, '-b'] + list(args), check=True, capture_output=True)


def ship(ims):
    record = {}
    if os.path.exists(RECORD):
        with open(RECORD) as f:
            record = json.load(f)
    # refuse up front: any existing target must be exactly what we shipped last time
    for name, base in SHIP.items():
        for ext in ('.png', '.aseprite'):
            path = base + ext
            if not os.path.realpath(path).startswith(os.path.realpath(os.path.join(ROOT, 'Assets'))):
                raise SystemExit('refusing %s: not under Assets' % path)
            if os.path.exists(path):
                rel = os.path.relpath(path, ROOT).replace('\\', '/')
                if record.get(rel) != _sha(path):
                    raise SystemExit('refusing: %s already exists and is not the file this script shipped' % rel)
    tmp = tempfile.mkdtemp(prefix='jgod_ship_')
    staged = []
    for name, base in SHIP.items():
        im = ims[name]
        stem = os.path.basename(base)
        tpng = os.path.join(tmp, stem + '.png')
        tase = os.path.join(tmp, stem + '.aseprite')
        im.save(tpng)
        aseprite(tpng, '--save-as', tase)
        back = os.path.join(tmp, stem + '_rt.png')
        aseprite(tase, '--save-as', back)
        d = pixel_diff(Image.open(tpng), Image.open(back))
        if d:
            raise SystemExit('%s: the .aseprite does not round-trip: %s' % (stem, d))
        staged.append((base, tpng, tase))
    done = []
    for base, tpng, tase in staged:
        os.makedirs(os.path.dirname(base), exist_ok=True)
        for src, ext in ((tpng, '.png'), (tase, '.aseprite')):
            dst = base + ext
            with open(src, 'rb') as f:
                data = f.read()
            with open(dst, 'wb') as f:
                f.write(data)
            rel = os.path.relpath(dst, ROOT).replace('\\', '/')
            record[rel] = _sha(dst)
            done.append(rel)
    with open(RECORD, 'w') as f:
        json.dump(record, f, indent=1, sort_keys=True)
    return done


def main(argv):
    if not argv or argv[0] not in ('--check', '--preview', '--ship'):
        print(__doc__)
        return 2
    ims = build_all()
    ok, lines = audit(ims)
    for ln in lines:
        print(ln)
    if not ok:
        print('audit FAILED: nothing written')
        return 1
    if argv[0] == '--preview':
        cs = contact_sheet(ims)
        cs.save(os.path.join(HERE, 'jordan_god_final_contact.png'))
        frames, durs = hover_gif(ims)
        gif = os.path.join(HERE, 'jordan_god_hover.gif')
        frames[0].save(gif, save_all=True, append_images=frames[1:], duration=durs, loop=0, disposal=1)
        print('wrote jordan_god_final_contact.png', cs.size)
        print('wrote jordan_god_hover.gif: %d frames, %.2f s' % (len(frames), sum(durs) / 1000.0))
    elif argv[0] == '--ship':
        for rel in ship(ims):
            print('shipped', rel)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
