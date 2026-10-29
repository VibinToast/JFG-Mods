"""The game's own weapon sounds from your ROM, as WAV files in original/ (gitignored: the source for make_sounds.py).

Run in WSL against the decomp's extracted assets (~/jfg, `make extract`), using its audio tool:
    cd ~/jfg && .venv/bin/python3 /mnt/c/.../Mods/jfg_weapon_sounds/extract_originals.py

A sound id (what the game plays, what jfg_sounds.json replaces) is an entry of the sound table (audio section 6,
10 bytes each: u16 sample, u8 volume, u8 minimum volume, u8 pitch in hundredths, ...); its sample is a sound of the
sound effect bank, played at the bank sound's rate times the pitch.
"""
import os
import struct
import sys

JFG = os.path.expanduser('~/jfg')
sys.path.insert(0, os.path.join(JFG, 'tools'))
os.chdir(JFG)
import audio  # noqa: E402

IDS = {
    0x3: 'pistol', 0xE: 'pistol_light', 0x8: 'machine_gun_loop', 0x1E1: 'spin_down', 0x95: 'missile',
    0xFA: 'plasma_charge', 0xE1: 'plasma_fire', 0x9B: 'shocker', 0x2F: 'throw', 0x9A: 'zing', 0xD0: 'mine_beep',
    0xF1: 'flare', 0x8B: 'switch',
}

blob = audio.load_audio_blob()
with open(audio.ASSETS_BIN, 'rb') as f:
    allb = f.read()
with open(audio.ASSETS_LUT, 'rb') as f:
    lut = f.read()
count = struct.unpack('>I', lut[:4])[0]
offsets = struct.unpack('>%dI' % (count + 1), lut[4:4 + 4 * (count + 1)])
table = struct.unpack('>8I', allb[offsets[audio.AUDIO_TABLE_ASSET]:offsets[audio.AUDIO_TABLE_ASSET] + 32])
data = allb[offsets[audio.AUDIO_ASSET]:offsets[audio.AUDIO_ASSET + 1]]
index = data[table[5]:table[6]]
_, sfx = audio.parse_bank(blob['sfx_ctl'])
sounds = sfx[0]['sounds']
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'original')
os.makedirs(out, exist_ok=True)
cache = {}
print('%d sound ids, %d bank sounds' % (len(index) // 10, len(sounds)))
for sid, name in sorted(IDS.items()):
    bite, volume, minvol, pitch = struct.unpack('>HBBB', index[sid * 10:sid * 10 + 5])
    if bite == 0 or bite >= len(sounds) + 1:
        print('0x%X %s: no sample (%d)' % (sid, name, bite))
        continue
    # The bank's sound list: amSndPlay hands the sample number to the player, which counts from 1 (0 = none).
    snd = sounds[bite - 1]
    samples = audio.decode_wave(snd['wave'], blob['sfx_tbl'], cache)
    rate = int(audio.sound_rate(snd) * (pitch / 100.0 if pitch else 1.0))
    audio.write_wav(os.path.join(out, '%s.wav' % name), samples, rate, snd.get('loop'))
    print('0x%X %-17s sample %3d  %5d Hz  %.2f s  volume %d%s' % (sid, name, bite, rate, len(samples) / rate, volume,
                                                               '  loops' if 'loop' in snd else ''))
