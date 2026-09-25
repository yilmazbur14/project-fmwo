"""Synthesizes Matt's sound effects, as 16-bit mono 44.1 kHz WAVs.

Pure Python with fixed seeds, built from make_voices.py's blocks and make_bixby_roar.py's voice source (pulse_train,
wander), so every run writes identical files. Nothing is sampled or downloaded.

    python make_matt_sfx.py PREVIEW_DIR   writes preview_matt_<name>.wav for every sound into PREVIEW_DIR
    python make_matt_sfx.py --ship        writes matt_<name>.wav into Assets/Audio/SFX
    ... --only stomp,boom_fire            either of those, for only the sounds named

Run with no argument, it only says how to use it: it never writes into the shipped folder unless asked to.
Ship a new sound with --only, so the approved ones are never rewritten.

Every sound is normalized to a -3 dBFS peak; MattArtLayout.SFX sets how loud each one plays.
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "audio_voices"))

from make_voices import (SR, PROJECT, samples, contour, oscillator, pulse, envelope, noise, lowpass, highpass,
                         bandpass, mul, mix, delayed, normalized, saturate, write_wav)
from make_bixby_roar import pulse_train, wander

SFX_DIR = os.path.join(PROJECT, "Assets", "Audio", "SFX")
PEAK_DBFS = -3.0


# ------------------------------------------------------------------------------------------------- building blocks

def finish(x, edge_ms=3.0):
    """Blocks DC, silences both ends and normalizes to PEAK_DBFS."""
    x = highpass(x, 25.0)
    edge = samples(edge_ms)
    for i in range(min(edge, len(x) // 2)):
        g = 0.5 - 0.5 * math.cos(math.pi * i / edge)
        x[i] *= g
        x[-1 - i] *= g
    peak = max(abs(s) for s in x) or 1.0
    return [s * 10.0 ** (PEAK_DBFS / 20.0) / peak for s in x]


def sweep(n, points):
    """A sine following (ms, Hz) points."""
    return oscillator(contour(n, points), [(1, 1.0)])


def formants(x, resonances):
    """A vocal tract: a band-pass per formant, mixed by weight. resonances: (Hz, Q, gain)."""
    return mix(*[(gain, bandpass(x, hz, q)) for hz, q, gain in resonances])


def gliding_formants(x, start, end, chunk_ms=20.0):
    """Formants gliding from `start` to `end` across the sound, filtered a chunk at a time and cross-faded."""
    n = len(x)
    size = samples(chunk_ms)
    out = [0.0] * n
    pieces = max(1, n // size)
    for p in range(pieces + 1):
        u = min(1.0, p / max(1, pieces))
        res = [(a[0] + (b[0] - a[0]) * u, a[1], a[2] + (b[2] - a[2]) * u) for a, b in zip(start, end)]
        lo = max(0, (p - 1) * size)
        hi = min(n, (p + 1) * size)
        if lo >= hi:
            continue
        piece = formants(x[lo:hi], res)
        for i, s in enumerate(piece):
            t = lo + i
            w = 1.0 - abs(t - p * size) / size
            if w > 0.0:
                out[t] += w * s
    return out


def falling_bandpass(x, from_hz, to_hz, q, chunk_ms=15.0):
    """A band-pass whose centre walks from from_hz to to_hz, a chunk at a time and cross-faded."""
    n = len(x)
    size = samples(chunk_ms)
    pieces = max(1, n // size)
    out = [0.0] * n
    for p in range(pieces + 1):
        u = min(1.0, p / max(1, pieces))
        hz = from_hz * (to_hz / from_hz) ** u
        lo = max(0, (p - 1) * size)
        hi = min(n, (p + 1) * size)
        if lo >= hi:
            continue
        piece = bandpass(x[lo:hi], hz, q)
        for i, s in enumerate(piece):
            t = lo + i
            w = 1.0 - abs(t - p * size) / size
            if w > 0.0:
                out[t] += w * s
    return out


def shimmer(n, low, high, rate, rng):
    """Airy high noise between low and high Hz, fluttering at `rate` Hz."""
    air = bandpass(highpass(noise(n, rng), low), (low + high) / 2.0, 1.2)
    return [s * (0.55 + 0.45 * math.sin(2.0 * math.pi * rate * i / SR)) for i, s in enumerate(air)]


def voice(n, pitch_points, jitter, sub, rng, pulse_ms=0.8):
    """His voice's source: sharp glottal pulses along (ms, Hz) points, rough by `jitter`, with every other pulse
    quietened by `sub` for a growl an octave down."""
    return pulse_train(contour(n, pitch_points), pulse_ms, [jitter] * n, [sub] * n, rng)


AH = [(820, 3.0, 1.0), (1250, 4.0, 0.7), (2600, 5.0, 0.35)]
RR = [(480, 3.0, 1.0), (1350, 4.0, 0.55), (1700, 6.0, 0.3)]


# ------------------------------------------------------------------------------------------------- the sounds

def teleport_out():
    """He squeezes out: a sine dropping 180 to 80 Hz under an airy 4-6 kHz shimmer."""
    rng = random.Random(701)
    n = samples(220)
    body = sweep(n, [(0, 180), (220, 80)])
    air = shimmer(n, 4000, 6000, 38.0, rng)
    return mul(mix((1.0, body), (0.35, air)), envelope(n, 4, 60, decay_ms=160))


def teleport_in():
    """He reforms: the same thing rising, 80 to 180 Hz."""
    rng = random.Random(702)
    n = samples(220)
    body = sweep(n, [(0, 80), (220, 180)])
    air = shimmer(n, 4000, 6000, 38.0, rng)
    swell = [min(1.0, (i / n) * 1.6) for i in range(n)]
    return mul(mix((1.0, body), (0.35, air)), mul(swell, envelope(n, 10, 30)))


def mystic_fire():
    """"HA!": a short bark on 220 Hz pulses, with a zap climbing 1.2 to 2.4 kHz and a glassy ring on top."""
    rng = random.Random(703)
    n = samples(320)
    bark_n = samples(130)
    bark = formants(voice(bark_n, [(0, 225), (130, 205)], 0.02, 0.1, rng), AH)
    bark = mul(saturate(normalized(bark), 1.8), envelope(bark_n, 2, 50, decay_ms=90))
    zap_n = samples(160)
    zap = mul(sweep(zap_n, [(0, 1200), (160, 2400)]), envelope(zap_n, 1, 40, decay_ms=70))
    crystal = mix(*[(a, oscillator([f] * n, [(1, 1.0)])) for f, a in ((3150, 0.5), (4420, 0.35), (6230, 0.2))])
    crystal = mul(crystal, envelope(n, 2, 80, decay_ms=110))
    return mix((1.0, bark), (0.55, zap), (0.35, delayed(crystal, 15)[:n]))


def mystic_bounce():
    """A bolt off the rope: two glassy pings, 3.2 and 4.7 kHz, a hair out of tune with each other."""
    n = samples(140)
    ping = mix((1.0, oscillator([3200.0] * n, [(1, 1.0)])), (0.6, oscillator([4715.0] * n, [(1, 1.0)])))
    return mul(ping, envelope(n, 1, 50, decay_ms=45))


def mystic_fizzle():
    """A bolt burning out: crackle through a band-pass falling from 4 kHz to 800 Hz."""
    rng = random.Random(704)
    n = samples(360)
    crackle = [rng.uniform(-1.0, 1.0) if rng.random() < 0.08 else 0.0 for _ in range(n)]
    hiss = [0.15 * s for s in noise(n, rng)]
    return mul(falling_bandpass(mix((1.0, crackle), (1.0, hiss)), 4000.0, 800.0, 2.0), envelope(n, 3, 120, decay_ms=220))


def trueshot_charge():
    """The megaphone filling: a breath swelling in under a chord that climbs a fifth."""
    rng = random.Random(705)
    n = samples(900)
    swell = [(i / n) ** 1.4 for i in range(n)]
    breath = mul(bandpass(noise(n, rng), 1400, 0.8), swell)
    rise = contour(n, [(0, 1.0), (900, 1.5)])
    chord = mix(*[(a, oscillator([f * r for r in rise], [(1, 1.0), (2, 0.25)])) for f, a in ((220, 1.0), (277.2, 0.7), (330, 0.8))])
    chord = mul(chord, [0.3 + 0.7 * s for s in swell])
    return mul(mix((0.6, breath), (0.8, chord)), envelope(n, 20, 40))


def trueshot_lock():
    """The aim latching: a small bell at 1.8 kHz."""
    n = samples(420)
    bell = mix(*[(a, mul(oscillator([1800.0 * r] * n, [(1, 1.0)]), envelope(n, 1, 20, decay_ms=d)))
                 for r, a, d in ((1.0, 1.0, 160), (2.76, 0.45, 70), (5.4, 0.2, 35))])
    return bell


def trueshot_fire():
    """The wave leaving: a saturated "HAAA" climbing 180 to 240 Hz, a 60 Hz thump, and a whoosh 300 Hz to 3 kHz."""
    rng = random.Random(706)
    n = samples(560)
    shout_n = samples(420)
    shout = formants(voice(shout_n, [(0, 180), (120, 240), (420, 225)], 0.03, 0.15, rng), AH)
    shout = mul(saturate(normalized(shout), 2.4), envelope(shout_n, 4, 140, decay_ms=380))
    thump_n = samples(180)
    thump = mul(sweep(thump_n, [(0, 72), (180, 48)]), envelope(thump_n, 2, 80, decay_ms=70))
    whoosh = mul(falling_bandpass(noise(n, rng), 300.0, 3000.0, 1.6), envelope(n, 30, 200, decay_ms=260))
    return mix((1.0, shout), (0.9, thump), (0.55, whoosh))


def yell_tell():
    """A sharp breath in: noise through a band rising from 900 Hz to 3 kHz, swelling fast."""
    rng = random.Random(707)
    n = samples(300)
    breath = falling_bandpass(noise(n, rng), 900.0, 3000.0, 1.4)
    swell = [min(1.0, (i / n) * 1.3) ** 1.5 for i in range(n)]
    return mul(breath, mul(swell, envelope(n, 5, 25)))


def yell():
    """His yell: a brutal 0.6 s shout, rough and saturated, on a sub thump."""
    rng = random.Random(708)
    n = samples(620)
    shout = formants(voice(n, [(0, 210), (80, 262), (420, 248), (620, 205)], 0.05, 0.3, rng), AH)
    wobble = wander(n, 18.0, rng)
    shout = mul(saturate(normalized(shout), 3.0), [1.0 - 0.18 * w for w in wobble])
    shout = mul(shout, envelope(n, 3, 160, decay_ms=900))
    thump_n = samples(240)
    thump = mul(sweep(thump_n, [(0, 58), (240, 40)]), envelope(thump_n, 2, 100, decay_ms=110))
    return mix((1.0, shout), (1.0, thump))


def roar():
    """The roar: 2.2 s of pulses climbing 150 to 230 Hz and settling at 190, rough with jitter, an "AAAH" gliding
    into an "RRR", a growl an octave down, a 40-60 Hz rumble and a delayed tail off the back of the arena."""
    rng = random.Random(709)
    n = samples(2200)
    source = pulse_train(contour(n, [(0, 150), (350, 205), (800, 230), (1500, 215), (2200, 190)]), 0.9,
                         contour(n, [(0, 0.03), (1200, 0.04), (2200, 0.08)]),
                         contour(n, [(0, 0.35), (900, 0.2), (2200, 0.45)]), rng)
    tract = gliding_formants(source, AH, RR)
    body = saturate(normalized(tract), 2.6)
    ragged = wander(n, 11.0, rng)
    shape = contour(n, [(0, 0.0), (40, 1.0), (1500, 0.95), (2000, 0.55), (2200, 0.0)])
    body = mul(body, [s * (1.0 - 0.2 * r) for s, r in zip(shape, ragged)])
    rumble = mul(sweep(n, [(0, 60), (1100, 48), (2200, 40)]), contour(n, [(0, 0.0), (60, 1.0), (1800, 0.8), (2200, 0.0)]))
    air = mul(bandpass(noise(n, rng), 1600, 0.6), contour(n, [(0, 0.0), (30, 0.8), (400, 0.35), (2200, 0.0)]))
    dry = mix((1.0, body), (0.55, rumble), (0.35, air))
    tail = mix((1.0, dry), (0.22, lowpass(delayed(dry, 180), 1800)), (0.12, lowpass(delayed(dry, 340), 1100)))
    return tail


def scream_hong():
    """Screaming at a doll: the roar's voice, low-passed at 1.5 kHz and trembling, for 1.6 s."""
    rng = random.Random(710)
    n = samples(1600)
    source = pulse_train(contour(n, [(0, 240), (300, 290), (1200, 275), (1600, 250)]), 0.7,
                         [0.05] * n, [0.25] * n, rng)
    shout = saturate(normalized(formants(source, AH)), 2.2)
    tremble = [0.72 + 0.28 * math.sin(2.0 * math.pi * 9.5 * i / SR) for i in range(n)]
    shape = contour(n, [(0, 0.0), (60, 1.0), (1300, 0.9), (1600, 0.0)])
    return lowpass(lowpass(mul(shout, mul(tremble, shape)), 1500), 2200)


def recover():
    """Hands on his knees: four hoarse breaths, in and out."""
    rng = random.Random(711)
    parts = []
    for k in range(4):
        for inhale in (True, False):
            n = samples(160 if inhale else 220)
            hz = 1900 if inhale else 1100
            breath = bandpass(noise(n, rng), hz, 1.1)
            rasp = bandpass(noise(n, rng), 650, 3.0)
            env = envelope(n, 40 if inhale else 15, 60, decay_ms=None if inhale else 180)
            parts.append(mul(mix((1.0, breath), (0.6, rasp)), env))
            parts.append([0.0] * samples(40 if inhale else 90))
    return [s for part in parts for s in part]


# ------------------------------------------------------------------------------------------------- the Glass Row

def slap(n, rng, hz=1300.0):
    """A flat hand on the canvas: a burst of noise, gone in a few tens of ms."""
    return mul(bandpass(highpass(noise(n, rng), 300.0), hz, 0.7), envelope(n, 1, 20, decay_ms=18))


def pings(n, count, low, high, spread_ms, decay_ms, rng):
    """`count` glassy pings between low and high Hz, scattered over the first spread_ms."""
    out = [0.0] * n
    for _ in range(count):
        hz = rng.uniform(low, high)
        start = samples(rng.uniform(0.0, spread_ms))
        length = n - start
        if length <= 0:
            continue
        ping = mul(oscillator([hz] * length, [(1, 1.0), (2.76, 0.25)]), envelope(length, 1, 10, decay_ms=decay_ms))
        gain = rng.uniform(0.4, 1.0)
        for i, s in enumerate(ping):
            out[start + i] += gain * s
    return out


def bell(n, hz, decay_ms):
    """A small bell on `hz`, its partials dying faster than the note."""
    return mix(*[(a, mul(oscillator([hz * r] * n, [(1, 1.0)]), envelope(n, 1, 20, decay_ms=decay_ms * d)))
                 for r, a, d in ((1.0, 1.0, 1.0), (2.76, 0.4, 0.45), (5.4, 0.15, 0.22))])


def stomp():
    """The stomp that roots the player: a "HUP!", a slap on the canvas, a sine falling 70 to 38 Hz and a 150 Hz
    rumble under it. 0.7 s."""
    rng = random.Random(721)
    n = samples(700)
    hup_n = samples(120)
    hup = formants(voice(hup_n, [(0, 190), (120, 170)], 0.03, 0.2, rng), AH)
    hup = mul(saturate(normalized(hup), 2.0), envelope(hup_n, 3, 50, decay_ms=70))
    drop_n = samples(350)
    drop = mul(sweep(drop_n, [(0, 70), (350, 38)]), envelope(drop_n, 2, 120, decay_ms=200))
    rumble = mul(sweep(n, [(0, 150), (700, 120)]), envelope(n, 10, 300, decay_ms=240))
    return mix((0.55, hup), (0.8, delayed(slap(samples(90), rng), 60)), (1.0, delayed(drop, 60)), (0.35, delayed(rumble, 60)))


def root_clamp():
    """The sound shackle closing: a 110 Hz "thoom" trembling at 7 Hz, and a metallic ring at 740 and 1130 Hz."""
    n = samples(650)
    thoom = oscillator([110.0] * n, [(1, 1.0), (2, 0.3)])
    tremolo = [0.6 + 0.4 * math.sin(2.0 * math.pi * 7.0 * i / SR) for i in range(n)]
    thoom = mul(mul(thoom, tremolo), envelope(n, 8, 200, decay_ms=300))
    ring = mix((1.0, oscillator([740.0] * n, [(1, 1.0)])), (0.7, oscillator([1130.0] * n, [(1, 1.0)])))
    ring = mul(ring, envelope(n, 2, 120, decay_ms=260))
    return mix((1.0, thoom), (0.35, ring))


def fury_stomp():
    """One of the fury's stamps: a sine falling 90 to 50 Hz over 0.12 s, and a slap."""
    rng = random.Random(722)
    n = samples(180)
    drop = mul(sweep(n, [(0, 90), (120, 50)]), envelope(n, 2, 60, decay_ms=70))
    return mix((1.0, drop), (0.6, slap(samples(70), rng)))


def glass_fall():
    """A shard coming down from the ceiling: band noise falling 5 to 2 kHz over 0.35 s."""
    rng = random.Random(723)
    n = samples(350)
    return mul(falling_bandpass(noise(n, rng), 5000.0, 2000.0, 2.5), envelope(n, 60, 40))


def glass_land():
    """A shard landing: a 5 ms crack and five to seven pings between 3 and 8 kHz."""
    rng = random.Random(724)
    n = samples(260)
    crack = highpass(noise(samples(5), rng), 3000.0)
    return mix((0.8, crack), (0.6, pings(n, rng.randint(5, 7), 3000.0, 8000.0, 30.0, 40.0, rng)))


def glass_shatter():
    """The player into the glass: a 60 Hz thud, noise high-passed at 2 kHz, and thirty pings between 2 and 9 kHz
    spread over 0.6 s."""
    rng = random.Random(725)
    n = samples(750)
    thud_n = samples(220)
    thud = mul(sweep(thud_n, [(0, 68), (220, 52)]), envelope(thud_n, 2, 80, decay_ms=90))
    hiss = mul(highpass(noise(n, rng), 2000.0), envelope(n, 1, 200, decay_ms=180))
    return mix((1.0, thud), (0.45, hiss), (0.5, pings(n, 30, 2000.0, 9000.0, 600.0, 55.0, rng)))


def glass_clear():
    """The glass going: pings climbing 3 to 7 kHz across 0.5 s."""
    n = samples(620)
    out = [0.0] * n
    for k in range(10):
        hz = 3000.0 * (7000.0 / 3000.0) ** (k / 9.0)
        start = samples(50.0 * k)
        length = n - start
        ping = mul(oscillator([hz] * length, [(1, 1.0), (2.76, 0.2)]), envelope(length, 1, 10, decay_ms=45))
        for i, s in enumerate(ping):
            out[start + i] += 0.8 * s
    return out


def boom_form():
    """A boom forming at his mouth: a "whum" swelling as it climbs 90 to 180 Hz."""
    n = samples(620)
    whum = oscillator(contour(n, [(0, 90), (620, 180)]), [(1, 1.0), (2, 0.45), (3, 0.2)])
    swell = [(i / n) ** 1.2 for i in range(n)]
    return mul(mul(whum, swell), envelope(n, 20, 40))


def n_wave(n):
    """A sonic boom's crack: the pressure jumps up, ramps straight down through zero and snaps back."""
    return [1.0 - 2.0 * i / max(1, n - 1) for i in range(n)]


def boom_fire():
    """The boom cracking down the lane: an N-wave twice over, a "BWAH" on 180 Hz, and a whoosh climbing 400 Hz to
    2.5 kHz."""
    rng = random.Random(726)
    n = samples(520)
    crack = n_wave(samples(4))
    cracks = mix((1.0, crack), (0.8, delayed(crack, 26)))
    bwah_n = samples(260)
    bwah = formants(voice(bwah_n, [(0, 175), (80, 190), (260, 170)], 0.03, 0.2, rng), AH)
    bwah = mul(saturate(normalized(bwah), 2.2), envelope(bwah_n, 4, 90, decay_ms=160))
    whoosh = mul(falling_bandpass(noise(n, rng), 400.0, 2500.0, 1.6), envelope(n, 20, 200, decay_ms=220))
    return mix((0.9, cracks), (0.9, delayed(bwah, 10)), (0.5, whoosh))


def boom_answer():
    """An arrow answered: a bell on 1568 Hz, then 2093 Hz."""
    n = samples(420)
    first = bell(n, 1568.0, 150)
    second = delayed(bell(n - samples(80), 2093.0, 170), 80)
    return mix((0.8, first), (1.0, second))


def boom_wrong():
    """A wrong arrow: detuned square waves on 110 and 117 Hz for 0.18 s."""
    n = samples(180)
    square = [(k, 1.0 / k) for k in (1, 3, 5, 7, 9, 11, 13)]
    buzz = mix((1.0, oscillator([110.0] * n, square)), (1.0, oscillator([117.0] * n, square)))
    return mul(lowpass(buzz, 2500), envelope(n, 3, 20))


def boom_block():
    """A boom breaking on the braced player: a sine falling 140 to 70 Hz, and air."""
    rng = random.Random(727)
    n = samples(260)
    drop = mul(sweep(n, [(0, 140), (260, 70)]), envelope(n, 2, 90, decay_ms=110))
    air = mul(bandpass(noise(n, rng), 2600, 0.8), envelope(n, 2, 60, decay_ms=60))
    return mix((1.0, drop), (0.35, air))


def boom_hit():
    """A boom landing on an unanswered player: a sine falling 80 to 40 Hz, and the whoosh of the shove."""
    rng = random.Random(728)
    n = samples(420)
    drop = mul(sweep(n, [(0, 80), (420, 40)]), envelope(n, 2, 150, decay_ms=170))
    shove = mul(falling_bandpass(noise(n, rng), 1800.0, 500.0, 1.4), envelope(n, 5, 200, decay_ms=180))
    return mix((1.0, drop), (0.5, shove))


def deafen_tell():
    """The Deafening Yell's breath in: noise through a band rising 700 Hz to 2.6 kHz, swelling over 0.5 s."""
    rng = random.Random(729)
    n = samples(500)
    breath = falling_bandpass(noise(n, rng), 700.0, 2600.0, 1.3)
    swell = [(i / n) ** 1.8 for i in range(n)]
    return mul(breath, mul(swell, envelope(n, 5, 30)))


def deafen_yell():
    """The Deafening Yell: 3 s of the roar's voice climbing 160 to 260 Hz, saturated, over a 45 Hz sub and a
    ripping 3 kHz band."""
    rng = random.Random(730)
    n = samples(3000)
    source = pulse_train(contour(n, [(0, 160), (600, 210), (2200, 250), (3000, 260)]), 0.9,
                         contour(n, [(0, 0.03), (1500, 0.05), (3000, 0.07)]), [0.3] * n, rng)
    body = saturate(normalized(gliding_formants(source, AH, RR)), 2.2)
    ragged = wander(n, 13.0, rng)
    shape = contour(n, [(0, 0.0), (60, 1.0), (2600, 0.95), (3000, 0.0)])
    body = mul(body, [s * (1.0 - 0.18 * r) for s, r in zip(shape, ragged)])
    sub = mul(oscillator([45.0] * n, [(1, 1.0)]), contour(n, [(0, 0.0), (100, 1.0), (2700, 0.9), (3000, 0.0)]))
    rip = bandpass(noise(n, rng), 3000, 2.0)
    rip = mul(rip, [0.5 + 0.5 * math.sin(2.0 * math.pi * 23.0 * i / SR) for i in range(n)])
    rip = mul(rip, contour(n, [(0, 0.0), (200, 0.8), (2800, 0.8), (3000, 0.0)]))
    return mix((1.0, body), (0.6, sub), (0.3, rip))


def ear_ring():
    """A deafened player's ears ringing: 3.9 kHz wavering by 15 Hz, with 3.1 kHz under it, fading over 2.5 s."""
    n = samples(2500)
    waver = [3900.0 + 15.0 * math.sin(2.0 * math.pi * 5.0 * i / SR) for i in range(n)]
    tone = mix((1.0, oscillator(waver, [(1, 1.0)])), (0.5, oscillator([3100.0] * n, [(1, 1.0)])))
    return mul(tone, envelope(n, 30, 300, decay_ms=900))


def resist():
    """Mashed through the yell: a whoosh and a chime on 1318 Hz."""
    rng = random.Random(731)
    n = samples(560)
    whoosh = mul(falling_bandpass(noise(n, rng), 600.0, 3000.0, 1.5), envelope(n, 20, 150, decay_ms=160))
    chime = delayed(bell(n - samples(60), 1318.0, 200), 60)
    return mix((0.6, whoosh), (1.0, chime))


SOUNDS = {
    "teleport_out": teleport_out,
    "teleport_in": teleport_in,
    "mystic_fire": mystic_fire,
    "mystic_bounce": mystic_bounce,
    "mystic_fizzle": mystic_fizzle,
    "trueshot_charge": trueshot_charge,
    "trueshot_lock": trueshot_lock,
    "trueshot_fire": trueshot_fire,
    "yell_tell": yell_tell,
    "yell": yell,
    "roar": roar,
    "scream_hong": scream_hong,
    "recover": recover,
    "stomp": stomp,
    "root_clamp": root_clamp,
    "fury_stomp": fury_stomp,
    "glass_fall": glass_fall,
    "glass_land": glass_land,
    "glass_shatter": glass_shatter,
    "glass_clear": glass_clear,
    "boom_form": boom_form,
    "boom_fire": boom_fire,
    "boom_answer": boom_answer,
    "boom_wrong": boom_wrong,
    "boom_block": boom_block,
    "boom_hit": boom_hit,
    "deafen_tell": deafen_tell,
    "deafen_yell": deafen_yell,
    "ear_ring": ear_ring,
    "resist": resist,
}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    ship = sys.argv[1] == "--ship"
    folder = SFX_DIR if ship else sys.argv[1]
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].split(",")
        unknown = [name for name in only if name not in SOUNDS]
        if unknown:
            print("no such sound: %s" % ", ".join(unknown))
            return
    os.makedirs(folder, exist_ok=True)
    for name, make in SOUNDS.items():
        if only is not None and name not in only:
            continue
        sound = finish(make())
        path = os.path.join(folder, ("matt_%s.wav" if ship else "preview_matt_%s.wav") % name)
        write_wav(path, sound)
        print("%-40s %5d ms  peak %5.1f dBFS" % (os.path.basename(path), round(len(sound) * 1000 / SR),
                                                20.0 * math.log10(max(abs(s) for s in sound))))


if __name__ == "__main__":
    main()
