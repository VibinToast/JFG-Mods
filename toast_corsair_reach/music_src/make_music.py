"""Makes the Corsair Reach music: 12 looping level tracks and 3 world-end stings, as OGG Vorbis next to this script.

    python make_music.py                      # everything
    python make_music.py driftwood_victory    # just the named tracks
    python make_music.py --png DIR            # also a waveform, spectrogram and loop-seam picture per track

Needs numpy and scipy, and Blender for the OGG encoder (BLENDER, or Blender 5.2's default install path). The same
run makes the same files.

A loop is written with a little of its own end before it (PRE samples) and of its start after it (POST), and tagged
LOOPSTART = PRE, LOOPLENGTH = its length: the port plays the lead-in once, then loops exactly the loop, so the
encoder's edges at the file's two ends never fall inside it. After encoding, each OGG is decoded and checked:
length, peak, loudness, and the seam where the loop's end runs back into its start.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import cinderhold  # noqa: E402
import driftwood_cay  # noqa: E402
import mirefall  # noqa: E402
from oggtags import get_comments, set_comments  # noqa: E402
from synth import RATE  # noqa: E402

PRE, POST = 4096, 8192

BLENDER = os.environ.get("BLENDER", r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe")
TRACKS = {**driftwood_cay.TRACKS, **mirefall.TRACKS, **cinderhold.TRACKS}


def check(name, x, looped):
    """x: (samples, 2) decoded. Peak, RMS and, for a loop, how the seam compares with the rest of the track."""
    peak = float(np.max(np.abs(x)))
    rms = float(np.sqrt(np.mean(x ** 2)))
    out = dict(name=name, samples=len(x), seconds=len(x) / RATE, peak_db=20 * np.log10(peak + 1e-12),
               rms_db=20 * np.log10(rms + 1e-12), clipped=int(np.sum(np.abs(x) >= 0.999)))
    if looped:
        mono = x.mean(axis=1)
        d2 = np.abs(np.diff(mono, 2))
        wrap = np.concatenate([mono[-64:], mono[:64]])
        seam = np.abs(np.diff(wrap, 2))[48:80].max()
        out["seam"] = float(seam / (np.percentile(d2, 99.9) + 1e-12))
        out["jump"] = float(abs(mono[-1] - mono[0]) / (np.percentile(np.abs(np.diff(mono)), 99) + 1e-12))
    return out


def picture(x, path, title):
    from PIL import Image, ImageDraw

    W, H1, H2, H3 = 1200, 140, 300, 140
    img = Image.new("RGB", (W, H1 + H2 + H3 + 40), (18, 18, 22))
    dr = ImageDraw.Draw(img)
    dr.text((6, 4), title, fill=(230, 230, 230))
    mono = x.mean(axis=1)
    # waveform: min/max per column, with the -1 dBFS line
    cols = np.array_split(mono, W)
    top = 20
    for i, c in enumerate(cols):
        lo, hi = c.min(), c.max()
        dr.line([(i, top + H1 / 2 - hi * H1 / 2), (i, top + H1 / 2 - lo * H1 / 2)], fill=(90, 170, 230))
    for v in (0.891, -0.891):
        dr.line([(0, top + H1 / 2 - v * H1 / 2), (W, top + H1 / 2 - v * H1 / 2)], fill=(200, 60, 60))
    # spectrogram, log frequency 30 Hz - 16 kHz
    top2 = top + H1 + 4
    frame = 4096
    hops = np.linspace(0, len(mono) - frame - 1, W).astype(int)
    win = np.hanning(frame)
    freqs = np.fft.rfftfreq(frame, 1 / RATE)
    rows = np.geomspace(30, 16000, H2)[::-1]
    bins = np.searchsorted(freqs, rows)
    spec = np.empty((H2, W))
    for i, h in enumerate(hops):
        mag = np.abs(np.fft.rfft(mono[h:h + frame] * win))
        spec[:, i] = 20 * np.log10(mag[bins] + 1e-9)
    spec = np.clip((spec - spec.max() + 90) / 90, 0, 1)
    rgb = np.stack([spec ** 0.7 * 255, spec ** 1.6 * 220, (spec ** 0.5) * (1 - spec) * 200 + spec ** 3 * 80], -1)
    img.paste(Image.fromarray(rgb.astype(np.uint8)), (0, top2))
    # the loop seam: the last and first 40 ms joined, the seam in red
    top3 = top2 + H2 + 4
    k = int(0.04 * RATE)
    seam = np.concatenate([mono[-k:], mono[:k]])
    scale = max(1e-3, np.max(np.abs(seam)))
    pts = [(i * W / len(seam), top3 + H3 / 2 - s / scale * H3 / 2.2) for i, s in enumerate(seam)]
    dr.line(pts, fill=(120, 220, 140))
    dr.line([(W / 2, top3), (W / 2, top3 + H3)], fill=(220, 60, 60))
    dr.text((6, top3 + 2), "loop seam: last 40 ms | first 40 ms", fill=(200, 200, 200))
    img.save(path)


def blender(tmp, jobs):
    path = os.path.join(tmp, "jobs.json")
    json.dump(jobs, open(path, "w"))
    subprocess.run([BLENDER, "--background", "--factory-startup", "--python", str(HERE / "encode_ogg.py"), "--", path],
                   check=True, stdout=subprocess.DEVNULL)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*")
    ap.add_argument("--png", help="folder for the check pictures")
    args = ap.parse_args()
    names = args.names or list(TRACKS)
    with tempfile.TemporaryDirectory() as tmp:
        jobs, songs = [], {}
        for name in names:
            label, fn = TRACKS[name]
            t0 = time.time()
            song = fn()
            audio = song.render(report=True)
            songs[name] = song
            if song.loop:
                audio = np.concatenate([audio[:, -PRE:], audio, audio[:, :POST]], axis=1)
            npy = os.path.join(tmp, name + ".npy")
            np.save(npy, np.ascontiguousarray(audio.T))
            jobs.append(dict(npy=npy, ogg=str(HERE / (name + ".ogg")), decoded=os.path.join(tmp, name + ".dec.npy")))
            print(f"rendered {name} ({label}) in {time.time() - t0:.1f}s")
        blender(tmp, [dict(j, mode="encode") for j in jobs])
        for job, name in zip(jobs, names):
            if songs[name].loop:
                set_comments(job["ogg"], {"LOOPSTART": PRE, "LOOPLENGTH": songs[name].length})
        blender(tmp, [dict(j, mode="decode") for j in jobs])
        print("| File | Loop seconds | LOOPSTART | LOOPLENGTH | Peak dBFS | RMS dB | Seam | Size KB |")
        print("|---|---|---|---|---|---|---|---|")
        for job, name in zip(jobs, names):
            song = songs[name]
            dec = np.load(job["decoded"])
            rendered = np.load(job["npy"])
            assert len(dec) == len(rendered), (name, len(dec), len(rendered))
            if song.loop:
                tags = get_comments(job["ogg"])
                assert tags == {**tags, "LOOPSTART": str(PRE), "LOOPLENGTH": str(song.length)}, tags
                dec = dec[PRE:PRE + song.length]
            c = check(name, dec, song.loop)
            seam = f"{c['seam']:.2f} / {c['jump']:.2f}" if song.loop else "one-shot"
            kb = os.path.getsize(job["ogg"]) // 1024
            loop = f"{PRE} | {song.length}" if song.loop else "- | -"
            print(f"| {name}.ogg | {c['seconds']:.2f} | {loop} | {c['peak_db']:.1f} | {c['rms_db']:.1f} | "
                  f"{seam} | {kb} |" + (f" CLIPPED {c['clipped']}" if c["clipped"] else ""))
            if args.png:
                os.makedirs(args.png, exist_ok=True)
                picture(dec, os.path.join(args.png, name + ".png"),
                        f"{name}  {c['seconds']:.1f}s  peak {c['peak_db']:.1f} dBFS  rms {c['rms_db']:.1f} dB")


if __name__ == "__main__":
    main()
