"""Animated GIF writer (global palette, LZW) for long previews.
Same output format as gifio.write_gif, but: no nested closures in the encoder, and frames are upscaled
while encoding (only one upscaled frame in memory at a time). Long previews (60+ frames of 840x780) built
in one process with gifio intermittently failed with nonsense TypeErrors under memory pressure."""
import struct
from gifio import _lzw_decode

EXT_LOOP = bytes([0x21, 0xFF, 0x0B]) + b'NETSCAPE2.0' + bytes([0x03, 0x01])
EXT_GCE = bytes([0x21, 0xF9, 0x04, 0x04])
IMG_SEP = bytes([0x2C])
TRAILER = bytes([0x3B])
ZERO = bytes([0x00])


class _Bits:
    __slots__ = ('out', 'buf', 'cnt')

    def __init__(self):
        self.out = bytearray()
        self.buf = 0
        self.cnt = 0

    def emit(self, code, size):
        self.buf |= code << self.cnt
        self.cnt += size
        while self.cnt >= 8:
            self.out.append(self.buf & 0xFF)
            self.buf >>= 8
            self.cnt -= 8

    def flush(self):
        if self.cnt:
            self.out.append(self.buf & 0xFF)
        return bytes(self.out)


def lzw_encode(indices, mcs):
    clear = 1 << mcs
    eoi = clear + 1
    bits = _Bits()
    table = {}
    next_code = eoi + 1
    cs = mcs + 1
    bits.emit(clear, cs)
    prefix = indices[0]
    n = len(indices)
    i = 1
    while i < n:
        c = indices[i]
        i += 1
        key = prefix * 4096 + c
        code = table.get(key)
        if code is not None:
            prefix = code
            continue
        bits.emit(prefix, cs)
        if next_code < 4095:
            table[key] = next_code
            next_code += 1
            if next_code - 1 == (1 << cs) and cs < 12:
                cs += 1
        else:
            bits.emit(clear, cs)
            table = {}
            next_code = eoi + 1
            cs = mcs + 1
        prefix = c
    bits.emit(prefix, cs)
    bits.emit(eoi, cs)
    return bits.flush()


def write_gif(path, frames, delays_cs, loop=0, verify=True, scale=1):
    """frames: a list of 1x frames, or a callable frames(i) -> frame (only one frame is held in memory, which
    matters for long previews). scale: integer upscale applied per frame while encoding."""
    n_frames = len(delays_cs)
    get = frames if callable(frames) else (lambda i: frames[i])
    first = get(0)
    h = len(first) * scale
    w = len(first[0]) * scale
    pal = {}
    for i in range(n_frames):
        fr = first if i == 0 else get(i)
        for row in fr:
            for p in row:
                k = (p[0], p[1], p[2])
                if k not in pal:
                    pal[k] = len(pal)
        del fr
    assert len(pal) <= 256, len(pal)
    bits_n = max(1, (len(pal) - 1).bit_length())
    size = 1 << bits_n
    colors = list(pal.keys()) + [(0, 0, 0)] * (size - len(pal))
    mcs = max(2, bits_n)
    b = bytearray(b'GIF89a')
    b += struct.pack('<HHBBB', w, h, 0x80 | (bits_n - 1), 0, 0)
    for c in colors:
        b += bytes(c)
    b += EXT_LOOP + struct.pack('<H', loop) + ZERO
    for i, d in enumerate(delays_cs):
        fr = get(i)
        b += EXT_GCE + struct.pack('<H', d) + ZERO + ZERO
        b += IMG_SEP + struct.pack('<HHHHB', 0, 0, w, h, 0)
        idx = []
        for row in fr:
            line = []
            for p in row:
                line.extend([pal[(p[0], p[1], p[2])]] * scale)
            for _ in range(scale):
                idx.extend(line)
        data = lzw_encode(idx, mcs)
        if verify:
            dec = _lzw_decode(data, mcs, len(idx))
            assert dec[:len(idx)] == idx, 'LZW round-trip mismatch'
        b += bytes([mcs])
        for k in range(0, len(data), 255):
            chunk = data[k:k + 255]
            b += bytes([len(chunk)]) + chunk
        b += ZERO
        del fr, idx, data
    b += TRAILER
    open(path, 'wb').write(bytes(b))
    return len(b)
