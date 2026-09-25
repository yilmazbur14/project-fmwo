"""Build, check and ship Bixby's defeat and transformation sheets.

    python export.py            # SAFE: builds every sheet, runs every check, writes previews to the scratchpad
    python export.py --write    # ALSO writes into Assets/Characters/Bixby (each PNG in one save), saves the
                                # .aseprite beside it and round-trips it through Aseprite with imgdiff

Sheets (names, sizes, frame counts and order are the shipped ones; scripts read their timing and anchors):
  bixby_beast_defeat.png         10 x 192x160   frames 0-2 new, 3-9 kept pixel for pixel
  bixby_transform.png            26 x 320x256 in 13x2   0-9 recoloured, 10-25 new
  bixby_transform_aura.png        4 x 320x256   colour-only: its sparks moved onto the same fire ramp
  bixby_transform_shockwave.png   5 x 320x96    unchanged (not written)
"""
import io
import os
import subprocess
import sys
from collections import Counter

import common as C
from imgdiff import pixel_diff
from PIL import Image, ImageDraw

import defeat
import early
import frame
import transform

WRITE = '--write' in sys.argv
OUT = C.SCRATCH
PAL_REDESIGN = set(C.PAL.values())
BIX_COLOURS = C.colours(C.load(C.asset('bixby.png')))
LIAM_COLOURS = C.colours(C.load(os.path.join(C.LIAM, 'liam.png')))

AURA_SRC = os.path.join(C.HERE, 'src', 'bixby_transform_aura_before.png')
SHOCK_SRC = os.path.join(C.HERE, 'src', 'bixby_transform_shockwave_before.png')


def aura_frames():
    """The shipped aura, its four fire colours moved onto the ramp the body frames now use."""
    out = []
    for f in C.cells(C.load(AURA_SRC), C.TW, C.TH):
        g = f.copy()
        px = g.load()
        for y in range(g.height):
            for x in range(g.width):
                c = px[x, y]
                if c[3] and c in early.FIRE:
                    px[x, y] = C.PAL[early.FIRE[c]]
        out.append(g)
    return out


def strip(frames):
    fw, fh = frames[0].size
    out = Image.new('RGBA', (fw * len(frames), fh), C.CLEAR)
    for i, f in enumerate(frames):
        out.paste(f, (i * fw, 0))
    return out


#CHECKS

FAILS = []


def check(ok, what):
    print('  %s %s' % ('ok  ' if ok else 'FAIL', what))
    if not ok:
        FAILS.append(what)


def hover_frame0_lifted():
    """frame.build('up', 0) placed where transformation frame 25 draws it (the hover frame lifted 40)."""
    im = Image.new('RGBA', (C.TW, C.TH), C.CLEAR)
    im.alpha_composite(frame.build('up', 0).image(), (C.BEAST_IN_T[0], C.BEAST_IN_T[1] - C.HOVER_HEIGHT))
    return im


def shipped_hover_is_new():
    hov = C.load(C.asset('bixby_beast.png')).crop((0, 0, C.BEAST_FW, C.BEAST_FH))
    return C.PAL['i'] in C.colours(hov), hov


def run_checks(dfr, tfr, afr):
    print('checks')
    old_d = C.cells(C.load(defeat.SOURCE), C.BEAST_FW, C.BEAST_FH)
    old_t = C.cells(C.load(early.SOURCE), C.TW, C.TH, 13, 2)
    old_a = C.cells(C.load(AURA_SRC), C.TW, C.TH)
    check(len(dfr) == 10 and all(f.size == (192, 160) for f in dfr), 'defeat: 10 frames of 192x160')
    check(all(pixel_diff(dfr[i], old_d[i]) is None for i in defeat.KEEP),
          'defeat: frames %s (smoke, normal Bixby, Liam, LANDING ON 8, hold) pixel-identical to the shipped ones'
          % defeat.KEEP)
    x0, y0, x1, y1 = defeat.DRAWN
    for i in range(3):
        bb = dfr[i].getbbox()
        check(bb[0] >= x0 and bb[1] >= y0 and bb[2] - 1 <= x1 and bb[3] - 1 <= y1,
              'defeat f%d inside BODY_DRAWN (x %d..%d, y %d..%d)' % (i, bb[0], bb[2] - 1, bb[1], bb[3] - 1))
    check(sum(defeat.CLIPPED.values()) == 0, 'defeat: nothing clipped at BODY_DRAWN')
    check(len(tfr) == 26 and all(f.size == (320, 256) for f in tfr), 'transform: 26 frames of 320x256')
    check(all(tfr[i].getchannel('A').tobytes() == old_t[i].getchannel('A').tobytes() for i in range(10)),
          'transform: frames 0-9 keep the shipped silhouettes exactly (colour remap only)')
    d = pixel_diff(tfr[25], hover_frame0_lifted())
    check(d is None, 'transform f25 == approved hover frame 0 (frame.build("up", 0)) lifted 40: %s'
          % (d or 'pixel-identical'))
    new, hov = shipped_hover_is_new()
    if new:
        lifted = Image.new('RGBA', (C.TW, C.TH), C.CLEAR)
        lifted.alpha_composite(hov, (C.BEAST_IN_T[0], C.BEAST_IN_T[1] - C.HOVER_HEIGHT))
        d = pixel_diff(tfr[25], lifted)
        check(d is None, 'transform f25 == shipped bixby_beast.png frame 0 lifted 40: %s' % (d or 'pixel-identical'))
    else:
        print('  note shipped bixby_beast.png is still the old design; f25 matches the approved frame the flight '
              'rig uses as hover frame 0 (rig.HOVER_UP)')
    check(len(afr) == 4 and all(f.getchannel('A').tobytes() == o.getchannel('A').tobytes() for f, o in zip(afr, old_a)),
          'aura: 4 frames, geometry identical to the shipped aura (colour-only)')
    for name, frames in (('defeat', dfr), ('transform', tfr), ('aura', afr)):
        semi = sum(C.measure(f)['semi'] for f in frames)
        check(semi == 0, '%s: no semi-transparent pixels' % name)


#NUMBERS

def numbers(label, im):
    m = C.measure(im)
    print('  %-44s colours %3d  black %5.2f%%  opaque %6d' % (label, m['colours'], m['black'], m['opaque']))
    return m


def report_numbers(dfr, tfr, afr, dsheet, tsheet, asheet):
    print('numbers (target from the redesign: pure #000000 keyline, ~24.6% black, 38-45 colours)')
    numbers('approved redesign sheet', C.load(C.asset('bixby_beast_redesign.png')))
    numbers('defeat sheet (whole)', dsheet)
    numbers('defeat f0-2 together (the beast)', strip(dfr[:3]))
    for i in range(3):
        numbers('  defeat f%d' % i, dfr[i])
    numbers('defeat f3-9 (kept: smoke, Bixby, Liam)', strip(dfr[3:]))
    numbers('transform sheet (whole)', tsheet)
    numbers('transform f0-9 (normal Bixby, recoloured)', strip(tfr[:10]))
    numbers('transform f10-20 (energy silhouettes, fx)', strip(tfr[10:21]))
    numbers('transform f21-25 (the beast)', strip(tfr[21:]))
    for i in range(21, 26):
        numbers('  transform f%d' % i, tfr[i])
    numbers('aura sheet', asheet)
    beast = C.colours(strip(dfr[:3])) | C.colours(strip(tfr[21:]))
    extra = beast - PAL_REDESIGN
    print('  colours in the beast frames outside the redesign palette: %d  %s' % (len(extra), sorted(extra)))
    kept = C.colours(strip(dfr[3:]))
    print('  defeat colours from normal Bixby / Liam / old fx: %d of %d' % (len(kept - C.colours(strip(dfr[:3]))),
                                                                          C.measure(dsheet)['colours']))


#PREVIEWS

BG = (46, 49, 58, 255)


def contact(frames, times, cols, s, name, labels=None):
    fw, fh = frames[0].size
    gap, lab = 6, 14
    rows = (len(frames) + cols - 1) // cols
    out = Image.new('RGBA', (cols * (fw * s + gap), rows * (fh * s + gap + lab)), (18, 17, 22, 255))
    d = ImageDraw.Draw(out)
    for i, f in enumerate(frames):
        x, y = (i % cols) * (fw * s + gap), (i // cols) * (fh * s + gap + lab)
        out.alpha_composite(C.up(C.on_bg(f, BG), s), (x, y + lab))
        t = '%d' % i + ('  %.2fs' % times[i] if times else '') + ('  ' + labels[i] if labels and labels[i] else '')
        d.text((x + 2, y + 1), t, fill=(255, 230, 120, 255))
    out.save(OUT + name)
    return OUT + name


def gif(frames, durations_s, s, name, bg=BG, loop=0):
    """A 2x GIF on a dark background with exact per-frame durations and one shared palette (no dither)."""
    ims = [C.up(C.on_bg(f, bg), s).convert('RGB') for f in frames]
    seen = set()
    for im in ims:
        flat = getattr(im, 'get_flattened_data', None)
        seen.update(flat() if flat else im.getdata())
    palette = sorted(seen)
    assert len(palette) <= 256, len(palette)
    pal_im = Image.new('P', (1, 1))
    flat = [v for c in palette for v in c] + [0] * (3 * (256 - len(palette)))
    pal_im.putpalette(flat)
    ps = [im.quantize(palette=pal_im, dither=Image.Dither.NONE) for im in ims]
    ms = [int(round(t * 1000)) for t in durations_s]
    ps[0].save(OUT + name, save_all=True, append_images=ps[1:], duration=ms, loop=loop, disposal=1, optimize=False)
    return OUT + name


def ingame_transform(tfr, afr, shock):
    """The transformation as BixbyBeastIntro plays it: the body frames on their times, the aura behind
    him from frame 3 (0.09 s a frame, cut at the end of frame 18 where the game fades it), and the ground
    ring behind both at frames 7 and 20 (0.06 s a frame), on one timeline quantised to 20 ms."""
    T = C.TRANSFORM_TIMES
    starts = [sum(T[:i]) for i in range(len(T))]
    end = sum(T)
    aura_on, aura_off = starts[3], starts[19]
    events = set(round(t, 3) for t in starts)
    t = aura_on
    while t < aura_off:
        events.add(round(t, 3))
        t += C.AURA_FRAME_TIME
    for s0 in (starts[7], starts[20]):
        for k in range(6):
            events.add(round(s0 + k * C.SHOCKWAVE_FRAME_TIME, 3))
    q = sorted(set(round(e / 0.02) * 0.02 for e in events if e < end))
    H = 256 + 48          # room below the frame for the lower half of the floor ring
    frames, durs = [], []
    for j, t0 in enumerate(q):
        t1 = q[j + 1] if j + 1 < len(q) else end
        bi = max(i for i in range(len(T)) if starts[i] <= t0 + 1e-6)
        im = Image.new('RGBA', (C.TW, H), C.CLEAR)
        for s0 in (starts[7], starts[20]):
            k = int((t0 - s0 + 1e-6) / C.SHOCKWAVE_FRAME_TIME)
            if 0 <= k < 5:
                im.alpha_composite(shock[k], (0, C.T_ANCHOR[1] - 48))
        if aura_on - 1e-6 <= t0 < aura_off:
            k = int((t0 - aura_on + 1e-6) / C.AURA_FRAME_TIME) % 4
            im.alpha_composite(afr[k], (0, 0))
        im.alpha_composite(tfr[bi], (0, 0))
        frames.append(im)
        durs.append(max(0.02, t1 - t0))
    return frames, durs


def previews(dfr, tfr, afr, shock):
    os.makedirs(OUT, exist_ok=True)
    dl = ['blow', 'collapse', 'glow dies', 'kept', 'kept', 'kept', 'kept', 'kept', 'LANDS', 'kept']
    made = [contact(dfr, C.DEFEAT_TIMES, 5, 2, 'defeat_contact_2x.png', dl)]
    made.append(contact(tfr, C.TRANSFORM_TIMES, 7, 1, 'transform_contact_1x.png'))
    made.append(contact(afr, [C.AURA_FRAME_TIME] * 4, 4, 1, 'aura_contact_1x.png'))
    made.append(contact(shock, [C.SHOCKWAVE_FRAME_TIME] * 5, 1, 2, 'shockwave_contact_2x.png'))
    made.append(gif(dfr, C.DEFEAT_TIMES, 2, 'defeat_2x.gif'))
    made.append(gif(tfr, C.TRANSFORM_TIMES, 2, 'transform_2x.gif'))
    made.append(gif(afr, [C.AURA_FRAME_TIME] * 4, 2, 'aura_2x.gif'))
    made.append(gif(shock, [C.SHOCKWAVE_FRAME_TIME] * 5, 2, 'shockwave_2x.gif'))
    fr, durs = ingame_transform(tfr, afr, shock)
    made.append(gif(fr, durs, 2, 'transform_ingame_2x.gif'))
    # before / after of the changed frames
    old_d = C.cells(C.load(defeat.SOURCE), C.BEAST_FW, C.BEAST_FH)
    made.append(contact(old_d[:3] + dfr[:3], None, 3, 2, 'defeat_before_after_2x.png',
                        ['before 0', 'before 1', 'before 2', 'after 0', 'after 1', 'after 2']))
    old_t = C.cells(C.load(early.SOURCE), C.TW, C.TH, 13, 2)
    idx = [9, 12, 15, 17, 19, 20, 22, 25]
    made.append(contact([old_t[i] for i in idx] + [tfr[i] for i in idx], None, 8, 1, 'transform_before_after_1x.png',
                        ['before %d' % i for i in idx] + ['after %d' % i for i in idx]))
    for m in made:
        print('  preview', m)


#WRITING

def write_png(im, path):
    """Encode fully in memory, then write the file in one go (the editor is open and re-imports on change)."""
    buf = io.BytesIO()
    im.save(buf, format='PNG')
    with open(path, 'wb') as fh:
        fh.write(buf.getvalue())


def ship(name, im):
    png = C.asset(name + '.png')
    ase = C.asset(name + '.aseprite')
    write_png(im, png)
    subprocess.run([C.ASEPRITE, '-b', png, '--save-as', ase], check=True, capture_output=True)
    back = os.path.join(C.WORK, name + '_roundtrip.png')
    subprocess.run([C.ASEPRITE, '-b', ase, '--save-as', back], check=True, capture_output=True)
    shipped = Image.open(png)
    shipped.load()
    d1 = pixel_diff(shipped, im)
    d2 = pixel_diff(shipped, Image.open(back))
    print('  wrote %s  (re-read vs built: %s; .aseprite round trip: %s)' % (png, d1 or 'pixel-exact', d2 or 'pixel-exact'))
    return d1 is None and d2 is None


if __name__ == '__main__':
    import pose
    assert pose.regress(), 'the posable build no longer reproduces the approved frame'
    dfr = defeat.frames()
    tfr = transform.frames()
    afr = aura_frames()
    shock = C.cells(C.load(SHOCK_SRC), C.TW, 96)
    dsheet = strip(dfr)
    tsheet = transform.sheet(tfr)
    asheet = strip(afr)
    check(dsheet.size == (1920, 160), 'defeat sheet 1920x160')
    check(tsheet.size == (4160, 512), 'transform sheet 4160x512 (13 x 2)')
    check(asheet.size == (1280, 256), 'aura sheet 1280x256')
    run_checks(dfr, tfr, afr)
    report_numbers(dfr, tfr, afr, dsheet, tsheet, asheet)
    previews(dfr, tfr, afr, shock)
    if FAILS:
        print('NOT WRITING: %d check(s) failed' % len(FAILS))
        sys.exit(1)
    if WRITE:
        ok = all([ship('bixby_beast_defeat', dsheet), ship('bixby_transform', tsheet),
                  ship('bixby_transform_aura', asheet)])
        print('shipped' if ok else 'ROUND TRIP FAILED')
        sys.exit(0 if ok else 1)
    print('dry run: nothing written to Assets (pass --write to ship)')
