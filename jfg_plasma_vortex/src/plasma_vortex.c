// Plasma Vortex for Jet Force Gemini: Recompiled (mod API version 6).
//
// A charged plasma shotgun ball (the game's own: kind JFG_KIND_PLASMA, its charge 1..4 read from its data) pulls the
// enemies around it in: it slows to a hover where it is headed (its speed, object + 0x1C..0x24, eased off each tick)
// and stays a little longer (its time, data + 0x12, in 1/60 s), and each tick the enemies around it slide toward it,
// faster the closer they are, until they bunch up
// around it, tinted blue, and those close to it take damage. When the ball is gone (its time is up or it hit a wall)
// it bursts where it last was: everything it gathered takes a blow, enough to burst the weak ones, with a big plasma
// flash (jfg_fire_plasma) and a bang. The pull reaches further and pulls harder the more the shot was charged.
// Tribals are never pulled nor hurt by it, and an enemy is only pulled while nothing stands between it and the ball.
// The port tells the mod as balls are made and freed (jfg_object_watch); a ball another mod drives (jfg_object_claim)
// is left alone.

#include "jfg_api.h"
#include "jfg_util.h"

RECOMP_IMPORT("*", unsigned int recomp_get_config_u32(const char* key));
RECOMP_IMPORT("*", double recomp_get_config_double(const char* key));

#define MAX_BALLS 24       // vortices followed at once
#define NEARBY 24
#define HOLD 34.0f          // enemies gather this far from the ball's middle
#define CORE 0.35f          // of the reach: close enough to take the vortex's damage
#define HURT_TICKS 15       // 1/60 s ticks between the vortex's damage
#define TINT 0x3C78FF90     // caught enemies glow blue
#define SOUND_BURST 0x22    // the game's blast
#define DRAG 0.92f          // a vortex keeps this much of its speed each 1/60 s: it stops within about half a second

static struct {
    int enabled;
    int min_charge;   // 1..4: the least charge that makes a vortex
    float reach;      // at full charge, level units
    float pull;       // level units per 1/60 s at full charge, at the ball
    int damage;       // per second inside, 256 a unit, at full charge
    int burst;        // the burst's blow at full charge, 256 a unit
    int stun, tint;
    int hover;        // extra 1/60 s ticks a vortex stays
} cfg;

static void read_config(void) {
    cfg.enabled = recomp_get_config_u32("enabled") != 0;
    cfg.min_charge = (int)recomp_get_config_double("min_charge");
    cfg.reach = (float)recomp_get_config_double("reach");
    cfg.pull = (float)recomp_get_config_double("pull") * 0.06f; // percent of 6 units a tick
    cfg.damage = (int)(recomp_get_config_double("damage") * 256.0 / 100.0);
    cfg.burst = (int)(recomp_get_config_double("burst") * 256.0);
    cfg.stun = recomp_get_config_u32("stun") != 0;
    cfg.tint = recomp_get_config_u32("tint") != 0;
    cfg.hover = (int)(recomp_get_config_double("hover") * 6.0); // tenths of a second
}

typedef struct {
    void* obj;
    int charge;         // 1..4; 0: not a vortex (too little charge, or our own burst flash)
    float x, y, z;      // where it was last seen
    int pull_id;        // its pull field (jfg_pull_set), -1 none yet
} Ball;
static Ball balls[MAX_BALLS];
static int ball_count;
static void* flashes[4];  // our burst flashes: plasma balls that are not vortices
static int next_flash;

// The shot's charge: its data (object + 0x68) + 0x11 is 0xFE - (charge - 1) (twisterInit, overlay 131).
static int charge_of(void* obj) {
    const unsigned char* data = *(const unsigned char**)((unsigned char*)obj + 0x68);
    if (data == 0) return 0;
    const int c = 0xFF - data[0x11];
    return c >= 1 && c <= 4 ? c : 0;
}

static int is_flash(void* obj) {
    for (int i = 0; i < 4; i++) if (flashes[i] == obj) return 1;
    return 0;
}

static void hurt(void* enemy, int damage, int overkill) {
    const int health = jfg_object_health(enemy);
    if (damage <= 0 || health <= 0) return;
    int left = health - damage;
    if (left < 0 && !overkill) left = 0;
    jfg_object_set_health(enemy, left);
}

static void release(Ball* b) {
    if (b->pull_id >= 0) jfg_pull_end(b->pull_id); // lets go, its tints off
    b->pull_id = -1;
}

static void burst(Ball* b, void* hero) {
    const float scale = b->charge / 4.0f, reach = cfg.reach * (0.5f + 0.5f * scale);
    JfgNear q = { b->x, b->y, b->z, reach * 0.6f, hero };
    JfgEnemy found[NEARBY];
    const int n = jfg_enemies_near(&q, found, NEARBY);
    for (int i = 0; i < n && i < NEARBY; i++) {
        if (found[i].tribal || found[i].health <= 0) continue;
        hurt(found[i].object, (int)(cfg.burst * scale), 1);
        if (hero != 0) jfg_enemy_alert(found[i].object, hero);
    }
    release(b);
    // The flash: a big plasma ball that stays put for a moment (it hurts what touches it, as the shotgun's).
    JfgPlasma p = { b->x, b->y, b->z, b->x, b->y, b->z - 1.0f, 4, 0.0f, 3, hero };
    void* flash = jfg_fire_plasma(&p);
    if (flash != 0) {
        flashes[next_flash] = flash;
        next_flash = (next_flash + 1) % 4;
    }
    jfg_game_sound(SOUND_BURST, b->x, b->y, b->z);
}

// The ball's pull field, run by the port (jfg_pull_set): it reaches further and pulls harder the more it was charged,
// a third as hard at the edge; those near its middle take damage, the more charged the more.
static void pull(Ball* b, void* hero) {
    const float scale = b->charge / 4.0f;
    JfgPull p = { b->x, b->y, b->z, cfg.reach * (0.5f + 0.5f * scale), cfg.pull * scale, 0.33f, HOLD, CORE,
                  cfg.damage * HURT_TICKS / 60 * b->charge / 4, HURT_TICKS, cfg.tint ? TINT : 0u,
                  cfg.stun ? JFG_PULL_STUN : 0, -1, hero };
    b->pull_id = jfg_pull_set(b->pull_id, &p);
}

RECOMP_CALLBACK("*", jfg_on_level_change) void vortex_level(int level, int character) {
    ball_count = 0;
    for (int i = 0; i < 4; i++) flashes[i] = 0;
}

// A new ball: a vortex if charged enough, unless it is our own burst flash or another mod drives it.
RECOMP_CALLBACK("*", jfg_on_object_spawn) void vortex_spawn(void* obj, int kind) {
    if (kind != JFG_KIND_PLASMA || !cfg.enabled || ball_count == MAX_BALLS) return;
    int charge = is_flash(obj) ? 0 : charge_of(obj);
    if (charge < cfg.min_charge) charge = 0;
    if (charge == 0 || !jfg_object_claim(obj)) return;
    Ball* b = &balls[ball_count++];
    b->obj = obj;
    b->charge = charge;
    b->pull_id = -1;
    const float* p = jfg_obj_pos(obj);
    b->x = p[0];
    b->y = p[1];
    b->z = p[2];
    if (cfg.hover > 0) { // it stays longer, to hover
        unsigned char* data = *(unsigned char**)((unsigned char*)obj + 0x68);
        if (data != 0) {
            short* time = (short*)(data + 0x12);
            const int t = *time + cfg.hover;
            *time = (short)(t > 0x7FFF ? 0x7FFF : t);
        }
    }
}

// A ball gone: it bursts where it last was.
RECOMP_CALLBACK("*", jfg_on_object_free) void vortex_free(void* obj, int kind) {
    for (int i = 0; i < ball_count; i++) {
        Ball* b = &balls[i];
        if (b->obj != obj) continue;
        if (cfg.enabled) burst(b, jfg_hero_get());
        else release(b);
        ball_count--;
        if (i != ball_count) { // the last takes its place (word by word: no memcpy in a mod)
            unsigned int* to = (unsigned int*)&balls[i];
            const unsigned int* from = (const unsigned int*)&balls[ball_count];
            for (unsigned int w = 0; w < sizeof(Ball) / 4; w++) to[w] = from[w];
        }
        return;
    }
}

RECOMP_CALLBACK("*", jfg_on_game_tick) void vortex_tick(int frames) {
    read_config();
    jfg_object_watch(JFG_KIND_PLASMA, cfg.enabled);
    if (jfg_game_paused()) return;
    void* hero = jfg_hero_get();
    for (int i = 0; i < ball_count; i++) {
        Ball* b = &balls[i];
        const float* p = jfg_obj_pos(b->obj);
        b->x = p[0];
        b->y = p[1];
        b->z = p[2];
        if (cfg.hover > 0) {
            float* v = jfg_obj_vel(b->obj);
            float keep = 1.0f;
            for (int f = 0; f < frames; f++) keep *= DRAG;
            v[0] *= keep;
            v[1] *= keep;
            v[2] *= keep;
        }
        pull(b, hero);
    }
}
