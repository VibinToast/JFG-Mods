// Better Pickups: what enemies drop stays until you take it, comes more or less often, and comes to you, for Jet Force
// Gemini: Recompiled (mod API version 6). It was Ammo Stays.
//
// - Staying: an enemy's dropped ammo, weapon or drone head is a severed-limb object (the game's: object 0x89) of kind
//   3, 4 or 2 (data + 0x17); its life (data + 0x14, s16, 950 at the start) counts down, then it fades (object + 0x39)
//   and is freed. Each tick (the jfg_on_severed_limb_tick event, before the game's code) the mod puts the life back
//   and the fade off, for the newest drops only: each is an object with a model, and the game stops making new drops
//   when its memory runs low.
// - Health gems: a gem an enemy drops (kind 61, the health pickup, with its drop countdown at data +0x10: 0 for the
//   level's own) hangs where the enemy died and goes after 480 ticks (blinking by its alpha, object +0x8C, from 0x80
//   left). It falls to the floor under it here, and with Health Gems Stay its countdown is put back each tick. The
//   pickup's home (data +0x00, +0x04, +0x08) moves with it.
// - Mod Drop Rate: the shared drop pool's chances (other mods' items: jfg_drop_rate).
// - Pickup Magnet: drops within reach drift to the hero, who picks them up the game's way; mods' items are drawn by the
//   port (jfg_drop_magnet).

#include "jfg_api.h"
#include "jfg_util.h"

RECOMP_IMPORT("*", unsigned int recomp_get_config_u32(const char* key));
RECOMP_IMPORT("*", double recomp_get_config_double(const char* key));

#define LIFE 950
#define TRACKED 256

static unsigned int tick = 1;

// Drops seen lately, by object address: when each first appeared and was last seen (a gap: a new object there).
static struct { void* obj; unsigned int first, last; } seen[TRACKED];

#define KIND_HEAD 2
#define KIND_AMMO 3
#define KIND_WEAPON 4
#define MAGNET_SPEED 7.0f    // units a 1/30 s tick
static const float MAGNET_REACH[3] = { 0.0f, 140.0f, 400.0f }; // Off, Short, Long

static float reach_now(void) {
    if (recomp_get_config_u32("enabled") == 0) return 0.0f;
    const unsigned int m = recomp_get_config_u32("magnet");
    return m < 3 ? MAGNET_REACH[m] : 0.0f;
}

#define KIND_HEALTH_PICKUP 61
#define MAX_GEMS 48
#define GEM_LIFE 480
#define GEM_REST 14.0f       // a resting gem's middle above the floor
#define GEM_FALL 7.0f        // units a 1/30 s tick

// Pulls p toward the hero (within reach, step units at most); 1 if it moved.
static int pull(float* p, const float* h, float reach, float step, float lift) {
    const float dx = h[0] - p[0], dy = h[1] + lift - p[1], dz = h[2] - p[2];
    const float d = jfg_sqrt(dx * dx + dy * dy + dz * dz);
    if (d >= reach || d < 1.0f) return 0;
    if (step > d) step = d;
    p[0] += dx / d * step;
    p[1] += dy / d * step;
    p[2] += dz / d * step;
    return 1;
}

static void gems_tick(void* hero) {
    JfgObjectInfo gems[MAX_GEMS];
    const int n = jfg_objects_of_kind(KIND_HEALTH_PICKUP, gems, MAX_GEMS);
    const float scale = jfg_get_tick_scale(), reach = reach_now();
    const int stay = recomp_get_config_u32("gems") != 0;
    for (int i = 0; i < n && i < MAX_GEMS; i++) {
        void* obj = gems[i].object;
        unsigned char* data = *(unsigned char**)((unsigned char*)obj + 0x68);
        if (data == 0) continue;
        short* countdown = (short*)(data + 0x10);
        if (*countdown <= 0) continue; // the level's own gem
        float* home = (float*)data;
        float* p = jfg_obj_pos(obj);
        int moved = hero != 0 && reach > 0.0f && pull(home, jfg_obj_pos(hero), reach, MAGNET_SPEED * scale, 30.0f);
        if (!moved) {
            // Down to the floor under it.
            const float from[3] = { home[0], home[1] + 5.0f, home[2] };
            const float to[3] = { home[0], home[1] - 4000.0f, home[2] };
            float hit[6];
            if (jfg_level_ray(from, to, hit)) {
                const float rest = hit[1] + GEM_REST;
                if (home[1] > rest) {
                    home[1] -= GEM_FALL * scale;
                    if (home[1] < rest) home[1] = rest;
                }
            }
        }
        p[0] = home[0];
        p[1] = home[1];
        p[2] = home[2];
        if (stay) {
            *countdown = GEM_LIFE;
            *(int*)((unsigned char*)obj + 0x8C) = 255;
        }
    }
}

RECOMP_CALLBACK("*", jfg_on_game_tick) void ammo_tick(int frames) {
    tick++;
    const int on = recomp_get_config_u32("enabled") != 0;
    jfg_drop_rate(on ? (int)recomp_get_config_double("mod_drop_rate") : 100);
    jfg_drop_magnet(reach_now());
    if (on && !jfg_game_paused()) gems_tick(jfg_hero_get());
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
    if (kind != KIND_AMMO && kind != KIND_WEAPON && kind != KIND_HEAD) return;
    // The magnet: within reach, it drifts toward the hero (across the ground; the game keeps it on the floor).
    const float reach = reach_now();
    void* hero = jfg_hero_get();
    if (reach > 0.0f && hero != 0) {
        float* p = jfg_obj_pos(limb);
        const float* h = jfg_obj_pos(hero);
        const float dx = h[0] - p[0], dz = h[2] - p[2], d = jfg_sqrt(dx * dx + dz * dz);
        if (d < reach && d > 1.0f) {
            float step = MAGNET_SPEED * jfg_get_tick_scale();
            if (step > d) step = d;
            p[0] += dx / d * step;
            p[2] += dz / d * step;
        }
    }
    const int stays = kind == KIND_AMMO ? recomp_get_config_u32("ammo") != 0
                    : kind == KIND_WEAPON ? recomp_get_config_u32("weapons") != 0
                    : recomp_get_config_u32("heads") != 0;
    if (!stays) return;
    const int keep = (int)recomp_get_config_double("keep");
    if (!newest(limb, keep)) return;
    *(short*)(data + 0x14) = LIFE;
    ((unsigned char*)limb)[0x39] = 0xFF;
}
