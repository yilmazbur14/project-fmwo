"""Minimal GIF89a writer (global palette, LZW, per-frame delays, looping)."""
import struct

def _lzw(indices, min_code_size):
    clear = 1 << min_code_size
    eoi = clear + 1
    code_size = min_code_size + 1
    dict_ = {(i,): i for i in range(clear)}
    next_code = eoi + 1
    out_bits = 0
    nbits = 0
    out = bytearray()

    def emit(code):
        nonlocal out_bits, nbits
        out_bits |= code << nbits
        nbits += code_size
        while nbits >= 8:
            out.append(out_bits & 0xFF)
            out_bits >>= 8
            nbits -= 8

    emit(clear)
    w = ()
    for k in indices:
        wk = w + (k,)
        if wk in dict_:
            w = wk
        else:
            emit(dict_[w])
            if next_code < 4096:
                dict_[wk] = next_code
                next_code += 1
                if next_code > (1 << code_size) and code_size < 12:
                    code_size += 1
            else:
                emit(clear)
                dict_ = {(i,): i for i in range(clear)}
                next_code = eoi + 1
                code_size = min_code_size + 1
            w = (k,)
    if w:
        emit(dict_[w])
    emit(eoi)
    if nbits > 0:
        out.append(out_bits & 0xFF)
    return bytes(out)

def write_gif(path, frames, delays_ms, loop=0):
    """frames: list of 2D lists of (r,g,b[,a]) tuples, all same size. Opaque output."""
    h = len(frames[0]); w = len(frames[0][0])
    colors = {}
    for fr in frames:
        for row in fr:
            for p in row:
                c = p[:3]
                if c not in colors:
                    colors[c] = len(colors)
    assert len(colors) <= 256, len(colors)
    size_bits = max(1, (len(colors) - 1).bit_length())
    table_size = 1 << size_bits
    pal = bytearray()
    inv = sorted(colors.items(), key=lambda kv: kv[1])
    for c, i in inv:
        pal.extend(c)
    pal.extend(b'\x00' * (3 * (table_size - len(colors))))
    out = bytearray(b'GIF89a')
    out += struct.pack('<HHBBB', w, h, 0x80 | (size_bits - 1), 0, 0)
    out += pal
    out += b'\x21\xFF\x0BNETSCAPE2.0\x03\x01' + struct.pack('<H', loop) + b'\x00'
    min_code = max(2, size_bits)
    for fr, d in zip(frames, delays_ms):
        cs = max(2, int(round(d / 10.0)))
        out += b'\x21\xF9\x04' + bytes([0x04]) + struct.pack('<H', cs) + b'\x00\x00'
        out += b'\x2C' + struct.pack('<HHHHB', 0, 0, w, h, 0)
        idx = [colors[p[:3]] for row in fr for p in row]
        data = _lzw(idx, min_code)
        out.append(min_code)
        for i in range(0, len(data), 255):
            chunk = data[i:i + 255]
            out.append(len(chunk))
            out += chunk
        out.append(0)
    out += b'\x3B'
    open(path, 'wb').write(out)
