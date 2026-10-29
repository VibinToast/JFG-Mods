// Rolling Shellback: a new squad enemy, run by this mod (mod API 6: jfg_squad_type_register, decomp MSR 12).
// The pack appends an object type the squad code treats like a mid-size ground soldier (jfg_assets.json "objtypes"
// "like"), with the pack's own model and animations (its list lines up with that soldier's animation set for the
// game's own actions: idle, flinches, deaths, walk, run; ours follow it). Squadrons placed with its object id spawn
// Shellbacks; the game walks them on their patrol, and this mod takes each one over when it sees the hero:
// - Curl: it hisses and curls into a ball (mission 7 under our group holds it; animation state 7, which the game never
//   advances, lets us play our own animations).
// - Roll: steering off (b26 each tick, track physics b18), our velocity toward the hero, turning slowly; walls (the
//   level ray ahead) bounce it off with a crack and a puff of dust. Armoured: shots from the front and sides stop on
//   its shell (jfg_squad_set_armour mode 1) with a spark and a ping; from behind, and blasts, they hurt.
// - Dizzy: after so many bounces it stops, half open, stars over its head, and can be hurt anywhere.
// - Uncurl and fire: it turns to the hero and fires a fan of three spines (the pack's spine objects, moved by the mod,
//   hitting the hero with jfg_hero_shot).
// - Then it stands a moment and attacks again, a roll or a fan of spines at random, while it sees the hero; out of
//   sight it walks again (handed back to the game). Each meeting with the hero starts with a roll. A roll ends after
//   so many bounces (dizzy) or after its time (it uncurls at once). Rolling into the hero rams: damage on top of the
//   game's own touch, a hard knock back the way it rolled (jfg_hero_push), and it glances off as off a wall.
// - Members keep apart: a rolling one glances off another, the rest are eased apart.
// Every distance follows the member's own size (its scale: the squadron's percent times the pack's definition scale).
// Sounds are the mod's own (make_sounds.py): the port silences the like soldier's voices for this type, and the mod
// plays its hurt and death sounds.
// Its baddy row is the port's copy of the soldier's with no body parts (they would cut our model up on a killing hit)
// and our head, neck and no aim joint (jfg_squad_type_register). Death is the game's: a killing hit plays our model's
// death (list 9/11/13/15, then the held 10/12/14/16) and fades it, from any state, ours included (decomp MSR 12i).

#include "jfg_api.h"
#include "jfg_util.h"

RECOMP_IMPORT("*", unsigned int recomp_get_config_u32(const char* key));
RECOMP_IMPORT("*", double recomp_get_config_double(const char* key));

#define DEF_NAME "jfg_shellback:objdef_shellback"   // the pack's definition (jfg_assets.json)
#define SPINE_TYPE "jfg_shellback:objtype_spine"
#define SPARK_TYPE "jfg_shellback:objtype_spark"
#define DUST_TYPE "jfg_shellback:objtype_dust"
#define DIZZY_TYPE "jfg_shellback:objtype_dizzy"
#define GROUP 0x20               // our mission group: only we clear it
#define HOLD_MISSION 7           // nothing replaces it but burning, hit-stop and electrocution
#define ANIM_STATE 7             // nothing in the game advances it
// The model's animation list: 0..20 line up with the like soldier's set (the game's own actions), ours follow.
#define ANIM_IDLE 0
#define ANIM_WALK 19
#define ANIM_TURN 21
#define ANIM_CURL 22
#define ANIM_BALL 23
#define ANIM_DIZZY 24
#define ANIM_UNCURL 25
#define ANIM_FIRE 18
// The set entry our moves run with (data +0x19): the soldier's first idle (no firing, stands), never our anim number.
#define ENTRY_IDLE 0
// The model's joints (art/build_models.py's order): the head, and the neck that leans into turns.
#define JOINT_NECK 12
#define JOINT_HEAD 13
// Their lengths in frames at 30 fps (art/build_models.py), for the phase.
#define LEN_CURL 16
#define LEN_BALL 16
#define LEN_DIZZY 31
#define LEN_UNCURL 16
#define LEN_FIRE 19
#define LEN_IDLE 61
#define FIRE_AT 0.4f             // the spines leave at this phase of the fire animation
// The member's control data (object +0x68) and object fields (decomp MSR 10c, 12c).
#define SQ_FLAGS0 0x00           // byte 0: b26 airborne (steering off) 0x04
#define SQ_FLAGS1 0x01           // byte 1: b18 track physics 0x04
#define SQ_B26 0x04
#define SQ_B18 0x04
#define SQ_ACTION 0x0A           // the current action: 0 makes the game pick its own move again
#define SQ_YAW_DIFF 0x10         // s16: the body lean toward the target (written by the game each call)
#define SQ_ENTRY 0x19            // the set entry whose flags run with the move
#define SQ_PHASE_BEFORE 0x60     // f32: the phase before the last step (the game's fire-point window)
#define SQ_ANIM_STATE 0x4B
#define SQ_HEALTH 0xA6
#define OBJ_VX 0x1C
#define OBJ_VY 0x20
#define OBJ_VZ 0x24
#define OBJ_SCALE 0x08
#define OBJ_PHASE 0x28
#define OBJ_PHASE_BEFORE 0xAC    // the phase before the last step and the step: the keyframe events read them
#define OBJ_STEP 0xB0
#define MAX_MEMBERS 16
#define MAX_SPINES 24
// Sizes of the model as built: times the member's scale (object +0x08).
#define BODY_HEIGHT 38.0f        // the ball's centre above the floor (and its radius)
#define SPINE_HEIGHT 34.0f       // where the spines leave, above the floor
#define SPINE_AHEAD 40.0f
#define KEEP_APART 44.0f         // members' centres stay this far apart
#define SPINE_LIFE 90
#define RAM_TICKS 40             // after a ram, it may ram again after this many ticks
#define RAM_REACH 26.0f          // the hero's girth, added to the ball's radius for a ram
#define BOUNCE_PITCH 0.9f        // the bounce, a little lower than as made (make_sounds.py: already a low thump)
#define PING_TICKS 8             // the deflect ping at most this often
#define HURT_TICKS 30             // the hurt sound at most this often: a blast's damage comes off over several ticks
#define ROLL_VOLUME 0.3f         // the rolling loop (the one-shots are louder)
#define SPINE_RADIUS 6.0f

enum { WALK, CURL, ROLL, DIZZY, UNCURL, FIRE, WAIT };

static struct {
    int enabled;
    float see, roll_speed, turn;
    int bounces, dizzy_ticks, rest_ticks, roll_ticks, pause_ticks;
    float spine_speed;
    int spine_damage, spread, armour, debug;
    int ram_damage;
    float sfx;                   // its sounds' volume (but the roll loop's), 0..1
    int health;                  // each member's health, in units (256 a unit in the game)
    float ram_push;
} cfg;

static void read_config(void) {
    cfg.enabled = recomp_get_config_u32("enabled") != 0;
    cfg.see = (float)recomp_get_config_double("sight");
    cfg.roll_speed = (float)recomp_get_config_double("roll_speed") / 10.0f;   // tenths of a unit a call
    cfg.turn = (float)recomp_get_config_double("turn") / 1000.0f;             // of the way to the hero a call
    cfg.bounces = (int)recomp_get_config_double("bounces");
    cfg.dizzy_ticks = (int)(recomp_get_config_double("dizzy") * 6.0);         // tenths of a second
    cfg.rest_ticks = (int)(recomp_get_config_double("rest") * 6.0);
    cfg.roll_ticks = (int)(recomp_get_config_double("roll_time") * 6.0);
    cfg.pause_ticks = (int)(recomp_get_config_double("pause") * 6.0);
    cfg.spine_speed = (float)recomp_get_config_double("spine_speed") / 10.0f;
    cfg.spine_damage = (int)(recomp_get_config_double("spine_damage") * 256.0 / 100.0);
    cfg.spread = (int)(recomp_get_config_double("spread") * 65536.0 / 360.0);  // degrees between spines
    cfg.armour = recomp_get_config_u32("armour") != 0;
    cfg.health = (int)recomp_get_config_double("health");
    cfg.sfx = (float)recomp_get_config_double("sfx_volume") / 100.0f;
    cfg.ram_damage = (int)(recomp_get_config_double("ram_damage") * 256.0 / 10.0);  // tenths of a health unit
    cfg.ram_push = (float)recomp_get_config_double("ram_push") / 10.0f;             // tenths of a unit a tick
    cfg.debug = recomp_get_config_u32("debug") != 0;
}

typedef struct {
    void* obj;
    int state, ticks, bounces, keep_heading;
    float phase, heading_x, heading_z;
    int fired, roll_voice, dizzy_voice;
    void* stars;
    int health;                  // at its last squad tick: a drop is a hurt sound
    int seen;                    // game_ticks at its last squad tick
    int health_set;              // its health set from the option (its first squad tick)
    int ram_wait;                // ticks before it may ram the hero again
    int ping_wait;               // ticks before the deflect ping may play again
    int hurt_wait;               // ticks before the hurt sound may play again
    int flung;                   // it was launched (another mod's push): rolling on its way when it lands
} Member;
static Member members[MAX_MEMBERS];

typedef struct { void* obj; float x, y, z, vx, vy, vz, r; int age; } Spine;
static Spine spines[MAX_SPINES];


static int type_id = -1, spine_type = -2, dizzy_type = -2;
static int last_state, last_bounces, last_deflects, last_hits, last_rams;
static int game_ticks;                // 1/60 s ticks counted by the game tick
#define GONE_TICKS 60            // a member no squad tick has seen this long is gone

// The game's angle of a direction (as Arctanf(x, z)): 0 along +z, 0x4000 along +x.
static unsigned int angle_of(float x, float z) {
    const float ax = x < 0 ? -x : x, az = z < 0 ? -z : z;
    if (ax < 1e-6f && az < 1e-6f) return 0;
    // atan in turns of 1/8 by the octant, then a rational approximation inside it.
    float t = ax < az ? ax / az : az / ax;
    float a = t * (0.7853981f + 0.273f * (1.0f - t));       // radians, 0..pi/4
    if (ax > az) a = 1.5707963f - a;
    if (z < 0) a = 3.1415926f - a;
    if (x < 0) a = -a;
    return (unsigned int)(int)(a * (32768.0f / 3.1415926f)) & 0xFFFF;
}

static unsigned char* sq_of(void* obj) { return *(unsigned char**)((unsigned char*)obj + 0x68); }
static float* fld(void* obj, int off) { return (float*)((unsigned char*)obj + off); }
static float scale_of(void* obj) {
    const float s = *fld(obj, OBJ_SCALE);
    return s > 0.05f && s < 20.0f ? s : 1.0f;
}

static unsigned int seed = 0x5EB1u;
static int coin(void) { // 0 or 1
    seed = seed * 1103515245u + 12345u;
    return (int)(seed >> 16 & 1);
}

static int spawn_type(int* type, const char* name) {
    if (*type == -2) *type = jfg_asset_number(name);
    return *type;
}

// A dust puff or spark the port runs to its end (jfg_fx_spawn): grown evenly while it fades out.
static void* effect(const char* name, const float* at, int ticks, float from, float to) {
    JfgFx f = { name, at[0], at[1], at[2], 0, 0.0f, 0.0f, 0.0f, 1.0f, ticks, from, to, 0, 255, 0.0f };
    return jfg_fx_spawn(&f);
}

// Sound volume by distance from the hero (and left/right by where it is from the camera's view, roughly).
static float near_volume(void* obj, float loud) {
    void* hero = jfg_hero_get();
    if (hero == 0) return 0.0f;
    const float* a = jfg_obj_pos(obj);
    const float* b = jfg_obj_pos(hero);
    const float dx = a[0] - b[0], dz = a[2] - b[2];
    const float d = jfg_sqrt(dx * dx + dz * dz);
    const float v = loud * (1.0f - d / 1500.0f);
    return v < 0.0f ? 0.0f : v;
}

// Every sound but the roll loop (ROLL_VOLUME): the Sound Volume option on top.
static float sfx_volume(void* obj, float loud) { return near_volume(obj, loud * cfg.sfx); }

static Member* member_of(void* obj) {
    Member* free_one = 0;
    for (int i = 0; i < MAX_MEMBERS; i++) {
        if (members[i].obj == obj) return &members[i];
        if (members[i].obj == 0 && free_one == 0) free_one = &members[i];
    }
    if (free_one != 0) {
        Member zero = { 0 };
        *free_one = zero;
        free_one->obj = obj;
        free_one->state = WALK;
        free_one->ticks = 0;
    }
    return free_one;
}

static void stop_sounds(Member* m) {
    if (m->roll_voice != 0) jfg_sound_stop(m->roll_voice);
    if (m->dizzy_voice != 0) jfg_sound_stop(m->dizzy_voice);
    m->roll_voice = m->dizzy_voice = 0;
    if (m->stars != 0) { jfg_object_free(m->stars); m->stars = 0; }
}

static void play(Member* m, int anim) {
    unsigned char* sq = sq_of(m->obj);
    if (sq != 0) {
        sq[SQ_ANIM_STATE] = ANIM_STATE;
        sq[SQ_ENTRY] = ENTRY_IDLE;   // else the old entry's flags run on (the soldier's fire entry would shoot bolts)
        *(float*)(sq + SQ_PHASE_BEFORE) = 0.0f;
    }
    jfg_object_anim_set(m->obj, anim, 0);
    m->phase = 0.0f;
}

// Advances our animation of len frames (30 fps); 1 when a one-shot ends. A loop stays below 1.0 (1.0 reads one frame
// past its end), a one-shot holds at 1.0.
static int advance(Member* m, int len, int frames, int loop) {
    const float step = (float)frames / (float)(len * 2);
    unsigned char* sq = sq_of(m->obj);
    if (sq != 0) *(float*)(sq + SQ_PHASE_BEFORE) = m->phase;
    *fld(m->obj, OBJ_PHASE_BEFORE) = m->phase;
    *fld(m->obj, OBJ_STEP) = step;
    m->phase += step;
    int ended = 0;
    if (m->phase >= 1.0f) {
        if (loop) { while (m->phase >= 1.0f) m->phase -= 1.0f; }
        else { m->phase = 1.0f; ended = 1; }
    }
    *fld(m->obj, OBJ_PHASE) = m->phase;
    return ended;
}

static void face(void* obj, float tx, float tz) {
    const float* p = jfg_obj_pos(obj);
    *(unsigned short*)obj = (unsigned short)angle_of(p[0] - tx, p[2] - tz); // the game's facers: self minus target
}

static void hold_still(void* obj, unsigned char* sq) {
    if (jfg_enemy_flung(obj)) return; // flung (a push): the throw moves it
    *fld(obj, OBJ_VX) = 0.0f;
    *fld(obj, OBJ_VZ) = 0.0f;
    sq[SQ_FLAGS0] |= SQ_B26;
    sq[SQ_FLAGS1] |= SQ_B18;
    *(short*)(sq + SQ_YAW_DIFF) = 0;
}

static void fire_spines(Member* m) {
    if (spawn_type(&spine_type, SPINE_TYPE) < 0) return;
    void* hero = jfg_hero_get();
    if (hero == 0) return;
    const float* p = jfg_obj_pos(m->obj);
    const float* h = jfg_obj_pos(hero);
    const unsigned int yaw = *(unsigned short*)m->obj;
    const float sc = scale_of(m->obj);
    // Forward is (-sin yaw, -cos yaw); aim at the hero's middle for the pitch.
    const float fx_ = -jfg_turn_sin(yaw), fz = -jfg_turn_sin(yaw + 0x4000);
    const float sx = p[0] + fx_ * SPINE_AHEAD * sc, sy = p[1] + SPINE_HEIGHT * sc, sz = p[2] + fz * SPINE_AHEAD * sc;
    const float dx = h[0] - sx, dz = h[2] - sz, dist = jfg_sqrt(dx * dx + dz * dz);
    const float vy = dist > 1.0f ? (h[1] + 40.0f - sy) / dist : 0.0f;
    for (int k = -1; k <= 1; k++) {
        Spine* s = 0;
        for (int i = 0; i < MAX_SPINES && s == 0; i++) if (spines[i].obj == 0) s = &spines[i];
        if (s == 0) return;
        const unsigned int a = yaw + (unsigned int)(k * cfg.spread);
        JfgSpawn sp = { spine_type, sx, sy, sz, 0.0f, 0.0f, 0.0f, (int)(a & 0xFFFF) };
        void* o = jfg_spawn(&sp);
        if (o == 0) return;
        jfg_object_set_scale(o, sc);
        s->obj = o;
        s->r = SPINE_RADIUS * sc;
        s->x = sx; s->y = sy; s->z = sz;
        s->vx = -jfg_turn_sin(a) * cfg.spine_speed;
        s->vz = -jfg_turn_sin(a + 0x4000) * cfg.spine_speed;
        s->vy = vy * cfg.spine_speed;
        s->age = 0;
    }
    jfg_sound_play("spines", sfx_volume(m->obj, 0.9f), 0.0f, 1.0f);
}

static void tick_spines(int frames) {
    for (int i = 0; i < MAX_SPINES; i++) {
        Spine* s = &spines[i];
        if (s->obj == 0) continue;
        s->age += frames;
        const float a[3] = { s->x, s->y, s->z };
        const float b[3] = { s->x + s->vx * frames, s->y + s->vy * frames, s->z + s->vz * frames };
        float hit[6];
        int done = s->age >= SPINE_LIFE || jfg_level_ray(a, b, hit);
        JfgHeroShot shot = { { a[0], a[1], a[2] }, { b[0], b[1], b[2] }, s->r, cfg.spine_damage, 0, s->obj };
        if (!done && jfg_hero_shot(&shot)) { done = 1; last_hits++; }
        if (done) { jfg_object_free(s->obj); s->obj = 0; continue; }
        s->x = b[0]; s->y = b[1]; s->z = b[2];
        float* p = jfg_obj_pos(s->obj);
        p[0] = b[0]; p[1] = b[1]; p[2] = b[2];
    }
}

// Keeps m off the other members: rolling, it glances off one (its heading turned away, as off a wall); otherwise it
// is moved out by half the overlap (the other does the same in its own tick).
static void keep_apart(Member* m, float* p, float sc, int rolling) {
    const float want = KEEP_APART * sc * 2.0f;
    for (int i = 0; i < MAX_MEMBERS; i++) {
        Member* o = &members[i];
        if (o == m || o->obj == 0) continue;
        const float* q = jfg_obj_pos(o->obj);
        float dx = p[0] - q[0], dz = p[2] - q[2];
        float d = jfg_sqrt(dx * dx + dz * dz);
        if (d >= want) continue;
        if (d < 0.5f) { // on top of each other: split by slot
            dx = (m < o) ? 1.0f : -1.0f;
            dz = 0.0f;
            d = 1.0f;
        }
        const float nx = dx / d, nz = dz / d;
        if (rolling) {
            const float into = m->heading_x * nx + m->heading_z * nz;
            if (into < 0.0f) {
                m->heading_x -= 2.0f * into * nx;
                m->heading_z -= 2.0f * into * nz;
                m->keep_heading = 20;
            }
        }
        const float push = (want - d) * 0.5f;
        p[0] += nx * push;
        p[2] += nz * push;
    }
}

// --- the per-member tick -------------------------------------------------------------------------------------------
static void go(Member* m, int state) {
    m->state = state;
    m->ticks = 0;
}

// Hands it back to the game. Its animation state is ours to reset only while it is still ours (7): a hit reaction,
// burning or death that took it over keeps going (resetting a death freezes it and the body never fades).
static void release(Member* m) {
    unsigned char* sq = sq_of(m->obj);
    jfg_squad_set_armour(m->obj, 0);
    jfg_squad_clear_mission(m->obj, GROUP, 30);
    if (sq != 0 && sq[SQ_ANIM_STATE] == ANIM_STATE && *(const short*)(sq + SQ_HEALTH) > 0) {
        sq[SQ_ANIM_STATE] = 0;
        sq[SQ_ACTION] = 0;
    }
    stop_sounds(m);
    go(m, WALK);
}

static void start_roll(Member* m) {
    play(m, ANIM_CURL);
    jfg_sound_play("curl", sfx_volume(m->obj, 0.7f), 0.0f, 1.0f);
    go(m, CURL);
}

static void start_fire(Member* m) {
    play(m, ANIM_FIRE);
    m->fired = 0;
    go(m, FIRE);
}

static void end_roll(Member* m) {
    *fld(m->obj, OBJ_VX) = 0.0f;
    *fld(m->obj, OBJ_VZ) = 0.0f;
    jfg_squad_set_armour(m->obj, 0);
    if (m->roll_voice != 0) { jfg_sound_stop(m->roll_voice); m->roll_voice = 0; }
}

RECOMP_CALLBACK("*", jfg_on_squad_tick) void shellback_tick(JfgSquadTick* t) {
    if (t->type != type_id || !cfg.enabled) { t->run_stock = !cfg.enabled; return; }
    void* obj = t->member;
    unsigned char* sq = (unsigned char*)t->data;
    Member* m = member_of(obj);
    void* hero = jfg_hero_get();
    if (m == 0 || sq == 0 || hero == 0) return;
    const int frames = t->frames;
    m->ticks += frames;
    m->seen = game_ticks; // alive: only here may its object be read (the game frees members on its own)
    if (!m->health_set) { // the Health option, in place of its squad's: the hit block's (damage comes off it) and its own
        m->health_set = 1;
        const int full = (cfg.health > 0 ? cfg.health : 12) * 256;
        jfg_object_set_health(obj, full);
        *(short*)(sq + SQ_HEALTH) = (short)full;
        m->health = full;
    }
    {
        const int health = *(const short*)(sq + SQ_HEALTH);
        if (m->hurt_wait > 0) m->hurt_wait -= frames;
        if (health > 0 && m->health > 0 && health < m->health && m->hurt_wait <= 0) {
            jfg_sound_play("hurt", sfx_volume(obj, 0.8f), 0.0f, 1.0f);
            m->hurt_wait = HURT_TICKS;
        }
        m->health = health;
    }
    float* p = jfg_obj_pos(obj);
    const float* h = jfg_obj_pos(hero);
    const float sc = scale_of(obj);
    const float body = BODY_HEIGHT * sc;
    const float dx = h[0] - p[0], dz = h[2] - p[2], dist = jfg_sqrt(dx * dx + dz * dz);
    // The game took it over (a hit reaction, burning, death): let go without touching its animation.
    if (jfg_enemy_flung(obj) && m->state != ROLL) return; // flung: the throw moves it (it rolls on once landed)
    if (m->state != WALK && (sq[SQ_ANIM_STATE] != ANIM_STATE || *(const short*)(sq + SQ_HEALTH) <= 0)) {
        release(m);
        return;
    }

    switch (m->state) {
    case WALK: {
        // The game walks it; it may curl again once rested, when the hero is near and in sight.
        keep_apart(m, p, sc, 0);
        if (m->ticks < cfg.rest_ticks || dist > cfg.see) break;
        const float a[3] = { p[0], p[1] + body, p[2] }, b[3] = { h[0], h[1] + 40.0f, h[2] };
        if (!jfg_line_of_sight(obj, hero, a, b)) break;
        if (!jfg_squad_set_mission(obj, GROUP, HOLD_MISSION, 0, 0, 0)) break;
        jfg_sound_play("alert", sfx_volume(obj, 0.8f), 0.0f, 1.0f);
        start_roll(m); // a meeting always starts with a roll
        break;
    }
    case CURL:
        hold_still(obj, sq);
        keep_apart(m, p, sc, 0);
        face(obj, h[0], h[2]);
        if (advance(m, LEN_CURL, frames, 0)) {
            play(m, ANIM_BALL);
            m->bounces = 0;
            m->keep_heading = 0;
            m->heading_x = dist > 1.0f ? dx / dist : 0.0f;
            m->heading_z = dist > 1.0f ? dz / dist : 1.0f;
            if (cfg.armour) jfg_squad_set_armour(obj, 1);
            m->roll_voice = jfg_sound_loop("roll", near_volume(obj, ROLL_VOLUME), 0.0f, 1.0f);
            go(m, ROLL);
        }
        break;
    case ROLL: {
        sq[SQ_FLAGS0] |= SQ_B26;
        sq[SQ_FLAGS1] |= SQ_B18;
        *(short*)(sq + SQ_YAW_DIFF) = 0;
        // Steer slowly toward the hero (not while keeping a bounce's heading).
        if (m->keep_heading > 0) m->keep_heading -= frames;
        else if (dist > 1.0f) {
            m->heading_x += (dx / dist - m->heading_x) * cfg.turn * frames;
            m->heading_z += (dz / dist - m->heading_z) * cfg.turn * frames;
            const float l = jfg_sqrt(m->heading_x * m->heading_x + m->heading_z * m->heading_z);
            if (l > 0.01f) { m->heading_x /= l; m->heading_z /= l; }
        }
        // A wall just ahead: bounce off it.
        // Its time is up: it uncurls where it is (no dizzy) and attacks again.
        if (m->ticks >= cfg.roll_ticks) {
            end_roll(m);
            play(m, ANIM_UNCURL);
            go(m, UNCURL);
            break;
        }
        // Flung (a push): the throw moves it; it rolls on the way it was thrown when it lands.
        if (jfg_enemy_flung(obj)) {
            m->flung = 1;
            advance(m, LEN_BALL, frames, 1);
            break;
        }
        if (m->flung) {
            m->flung = 0;
            const float vx = *fld(obj, OBJ_VX), vz = *fld(obj, OBJ_VZ), v = jfg_sqrt(vx * vx + vz * vz);
            if (v > 0.5f) { m->heading_x = vx / v; m->heading_z = vz / v; m->keep_heading = 20; }
        }
        keep_apart(m, p, sc, 1);
        const float a[3] = { p[0], p[1] + body, p[2] };
        const float reach = cfg.roll_speed * 2.0f + body + 4.0f;
        const float b[3] = { a[0] + m->heading_x * reach, a[1], a[2] + m->heading_z * reach };
        float hit[6];
        if (jfg_level_ray(a, b, hit) && hit[4] < 0.7f && hit[4] > -0.7f) {
            const float d = m->heading_x * hit[3] + m->heading_z * hit[5];
            m->heading_x -= 2.0f * d * hit[3];
            m->heading_z -= 2.0f * d * hit[5];
            const float l = jfg_sqrt(m->heading_x * m->heading_x + m->heading_z * m->heading_z);
            if (l > 0.01f) { m->heading_x /= l; m->heading_z /= l; }
            m->keep_heading = 20;
            // Only a wall it hits by itself makes it dizzy: not one just after a ram (the hero knocked into it), nor
            // one with the hero in the way (it hits the hero first).
            const float hx = h[0] - a[0], hz = h[2] - a[2];
            const float wx = hit[0] - a[0], wz = hit[2] - a[2];
            const float hd = jfg_sqrt(hx * hx + hz * hz), wd = jfg_sqrt(wx * wx + wz * wz);
            const int hero_first = hd < wd + body + RAM_REACH &&                           // no further than the wall
                                   hx * m->heading_x + hz * m->heading_z > 0.5f * hd;      // and ahead of it
            if (m->ram_wait <= 0 && !hero_first) m->bounces++;
            jfg_sound_play("bounce", sfx_volume(obj, 1.0f), 0.0f, BOUNCE_PITCH);
            const float at[3] = { hit[0], hit[1], hit[2] };
            effect(DUST_TYPE, at, 20, 0.5f * sc, 1.4f * sc);
            if (m->bounces >= cfg.bounces) {
                end_roll(m);
                play(m, ANIM_DIZZY);
                m->dizzy_voice = jfg_sound_loop("dizzy", sfx_volume(obj, 0.6f), 0.0f, 1.0f);
                if (spawn_type(&dizzy_type, DIZZY_TYPE) >= 0) {
                    JfgSpawn s = { dizzy_type, p[0], p[1] + body * 2.0f, p[2], 0, 0, 0, 0 };
                    m->stars = jfg_spawn(&s);
                    if (m->stars != 0) jfg_object_set_scale(m->stars, sc);
                }
                go(m, DIZZY);
                break;
            }
        }
        // Rolling into the hero: a ram.
        if (m->ram_wait > 0) m->ram_wait -= frames;
        {
            const float hx = h[0] - p[0], hy = h[1] + 40.0f - (p[1] + body), hz = h[2] - p[2];
            const float reach = body + RAM_REACH;
            if (m->ram_wait <= 0 && hx * hx + hy * hy + hz * hz < reach * reach) {
                m->ram_wait = RAM_TICKS;
                const float hd = jfg_sqrt(hx * hx + hz * hz);
                const float nx = hd > 0.5f ? hx / hd : m->heading_x, nz = hd > 0.5f ? hz / hd : m->heading_z;
                if (cfg.ram_damage > 0) {
                    JfgHeroShot ram = { { p[0], p[1] + body, p[2] }, { h[0], h[1] + 40.0f, h[2] }, body, cfg.ram_damage, 0, obj };
                    jfg_hero_shot(&ram);
                }
                if (cfg.ram_push > 0.0f) jfg_hero_push(hero, nx * cfg.ram_push, nz * cfg.ram_push, 18);
                // It glances off the hero, as off a wall.
                const float into = m->heading_x * nx + m->heading_z * nz;
                if (into > 0.0f) {
                    m->heading_x -= 2.0f * into * nx;
                    m->heading_z -= 2.0f * into * nz;
                }
                m->keep_heading = 20;
                jfg_sound_play("bounce", sfx_volume(obj, 1.0f), 0.0f, BOUNCE_PITCH * 0.85f);
                last_rams++;
            }
        }
        *fld(obj, OBJ_VX) = m->heading_x * cfg.roll_speed;
        *fld(obj, OBJ_VZ) = m->heading_z * cfg.roll_speed;
        *(unsigned short*)obj = (unsigned short)angle_of(-m->heading_x, -m->heading_z);
        advance(m, LEN_BALL, frames, 1);
        if (m->roll_voice != 0) jfg_sound_set(m->roll_voice, near_volume(obj, ROLL_VOLUME), 0.0f, 1.0f);
        // Shots its shell stopped: a ping and a spark.
        const int deflected = jfg_squad_deflects(obj);
        if (m->ping_wait > 0) m->ping_wait -= frames;
        if (deflected > 0) {
            last_deflects += deflected;
        }
        if (deflected > 0 && m->ping_wait <= 0) { // one ping (and spark) at most every PING_TICKS under rapid fire
            m->ping_wait = PING_TICKS;
            jfg_sound_play("deflect", sfx_volume(obj, 0.9f), 0.0f, 1.0f);
            const float at[3] = { p[0], p[1] + body, p[2] };
            effect(SPARK_TYPE, at, 12, 0.6f * sc, 1.2f * sc);
        }
        break;
    }
    case DIZZY:
        hold_still(obj, sq);
        keep_apart(m, p, sc, 0);
        advance(m, LEN_DIZZY, frames, 1);
        if (m->stars != 0) {
            float* s = jfg_obj_pos(m->stars);
            s[0] = p[0]; s[1] = p[1] + body * 2.0f; s[2] = p[2];
            *(unsigned short*)m->stars = (unsigned short)(*(unsigned short*)m->stars + 1500 * frames);
        }
        if (m->dizzy_voice != 0) jfg_sound_set(m->dizzy_voice, sfx_volume(obj, 0.6f), 0.0f, 1.0f);
        if (m->ticks >= cfg.dizzy_ticks) {
            stop_sounds(m);
            play(m, ANIM_UNCURL);
            go(m, UNCURL);
        }
        break;
    case UNCURL:
        hold_still(obj, sq);
        keep_apart(m, p, sc, 0);
        face(obj, h[0], h[2]);
        if (advance(m, LEN_UNCURL, frames, 0)) start_fire(m);
        break;
    case FIRE: {
        hold_still(obj, sq);
        keep_apart(m, p, sc, 0);
        face(obj, h[0], h[2]);
        const int ended = advance(m, LEN_FIRE, frames, 0);
        if (!m->fired && m->phase >= FIRE_AT) { m->fired = 1; fire_spines(m); }
        if (ended) {
            play(m, ANIM_IDLE);
            go(m, WAIT);
        }
        break;
    }
    case WAIT: {
        // A moment standing, facing the hero; then another attack while it sees the hero, else it walks again.
        hold_still(obj, sq);
        keep_apart(m, p, sc, 0);
        face(obj, h[0], h[2]);
        advance(m, LEN_IDLE, frames, 1);
        if (m->ticks < cfg.pause_ticks) break;
        const float a[3] = { p[0], p[1] + body, p[2] }, b[3] = { h[0], h[1] + 40.0f, h[2] };
        if (dist > cfg.see || !jfg_line_of_sight(obj, hero, a, b)) { release(m); break; }
        if (coin()) start_roll(m);
        else start_fire(m);
        break;
    }
    }
    last_state = m->state;
    last_bounces = m->bounces;
}

// --- the game tick: registration, spines, effects, members gone ----------------------------------------------------
RECOMP_CALLBACK("*", jfg_on_game_tick) void shellback_game_tick(int frames) {
    read_config();
    if (type_id < 0) {
        // No aim joint: the head would turn toward the hero inside the ball. The eye is just in front of the head.
        JfgSquadTypeDef d = { "jfg_shellback:shellback", DEF_NAME, 0, JOINT_HEAD, { 0, 4, -10 },
                              { JOINT_NECK, 0, 0 }, { 0x5D, 0, 0 }, 0 };
        type_id = jfg_squad_type_register(&d);
    }
    if (jfg_game_paused()) return;
    tick_spines(frames);
    game_ticks += frames;
    // Members the squad tick hasn't seen for a while are gone (dead and faded, or despawned): forgotten without
    // reading their object, which the game may have freed and reused (reading it crashed the game).
    for (int i = 0; i < MAX_MEMBERS; i++) {
        Member* m = &members[i];
        if (m->obj == 0 || game_ticks - m->seen < GONE_TICKS) continue;
        stop_sounds(m);
        jfg_squad_forget(m->obj);
        m->obj = 0;
    }
}

// A member died: its death sound (the port silences the soldier's), its loops stopped, forgotten.
RECOMP_CALLBACK("*", jfg_on_kill) void shellback_killed(JfgKill* k) {
    for (int i = 0; i < MAX_MEMBERS; i++) {
        Member* m = &members[i];
        if (m->obj == 0 || m->obj != k->victim) continue;
        jfg_sound_play("death", sfx_volume(m->obj, 0.9f), 0.0f, 1.0f);
        stop_sounds(m);
        jfg_squad_forget(m->obj);
        m->obj = 0;
    }
}

RECOMP_CALLBACK("*", jfg_on_level_change) void shellback_level(int level, int character) {
    for (int i = 0; i < MAX_MEMBERS; i++) {
        if (members[i].roll_voice != 0) jfg_sound_stop(members[i].roll_voice);
        if (members[i].dizzy_voice != 0) jfg_sound_stop(members[i].dizzy_voice);
        members[i].obj = 0;
    }
    for (int i = 0; i < MAX_SPINES; i++) spines[i].obj = 0; // gone with the level
}

// --- debug line ------------------------------------------------------------------------------------------------------

RECOMP_CALLBACK("*", jfg_on_draw_hud) void shellback_debug(JfgHudGfx* hud) {
    if (!cfg.debug) return;
    static const char* names[] = { "walk", "curl", "roll", "dizzy", "uncurl", "fire", "wait" };
    static JfgLine l; // static: the overlay may read the text after the call
    l.n = 0;
    l.text[0] = 0;
    int count = 0;
    for (int i = 0; i < MAX_MEMBERS; i++) count += members[i].obj != 0;
    jfg_line_str(&l, "type "); jfg_line_num(&l, type_id);
    jfg_line_str(&l, " members "); jfg_line_num(&l, count);
    jfg_line_str(&l, " last "); jfg_line_str(&l, names[last_state]);
    jfg_line_str(&l, " bounces "); jfg_line_num(&l, last_bounces);
    jfg_line_str(&l, " deflects "); jfg_line_num(&l, last_deflects);
    jfg_line_str(&l, " spine hits "); jfg_line_num(&l, last_hits);
    jfg_line_str(&l, " rams "); jfg_line_num(&l, last_rams);
    jfg_line_draw(&l);
}
