"""Decode a GIF (global palette, full-frame images) -> frames + delays; optional contact sheet."""
import sys, struct
from gifio import _lzw_decode
from pngio import write_png


def read_gif(path):
    b = open(path, 'rb').read()
    assert b[:6] in (b'GIF89a', b'GIF87a')
    w, h, flags, bgi, asp = struct.unpack('<HHBBB', b[6:13])
    pos = 13
    gct = []
    if flags & 0x80:
        n = 1 << ((flags & 7) + 1)
        gct = [tuple(b[pos + 3 * i:pos + 3 * i + 3]) for i in range(n)]
        pos += 3 * n
    frames, delays, delay = [], [], 0
    loop = None
    while pos < len(b):
        t = b[pos]
        if t == 0x21:
            label = b[pos + 1]
            pos += 2
            if label == 0xF9:
                size = b[pos]
                delay = struct.unpack('<H', b[pos + 2:pos + 4])[0]
                pos += size + 1
                pos += 1  # terminator
            else:
                if label == 0xFF and b[pos + 1:pos + 12] == b'NETSCAPE2.0':
                    loop = struct.unpack('<H', b[pos + 15:pos + 17])[0]
                while b[pos] != 0:
                    pos += b[pos] + 1
                pos += 1
        elif t == 0x2C:
            x, y, iw, ih, f = struct.unpack('<HHHHB', b[pos + 1:pos + 10])
            pos += 10
            mcs = b[pos]
            pos += 1
            data = bytearray()
            while b[pos] != 0:
                data += b[pos + 1:pos + 1 + b[pos]]
                pos += b[pos] + 1
            pos += 1
            idx = _lzw_decode(bytes(data), mcs, iw * ih)
            assert len(idx) >= iw * ih, ('short frame', len(idx), iw * ih)
            frames.append([[gct[idx[yy * iw + xx]] for xx in range(iw)] for yy in range(ih)])
            delays.append(delay)
        elif t == 0x3B:
            break
        else:
            raise ValueError('bad block %x at %d' % (t, pos))
    return w, h, frames, delays, loop


if __name__ == '__main__':
    for p in sys.argv[1:]:
        w, h, fr, d, loop = read_gif(p)
        print(p.split('/')[-1], '%dx%d' % (w, h), 'frames', len(fr), 'loop', loop, 'delays(cs)', d[:12], '...' if len(d) > 12 else '')
