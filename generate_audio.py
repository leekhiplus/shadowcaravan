#!/usr/bin/env python3
"""Procedural audio generator for Shadow Caravan.

Every sound effect, the ambience loops and the three music loops shipped in
assets/audio/ are synthesised by this script from scratch (sine/noise synthesis
only, no samples, no third-party material). They are therefore original works,
released under the project's MIT license (see ASSET_LICENSES.md).

Usage:  python3 tools/generate_audio.py            (requires numpy)
Output: assets/audio/*.wav  (mono, 16-bit, 22050 Hz, deterministic)
"""
import os
import wave

import numpy as np

SR = 22050
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "audio")
rng = np.random.default_rng(20261016)


# --------------------------------------------------------------------------- helpers
def ns(d):
    return int(SR * d)


def tt(d):
    return np.arange(ns(d)) / SR


def sine(f, d, ph=0.0):
    return np.sin(2 * np.pi * f * tt(d) + ph)


def decay(n, tau):
    return np.exp(-np.arange(n) / SR / tau)


def ar(n, a, tau):
    """Linear attack of `a` seconds followed by an exponential decay."""
    e = decay(n, tau)
    na = max(1, int(a * SR))
    e[:na] *= np.linspace(0.0, 1.0, na)
    return e


def sweep(f0, f1, d):
    n = ns(d)
    f = np.geomspace(f0, f1, n)
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def shaped_noise(d, f_lo, f_hi):
    """Smooth band-limited noise (FFT shaped, circular so it loops cleanly)."""
    n = ns(d)
    spec = np.fft.rfft(rng.standard_normal(n))
    fr = np.fft.rfftfreq(n, 1.0 / SR)
    lo = 1.0 / (1.0 + (f_lo / np.maximum(fr, 1.0)) ** 4) if f_lo > 0 else np.ones_like(fr)
    hi = 1.0 / (1.0 + (fr / f_hi) ** 4)
    out = np.fft.irfft(spec * lo * hi, n)
    return out / (np.max(np.abs(out)) + 1e-9)


def saw(f, d):
    return 2.0 * ((tt(d) * f) % 1.0) - 1.0


def square(f, d):
    return np.sign(np.sin(2 * np.pi * f * tt(d)))


def add(buf, sig, t0, gain=1.0, wrap=False):
    i = int(t0 * SR)
    n = len(sig)
    if wrap:
        idx = (np.arange(n) + i) % len(buf)
        np.add.at(buf, idx, sig * gain)
        return
    j = min(len(buf), i + n)
    if j > i:
        buf[i:j] += sig[: j - i] * gain


def save(name, x, peak=0.85, fade=True):
    x = np.asarray(x, dtype=np.float64)
    m = np.max(np.abs(x))
    if m > 0:
        x = x / m * peak
    if fade:
        k = min(len(x) // 4, int(0.004 * SR))
        x[:k] *= np.linspace(0, 1, k)
        x[-k:] *= np.linspace(1, 0, k)
    os.makedirs(OUT, exist_ok=True)
    data = (np.clip(x, -1, 1) * 32767).astype("<i2").tobytes()
    with wave.open(os.path.join(OUT, name + ".wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data)
    print(f"  {name:<16} {len(x) / SR:5.2f}s")


def hz(semi_from_a4):
    return 440.0 * 2 ** (semi_from_a4 / 12.0)


# --------------------------------------------------------------------------- sound effects
def sfx():
    # UI
    d = 0.07
    save("ui_click", sine(1500, d) * decay(ns(d), 0.02) + 0.25 * shaped_noise(d, 3000, 9000) * decay(ns(d), 0.008))
    d = 0.3
    save("ui_open", sweep(260, 620, d) * ar(ns(d), 0.04, 0.12) * 0.7 + sine(930, d) * ar(ns(d), 0.05, 0.1) * 0.25)
    d = 0.22
    save("ui_back", sweep(520, 240, d) * ar(ns(d), 0.01, 0.08))

    # combat
    d = 0.34
    sw = shaped_noise(d, 600, 5000) * np.sin(np.pi * np.clip(tt(d) / d, 0, 1)) ** 2
    save("sword_swing", sw * 0.9 + sweep(1100, 320, d) * 0.15 * ar(ns(d), 0.05, 0.1))
    d = 0.24
    save("hit_enemy", sweep(190, 55, d) * decay(ns(d), 0.07) + 0.8 * shaped_noise(d, 900, 4500) * decay(ns(d), 0.035))
    d = 0.32
    save("hit_player", sweep(130, 45, d) * decay(ns(d), 0.1)
         + 0.6 * shaped_noise(d, 100, 1400) * decay(ns(d), 0.07)
         + 0.2 * (sine(220, d) + sine(233, d)) * decay(ns(d), 0.06))
    d = 0.6
    save("enemy_die", sweep(420, 60, d) * decay(ns(d), 0.22) * 0.8 + 0.5 * shaped_noise(d, 200, 3000) * decay(ns(d), 0.15))
    d = 0.4
    save("roll", shaped_noise(d, 250, 1800) * np.sin(np.pi * np.clip(tt(d) / d, 0, 1)) ** 1.5)
    d = 0.17
    save("jump", sweep(240, 430, d) * ar(ns(d), 0.01, 0.07))
    for k in (1, 2):
        d = 0.13
        save(f"step{k}", shaped_noise(d, 200 * k, 2200 + 500 * k) * decay(ns(d), 0.035), peak=0.55)
    d = 0.5
    wob = 1 + 0.04 * np.sin(2 * np.pi * 9 * tt(d))
    save("projectile", sweep(760, 520, d) * wob * ar(ns(d), 0.05, 0.25) * 0.7 + 0.3 * shaped_noise(d, 800, 3000) * ar(ns(d), 0.1, 0.2))
    d = 1.4
    n = ns(d)
    growl = (0.6 + 0.4 * np.sin(2 * np.pi * 24 * tt(d))) * (saw(66, d) * 0.6 + saw(99, d) * 0.3)
    growl = growl * ar(n, 0.12, 0.55) + 0.7 * shaped_noise(d, 60, 700) * ar(n, 0.1, 0.5)
    save("boss_roar", growl)
    d = 1.0
    save("boss_slam", sweep(95, 32, d) * decay(ns(d), 0.35) + 0.7 * shaped_noise(d, 40, 600) * decay(ns(d), 0.28))
    d = 1.7
    n = ns(d)
    save("player_death", sweep(330, 55, d) * ar(n, 0.02, 0.7) * 0.7 + sine(55, d) * ar(n, 0.3, 0.9) * 0.6
         + 0.25 * shaped_noise(d, 100, 2000) * decay(n, 0.4))

    # pickups and magic
    d = 0.28
    c = np.zeros(ns(d))
    add(c, sine(1319, 0.2) * decay(ns(0.2), 0.08), 0.0)
    add(c, sine(1760, 0.2) * decay(ns(0.2), 0.09), 0.07)
    save("coin", c)
    d = 0.55
    c = np.zeros(ns(d))
    for i, f in enumerate((523, 659, 784)):
        add(c, sine(f, 0.4) * decay(ns(0.4), 0.12), 0.08 * i)
    save("pickup", c)
    d = 1.4
    n = ns(d)
    c = np.zeros(n)
    for i, f in enumerate((392, 587, 784, 1175, 1568)):
        trem = 1 + 0.25 * np.sin(2 * np.pi * (5 + i) * tt(1.2))
        add(c, sine(f, 1.2) * trem * ar(ns(1.2), 0.05, 0.5), 0.06 * i, 1.0 / (1 + 0.3 * i))
    c += 0.08 * shaped_noise(d, 4000, 9000) * ar(n, 0.2, 0.4)
    save("relic", c)
    d = 0.8
    n = ns(d)
    c = np.zeros(n)
    creak = (saw(95, 0.4) + saw(143, 0.4) * 0.5) * (0.5 + 0.5 * np.sin(2 * np.pi * 16 * tt(0.4))) * np.linspace(0.8, 0.2, ns(0.4))
    add(c, creak * 0.4, 0.0)
    add(c, sine(880, 0.4) * decay(ns(0.4), 0.12), 0.35)
    add(c, sine(1320, 0.4) * decay(ns(0.4), 0.1), 0.42, 0.6)
    save("chest", c)
    d = 0.6
    n = ns(d)
    c = np.zeros(n)
    for i in range(7):
        f = rng.uniform(280, 520) * (1 + i * 0.12)
        dd = 0.09
        add(c, sine(f, dd) * np.sin(np.pi * np.linspace(0, 1, ns(dd))) * 0.8, 0.06 * i)
    save("potion", c)
    d = 0.8
    n = ns(d)
    c = np.zeros(n)
    for i, f in enumerate((440, 554, 659, 880)):
        add(c, sine(f, 0.6) * ar(ns(0.6), 0.04, 0.3), 0.07 * i)
    c += 0.1 * sweep(300, 900, d) * ar(n, 0.1, 0.3)
    save("heal", c)
    d = 1.0
    c = np.zeros(ns(d))
    for i, f in enumerate((523, 659, 784, 1047)):
        add(c, (sine(f, 0.7) + 0.3 * sine(f * 2, 0.7)) * ar(ns(0.7), 0.02, 0.22), 0.1 * i)
    save("level_up", c)
    d = 2.6
    n = ns(d)
    c = np.zeros(n)
    prog = [((293.7, 349.2, 440.0), 0.0), ((329.6, 415.3, 493.9), 0.7), ((349.2, 440.0, 523.3), 1.4)]
    for chord, t0 in prog:
        for f in chord:
            tone = sine(f, 1.4) + 0.4 * sine(2 * f, 1.4) + 0.2 * sine(3 * f, 1.4)
            add(c, tone * ar(ns(1.4), 0.04, 0.55), t0, 0.5)
    for f, t0 in ((587.3, 1.4), (659.3, 1.6), (880.0, 1.8)):
        add(c, (sine(f, 0.9) + 0.4 * sine(2 * f, 0.9)) * ar(ns(0.9), 0.02, 0.4), t0, 0.5)
    save("quest_done", c)
    d = 0.9
    c = np.zeros(ns(d))
    add(c, (saw(220, 0.5) * 0.4 + sine(220, 0.5)) * ar(ns(0.5), 0.05, 0.25), 0.0)
    add(c, (saw(330, 0.5) * 0.4 + sine(330, 0.5)) * ar(ns(0.5), 0.05, 0.3), 0.3)
    save("quest_accept", c)

    # world mechanics
    d = 3.4
    n = ns(d)
    grind = shaped_noise(d, 180, 700) * (0.55 + 0.45 * np.sin(2 * np.pi * 6.5 * tt(d)))
    rumble = shaped_noise(d, 20, 140)
    env_ = np.sin(np.pi * np.clip(tt(d) / d, 0, 1)) ** 0.7
    save("gate_rumble", (grind * 0.6 + rumble * 1.0) * env_)
    d = 0.5
    n = ns(d)
    save("stone_turn", shaped_noise(d, 130, 520) * np.sin(np.pi * np.clip(tt(d) / d, 0, 1)) ** 0.8 + 0.5 * sine(58, d) * ar(n, 0.02, 0.2))
    d = 1.5
    c = np.zeros(ns(d))
    for f, t0 in ((261.6, 0.0), (329.6, 0.12), (392.0, 0.24), (523.3, 0.36), (784.0, 0.5)):
        add(c, (sine(f, 1.0) + 0.3 * sine(2 * f, 1.0)) * ar(ns(1.0), 0.03, 0.4), t0, 0.7)
    save("puzzle_ok", c)
    d = 0.55
    n = ns(d)
    save("puzzle_fail", (square(110, d) * 0.4 + square(116.5, d) * 0.4 + saw(55, d) * 0.3) * ar(n, 0.01, 0.2))
    d = 0.9
    save("rest", sine(220, d) * ar(ns(d), 0.2, 0.5) * 0.4 + sine(330, d) * ar(ns(d), 0.3, 0.5) * 0.3 + sine(440, d) * ar(ns(d), 0.4, 0.4) * 0.2)
    d = 0.4
    save("craft", shaped_noise(d, 1500, 7000) * decay(ns(d), 0.04) * 0.8 + sine(1200, d) * decay(ns(d), 0.06) * 0.5 + sine(1800, d) * decay(ns(d), 0.1) * 0.3)
    d = 0.3
    save("upgrade", sweep(300, 1200, d) * ar(ns(d), 0.01, 0.15) * 0.6 + sine(1500, d) * decay(ns(d), 0.12) * 0.4)


# --------------------------------------------------------------------------- ambience loops
def ambience():
    d = 10.0
    n = ns(d)
    t = tt(d)
    # circular noise + modulations whose frequency is an integer number of cycles -> seamless loop
    mod = 0.55 + 0.25 * np.sin(2 * np.pi * 3 / d * t + 1.0) + 0.2 * np.sin(2 * np.pi * 5 / d * t + 2.2)
    wind = shaped_noise(d, 120, 900) * mod
    hiss = shaped_noise(d, 1500, 4500) * (0.12 + 0.1 * np.sin(2 * np.pi * 2 / d * t))
    whistle = np.sin(2 * np.pi * np.cumsum(560 + 120 * np.sin(2 * np.pi * 4 / d * t)) / SR) * (0.5 + 0.5 * np.sin(2 * np.pi * 2 / d * t + 0.5)) ** 4 * 0.05
    amb = wind + hiss + whistle
    # sparse night insects (whole pulses placed well away from the loop edges)
    for t0 in (1.7, 3.9, 6.4, 8.2):
        dur = 0.7
        k = ns(dur)
        pulse = np.sin(2 * np.pi * 4300 * tt(dur)) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 22 * tt(dur)))) * np.sin(np.pi * np.linspace(0, 1, k)) ** 2
        add(amb, pulse * 0.035, t0)
    save("ambience", amb, peak=0.6, fade=False)

    d = 4.0
    n = ns(d)
    fire = shaped_noise(d, 40, 380) * 0.55 + shaped_noise(d, 900, 5000) * 0.07
    for _ in range(26):
        t0 = rng.uniform(0.1, d - 0.2)
        dur = rng.uniform(0.01, 0.035)
        k = ns(dur)
        pop = shaped_noise(dur, 500, 7000) * decay(k, dur / 4) * rng.uniform(0.2, 0.9)
        add(fire, pop, t0, 0.5)
    save("fire", fire, peak=0.6, fade=False)


# --------------------------------------------------------------------------- music
PHRYG = [0, 1, 4, 5, 7, 8, 10]  # D phrygian dominant intervals (semitones)
D2 = 73.416


def scale_note(degree, octave=0):
    """degree may exceed 6 to climb octaves."""
    oc, idx = divmod(degree, 7)
    return D2 * 2 ** ((PHRYG[idx] + 12 * (oc + octave)) / 12.0)


def pad(f, d, gain=1.0):
    t = tt(d)
    sig = np.zeros(len(t))
    for det in (0.996, 1.0, 1.004):
        sig += np.sin(2 * np.pi * f * det * t) + 0.35 * np.sin(2 * np.pi * 2 * f * det * t)
    n = len(t)
    a = int(0.35 * d * SR)
    e = np.ones(n)
    e[:a] = np.linspace(0, 1, a)
    e[n - a:] = np.linspace(1, 0, a)
    return sig * e * gain / 3.0


def pluck(f, d=1.2):
    n = ns(d)
    t = tt(d)
    sig = np.zeros(n)
    for h, a, tau in ((1, 1.0, 0.45), (2, 0.5, 0.3), (3, 0.3, 0.2), (4, 0.15, 0.12), (5, 0.08, 0.08)):
        sig += a * np.sin(2 * np.pi * f * h * t) * np.exp(-t / tau)
    sig[: int(0.002 * SR)] *= np.linspace(0, 1, int(0.002 * SR))
    return sig


def bell(f, d=3.0):
    t = tt(d)
    sig = np.zeros(len(t))
    for r, a, tau in ((1.0, 1.0, 1.4), (2.76, 0.4, 0.8), (5.4, 0.2, 0.4), (8.93, 0.08, 0.2)):
        sig += a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / tau)
    return sig


def bass(f, d=0.5):
    t = tt(d)
    return (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * 2 * f * t)) * np.exp(-t / (d * 0.5))


def kick(d=0.3):
    return sweep(130, 45, d) * decay(ns(d), 0.09)


def tek(d=0.12):
    return shaped_noise(d, 1800, 8000) * decay(ns(d), 0.025)


def tom(f=110, d=0.35):
    return sweep(f * 1.6, f, d) * decay(ns(d), 0.12)


def music_menu():
    d = 32.0
    buf = np.zeros(ns(d))
    chords = [(0, 2, 4), (1, 3, 5), (0, 2, 4), (6, 1, 3)]  # scale degrees (stacked thirds)
    for i, ch in enumerate(chords):
        for deg in ch:
            add(buf, pad(scale_note(deg, 1), 8.8, 0.6), i * 8.0, 1.0, wrap=True)
    add(buf, pad(scale_note(0, -0.0) / 2, d - 0.0, 0.35)[: len(buf)], 0.0)
    r = np.random.default_rng(7)
    for t0 in (2.0, 5.5, 9.0, 12.5, 16.0, 19.5, 23.0, 27.5, 30.0):
        deg = int(r.choice([0, 2, 4, 5, 7, 9, 11]))
        add(buf, bell(scale_note(deg, 2)), t0, 0.22, wrap=True)
    save("music_menu", buf, peak=0.7, fade=False)


def music_world():
    bpm = 72
    beat = 60.0 / bpm
    bars = 8
    d = beat * 4 * bars
    buf = np.zeros(ns(d))
    # drone
    add(buf, pad(scale_note(0, 0), d, 0.4)[: len(buf)], 0.0)
    add(buf, pad(scale_note(4, 0), d, 0.25)[: len(buf)], 0.0)
    for bar in range(bars):
        t0 = bar * 4 * beat
        add(buf, kick(), t0, 0.9, wrap=True)
        add(buf, kick(), t0 + 2.5 * beat, 0.7, wrap=True)
        add(buf, tek(), t0 + 1.0 * beat, 0.35, wrap=True)
        add(buf, tek(), t0 + 3.0 * beat, 0.35, wrap=True)
        add(buf, tom(150), t0 + 3.5 * beat, 0.4, wrap=True)
        add(buf, bass(scale_note(0, 0), 0.9), t0, 0.5, wrap=True)
        if bar % 2 == 1:
            add(buf, bass(scale_note(1, 0), 0.9), t0 + 2 * beat, 0.45, wrap=True)
    motif = [(0, 0.0), (1, 0.75), (2, 1.5), (3, 2.0), (2, 2.75), (1, 3.25),
             (0, 4.0), (4, 5.0), (3, 6.0), (2, 6.5), (1, 7.0), (0, 7.5)]
    for rep in range(bars // 2):
        for deg, pos in motif:
            add(buf, pluck(scale_note(deg + 7, 0), 1.4), rep * 8 * beat + pos * beat, 0.5, wrap=True)
    for t0 in (7.0, 19.0):
        add(buf, bell(scale_note(4, 2), 4.0), t0, 0.12, wrap=True)
    save("music_world", buf, peak=0.7, fade=False)


def music_boss():
    bpm = 126
    beat = 60.0 / bpm
    bars = 10
    d = beat * 4 * bars
    buf = np.zeros(ns(d))
    add(buf, pad(scale_note(0, 0), d, 0.45)[: len(buf)], 0.0)
    add(buf, pad(scale_note(0, 0) * 2 ** (6 / 12), d, 0.25)[: len(buf)], 0.0)  # tritone tension
    for bar in range(bars):
        t0 = bar * 4 * beat
        for k in range(8):
            f = scale_note(0 if (k % 4) != 3 else 1, 0)
            add(buf, bass(f, 0.28), t0 + k * 0.5 * beat, 0.55, wrap=True)
        for k in (0, 1.5, 2, 3.5):
            add(buf, kick(), t0 + k * beat, 0.9, wrap=True)
        for k in (1, 3):
            add(buf, tek(0.16), t0 + k * beat, 0.5, wrap=True)
        for k in (0.5, 2.5, 3.75):
            add(buf, tom(120 + 25 * (k > 3)), t0 + k * beat, 0.35, wrap=True)
        if bar % 2 == 0:
            for deg, pos in ((7, 0.0), (8, 0.5), (11, 1.0), (10, 1.5), (7, 2.0), (6, 3.0)):
                add(buf, pluck(scale_note(deg, 0), 0.7), t0 + pos * beat, 0.5, wrap=True)
        else:
            add(buf, pad(scale_note(4, 1), 4 * beat * 0.95, 0.3), t0, 1.0, wrap=True)
    save("music_boss", buf, peak=0.7, fade=False)


if __name__ == "__main__":
    print("Generating Shadow Caravan audio ->", os.path.normpath(OUT))
    sfx()
    ambience()
    music_menu()
    music_world()
    music_boss()
    total = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT) if f.endswith(".wav"))
    print(f"done: {total / 1e6:.1f} MB")
