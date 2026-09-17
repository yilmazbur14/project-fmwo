"""Minimal animated GIF89a writer (pure Python). Frames are lists of rows of RGBA tuples, all opaque."""
import struct


def _lzw(indices, min_code_size):
    clear = 1 << min_code_size
    eoi = clear + 1
    out_bits = []
    bitbuf = 0
    bitcnt = 0
    data = bytearray()

    def emit(code, size):
        nonlocal bitbuf, bitcnt
        bitbuf |= code << bitcnt
        bitcnt += size
        while bitcnt >= 8:
            data.append(bitbuf & 255)
            bitbuf >>= 8
            bitcnt -= 8

    def reset():
        return {(i,): i for i in range(clear)}, clear + 2, min_code_size + 1

    table, nxt, size = reset()
    emit(clear, size)
    w = ()
    for idx in indices:
        wc = w + (idx,)
        if wc in table:
            w = wc
            continue
        emit(table[w], size)
        if nxt < 4096:
            table[wc] = nxt
            nxt += 1
            if nxt > (1 << size) and size < 12:
                size += 1
        else:
            emit(clear, size)
            table, nxt, size = reset()
        w = (idx,)
    if w:
        emit(table[w], size)
        if nxt >= (1 << size) and size < 12:
            size += 1
    emit(eoi, size)
    if bitcnt:
        data.append(bitbuf & 255)
    return bytes(data)


def write_gif(path, frames, durations_ms, loop=0):
    h = len(frames[0])
    w = len(frames[0][0])
    colors = {}
    for fr in frames:
        for row in fr:
            for p in row:
                c = p[:3]
                if c not in colors:
                    colors[c] = len(colors)
    assert len(colors) <= 256, len(colors)
    bits = max(1, (len(colors) - 1).bit_length())
    tsize = 1 << bits
    pal = bytearray()
    inv = sorted(colors.items(), key=lambda kv: kv[1])
    for c, _ in inv:
        pal += bytes(c)
    pal += bytes(3 * (tsize - len(colors)))
    out = bytearray(b'GIF89a')
    out += struct.pack('<HHBBB', w, h, 0x80 | (bits - 1), 0, 0)
    out += pal
    out += b'\x21\xff\x0bNETSCAPE2.0\x03\x01' + struct.pack('<H', loop) + b'\x00'
    mcs = max(2, bits)
    for fr, d in zip(frames, durations_ms):
        out += b'\x21\xf9\x04' + bytes([0x04]) + struct.pack('<H', max(1, round(d / 10))) + b'\x00\x00'
        out += b'\x2c' + struct.pack('<HHHHB', 0, 0, w, h, 0)
        idx = [colors[p[:3]] for row in fr for p in row]
        comp = _lzw(idx, mcs)
        out.append(mcs)
        for i in range(0, len(comp), 255):
            chunk = comp[i:i + 255]
            out.append(len(chunk))
            out += chunk
        out.append(0)
    out += b'\x3b'
    open(path, 'wb').write(bytes(out))
