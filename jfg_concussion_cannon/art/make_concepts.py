"""Concussion Cannon's concept sheet, from the mod's own art (nothing from the game), into
concepts/concussion_cannon_concept.png: the cannon close up, the models, the HUD icon and the textures
(art/previews, art/textures). concepts/concussion_cannon_first_look.jpg is the first render, as the owner saved it.

    python art/make_concepts.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

ART = Path(__file__).resolve().parent
OUT = ART.parent / "concepts"
BG = (24, 30, 40, 255)
TEXT = (220, 235, 255, 255)


def main():
    cannon = Image.open(ART / "previews" / "cannon.png").convert("RGBA")
    models = Image.open(ART / "previews" / "models.png").convert("RGBA")
    icon = Image.open(ART / "textures" / "hud_icon_big.png").convert("RGBA")
    textures = Image.open(ART / "previews" / "textures.png").convert("RGBA")
    textures.thumbnail((models.width, 600))
    top_w = cannon.width + icon.width + 40
    w = max(top_w, models.width, textures.width) + 40
    h = 60 + max(cannon.height, icon.height) + 30 + models.height + 30 + textures.height + 20
    sheet = Image.new("RGBA", (w, h), BG)
    d = ImageDraw.Draw(sheet)
    d.text((20, 20), "Concussion Cannon: a charged cone of force (the mod's own models, icon and textures)", fill=TEXT)
    y = 60
    sheet.alpha_composite(cannon, (20, y))
    sheet.alpha_composite(icon, (cannon.width + 60, y + (cannon.height - icon.height) // 2))
    y += max(cannon.height, icon.height) + 30
    sheet.alpha_composite(models, (20, y))
    y += models.height + 30
    sheet.alpha_composite(textures, (20, y))
    OUT.mkdir(exist_ok=True)
    sheet.convert("RGB").save(OUT / "concussion_cannon_concept.png")
    print("wrote", OUT / "concussion_cannon_concept.png", sheet.size)


if __name__ == "__main__":
    main()
