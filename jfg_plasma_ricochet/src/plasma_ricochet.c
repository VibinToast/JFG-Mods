// Ricochet Plasma for Jet Force Gemini: Recompiled (mod API version 6).
//
// The plasma shotgun's balls (the game's own: kind JFG_KIND_PLASMA, its charge 1..4 read from its data) bounce off
// walls, floors and ceilings instead of dying on them, as many times as the charge allows. The port tells the mod as
// balls are made and freed (jfg_object_watch); a ball another mod drives (jfg_object_claim) is left alone. Each tick the mod looks a
// step ahead along the ball's flight (jfg_level_ray); when the level is there and the ball has bounces left, its speed
// (object + 0x1C..0x24) is mirrored off the surface before the game's own test sees the wall. Each bounce makes it
// split: the ball breaks into a chosen number of shots fanned off the bounce (it takes one way, new ones from
// jfg_fire_plasma the others), all smaller (their scale and hit radius) and weaker (their damage, hit data + 0x06, 256 a unit), each able to bounce and split again
// with the bounces left, so a full charge ends in a spray of small shots. Each bounce also lasts a little longer (its
// time, data + 0x12, 1/60 s), with a zap. With Split off a bounce makes the ball bigger and stronger instead. Optionally a bounce turns it a little toward the nearest
// enemy ahead. Once its bounces are spent, the next wall ends it as the game's shot.

#include "jfg_api.h"
#include "jfg_util.h"

RECOMP_IMPORT("*", unsigned int recomp_get_config_u32(const char* key));
RECOMP_IMPORT("*", double recomp_get_config_double(const char* key));

#define MAX_BALLS 48       // balls followed at once: the splits stop when it is full
#define NEARBY 12
#define BACK_OFF 6.0f        // a bounced ball is put this far off the surface
#define GROW 1.12f           // size gained by a bounce that does not split
#define SHRINK 0.8f          // size kept by both halves of a split
#define EXTRA_TIME 30        // 1/60 s added each bounce
#define SOUND_BOUNCE 0xE1    // the plasma shotgun's shot
#define HOMING_REACH 600.0f

static struct {
    int enabled;
    int bounces;      // at full charge
    int split;        // a bounce splits the ball in two
    int pieces;       // shots a split makes (this one among them)
    float angle;      // degrees the outermost pieces turn off the plain bounce
    int split_damage; // percent of the damage each piece keeps
    float homing;     // 0..1: how far a bounce turns toward an enemy
    int sound;
} cfg;

static void read_config(void) {
    cfg.enabled = recomp_get_config_u32("enabled") != 0;
    cfg.bounces = (int)recomp_get_config_double("bounces");
    cfg.split = recomp_get_config_u32("split") != 0;
    cfg.pieces = (int)recomp_get_config_double("pieces");
    cfg.angle = (float)recomp_get_config_double("angle");
    cfg.split_damage = (int)recomp_get_config_double("split_damage");
    cfg.homing = (float)recomp_get_config_double("homing") / 100.0f;
    cfg.sound = recomp_get_config_u32("sound") != 0;
}

typedef struct {
    void* obj;
    int left;   // bounces left
} Ball;
static Ball balls[MAX_BALLS];
static int ball_count;

static unsigned char* data_of(void* obj) { return *(unsigned char**)((unsigned char*)obj + 0x68); }
static unsigned char* hit_of(void* obj) { return *(unsigned char**)((unsigned char*)obj + 0x4C); }
static float* speed(void* obj) { return (float*)((unsigned char*)obj + 0x1C); }

// The shot's charge: its data + 0x11 is 0xFE - (charge - 1) (twisterInit, overlay 131).
static int charge_of(void* obj) {
    const unsigned char* data = data_of(obj);
    if (data == 0) return 0;
    const int c = 0xFF - data[0x11];
    return c >= 1 && c <= 4 ? c : 0;
}

// Turn the direction d (unit) a share of the way toward the nearest enemy in front of p, keeping its length.
static void home(const float* p, float* v, float spd) {
    JfgNear q = { p[0], p[1], p[2], HOMING_REACH, 0 };
    JfgEnemy found[NEARBY];
    const int n = jfg_enemies_near(&q, found, NEARBY);
    for (int i = 0; i < n && i < NEARBY; i++) {
        if (found[i].tribal || found[i].health <= 0) continue;
        float tx = found[i].x - p[0], ty = found[i].y - p[1], tz = found[i].z - p[2];
        const float tl = jfg_sqrt(tx * tx + ty * ty + tz * tz);
        if (tl < 1.0f) continue;
        tx /= tl; ty /= tl; tz /= tl;
        if (tx * v[0] + ty * v[1] + tz * v[2] <= 0.0f) continue; // behind the bounce
        const float to[3] = { found[i].x, found[i].y, found[i].z };
        if (!jfg_line_of_sight(0, found[i].object, p, to)) continue;
        float nx = v[0] / spd * (1.0f - cfg.homing) + tx * cfg.homing;
        float ny = v[1] / spd * (1.0f - cfg.homing) + ty * cfg.homing;
        float nz = v[2] / spd * (1.0f - cfg.homing) + tz * cfg.homing;
        const float nl = jfg_sqrt(nx * nx + ny * ny + nz * nz);
        if (nl < 0.001f) return;
        v[0] = nx / nl * spd;
        v[1] = ny / nl * spd;
        v[2] = nz / nl * spd;
        return;
    }
}

// v turned by deg about the axis n (unit), into out.
static void turn(const float* v, const float* n, float deg, float* out) {
    const float c = jfg_deg_cos(deg), s = jfg_deg_sin(deg), d = (v[0] * n[0] + v[1] * n[1] + v[2] * n[2]) * (1.0f - c);
    const float cx = n[1] * v[2] - n[2] * v[1], cy = n[2] * v[0] - n[0] * v[2], cz = n[0] * v[1] - n[1] * v[0];
    out[0] = v[0] * c + cx * s + n[0] * d;
    out[1] = v[1] * c + cy * s + n[1] * d;
    out[2] = v[2] * c + cz * s + n[2] * d;
}

static Ball* track(void* obj, int left) {
    if (ball_count == MAX_BALLS) return 0;
    Ball* b = &balls[ball_count++];
    b->obj = obj;
    b->left = left;
    return b;
}

// Scale a ball (drawn size and hit radius) by f and set its damage.
static void resize(void* obj, float f, int damage) {
    *(float*)((unsigned char*)obj + 0x08) *= f;
    unsigned char* h = hit_of(obj);
    if (h == 0) return;
    *(short*)(h + 0x06) = (short)(damage < 64 ? 64 : damage > 0x7FFF ? 0x7FFF : damage);
    *(float*)(h + 0x24) *= f;
    *(float*)(h + 0x28) *= f;
}

// A shot heading back toward the hero (within about 70 degrees of the line to them) is turned to run along the
// surface it bounced off instead, on the side it already leans to, a little out from it: bounces carry the fire on,
// never back.
static void keep_off_hero(float* d, const float* p, const float* n, float spd) {
    void* hero = jfg_hero_get();
    if (hero == 0 || spd < 0.01f) return;
    const float* hp = jfg_obj_pos(hero);
    float hx = hp[0] - p[0], hy = hp[1] - p[1], hz = hp[2] - p[2];
    const float hl = jfg_sqrt(hx * hx + hy * hy + hz * hz);
    if (hl < 1.0f) return;
    if ((d[0] * hx + d[1] * hy + d[2] * hz) / (hl * spd) < 0.3f) return;
    // Along the surface: across its normal, level (a wall's run), or the shot's own way along a floor.
    float t[3] = { n[2], 0.0f, -n[0] }; // up x n
    float tl = jfg_sqrt(t[0] * t[0] + t[2] * t[2]);
    if (tl < 0.2f) { t[0] = d[0]; t[2] = d[2]; t[1] = 0.0f; tl = jfg_sqrt(t[0] * t[0] + t[2] * t[2]); }
    if (tl < 0.001f) return;
    t[0] /= tl; t[2] /= tl;
    // The side the shot leans to (so the two halves of a split keep apart), or, going straight back, away from the hero.
    const float lean = t[0] * d[0] + t[2] * d[2];
    if (lean < -0.05f * spd || ((lean < 0.05f * spd) && t[0] * hx + t[2] * hz > 0.0f)) { t[0] = -t[0]; t[2] = -t[2]; }
    float o[3] = { t[0] + n[0] * 0.3f, n[1] * 0.3f, t[2] + n[2] * 0.3f };
    const float ol = jfg_sqrt(o[0] * o[0] + o[1] * o[1] + o[2] * o[2]);
    d[0] = o[0] / ol * spd;
    d[1] = o[1] / ol * spd;
    d[2] = o[2] / ol * spd;
}

static void bounce(Ball* b, const float* hit, int frames) {
    void* obj = b->obj;
    float* v = speed(obj);
    float* p = jfg_obj_pos(obj);
    const float* n = hit + 3;
    const float dot = v[0] * n[0] + v[1] * n[1] + v[2] * n[2];
    float r[3] = { v[0] - 2.0f * dot * n[0], v[1] - 2.0f * dot * n[1], v[2] - 2.0f * dot * n[2] };
    // Off a floor or a ceiling the shot keeps its way across the ground and only turns up (or down): forward.
    if (n[1] > 0.6f || n[1] < -0.6f) {
        r[0] = v[0];
        r[2] = v[2];
        r[1] = (v[1] < 0 ? -v[1] : v[1]) * (n[1] > 0 ? 1.0f : -1.0f);
    }
    // Off the surface, and the hit test's last position with it, so the game's own test starts clear of the wall.
    p[0] = hit[0] + n[0] * BACK_OFF;
    p[1] = hit[1] + n[1] * BACK_OFF;
    p[2] = hit[2] + n[2] * BACK_OFF;
    unsigned char* h = hit_of(obj);
    if (h != 0) {
        float* prev = (float*)(h + 0x0C);
        prev[0] = p[0]; prev[1] = p[1]; prev[2] = p[2];
    }
    unsigned char* data = data_of(obj);
    short* time = data != 0 ? (short*)(data + 0x12) : 0;
    if (time != 0) {
        const int t = *time + EXTRA_TIME;
        *time = (short)(t > 0x7FFF ? 0x7FFF : t);
    }
    b->left--;
    const int damage = h != 0 ? *(short*)(h + 0x06) : 256;
    const float spd = jfg_sqrt(r[0] * r[0] + r[1] * r[1] + r[2] * r[2]);

    // The split: the ball breaks into cfg.pieces smaller shots, each with less damage, fanned evenly across the split
    // angle either side of the bounce: this ball takes the first way, new ones (jfg_fire_plasma) the others. All can
    // bounce (and split) again with the bounces left.
    void* twin = 0;
    float first[3] = { r[0], r[1], r[2] };
    if (cfg.split && cfg.pieces > 1 && ball_count < MAX_BALLS) {
        // They fan out left and right (about the vertical; about the level side line for a shot going straight up or
        // down), so a shot that comes straight off a surface still splits, then none may come back at the hero.
        float axis[3] = { 0.0f, 1.0f, 0.0f };
        if (r[1] * r[1] > 0.9f * spd * spd) { axis[0] = n[2] != 0.0f || n[0] != 0.0f ? -n[2] : 1.0f; axis[1] = 0.0f; axis[2] = n[0]; }
        const float al = jfg_sqrt(axis[0] * axis[0] + axis[1] * axis[1] + axis[2] * axis[2]);
        axis[0] /= al; axis[1] /= al; axis[2] /= al;
        const int kept = damage * cfg.split_damage / 100;
        const float size = *(float*)((unsigned char*)obj + 0x08);
        const float radius = h != 0 ? *(float*)(h + 0x24) : 0.0f, radius2 = h != 0 ? *(float*)(h + 0x28) : 0.0f;
        for (int k = 0; k < cfg.pieces; k++) {
            float d[3];
            turn(r, axis, cfg.angle - 2.0f * cfg.angle * k / (cfg.pieces - 1), d);
            keep_off_hero(d, p, n, spd);
            if (k == 0) { first[0] = d[0]; first[1] = d[1]; first[2] = d[2]; continue; }
            if (ball_count >= MAX_BALLS) break;
            JfgPlasma pl = { p[0], p[1], p[2], p[0] + d[0], p[1] + d[1], p[2] + d[2], 1, spd,
                             time != 0 && *time > 6 ? *time / 6 : 5, jfg_hero_get() };
            void* piece = jfg_fire_plasma(&pl);
            if (piece == 0) break;
            twin = piece;
            float* pv = speed(piece);
            pv[0] = d[0]; pv[1] = d[1]; pv[2] = d[2];
            // Each piece takes this ball's size, then shrinks with it.
            *(float*)((unsigned char*)piece + 0x08) = size;
            unsigned char* ph = hit_of(piece);
            if (ph != 0 && h != 0) {
                *(float*)(ph + 0x24) = radius;
                *(float*)(ph + 0x28) = radius2;
            }
            unsigned char* pd = data_of(piece);
            if (pd != 0 && time != 0) *(short*)(pd + 0x12) = *time;
            resize(piece, SHRINK, kept);
            if (cfg.homing > 0.0f) {
                home(p, pv, spd);
                keep_off_hero(pv, p, n, spd);
            }
            track(piece, b->left);
        }
        if (twin != 0) {
            resize(obj, SHRINK, kept);
            r[0] = first[0]; r[1] = first[1]; r[2] = first[2];
        }
    }
    if (twin == 0) { // a plain bounce: it grows instead
        resize(obj, GROW, damage + 256);
        keep_off_hero(r, p, n, spd);
    }
    v[0] = r[0]; v[1] = r[1]; v[2] = r[2];
    if (cfg.homing > 0.0f) {
        home(p, v, spd);
        keep_off_hero(v, p, n, spd);
    }
    if (cfg.sound) jfg_game_sound(SOUND_BOUNCE, p[0], p[1], p[2]);
}

RECOMP_CALLBACK("*", jfg_on_level_change) void ricochet_level(int level, int character) {
    ball_count = 0;
}

// A new ball: followed while it has bounces (its own splits are followed already).
RECOMP_CALLBACK("*", jfg_on_object_spawn) void ricochet_spawn(void* obj, int kind) {
    if (kind != JFG_KIND_PLASMA || !cfg.enabled) return;
    for (int k = 0; k < ball_count; k++) if (balls[k].obj == obj) return;
    const int charge = charge_of(obj);
    // Charge 1 none, full charge the most: 1, 2, 3, 4 -> 0, 1/3, 2/3, all of them (rounded).
    const int bounces = charge > 1 ? ((charge - 1) * cfg.bounces + 1) / 3 : 0;
    if (bounces > 0 && jfg_object_claim(obj)) track(obj, bounces); // unless another mod drives it
}

RECOMP_CALLBACK("*", jfg_on_object_free) void ricochet_free(void* obj, int kind) {
    for (int i = 0; i < ball_count; i++) {
        if (balls[i].obj != obj) continue;
        ball_count--;
        balls[i].obj = balls[ball_count].obj; // field by field: no memcpy in a mod
        balls[i].left = balls[ball_count].left;
        return;
    }
}

RECOMP_CALLBACK("*", jfg_on_game_tick) void ricochet_tick(int frames) {
    read_config();
    jfg_object_watch(JFG_KIND_PLASMA, cfg.enabled);
    if (jfg_game_paused()) return;
    const int n = ball_count; // not the splits made this tick
    for (int i = 0; i < n; i++) {
        Ball* b = &balls[i];
        if (b->left <= 0) continue;
        // A step and a half ahead, and the ball's own size.
        const float* v = speed(b->obj);
        const float* p = jfg_obj_pos(b->obj);
        const float spd = jfg_sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]);
        if (spd < 0.01f) continue;
        const float ahead = spd * frames * 1.5f + 10.0f;
        const float to[3] = { p[0] + v[0] / spd * ahead, p[1] + v[1] / spd * ahead, p[2] + v[2] / spd * ahead };
        float hit[6];
        if (jfg_level_ray(p, to, hit)) bounce(b, hit, frames);
    }
}
