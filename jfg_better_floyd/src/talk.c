// Better Floyd: Floyd Talks. While Floyd follows the hero (the game's AI flying him, not hidden), he remarks on what
// happens: a level reached for the first time this session, the first level after the one where he joins (253), a
// Tribal near (within the alert range), rescued (jfg_tribal_counts' saved count going up) or killed (jfg_on_kill), the
// hero low on health (jfg_on_health_draw: under 30 % of the meter), the weapon in hand running dry (jfg_on_weapon_hud:
// a weapon with ammo at 0), a streak of the hero's kills (5 within 10 s), his own kills, and a quiet minute or more with
// no kills and no enemy near.
//
// A line shows over a dark rounded backdrop at the bottom of the screen (the overlay), typed out a letter at a time
// with a chirp, held, then faded. Lines come at most every so often (How Chatty), each trigger has its own wait, and each trigger's lines
// are taken in turn. He says nothing while the game is paused, while the HUD is hidden (cutscenes, menus: no health
// meter drawn for a while), or while a line is showing (that trigger's line is dropped).

#include "jfg_api.h"
#include "jfg_util.h"

RECOMP_IMPORT("*", unsigned int recomp_get_config_u32(const char* key));
RECOMP_IMPORT("*", double recomp_get_config_double(const char* key));

#define FLOYD_LEVEL  253   // where Floyd joins
#define NEAR_MAX     16
#define TYPE_RATE    2     // 1/60 s per letter
#define HOLD         150   // 1/60 s a line stays once typed
#define FADE         20
#define TRIGGER_WAIT (60 * 60) // 1/60 s before the same trigger speaks again
#define HUD_GONE     20    // 1/60 s without the health meter drawn: the HUD is hidden

enum { T_JOIN, T_LEVEL, T_TRIBAL_NEAR, T_TRIBAL_SAVED, T_TRIBAL_KILLED, T_LOW_HEALTH, T_AMMO, T_STREAK, T_FLOYD_KILL,
       T_QUIET, T_COUNT };

typedef struct {
    const char* option;  // the group's switch
    int count;
    const char* lines[6];
} Trigger;

static const Trigger triggers[T_COUNT] = {
    [T_JOIN] = { "talk_arrivals", 1, { "Floyd, at your service." } },
    [T_LEVEL] = { "talk_arrivals", 6, {
        "New place. Logging it.",
        "Air: breathable. Locals: hostile.",
        "Stay close, please.",
        "Mapping the area now.",
        "I don't like the look of this.",
        "Somewhere new. How exciting!" } },
    [T_TRIBAL_NEAR] = { "talk_tribals", 6, {
        "Tribal nearby. Be gentle.",
        "Tribal close. Mind your aim.",
        "Someone needs rescuing.",
        "I hear a Tribal.",
        "A friend is near. Hold fire.",
        "Tribal ahead. Careful now." } },
    [T_TRIBAL_SAVED] = { "talk_tribals", 4, {
        "Splendid! One more home.",
        "Rescue confirmed.",
        "Safe and sound.",
        "That one's grateful. I can tell." } },
    [T_TRIBAL_KILLED] = { "talk_tribals", 4, {
        "Oh dear. That was a friend.",
        "I saw nothing.",
        "That was not an enemy.",
        "I'll leave that out of my report." } },
    [T_LOW_HEALTH] = { "talk_health", 4, {
        "Your vitals are alarming.",
        "Health low. Do retreat.",
        "You're leaking. Find health.",
        "Please don't die. I'd be lonely." } },
    [T_AMMO] = { "talk_ammo", 4, {
        "Your weapon is empty.",
        "Click, click. Switch weapons?",
        "Out of ammo.",
        "That one's spent. Try another." } },
    [T_STREAK] = { "talk_kills", 4, {
        "Impressive. Taking notes.",
        "I can't keep up with you!",
        "Remind me never to upset you.",
        "Five down. Show-off." } },
    [T_FLOYD_KILL] = { "talk_kills", 4, {
        "Got one. You're welcome.",
        "Did you see that?",
        "Target removed.",
        "Floyd: one. Them: zero." } },
    [T_QUIET] = { "talk_quiet", 6, {
        "Lovely weather for a war.",
        "I was built for gardening.",
        "Do the Tribals like me?",
        "My left thruster itches.",
        "Quiet. Too quiet.",
        "Are we there yet?" } },
};

static int next_line[T_COUNT];
static int trigger_wait[T_COUNT];
static int global_wait;

// The line showing: its text, how far it is typed, its age in 1/60 s ticks.
static const char* showing = 0;
static int show_ticks;

static int level_now = -1, level_before = -1;
static int join_pending, joined;
static int arrive_wait;
static unsigned char seen_level[64]; // levels reached this session, a bit each (0..511)

static int hud_ticks = 1000;          // 1/60 s since the health meter was last drawn
static int ammo_was = -1, weapon_was = -1;
static int tribal_near_was;
static int saved_was = -1;
static int kill_times[5];             // the ticks of the hero's last kills
static int kill_count;
static int quiet_ticks;
static int now;                       // 1/60 s ticks since start
static int low_health_armed = 1;
static int can_talk;                  // Floyd is there to talk, as the last tick saw

// A line's length (not optimised: the compiler would make the loop a call to strlen, which mods don't have).
__attribute__((optnone)) static int text_len(const char* t) {
    int n = 0;
    while (t[n] != 0) n++;
    return n;
}

static int on(void) {
    return recomp_get_config_u32("enabled") != 0 && recomp_get_config_u32("talk") != 0;
}

// Chatty: 0 Quiet, 1 Normal, 2 Chatty. The least time between lines, and the idle time before small talk.
static int gap(void) {
    const int c = (int)recomp_get_config_u32("chatty");
    return c == 0 ? 40 * 60 : c == 2 ? 10 * 60 : 20 * 60;
}
static int quiet_needed(void) {
    const int c = (int)recomp_get_config_u32("chatty");
    return c == 0 ? 240 * 60 : c == 2 ? 60 * 60 : 120 * 60;
}

static int say(int t, int force) {
    if (!can_talk || !on() || recomp_get_config_u32(triggers[t].option) == 0) return 0;
    if (showing != 0) return 0;
    if (!force && (global_wait > 0 || trigger_wait[t] > 0)) return 0;
    showing = triggers[t].lines[next_line[t]];
    next_line[t] = (next_line[t] + 1) % triggers[t].count;
    show_ticks = 0;
    global_wait = gap();
    trigger_wait[t] = TRIGGER_WAIT;
    jfg_sound_play("chirp", 0.35f, 0.0f, 1.1f);
    return 1;
}

RECOMP_CALLBACK("*", jfg_on_level_change) void talk_level(int level, int character) {
    level_before = level_now;
    level_now = level;
    if (level_before == FLOYD_LEVEL && level != FLOYD_LEVEL && !joined) join_pending = 1;
    arrive_wait = 150;
    showing = 0;
    ammo_was = -1;
    weapon_was = -1;
    tribal_near_was = 0;
    saved_was = -1;
    kill_count = 0;
    quiet_ticks = 0;
}

RECOMP_CALLBACK("*", jfg_on_health_draw) void talk_health(JfgHealth* h) {
    hud_ticks = 0;
    if (h->max <= 0 || h->players != 1) return;
    const int low = h->health * 10 < h->max * 3;
    if (low && low_health_armed && h->health > 0) {
        if (say(T_LOW_HEALTH, 0)) low_health_armed = 0;
    }
    if (h->health * 10 >= h->max * 5) low_health_armed = 1; // healed past half: he may worry again
}

RECOMP_CALLBACK("*", jfg_on_weapon_hud) void talk_weapon(JfgWeaponHud* w) {
    if (w->weapon == weapon_was && ammo_was > 0 && w->ammo == 0 && w->max_ammo > 0) say(T_AMMO, 0);
    weapon_was = w->weapon;
    ammo_was = w->ammo;
}

RECOMP_CALLBACK("*", jfg_on_kill) void talk_kill(JfgKill* k) {
    quiet_ticks = 0;
    if (k->tribal) {
        if (k->killer_kind >= 0 && k->killer_kind <= 3) say(T_TRIBAL_KILLED, 0);
        return;
    }
    if (k->killer_kind == 3) {
        say(T_FLOYD_KILL, 0);
        return;
    }
    if (k->killer_kind < 0 || k->killer_kind > 2) return;
    for (int i = 4; i > 0; i--) kill_times[i] = kill_times[i - 1];
    kill_times[0] = now;
    if (kill_count < 5) kill_count++;
    if (kill_count == 5 && now - kill_times[4] <= 10 * 60) {
        if (say(T_STREAK, 0)) kill_count = 0;
    }
}

// A living Tribal within the alert range; and whether any enemy is within reach (for the quiet minute).
static void look_around(void* hero, int* tribal, int* enemy) {
    const float* at = (const float*)((unsigned char*)hero + 0x0C);
    JfgNear q;
    q.x = at[0];
    q.y = at[1];
    q.z = at[2];
    q.radius = (float)recomp_get_config_double("alert_range");
    q.source = hero;
    JfgEnemy found[NEAR_MAX];
    int n = jfg_enemies_near(&q, found, NEAR_MAX);
    *tribal = 0;
    *enemy = 0;
    for (int i = 0; i < n && i < NEAR_MAX; i++) {
        if (found[i].health <= 0) continue;
        if (found[i].tribal) *tribal = 1;
        else *enemy = 1;
    }
}

// The line over its backdrop (a rounded-ended bar), at the bottom middle of the screen.
#define ARC 10 // points on each rounded end

static void draw(void) {
    float screen[2];
    jfg_overlay_size(screen);
    const float scale = (float)recomp_get_config_double("talk_size") / 100.0f;
    const float size = 11.0f * scale, pad = 4.0f * scale;
    const int len = text_len(showing);
    int typed = show_ticks / TYPE_RATE;
    if (typed > len) typed = len;
    char buf[96];
    int i = 0;
    for (; i < typed && i < (int)sizeof(buf) - 1; i++) buf[i] = showing[i];
    buf[i] = 0;
    const int full_at = len * TYPE_RATE;
    float alpha = 1.0f;
    if (show_ticks > full_at + HOLD) alpha = 1.0f - (float)(show_ticks - full_at - HOLD) / (float)FADE;
    if (alpha < 0.0f) alpha = 0.0f;

    JfgOverlayText t;
    t.size = size;
    t.font = JFG_FONT_LATO;
    t.align = 0;
    t.text = showing; // the backdrop fits the whole line, so it doesn't grow as it types
    float w = 0.0f;
    jfg_overlay_text_width(&t, &w);
    const float h = size + pad * 2.0f, r = h * 0.5f;
    const float cx = screen[0] * 0.5f, cy = screen[1] - r - 16.0f * scale;
    const float half = w * 0.5f + pad * 1.5f; // the straight part's half width
    float xy[(ARC + 1) * 4];
    int n = 0;
    // Half circles on the ends (angles in the game's units, 0x10000 a turn; y grows downwards): the right one from the
    // top (-90 degrees) round to the bottom (90), the left one from the bottom round to the top.
    for (int end = 0; end < 2; end++) {
        const float ex = end == 0 ? cx + half : cx - half;
        for (int k = 0; k <= ARC; k++) {
            const unsigned int a = (end == 0 ? 0xC000u : 0x4000u) + (unsigned int)(k * 0x8000 / ARC);
            xy[n++] = ex + r * jfg_turn_sin(a + 0x4000u); // cos
            xy[n++] = cy + r * jfg_turn_sin(a);
        }
    }
    JfgOverlayPolygon p;
    p.xy = xy;
    p.count = n / 2;
    p.fill = 0x08122A00u | (unsigned int)(alpha * 0xB0);
    p.line = 0;
    p.thickness = 0.0f;
    jfg_overlay_polygon(&p);

    t.x = cx - w * 0.5f; // from the full line's left, so it doesn't drift as it types
    t.y = cy - size * 0.5f;
    t.color = 0xF2F6FF00u | (unsigned int)(alpha * 255.0f);
    t.text = buf;
    jfg_overlay_text(&t);
}

RECOMP_CALLBACK("*", jfg_on_game_tick) void talk_tick(int frames) {
    now += frames;
    if (hud_ticks < 1000) hud_ticks += frames;
    can_talk = 0;
    if (!on()) { showing = 0; return; }
    if (jfg_game_paused()) return; // the box stays as it is under the menu
    for (int t = 0; t < T_COUNT; t++) if (trigger_wait[t] > 0) trigger_wait[t] -= frames;
    if (global_wait > 0) global_wait -= frames;

    int state = 0;
    void* floyd = jfg_floyd_get(&state);
    void* hero = jfg_hero_get();
    const int present = floyd != 0 && state == 0 && hero != 0 && recomp_get_config_u32("hide") == 0 &&
                        jfg_hero_state(hero) != JFG_HERO_DEAD && hud_ticks < HUD_GONE;
    if (!present) { showing = 0; return; }
    can_talk = 1;

    if (showing != 0) {
        show_ticks += frames;
        const int len = text_len(showing);
        if (show_ticks > len * TYPE_RATE + HOLD + FADE) showing = 0;
        else draw();
    }

    // Arriving: his first words after joining, else a level reached for the first time this session.
    if (arrive_wait > 0) {
        arrive_wait -= frames;
        if (arrive_wait <= 0 && level_now >= 0 && level_now < 512) {
            const int seen = seen_level[level_now >> 3] & (1 << (level_now & 7));
            seen_level[level_now >> 3] |= (unsigned char)(1 << (level_now & 7));
            if (join_pending) {
                join_pending = 0;
                joined = say(T_JOIN, 1) || joined;
            } else if (!seen) {
                say(T_LEVEL, 0);
            }
        }
        return;
    }

    int tribal = 0, enemy = 0;
    look_around(hero, &tribal, &enemy);
    if (tribal && !tribal_near_was) say(T_TRIBAL_NEAR, 0);
    tribal_near_was = tribal;

    int saved = 0, killed = 0, left = 0;
    if (jfg_tribal_counts(&saved, &killed, &left)) {
        if (saved_was >= 0 && saved > saved_was) say(T_TRIBAL_SAVED, 0);
        saved_was = saved;
    }

    if (enemy) quiet_ticks = 0;
    else quiet_ticks += frames;
    if (quiet_ticks >= quiet_needed()) {
        if (say(T_QUIET, 0)) quiet_ticks = 0;
    }
}
