// Ammo Stays: ammo that enemies drop no longer disappears, for Jet Force Gemini: Recompiled (mod API version 5).
//
// An enemy's dropped ammo is a severed-limb object (the game's: object 0x89) of kind 3 or 4 (data + 0x17); its life
// (data + 0x14, s16, 950 at the start) counts down, then it fades (object + 0x39) and is freed. Each tick (the
// jfg_on_severed_limb_tick event, before the game's code) the mod puts the life back and the fade off, for the newest
// drops only: each is an object with a model, and the game stops making new drops when its memory runs low. Drone
// heads (kind 2) can be kept the same way.

#include "jfg_api.h"

RECOMP_IMPORT("*", unsigned int recomp_get_config_u32(const char* key));
RECOMP_IMPORT("*", double recomp_get_config_double(const char* key));

#define LIFE 950
#define TRACKED 256

static unsigned int tick = 1;

// Drops seen lately, by object address: when each first appeared and was last seen (a gap: a new object there).
static struct { void* obj; unsigned int first, last; } seen[TRACKED];

RECOMP_CALLBACK("*", jfg_on_game_tick) void ammo_tick(int frames) {
    tick++;
}

RECOMP_CALLBACK("*", jfg_on_level_change) void ammo_level(int level, int character) {
    for (int i = 0; i < TRACKED; i++) seen[i].obj = 0;
}

// True if obj is among the keep newest drops (and notes this tick's sighting).
static int newest(void* obj, int keep) {
    int slot = -1, free_slot = -1, oldest = 0;
    for (int i = 0; i < TRACKED; i++) {
        if (seen[i].obj != 0 && tick - seen[i].last > 30) seen[i].obj = 0; // gone
        if (seen[i].obj == obj) slot = i;
        else if (seen[i].obj == 0 && free_slot < 0) free_slot = i;
        if (seen[i].obj != 0 && seen[i].first < seen[oldest].first) oldest = i;
    }
    if (slot < 0) {
        slot = free_slot >= 0 ? free_slot : oldest;
        seen[slot].obj = obj;
        seen[slot].first = tick;
    } else if (tick - seen[slot].last > 2) {
        seen[slot].first = tick; // the address holds a new drop
    }
    seen[slot].last = tick;
    int newer = 0;
    for (int i = 0; i < TRACKED; i++)
        if (i != slot && seen[i].obj != 0 && seen[i].first > seen[slot].first) newer++;
    return newer < keep;
}

RECOMP_CALLBACK("*", jfg_on_severed_limb_tick) void ammo_limb(void* limb, int frames) {
    if (limb == 0 || recomp_get_config_u32("enabled") == 0) return;
    unsigned char* data = *(unsigned char**)((unsigned char*)limb + 0x68);
    if (data == 0) return;
    const int kind = data[0x17];
    const int heads = recomp_get_config_u32("heads") != 0;
    if (!(kind == 3 || kind == 4 || (heads && kind == 2))) return;
    const int keep = (int)recomp_get_config_double("keep");
    if (!newest(limb, keep)) return;
    *(short*)(data + 0x14) = LIFE;
    ((unsigned char*)limb)[0x39] = 0xFF;
}
