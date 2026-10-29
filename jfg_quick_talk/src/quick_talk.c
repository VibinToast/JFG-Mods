// Quick Talk: hint characters turn to you and talk at once, for Jet Force Gemini: Recompiled (mod API version 6).
//
// The hint characters (the moles, the limpet and the rest) are objects of behaviour 90 ("mrhints", overlay 32). When
// one is triggered it runs states 3 (turn to a point 80 units in front of the hero), 4 (walk there), 5 (turn to face
// the hero), 6 (greeting, then the hint text from the end of its move) and 8 (talking). Its turns step by an eighth of
// the angle left, at most 0x16C a tick. Each tick, before the game runs it, the mod:
//   - sends a character that starts state 3 or 4 straight to state 5 (Walk Up To You off);
//   - turns it toward its target in states 3 and 5 by up to 0x1000 a tick (Fast) or at once (Instant); the game's own
//     state 5 then finds it facing the hero and goes on to its greeting;
//   - ends the greeting move (state 6 or 7: the text starts when its move reaches the end, phase 1.0);
//   - scales its talk range (data +0x18, set from the level's entry at init) by Talk Range.
// Its data (object +0x68): +0x00 u8 state, +0x18 f32 talk radius, +0x24 f32 speed, +0x28 f32 target speed.

#include "jfg_api.h"
#include "jfg_util.h"

RECOMP_IMPORT("*", unsigned int recomp_get_config_u32(const char* key));
RECOMP_IMPORT("*", double recomp_get_config_double(const char* key));

#define KIND_HINTS 90
#define MAX_HINTS 32
#define FAST_STEP 0x1000      // per 1/30 s tick: a half turn in about a quarter of a second

#define ST_TURN_TO_SPOT 3
#define ST_WALK 4
#define ST_FACE 5
#define ST_GREET 6
#define ST_GREET_SHOT 7

#define OBJ_YAW 0x00          // s16
#define OBJ_X 0x0C
#define OBJ_Z 0x14
#define OBJ_PHASE 0x28        // f32, the animation's phase 0..1
#define OBJ_DATA 0x68
#define D_STATE 0x00
#define D_TALK_RADIUS 0x18
#define D_TARGET_SPEED 0x28

// The game's angle of a direction (as Arctanf(x, z)): 0 along +z, 0x4000 along +x.
static int angle_of(float x, float z) {
    const float ax = x < 0 ? -x : x, az = z < 0 ? -z : z;
    if (ax < 1e-6f && az < 1e-6f) return 0;
    float t = ax < az ? ax / az : az / ax;
    float a = t * (0.7853981f + 0.273f * (1.0f - t)); // radians, 0..pi/4
    if (ax > az) a = 1.5707963f - a;
    if (z < 0) a = 3.1415926f - a;
    if (x < 0) a = -a;
    return (int)(a * (32768.0f / 3.1415926f));
}

static float* f32_at(void* p, int off) { return (float*)((unsigned char*)p + off); }
static short* s16_at(void* p, int off) { return (short*)((unsigned char*)p + off); }

// The talk radius each character came with, by object: the mod only ever writes base * scale, so a radius that is
// neither is a new object in that slot (its own base).
static struct { void* obj; float base, set; } radii[MAX_HINTS];

RECOMP_CALLBACK("*", jfg_on_level_change) void qt_level(int level, int character) {
    for (int i = 0; i < MAX_HINTS; i++) radii[i].obj = 0;
}

static void scale_radius(void* obj, unsigned char* data, float scale) {
    float* r = f32_at(data, D_TALK_RADIUS);
    int slot = -1, free_slot = -1;
    for (int i = 0; i < MAX_HINTS; i++) {
        if (radii[i].obj == obj) slot = i;
        else if (radii[i].obj == 0 && free_slot < 0) free_slot = i;
    }
    if (slot >= 0 && *r != radii[slot].set && *r != radii[slot].base) slot = -1; // a new object at that address
    if (slot < 0) {
        slot = free_slot >= 0 ? free_slot : 0;
        radii[slot].obj = obj;
        radii[slot].base = *r;
    }
    radii[slot].set = radii[slot].base * scale;
    *r = radii[slot].set;
}

// Turns the object toward yaw target by at most step (0: at once).
static void turn_to(void* obj, int target, int step) {
    short* yaw = s16_at(obj, OBJ_YAW);
    int diff = (short)(target - *yaw);
    if (step > 0 && diff > step) diff = step;
    if (step > 0 && diff < -step) diff = -step;
    *yaw = (short)(*yaw + diff);
}

RECOMP_CALLBACK("*", jfg_on_game_tick) void qt_tick(int frames) {
    const int on = recomp_get_config_u32("enabled") != 0;
    const float scale = on ? (float)recomp_get_config_double("range") / 100.0f : 1.0f;
    if (jfg_game_paused()) return;
    JfgObjectInfo hints[MAX_HINTS];
    const int n = jfg_objects_of_kind(KIND_HINTS, hints, MAX_HINTS);
    void* hero = jfg_hero_get();
    const unsigned int turn = recomp_get_config_u32("turn"); // 0 game's, 1 fast, 2 instant
    const int walk = recomp_get_config_u32("walk") != 0;
    const int skip_greeting = recomp_get_config_u32("skip_greeting") != 0;
    const int step = turn == 2 ? 0 : (int)(FAST_STEP * jfg_get_tick_scale());
    for (int i = 0; i < n && i < MAX_HINTS; i++) {
        void* obj = hints[i].object;
        unsigned char* data = *(unsigned char**)((unsigned char*)obj + OBJ_DATA);
        if (data == 0) continue;
        scale_radius(obj, data, scale); // back to 100% when off
        if (!on || hero == 0) continue;
        unsigned char* state = data + D_STATE;
        if (!walk && (*state == ST_TURN_TO_SPOT || *state == ST_WALK)) {
            *state = ST_FACE;
            *f32_at(data, D_TARGET_SPEED) = 0.0f; // stand: state 5 turns on the spot
        }
        if (turn != 0 && (*state == ST_FACE || *state == ST_TURN_TO_SPOT)) {
            float tx = *f32_at(hero, OBJ_X), tz = *f32_at(hero, OBJ_Z);
            if (*state == ST_TURN_TO_SPOT) { // the point 80 units in front of the hero, as the game aims it
                const int hy = *s16_at(hero, OBJ_YAW);
                tx -= jfg_turn_sin((unsigned int)hy) * 80.0f;
                tz -= jfg_turn_cos((unsigned int)hy) * 80.0f;
            }
            turn_to(obj, angle_of(tx - *f32_at(obj, OBJ_X), tz - *f32_at(obj, OBJ_Z)), step);
        }
        if (skip_greeting && (*state == ST_GREET || *state == ST_GREET_SHOT)) {
            *f32_at(obj, OBJ_PHASE) = 1.0f; // the game starts the text when the greeting reaches its end
        }
    }
}
