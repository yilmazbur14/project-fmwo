"""Building blocks for the Eric V2 finisher sounds that make_voices.py doesn't have: steeper filters, filters that
leave a looped signal exactly periodic, Godot's own resampler (for previews and the loop check), a WAV writer that
stores a loop in a `smpl` chunk, and the level measurements the report prints.

Pure Python and deterministic: the same inputs always give the same bytes.
"""

import math
import os
import struct
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "audio_voices"))

from make_voices import SR, samples, loudness_db, b_weighted  # noqa: E402


# ------------------------------------------------------------------------------------------------- filters

def biquad(x, kind, hz, q=0.7071, state=None):
    """RBJ biquad low-pass or high-pass (12 dB/octave). `state` carries the filter memory across calls, which is
    how periodic() warms a filter up on the loop before the pass it keeps."""
    w = 2.0 * math.pi * hz / SR
    cw, alpha = math.cos(w), math.sin(w) / (2.0 * q)
    if kind == "lp":
        b0, b1, b2 = (1.0 - cw) / 2.0, 1.0 - cw, (1.0 - cw) / 2.0
    else:
        b0, b1, b2 = (1.0 + cw) / 2.0, -(1.0 + cw), (1.0 + cw) / 2.0
    a0, a1, a2 = 1.0 + alpha, -2.0 * cw, 1.0 - alpha
    b0, b1, b2, a1, a2 = b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0
    x1, x2, y1, y2 = state if state else (0.0, 0.0, 0.0, 0.0)
    out = []
    for s in x:
        y = b0 * s + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1, y2, y1 = x1, s, y1, y
        out.append(y)
    if state is not None:
        state[:] = [x1, x2, y1, y2]
    return out


def lp(x, hz, q=0.7071):
    return biquad(x, "lp", hz, q)


def hp(x, hz, q=0.7071):
    return biquad(x, "hp", hz, q)


def resonator(x, hz, q, state=None):
    """Constant-peak band-pass (RBJ, 0 dB at the centre)."""
    w = 2.0 * math.pi * hz / SR
    alpha = math.sin(w) / (2.0 * q)
    a0 = 1.0 + alpha
    b0, b2, a1, a2 = alpha / a0, -alpha / a0, -2.0 * math.cos(w) / a0, (1.0 - alpha) / a0
    x1, x2, y1, y2 = state if state else (0.0, 0.0, 0.0, 0.0)
    out = []
    for s in x:
        y = b0 * s + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1, y2, y1 = x1, s, y1, y
        out.append(y)
    if state is not None:
        state[:] = [x1, x2, y1, y2]
    return out


def swept_band(x, centres, q, state=None):
    """Chamberlin state-variable band-pass following a per-sample centre, run twice per sample so it stays
    stable up to SR / 6 (make_whoosh.py's filter). Unity gain at the centre."""
    low, band = state if state else (0.0, 0.0)
    damp = 1.0 / q
    out = []
    for s, hz in zip(x, centres):
        f = 2.0 * math.sin(math.pi * min(hz, SR / 6.0) / (2.0 * SR))
        for _ in range(2):
            high = s - low - damp * band
            band += f * high
            low += f * band
        out.append(band * damp)
    if state is not None:
        state[:] = [low, band]
    return out


def periodic(fn, x, *args, warmups=3):
    """Runs a filter on a looped signal so that its output loops too: the filter first runs over the loop
    `warmups` times to settle, then once more from the state it settled in, and only that last pass is kept.
    `fn` takes (signal, *args, state=list). Any stable filter settles to a periodic output this way, so the
    loop has no seam in it however long the filter rings."""
    state = []
    fn(x, *args, state=state)
    for _ in range(warmups - 1):
        fn(x, *args, state=state)
    return fn(x, *args, state=state)


def periodic_biquad(x, kind, hz, q=0.7071):
    return periodic(lambda s, state: biquad(s, kind, hz, q, state=state), x)


# ------------------------------------------------------------------------------------------------- signals

def tone(n, freqs, amp=1.0, phase=0.0):
    """A sine following a per-sample frequency."""
    out = []
    angle = phase
    for f in freqs:
        out.append(amp * math.sin(angle))
        angle += 2.0 * math.pi * f / SR
    return out


def decay(n, ms, attack_ms=0.0):
    """exp decay reaching -60 dB at `ms`, with an optional raised-cosine attack."""
    k = 6.908 / max(1.0, samples(ms))
    attack = samples(attack_ms)
    out = []
    for i in range(n):
        g = math.exp(-k * i)
        if i < attack:
            g *= 0.5 - 0.5 * math.cos(math.pi * i / attack)
        out.append(g)
    return out


def place(out, x, at_ms, gain=1.0):
    """Adds x into out starting at at_ms, clipped to out's length."""
    start = samples(at_ms)
    for i, s in enumerate(x):
        if start + i >= len(out):
            break
        out[start + i] += gain * s
    return out


def fade_edges(x, head_ms=1.5, tail_ms=1.5):
    head, tail = samples(head_ms), samples(tail_ms)
    for i in range(head):
        x[i] *= 0.5 - 0.5 * math.cos(math.pi * i / head)
    for i in range(tail):
        x[-1 - i] *= 0.5 - 0.5 * math.cos(math.pi * i / tail)
    return x


def soft_limit(x, ceiling):
    """tanh knee over the top 25 % below `ceiling`, transparent under it: the few transient peaks a layered hit
    throws above its body get rounded off instead of setting the whole sound's level."""
    knee = 0.75 * ceiling
    span = ceiling - knee
    out = []
    for s in x:
        a = abs(s)
        if a > knee:
            a = knee + span * math.tanh((a - knee) / span)
            s = a if s > 0 else -a
        out.append(s)
    return out


# ------------------------------------------------------------------------------------------------- Godot's playback

def godot_native(x, count, loop=None):
    """The frames AudioStreamPlaybackWAV hands its resampler, at the stream's own rate (Godot 4.6, measured with
    verify_eric_v2_sfx.gd): the data in order, zeros past its end, and with a forward loop (begin, end) the sample
    AT `end` is played and playback carries on from begin + 1. So a loop repeats every end - begin frames, and
    the frame at `end` has to be a copy of the one at `begin` for the repeat to be seamless."""
    out = []
    pos = 0
    n = len(x)
    for _ in range(count):
        out.append(x[pos] if pos < n else 0.0)
        pos += 1
        if loop is not None and pos > loop[1]:
            pos = loop[0] + 1
    return out


def godot_resample(x, rate, count, loop=None):
    """What Godot 4.6 plays for a 16-bit mono 44.1 kHz stream at pitch `rate` on a 44.1 kHz mix
    (AudioStreamPlaybackResampled): godot_native's frames behind 4 frames of zero history, read by a 16.16
    fixed-point head through Catmull-Rom interpolation, so the output lags the data by 2 frames. `count` output
    samples. For a 48 kHz device, pass rate * 44100 / 48000."""
    one = 1 << 16
    step = int(rate * one)
    need = ((count * step) >> 16) + 8
    q = [max(-32768, min(32767, int(round(s * 32767.0)))) / 32767.0 for s in x]
    buf = [0.0] * 4 + godot_native(q, need, loop)
    out = []
    offset = 0
    for _ in range(count):
        idx = 4 + (offset >> 16)
        mu = (offset & (one - 1)) / one
        y0, y1, y2, y3 = buf[idx - 3], buf[idx - 2], buf[idx - 1], buf[idx]
        mu2 = mu * mu
        h11 = mu2 * (mu - 1.0)
        z = mu2 - h11
        h01 = z - h11
        h10 = mu - z
        out.append(y1 + (y2 - y1) * h01 + ((y2 - y0) * h10 + (y3 - y1) * h11) * 0.5)
        offset += step
    return out


# ------------------------------------------------------------------------------------------------- files

def to_ints(x):
    return [max(-32768, min(32767, int(round(s * 32767.0)))) for s in x]


def wav_bytes(x, loop=None):
    """A 16-bit mono 44.1 kHz WAV as bytes. With loop = (begin, end) it adds a `smpl` chunk holding one forward
    loop, which Godot's importer reads when edit/loop_mode is "Detect From WAV", the default every SFX here
    keeps. Godot treats `end` as the first sample after the loop, so end = the loop's length."""
    ints = to_ints(x)
    data = struct.pack("<%dh" % len(ints), *ints)
    fmt = struct.pack("<HHIIHH", 1, 1, SR, SR * 2, 2, 16)
    chunks = b"fmt " + struct.pack("<I", len(fmt)) + fmt
    chunks += b"data" + struct.pack("<I", len(data)) + data
    if loop is not None:
        period_ns = int(round(1e9 / SR))
        smpl = struct.pack("<9I", 0, 0, period_ns, 60, 0, 0, 0, 1, 0)
        smpl += struct.pack("<6I", 0, 0, loop[0], loop[1], 0, 0)
        chunks += b"smpl" + struct.pack("<I", len(smpl)) + smpl
    return b"RIFF" + struct.pack("<I", 4 + len(chunks)) + b"WAVE" + chunks


def read_wav_file(path):
    """(samples, loop) from a 16-bit mono WAV, loop = (begin, end) from its smpl chunk or None."""
    with open(path, "rb") as f:
        raw = f.read()
    assert raw[:4] == b"RIFF" and raw[8:12] == b"WAVE", path
    pos, x, loop = 12, None, None
    while pos + 8 <= len(raw):
        cid, size = raw[pos:pos + 4], struct.unpack("<I", raw[pos + 4:pos + 8])[0]
        body = raw[pos + 8:pos + 8 + size]
        if cid == b"fmt ":
            tag, channels, rate, _, _, bits = struct.unpack("<HHIIHH", body[:16])
            assert (tag, channels, rate, bits) == (1, 1, SR, 16), (path, tag, channels, rate, bits)
        elif cid == b"data":
            x = [v / 32767.0 for v in struct.unpack("<%dh" % (len(body) // 2), body)]
        elif cid == b"smpl":
            loop = struct.unpack("<II", body[44:52])
        pos += 8 + size + (size & 1)
    return x, loop


# ------------------------------------------------------------------------------------------------- measures

def db(v):
    return 20.0 * math.log10(max(v, 1e-12))


def peak_db(x):
    return db(max(abs(s) for s in x))


def true_peak_db(x):
    """Peak of the signal reconstructed at 4x by windowed-sinc interpolation, which catches the overs between
    samples a DAC would produce."""
    taps = 16
    best = max(abs(s) for s in x)
    for i in range(len(x) - 1):
        if abs(x[i]) < 0.5 * best and abs(x[i + 1]) < 0.5 * best:
            continue
        for k in (1, 2, 3):
            t = i + k / 4.0
            acc = 0.0
            for j in range(i - taps + 1, i + taps + 1):
                if 0 <= j < len(x):
                    d = t - j
                    w = 0.5 + 0.5 * math.cos(math.pi * d / taps)
                    acc += x[j] * w * math.sin(math.pi * d) / (math.pi * d)
            best = max(best, abs(acc))
    return db(best)


def rms_db(x):
    return db(math.sqrt(sum(s * s for s in x) / len(x)))


def short_rms_db(x, window_ms=80.0):
    """RMS of the loudest window, unweighted."""
    n = samples(window_ms)
    y = x + [0.0] * n
    total = sum(s * s for s in y[:n])
    best = total
    for i in range(n, len(y)):
        total += y[i] * y[i] - y[i - n] * y[i - n]
        best = max(best, total)
    return db(math.sqrt(best / n))


def long_loudness_db(x, window_ms=400.0, hop_ms=100.0):
    """Median B-weighted loudness over 400 ms windows: what a steady sound (the loop, the music) sits at."""
    w = b_weighted(x)
    n, hop = samples(window_ms), samples(hop_ms)
    levels = sorted(10.0 * math.log10(sum(s * s for s in w[i:i + n]) / n + 1e-20)
                    for i in range(0, len(w) - n + 1, hop))
    return levels[len(levels) // 2]


def band_share(x, low_hz=None, high_hz=None):
    """Share of the energy under low_hz (or over high_hz), through 24 dB/octave filters."""
    y = x
    if low_hz:
        y = lp(lp(y, low_hz), low_hz)
    if high_hz:
        y = hp(hp(y, high_hz), high_hz)
    return sum(s * s for s in y) / (sum(s * s for s in x) + 1e-20)


def ring_out_ms(x, down_db=40.0):
    """Where the 10 ms level last sits within down_db of its loudest 10 ms."""
    frame = samples(10.0)
    levels = [10.0 * math.log10(sum(s * s for s in x[i:i + frame]) / frame + 1e-20)
              for i in range(0, len(x) - frame + 1, frame)]
    top = max(levels)
    return (max(i for i, level in enumerate(levels) if level > top - down_db) + 1) * 10.0


def centroid_hz(x):
    """Spectral centroid from the energy in octave bands (a cheap stand-in for an FFT, fine for comparing)."""
    edges = [31.25 * 2 ** k for k in range(10)]
    total = weighted = 0.0
    for lo in edges:
        hi = lo * 2.0
        centre = lo * math.sqrt(2.0)
        band = hp(hp(x, lo), lo)
        if hi < 0.45 * SR:
            band = lp(lp(band, hi), hi)
        e = sum(s * s for s in band)
        total += e
        weighted += e * centre
    return weighted / (total + 1e-20)


__all__ = [name for name in dir() if not name.startswith("_")] + ["SR", "samples", "loudness_db", "b_weighted"]
