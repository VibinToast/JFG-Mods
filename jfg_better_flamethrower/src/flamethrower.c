// Better Flamethrower for Jet Force Gemini: Recompiled (mod API version 5).
//
// While the hero fires the flamethrower (weapon 6), the mod reads where its flames are (jfg_flames_get) and:
//  - leaves fires on the ground where the flames reach (the game's own fire, as explosions leave it: jfg_fx_fire), which
//    hurt anyone standing in them (jfg_damage_sphere; the hero too, with Fire Hurts You) and set enemies in them alight
//    (jfg_enemy_ignite: the game's burning, as the flamethrower does it), Tribals too with Fire Hurts Tribals;
//  - adds damage to whatever the flames touch (Flame Damage);
//  - lets burning spread: an enemy the flames or a fire caught keeps burning for a while, and sets alight the ones
//    that come near it.
// The ground under a fire is the hero's feet when the flames are about level with the hero, else just under the flame.
// Fuel Use: the fuel the flamethrower burns (its ammo, jfg_hero_ammo) is partly given back as it goes, so a tank lasts
// longer. A ground fire burns as long as asked: the game's fire lasts at most 12.7 s, so it is lit again until then.
// Off (the mods menu's switch): none of it.

#include "jfg_api.h"
#include "jfg_util.h"

RECOMP_IMPORT("*", unsigned int recomp_get_config_u32(const char* key));
RECOMP_IMPORT("*", double recomp_get_config_double(const char* key));

#define WEAPON_FLAMETHROWER 6
#define FLAMES 30
#define FIRES 16
#define BURNING 32
#define NEARBY 16
typedef struct { float x, y, z; int left, shown; float radius; } Fire; // left, shown (the game's fire): 1/60 s ticks
typedef struct { void* obj; int left; int spread_in; } Burning;

static Fire fires[FIRES];
static Burning burning[BURNING];
static int drop_in = 0;      // 1/60 s ticks until the next ground fire may be left
static int last_fuel = -1;   // the flamethrower's ammo last tick
static int fuel_owed = 0;    // fuel to give back, in hundredths
static unsigned int seed = 12345;

static int chance(int percent) {
    seed = seed * 1103515245u + 12345u;
    return (int)((seed >> 16) % 100) < percent;
}

RECOMP_CALLBACK("*", jfg_on_level_change) void flame_level(int level, int character) {
    last_fuel = -1;
    for (int i = 0; i < FIRES; i++) fires[i].left = 0;
    for (int i = 0; i < BURNING; i++) burning[i].obj = 0;
}

static void note_burning(void* obj, int ticks) {
    int free_slot = -1;
    for (int i = 0; i < BURNING; i++) {
        if (burning[i].obj == obj) { if (burning[i].left < ticks) burning[i].left = ticks; return; }
        if (burning[i].obj == 0 && free_slot < 0) free_slot = i;
    }
    if (free_slot < 0) return;
    burning[free_slot].obj = obj;
    burning[free_slot].left = ticks;
    burning[free_slot].spread_in = 30;
}

// Sets alight the enemies (and, if allowed, Tribals) whose hit sphere reaches into the sphere.
static void ignite_near(float x, float y, float z, float radius, void* hero, void* except) {
    const int tribals = recomp_get_config_u32("tribals") != 0;
    const int spread_secs = (int)recomp_get_config_double("spread_time");
    JfgNear q = { x, y, z, radius, except };
    JfgEnemy found[NEARBY];
    const int n = jfg_enemies_near(&q, found, NEARBY);
    for (int i = 0; i < n && i < NEARBY; i++) {
        if (found[i].health <= 0 || (found[i].tribal && !tribals)) continue;
        jfg_enemy_ignite(found[i].object, found[i].tribal ? 0 : hero);
        if (spread_secs > 0) note_burning(found[i].object, spread_secs * 60);
    }
}

static void hurt(float x, float y, float z, float radius, int damage, void* hero) {
    JfgDamageSphere d;
    d.x = x;
    d.y = y;
    d.z = z;
    d.radius = radius;
    d.damage = damage;
    d.source = hero; // the source is never hurt: the hero is hit by the fires the game's way (fire_hits_hero)
    d.targets = JFG_TARGET_HEALTH;
    d.props_hit = 0;
    jfg_damage_sphere(&d);
}

// With Fire Hurts You: a hero standing in a ground fire is hit as by a shot (jfg_hero_hit: its hit reaction, sound
// and red flash), once a second while it stays in (the game's protection after a hit decides the rest).
static int burn_in = 0; // 1/60 s ticks until the next one
static void fire_hits_hero(void* hero, const float* hero_pos, int frames) {
    if (burn_in > 0) burn_in -= frames;
    if (burn_in > 0 || recomp_get_config_u32("hurts_you") == 0) return;
    for (int i = 0; i < FIRES; i++) {
        if (fires[i].left <= 0) continue;
        const float dx = fires[i].x - hero_pos[0], dz = fires[i].z - hero_pos[2], dy = hero_pos[1] - fires[i].y;
        if (dy < -30.0f || dy > 60.0f || dx * dx + dz * dz > fires[i].radius * fires[i].radius * 0.5f) continue;
        jfg_hero_hit(hero, (int)recomp_get_config_double("fire_damage") >= 200 ? 2 : 1);
        burn_in = 60;
        return;
    }
}

// Gives back (100 - Fuel Use) % of the fuel burnt since the last tick. Returns 1 if the flamethrower burnt fuel since
// the last tick (it is firing).
static int save_fuel(void) {
    const int fuel = jfg_hero_ammo(WEAPON_FLAMETHROWER);
    if (fuel < 0) { last_fuel = -1; return 0; }
    if (last_fuel >= 0 && fuel < last_fuel && jfg_hero_weapon() == WEAPON_FLAMETHROWER) {
        const int use = (int)recomp_get_config_double("fuel_use"); // percent
        fuel_owed += (last_fuel - fuel) * (100 - use);
        const int back = fuel_owed / 100;
        fuel_owed -= back * 100;
        if (back > 0) {
            jfg_hero_set_ammo(WEAPON_FLAMETHROWER, fuel + back);
            last_fuel = jfg_hero_ammo(WEAPON_FLAMETHROWER);
            return 1;
        }
        last_fuel = fuel;
        return 1;
    }
    last_fuel = fuel;
    return 0;
}

RECOMP_CALLBACK("*", jfg_on_game_tick) void flame_tick(int frames) {
    if (jfg_game_paused()) return; // fires and burns wait while the menus are open
    if (drop_in > 0) drop_in -= frames;
    if (recomp_get_config_u32("enabled") == 0) { last_fuel = -1; return; }
    void* hero = jfg_hero_get();
    if (hero == 0) { last_fuel = -1; return; }
    const int firing = save_fuel();
    const float* hero_pos = (const float*)((unsigned char*)hero + 0x0C);

    // The flames: where the game has them; else, while it burns fuel, a line of points in front of the hero as far as
    // they reach (its facing: object + 0x00; forward is (-sin, -cos): the fires landed behind the hero with (sin, cos)).
    float flames[FLAMES * 3];
    const int n = jfg_hero_weapon() == WEAPON_FLAMETHROWER ? jfg_flames_get(hero, flames, FLAMES) : 0;
    int count = n < FLAMES ? n : FLAMES;
    if (count == 0 && firing) {
        const unsigned int yaw = *(unsigned short*)hero;
        const float fx = -jfg_turn_sin(yaw), fz = -jfg_turn_sin(yaw + 0x4000);
        const float reach = (float)recomp_get_config_double("reach");
        for (int i = 0; i < 6; i++) {
            const float d = reach * (float)(i + 1) / 6.0f;
            flames[i * 3 + 0] = hero_pos[0] + fx * d;
            flames[i * 3 + 1] = hero_pos[1] + 20.0f;
            flames[i * 3 + 2] = hero_pos[2] + fz * d;
        }
        count = 6;
    }
    if (count > 0) {
        const int boost = (int)recomp_get_config_double("flame_damage"); // percent of a unit each second
        for (int i = 0; i < count; i += 3) {
            const float* f = &flames[i * 3];
            if (boost > 0) hurt(f[0], f[1], f[2], 25.0f, boost * 256 / 100 * frames / 60 + 1, hero);
            if (recomp_get_config_u32("spread") != 0) ignite_near(f[0], f[1], f[2], 20.0f, hero, hero);
        }
        // A ground fire where the flames reach: the farthest one from the hero.
        if (recomp_get_config_u32("ground_fire") != 0 && drop_in <= 0) {
            int far = 0;
            float far_d = -1;
            for (int i = 0; i < count; i++) {
                const float dx = flames[i * 3] - hero_pos[0], dz = flames[i * 3 + 2] - hero_pos[2];
                const float d = dx * dx + dz * dz;
                if (d > far_d) { far_d = d; far = i; }
            }
            const float* f = &flames[far * 3];
            const float dy = f[1] - hero_pos[1];
            const float ground = (dy > -60.0f && dy < 60.0f) ? hero_pos[1] : f[1] - 25.0f;
            const int secs10 = (int)recomp_get_config_double("fire_time"); // tenths of a second
            const int size = (int)recomp_get_config_double("fire_size");
            const float radius = (float)size * 1.5f;
            // Not on top of a fire still burning: it is just kept going.
            int slot = -1;
            for (int i = 0; i < FIRES; i++) {
                if (fires[i].left <= 0) continue;
                const float dx = fires[i].x - f[0], dz = fires[i].z - f[2];
                if (dx * dx + dz * dz < radius * radius * 0.36f) { slot = i; break; }
            }
            if (slot >= 0) {
                if (fires[slot].left < secs10 * 6) fires[slot].left = secs10 * 6;
            } else {
                slot = 0;
                for (int i = 0; i < FIRES; i++) if (fires[i].left < fires[slot].left) slot = i;
                fires[slot].x = f[0];
                fires[slot].y = ground;
                fires[slot].z = f[2];
                fires[slot].left = secs10 * 6;
                fires[slot].shown = 0;
                fires[slot].radius = radius;
            }
            drop_in = 24; // a fire every 0.4 s while firing
        }
    }

    fire_hits_hero(hero, hero_pos, frames);

    // The ground fires burn whoever stands in them.
    const int fire_damage = (int)recomp_get_config_double("fire_damage"); // percent of a unit each second
    for (int i = 0; i < FIRES; i++) {
        Fire* fire = &fires[i];
        if (fire->left <= 0) continue;
        // The game's fire, lit again while this one still has time to burn (it lasts 12.7 s at most).
        if (fire->shown <= 0 && fire->left > 30) {
            const int tenths = fire->left / 6 < 127 ? fire->left / 6 : 127;
            jfg_fx_fire(fire->x, fire->y, fire->z, (int)recomp_get_config_double("fire_size"), tenths);
            fire->shown = tenths * 6;
        }
        fire->shown -= frames;
        fire->left -= frames;
        if (fire_damage > 0) hurt(fire->x, fire->y + 15.0f, fire->z, fire->radius, fire_damage * 256 / 100 * frames / 60 + 1, hero);
        ignite_near(fire->x, fire->y + 15.0f, fire->z, fire->radius * 0.6f, hero, 0);
    }

    // Burning enemies pass it on.
    const int spread = recomp_get_config_u32("spread") != 0;
    for (int i = 0; i < BURNING; i++) {
        Burning* b = &burning[i];
        if (b->obj == 0) continue;
        b->left -= frames;
        if (b->left <= 0 || jfg_object_health(b->obj) <= 0) { b->obj = 0; continue; }
        if (!spread) continue;
        b->spread_in -= frames;
        if (b->spread_in > 0) continue;
        b->spread_in = 30; // twice a second
        if (!chance((int)recomp_get_config_double("spread_chance"))) continue;
        const float* p = (const float*)((unsigned char*)b->obj + 0x0C);
        ignite_near(p[0], p[1] + 20.0f, p[2], 70.0f, hero, b->obj);
    }
}
