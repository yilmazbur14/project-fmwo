"""Jordan's puppets, STEP 2: ship the four puppets the attacks use, take B ("Rune"), and generate their
back-hook table. The user approved take B on 2026-09-28 ("blue, strings on back only").

A bare run writes nothing:

    python jp_ship.py                     # print this and exit
    python jp_ship.py --check DIR         # build every sheet into scratch folder DIR, audit, write the
                                          # contact sheets and the hooks table there (never into Assets)
    python jp_ship.py --ship DIR          # the same build and audit into DIR, then copy the files into
                                          # Assets/Characters/Jordan/Puppets/<key>/ and
                                          # Scripts/JordanPuppetHooks.gd with EXCLUSIVE CREATE: any file
                                          # that already exists stops the ship before anything is written
    python jp_ship.py --add DIR           # after a ship: build and audit everything, check every shipped
                                          # file rebuilds byte-identical, exclusive-create only the sheets
                                          # not shipped yet, regenerate the hooks table in place (every
                                          # shipped line unchanged) and add the new hashes to shipped.json

What ships (the twin rule: every puppet sheet is its source's size, frame grid, anchors and silhouette,
pure-black keylines, no semi-alpha, every colour mapped):
  res://Assets/Characters/Jordan/Puppets/<key>/<source file name>   .png + .aseprite beside it
  res://Scripts/JordanPuppetHooks.gd                                 const BACK, generated

The keys are exactly greyson, matt, burak and danny (Danny is the SUMO: his fight's sheets); ship 2
(09-28) adds eric, mason, josh and carter (and Carter's two Raging Demon clone sheets, effects
recoloured by table with their authored alpha: FX). The hooks table also carries OVER: the back-view
frames of every sheet, where the ring is drawn on his back and the strings tie on over the sprite.
A record of every shipped file's sha256 goes to art_source/jordan_puppets/shipped.json.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jp_bosses as B  # noqa: E402
import jp_core as C  # noqa: E402
import jp_present as PR  # noqa: E402
import jp_palette as PAL  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402
from PIL import Image  # noqa: E402

TAKE = 'B'
# key -> (recipe boss, [(source sheet under Assets/Characters, frame width)])
SHIP = {
    'greyson': ('greyson', [(s, 192 if s.endswith('juggle.png') else 112) for s in (
        'Greyson/greyson_idle.png', 'Greyson/greyson_pose_a.png', 'Greyson/greyson_pose_b.png',
        'Greyson/greyson_pose_c.png', 'Greyson/greyson_pose_hit.png', 'Greyson/greyson_spirit.png',
        'Greyson/greyson_hit.png', 'Greyson/greyson_juggle.png',
        # step 2b (09-28): the hang (limp = hit) and the crumble (crumple = defeat)
        'Greyson/greyson_defeat.png')]),
    'matt': ('matt', [(s, 96) for s in (
        'Matt/matt_idle.png', 'Matt/matt_yell_tell.png', 'Matt/matt_roar.png',
        'Matt/matt_hit.png', 'Matt/matt_defeat.png')]),
    'burak': ('captain_burak', [(s, 192 if s.endswith('juggle.png') else 96) for s in (
        'BurakBoss/burak_idle.png', 'BurakBoss/burak_throw.png', 'BurakBoss/burak_fire.png',
        'BurakBoss/burak_broken.png', 'BurakBoss/burak_hit.png', 'BurakBoss/burak_boss_juggle.png',
        'BurakBoss/burak_defeat.png')]),
    'danny': ('danny_sumo', [(s, 176) for s in (
        'Danny/Sumo/danny_sumo_idle.png', 'Danny/Sumo/danny_sumo_jump.png', 'Danny/Sumo/danny_sumo_air.png',
        'Danny/Sumo/danny_sumo_slam.png',
        'Danny/Sumo/danny_sumo_hit.png', 'Danny/Sumo/danny_sumo_defeat.png')]),
    # ship 2 (09-28, the user approved the concept art and its defaults): the other four, every body
    # sheet of theirs a puppet would play, and Carter's two clone sheets (effects: no strings, no hooks)
    'eric': ('eric', [(s, 256) for s in (
        'Eric/eric_entrance.png', 'Eric/eric_sheet_v2.png', 'Eric/eric_bearhug_v2.png', 'Eric/eric_winded.png',
        'Eric/eric_broken.png', 'Eric/eric_juggle.png')]),
    'mason': ('mason', [('Mason/mason_sheet.png', 64), ('Mason/mason_juggle.png', 128)]),
    'josh': ('josh', [(s, 160 if s.endswith('juggle.png') else 80) for s in (
        'Josh/josh_idle.png', 'Josh/josh_throw.png', 'Josh/josh_glide.png', 'Josh/josh_intro.png',
        'Josh/josh_mount.png', 'Josh/josh_dismount.png', 'Josh/josh_recovery.png', 'Josh/josh_hit.png',
        'Josh/josh_defeat.png', 'Josh/josh_juggle.png')]),
    # (carter_juggle: twelve 192x144 frames, CarterArtLayout.FINAL_JUGGLE; first shipped sliced at 144, fixed)
    'carter': ('carter', [(s, 192 if s.endswith('juggle.png') else 96) for s in (
        'Carter/carter_idle.png', 'Carter/carter_eye_flash.png', 'Carter/carter_rush.png',
        'Carter/carter_rush_pass.png', 'Carter/carter_messatsu_charge.png', 'Carter/carter_messatsu_fire.png',
        'Carter/carter_intro.png', 'Carter/carter_spent.png', 'Carter/carter_hit.png', 'Carter/carter_defeat.png',
        'Carter/carter_juggle.png')] + [('Carter/Demon/demon_clone.png', 48), ('Carter/Demon/demon_clone_ghost.png', 96)]),
}
# Effect sheets shipped beside a puppet: recoloured by the boss's table alone (plus their own overrides),
# their authored alpha kept exactly; not puppets, so no hooks and no rings.
FX = {
    'Carter/Demon/demon_clone.png': B.CARTER_CLONE_EYES,
    'Carter/Demon/demon_clone_ghost.png': B.CARTER_CLONE_EYES,
}
# Sheets DERIVED from a shipped twin rather than treated from a source sheet: key -> [(sheet name,
# builder)]. A builder returns (sheet image, BACK points per frame, problems). Each one was approved
# as an image, so its rebuild must be byte-identical to the approved file (APPROVED, sha256).
def _portal_charge():
    """Eric's sword-less bear-hug charge for Jordan's attack 3 (approved 09-28): eric_bearhug_v2 f1-2
    without the planted sword, the aura carried on behind it (portal_charge/jp_portal_charge.py)."""
    d = os.path.join(HERE, 'portal_charge')
    if d not in sys.path:
        sys.path.insert(0, d)
    import jp_portal_charge as PCH  # noqa: E402
    PCH.load()
    sheet, _frames, _mask, info, problems = PCH.build()
    return sheet, [tuple(p) for p in info['back']], problems


DERIVED = {'eric': [('eric_portal_charge', _portal_charge)]}
APPROVED = {
    'eric/eric_portal_charge.png': '3deda88cc1ca6e66896c512aadcb94c407631f8462995e84a3dc92786017cff8',
    'eric/eric_portal_charge.aseprite': '4a60341021c71335cc9ba17789857619249c7af95f14be2eda40406c046cc6af',
}
# The anims of the sheets that hold more than one, as their scenes play them (EricScene.tscn and
# MasonScene.tscn animation tracks; the finale's eric_entrance: the walk-in, then frame 3 held as his
# idle, the approved look). A ring is kept on a frame only if the tracker finds it on EVERY frame of
# its anim - the all-or-nothing rule, per anim; a sheet not listed here is one anim.
ANIMS = {
    'Eric/eric_entrance.png': {'walk': [0, 1, 2], 'idle': [3]},
    'Eric/eric_sheet_v2.png': {
        'earthquake': range(0, 11), 'recover': [11, 12], 'whirlwind': range(13, 21), 'idle': range(21, 27),
        'downed': range(27, 32), 'throw_windup': [32, 33], 'throw_release': [34, 35], 'empty_wait': [36, 37],
        'recall_reach': [38], 'recall_catch': [39]},
    'Eric/eric_bearhug_v2.png': {
        'hug_plant': [0], 'hug_charge': [1, 2], 'hug_lunge': [3, 4], 'hug_whiff': [5], 'hug_stumble': [6],
        'hug_grab': [7], 'hug_squeeze': [8, 9, 10], 'hug_toss': [11], 'hug_toss_end': [12], 'hug_retrieve': [13, 14]},
    'Eric/eric_broken.png': {'broken_final': range(0, 5), 'broken_final_loop': [5, 6, 7]},
    'Eric/eric_juggle.png': {'juggle_hit_final': [0, 1], 'juggle_tumble_final': [2, 3, 4, 5],
                             'juggle_crash_final': [6, 7, 8, 9]},
    'Mason/mason_sheet.png': {
        'idle': [0, 1], 'waddle': [2, 3, 4, 5], 'poop': [6, 7], 'eat': [8, 9], 'phone': [10, 11], 'hit': [12],
        'defeated': [13, 14], 'nugget_toss': [15, 16, 17], 'nugget_hold': [18]},
    'Mason/mason_juggle.png': {'juggle_hit_final': [0, 1], 'juggle_tumble_final': [2, 3, 4, 5, 6],
                               'juggle_crash_final': [7, 8, 9], 'juggle_down_final': [10, 11]},
}
DEST = os.path.join(C.ROOT, 'Assets', 'Characters', 'Jordan', 'Puppets')
HOOKS_GD = os.path.join(C.ROOT, 'Scripts', 'JordanPuppetHooks.gd')
RECORD = os.path.join(HERE, 'shipped.json')
AUDITED = ('gaps', 'lone', 'holes', 'bad_keys', 'silhouette', 'edge_black_lost')


def _under(path, root):
    p, r = os.path.normcase(os.path.realpath(path)), os.path.normcase(os.path.realpath(root))
    return p == r or p.startswith(r + os.sep)


def build_sheet(boss, rel, fw):
    """The whole sheet treated frame by frame; returns (sheet image, per-frame info, problems)."""
    src_sheet = C.sheet(rel)
    fh = src_sheet.shape[0]
    n = C.frames_in(rel, fw)
    out = Image.new('RGBA', (src_sheet.shape[1], fh), (0, 0, 0, 0))
    infos, problems = [], []
    if rel in FX:
        return build_fx_sheet(boss, rel, fw)
    key = boss.key_frame()
    # pass 1: which rings can be drawn on EVERY frame of each anim of this sheet (ANIMS; a sheet not
    # listed is one anim). A ring the tracker finds on only some frames of an anim would pop in and out
    # as it plays, so it is left off that anim (its point is still recorded). A frame in more than one
    # anim keeps only what all of them keep. The back ring is not weighed: it is drawn by hand, on the
    # back views only, where the strings tie on over the sprite.
    found = []
    for f in range(n):
        info = C.treat(boss, C.frame(rel, fw, fh, f), TAKE, key_src=key, sheet_rel=rel, frame_no=f)[1]
        found.append({r for r in info.get('rings_drawn', []) if r != 'back'})
    anims = [list(fr) for fr in (ANIMS.get(rel) or {'all': range(n)}).values()]
    for f in range(n):
        if not any(f in fr for fr in anims):
            raise SystemExit('%s: frame %d is in none of its anims' % (rel, f))
    for f in range(n):
        src = C.frame(rel, fw, fh, f)
        keep = set(found[f])
        for fr in anims:
            if f in fr:
                keep &= set.intersection(*[found[g] for g in fr])
        skip = found[f] - keep
        im, info = C.treat(boss, src, TAKE, key_src=key, sheet_rel=rel, frame_no=f, skip_rings=skip)
        info['rings_left_off_sheet'] = sorted(skip)
        out.alpha_composite(im, (f * fw, 0))
        infos.append(info)
        for kind in AUDITED:
            if info['lint'][kind]:
                problems.append('%s f%d: %d %s %s' % (rel, f, len(info['lint'][kind]), kind, info['lint'][kind][:4]))
        for c in info.get('clipped', []):
            problems.append('%s f%d: %s' % (rel, f, c))
        if info['unknown']:
            problems.append('%s f%d: unmapped colours %s' % (rel, f, info['unknown']))
    # whole-sheet checks: size, silhouette, semi-alpha, palette
    src_img = Image.fromarray(src_sheet, 'RGBA')
    if out.size != src_img.size:
        problems.append('%s: sheet size %s vs %s' % (rel, out.size, src_img.size))
    a = C.np.array(out)
    if ((a[:, :, 3] > 0) & (a[:, :, 3] < 255)).any():
        problems.append('%s: semi-alpha' % rel)
    if ((a[:, :, 3] > 0) != (src_sheet[:, :, 3] > 0)).any():
        problems.append('%s: silhouette differs from the source' % rel)
    problems += palette_problems(rel, a, src_sheet, fw, infos)
    return out, infos, problems


def palette_problems(rel, a, src_sheet, fw, infos):
    """Every visible pixel is a take-B palette colour, but a keep region's, which is its source pixel."""
    pal = {tuple(v[:3]) for v in PAL.colours(TAKE).values()}
    op = a[:, :, 3] > 0
    rgb = a[:, :, :3].reshape(-1, 3)
    flat_op = op.reshape(-1)
    as_int = (rgb[:, 0].astype(C.np.int64) << 16) | (rgb[:, 1].astype(C.np.int64) << 8) | rgb[:, 2]
    pal_int = C.np.array(sorted((r << 16) | (g << 8) | b for r, g, b in pal), C.np.int64)
    off = flat_op & ~C.np.isin(as_int, pal_int)
    if not off.any():
        return []
    ys, xs = C.np.nonzero(off.reshape(op.shape))
    bad = [(int(x), int(y)) for x, y in zip(xs, ys) if not (a[y, x] == src_sheet[y, x]).all()
           or not infos[x // fw].get('kept')]
    return ['%s: %d pixel(s) off the palette, e.g. %s' % (rel, len(bad), bad[:4])] if bad else []


def build_fx_sheet(boss, rel, fw):
    """An effect sheet: every frame recoloured by the boss's table (plus the sheet's own overrides) and
    nothing else - no tracking, no overlays, no keyline pass - its alpha kept exactly as authored."""
    src_sheet = C.sheet(rel)
    fh = src_sheet.shape[0]
    n = C.frames_in(rel, fw)
    table = dict(boss.table)
    table.update(C.table(FX[rel]))
    out = Image.new('RGBA', (src_sheet.shape[1], fh), (0, 0, 0, 0))
    infos, problems = [], []
    for f in range(n):
        src = C.frame(rel, fw, fh, f)
        wk, unknown = C.recolour(src, table)
        a = C.np.array(wk.image(TAKE))
        a[:, :, 3] = C.np.where(a[:, :, 3] > 0, src[:, :, 3], 0)
        out.alpha_composite(Image.fromarray(a, 'RGBA'), (f * fw, 0))
        infos.append({'fx': True, 'hooks': {}, 'skipped': [], 'unknown': unknown})
        if unknown:
            problems.append('%s f%d: unmapped colours %s' % (rel, f, unknown))
    a = C.np.array(out)
    if out.size != (src_sheet.shape[1], fh):
        problems.append('%s: sheet size %s' % (rel, out.size))
    if (a[:, :, 3] != src_sheet[:, :, 3]).any():
        problems.append('%s: alpha differs from the source' % rel)
    pal = {tuple(v[:3]) for v in PAL.colours(TAKE).values()}
    cols = {tuple(c) for c in a[a[:, :, 3] > 0][:, :3].tolist()}
    if cols - pal:
        problems.append('%s: %d colour(s) off the palette' % (rel, len(cols - pal)))
    return out, infos, problems


def gd_value(p):
    return 'null' if p is None else 'Vector2(%d, %d)' % (p[0], p[1])


def hooks_gd(back, over=None):
    lines = ['extends RefCounted',
             '# Generated by art_source/jordan_puppets/jp_ship.py - do not edit by hand; re-run it instead.',
             '#',
             "# BACK: where each puppet's string ties on, between the shoulder blades, for every frame of every",
             '# puppet sheet (res://Assets/Characters/Jordan/Puppets/<key>/<sheet>.png): texels on that frame,',
             '# (0, 0) its top-left, on the UNFLIPPED sheet (mirror x as frame_width - 1 - x when flipped).',
             '# On front views the point is behind the body: draw the string UNDER the sprite. On Greyson\'s',
             '# back views (greyson_pose_a, greyson_pose_c) his back faces the camera and the ring is drawn',
             '# there. null: not placed on that frame (the tumbling juggle frames): use the fallback.',
             '',
             'const BACK := {']
    for key in SHIP:
        lines.append('\t&"%s": {' % key)
        for sheet, pts in back[key].items():
            lines.append('\t\t&"%s": [%s],' % (sheet, ', '.join(gd_value(p) for p in pts)))
        lines.append('\t},')
    lines.append('}')
    if over:
        lines += ['',
                  '# OVER: the back views. For each sheet (named as in BACK: its file name with no extension), the',
                  '# frames where his back faces the camera: the ring is drawn on his back there, at the BACK point,',
                  '# and the strings tie on OVER the sprite. On every other frame they run in under it.',
                  'const OVER := {']
        for sheet, frames in over.items():
            lines.append('\t"%s": [%s],' % (sheet, ', '.join(str(f) for f in frames)))
        lines.append('}')
    return '\n'.join(lines) + '\n'


def aseprite(*args):
    subprocess.run([C.ASEPRITE, '-b'] + list(args), check=True, capture_output=True)


def build_all(out_dir):
    """Build every sheet into out_dir/<key>/, with its .aseprite (round-tripped), plus the hooks table and
    one contact sheet per key. Returns (files {relative path under out_dir: sha256}, back table, report)."""
    if _under(out_dir, os.path.join(C.ROOT, 'Assets')) or (_under(out_dir, C.ROOT) and not _under(out_dir, HERE)):
        raise SystemExit('refusing: %s must be a scratch folder outside the project (or under art_source/jordan_puppets)' % out_dir)
    os.makedirs(out_dir, exist_ok=True)
    files, back, report, ok = {}, {}, [], True
    over = {}
    tmp = tempfile.mkdtemp(prefix='jpship_')
    try:
        for key, (bname, sheets) in SHIP.items():
            boss = B.BOSSES[bname]
            d = os.path.join(out_dir, key)
            os.makedirs(d, exist_ok=True)
            back[key] = {}
            contact = []
            for rel, fw in sheets:
                name = os.path.basename(rel)
                sheet, infos, problems = build_sheet(boss, rel, fw)
                png = os.path.join(d, name)
                sheet.save(png)
                ase = os.path.splitext(png)[0] + '.aseprite'
                aseprite(png, '--save-as', ase)
                rt = os.path.join(tmp, key + '_' + name)
                aseprite(ase, '--save-as', rt)
                dif = pixel_diff(Image.open(png), Image.open(rt))
                if dif:
                    problems.append('%s: the .aseprite does not round-trip: %s' % (name, dif))
                for p in (png, ase):
                    with open(p, 'rb') as fh:
                        files[os.path.relpath(p, out_dir).replace(os.sep, '/')] = hashlib.sha256(fh.read()).hexdigest()
                pts = [info['hooks'].get('back') for info in infos]
                stem = os.path.splitext(name)[0]
                if rel not in FX:             # an effect has no strings: no hooks
                    back[key][stem] = pts
                    views = [f for f, info in enumerate(infos) if info.get('hook_how', {}).get('back') == 'by hand'
                             and 'back' in info.get('rings_drawn', [])]
                    if views:
                        over[stem] = views
                src = Image.fromarray(C.sheet(rel), 'RGBA')
                n = len(infos)
                skipped = {}
                for f, info in enumerate(infos):
                    for s in info['skipped']:
                        skipped.setdefault(s, []).append(f)
                how = {}
                for f, info in enumerate(infos):
                    h = info.get('hook_how', {}).get('back')
                    how[h] = how.get(h, 0) + 1
                a = C.np.array(sheet)
                op = a[:, :, 3] > 0
                black = int((op & (a[:, :, 0] == 0) & (a[:, :, 1] == 0) & (a[:, :, 2] == 0)).sum())
                cols = len({tuple(c) for c in a[op].tolist()})
                rings_on = sorted(set(infos[0].get('rings_drawn', [])))
                report.append('%s/%s: %d frames of %dx%d | black %.1f%% | colours %d | back %d/%d (%s) | rings drawn %s, '
                              'left off this sheet %s | overlays not placed %s%s' % (
                                  key, name, n, fw, sheet.size[1], 100.0 * black / max(1, int(op.sum())), cols,
                                  sum(1 for p in pts if p is not None), n,
                                  ', '.join('%s %d' % (k or 'none', v) for k, v in how.items()),
                                  rings_on or '-', infos[0].get('rings_left_off_sheet') or '-',
                                  {k: v for k, v in skipped.items() if not k.startswith('hook:')} or '-',
                                  ('\n   PROBLEM ' + '\n   PROBLEM '.join(problems)) if problems else ''))
                if problems:
                    ok = False
                s = 3 if fw <= 112 else 2
                frames_src = [src.crop((f * fw, 0, (f + 1) * fw, src.height)) for f in range(n)]
                frames_out = [sheet.crop((f * fw, 0, (f + 1) * fw, sheet.height)) for f in range(n)]
                marked = []
                for f, im in enumerate(frames_out):
                    im = C.up(im, s)
                    p = pts[f]
                    if p is not None:     # mark the back point on the contact sheet only
                        px = im.load()
                        for dy in range(-s, 2 * s):
                            for dx in range(-s, 2 * s):
                                x, y = p[0] * s + dx, p[1] * s + dy
                                if 0 <= x < im.width and 0 <= y < im.height and (abs(dx - s // 2) > s // 2 or abs(dy - s // 2) > s // 2):
                                    px[x, y] = (255, 0, 255, 255)
                    marked.append(im)
                contact.append(PR.label(PR.vstack([PR.hstack([C.up(i, s) for i in frames_src], gap=4),
                                                   PR.hstack(marked, gap=4)], gap=4),
                                        '%s  (source above; take B puppet below; magenta box = the back point)' % rel))
            PR.vstack(contact, gap=14).save(os.path.join(out_dir, 'contact_%s.png' % key))
            # the sheets derived from his twins (after his own, so the table keeps its order)
            for name, builder in DERIVED.get(key, []):
                sheet, pts, problems = builder()
                png = os.path.join(d, name + '.png')
                sheet.save(png)
                ase = os.path.splitext(png)[0] + '.aseprite'
                aseprite(png, '--save-as', ase)
                rt = os.path.join(tmp, key + '_' + name + '.png')
                aseprite(ase, '--save-as', rt)
                dif = pixel_diff(Image.open(png), Image.open(rt))
                if dif:
                    problems.append('%s: the .aseprite does not round-trip: %s' % (name, dif))
                for p in (png, ase):
                    rel_out = os.path.relpath(p, out_dir).replace(os.sep, '/')
                    with open(p, 'rb') as fh:
                        files[rel_out] = hashlib.sha256(fh.read()).hexdigest()
                    if rel_out in APPROVED and files[rel_out] != APPROVED[rel_out]:
                        problems.append('%s is not the approved file (%s, approved %s)' % (
                            rel_out, files[rel_out][:16], APPROVED[rel_out][:16]))
                back[key][name] = pts
                report.append('%s/%s.png: derived, %d frames | back %s%s' % (
                    key, name, len(pts), pts, ('\n   PROBLEM ' + '\n   PROBLEM '.join(problems)) if problems else ''))
                if problems:
                    ok = False
        gd = hooks_gd(back, over)
        with open(os.path.join(out_dir, 'JordanPuppetHooks.gd'), 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(gd)
        files['JordanPuppetHooks.gd'] = hashlib.sha256(gd.encode('utf-8')).hexdigest()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return files, back, report, ok


def ship(out_dir, files):
    """Copy the built files into the live tree with exclusive create. Nothing is written unless every
    destination is new."""
    plan = []
    for rel in files:
        if rel == 'JordanPuppetHooks.gd':
            dst = HOOKS_GD
        else:
            dst = os.path.join(DEST, *rel.split('/'))
        if not _under(dst, os.path.join(C.ROOT, 'Assets', 'Characters', 'Jordan', 'Puppets')) and dst != HOOKS_GD:
            raise SystemExit('refusing: %s is outside the puppet folder' % dst)
        plan.append((os.path.join(out_dir, *rel.split('/')), dst, rel))
    clash = [dst for _s, dst, _r in plan if os.path.exists(dst)]
    if clash:
        raise SystemExit('refusing: already exists, nothing shipped:\n  ' + '\n  '.join(clash))
    shipped = {}
    for srcp, dst, rel in plan:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(srcp, 'rb') as fh:
            data = fh.read()
        if hashlib.sha256(data).hexdigest() != files[rel]:
            raise SystemExit('refusing: %s changed since it was audited' % srcp)
        with open(dst, 'xb') as fh:        # exclusive create: never overwrite
            fh.write(data)
        shipped[os.path.relpath(dst, C.ROOT).replace(os.sep, '/')] = files[rel]
    with open(RECORD, 'x', encoding='utf-8') as fh:
        json.dump({'take': TAKE, 'shipped': shipped}, fh, indent=1)
    return shipped


def add(out_dir, files):
    """Ship only the sheets not shipped yet. Every file already shipped must rebuild byte-identical
    (the recipe has not moved under it), every new destination must be new (exclusive create), and
    every line of the shipped hooks table must survive unchanged; the table itself is regenerated in
    place (it is this rig's own generated file) and shipped.json gains the new hashes."""
    with open(RECORD, encoding='utf-8') as fh:
        rec = json.load(fh)
    shipped = rec['shipped']
    for path, h in shipped.items():       # the live files are still what was shipped
        with open(os.path.join(C.ROOT, *path.split('/')), 'rb') as fh:
            if hashlib.sha256(fh.read()).hexdigest() != h:
                raise SystemExit('refusing: %s changed since it was shipped' % path)
    plan, same = [], []
    for rel, h in files.items():
        if rel == 'JordanPuppetHooks.gd':
            continue
        dst = os.path.join(DEST, *rel.split('/'))
        path = os.path.relpath(dst, C.ROOT).replace(os.sep, '/')
        if path in shipped:
            if shipped[path] != h:
                raise SystemExit('refusing: the rebuild of the shipped %s differs from what shipped' % path)
            same.append(path)
            continue
        if not _under(dst, DEST):
            raise SystemExit('refusing: %s is outside the puppet folder' % dst)
        if os.path.exists(dst):
            raise SystemExit('refusing: %s already exists' % dst)
        plan.append((os.path.join(out_dir, *rel.split('/')), dst, rel, path))
    with open(HOOKS_GD, encoding='utf-8') as fh:
        old_gd = fh.read()
    with open(os.path.join(out_dir, 'JordanPuppetHooks.gd'), encoding='utf-8') as fh:
        new_gd = fh.read()
    old_lines, new_lines = old_gd.split('\n'), new_gd.split('\n')
    lost = [ln for ln in old_lines if ln not in new_lines]
    if lost:
        raise SystemExit('refusing: the regenerated hooks table drops or changes %d line(s):\n  %s' % (
            len(lost), '\n  '.join(lost)))
    added = []
    for srcp, dst, rel, path in plan:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(srcp, 'rb') as fh:
            data = fh.read()
        if hashlib.sha256(data).hexdigest() != files[rel]:
            raise SystemExit('refusing: %s changed since it was audited' % srcp)
        with open(dst, 'xb') as fh:        # exclusive create: never overwrite
            fh.write(data)
        shipped[path] = files[rel]
        added.append((path, files[rel]))
    with open(HOOKS_GD, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(new_gd)
    gd_path = os.path.relpath(HOOKS_GD, C.ROOT).replace(os.sep, '/')
    shipped[gd_path] = files['JordanPuppetHooks.gd']
    with open(RECORD, 'w', encoding='utf-8') as fh:
        json.dump(rec, fh, indent=1)
    diff = [ln for ln in new_lines if ln not in old_lines]
    return added, same, diff


def main(argv):
    if len(argv) < 2 or argv[0] not in ('--check', '--ship', '--add'):
        print(__doc__)
        return 2
    out_dir = os.path.abspath(argv[1])
    files, back, report, ok = build_all(out_dir)
    for ln in report:
        print(ln)
    if not ok:
        print('audit FAILED: nothing shipped')
        return 1
    print('audit clean: %d files built in %s' % (len(files), out_dir))
    if argv[0] == '--ship':
        shipped = ship(out_dir, files)
        for p, h in shipped.items():
            print('shipped', p, h[:16])
        print('record:', RECORD)
    if argv[0] == '--add':
        added, same, diff = add(out_dir, files)
        print('already shipped, rebuilt byte-identical and left alone: %d files' % len(same))
        for p, h in added:
            print('shipped', p, h[:16])
        print('hooks table regenerated in place: %s; lines added (no line removed or changed):' % HOOKS_GD)
        for ln in diff:
            print('+ ' + ln)
        print('record:', RECORD)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
