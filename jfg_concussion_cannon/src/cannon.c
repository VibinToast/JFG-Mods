// Concussion Cannon: a new weapon that charges like the plasma shotgun and lets go a cone of force along the hero's aim.
// - The weapon (jfg_weapon_register: "jfg_concussion_cannon:cannon") is held on the slot the port lends modded weapons,
//   with the plasma shotgun's row (host 3: hold to charge, let go to fire; the port charges it at the shotgun's rate and
//   fills the HUD's charge bar, decomp MSR 10b). On the shot the game's bolt is cancelled (jfg_on_weapon_fire) and the
//   charge level (1..5, charge >> 5) sets how far and how hard the blast reaches.
// - The blast: every enemy in a cone along the aim (the aim's yaw, and its pitch while aiming, as the game aims a shot),
//   in sight of the hero, is knocked away, heavy ones less (mass from full health and hit radius, as the Singularity
//   weighs them). They are flung the game's own way (decomp MSR 10c: velocity, track collision, AI off until they
//   touch something; flyers for a few calls, spinning). A wall touched fast enough (the member's touch flags) is a
//   slam: damage by how fast, an impact effect, and the kill is the cannon's (jfg_weapon_credit). Members the game
//   doesn't move that way are slid by the mod and test walls with jfg_level_ray.
// - The hero is pushed back (jfg_hero_push) and the view shakes (jfg_camera_shake) by the charge level. The cannon is in
//   the hero's hand (jfg_weapon_set_held_model, the pack's model); a slam also sets off the game's small flash.
// - Sounds are the mod's own (make_sounds.py): a charge hum rising with the charge, a cue when full, the blast, slams.
// - Effects: the pack's objects (art/, build_assets.py) when the pack has them, else the game's flat shockwave ring.

#include "jfg_api.h"
#include "jfg_util.h"
#include "icon_big.h"

RECOMP_IMPORT("*", unsigned int recomp_get_config_u32(const char* key));
RECOMP_IMPORT("*", double recomp_get_config_double(const char* key));

#define HOST 3              // the plasma shotgun: hold to charge
#define LEVELS 5            // charge levels (its row's +0x03 = 5: charge 32..160)
#define MAX_KNOCKED 24
#define NEARBY 24
#define FLYER_HEIGHT 35.0f  // above the floor: a flyer
#define FLYER_LIFT 0.35f    // of the push, upward for a flyer
#define FLYER_SPIN 3000     // yaw a tick while a flyer is knocked
#define SLIDE_KEEP 0.90f    // a knocked enemy keeps this much of its speed a tick
#define STOP_SPEED 0.6f     // slower than this (units a tick): no longer knocked
#define SLAM_SPEED 3.0f     // a wall hit this fast or faster slams
#define SLAM_REACH 12.0f    // a wall this far ahead of its body counts as hit
#define KNOCK_TICKS 90      // knocked for this long at most
#define CREDIT_TICKS 600    // kills within this long of a blow are the cannon's
#define MUZZLE_HEIGHT 30.0f // where the blast leaves the hero: this high, a little ahead
#define MUZZLE_AHEAD 20.0f
#define CHARGE 0x53E        // the hero's control data: s16 charge (32 up), u8 flags (bit 7 charging)
#define CHARGE_FLAGS 0x540
#define CHARGING 0x80
#define WAVE_TYPE "jfg_concussion_cannon:objtype_wave"     // the pack's objects (jfg_assets.json)
#define IMPACT_TYPE "jfg_concussion_cannon:objtype_impact"
#define ORB_TYPE "jfg_concussion_cannon:objtype_charge"
#define ICON_SPRITE "jfg_concussion_cannon:sprite_icon"
#define HELD_MODEL "jfg_concussion_cannon:model_cannon"    // in the hero's hand (jfg_weapon_set_held_model)
#define FLASH_EXPLOSION 3   // the game's small explosion with a light flash, a ring and no damage (decomp MSR 10d)
#define WAVE_TICKS 50       // the blast's wave flies, grows and fades out over this long
#define WAVE_SPEED 14.0f    // units a tick at first, slowing (WAVE_KEEP a tick)
#define WAVE_KEEP 0.93f
#define WAVE_AIM_AHEAD 70.0f // aiming: the wave starts this far ahead, smaller, so the view isn't inside it
#define AIM_AHEAD 45.0f     // aiming: the muzzle (and the charge orb) this far ahead of the hero, this high, this
#define AIM_HEIGHT 38.0f    //   far to the right
#define AIM_RIGHT 12.0f
#define FADE_TOP 140.0f     // a fading effect's opacity at its most (255 solid)
#define FADE_FROM 0.3f      // a fading effect is solid for this much of its life, then fades out
#define IMPACT_TICKS 20
#define FLING_CALL 2.0f     // a fling's speed a squad call (the squads move once per 1/30 s) from units a 1/60 s tick
#define FLING_UP 4.0f       // a walker's fling upward, plus some with the charge (the game's own knock-back: 5..14)
#define FLING_CALLS 14      // a flyer's AI is off for this many calls
#define WALK_CALLS 12       // a walker's
#define FLING_SLAM 3.5f     // a flung member hitting a wall this fast or faster (units a call) slams
#define SQ_FLAGS0 0x00      // the squad member's control data (object + 0x68): its flag word, big-endian; byte 0:
#define SQ_B25 0x02         //   no physics move, b26 airborne (AI off until it touches), b28 launched (AI off for
#define SQ_B26 0x04         //   +0x17 calls); byte 1: b18 track collision; byte 2: b9 riding (with byte 3 b4 clear)
#define SQ_B28 0x10
#define SQ_B18 0x04
#define SQ_B9 0x02
#define SQ_B4 0x10
#define SQ_CALLS 0x17
#define SQ_TOUCH 0x18       // what its last move touched: 0x10 floor, 0x20 wall, 0x40 ceiling
#define TOUCH_WALL 0x20

static struct {
    int enabled, give;
    float range, cone_cos, power;
    int damage, slam_damage;
    float recoil, shake;
    int push_tribals, debug, infinite;
} cfg;

static void read_config(void) {
    cfg.enabled = recomp_get_config_u32("enabled") != 0;
    cfg.give = recomp_get_config_u32("give") != 0;
    cfg.range = (float)recomp_get_config_double("range");
    const double half = recomp_get_config_double("cone") * 0.5 * 3.14159265 / 180.0; // degrees, the whole cone
    cfg.cone_cos = (float)(1.0 - half * half / 2.0 + half * half * half * half / 24.0);  // cos, close enough to 90
    cfg.power = (float)recomp_get_config_double("power") * 0.36f;                       // percent of 36 units a tick
    cfg.damage = (int)(recomp_get_config_double("damage") * 256.0 / 100.0);
    cfg.slam_damage = (int)(recomp_get_config_double("slam") * 256.0 / 100.0);
    cfg.recoil = (float)recomp_get_config_double("recoil") / 100.0f;
    cfg.shake = (float)recomp_get_config_double("shake") / 100.0f;
    cfg.push_tribals = recomp_get_config_u32("push_tribals") != 0;
    cfg.debug = recomp_get_config_u32("debug") != 0;
    cfg.infinite = recomp_get_config_u32("infinite") != 0;
}

int weapon_id = -1;

typedef struct {
    void* object;
    float vx, vy, vz;
    int ticks;
    int flyer;
    int tribal;
    int flung;     // moved by the game's own physics (decomp MSR 10c), else by the mod
    float speed;   // its speed last tick (flung: the game's units a call)
    float peak;    // its recent top speed (the slam's strength)
    float strength; // the shot's, 0.2 .. 1
    int damage;    // the blast's damage, dealt when the throw ends: a hit's reaction would stop the throw
    int reflings;  // throws given again when the game took the first one back
} Knocked;
static Knocked knocked[MAX_KNOCKED];


static int orb_type = -2;
static void* orb;           // the charge orb at the hero's hand while charging
static int charge_voice, was_full, last_level, last_hit, last_slams;
static void* dbg_object;    // the first member the last shot flung, for the debug line
static float dbg_v;

static unsigned char* control(void* hero) { return *(unsigned char**)((unsigned char*)hero + 0x68); }

// The hero's aim as a direction (x, y, z) and its yaw: the aim's pitch while aiming or with a target, else level
// (jfg_hero_aim).
static unsigned int aim(void* hero, float* d) {
    JfgAim a;
    if (!jfg_hero_aim(hero, &a)) { d[0] = 0.0f; d[1] = 0.0f; d[2] = -1.0f; return 0; }
    d[0] = a.dir[0];
    d[1] = a.dir[1];
    d[2] = a.dir[2];
    return (unsigned int)a.yaw;
}

// Where the blast leaves: the gun's barrel as the game keeps it (jfg_hero_barrel), else a little ahead of the hero.
static int aiming(void* hero) {
    JfgAim a;
    return jfg_hero_aim(hero, &a) && a.aiming;
}

static void muzzle(void* hero, const float* d, float* m) {
    const float* p = jfg_obj_pos(hero);
    if (aiming(hero)) {
        // The aim view looks from the hero's head and the gun isn't drawn (nor its barrel kept): just ahead of the
        // view, low and to the right, where the gun would be.
        m[0] = p[0] + d[0] * AIM_AHEAD - d[2] * AIM_RIGHT;
        m[1] = p[1] + AIM_HEIGHT + d[1] * AIM_AHEAD;
        m[2] = p[2] + d[2] * AIM_AHEAD + d[0] * AIM_RIGHT;
        return;
    }
    if (jfg_hero_barrel(hero, m)) return;
    m[0] = p[0] + d[0] * MUZZLE_AHEAD;
    m[1] = p[1] + MUZZLE_HEIGHT;
    m[2] = p[2] + d[2] * MUZZLE_AHEAD;
}

// --- effects ---------------------------------------------------------------------------------------------------------
// The port runs each effect's life (jfg_fx_spawn): moved and slowed by keep a tick, grown easing out, and with fade
// solid for FADE_FROM of its life, then faded out.
static void* effect(const char* name, const float* at, unsigned int yaw, float v_speed, const float* dir, int ticks,
                    float from, float to, float keep, int fade) {
    JfgFx fx = { name, at[0], at[1], at[2], (int)yaw,
                 dir ? dir[0] * v_speed : 0.0f, dir ? dir[1] * v_speed : 0.0f, dir ? dir[2] * v_speed : 0.0f,
                 keep, ticks, from, to, 1, fade ? (int)FADE_TOP : 255, fade ? FADE_FROM : 1.0f };
    return jfg_fx_spawn(&fx);
}

static void ring(const float* at, float size) {
    JfgShockwave w = { at[0], at[1], at[2], 0.0f, size * 0.2f, size * 0.12f, size * 0.16f, 4, 10 };
    jfg_shockwave(&w);
}

// --- the blast -------------------------------------------------------------------------------------------------------
static Knocked* knock_slot(void* obj) {
    Knocked* free_one = 0;
    for (int i = 0; i < MAX_KNOCKED; i++) {
        if (knocked[i].object == obj) return &knocked[i];
        if (knocked[i].object == 0 && free_one == 0) free_one = &knocked[i];
    }
    return free_one;
}

static float mass_of(void* enemy, int* flyer) {
    JfgEnemyTraits t;
    float mass = 1.0f;
    *flyer = 0;
    if (jfg_enemy_traits(enemy, &t)) {
        mass = 1.0f + t.full_health / 256.0f / 12.0f + t.radius / 50.0f; // tough and big: heavier, at most 2.2
        if (mass > 2.2f) mass = 2.2f;
        if (t.height > FLYER_HEIGHT) { mass *= 0.5f; *flyer = 1; }        // flyers: light
    }
    return mass;
}

// Flings a squad member the game's way (jfg_enemy_fling): its velocity, track collision, and its AI off until it
// touches something (walkers) or for some calls (flyers). 0 if it can't be (the mover skips it): the mod moves it.
static int fling(Knocked* k, float strength) {
    JfgFling f;
    f.vx = k->vx * FLING_CALL;
    f.vz = k->vz * FLING_CALL;
    f.vy = k->flyer ? k->vy * FLING_CALL : FLING_UP * 0.5f + 7.0f * strength + (k->vy > 0.0f ? k->vy : 0.0f);
    f.calls = k->flyer ? FLING_CALLS : WALK_CALLS;
    if (!jfg_enemy_fling(k->object, &f)) return 0;
    k->speed = jfg_sqrt(f.vx * f.vx + f.vz * f.vz);
    if (dbg_object == 0) { dbg_object = k->object; dbg_v = k->speed; }
    return 1;
}

static void slam(Knocked* k, void* hero, const float* at, float speed, float threshold) {
    const int dmg = (int)(cfg.slam_damage * (speed / (threshold * 2.0f)));
    jfg_weapon_credit(k->object, weapon_id, hero, CREDIT_TICKS);
    const int h = jfg_object_health(k->object);
    if (dmg > 0 && h > 0) jfg_object_set_health(k->object, h - dmg > 0 ? h - dmg : 0);
    void* imp = effect(IMPACT_TYPE, at, 0, 0.0f, 0, IMPACT_TICKS, 0.4f, 1.1f, 1.0f, 1);
    if (imp == 0) ring(at, 30.0f);
    JfgExplosion flash = { FLASH_EXPLOSION, at[0], at[1], at[2], hero };
    jfg_explosion(&flash);
    const float vol = 0.25f + 0.05f * (speed / threshold); // quieter: several slams can come at once
    jfg_sound_play("slam", vol < 0.45f ? vol : 0.45f, 0.0f, 1.0f);
    last_slams++;
}

static void blast(void* hero, int level) {
    float d[3], m[3];
    const unsigned int yaw = aim(hero, d);
    muzzle(hero, d, m);
    const float strength = (float)level / LEVELS;            // 0.2 .. 1
    // A tap is a short shove, a full charge throws: the push rises with the square of the charge (about 5x apart).
    const float range = cfg.range * (0.35f + 0.65f * strength);
    const float push = cfg.power * (0.2f + 1.1f * strength * strength);

    const int aim_view = aiming(hero);
    float w_at[3] = { m[0], m[1], m[2] };
    if (aim_view) for (int i = 0; i < 3; i++) w_at[i] += d[i] * WAVE_AIM_AHEAD;
    void* wave = effect(WAVE_TYPE, w_at, yaw, WAVE_SPEED, d, aim_view ? WAVE_TICKS * 2 / 3 : WAVE_TICKS,
                        0.3f, aim_view ? 0.7f + 0.7f * strength : 1.0f + 1.2f * strength, WAVE_KEEP, 1);
    if (wave == 0) {
        float at[3] = { m[0] + d[0] * 40.0f, m[1] - MUZZLE_HEIGHT + 4.0f, m[2] + d[2] * 40.0f };
        ring(at, 30.0f + 40.0f * strength);
    }
    jfg_sound_play("blast", 0.6f + 0.4f * strength, 0.0f, 1.25f - 0.3f * strength);
    if (cfg.shake > 0) jfg_camera_shake((int)(cfg.shake * (3.0f + 9.0f * strength)), (int)(300 + 700 * strength));
    if (cfg.recoil > 0.0f) jfg_hero_push(hero, -d[0] * 3.0f * strength * cfg.recoil, -d[2] * 3.0f * strength * cfg.recoil,
                                         (int)(8 + 10 * strength));

    JfgNear q = { m[0], m[1], m[2], range, hero };
    JfgEnemy found[NEARBY];
    const int n = jfg_enemies_near(&q, found, NEARBY);
    last_hit = 0;
    dbg_object = 0;
    for (int i = 0; i < n && i < NEARBY; i++) {
        JfgEnemy* e = &found[i];
        if (e->tribal && !cfg.push_tribals) continue;
        const float tx = e->x - m[0], ty = e->y - m[1], tz = e->z - m[2];
        const float dist = jfg_sqrt(tx * tx + ty * ty + tz * tz);
        if (dist > 1.0f) {
            // In the cone: measured flat for the yaw (enemies stand above or below the muzzle) unless aiming up/down.
            const float flat = jfg_sqrt(tx * tx + tz * tz);
            const float c = d[1] > 0.2f || d[1] < -0.2f ? (tx * d[0] + ty * d[1] + tz * d[2]) / dist
                                                        : flat > 1.0f ? (tx * d[0] + tz * d[2]) / flat : 1.0f;
            if (c < cfg.cone_cos && dist > e->radius + 20.0f) continue;
        }
        const float to[3] = { e->x, e->y, e->z };
        if (!jfg_line_of_sight(hero, e->object, m, to)) continue;
        int flyer;
        const float mass = mass_of(e->object, &flyer);
        const float near = 1.0f - 0.5f * (dist / range);     // closer: harder
        float k = push * near / mass;
        // Away from the muzzle, mostly along the aim.
        float ax = dist > 1.0f ? tx / dist : d[0], az = dist > 1.0f ? tz / dist : d[2];
        ax = ax * 0.5f + d[0] * 0.5f;
        az = az * 0.5f + d[2] * 0.5f;
        const float len = jfg_sqrt(ax * ax + az * az);
        if (len > 0.01f) { ax /= len; az /= len; }
        Knocked* kn = knock_slot(e->object);
        if (kn == 0) continue;
        const int pending = kn->object == e->object ? kn->damage : 0; // still flying from an earlier blast
        kn->object = e->object;
        kn->vx = ax * k;
        kn->vz = az * k;
        kn->vy = flyer ? k * FLYER_LIFT : d[1] * k;
        kn->ticks = 0;
        kn->flyer = flyer;
        kn->tribal = e->tribal;
        kn->speed = jfg_sqrt(kn->vx * kn->vx + kn->vz * kn->vz);
        kn->strength = strength;
        kn->damage = pending;
        kn->reflings = 0;
        kn->flung = fling(kn, strength);
        kn->peak = kn->speed;
        last_hit++;
        if (!e->tribal) {
            jfg_weapon_credit(e->object, weapon_id, hero, CREDIT_TICKS);
            if (cfg.damage > 0) kn->damage += (int)(cfg.damage * strength * near); // when the throw ends
        }
    }
}

// The throw is over: the blast's damage now (a hit reaction no longer stops the throw), and the slot is free.
static void finish(Knocked* k) {
    if (k->damage > 0 && !k->tribal) {
        const int h = jfg_object_health(k->object);
        if (h > 0) jfg_object_set_health(k->object, h - k->damage > 0 ? h - k->damage : 0);
    }
    k->damage = 0;
    k->object = 0;
}

// Each tick: knocked enemies slide (moving their position sticks: they steer back to their path afterwards) and slam
// into walls.
static void tick_knocked(void* hero, int frames) {
    for (int i = 0; i < MAX_KNOCKED; i++) {
        Knocked* k = &knocked[i];
        if (k->object == 0) continue;
        if (!k->flung && jfg_object_health(k->object) <= 0 && k->ticks > 0 && !k->tribal) { k->object = 0; continue; }
        k->ticks += frames;
        if (k->flung) {
            // The game moves it. A wall touched on its last move, fast enough: a slam; then it stops against the
            // wall (the game keeps pushing a member that doesn't bounce into it).
            unsigned char* o = (unsigned char*)k->object;
            const unsigned char* sq = *(unsigned char**)(o + 0x68);
            float* v = (float*)(o + 0x1C);
            if (sq == 0) { k->object = 0; continue; }
            // The game took the throw back at once (a reaction, its own move): throw it again, twice at most.
            if (!(sq[0] & (SQ_B26 | SQ_B28)) && k->ticks <= 4 && k->reflings < 2) {
                k->reflings++;
                fling(k, k->strength);
                continue;
            }
            // The game's wall touch, or a wall just ahead of where it is going (the flag lasts one move only).
            int wall = (sq[SQ_TOUCH] & TOUCH_WALL) && k->ticks > 1;
            if (!wall && k->speed > 0.01f) {
                const float* p = jfg_obj_pos(k->object);
                const float a[3] = { p[0], p[1] + 15.0f, p[2] };
                const float reach = 2.0f * k->speed + SLAM_REACH + 10.0f; // a squad move can come every other tick
                const float b[3] = { a[0] + v[0] / k->speed * reach, a[1], a[2] + v[2] / k->speed * reach };
                float hit[6];
                wall = jfg_level_ray(a, b, hit) && hit[4] < 0.7f && hit[4] > -0.7f; // a wall, not a slope or floor
            }
            if (wall) {
                if (k->peak >= FLING_SLAM && !k->tribal) {
                    const float* p = jfg_obj_pos(k->object);
                    const float at[3] = { p[0], p[1] + 15.0f, p[2] };
                    slam(k, hero, at, k->peak, FLING_SLAM);
                }
                v[0] = 0.0f;
                v[2] = 0.0f;
                finish(k);
                continue;
            }
            k->speed = jfg_sqrt(v[0] * v[0] + v[2] * v[2]);
            k->peak = k->peak * 0.9f > k->speed ? k->peak * 0.9f : k->speed; // a bounce off the wall halves it
            if (k->flyer) {
                unsigned short* yaw = (unsigned short*)k->object;
                *yaw = (unsigned short)(*yaw + FLYER_SPIN * frames);
            }
            // Done once the game gives it back to its AI.
            if ((!(sq[0] & (SQ_B26 | SQ_B28)) && k->ticks > 4) || k->ticks >= KNOCK_TICKS) finish(k);
            continue;
        }
        float* p = jfg_obj_pos(k->object);
        const float speed = jfg_sqrt(k->vx * k->vx + k->vz * k->vz);
        // A wall ahead: slam.
        if (speed > 0.01f) {
            const float a[3] = { p[0], p[1] + 15.0f, p[2] };
            const float reach = speed * frames + SLAM_REACH;
            const float b[3] = { a[0] + k->vx / speed * reach, a[1], a[2] + k->vz / speed * reach };
            float hit[6];
            if (jfg_level_ray(a, b, hit)) {
                if (speed >= SLAM_SPEED && !k->tribal) {
                    const float at[3] = { hit[0], hit[1], hit[2] };
                    slam(k, hero, at, speed, SLAM_SPEED);
                }
                // Bounce off a little; the rest is spent on the wall.
                const float nx = hit[3], nz = hit[5];
                const float dot = k->vx * nx + k->vz * nz;
                k->vx = (k->vx - 2.0f * dot * nx) * 0.25f;
                k->vz = (k->vz - 2.0f * dot * nz) * 0.25f;
                continue;
            }
        }
        p[0] += k->vx * frames;
        p[2] += k->vz * frames;
        if (k->flyer) {
            p[1] += k->vy * frames;
            unsigned short* yaw = (unsigned short*)k->object;
            *yaw = (unsigned short)(*yaw + FLYER_SPIN * frames);
        }
        for (int f = 0; f < frames; f++) { k->vx *= SLIDE_KEEP; k->vy *= SLIDE_KEEP; k->vz *= SLIDE_KEEP; }
        if ((speed < STOP_SPEED && k->ticks > 4) || k->ticks >= KNOCK_TICKS) finish(k);
    }
}

// --- charging --------------------------------------------------------------------------------------------------------
static void stop_charge(void) {
    if (charge_voice != 0) jfg_sound_stop(charge_voice);
    charge_voice = 0;
    was_full = 0;
    if (orb != 0) jfg_object_free(orb);
    orb = 0;
}

static void tick_charge(void* hero) {
    const unsigned char* c = control(hero);
    if (c == 0 || jfg_hero_weapon() != weapon_id || !(c[CHARGE_FLAGS] & CHARGING)) { stop_charge(); return; }
    const int charge = *(const short*)(c + CHARGE);
    const float t = charge <= 32 ? 0.0f : (float)(charge - 32) / (float)(LEVELS * 32 - 32);
    const float full = t >= 1.0f ? 1.0f : t;
    if (charge_voice == 0) charge_voice = jfg_sound_loop("charge", 0.5f, 0.0f, 0.8f);
    else jfg_sound_set(charge_voice, 0.5f + 0.3f * full, 0.0f, 0.8f + 0.7f * full);
    if (full >= 1.0f && !was_full) jfg_sound_play("full", 0.8f, 0.0f, 1.0f);
    was_full = full >= 1.0f;
    last_level = charge >> 5;
    // The orb at the hand grows with the charge.
    float d[3], m[3];
    const unsigned int yaw = aim(hero, d);
    muzzle(hero, d, m);
    if (orb_type == -2) orb_type = jfg_asset_number(ORB_TYPE);
    if (orb == 0 && orb_type >= 0) {
        JfgSpawn s = { orb_type, m[0], m[1], m[2], 0.0f, 0.0f, 0.0f, (int)yaw };
        orb = jfg_spawn(&s);
    }
    if (orb != 0) {
        float* p = jfg_obj_pos(orb);
        p[0] = m[0];
        p[1] = m[1];
        p[2] = m[2];
        unsigned short* spin = (unsigned short*)orb;
        *spin = (unsigned short)(*spin + 2500);
        jfg_object_set_scale(orb, (0.3f + 0.7f * full) * (aiming(hero) ? 0.6f : 1.0f));
    }
}

// --- the hooks -------------------------------------------------------------------------------------------------------
RECOMP_CALLBACK("*", jfg_on_weapon_fire) void cannon_fire(JfgWeaponFire* f) {
    if (weapon_id < 0 || f->weapon != weapon_id || !cfg.enabled) return;
    int level = f->charge >> 5;
    if (level < 1) level = 1;
    if (level > LEVELS) level = LEVELS;
    f->cancel = 1; // no laser bolt; one charge is used (none with Infinite Ammo)
    f->take_ammo = !cfg.infinite;
    stop_charge();
    last_level = level;
    blast(f->hero, level);
}

RECOMP_CALLBACK("*", jfg_on_level_change) void cannon_level(int level, int character) {
    for (int i = 0; i < MAX_KNOCKED; i++) knocked[i].object = 0;
    orb = 0;
    dbg_object = 0;
    if (charge_voice != 0) jfg_sound_stop(charge_voice);
    charge_voice = 0;
}

RECOMP_CALLBACK("*", jfg_on_game_tick) void cannon_tick(int frames) {
    read_config();
    if (weapon_id < 0) {
        JfgWeaponDef d = { "jfg_concussion_cannon:cannon", "Concussion Cannon", "Concussion Charges", HOST, -1, 0, HOST,
                           20, 10, 5 };
        weapon_id = jfg_weapon_register(&d);
        const int icon = jfg_asset_number(ICON_SPRITE);
        if (weapon_id >= 0 && icon >= 0) jfg_weapon_set_icon(weapon_id, icon);
        if (weapon_id >= 0) jfg_weapon_set_icon_image(weapon_id, ICON_BIG_W, ICON_BIG_H, icon_big); // mods' HUDs
        const int held = jfg_asset_number(HELD_MODEL);
        if (weapon_id >= 0 && held >= 0) jfg_weapon_set_held_model(weapon_id, held);
    }
    void* hero = jfg_hero_get();
    if (hero == 0 || jfg_game_paused()) {
        if (charge_voice != 0) { jfg_sound_stop(charge_voice); charge_voice = 0; }
        return;
    }
    if (cfg.enabled && cfg.give && weapon_id >= 0 && !jfg_hero_has_weapon(weapon_id)) jfg_hero_give_weapon(weapon_id, -1);
    if (!cfg.enabled) { stop_charge(); return; }
    if (cfg.infinite && weapon_id >= 0 && jfg_hero_has_weapon(weapon_id)) { // always full
        JfgWeaponInfo info;
        const int most = jfg_weapon_info(weapon_id, &info) && info.max_ammo > 0 ? info.max_ammo : 20;
        if (jfg_hero_ammo(weapon_id) != most) jfg_hero_set_ammo(weapon_id, most);
    }
    tick_charge(hero);
    tick_knocked(hero, frames);
}

// --- debug line ------------------------------------------------------------------------------------------------------

RECOMP_CALLBACK("*", jfg_on_draw_hud) void cannon_debug(JfgHudGfx* hud) {
    if (!cfg.debug) return;
    static JfgLine l; // static: the overlay may read the text after the call
    l.n = 0;
    l.text[0] = 0;
    void* hero = jfg_hero_get();
    const unsigned char* c = hero != 0 ? control(hero) : 0;
    int active = 0;
    for (int i = 0; i < MAX_KNOCKED; i++) active += knocked[i].object != 0;
    jfg_line_str(&l, "id "); jfg_line_num(&l, weapon_id);
    jfg_line_str(&l, " hand "); jfg_line_num(&l, jfg_hero_weapon());
    jfg_line_str(&l, " charge "); jfg_line_num(&l, c != 0 ? *(const short*)(c + CHARGE) : -1);
    jfg_line_str(&l, c != 0 && (c[CHARGE_FLAGS] & CHARGING) ? " on" : " off");
    jfg_line_str(&l, " lvl "); jfg_line_num(&l, last_level);
    jfg_line_str(&l, " hit "); jfg_line_num(&l, last_hit);
    jfg_line_str(&l, " knocked "); jfg_line_num(&l, active);
    jfg_line_str(&l, " slams "); jfg_line_num(&l, last_slams);
    if (dbg_object != 0) { // the first flung member now: its flags byte, speed (tenths a call) and what it touched
        const unsigned char* o = (const unsigned char*)dbg_object;
        const unsigned char* sq = *(unsigned char* const*)(o + 0x68);
        const float* v = (const float*)(o + 0x1C);
        jfg_line_str(&l, " | v0 "); jfg_line_num(&l, (int)(dbg_v * 10.0f));
        jfg_line_str(&l, " v "); jfg_line_num(&l, (int)(jfg_sqrt(v[0] * v[0] + v[2] * v[2]) * 10.0f));
        if (sq != 0) {
            jfg_line_str(&l, " f "); jfg_line_num(&l, sq[0]); jfg_line_str(&l, "/"); jfg_line_num(&l, sq[1]);
            jfg_line_str(&l, " n "); jfg_line_num(&l, sq[SQ_CALLS]); jfg_line_str(&l, " t "); jfg_line_num(&l, sq[SQ_TOUCH]);
        }
    }
    jfg_line_str(&l, "/"); jfg_line_num(&l, orb_type);
    jfg_line_draw(&l);
}
