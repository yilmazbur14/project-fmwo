"""python jj_lint.py  - the numbers and the audit, per juggle frame, against Jordan's approved v2 sprite.

The reference is his approved v2 art: the approval sprite (jordan_redesign_v2.png, approved
2026-09-24) and the five fight sheets redrawn from it and shipped the same day as part of the approved
v2 cascade (idle, summon, taunt, hit, defeat): 22 frames, the quiff standing and knocked flat.

Per frame:
  black     keyline share of all drawn pixels. The approved v2 frames run 28.2-29.3%; a juggle frame
            may sit BLACK_PAD either side of that and no further.
            'body' is him alone; 'all' includes the effects.
  colours   distinct colours; every one must be one of the approved 40, black pure #000000.
  ramps     the tone shares of his big ramps (shirt red, dress pink, denim, skin, hair, gold). A
            turned body that has been lit wrong shows here first: the ramp collapses into its
            tails. Each share must stay inside the range his approved frames span. Where the hug
            or the tuck covers part of him differently from every approved frame, a finding is
            allowed only while the part proof holds (part_check: the rule-lit parts as built,
            before anything covers them, against the same parts at the rig's own light) and the
            turn check holds (rot_check: the frame against the same figure before it was turned).
  turn      rot_check, on every frame: quarter turns move pixels without resampling and must leave
            every share exactly as built; RotSprite (the lift, the apex, the loop's last frame) and
            the crash's row removal may move a tone by ROT_TOL points and the deep share by
            ROT_DEEP_TOL, no more.
  audit     keyline gaps (a coloured pixel touching transparency), stray pixels (no neighbour),
            pinholes (a transparent pixel boxed in on four sides), keys off the palette. Effects
            (jj_fx) float free by design and are left out of gaps and strays. There are no other
            exceptions: the approved sneakers' three open edge texels (janim_export's
            SNEAKER_QUIRKS) are sealed with a keyline wherever a sneaker meets open air
            (jj_build.seal_sneakers), so they are not whitelisted here.

Exits 1 if anything is fatal: an off-palette colour, a hole, a gap, a stray, a black share outside
the band, a ramp outside its band, or a failed part or turn check.
"""
import os
import sys
from collections import Counter

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jj_base as J  # noqa: E402
from PIL import Image  # noqa: E402

SHEETS = ['jordan_redesign_v2.png', 'jordan_idle.png', 'jordan_summon.png', 'jordan_taunt.png',
          'jordan_hit.png', 'jordan_defeat.png']
RAMPS = {'red': 'TRVv', 'pink': 'QPq', 'denim': 'SsNn', 'skin': 'edcba', 'hair': 'mljih',
         'gold': 'YOoGg'}
# Per frame. A juggle frame is a turned body with its limbs flung out, so its outline is longer
# for the same body than a standing frame's; the band allows for that (two points either side of
# the approved frames' own range), and no more. Nothing is padded to reach it.
BLACK_PAD = 0.02
# Each tone's share must stay inside the range the approved frames themselves span (per frame,
# every approved frame with at least MIN_PX pixels of that ramp), widened by TOL points; and the
# deepest shadow tones together inside their approved range widened by DEEP_TOL. The ranges are
# measured, not guessed: his own frames swing widely where a limb or the box moves.
TOL = 6.0
DEEP = {'red': 'v', 'pink': 'q', 'denim': 'n', 'skin': 'ba', 'hair': 'h', 'gold': 'g'}
DEEP_TOL = 5.0
MIN_PX = 40
# Visible-share findings that are coverage, not light, each checked by eye at 6-8x. The hug puts
# the box and both arms over his chest, so what shows of the shirt, the print and the box differs
# from every approved frame (none of them hugs the box: it is held up, at his hip, or on the mat).
# They are reported, not fatal, and only while the part proof for that ramp (part_check: the parts
# as built, before anything covers them, against the same parts at the rig's own light) and the
# turn check (rot_check) pass on that frame: those are what show the relight and the turn did not
# wreck it.
HUGGED = (2, 3, 4, 5, 6, 7, 8, 9, 10, 11)   # hugging the box (from the apex on), any light
TUCKED = (3, 4, 5, 6)                    # the backflip's tuck, the thighs level
REASONS = {
    'red': (HUGGED, "the hug: the box is held against the far side of the tee, over its shaded "
                    "edge, and when he is lit from his right the print covers the side that goes "
                    "into shade, so more of the tee's lit and base cloth shows than on any approved "
                    "frame"),
    'denim': (TUCKED, 'the tuck: thighs drawn up level are seen broadside, more of each the mid tone '
                      'than a standing leg seen edge-on'),
    'gold': (HUGGED, "the hug: the near hand and forearm cover the print's jaw and one of the box's "
                     "bars, and when the box turns upside down its tones mirror while the hands stay "
                     "on the same edges, so a different bar shows"),
}
JUSTIFIED = {(i, r): why for r, (frames, why) in REASONS.items() for i in frames}


def source_counts():
    inv = {v[:3]: k for k, v in J.PAL.items()}
    tot = Counter()
    frames = []
    for s in SHEETS:
        im = Image.open(os.path.join(J.ASSETS, s)).convert('RGBA')
        for f in range(im.width // 96):
            c = Counter()
            for p in J.flat(im.crop((f * 96, 0, f * 96 + 96, 96))):
                if p[3]:
                    c[inv[p[:3]]] += 1
            frames.append(c)
            tot += c
    return tot, frames


def black_band():
    """(lo, hi): the approved frames' own keyline shares, BLACK_PAD either side."""
    _, frames = source_counts()
    vals = [c['k'] / sum(c.values()) for c in frames]
    return min(vals) - BLACK_PAD, max(vals) + BLACK_PAD


def shares(c, ramp):
    n = sum(c.get(k, 0) for k in ramp)
    return [100.0 * c.get(k, 0) / n if n else 0.0 for k in ramp], n


def audit(px, fx):
    gaps, lone, holes = [], [], []
    for (x, y), k in px.items():
        if (x, y) in fx:
            continue
        n4 = ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
        if k != 'k' and any(q not in px for q in n4):
            gaps.append((x, y, k))
        if not any((x + dx, y + dy) in px for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy):
            lone.append((x, y, k))
    x0, y0, x1, y1 = J.bbox(px)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if (x, y) not in px and all(q in px for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
                holes.append((x, y))
    keys = sorted(set(px.values()) - J.ALLOWED)
    return {'gaps': gaps, 'lone': lone, 'holes': holes, 'keys': keys}


def bands():
    """{ramp: ([(lo, hi) per tone], (deep lo, deep hi), overall shares)} from the approved frames."""
    tot, frames = source_counts()
    out = {}
    for r, ramp in RAMPS.items():
        per = []
        for c in frames:
            s, n = shares(c, ramp)
            if n >= MIN_PX:
                per.append(s)
        lo = [min(p[j] for p in per) for j in range(len(ramp))]
        hi = [max(p[j] for p in per) for j in range(len(ramp))]
        deep = [sum(v for k, v in zip(ramp, p) if k in DEEP[r]) for p in per]
        out[r] = (list(zip(lo, hi)), (min(deep), max(deep)), shares(tot, ramp)[0])
    return out


# Which parts carry which rule-lit ramp: the parts the rig shades by its rules, whose light jj_light
# turns. Their tones are measured as built, before anything covers them.
PART_RAMPS = {'red': ('shirt', 'sleeve_near', 'sleeve_far'), 'pink': ('shirt',), 'denim': ('legs',),
              'skin': ('arm_near', 'arm_far', 'neck'), 'gold': ('box',)}
# The turned part may differ from the same part at the rig light by this much and no more: per tone,
# PART_TOL points; the deep share, the larger of PART_DEEP_TOL points or PART_DEEP_REL of the rig's
# own share. Why any difference at all: a mirrored span is exact, but the rig's fold strokes are
# drawing and land on the lit side when the light is mirrored, and a rim-lit bent leg's top and
# bottom edges are different lengths, so lighting the other one changes the count. The failure the
# contract names (a relight refitted to the turned box: 31% deep shadow against 14%) is a doubling,
# far outside either allowance.
PART_TOL = 8.0
PART_DEEP_TOL = 4.0
PART_DEEP_REL = 0.40


def part_check(i):
    """The relight's own proof for frame i: every rule-lit part built for this frame's turn has the
    same tones, in the same shares, as the same part built at the rig's own light. The shapes are
    identical; only which edges are lit may differ. Returns {ramp: (ok, note)}."""
    import jj_fig as F
    import jj_poses as MP
    spec = MP.FRAMES[i]()
    turned = F.build(spec.fig, spec.theta)
    rig = F.build(spec.fig, 0.0)
    out = {}
    for r, owners in PART_RAMPS.items():
        a, b = Counter(), Counter()
        for o in owners:
            a.update(turned.counts.get(o, Counter()))
            b.update(rig.counts.get(o, Counter()))
        sa, na = shares(a, RAMPS[r])
        sb, nb = shares(b, RAMPS[r])
        if na < MIN_PX:
            continue
        dev = max(abs(x - y) for x, y in zip(sa, sb))
        da = sum(v for k, v in zip(RAMPS[r], sa) if k in DEEP[r])
        db = sum(v for k, v in zip(RAMPS[r], sb) if k in DEEP[r])
        ok = dev <= PART_TOL and abs(da - db) <= max(PART_DEEP_TOL, PART_DEEP_REL * db)
        out[r] = (ok, 'as built: deep %.1f%% turned vs %.1f%% at the rig light, worst tone %.1f pts'
                  % (da, db, dev))
    return out


# What the turn itself may do to a ramp (rot_check): ROT_TOL points per tone and ROT_DEEP_TOL on the
# deep share, or ROT_PX texels' worth of the ramp if that is more. The floor is for the small ramps:
# RotSprite moves a handful of texels of a one-texel bar between its tones at 20-40 degrees, which on
# the box's ~90 gold texels is six points by itself. A wrecked ramp (the contract's 31% deep against
# 14%) is many times either allowance.
ROT_TOL = 5.0
ROT_DEEP_TOL = 4.0
ROT_PX = 6


def rot_check(i, b):
    """The turn's own proof for frame i: his visible tones in the frame against the same figure as it
    was built for this frame, before it was turned (and flattened). Returns {ramp: (ok, note)}."""
    import jj_fig as F
    import jj_poses as MP
    spec = MP.FRAMES[i]()
    cv = F.build(spec.fig, spec.theta)
    before = Counter(F.close_holes(cv.px, spec.fig.fx).values())
    after = Counter(b.body.values())
    exact = (spec.theta % 90 == 0) and spec.flatten >= 1.0
    out = {}
    for r, ramp in RAMPS.items():
        sa, na = shares(after, ramp)
        sb, nb = shares(before, ramp)
        if min(na, nb) < MIN_PX:
            continue
        dev = max(abs(x - y) for x, y in zip(sa, sb))
        da = sum(v for k, v in zip(ramp, sa) if k in DEEP[r])
        db = sum(v for k, v in zip(ramp, sb) if k in DEEP[r])
        floor = 100.0 * ROT_PX / na
        if exact:
            ok = dev < 1e-9 and abs(da - db) < 1e-9
        else:
            ok = dev <= max(ROT_TOL, floor) and abs(da - db) <= max(ROT_DEEP_TOL, floor)
        out[r] = (ok, 'the turn: worst tone %.1f pts, deep %.1f%% vs %.1f%% before it' % (dev, da, db))
    return out


def lint(built, verbose=True):
    B_ = bands()
    BLACK_BAND = black_band()
    allowed = J.approved_colours()
    fatal = []
    rows = []
    for i, b in enumerate(built):
        c_all = Counter(b.px.values())
        c_body = Counter(b.body.values())
        black_all = c_all['k'] / sum(c_all.values())
        black_body = c_body['k'] / sum(c_body.values())
        im = J.image(b.px)
        cols = {p for p in J.flat(im) if p[3]}
        semi = sum(1 for p in J.flat(im) if 0 < p[3] < 255)
        a = audit(b.px, b.fx)
        probs = []
        if cols - allowed:
            probs.append('%d colours off the approved %d' % (len(cols - allowed), len(allowed)))
        if semi:
            probs.append('%d semi-alpha' % semi)
        for k in ('gaps', 'lone', 'holes', 'keys'):
            if a[k]:
                probs.append('%s %s' % (k, a[k][:4]))
        if not BLACK_BAND[0] <= black_all <= BLACK_BAND[1]:
            probs.append('black %.1f%% outside %.0f-%.0f%%' % (100 * black_all, 100 * BLACK_BAND[0],
                                                               100 * BLACK_BAND[1]))
        ramp_txt = []
        notes = []
        parts = part_check(i)
        for r, (ok, note) in parts.items():
            if not ok:
                probs.append('%s relight check FAILED: %s' % (r, note))
        turns = rot_check(i, b)
        for r, (ok, note) in turns.items():
            if not ok:
                probs.append('%s turn check FAILED: %s' % (r, note))
        for r in ('red', 'pink', 'denim', 'skin', 'hair', 'gold'):
            s, n = shares(c_body, RAMPS[r])
            if n < MIN_PX:
                ramp_txt.append('%s    -' % r)
                continue
            tones, (dlo, dhi), _ = B_[r]
            deep = sum(v for k, v in zip(RAMPS[r], s) if k in DEEP[r])
            ramp_txt.append('%s %4.1f' % (r, deep))
            found = []
            hard = False
            for j, (lo, hi) in enumerate(tones):
                if not lo - TOL <= s[j] <= hi + TOL:
                    found.append('%s tone %s %.1f%% (approved %.1f-%.1f)' % (r, RAMPS[r][j], s[j], lo, hi))
                    hard |= not lo - 2 * TOL <= s[j] <= hi + 2 * TOL
            if not dlo - DEEP_TOL <= deep <= dhi + DEEP_TOL:
                found.append('%s deep shadow %.1f%% (approved %.1f-%.1f)' % (r, deep, dlo, dhi))
                hard |= not dlo * 0.5 <= deep <= dhi * 1.5
            if found and (i, r) in JUSTIFIED:
                pc = parts.get(r)
                tc = turns.get(r)
                if pc is not None and not pc[0]:
                    probs += found
                elif tc is not None and not tc[0]:
                    probs += found
                else:
                    proof = '; '.join(x[1] for x in (pc, tc) if x)
                    notes.append('justified %s: %s (%s)%s' % (r, JUSTIFIED[(i, r)], '; '.join(found),
                                                         (' [%s]' % proof) if proof else ''))
            else:
                probs += found
        rows.append((i, b.name, 100 * black_body, 100 * black_all, len(cols), ramp_txt, probs, notes))
        fatal += ['f%d %s: %s' % (i, b.name, p) for p in probs]
    if verbose:
        print('reference: %s; black band %.1f-%.1f%%' % (', '.join(SHEETS), 100 * BLACK_BAND[0],
                                                          100 * BLACK_BAND[1]))
        print('approved deep-shadow ranges: ' + '  '.join('%s %.1f-%.1f' % (r, B_[r][1][0], B_[r][1][1])
                                                         for r in RAMPS))
        print('%-3s %-13s %6s %6s %4s  %s' % ('#', 'frame', 'body', 'all', 'col', 'deep shadow % per ramp'))
        for (i, name, bb, ba, nc, rt, probs, notes) in rows:
            print('%-3d %-13s %5.1f%% %5.1f%% %4d  %s%s' % (i, name, bb, ba, nc, '  '.join(rt),
                                                        ('   <- ' + '; '.join(probs)) if probs else ''))
            for n in notes:
                print('      ' + n)
    return rows, fatal


def main():
    import jj_build as MB
    built = MB.frames()
    rows, fatal = lint(built)
    print('\n%d fatal finding(s)' % len(fatal))
    return 1 if fatal else 0


if __name__ == '__main__':
    sys.exit(main())
