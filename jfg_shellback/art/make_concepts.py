"""Rolling Shellback's concept sheets, laid out from the renders in previews/ (build_models.py) and the textures
(make_textures.py), into concepts/ at the mod's top:

    shellback_concept.png   the beetle: standing (three-quarter and side), firing, curling, curled, dizzy and dead
    effects_concept.png     the spine, spark, dizzy stars and dust ring, over the texture sheet

    python make_concepts.py    (after make_textures.py and build_models.py)
"""
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
PREVIEW = HERE / "previews"
OUT = HERE.parent / "concepts"
BG = (24, 26, 34)
INK = (220, 230, 240)

POSES = [("standing.png", "walks its patrol"), ("standing_side.png", "side: five plates, amber belly, glowing rear pad"),
         ("fire.png", "plates flare, three spines from the middle plate's slits"),
         ("curling.png", "curling: plates hinge round, head and legs tuck"),
         ("curled.png", "curled: a ball of radius ~38 that rolls and bounces"),
         ("dizzy.png", "dizzy: half open, head lolling"), ("death.png", "dead: flipped on its back")]


def label(im, text):
    d = ImageDraw.Draw(im)
    d.rectangle((0, im.size[1] - 22, im.size[0], im.size[1]), fill=BG)
    d.text((8, im.size[1] - 18), text, fill=INK)


def beetle_sheet():
    w, h, cols = 400, 300, 4
    sheet = Image.new("RGB", (cols * w, 40 + 2 * h), BG)
    ImageDraw.Draw(sheet).text((10, 12), "Rolling Shellback: armoured squad beetle (about 140 long, 68 wide, 60 high)",
                               fill=INK)
    for i, (name, text) in enumerate(POSES):
        im = Image.open(PREVIEW / name).convert("RGB").resize((w, h), Image.LANCZOS)
        label(im, text)
        sheet.paste(im, ((i % cols) * w, 40 + (i // cols) * h))
    sheet.save(OUT / "shellback_concept.png")


def effects_sheet():
    models = Image.open(PREVIEW / "models.png").convert("RGB")
    tex = Image.open(PREVIEW / "textures.png").convert("RGB")
    w = max(models.size[0], tex.size[0])
    sheet = Image.new("RGB", (w, 40 + models.size[1] + tex.size[1]), BG)
    ImageDraw.Draw(sheet).text((10, 12), "Effects: spine, deflect spark, dizzy stars, dust ring; and every texture",
                               fill=INK)
    sheet.paste(models, (0, 40))
    sheet.paste(tex, (0, 40 + models.size[1]))
    sheet.save(OUT / "effects_concept.png")


OUT.mkdir(exist_ok=True)
beetle_sheet()
effects_sheet()
print("concepts in", OUT)
