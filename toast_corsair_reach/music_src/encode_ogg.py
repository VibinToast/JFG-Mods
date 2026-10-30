"""Run inside Blender (its `aud` library writes OGG Vorbis): encodes each job's rendered .npy to its .ogg, or
decodes its .ogg back to .npy so make_music.py can check what the game will actually play.

    blender --background --factory-startup --python encode_ogg.py -- jobs.json
"""

import json
import sys

import aud
import numpy as np

RATE = 44100
BITRATE = 128000

jobs = json.load(open(sys.argv[sys.argv.index("--") + 1]))
for job in jobs:
    if job["mode"] == "encode":
        data = np.load(job["npy"])  # (samples, 2) float32
        sound = aud.Sound.buffer(np.ascontiguousarray(data, dtype=np.float32), RATE)
        sound.write(job["ogg"], RATE, aud.CHANNELS_STEREO, aud.FORMAT_S16, aud.CONTAINER_OGG, aud.CODEC_VORBIS,
                    BITRATE)
    else:
        np.save(job["decoded"], aud.Sound(job["ogg"]).data())
