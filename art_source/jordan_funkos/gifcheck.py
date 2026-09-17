"""Parse GIFs: count frames, read delays, decode frames and confirm they differ (animation present)."""
import sys, struct, glob, os
from gifio import _lzw_decode


def parse(path):
    b = open(path, 'rb').read()
    assert b[:6] in (b'GIF89a', b'GIF87a')
    w, h, flags = struct.unpack('<HHB', b[6:11])
    pos = 13
    if flags & 0x80:
        pos += 3 * (1 << ((flags & 7) + 1))
    frames, delays = [], []
    delay = None
    while pos < len(b):
        blk = b[pos]
        if blk == 0x21:
            label = b[pos + 1]
            pos += 2
            if label == 0xF9:
                delay = struct.unpack('<H', b[pos + 2:pos + 4])[0]
            while b[pos]:
                pos += b[pos] + 1
            pos += 1
        elif blk == 0x2C:
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
            frames.append(idx[:fw * fh])
            delays.append(delay)
        elif blk == 0x3B:
            break
        else:
            raise ValueError('bad block %x' % blk)
    return w, h, frames, delays


for path in sorted(glob.glob(sys.argv[1])):
    w, h, frames, delays = parse(path)
    distinct = len(set(bytes(f) if max(f) < 256 else tuple(f) for f in frames))
    complete = all(len(f) == w * h for f in frames)
    print('%-40s %4dx%-4d frames=%-3d distinct=%-3d complete=%s delays=%s' % (
        os.path.basename(path), w, h, len(frames), distinct, complete, sorted(set(delays))))
