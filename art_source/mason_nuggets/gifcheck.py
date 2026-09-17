"""gifcheck.py in.gif out.png cols scale_div -> decode our GIF (global palette, full frames) into a contact sheet"""
import sys, struct, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gifio import _lzw_decode
from pngio import write_png
data = open(sys.argv[1], 'rb').read()
w, h, flags = struct.unpack('<HHB', data[6:11])
gct = 2 << (flags & 7)
pal = [tuple(data[13 + 3 * i:16 + 3 * i]) for i in range(gct)]
pos = 13 + 3 * gct
frames = []
while pos < len(data):
    b = data[pos]
    if b == 0x21:
        pos += 2
        while data[pos]:
            pos += data[pos] + 1
        pos += 1
    elif b == 0x2c:
        pos += 10
        mcs = data[pos]; pos += 1
        blob = b''
        while data[pos]:
            blob += data[pos + 1:pos + 1 + data[pos]]
            pos += data[pos] + 1
        pos += 1
        idx = _lzw_decode(blob, mcs, w * h)
        frames.append([[pal[idx[y * w + x]] for x in range(w)] for y in range(h)])
    else:
        break
cols = int(sys.argv[3]); div = int(sys.argv[4])
fw, fh = w // div, h // div
rows = (len(frames) + cols - 1) // cols
out = [[(30, 30, 30, 255)] * (cols * (fw + 4)) for _ in range(rows * (fh + 4))]
for i, fr in enumerate(frames):
    ox, oy = (i % cols) * (fw + 4), (i // cols) * (fh + 4)
    for y in range(fh):
        for x in range(fw):
            out[oy + y][ox + x] = fr[y * div][x * div] + (255,)
write_png(sys.argv[2], len(out[0]), len(out), out)
print('frames', len(frames), 'size', w, h)
