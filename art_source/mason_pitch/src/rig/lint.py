"""Numbers for every new frame against Mason's live sheets (read-only on Assets)."""
import sys; sys.dont_write_bytecode = True
from PIL import Image
from collections import Counter
A = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Mason/'

def cols_of(im):
    return Counter(p[:3] for p in im.get_flattened_data() if p[3] > 0)

SHEET = Image.open(A + 'mason_sheet.png').convert('RGBA')
METEOR = Image.open(A + 'nugget_meteor.png').convert('RGBA')
APPROVED = set(cols_of(SHEET)) | set(cols_of(METEOR))

def lint(name, im, fw, fh, feet=None):
    n = im.width // fw
    rows = []
    allc = Counter()
    for i in range(n):
        f = im.crop((i * fw, 0, (i + 1) * fw, fh))
        px = list(f.get_flattened_data())
        op = [p for p in px if p[3] > 0]
        semi = sum(1 for p in px if 0 < p[3] < 255)
        blk = sum(1 for p in op if p[:3] == (0, 0, 0))
        c = cols_of(f); allc.update(c)
        edge = sum(1 for y in range(fh) for x in range(fw) if f.getpixel((x, y))[3] and (x in (0, fw - 1) or y == 0 or (y == fh - 1 and feet is None)))
        foreign = sorted('#%02X%02X%02X' % k for k in c if k not in APPROVED)
        feet_ok = ''
        if feet is not None:
            row = [x for x in range(fw) if f.getpixel((x, fh - 1))[3]]
            feet_ok = ' feet-row px %d' % len(row)
        rows.append('  %s[%d] opaque %4d black %4d ratio %.3f colours %2d semi %d edge %d foreign %s%s' % (
            name, i, len(op), blk, blk / max(1, len(op)), len(c), semi, edge, foreign or '-', feet_ok))
    print('\n'.join(rows))
    return allc

if __name__ == '__main__':
    import fastball as FB, projectile as PJ
    from view import to_img
    for nm, pose in FB.FRAMES:
        lint(nm, to_img(FB.render(pose)), 64, 64, feet=True)
    print('live sheet: ratio 0.241 overall, frames 0.221-0.285, colours 13-21 per frame')
