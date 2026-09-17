"""Minimal animated GIF writer (global palette, LZW) + decoder for verification."""
import struct

def _lzw_encode(indices, mcs):
    clear = 1 << mcs
    eoi = clear + 1
    out = bytearray()
    state = [0, 0]  # bitbuf, bitcnt

    def emit(code, size):
        state[0] |= code << state[1]
        state[1] += size
        while state[1] >= 8:
            out.append(state[0] & 0xFF)
            state[0] >>= 8
            state[1] -= 8

    def reset():
        return {}, eoi + 1, mcs + 1

    table, next_code, cs = reset()
    emit(clear, cs)
    prefix = indices[0]
    for c in indices[1:]:
        key = (prefix, c)
        if key in table:
            prefix = table[key]
            continue
        emit(prefix, cs)
        if next_code < 4095:
            table[key] = next_code
            next_code += 1
            if next_code - 1 == (1 << cs) and cs < 12:
                cs += 1
        else:
            emit(clear, cs)
            table, next_code, cs = reset()
        prefix = c
    emit(prefix, cs)
    emit(eoi, cs)
    if state[1]:
        out.append(state[0] & 0xFF)
    return bytes(out)

def _lzw_decode(data, mcs, npix):
    clear = 1 << mcs
    eoi = clear + 1
    pos = 0
    bitbuf = 0
    bitcnt = 0
    cs = mcs + 1

    def base():
        return {i: (i,) for i in range(clear)}

    table = base()
    nxt = eoi + 1
    prev = None
    out = []
    while True:
        while bitcnt < cs:
            if pos >= len(data):
                return out
            bitbuf |= data[pos] << bitcnt
            pos += 1
            bitcnt += 8
        code = bitbuf & ((1 << cs) - 1)
        bitbuf >>= cs
        bitcnt -= cs
        if code == clear:
            table = base(); nxt = eoi + 1; cs = mcs + 1; prev = None
            continue
        if code == eoi:
            return out
        if prev is None:
            entry = table[code]
            out.extend(entry)
            prev = code
            continue
        if code in table:
            entry = table[code]
            if nxt < 4096:
                table[nxt] = table[prev] + (entry[0],)
        elif code == nxt:
            entry = table[prev] + (table[prev][0],)
            table[nxt] = entry
        else:
            raise ValueError('bad code %d (next %d)' % (code, nxt))
        if nxt < 4096:
            nxt += 1
        out.extend(entry)
        if nxt == (1 << cs) and cs < 12:
            cs += 1
        prev = code

def write_gif(path, frames, delays_cs, loop=0):
    """frames: list of 2D lists of RGB(A) tuples (same size). delays in 1/100 s."""
    h = len(frames[0]); w = len(frames[0][0])
    pal = {}
    for fr in frames:
        for row in fr:
            for p in row:
                k = tuple(p[:3])
                if k not in pal:
                    pal[k] = len(pal)
    assert len(pal) <= 256, len(pal)
    bits = max(1, (len(pal) - 1).bit_length())
    size = 1 << bits
    colors = list(pal.keys()) + [(0, 0, 0)] * (size - len(pal))
    mcs = max(2, bits)
    b = bytearray(b'GIF89a')
    b += struct.pack('<HHBBB', w, h, 0x80 | (bits - 1), 0, 0)
    for c in colors:
        b += bytes(c)
    b += b'\x21\xff\x0bNETSCAPE2.0\x03\x01' + struct.pack('<H', loop) + b'\x00'
    encoded = []
    for fr, d in zip(frames, delays_cs):
        b += b'\x21\xf9\x04' + bytes([0x04]) + struct.pack('<H', d) + b'\x00\x00'
        b += b'\x2c' + struct.pack('<HHHHB', 0, 0, w, h, 0)
        idx = [pal[tuple(p[:3])] for row in fr for p in row]
        data = _lzw_encode(idx, mcs)
        encoded.append((idx, data))
        b += bytes([mcs])
        for i in range(0, len(data), 255):
            chunk = data[i:i + 255]
            b += bytes([len(chunk)]) + chunk
        b += b'\x00'
    b += b'\x3b'
    open(path, 'wb').write(bytes(b))
    # verify round trip
    for idx, data in encoded:
        dec = _lzw_decode(data, mcs, len(idx))
        assert dec[:len(idx)] == idx, 'LZW round-trip mismatch'
    return len(b)
