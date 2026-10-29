"""The pack: the Rolling Shellback's model, animations and object type, and its effects. Everything is made by the
scripts in art/ (nothing from the ROM): each art/models/*.glb becomes a new model with new textures
(jfgformats.models.import_new, decomp MSR 9a; the shellback is skinned: its joints, animations and slot row, MSR 12a,
and its hit spheres, MSR 12i).

- shellback: its 11 animations are appended (0x2A/0x2B) and its animation list ("animRows" "anims") is laid out as the
  like soldier's animation set (object 0xEE, 21 entries) asks for the game's own actions, ours after (LIST below). Its
  definition is a copy of 0xEE's (definition 336, MSR 12i part 2) with our model and a hit box and collision radius
  sized to it; its object type is "like" 0xEE, so squadrons placed with it spawn shellbacks the squad code runs as
  that soldier, and the mod takes over (src/shellback.c).
- spine (the projectile, moved by the mod) and dizzy (the stars): copies of the player's definition 427, behaviour 0x35
  (no code runs). spark and dust: the same with behaviour 0x7E, whose opacity the mod fades (obj +0x8C, MSR 11).
Writes assets/*.bin and jfg_assets.json; the mod finds them by name (jfg_asset_number "jfg_shellback:objdef_shellback",
"...:objtype_spine", ...). Run in WSL with the decomp's tools on the path:

    python3 build_assets.py ~/jfg/tools
"""
import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else str(Path.home() / "jfg" / "tools"))
from jfgformats import models  # noqa: E402

TEX_TABLE, TEX_DATA = 1, 0            # the 3D texture set
MODEL_TABLE, MODEL_DATA = 0x26, 0x27
ANIM_TABLE, ANIM_DATA = 0x2A, 0x2B
OBJDEF_TABLE, OBJDEF_DATA = 0x2E, 0x2F
HOST_DEF = 427                        # the player's own definition: a plain model holder (the effects)
SOLDIER_DEF, SOLDIER_ID = 336, 0xEE   # the like soldier's definition and object id (MSR 12i part 2)
SIZE = 0.84375                            # its size against the model as built: the definition scale (the mod reads each member's)

# The model's animation list: position k plays the .glb animation named here. 0-20 are the soldier's set (the game
# picks them for its own actions: idles, flinches, deaths then the held dead pose, electrocuted, fire, walk, run); 21-25
# are the mod's (src/shellback.c ANIM_*). The dead pose doesn't loop, so it ends and the game fades the body.
LIST = (["00_idle_loop"] * 4 + ["08_hit"] * 5 + ["09_death", "10_dead"] * 4 +
        ["05_dizzy_loop", "07_fire", "01_walk_loop", "01_walk_loop",
         "02_turn_loop", "03_curl", "04_ball_loop", "05_dizzy_loop", "06_uncurl"])
assert len(LIST) == 26

out = HERE / "assets"
out.mkdir(exist_ok=True)
entries, files, types = [], [], []


def put(name, data):
    path = out / (name + ".bin")
    path.write_bytes(data)
    files.append("assets/" + path.name)
    return "assets/" + path.name


def add_model(name, lit=True):
    """A .glb as a new model with its new textures; returns import_new's result."""
    r = models.import_new(str(HERE / "art" / "models" / (name + ".glb")), name=name, lit=lit, log=print)
    for t in r["textures"]:
        tname = "tex_%s_%s" % (name, t["key"])
        entries.append({"table": TEX_TABLE, "data": TEX_DATA, "append": tname, "file": put(tname, t["entry"])})
        print(name, "texture", t["key"], t["width"], "x", t["height"], "format", t["format"], "alpha", t["alpha"])
    entries.append({"table": MODEL_TABLE, "data": MODEL_DATA, "append": "model_" + name,
                    "file": put("model_" + name, r["packed"]), "packed": True,
                    "fixups": [{"at": f["at"], "type": f["type"], "ref": "tex_%s_%s" % (name, f["texture"]),
                                "add": f["or"]} for f in r["textureRefs"]]})
    return r


def f32(v):
    return struct.pack(">f", v).hex()


def s16(v):
    return struct.pack(">h", v).hex()


def add_type(name, copy_of, sets, like=None):
    entries.append({"table": OBJDEF_TABLE, "data": OBJDEF_DATA, "append": "objdef_" + name, "copyOf": copy_of,
                    "set": [{"at": at, "hex": hx} for at, hx in sets],
                    "fixups": [{"at": 0xE0, "type": "u32", "ref": "model_" + name}]})
    t = {"append": "objtype_" + name, "def": "objdef_" + name}
    if like is not None:
        t["like"] = like
    types.append(t)


# --- the shellback ---------------------------------------------------------------------------------------------------
# Lit (jfgformats 0.9.1 or later: 0.9.0 packed up to 16 vertices in a lighting entry where the game reads 6, MSR 12j).
r = add_model("shellback")
problems = models.check_lighting(r["data"])
assert not problems, problems
joints = r["joints"] if isinstance(r["joints"], int) else len(r["joints"])
by_name = {a["name"]: a for a in r["animations"]}
row = len(r["slotRow"]) // len(r["animations"])
assert row == joints and set(LIST) <= set(by_name), (row, joints, sorted(by_name))
for a in r["animations"]:
    entries.append({"table": ANIM_TABLE, "data": ANIM_DATA, "append": "anim_" + a["name"],
                    "file": put("anim_" + a["name"], a["data"])})
    print("animation", a["index"], a["name"], a["frames"], "frames", "loops" if a["loops"] else "once")
slots = b"".join(r["slotRow"][by_name[n]["index"] * row:(by_name[n]["index"] + 1) * row] for n in LIST)
anim_rows = [{"model": "model_shellback", "anims": ["anim_" + n for n in LIST], "slots": put("slots_shellback", slots)}]
print("shellback:", joints, "joints,", len(r.get("points", [])), "points,", len(r.get("hitSpheres", [])),
      "hit spheres; list of", len(LIST), "(", len(slots), "slot bytes )")
# The soldier's definition with our model (MSR 12i part 2). The hit box (an upright cylinder) must hold every hit
# sphere in every pose, or shots miss where a sphere sticks out: the head sphere reaches 68 in front of the centre and
# the rear plate's 80 behind, the ball 2..74 high. The collision radius (+0x100, the +0xF4 block) is the ball's.
add_type("shellback", SOLDIER_DEF, [
    (0x00, f32(SIZE)),                   # its scale: the model, hit spheres and hit box grow with it
    (0xB4, s16(0) + s16(38) + s16(0)),   # the hit box centre, from the origin (as built: times the scale)
    (0xBC, f32(84.0)),                   # its radius
    (0xC0, f32(42.0)),                   # its half height: -4..80
    (0x100, f32(38.0 * SIZE)),           # the rolling ball's collision radius (used as it is: not scaled)
], like=SOLDIER_ID)

# --- the effects -----------------------------------------------------------------------------------------------------
HOVER = [(0x00, f32(1.0)), (0x1C, "0035"), (0xD0, "00000000")]
FADING = [(0x00, f32(1.0)), (0x1C, "007E"), (0xD0, "00000000")]
for name, sets in (("spine", HOVER), ("dizzy", HOVER), ("spark", FADING), ("dust", FADING)):
    add_model(name)
    add_type(name, HOST_DEF, sets)

# Placing them: JFG-Studio places a mod's own types (its jfg_debug_room project has a squad of them).
doc = {"entries": entries, "objtypes": types, "animRows": anim_rows}
(HERE / "jfg_assets.json").write_text(json.dumps(doc, indent=2) + "\n")
print("files:", " ".join(files))
