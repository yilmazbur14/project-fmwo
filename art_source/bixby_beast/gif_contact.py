"""Decode a GIF written by gifio.write_gif and lay out its frames as a contact sheet (verification)."""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gifio import _lzw_decode
from pngio import write_png
import anim_common as AC


def read_gif(path):
    b = open(path, 'rb').read()
    assert b[:6] == b'GIF89a'
    w, h, flags, _, _ = struct.unpack('<HHBBB', b[6:13])
    pos = 13
    gct = []
    if flags & 0x80:
        n = 2 << (flags & 7)
        gct = [tuple(b[pos + i * 3:pos + i * 3 + 3]) for i in range(n)]
        pos += 3 * n
    frames, delays = [], []
    delay = 0
    while pos < len(b):
        t = b[pos]
        if t == 0x21:
            label = b[pos + 1]
            pos += 2
            if label == 0xF9:
                delay = struct.unpack('<H', b[pos + 2:pos + 4])[0]
            while b[pos]:
                pos += b[pos] + 1
            pos += 1
        elif t == 0x2C:
            x, y, fw, fh, fl = struct.unpack('<HHHHB', b[pos + 1:pos + 10])
            pos += 10
            mcs = b[pos]
            pos += 1
            data = bytearray()
            while b[pos]:
                data += b[pos + 1:pos + 1 + b[pos]]
                pos += b[pos] + 1
            pos += 1
            idx = _lzw_decode(bytes(data), mcs, fw * fh)
            frames.append([[gct[idx[yy * fw + xx]] + (255,) for xx in range(fw)] for yy in range(fh)])
            delays.append(delay)
        elif t == 0x3B:
            break
        else:
            raise ValueError('bad block %x' % t)
    return w, h, frames, delays


if __name__ == '__main__':
    path, out, step, shrink, cols = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
    w, h, frames, delays = read_gif(path)
    print(os.path.basename(path), w, 'x', h, len(frames), 'frames, total', sum(delays), 'cs')
    sel = list(range(0, len(frames), step))
    fw, fh = w // shrink, h // shrink
    rows = (len(sel) + cols - 1) // cols
    W, H = cols * (fw + 4), rows * (fh + 4)
    img = [[(30, 30, 30, 255)] * W for _ in range(H)]
    for k, i in enumerate(sel):
        ox, oy = (k % cols) * (fw + 4), (k // cols) * (fh + 4)
        fr = frames[i]
        for y in range(fh):
            for x in range(fw):
                img[oy + y][ox + x] = fr[y * shrink][x * shrink]
    write_png(os.path.join(AC.PREV, out), W, H, img)
    print('frames shown:', sel)
