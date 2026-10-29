// Weapon Sounds for Jet Force Gemini: Recompiled (mod API version 5).
//
// The weapons' sound effects replaced with remastered ones (remaster.py, from the game's own: extract_originals.py).
// The replacing is the port's, from jfg_sounds.json's "replace" list (the game's sound ids and the mod's sounds for
// them). This code follows the options: each weapon's sounds on or off, live (jfg_sound_replace_enable; off, the
// game's own sound plays again). The pistol and the sniper rifle share one game sound: while the sniper rifle is in hand
// the mod's sniper sound stands in for it (jfg_sound_replace_use), under the sniper's option.

#include "jfg_api.h"

RECOMP_IMPORT("*", unsigned int recomp_get_config_u32(const char* key));

typedef struct {
    const char* option;
    int ids[3];   // the game's sound ids it covers, 0 ends the list
    int on;       // as last applied: -1 not yet
} Group;

static Group groups[] = {
    { "machine_gun",  { 0x8, 0xE, 0x1E1 }, -1 },   // the stream, the last round, the settle
    { "missiles",     { 0x95 }, -1 },              // homing missiles and the tri-rocket launcher
    { "plasma",       { 0xFA, 0xE1 }, -1 },        // the charge and the shot
    { "shocker",      { 0x9B }, -1 },
    { "throws",       { 0x2F }, -1 },              // throws, grenades' bounces
    { "shuriken",     { 0x9A }, -1 },
    { "mines",        { 0xD0 }, -1 },
    { "flares",       { 0xF1 }, -1 },
    { "switch",       { 0x8B }, -1 },              // changing weapons
};

#define SHOT       0x3   // the pistol's and the sniper rifle's shot
#define SNIPER     7     // the sniper rifle (jfg_hero_weapon)
#define SHOT_LEVEL 0.55f // as jfg_sounds.json gives the pistol
#define SNIPER_LEVEL 0.6f

static int shot_as = -1; // 0 the pistol's, 1 the sniper's, as last applied
static int shot_on = -1;

RECOMP_CALLBACK("*", jfg_on_game_tick) void weapon_sounds_tick(int frames) {
    const int sniper = jfg_hero_weapon() == SNIPER;
    const int on = recomp_get_config_u32(sniper ? "sniper" : "pistol") != 0;
    if (sniper != shot_as) {
        shot_as = sniper;
        jfg_sound_replace_use(SHOT, sniper ? "sniper" : "pistol", sniper ? SNIPER_LEVEL : SHOT_LEVEL);
    }
    if (on != shot_on) {
        shot_on = on;
        jfg_sound_replace_enable(SHOT, on);
    }

    for (unsigned int g = 0; g < sizeof(groups) / sizeof(groups[0]); g++) {
        const int on = recomp_get_config_u32(groups[g].option) != 0;
        if (on == groups[g].on) continue;
        groups[g].on = on;
        for (int i = 0; i < 3 && groups[g].ids[i] != 0; i++) jfg_sound_replace_enable(groups[g].ids[i], on);
    }
}
