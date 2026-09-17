import os, struct, glob
from gifio import _lzw_decode
from pngio import write_png, blank, paste, scale

def decode(path):
    b = open(path, 'rb').read()
    assert b[:6] == b'GIF89a'
    w, h, flags = struct.unpack('<HHB', b[6:11])
    pos = 13
    gct = []
    if flags & 0x80:
        n = 2 << (flags & 7)
        gct = [tuple(b[pos + 3 * i:pos + 3 * i + 3]) for i in range(n)]
        pos += 3 * n
    frames, delays = [], []
    delay = 0
    while pos < len(b):
        c = b[pos]
        if c == 0x21:
            label = b[pos + 1]
            pos += 2
            if label == 0xF9:
                delay = struct.unpack('<H', b[pos + 2:pos + 4])[0]
            while b[pos]:
                pos += b[pos] + 1
            pos += 1
        elif c == 0x2C:
            pos += 10
            mcs = b[pos]; pos += 1
            data = bytearray()
            while b[pos]:
                data += b[pos + 1:pos + 1 + b[pos]]; pos += b[pos] + 1
            pos += 1
            idx = _lzw_decode(bytes(data), mcs, w * h)
            frames.append([[gct[idx[y * w + x]] + (255,) for x in range(w)] for y in range(h)])
            delays.append(delay)
        elif c == 0x3B:
            break
    return w, h, frames, delays

for path in sorted(glob.glob('../preview/gif_*.gif')):
    w, h, frames, delays = decode(path)
    print(os.path.basename(path), '%dx%d' % (w, h), 'frames', len(frames), 'delays(cs)', delays)
    if 'full' in path or 'from_idle' in path:
        continue
    s = 1 if w > 200 else 2
    th = [[row[::3] for row in f[::3]] for f in frames]
    tw, thh = len(th[0][0]), len(th[0])
    out = blank(len(th) * (tw + 4), thh, (40, 40, 40, 255))
    for i, f in enumerate(th):
        paste(out, f, i * (tw + 4), 0)
    write_png('../preview/check_' + os.path.basename(path).replace('.gif', '.png'), len(out[0]), len(out), out)
