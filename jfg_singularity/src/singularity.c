// Singularity for Jet Force Gemini: Recompiled (mod API version 6): a thrown black hole.
//
// A new weapon (jfg_weapon_register: "jfg_singularity:singularity", thrown as the grenades are, on the weapon slot the
// port lends modded weapons, with its own HUD icon: the pack's sprite, jfg_weapon_set_icon). The thrown core is the
// pack's own object (a 3D model with the grenade's physics, no code): when our weapon lets go, the game's shot is
// cancelled (jfg_on_weapon_fire) and the core is thrown from the hero's hand the way the hero faces, as far as the
// Throw Distance option says. (Without the pack's objects it is the game's grenade with its fuse held, grenade data
// +0x08, decomp MSR 8c, found as the grenade, kind 0x9B, that appears after our weapon fires.) When it comes to rest (its physics flag
// 2), lands (its first bounce; then it is braked) or flies too long it opens: a black hole that grows, then for a
// while pulls the enemies around it in, heavy ones slowly (their health and size: the port's pull field, jfg_pull_set) and flyers easily
// (high above the floor; they are pulled up or down too, and fly back to their path after: their squad steers them,
// decomp MSR 8d), hurting those at its heart. Then it collapses in the game's grenade explosion (jfg_explosion) and a
// blast (jfg_blast, Collapse Radius) that hits what it gathered. Tribals are pulled too (Pull Tribals) but never hurt by
// the mod; nothing is pulled through walls.
//
// The black hole is a 3D object of the pack's own (jfg_assets.json, build_assets.py: the model from art/, an object
// type with no code and no physics, so it hovers where it is put): spawned where the core opens, spun about its
// vertical, grown as it opens and shrunk as it collapses. Without the pack's objects (its assets not loaded) the core's
// glow and the black hole are pictures drawn over the game at their place on screen (jfg_world_to_screen, the
// overlay, frames.h), hidden while a wall stands between the camera and them. A hum loops while it is open, its whoosh in time with the spin.

#include "jfg_api.h"
#include "jfg_util.h"
#include "frames.h"
#include "icon_big.h"

RECOMP_IMPORT("*", unsigned int recomp_get_config_u32(const char* key));
RECOMP_IMPORT("*", double recomp_get_config_double(const char* key));

#define KIND_GRENADE 0x9B
#define MAX_GRENADES 16
#define MAX_HOLES 4
#define NEARBY 24
#define HOLD 30.0f          // enemies gather this far from the middle
#define CORE 0.3f           // of the reach: close enough to be hurt
#define HURT_TICKS 20
#define OPEN_TICKS 40       // the black hole grows to full size
#define COLLAPSE_TICKS 30   // it shrinks before the blast
#define FLY_LIMIT 150       // a core still flying after this opens anyway
#define SETTLE_SPEED 2.0f   // a landed core this slow (units a tick) opens
#define LANDED_TICKS 20     // a landed core opens this long after its first bounce at most
#define BRAKE 0.8f          // a landed core keeps this much of its speed a tick (a held-fuse grenade rolls on and on)
#define TINT 0x5020A0A0     // caught enemies glow violet
#define FUSE_HELD 0x7FFF
#define IMG_BASE 0x51470000 // our overlay picture ids (ids are shared by all mods): swirl, burst, core
#define IMG_BURST (IMG_BASE + 0x100)
#define IMG_CORE (IMG_BASE + 0x200)
#define SWIRL_TURN 30       // ticks a turn of the swirl takes (the hum's whoosh passes twice a second)
#define SWIRL_RADIUS 75.0f  // level units the swirl picture's half covers at full size
#define CORE_SIZE 30.0f     // level units the core picture covers
#define BURST_TICKS 36      // the burst's frames, spread over this
#define MAX_BURSTS 4
#define SEE_TICKS 6         // how often each picture checks for a wall in front of it
#define BODY_TYPE "jfg_singularity:objtype_blackhole" // the pack's object type (jfg_assets.json)
#define BODY_SCALE 1.15f    // its size when fully open (the model's spiral arms reach 150 units at 1)
#define BODY_SPIN 1092      // yaw a tick: a turn every SWIRL_TURN ticks (0x10000 / 60)
#define BODY_HEIGHT 35.0f   // its middle above where the core opened
#define CORE_TYPE "jfg_singularity:objtype_core"      // the thrown core (jfg_assets.json)
#define ICON_SPRITE "jfg_singularity:sprite_icon"     // the HUD icon
#define CORE_SPIN 2400      // the thrown core's yaw a tick
#define CREDIT_TICKS 600    // kills within this long of our damage are the Singularity's (jfg_weapon_credit): the
                            // dying ones lie down and bleed out a while first
#define EXPLOSION_REACH 160.0f // the grenade explosion's reach (its type 0: radius 150)
#define THROW_PITCH 0x1800  // the throw's pitch when the hero isn't aiming (the grenade's: about 34 degrees up)
#define HAND_HEIGHT 32.0f   // where the core leaves the hero: this high, a little ahead
#define HAND_AHEAD 14.0f

static struct {
    int enabled, give;
    float throw_speed;
    float reach, pull;
    int pull_ticks, damage, burst, tint, debug;
    float blast_radius;
    int pull_tribals;
} cfg;

static void read_config(void) {
    cfg.enabled = recomp_get_config_u32("enabled") != 0;
    cfg.give = recomp_get_config_u32("give") != 0;
    cfg.throw_speed = (float)recomp_get_config_double("throw") / 10.0f; // tenths of a unit a tick
    cfg.reach = (float)recomp_get_config_double("reach");
    cfg.pull = (float)recomp_get_config_double("pull") * 0.07f;          // percent of 7 units a tick
    cfg.pull_ticks = (int)(recomp_get_config_double("duration") * 6.0); // tenths of a second
    cfg.damage = (int)(recomp_get_config_double("damage") * 256.0 / 100.0);
    cfg.burst = (int)(recomp_get_config_double("burst") * 256.0);
    cfg.blast_radius = (float)recomp_get_config_double("blast_radius");
    cfg.pull_tribals = recomp_get_config_u32("pull_tribals") != 0;
    cfg.tint = recomp_get_config_u32("tint") != 0;
    cfg.debug = recomp_get_config_u32("debug") != 0;
}

int weapon_id = -1; // the Singularity's weapon id (ammo.c too)
static int grenades_seen, claims, last_phys = -9; // for the debug line
static int fired_wait;                   // ticks in which a new grenade is ours
static void* known[MAX_GRENADES];        // grenades seen last tick
static int known_count;

typedef struct {
    void* core;          // the thrown core while it flies; 0 once open
    int own_core;        // the core is the pack's object (else the game's grenade)
    int age;             // ticks since thrown, then since it opened
    int landed;          // ticks since its first bounce (0: still in the air)
    float last_vy;
    int open;            // 1 pulling, 2 collapsing
    float x, y, z;
    int pull_id;         // its pull field (jfg_pull_set) while open, else 0 or -1
    int voice;
    int seen, see_in;    // no wall between the camera and it; ticks to the next check
    void* body;          // the 3D black hole (the pack's object), or 0
    void* owner;
} Hole;
static Hole holes[MAX_HOLES];

typedef struct {
    int age;             // -1: none
    float x, y, z, radius;
    int seen;
} Burst;
static Burst bursts[MAX_BURSTS] = { { -1, 0, 0, 0, 0, 0 }, { -1, 0, 0, 0, 0, 0 }, { -1, 0, 0, 0, 0, 0 }, { -1, 0, 0, 0, 0, 0 } };
static int anim;         // ticks, for the swirl
static int body_type = -2; // the pack's object id (-2: not looked up yet, -1: none)
static int core_type = -2;

static void hold_fuse(void* grenade) {
    unsigned char* data = *(unsigned char**)((unsigned char*)grenade + 0x68);
    if (data != 0) *(short*)(data + 0x08) = FUSE_HELD;
}

static int was_known(void* obj) {
    for (int i = 0; i < known_count; i++) if (known[i] == obj) return 1;
    return 0;
}

static Hole* hole_of(void* core) {
    for (int i = 0; i < MAX_HOLES; i++) if (holes[i].core == core && (core != 0)) return &holes[i];
    return 0;
}

static Hole* free_hole(void) {
    for (int i = 0; i < MAX_HOLES; i++) if (holes[i].core == 0 && holes[i].open == 0) return &holes[i];
    return 0;
}

static void release(Hole* h) {
    if (h->pull_id > 0) jfg_pull_end(h->pull_id); // lets go, its tints off
    h->pull_id = -1;
    if (h->voice) jfg_sound_stop(h->voice);
    h->voice = 0;
}

static void free_body(Hole* h) {
    if (h->body != 0) jfg_object_free(h->body);
    h->body = 0;
}

static void clear(Hole* h) {
    release(h);
    free_body(h);
    h->core = 0;
    h->open = 0;
    h->age = 0;
}

// 1 when no wall stands between the camera and the point.
static int in_sight(float x, float y, float z) {
    JfgCameraView cam;
    jfg_camera_get(&cam);
    const float from[3] = { cam.x, cam.y, cam.z }, to[3] = { x, y, z };
    float hit[6];
    if (!jfg_level_ray(from, to, hit)) return 1;
    const float dx = hit[0] - x, dy = hit[1] - y, dz = hit[2] - z;
    return dx * dx + dy * dy + dz * dz < 40.0f * 40.0f; // the floor right under it doesn't count
}

static void hurt(void* enemy, int damage, int overkill) {
    const int health = jfg_object_health(enemy);
    if (damage <= 0 || health <= 0) return;
    int left = health - damage;
    if (left < 0 && !overkill) left = 0;
    jfg_object_set_health(enemy, left);
}

// 1 at the start of the pull; how far it reaches grows as it opens.
static float size_now(Hole* h) {
    if (h->open == 2) return 1.0f - (float)h->age / COLLAPSE_TICKS;
    return h->age < OPEN_TICKS ? (float)h->age / OPEN_TICKS : 1.0f;
}

// The hole's pull field, run by the port (jfg_pull_set): reaching further as it opens, heavier enemies slower and
// flyers drawn in too, those near its middle hurt (the Singularity's damage).
static void pull(Hole* h) {
    JfgPull p = { h->x, h->y, h->z, cfg.reach * (0.4f + 0.6f * size_now(h)), cfg.pull, 0.3f, HOLD, CORE,
                  cfg.damage * HURT_TICKS / 60, HURT_TICKS, cfg.tint ? TINT : 0u,
                  JFG_PULL_MASS | (cfg.pull_tribals ? JFG_PULL_TRIBALS : 0), weapon_id, h->owner };
    h->pull_id = jfg_pull_set(h->pull_id, &p);
}

static void collapse(Hole* h) {
    const float radius = cfg.blast_radius;
    // What dies of the collapse is the Singularity's kill (kill feeds, stats): everything the blasts can reach.
    {
        JfgNear q = { h->x, h->y, h->z, radius > EXPLOSION_REACH ? radius : EXPLOSION_REACH, 0 };
        JfgEnemy near[NEARBY];
        const int n = jfg_enemies_near(&q, near, NEARBY);
        for (int i = 0; i < n && i < NEARBY; i++) {
            if (!near[i].tribal) jfg_weapon_credit(near[i].object, weapon_id, h->owner, CREDIT_TICKS);
        }
    }
    JfgPullCaught caught[NEARBY];
    int caught_count = h->pull_id > 0 ? jfg_pull_caught(h->pull_id, caught, NEARBY) : 0;
    if (caught_count > NEARBY) caught_count = NEARBY;
    for (int i = 0; i < caught_count; i++) {
        if (!caught[i].tribal) jfg_weapon_credit(caught[i].enemy, weapon_id, h->owner, CREDIT_TICKS);
    }
    JfgBlast b = { h->x, h->y, h->z, radius, (float)cfg.burst, 0.25f, h->owner };
    jfg_blast(&b);
    // What it gathered takes the full blow, within the blast's radius (the blast itself fades out to it).
    for (int i = 0; i < caught_count; i++) {
        if (caught[i].tribal) continue;
        const float* p = jfg_obj_pos(caught[i].enemy);
        const float dx = p[0] - h->x, dy = p[1] - h->y, dz = p[2] - h->z;
        if (dx * dx + dy * dy + dz * dz <= radius * radius) hurt(caught[i].enemy, cfg.burst, 1);
    }
    JfgExplosion ex = { 0, h->x, h->y - BODY_HEIGHT * 0.5f, h->z, h->owner }; // the grenade's own explosion
    jfg_explosion(&ex);
    jfg_sound_play("collapse", 1.0f, 0.0f, 1.0f);
    release(h);
}

static void hum(Hole* h, void* hero) {
    float vol = 1.0f, pitch = 0.9f + 0.25f * (h->open == 1 ? (float)h->age / (cfg.pull_ticks + OPEN_TICKS) : 1.0f);
    if (hero != 0) {
        const float* p = jfg_obj_pos(hero);
        const float dx = p[0] - h->x, dz = p[2] - h->z, d = jfg_sqrt(dx * dx + dz * dz);
        vol = 1.1f - d / 2500.0f;
        if (vol > 1.0f) vol = 1.0f;
        if (vol < 0.3f) vol = 0.3f;
    }
    if (h->open == 2) vol *= size_now(h);
    if (h->voice == 0) h->voice = jfg_sound_loop("hum", vol, 0.0f, pitch);
    else jfg_sound_set(h->voice, vol, 0.0f, pitch);
}

static void open_hole(Hole* h, float x, float y, float z) {
    if (h->core != 0) jfg_object_free(h->core);
    h->core = 0;
    h->open = 1;
    h->age = 0;
    h->x = x;
    h->y = y + BODY_HEIGHT;
    h->z = z;
    if (body_type == -2) body_type = jfg_asset_number(BODY_TYPE);
    h->body = 0;
    if (body_type >= 0) {
        JfgSpawn sp = { body_type, h->x, h->y, h->z, 0.0f, 0.0f, 0.0f, 0 };
        h->body = jfg_spawn(&sp);
        if (h->body != 0) jfg_object_set_scale(h->body, 0.01f);
    }
    h->pull_id = -1;
    h->see_in = 0;
    jfg_sound_play("open", 0.9f, 0.0f, 1.0f);
}

RECOMP_CALLBACK("*", jfg_on_level_change) void singularity_level(int level, int character) {
    for (int i = 0; i < MAX_HOLES; i++) {
        if (holes[i].voice) jfg_sound_stop(holes[i].voice);
        holes[i].voice = 0;
        holes[i].core = 0;
        holes[i].open = 0;
        holes[i].pull_id = -1; // the port ends pulls at a level change
        holes[i].body = 0; // gone with the level
    }
    for (int i = 0; i < MAX_BURSTS; i++) bursts[i].age = -1;
    known_count = 0;
    fired_wait = 0;
}

// Throws the pack's core from the hero's hand along the hero's aim, as the game throws a grenade: the aim's yaw, and
// its pitch while the hero aims (or has a target), else a fixed lob; 1 if thrown.
static int throw_core(void* hero) {
    if (core_type == -2) core_type = jfg_asset_number(CORE_TYPE);
    Hole* h = free_hole();
    if (core_type < 0 || h == 0 || hero == 0) return 0;
    const float* p = jfg_obj_pos(hero);
    unsigned int yaw = *(const unsigned short*)hero, pitch = THROW_PITCH;
    JfgAim a;
    if (jfg_hero_aim(hero, &a)) {
        yaw = (unsigned int)a.yaw;
        if (a.pitched) pitch = (unsigned int)a.pitch & 0xFFFF;
    }
    // grenadeInit: (0, 0, -1) turned by the pitch, then the yaw.
    const float cp = jfg_turn_sin(pitch + 0x4000), sp_ = jfg_turn_sin(pitch);
    const float fx = -jfg_turn_sin(yaw) * cp, fy = sp_, fz = -jfg_turn_sin(yaw + 0x4000) * cp;
    const float hx = -jfg_turn_sin(yaw), hz = -jfg_turn_sin(yaw + 0x4000); // ahead, on the ground plane
    const float v = cfg.throw_speed;
    JfgSpawn sp = { core_type, p[0] + hx * HAND_AHEAD, p[1] + HAND_HEIGHT, p[2] + hz * HAND_AHEAD,
                    fx * v, fy * v, fz * v, (int)yaw };
    void* core = jfg_spawn(&sp);
    if (core == 0) return 0;
    h->core = core;
    h->own_core = 1;
    h->age = 0;
    h->landed = 0;
    h->last_vy = 0.0f;
    h->open = 0;
    h->owner = hero;
    h->seen = 1;
    h->see_in = 0;
    claims++;
    return 1;
}

RECOMP_CALLBACK("*", jfg_on_weapon_fire) void singularity_fire(JfgWeaponFire* f) {
    if (weapon_id < 0 || f->weapon != weapon_id) return;
    if (cfg.enabled && throw_core(f->hero)) {
        f->cancel = 1; // the game's grenade isn't made; one Singularity is used
        f->take_ammo = 1;
        return;
    }
    fired_wait = 6; // the game's grenade is the core
}

RECOMP_CALLBACK("*", jfg_on_game_tick) void singularity_tick(int frames) {
    read_config();
    if (weapon_id < 0) {
        JfgWeaponDef d = { "jfg_singularity:singularity", "Singularity", "Singularities", 8, -1, 1, 8, 6, 3, 2 };
        weapon_id = jfg_weapon_register(&d);
        const int icon = jfg_asset_number(ICON_SPRITE);
        if (weapon_id >= 0 && icon >= 0) jfg_weapon_set_icon(weapon_id, icon);
        if (weapon_id >= 0) jfg_weapon_set_icon_image(weapon_id, ICON_BIG_W, ICON_BIG_H, icon_big); // mods' HUDs
    }
    void* hero = jfg_hero_get();
    if (hero == 0 || jfg_game_paused()) return;
    anim += frames;
    for (int i = 0; i < MAX_BURSTS; i++) {
        if (bursts[i].age < 0) continue;
        bursts[i].age += frames;
        if (bursts[i].age >= BURST_TICKS) bursts[i].age = -1;
    }
    if (cfg.enabled && cfg.give && weapon_id >= 0 && !jfg_hero_has_weapon(weapon_id)) jfg_hero_give_weapon(weapon_id, -1);

    // New grenades after our weapon fired are ours, unless another mod has claimed them (jfg_object_claim).
    JfgObjectInfo g[MAX_GRENADES];
    const int n = jfg_objects_of_kind(KIND_GRENADE, g, MAX_GRENADES);
    for (int i = 0; i < n && i < MAX_GRENADES; i++) {
        if (fired_wait > 0 && !was_known(g[i].object) && hole_of(g[i].object) == 0 && jfg_object_claim(g[i].object)) {
            Hole* h = free_hole();
            if (h != 0) {
                h->core = g[i].object;
                h->own_core = 0;
                h->age = 0;
                h->landed = 0;
                h->last_vy = 0.0f;
                h->open = 0;
                h->owner = hero;
                fired_wait = 0;
                claims++;
            }
        }
    }
    grenades_seen = n;
    known_count = 0;
    for (int i = 0; i < n && i < MAX_GRENADES; i++) known[known_count++] = g[i].object;
    if (fired_wait > 0) fired_wait -= frames;

    for (int i = 0; i < MAX_HOLES; i++) {
        Hole* h = &holes[i];
        if (h->core != 0) {
            // Flying: still there? (an explosion or the level may have taken it)
            int there = h->own_core; // the pack's core goes only when we free it (or with the level)
            for (int k = 0; k < n && k < MAX_GRENADES && !there; k++) if (g[k].object == h->core) there = 1;
            if (!there) { clear(h); continue; }
            if (h->own_core) {
                unsigned short* yaw = (unsigned short*)h->core;
                *yaw = (unsigned short)(*yaw + CORE_SPIN * frames);
            } else {
                hold_fuse(h->core);
            }
            h->age += frames;
            if ((h->see_in -= frames) <= 0) {
                const float* cp = jfg_obj_pos(h->core);
                h->seen = in_sight(cp[0], cp[1], cp[2]);
                h->see_in = SEE_TICKS;
            }
            const int phys = jfg_object_physics(h->core);
            last_phys = phys;
            float* v = (float*)((unsigned char*)h->core + 0x1C);
            // Its first bounce (falling, then rising) is the landing; from there it is braked hard.
            if (h->landed == 0 && h->age > 4 && h->last_vy < -0.5f && v[1] >= 0.0f) h->landed = 1;
            h->last_vy = v[1];
            if (h->landed > 0) {
                h->landed += frames;
                for (int f = 0; f < frames; f++) { v[0] *= BRAKE; v[2] *= BRAKE; }
            }
            const float speed = jfg_sqrt(v[0] * v[0] + v[2] * v[2]);
            if ((phys >= 0 && (phys & 2)) || (h->landed > 0 && (speed < SETTLE_SPEED || h->landed >= LANDED_TICKS)) ||
                h->age >= FLY_LIMIT) {
                const float* p = jfg_obj_pos(h->core);
                open_hole(h, p[0], p[1], p[2]);
            }
            continue;
        }
        if (h->open == 0) continue;
        h->age += frames;
        hum(h, hero);
        if (h->body != 0) {
            unsigned short* yaw = (unsigned short*)h->body;
            *yaw = (unsigned short)(*yaw + BODY_SPIN * frames);
            float size = size_now(h);
            if (h->open == 1 && h->age < OPEN_TICKS) size = size * (1.0f + 0.25f * (1.0f - size)); // it pops open
            jfg_object_set_scale(h->body, (size > 0.01f ? size : 0.01f) * BODY_SCALE);
        }
        if ((h->see_in -= frames) <= 0) {
            h->seen = in_sight(h->x, h->y, h->z);
            h->see_in = SEE_TICKS;
        }
        if (h->open == 1) {
            pull(h);
            if (h->age >= OPEN_TICKS + cfg.pull_ticks) {
                h->open = 2;
                h->age = 0;
            }
        } else {
            pull(h);
            if (h->age >= COLLAPSE_TICKS) {
                free_body(h);
                collapse(h);
                clear(h);
            }
        }
    }
}

// --- the looks: pictures over the game ------------------------------------------------------------------------------
static int uploaded;

static void upload(void) {
    for (int i = 0; i < SWIRL_FRAMES; i++) jfg_overlay_image(IMG_BASE + i, FRAME_SIZE, FRAME_SIZE, swirl_frames[i]);
    for (int i = 0; i < BURST_FRAMES; i++) jfg_overlay_image(IMG_BURST + i, FRAME_SIZE, FRAME_SIZE, burst_frames[i]);
    jfg_overlay_image(IMG_CORE, FRAME_SIZE, FRAME_SIZE, core_frames[0]);
    uploaded = 1;
}

// A picture centred on a point of the level, `across` level units wide; 0 if it is behind the camera.
static int picture(int id, float x, float y, float z, float across, unsigned int tint) {
    const float at[3] = { x, y, z };
    float s[4];
    if (!jfg_world_to_screen(at, s)) return 0;
    const float w = across * s[3];
    if (w < 1.0f) return 0;
    JfgOverlayImage img = { s[0] - w * 0.5f, s[1] - w * 0.5f, w, w, tint, id };
    jfg_overlay_draw_image(&img);
    return 1;
}

RECOMP_CALLBACK("*", jfg_on_draw_hud) void singularity_draw(JfgHudGfx* hud) {
    if (!cfg.enabled || jfg_hero_get() == 0) return;
    if (!uploaded) upload();
    const int frame = (anim * SWIRL_FRAMES / SWIRL_TURN) % SWIRL_FRAMES;
    for (int i = 0; i < MAX_HOLES; i++) {
        const Hole* h = &holes[i];
        if (!h->seen) continue;
        if (h->core != 0) {
            if (h->own_core) continue; // a 3D object of its own
            const float* p = jfg_obj_pos(h->core);
            picture(IMG_CORE, p[0], p[1] + 4.0f, p[2], CORE_SIZE, 0xFFFFFFFF);
        } else if (h->open && h->body == 0) {
            float size = size_now((Hole*)h);
            if (size < 0.05f) continue;
            // It opens with a little overshoot, so it pops.
            if (h->open == 1 && h->age < OPEN_TICKS) size = size * (1.0f + 0.25f * (1.0f - size));
            picture(IMG_BASE + frame, h->x, h->y, h->z, SWIRL_RADIUS * 2.0f * size, 0xFFFFFFFF);
        }
    }
    for (int i = 0; i < MAX_BURSTS; i++) {
        const Burst* b = &bursts[i];
        if (b->age < 0 || !b->seen) continue;
        int f = b->age * BURST_FRAMES / BURST_TICKS;
        if (f >= BURST_FRAMES) f = BURST_FRAMES - 1;
        // The picture's ring ends near its edge: the picture spans the blast's reach.
        picture(IMG_BURST + f, b->x, b->y, b->z, b->radius * 2.2f, 0xFFFFFFFF);
    }
}

// --- the debug line (option Debug Line; Recomp-Docs guides/qa.md) ----------------------------------------------------

RECOMP_CALLBACK("*", jfg_on_draw_hud) void singularity_debug(JfgHudGfx* hud) {
    if (!cfg.debug) return;
    static JfgLine l; // static: the overlay may read the text after the call
    l.n = 0;
    l.text[0] = 0;
    jfg_line_str(&l, "id "); jfg_line_num(&l, weapon_id);
    jfg_line_str(&l, " gren "); jfg_line_num(&l, grenades_seen);
    jfg_line_str(&l, " claims "); jfg_line_num(&l, claims);
    jfg_line_str(&l, " phys "); jfg_line_num(&l, last_phys);
    jfg_line_str(&l, " type "); jfg_line_num(&l, body_type);
    {
        const short* items = *(short* const*)0x800A51D0; // the front-end item list: slot 15's icon is entry 25
        jfg_line_str(&l, " icon "); jfg_line_num(&l, items != 0 ? (items[25] & 0x3FFF) : -1);
    }
    for (int i = 0; i < MAX_HOLES; i++) {
        const Hole* h = &holes[i];
        if (h->core == 0 && h->open == 0) continue;
        jfg_line_str(&l, " | "); jfg_line_str(&l, h->core ? "fly " : h->open == 1 ? "pull " : "end ");
        jfg_line_num(&l, h->age); jfg_line_str(&l, "t c"); jfg_line_num(&l, h->pull_id > 0 ? jfg_pull_caught(h->pull_id, 0, 0) : 0);
        if (h->body != 0) {
            const unsigned char* b = (const unsigned char*)h->body;
            jfg_line_str(&l, " body s"); jfg_line_num(&l, (int)(*(const float*)(b + 0x08) * 100.0f));
            jfg_line_str(&l, " k"); jfg_line_num(&l, *(const short*)(b + 0x48));
            jfg_line_str(&l, " seg"); jfg_line_num(&l, *(const short*)(b + 0x2E));
            jfg_line_str(&l, " m"); jfg_line_num(&l, *(const int*)(b + 0x6C) != 0);
            jfg_line_str(&l, " y"); jfg_line_num(&l, (int)((const float*)(b + 0x0C))[1]);
            jfg_line_str(&l, " a"); jfg_line_num(&l, b[0x39]);
        }
        jfg_line_str(&l, " d"); 
        void* hero = jfg_hero_get();
        if (hero != 0) {
            const float* hp = jfg_obj_pos(hero);
            const float x = h->core ? jfg_obj_pos(h->core)[0] : h->x, z = h->core ? jfg_obj_pos(h->core)[2] : h->z;
            const float dx = x - hp[0], dz = z - hp[2];
            jfg_line_num(&l, (int)jfg_sqrt(dx * dx + dz * dz));
        }
    }
    jfg_line_draw(&l);
}
