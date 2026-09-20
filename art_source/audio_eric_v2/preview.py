"""Mixes the Eric V2 finisher sounds into one listen-through of a tier-3 finisher.

    python preview.py OUT_DIR DECODED_DIR

Reads the shipped WAVs from Assets/Audio/SFX and hit_impact.wav from DECODED_DIR (hit_impact.ogg decoded through
Godot by punch_fx/dump_audio.gd), and writes OUT_DIR/preview_eric_v2_finisher.wav. Every sound plays at 0 dB, as
the game plays them, and the whole file is only turned down if the sum would clip (the existing super contact
already does: two full-scale hits land together). The timeline follows eric_pacing_plan.md with the waits cut short:

  the Break           break_sting
  (Broken, the snap-in and the opener are skipped: a short gap)
  the mash            finisher_charge_loop from the prompt, its pitch 1.0 + 0.2 * m_s, where m_s comes from the
                      plan's meter model (section 3.3) mashed at 12 presses a second: +0.20 a press, draining
                      0.75 / 1.0 / 1.2 a second, never below the banked bars, banking snaps, smoothed over
                      0.12 s. That banks the bars at 0.50, 1.17 and 1.92 s (the floor swallows the first drain
                      after each bank, so bars 2 and 3 come a press sooner than the plan's table), each with its
                      clunk; the loop stops on bar 3 with Godot's stop fade.
  the juggle          hits at 0.11, 0.66 and 1.21 s of game time plus the 0.10 s hit-stops before them:
                      hit_impact at pitch 1.12 and 1.26 (placeholders for "pitched up with each hit"), then the
                      special: hit_impact at 1.4, the super impact's fallback (hit_impact at 0.7) and
                      knight_breaker_sting together
  the crash           eric_crash_thud 0.35 s of hit-stop plus 0.84 s of fall after the special
"""

import math
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import dsp  # noqa: E402
from dsp import SR, samples  # noqa: E402
from make_eric_v2_sfx import SFX_DIR  # noqa: E402

FPS = 60
PRESS_EVERY = 5          # frames: 12 presses a second, the plan's tier-3 pass rate
PRESS_GAIN = 0.20
DRAINS = [0.75, 1.0, 1.2]
SMOOTH_S = 0.12
# Godot fades a stopped stream out over one mix step.
STOP_FADE = 512

BREAK_AT_MS = 250.0
MASH_AT_MS = 1900.0
JUGGLE_HITS_S = [0.11, 0.66, 1.21]
HIT_STOPS_S = [0.10, 0.10, 0.35]
JUGGLE_PITCHES = [1.12, 1.26, 1.4]
SUPER_PITCH = 0.7
FALL_S = 0.84


def mash_pitches():
    """(loop pitch per 60 fps frame, bank frames) for a tier-3 mash, per the plan's model."""
    meter = smooth = 0.0
    banked = 0
    pitches, banks = [], []
    frame = 0
    dt = 1.0 / FPS
    while banked < 3:
        if frame > 0:
            meter = max(float(banked), meter - DRAINS[banked] * dt)
        if frame % PRESS_EVERY == 0:
            meter += PRESS_GAIN
            if meter >= banked + 1 - 1e-6:
                banked += 1
                meter = float(banked)
                banks.append(frame)
        smooth += (meter - smooth) * (1.0 - math.exp(-dt / SMOOTH_S))
        pitches.append(1.0 + 0.2 * max(float(banked), smooth))
        frame += 1
    return pitches, banks


def loop_with_pitch(x, loop, pitches):
    """The loop through Godot 4.6's playback (dsp.godot_resample's model) with its pitch changing every frame,
    then Godot's stop fade."""
    one = 1 << 16
    per_frame = SR // FPS
    total = sum(int(p * one) for p in pitches) * per_frame
    q = [max(-32768, min(32767, int(round(s * 32767.0)))) / 32767.0 for s in x]
    buf = [0.0] * 4 + dsp.godot_native(q, (total >> 16) + 8, loop)
    out = []
    offset = 0
    for pitch in pitches:
        step = int(pitch * one)
        for _ in range(per_frame):
            idx = 4 + (offset >> 16)
            mu = (offset & (one - 1)) / one
            y0, y1, y2, y3 = buf[idx - 3], buf[idx - 2], buf[idx - 1], buf[idx]
            mu2 = mu * mu
            h11 = mu2 * (mu - 1.0)
            z = mu2 - h11
            out.append(y1 + (y2 - y1) * (z - h11) + ((y2 - y0) * (mu - z) + (y3 - y1) * h11) * 0.5)
            offset += step
    tail = out[-STOP_FADE:]
    out[-STOP_FADE:] = [s * (1.0 - k / STOP_FADE) for k, s in enumerate(tail)]
    return out


def main():
    out_dir, decoded_dir = sys.argv[1], sys.argv[2]
    sfx = {}
    for name in ("finisher_charge_loop", "finisher_bar_1", "finisher_bar_2", "finisher_bar_3", "break_sting",
                 "eric_crash_thud", "knight_breaker_sting"):
        sfx[name] = dsp.read_wav_file(os.path.join(SFX_DIR, name + ".wav"))
    hit = dsp.read_wav_file(os.path.join(decoded_dir, "hit_impact.wav"))[0]

    def pitched(x, rate):
        return dsp.godot_resample(x, rate, int(len(x) / rate))

    pitches, banks = mash_pitches()
    bank_ms = [MASH_AT_MS + 1000.0 * f / FPS for f in banks]
    special_ms = bank_ms[2] + 1000.0 * (JUGGLE_HITS_S[2] + HIT_STOPS_S[0] + HIT_STOPS_S[1])
    crash_ms = special_ms + 1000.0 * (HIT_STOPS_S[2] + FALL_S)
    mix = [0.0] * samples(crash_ms + 1800.0)

    events = [(BREAK_AT_MS, "break_sting", sfx["break_sting"][0])]
    events.append((MASH_AT_MS, "finisher_charge_loop (pitch %.2f -> %.2f)" % (pitches[0], pitches[-1]),
                   loop_with_pitch(*sfx["finisher_charge_loop"], pitches)))
    for k, at in enumerate(bank_ms, 1):
        events.append((at, "finisher_bar_%d" % k, sfx["finisher_bar_%d" % k][0]))
    for k in range(2):
        at = bank_ms[2] + 1000.0 * (JUGGLE_HITS_S[k] + sum(HIT_STOPS_S[:k]))
        events.append((at, "juggle hit %d: hit_impact at %.2f" % (k + 1, JUGGLE_PITCHES[k]),
                       pitched(hit, JUGGLE_PITCHES[k])))
    events.append((special_ms, "special: hit_impact at %.2f" % JUGGLE_PITCHES[2], pitched(hit, JUGGLE_PITCHES[2])))
    events.append((special_ms, "special: super impact fallback, hit_impact at %.2f" % SUPER_PITCH,
                   pitched(hit, SUPER_PITCH)))
    events.append((special_ms, "special: knight_breaker_sting", sfx["knight_breaker_sting"][0]))
    events.append((crash_ms, "eric_crash_thud", sfx["eric_crash_thud"][0]))

    for at, label, x in events:
        dsp.place(mix, x, at)
        print("%7.0f ms  %s" % (at, label))

    # The special's contact with and without the sting, to show what the sting adds to the peak there.
    window = (samples(special_ms), samples(special_ms + 400.0))
    without = [0.0] * (window[1] - window[0])
    for x in (pitched(hit, JUGGLE_PITCHES[2]), pitched(hit, SUPER_PITCH)):
        for i, s in enumerate(x[:len(without)]):
            without[i] += s
    print("special contact peak: %.1f dBFS with the sting, %.1f dBFS without it" % (
        dsp.peak_db(mix[window[0]:window[1]]), dsp.peak_db(without)))
    for at, label, _ in events:
        start = samples(at)
        print("  peak within 150 ms of %-55s %5.1f dBFS" % (label, dsp.peak_db(mix[start:start + samples(150.0)])))
    peak = dsp.peak_db(mix)
    # The game's own super contact (two full-scale hits at once) already goes over full scale, so the file is
    # turned down as a whole rather than clipped: the balance between the sounds is what it is in the game.
    trim = min(0.0, -1.0 - peak)
    mix = [s * 10.0 ** (trim / 20.0) for s in mix]
    print("preview peak %.1f dBFS before trimming, trimmed %.1f dB to %.1f dBFS; %.2f s" % (
        peak, trim, dsp.peak_db(mix), len(mix) / SR))

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "preview_eric_v2_finisher.wav")
    with open(path, "wb") as f:
        f.write(dsp.wav_bytes(mix))
    print("wrote", path)


if __name__ == "__main__":
    main()
