// Better Shocker for Jet Force Gemini: Recompiled (mod API version 5).
//
// While the hero's shocker beam is on (jfg_shocker_end: where it ends), the enemy it touches is electrocuted (the
// game's own: held in place and drained, with sparks; jfg_enemy_electrocute) and the shock arcs on: from that enemy
// to the nearest other enemy within reach it can see, then from that one to the next, up to the chosen number of
// jumps, each jump weaker (Chain Falloff). Tribals are never chained. Extra damage (Shock Damage) is added along the
// chain.

#include "jfg_api.h"

RECOMP_IMPORT("*", unsigned int recomp_get_config_u32(const char* key));
RECOMP_IMPORT("*", double recomp_get_config_double(const char* key));

#define WEAPON_SHOCKER 4
#define CHAIN_MAX 8
#define NEARBY 16

static int pulse_in = 0; // 1/60 s ticks until the next chain pulse

static void hurt(void* obj, int damage) {
    if (damage <= 0) return;
    const int health = jfg_object_health(obj);
    if (health <= 0) return;
    jfg_object_set_health(obj, health > damage ? health - damage : 0);
}

static int in_chain(void* const* chain, int n, void* obj) {
    for (int i = 0; i < n; i++) if (chain[i] == obj) return 1;
    return 0;
}

RECOMP_CALLBACK("*", jfg_on_game_tick) void shocker_tick(int frames) {
    if (jfg_game_paused()) return;
    if (pulse_in > 0) pulse_in -= frames;
    if (recomp_get_config_u32("enabled") == 0) return;
    void* hero = jfg_hero_get();
    if (hero == 0 || jfg_hero_weapon() != WEAPON_SHOCKER) return;
    float end[3];
    if (!jfg_shocker_end(hero, end)) return;
    if (pulse_in > 0) return;
    pulse_in = (int)(recomp_get_config_double("pulse") * 6.0); // tenths of a second

    // The enemy the beam touches.
    JfgNear q = { end[0], end[1], end[2], 30.0f, hero };
    JfgEnemy found[NEARBY];
    int n = jfg_enemies_near(&q, found, NEARBY);
    void* first = 0;
    float at[3];
    for (int i = 0; i < n && i < NEARBY; i++) {
        if (found[i].tribal || found[i].health <= 0) continue;
        first = found[i].object;
        at[0] = found[i].x; at[1] = found[i].y; at[2] = found[i].z;
        break;
    }
    if (first == 0) return;

    const int stun = recomp_get_config_u32("stun") != 0;
    const int jumps = (int)recomp_get_config_double("jumps");
    const float reach = (float)recomp_get_config_double("reach");
    const int falloff = (int)recomp_get_config_double("falloff");  // percent kept each jump
    int damage = (int)recomp_get_config_double("damage") * 256 / 100; // percent of a unit each pulse

    void* chain[CHAIN_MAX + 1];
    int links = 0;
    chain[links++] = first;
    if (stun) jfg_enemy_electrocute(first, hero);
    hurt(first, damage);
    if (recomp_get_config_u32("chain") == 0) return;

    void* from = first;
    for (int j = 0; j < jumps && j < CHAIN_MAX; j++) {
        JfgNear r = { at[0], at[1], at[2], reach, from };
        n = jfg_enemies_near(&r, found, NEARBY);
        void* next = 0;
        for (int i = 0; i < n && i < NEARBY; i++) {
            if (found[i].tribal || found[i].health <= 0 || in_chain(chain, links, found[i].object)) continue;
            const float to[3] = { found[i].x, found[i].y, found[i].z };
            if (!jfg_line_of_sight(from, found[i].object, at, to)) continue;
            next = found[i].object;
            at[0] = to[0]; at[1] = to[1]; at[2] = to[2];
            break;
        }
        if (next == 0) break;
        damage = damage * falloff / 100;
        if (stun) jfg_enemy_electrocute(next, hero);
        else jfg_enemy_alert(next, hero);
        hurt(next, damage);
        chain[links++] = next;
        from = next;
    }
}
