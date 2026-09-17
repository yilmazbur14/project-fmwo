"""gifcheck.py in.gif out.png [every] [scale_div] -> decode frames of a gif written by gifio (global palette,
full-size frames) into a contact sheet; prints frame count and delays."""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gifio import _lzw_decode
from pngio import write_png

path, out = sys.argv[1], sys.argv[2]
every = int(sys.argv[3]) if len(sys.argv) > 3 else 1
div = int(sys.argv[4]) if len(sys.argv) > 4 else 1
b = open(path, 'rb').read()
assert b[:6] == b'GIF89a'
w, h, flags, _, _ = struct.unpack('<HHBBB', b[6:13])
gsize = 2 << (flags & 7)
pal = [tuple(b[13 + 3 * i:16 + 3 * i]) for i in range(gsize)]
pos = 13 + 3 * gsize
frames, delays = [], []
delay = 0
while pos < len(b):
    t = b[pos]
    if t == 0x21:
        label = b[pos + 1]
        if label == 0xF9:
            delay = struct.unpack('<H', b[pos + 4:pos + 6])[0]
        pos += 2
        while b[pos] != 0:
            pos += b[pos] + 1
        pos += 1
    elif t == 0x2C:
        fx, fy, fw, fh, fl = struct.unpack('<HHHHB', b[pos + 1:pos + 10])
        pos += 10
        mcs = b[pos]
        pos += 1
        data = bytearray()
        while b[pos] != 0:
            n = b[pos]
            data += b[pos + 1:pos + 1 + n]
            pos += n + 1
        pos += 1
        idx = _lzw_decode(bytes(data), mcs, fw * fh)
        frames.append(idx)
        delays.append(delay)
    elif t == 0x3B:
        break
    else:
        raise ValueError('bad block %x' % t)
print(len(frames), 'frames', w, 'x', h, 'delays(cs):', delays)
sel = list(range(0, len(frames), every))
cw, ch = w // div, h // div
cols = min(6, len(sel))
rows = (len(sel) + cols - 1) // cols
sheet = [[(30, 30, 36, 255)] * (cols * (cw + 4)) for _ in range(rows * (ch + 4))]
for k, fi in enumerate(sel):
    r, c = divmod(k, cols)
    idx = frames[fi]
    for y in range(ch):
        for x in range(cw):
            p = pal[idx[(y * div) * w + x * div]]
            sheet[r * (ch + 4) + y][c * (cw + 4) + x] = p + (255,)
write_png(out, cols * (cw + 4), rows * (ch + 4), sheet)
print('wrote', out)
