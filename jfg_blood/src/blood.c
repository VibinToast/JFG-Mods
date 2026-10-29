// Blood: the blood options for Jet Force Gemini: Recompiled (mod API version 6).
//
// No blood and Blood amount change each spurt in the blood events; Blood stays and Body parts stay are the port's
// (jfg_blood_keep, jfg_limbs_keep), turned on from here. Colours: each kind of creature (the event's group) gets a
// colour index of its own, and the mod fills the index's colour (jfg_blood_set_color): heroes keep index 0, the
// insects 1, flyers and drones 2, the final boss 4; Tribals, which share the heroes' red in the game, and the rest get
// two indexes of the mod's own (jfg_blood_color_alloc: never another mod's). "Original" fills a group's index with the game's colour for it, so changing one group never changes another.
// With every group on Original the mod leaves the game's colours and indexes alone. Options are read every tick, so
// changes in the mod's settings apply at once.

#include "jfg_api.h"

RECOMP_IMPORT("*", unsigned int recomp_get_config_u32(const char* key));
RECOMP_IMPORT("*", double recomp_get_config_double(const char* key));

#define GROUPS 6

// The colour index each group (JFG_BLOOD_*) bleeds with, and the game's colour for it (drops, hits).
static int group_index[GROUPS] = { 0, -1, 1, 2, 4, -1 }; // -1: the mod's own, taken at the first tick

// The two groups without a colour of their own in the game get the mod's own indexes (the heroes' 0 if none is free).
static void take_indexes(void) {
    if (group_index[1] >= 0) return;
    const int a = jfg_blood_color_alloc(0), b = jfg_blood_color_alloc(1);
    group_index[1] = a >= 0 ? a : 0;
    group_index[5] = b >= 0 ? b : 0;
}
static const unsigned int game_drops[GROUPS] = { 0x500000, 0x500000, 0x005013, 0x000000, 0xAAFF00, 0x500000 };
static const unsigned int game_hits[GROUPS]  = { 0xA00000, 0xA00000, 0x00A028, 0x000000, 0xAAFF00, 0xA00000 };
static const char* const group_option[GROUPS] = {
    "color_heroes", "color_tribals", "color_insects", "color_flyers", "color_boss", "color_other"
};

// The colour choices after "Original" (option 1..), for hit sprites; drops take half of each channel, as the game's do.
static const unsigned int choices[] = {
    0xA00000, // Red
    0x00A028, // Green
    0x0028C8, // Blue
    0xC8B400, // Yellow
    0xD06000, // Orange
    0x7800C8, // Purple
    0xE04898, // Pink
    0x00B4C8, // Cyan
    0xE0E0E0, // White
    0x000000, // Black
};
#define CHOICES (int)(sizeof(choices) / sizeof(choices[0]))

static struct {
    int no_blood;
    int amount;
    int rainbow;
    int remap;            // some group has a colour of its own: hand out the indexes
    int color[GROUPS];    // 0 = Original, else choices[color - 1]
} cfg;

static int applied = 0;          // the port has the settings below
static int last_keep = -1, last_limbs = -1, last_rainbow = -1;
static int last_color[GROUPS];

static unsigned int half(unsigned int rgb) {
    return ((rgb >> 1) & 0x7F7F7F);
}

static void read_config(void) {
    // Off (the mods menu's switch): every option as the game has it.
    const int on = recomp_get_config_u32("enabled") != 0;
    cfg.no_blood = on && recomp_get_config_u32("no_blood") != 0;
    cfg.amount = on ? (int)recomp_get_config_double("amount") : 100;
    cfg.rainbow = on && recomp_get_config_u32("rainbow") != 0;
    cfg.remap = 0;
    for (int g = 0; g < GROUPS; g++) {
        int c = on ? (int)recomp_get_config_u32(group_option[g]) : 0;
        if (c < 0 || c > CHOICES) c = 0;
        cfg.color[g] = c;
        if (c != 0) cfg.remap = 1;
    }

    const int keep = (on && !cfg.no_blood && recomp_get_config_u32("keep_blood") != 0) ? (int)recomp_get_config_double("splats") : 0;
    const int limbs = on && !cfg.no_blood && recomp_get_config_u32("keep_limbs") != 0;
    if (keep != last_keep) { jfg_blood_keep(keep); last_keep = keep; }
    if (limbs != last_limbs) { jfg_limbs_keep(limbs); last_limbs = limbs; }
    // Only on a change: the game's own cheat menu may have turned it on.
    if (cfg.rainbow != last_rainbow) {
        if (last_rainbow != -1 || cfg.rainbow) jfg_blood_set_rainbow(cfg.rainbow);
        last_rainbow = cfg.rainbow;
    }

    int changed = !applied;
    for (int g = 0; g < GROUPS; g++) if (cfg.color[g] != last_color[g]) changed = 1;
    if (!changed) return;
    for (int g = 0; g < GROUPS; g++) {
        last_color[g] = cfg.color[g];
        const int c = cfg.color[g];
        if (!cfg.remap) {
            jfg_blood_set_color(group_index[g], 0xFFFFFFFF, 0xFFFFFFFF); // the game's tables as they were
        } else if (c == 0) {
            jfg_blood_set_color(group_index[g], game_drops[g], game_hits[g]);
        } else {
            jfg_blood_set_color(group_index[g], half(choices[c - 1]), choices[c - 1]);
        }
    }
    applied = 1;
}

RECOMP_CALLBACK("*", jfg_on_game_tick) void blood_tick(int frames) {
    take_indexes();
    read_config();
}

// The group's own index, when the colours are handed out (the game gives "other" creatures the heroes' red).
static int index_for(int group, int color) {
    if (!cfg.remap || group < 0 || group >= GROUPS || group_index[group] < 0) return color;
    return group_index[group];
}

RECOMP_CALLBACK("*", jfg_on_blood_spurt) void blood_spurt(JfgBloodSpurt* blood) {
    if (cfg.no_blood) { blood->cancel = 1; return; }
    blood->amount = blood->amount * cfg.amount / 100;
    blood->color = index_for(blood->group, blood->color);
}

RECOMP_CALLBACK("*", jfg_on_blood_hit) void blood_hit(JfgBloodHit* hit) {
    if (cfg.no_blood) { hit->cancel = 1; return; }
    hit->color = index_for(hit->group, hit->color);
}
