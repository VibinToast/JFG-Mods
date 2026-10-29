// Better Floyd: Floyd shoots enemies by himself while he follows you, and Hide Floyd (once the port's option), for Jet
// Force Gemini: Recompiled (mod API version 5).
//
// While the game's AI flies Floyd after the hero (not while a player flies him, nor in his own missions), he looks for
// the nearest enemy in range he can see (jfg_enemies_near, jfg_line_of_sight: Tribals are never targets, and one
// standing in the way blocks the shot), in front of him if Only Fire Ahead is on (his facing: object + 0x00, the
// game's angle, forward = (sin, cos)), and not one already dying on the ground (jfg_enemy_dying) unless asked. Once an
// enemy has been his target for the reaction delay he fires his laser bolts at it (jfg_fire_bolt: the bolts he fires
// when a player flies him, with his sound), each aimed a little off by the aim spread. Kills count as the hero's.
// Hide Floyd hides him, his shadow and his sounds, and stops his shooting. Off (the mods menu's switch): none of it.
//
// Tribal Alert, the game's enemy warning in blue: while the hero's aim is locked on an enemy the game blinks Floyd's
// lights red (texture frame 0, every other 32 ticks) and he beeps once. While a Tribal (alive, not yet rescued) is
// within the alert range of the hero, his lights blink his blue frame the same way (jfg_floyd_light) and he chirps once
// when he first spots one (the mod's sound, chirp.wav from make_chirp.py). The enemy warning wins when both apply.
// Works whether or not he shoots.

#include "jfg_api.h"
#include "jfg_util.h"

RECOMP_IMPORT("*", unsigned int recomp_get_config_u32(const char* key));
RECOMP_IMPORT("*", double recomp_get_config_double(const char* key));

#define MAX_TARGETS 16

static int hidden = -1;
static int reload = 0;          // 1/60 s ticks until he may fire again
static int volley = 0;          // bolts left in this volley
static void* target = 0;        // the enemy he has his eye on
static int target_ticks = 0;    // 1/60 s ticks it has been his target
static unsigned int seed = 0x464C4F59;

// Tribal Alert
#define LIGHT_BLUE 1     // Floyd's blue light frame (0 red, 2 green, 3 his usual dark)
#define BLINK      32    // 1/60 s per half blink, as the game's enemy warning
static int alerting = 0; // a Tribal is in range: the blink runs
static int blink_ticks = 0;

RECOMP_CALLBACK("*", jfg_on_level_change) void floyd_level(int level, int character) {
    reload = 60;
    volley = 0;
    alerting = 0;
    target = 0;
    target_ticks = 0;
}

// -1..1
static float rnd(void) {
    seed = seed * 1103515245u + 12345u;
    return (float)((seed >> 8) & 0xFFFF) / 32767.5f - 1.0f;
}

// Whether the point is within the firing arc (degrees, all of it) in front of Floyd, on the ground plane.
static int ahead(void* floyd, const float* pos, const float* to, float arc) {
    const unsigned int yaw = *(unsigned short*)floyd;
    const float fx = jfg_turn_sin(yaw), fz = jfg_turn_sin(yaw + 0x4000);
    const float dx = to[0] - pos[0], dz = to[2] - pos[2];
    const float len = jfg_sqrt(dx * dx + dz * dz);
    if (len < 1.0f) return 1;
    // cos(arc / 2) from the arc in degrees: the game's sine at a quarter turn less half the arc.
    const float half = arc * 0.5f;
    const float cos_half = jfg_turn_sin(0x4000 - (unsigned int)(half * 65536.0f / 360.0f));
    return (fx * dx + fz * dz) / len >= cos_half;
}

static void fire_at(void* floyd, const float* from, const float* to) {
    const float spread = (float)recomp_get_config_double("spread");
    JfgBolt b;
    b.x = from[0];
    b.y = from[1] - 4.0f;
    b.z = from[2];
    b.tx = to[0] + rnd() * spread;
    b.ty = to[1] + rnd() * spread * 0.5f;
    b.tz = to[2] + rnd() * spread;
    b.damage = (int)recomp_get_config_double("damage");
    b.speed = 35.0f;
    b.life = 30;
    b.owner = floyd;
    b.sound = 0xDA;
    jfg_fire_bolt(&b);
}

static void alert_off(void) {
    if (alerting) jfg_floyd_light(-1);
    alerting = 0;
}

// A living Tribal within the alert range of the hero: Floyd's lights blink blue, and he chirps on spotting it.
static void tribal_alert(void* hero, int frames) {
    const float* at = (const float*)((unsigned char*)hero + 0x0C);
    JfgNear q;
    q.x = at[0];
    q.y = at[1];
    q.z = at[2];
    q.radius = (float)recomp_get_config_double("alert_range");
    q.source = hero;
    JfgEnemy found[MAX_TARGETS];
    const int n = jfg_enemies_near(&q, found, MAX_TARGETS);
    int near = 0;
    for (int i = 0; i < n && i < MAX_TARGETS && !near; i++) near = found[i].tribal && found[i].health > 0;
    if (!near) { alert_off(); return; }
    if (!alerting) {
        alerting = 1;
        blink_ticks = 0;
        jfg_sound_play("chirp", 0.45f, 0.0f, 1.0f);
    }
    jfg_floyd_light(blink_ticks / BLINK % 2 == 0 ? LIGHT_BLUE : -1); // blue first, then his usual frame
    blink_ticks += frames;
}

RECOMP_CALLBACK("*", jfg_on_game_tick) void floyd_tick(int frames) {
    const int on = recomp_get_config_u32("enabled") != 0;
    const int hide = on && recomp_get_config_u32("hide") != 0;
    if (hide != hidden) {
        jfg_floyd_hide(hide);
        hidden = hide;
    }
    if (jfg_game_paused()) return; // the menus are open: he holds his fire
    if (reload > 0) reload -= frames;
    int state = 0;
    void* floyd = jfg_floyd_get(&state);
    void* hero = jfg_hero_get();
    if (on && floyd != 0 && state == 0 && !hide && hero != 0 && recomp_get_config_u32("tribal_alert") != 0)
        tribal_alert(hero, frames);
    else
        alert_off();
    if (!on || floyd == 0 || state != 0 || hide || recomp_get_config_u32("shoots") == 0) {
        volley = 0;
        target = 0;
        return;
    }
    if (hero == 0 || jfg_hero_state(hero) == JFG_HERO_DEAD) return;

    // The nearest enemy he may shoot at.
    const float* pos = (const float*)((unsigned char*)floyd + 0x0C);
    JfgNear q;
    q.x = pos[0];
    q.y = pos[1];
    q.z = pos[2];
    q.radius = (float)recomp_get_config_double("range");
    q.source = floyd;
    JfgEnemy found[MAX_TARGETS];
    const int n = jfg_enemies_near(&q, found, MAX_TARGETS);
    const int ahead_only = recomp_get_config_u32("ahead") != 0;
    const float arc = (float)recomp_get_config_double("arc");
    const int skip_dying = recomp_get_config_u32("ignore_dying") != 0;
    const JfgEnemy* best = 0;
    for (int i = 0; i < n && i < MAX_TARGETS; i++) {
        const JfgEnemy* e = &found[i];
        if (e->tribal || e->health <= 0) continue;
        if (skip_dying && jfg_enemy_dying(e->object) == 1) continue;
        const float at[3] = { e->x, e->y, e->z };
        if (ahead_only && !ahead(floyd, pos, at, arc)) continue;
        if (!jfg_line_of_sight(floyd, e->object, pos, at)) continue;
        if (best == 0 || e->object == target) best = e; // the nearest, but he keeps his current one while he can
        if (e->object == target) break;
    }
    if (best == 0) {
        target = 0;
        target_ticks = 0;
        volley = 0;
        return;
    }
    if (best->object != target) {
        target = best->object;
        target_ticks = 0;
        volley = 0;
    }
    target_ticks += frames;
    if (target_ticks < (int)(recomp_get_config_double("delay") * 6.0)) return; // reaction time, tenths of a second
    if (reload > 0) return;

    const float at[3] = { best->x, best->y, best->z };
    fire_at(floyd, pos, at);
    if (volley <= 0) volley = (int)recomp_get_config_u32("burst") + 1; // One, Two, Three
    volley--;
    // Between bolts of a volley a short pause; after it, the chosen fire interval (tenths of a second).
    reload = volley > 0 ? 6 : (int)(recomp_get_config_double("interval") * 6.0);
}
