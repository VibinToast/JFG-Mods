# Corsair Reach: design

The plan is split so each level's session reads only what it needs (2026-10-30):

- [KIT.md](KIT.md): the pack, the route, the shared tables (keys, flags, weapons, kinds, difficulty, mood, skies,
  music, weather), the binding rules from the owner's play-tests, the build method, the known tool gaps and the
  finishing checklist. Its status table says which levels are built.
- [levels/](levels/): one file per level: its links (arrivals, exits, TODOs from earlier levels), its plan, the fuller
  design from the original brief, and "As built".
- [TEST_NOTES.md](TEST_NOTES.md): what the owner should play-test in each level.
- History: the original brief, JFG-Modding `Docs/GALAXY_PACK_BRIEF.md`; this file's full text before the split is in
  JFG-Mods d759fb0.

Changes from the brief that hold for the whole pack:
- **Death**: the code restarts the level the hero is in, at its entry, while the world's continues last (the brief
  expected the world's first level).
- **Rain**: Studio writes the weather now (3f4674d) and the owner saw rain in a pack level: Mirefall has it.
- **Skies**: every level that shows the sky has the pack's own dome (owner, 2026-10-30), never one of the game's.
