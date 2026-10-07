"""Sheets: frame specs -> checked 96x96 frames -> strip PNG + .aseprite + previews + GIF, all inside the
rider scratch folder (every path goes through jr_common.guard_out). Never writes into Assets.

A sheet module gives NAME, TIMES, LOOP, KIND ('ride' or 'mat'), OFFSET (build -> frame), and
frames(): a list of Frame objects (each a jr_fig.Fig plus anchor rules).
"""
import json
import os
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jr_common as C  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

JB = C.JB
W = H = 96

# Black-ratio references (pure #000 share of opaque pixels), measured 2026-10-04:
#   the approved rider (approval/kaiju_*.aseprite, layer 'rider'): 28.96% -> ride sheets aim here
#   Jordan's live sheets (idle f0 30.67%, the set 30.7-31.9%): mat / standing sheets aim here
REF = {'ride': 0.2896, 'mat': 0.3067}
TOL = 0.015


class Frame:
    """One frame: px / fx in FRAME coordinates, plus its anchors and flags."""

    def __init__(self, px, fx, anchors, on_mat=False, note=''):
        self.px, self.fx, self.anchors, self.on_mat, self.note = px, set(fx), anchors, on_mat, note
        self.allow_gaps = set()         # documented exceptions (the approved rider's own heel pixel)


def to_frame(fig, offset, anchors_build, on_mat=False, note=''):
    """A jr_fig.Fig in build coordinates -> Frame (pixels moved by `offset`, clipped to 96x96; the
    clip must not cut anything, checked here). anchors_build: {name: (x, y) | [x0, y0, x1, y1]}."""
    ox, oy = offset
    px = {}
    for (x, y), k in fig.px.items():
        q = (x + ox, y + oy)
        if not (0 <= q[0] < W and 0 <= q[1] < H):
            raise SystemExit('pixel %s falls outside the frame at %s' % ((x, y), q))
        px[q] = k
    fx = {(x + ox, y + oy) for (x, y) in fig.fx if (x, y) in fig.px}
    anchors = {}
    boxpx = set(getattr(fig, 'pts', {}).get('box', {}) or {})
    body = [q for q in fig.px if q not in fig.fx and q not in boxpx]
    bx0, by0, bx1, by1 = C.bbox(body)
    anchors['BODY_BOX'] = [bx0 + ox, by0 + oy, bx1 - bx0 + 1, by1 - by0 + 1]     # his body, not the box or effects
    if boxpx:
        x0_, y0_, x1_, y1_ = C.bbox(boxpx)
        anchors['BOX'] = [(x0_ + x1_) // 2 + ox, (y0_ + y1_) // 2 + oy]
    for n, v in anchors_build.items():
        if v is None:
            continue
        if len(v) == 2:
            anchors[n] = [v[0] + ox, v[1] + oy]
        else:
            anchors[n] = [v[0] + ox, v[1] + oy, v[2] + ox, v[3] + oy]
    return Frame(px, fx, anchors, on_mat, note)


def fill_holes(px):
    """A single transparent pixel boxed in by keylines on four sides is a pinhole: ink it."""
    for q in JB.audit(px)['holes']:
        px[q] = 'k'
    return px


def crown(px, part):
    """CROWN: the top of his hair, as (x, y): the middle column of the head part's topmost row."""
    ys = [y for (x, y) in part]
    top = min(ys)
    xs = sorted(x for (x, y) in part if y == top)
    return (xs[len(xs) // 2], top)


def body_box(px, fx, exclude=()):
    """BODY_BOX: [x, y, w, h] round every non-effect pixel (and not the `exclude` pixels, e.g. the box)."""
    pts = [q for q in px if q not in fx and q not in exclude]
    x0, y0, x1, y1 = C.bbox(pts)
    return [x0, y0, x1 - x0 + 1, y1 - y0 + 1]


def check_frame(fr, kind, allowed_cols):
    im = C.render(fr.px)
    st = C.stats(im)
    cols = {c for c in C.flat(im) if c[3]}
    a = JB.audit(fr.px, fr.fx)
    probs = []
    if cols - allowed_cols:
        probs.append('colours outside the approved 40: %s' % sorted(cols - allowed_cols)[:4])
    if any(c[:3] == (0, 0, 0) and c != (0, 0, 0, 255) for c in cols):
        probs.append('impure black')
    if st['semi']:
        probs.append('%d semi-alpha' % st['semi'])
    a['gaps'] = [g for g in a['gaps'] if (g[0], g[1]) not in fr.allow_gaps]
    for key in ('gaps', 'lone', 'holes', 'keys'):
        if a[key]:
            probs.append('%s %s' % (key, a[key][:6]))
    xs = [x for (x, y) in fr.px]
    ys = [y for (x, y) in fr.px]
    edge = [q for q in fr.px if q[0] in (0, W - 1) or q[1] == 0 or (q[1] == H - 1 and not fr.on_mat)]
    if edge:
        probs.append('frame-edge pixels %s' % edge[:6])
    if fr.on_mat and max(ys) != H - 1:
        probs.append('on the mat but the lowest row is %d' % max(ys))
    ref = REF[kind]
    if abs(st['black'] - ref) > TOL + 1e-9:
        probs.append('black %.2f%% outside %.1f +- 1.5' % (100 * st['black'], 100 * ref))
    num = {'opaque': st['opaque'], 'colours': len(cols), 'black': round(st['black'], 4),
           'black_vs_ref_pts': round(100 * (st['black'] - ref), 2), 'semi': st['semi'],
           'audit': {k: len(a[k]) for k in ('gaps', 'lone', 'holes', 'keys')},
           'edge_px': len(edge), 'bbox': [min(xs), min(ys), max(xs), max(ys)]}
    if fr.allow_gaps:
        num['allowed_gaps'] = sorted(fr.allow_gaps)
    return num, probs


def strip(frames):
    out = Image.new('RGBA', (W * len(frames), H), (0, 0, 0, 0))
    for i, fr in enumerate(frames):
        out.alpha_composite(C.render(fr.px), (W * i, 0))
    return out


def aseprite_roundtrip(png, ase):
    subprocess.run([C.ASEPRITE, '-b', png, '--save-as', ase], check=True, capture_output=True)
    tmp = tempfile.mkdtemp(prefix='jr_rt_')
    back = os.path.join(tmp, 'rt.png')
    subprocess.run([C.ASEPRITE, '-b', ase, '--save-as', back], check=True, capture_output=True)
    return C.pixel_diff(Image.open(png).convert('RGBA'), Image.open(back).convert('RGBA'))


def gif(frames, times, path, scale=3, bg=C.MAT):
    ims = []
    for fr in frames:
        base = Image.new('RGBA', (W, H), bg)
        base.alpha_composite(C.render(fr.px))
        ims.append(base.resize((W * scale, H * scale), Image.NEAREST).convert('P', palette=Image.ADAPTIVE, colors=255))
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=[int(round(t * 1000)) for t in times],
                loop=0, disposal=2)


def preview(frames, path, scale=3, anchors=True):
    """3x strip on the mat colour, with the anchors marked under it on a second copy."""
    im = strip(frames)
    top = C.up(im, scale, C.MAT)
    if not anchors:
        top.save(path)
        return
    bot = C.up(im, scale, C.BG)
    d = ImageDraw.Draw(bot)
    cols = {'SEAT': (255, 140, 0), 'CROWN': (255, 255, 0), 'HAND': (255, 0, 0), 'SOLES': (0, 255, 255),
            'TOY': (255, 0, 255), 'PIVOT': (255, 255, 255), 'BOX': (0, 200, 0)}
    for i, fr in enumerate(frames):
        for n, v in fr.anchors.items():
            if n == 'BODY_BOX':
                x, y, w, h = v
                d.rectangle([(W * i + x) * scale, y * scale, (W * i + x + w) * scale - 1, (y + h) * scale - 1],
                            outline=(120, 200, 255))
            elif n in cols:
                x, y = v
                cx, cy = (W * i + x) * scale + scale // 2, y * scale + scale // 2
                d.rectangle([cx - 3, cy - 3, cx + 3, cy + 3], outline=cols[n])
        d.rectangle([W * i * scale, 0, W * (i + 1) * scale - 1, H * scale - 1], outline=(70, 70, 90))
    out = Image.new('RGBA', (top.width, top.height * 2 + 4), (10, 10, 12, 255))
    out.paste(top, (0, 0))
    out.paste(bot, (0, top.height + 4))
    out.save(path)


def build_sheet(mod, out_dir, write=True):
    """Check every frame of a sheet module; write PNG + .aseprite + 3x preview + GIF into out_dir.
    Returns the sheet's contract entry and its problems."""
    allowed = C.approved_colours()
    assert len(allowed) == 40
    frames = mod.frames()
    if len(frames) != len(mod.TIMES):
        raise SystemExit('%s: %d frames, %d times' % (mod.NAME, len(frames), len(mod.TIMES)))
    nums, probs = [], []
    for i, fr in enumerate(frames):
        n, p = check_frame(fr, mod.KIND, allowed)
        nums.append(n)
        probs += ['%s f%d: %s' % (mod.NAME, i, x) for x in p]
    entry = {'file': mod.NAME + '.png', 'aseprite': mod.NAME + '.aseprite', 'frame': [W, H],
             'frames': len(frames), 'hframes': len(frames), 'vframes': 1, 'times': mod.TIMES,
             'loop': mod.LOOP, 'kind': mod.KIND, 'black_ref': REF[mod.KIND],
             'build_to_frame_offset': list(mod.OFFSET), 'note': mod.NOTE,
             'per_frame': [dict(anchors=fr.anchors, numbers=n, note=fr.note) for fr, n in zip(frames, nums)]}
    im = strip(frames)
    sheet = C.stats(im)
    entry['sheet_numbers'] = {'black': round(sheet['black'], 4), 'colours': sheet['colours']}
    if write:
        os.makedirs(C.guard_out(out_dir), exist_ok=True)
        png = C.guard_out(os.path.join(out_dir, mod.NAME + '.png'))
        ase = C.guard_out(os.path.join(out_dir, mod.NAME + '.aseprite'))
        im.save(png)
        rt = aseprite_roundtrip(png, ase)
        entry['aseprite_roundtrip'] = rt or 'identical'
        if rt:
            probs.append('%s: .aseprite round trip %s' % (mod.NAME, rt))
        preview(frames, C.guard_out(os.path.join(out_dir, mod.NAME + '_3x.png')))
        gdir = C.guard_out(os.path.join(out_dir, 'gifs'))
        os.makedirs(gdir, exist_ok=True)
        gif(frames, mod.TIMES if all(t for t in mod.TIMES) else [0.12] * len(frames),
            C.guard_out(os.path.join(gdir, mod.NAME + '.gif')))
    return entry, probs, frames
