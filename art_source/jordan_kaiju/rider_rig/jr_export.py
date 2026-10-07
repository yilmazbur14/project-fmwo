"""Write Jordan's kaiju-fight sheets into scratchpad/jordan_kaiju/rider/ (NEVER into Assets): each sheet's
PNG + .aseprite (round-trip checked), a 3x preview, a GIF, then contract.json and a contact sheet beside
his live idle and the approved rider, and the ride frames sat on the approved kaiju.

    python jr_export.py wave1          # the six wave-1 sheets
    python jr_export.py wave2          # the four wave-2 sheets
    python jr_export.py all
"""
import importlib
import json
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jr_common as C  # noqa: E402
import jr_sheet as S   # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

WAVES = {
    'wave1': ['jr_s_ride_idle', 'jr_s_ride_throw', 'jr_s_ride_brace', 'jr_s_topple', 'jr_s_daze', 'jr_s_climb'],
    'wave2': ['jr_s_ride_taunt', 'jr_s_box_open', 'jr_s_toss', 'jr_s_butt_land'],
}
OUT = C.RIDER
CONTRACT = os.path.join(OUT, 'contract.json')


def label(im, text, pad=16):
    out = Image.new('RGBA', (im.width, im.height + pad), (10, 10, 12, 255))
    out.paste(im, (0, pad))
    ImageDraw.Draw(out).text((4, 2), text, fill=(230, 230, 236, 255))
    return out


def stack(ims, gap=6, bg=(10, 10, 12, 255)):
    w = max(i.width for i in ims)
    h = sum(i.height for i in ims) + gap * (len(ims) - 1)
    out = Image.new('RGBA', (w, h), bg)
    y = 0
    for i in ims:
        out.paste(i, (0, y))
        y += i.height + gap
    return out


def row(ims, gap=6, bg=(10, 10, 12, 255)):
    w = sum(i.width for i in ims) + gap * (len(ims) - 1)
    h = max(i.height for i in ims)
    out = Image.new('RGBA', (w, h), bg)
    x = 0
    for i in ims:
        out.paste(i, (x, 0))
        x += i.width + gap
    return out


def refs():
    """His live idle f0 and the approved rider (cropped to the ride frame), 3x on the mat colour."""
    live = C.live_sheet('jordan_idle').crop((0, 0, 96, 96))
    rider = Image.open(os.path.join(C.RIDER, 'ref', 'kaiju_mounted_idle_rider.png')).convert('RGBA').crop((83, -10, 179, 86))
    return [label(C.up(live, 3, C.MAT), 'LIVE jordan_idle f0'), label(C.up(rider, 3, C.MAT), 'APPROVED rider')]


def on_kaiju(frames, name):
    """Ride frames sat on the approved kaiju (its 'kaiju' layer), SEAT on its RIDER_SEAT (127, 65)."""
    k = Image.open(os.path.join(C.RIDER, 'ref', 'kaiju_mounted_idle_kaiju.png')).convert('RGBA')
    pad = 24
    ims = []
    for fr in frames:
        base = Image.new('RGBA', (k.width, k.height + pad), C.BG)
        base.alpha_composite(k, (0, pad))
        sx, sy = fr.anchors['SEAT']
        base.alpha_composite(C.render(fr.px), (127 - sx, 65 - sy + pad))
        ims.append(C.up(base.crop((70, 0, 200, 130)), 3))
    p = C.guard_out(os.path.join(OUT, 'look', 'on_kaiju_%s.png' % name))
    row(ims).save(p)
    return p


def main(which):
    names = WAVES['wave1'] + WAVES['wave2'] if which == 'all' else WAVES[which]
    contract = {}
    if os.path.exists(CONTRACT):
        contract = json.load(open(CONTRACT))
    contract.setdefault('sheets', {})
    contract.update({
        'frame': [96, 96], 'scale_in_game': 3, 'keyline': '#000000', 'layout': 'horizontal strip, hframes = frames, vframes = 1',
        'colours': "only Jordan's approved 40 (Assets/Characters/Jordan/jordan_redesign_v2.png)",
        'black_refs': {'ride': 'approved rider layer 28.96% (+-1.5)', 'mat': 'live jordan_idle f0 30.67% (+-1.5)'},
        'anchor_meaning': {
            'SEAT': 'the texel that sits on the kaiju RIDER_SEAT',
            'CROWN': 'top of his hair (topmost head texel; middle column of that row)',
            'HAND': 'release texel: where the thrown figure appears (ride_throw f2)',
            'SOLES': 'mat contact point (soles row 95): place on the floor spot',
            'PIVOT': 'body centre (hips) for arcs between SEAT and SOLES',
            'BODY_BOX': '[x, y, w, h] round every non-effect texel (hurtbox source)',
            'BOX': 'centre of his gold box', 'GRIP': 'his gripping fist', 'STARS': 'centre of the daze stars',
            'TOY': 'where kaiju_toy FEET (its pivot (12, 27)) goes when he holds it'},
        'rig': 'scratchpad/jordan_kaiju/rider/rig (jr_*.py), on a scratch copy of art_source/jordan_anims + jordan_v2 '
               '(vendor/, verified to rebuild the live idle/summon/taunt/hit/defeat sheets pixel for pixel)',
    })
    allp = []
    rows = [row(refs())]
    for n in names:
        mod = importlib.import_module(n)
        entry, probs, frames = S.build_sheet(mod, OUT, write=True)
        contract['sheets'][mod.NAME] = entry
        allp += probs
        strip = S.strip(frames)
        rows.append(label(C.up(strip, 3, C.MAT), '%s  %d frames  times %s' % (mod.NAME, len(frames), mod.TIMES)))
        if mod.KIND == 'ride':
            print('on kaiju:', on_kaiju(frames, mod.NAME))
        print('%s: %s' % (mod.NAME, 'OK' if not probs else probs))
    with open(C.guard_out(CONTRACT), 'w') as f:
        json.dump(contract, f, indent=1)
    sheet = stack(rows)
    p = C.guard_out(os.path.join(OUT, 'contact_sheet_%s.png' % which))
    sheet.save(p)
    print('contact sheet:', p)
    print('contract:', CONTRACT)
    for x in allp:
        print('PROBLEM', x)
    return 1 if allp else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else 'wave1'))
