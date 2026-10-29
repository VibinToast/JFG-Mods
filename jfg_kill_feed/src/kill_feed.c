// Kill Feed: a feed of kills at the top right, for Jet Force Gemini: Recompiled (mod API version 5). It pairs with the
// Health Ring and the Ammo Ring.
//
// Each kill (jfg_on_kill) is a row: who fired (the hero, in their colour, or Floyd), the weapon's icon, and who died.
// The icon is the game's own picture (jfg_hud_weapon_icon: texture packs replace it) on a dark disc drawn into the
// game's HUD (jfg_hud_disc), so the overlay's names sit in pills either side of it rather than over it. The victim's
// name is its object's own name from the player's game, spaced out ("CaveBeetle" becomes "Cave Beetle"); this mod ships none.
// Tribals are named "Tribal" and their row is tinted red. Kills by others (an enemy's shot, a blast) show a crosshair
// in place of the icon. Rows come in from the right, newest at the bottom, and fade out after a few seconds.
// Drawn while the weapon panel is (jfg_on_weapon_hud: in play, not in menus or cutscenes).

#include "jfg_api.h"
#include "jfg_util.h"

RECOMP_IMPORT("*", unsigned int recomp_get_config_u32(const char* key));
RECOMP_IMPORT("*", double recomp_get_config_double(const char* key));

#define PANEL_SIDE 19.0f     // the HUD's side margin (the weapon panel's), in the game's 240-high units
#define PANEL_TOP 13.6f      // and its top margin
#define MAX_ROWS 8
#define FADE_TICKS 12        // 1/60 s ticks a row takes to come in and to go
#define ROW_EASE 0.25f       // of the way a row moves to its place each tick, when one above it goes
#define ARC_MAX 80

#define BACK 0x0B1622
#define TEXT 0xF2F6FA
#define ENEMY 0xFF6B5E
#define TRIBAL 0xA8CCFF
#define TRIBAL_ROW 0x4A1A1E
#define OTHER 0xFFB347

static const char* const HERO_NAMES[4] = { "Vela", "Juno", "Lupus", "Floyd" };
static const unsigned int HERO_COLORS[4] = { 0xFF8FC8, 0x5CB8FF, 0xFFC04D, 0xC8D4DE };

static struct {
    int enabled;
    float size;     // 1 = the default row height
    float opacity;  // 0..1
    int font;       // JFG_FONT_*
    int rows;       // rows shown at most
    int ticks;      // how long a row stays, 1/60 s
    int others;     // kills by others shown
} cfg;

static void read_config(void) {
    cfg.enabled = recomp_get_config_u32("enabled") != 0;
    cfg.size = (float)recomp_get_config_double("size") / 100.0f;
    cfg.opacity = (float)recomp_get_config_double("opacity") / 100.0f;
    cfg.font = recomp_get_config_u32("font") ? JFG_FONT_JFG : JFG_FONT_LATO;
    cfg.rows = (int)recomp_get_config_double("rows");
    if (cfg.rows < 1) cfg.rows = 1;
    if (cfg.rows > MAX_ROWS) cfg.rows = MAX_ROWS;
    cfg.ticks = (int)(recomp_get_config_double("seconds") * 60.0);
    if (cfg.ticks < FADE_TICKS * 3) cfg.ticks = FADE_TICKS * 3;
    cfg.others = recomp_get_config_u32("others") != 0;
}

// --- the rows --------------------------------------------------------------------------------------------------------
typedef struct {
    char killer[24];
    char victim[24];
    unsigned int killer_color;
    int weapon;         // -1: no icon (a crosshair)
    int tribal;
    void* who;          // the victim's object, to drop a second report of the same death
    int ticks;          // how long it has been shown
    float y;            // its place, moving up as rows above it go (from the feed's top, in rows)
} Row;
static Row rows[MAX_ROWS];
static int row_count;

// The oldest row goes, the rest move up a place (word by word: no memcpy in a mod).
static void drop_oldest(void) {
    for (int i = 1; i < row_count; i++) {
        unsigned int* to = (unsigned int*)&rows[i - 1];
        const unsigned int* from = (const unsigned int*)&rows[i];
        for (unsigned int w = 0; w < sizeof(Row) / 4; w++) to[w] = from[w];
    }
    row_count--;
}

// "CaveBeetle" -> "Cave Beetle": spaces where a capital follows a small letter, trailing digits dropped.
static void spaced(char* out, int size, const char* name) {
    int n = 0, end = 0;
    while (end < 16 && name[end]) end++;
    while (end > 0 && name[end - 1] >= '0' && name[end - 1] <= '9') end--;
    for (int i = 0; i < end && n < size - 2; i++) {
        const char c = name[i];
        if (i > 0 && c >= 'A' && c <= 'Z' && name[i - 1] >= 'a' && name[i - 1] <= 'z') out[n++] = ' ';
        out[n++] = (i == 0 && c >= 'a' && c <= 'z') ? (char)(c - 32) : c;
    }
    out[n] = 0;
}

static void copy(char* out, int size, const char* s) {
    int n = 0;
    while (s[n] && n < size - 1) { out[n] = s[n]; n++; }
    out[n] = 0;
}

RECOMP_CALLBACK("*", jfg_on_kill) void kill_feed_kill(JfgKill* k) {
    read_config();
    if (!cfg.enabled) return;
    const int by_hero = k->killer_kind >= 0 && k->killer_kind <= 3;
    if (!by_hero && !cfg.others) return;
    for (int i = 0; i < row_count; i++) {
        if (rows[i].who == k->victim) return; // reported twice (a blast and its death both count)
    }
    if (row_count == MAX_ROWS) drop_oldest();
    Row* r = &rows[row_count];
    if (by_hero) {
        copy(r->killer, sizeof(r->killer), HERO_NAMES[k->killer_kind]);
        r->killer_color = HERO_COLORS[k->killer_kind];
        // Any weapon id: the game's (0..15) or a mod's (16 up, credited by its mod; jfg_hud_weapon_icon draws its icon).
        r->weapon = (k->killer_kind < 3 && k->weapon >= 0) ? k->weapon : -1;
    } else {
        spaced(r->killer, sizeof(r->killer), k->killer_kind == 4 ? k->killer_name : "");
        r->killer_color = OTHER;
        r->weapon = -1;
    }
    if (k->tribal) copy(r->victim, sizeof(r->victim), "Tribal");
    else spaced(r->victim, sizeof(r->victim), k->victim_name);
    if (!r->victim[0]) copy(r->victim, sizeof(r->victim), "?");
    r->tribal = k->tribal;
    r->who = k->victim;
    r->ticks = 0;
    r->y = (float)row_count;
    row_count++;
}

RECOMP_CALLBACK("*", jfg_on_level_change) void kill_feed_level(int level, int character) {
    row_count = 0;
}

// --- drawing helpers -------------------------------------------------------------------------------------------------

static void rounded(float x, float y, float w, float h, float r, unsigned int fill) {
    jfg_draw_rounded(x, y, w, h, r, 8, fill);
}

static void text(float x, float y, float size, unsigned int color, int align, const char* s) {
    jfg_draw_text(x, y, size, color, align, cfg.font, s);
}

static float text_w(float size, const char* s) { return jfg_text_width(size, cfg.font, s); }

static float fade(int ticks, int total) {
    if (ticks < FADE_TICKS) return (float)ticks / FADE_TICKS;
    if (ticks > total - FADE_TICKS) return (float)(total - ticks) / FADE_TICKS;
    return 1.0f;
}

// A crosshair: a ring with four ticks, for kills without a weapon of the heroes'.
static void crosshair(float x, float y, float r, float line, unsigned int color) {
    JfgOverlayCircle c = { x, y, r * 0.55f, 0, color, line };
    jfg_overlay_circle(&c);
    for (int i = 0; i < 4; i++) {
        const float dx = i == 0 ? 1.0f : i == 1 ? -1.0f : 0.0f, dy = i == 2 ? 1.0f : i == 3 ? -1.0f : 0.0f;
        const float a = r * 0.3f, b = r * 0.85f, hw = line / 2;
        float xy[8] = { x + dx * a - dy * hw, y + dy * a - dx * hw, x + dx * b - dy * hw, y + dy * b - dx * hw,
                        x + dx * b + dy * hw, y + dy * b + dx * hw, x + dx * a + dy * hw, y + dy * a + dx * hw };
        JfgOverlayPolygon p = { xy, 4, color, 0, 0 };
        jfg_overlay_polygon(&p);
    }
}

// --- the feed --------------------------------------------------------------------------------------------------------
RECOMP_CALLBACK("*", jfg_on_weapon_hud) void kill_feed_draw(JfgWeaponHud* h) {
    read_config();
    if (!cfg.enabled) { row_count = 0; return; }
    const int frames = h->frames > 0 ? h->frames : 1;

    // Age the rows; the old ones go, and more than the rows shown push the oldest out early.
    for (int i = 0; i < row_count; i++) rows[i].ticks += frames;
    const int extra = row_count - cfg.rows;
    for (int i = 0; i < extra; i++) {
        if (rows[i].ticks < cfg.ticks - FADE_TICKS) rows[i].ticks = cfg.ticks - FADE_TICKS;
    }
    while (row_count > 0 && rows[0].ticks >= cfg.ticks) drop_oldest();
    if (row_count == 0) return;

    float screen[2];
    jfg_overlay_size(screen);
    float area[2]; // the game HUD's edges (in the corners, the HUD ratio's area: Clamp 16:9 in a wider window)
    jfg_hud_area(area);
    const float hud_right = area[1];
    const float op = cfg.opacity, hgt = 11.0f * cfg.size, ts = hgt * 0.64f, gap = hgt * 0.4f;
    const float pad = hgt * 0.45f, corner = hgt * 0.3f, rad = hgt * 0.62f, space = hgt * 0.14f;
    const float right = hud_right - PANEL_SIDE;
    float ease = 1.0f;
    for (int f = 0; f < frames; f++) ease *= 1.0f - ROW_EASE;

    for (int i = 0; i < row_count; i++) {
        Row* r = &rows[i];
        r->y += ((float)i - r->y) * (1.0f - ease);
        const float t = fade(r->ticks, cfg.ticks);
        const float in = r->ticks < FADE_TICKS ? 1.0f - (float)r->ticks / FADE_TICKS : 0.0f;
        const float slide = in * in * hgt * 2.0f;
        const float y = PANEL_TOP + (rad - hgt / 2) + r->y * (hgt + gap), mid = y + hgt / 2;
        const float ty = mid - ts * 0.56f;

        // From the right: the victim, the icon, the killer.
        const float vw = text_w(ts, r->victim) + pad * 2;
        float x = right + slide - vw;
        rounded(x, y, vw, hgt, corner, jfg_rgba(r->tribal ? TRIBAL_ROW : BACK, op * 0.85f * t));
        text(x + pad, ty, ts, jfg_rgba(r->tribal ? TRIBAL : ENEMY, op * t), 0, r->victim);
        const float ix = x - space - rad;
        JfgHudDisc disc = { ix, mid, rad, jfg_rgba(BACK, op * 0.85f * t) };
        jfg_hud_disc(&disc);
        if (r->weapon >= 0) {
            JfgWeaponIcon icon = { r->weapon, ix, mid, rad * 2.0f * 0.85f / 32.0f, t * (op > 0.6f ? 1.0f : op / 0.6f) };
            jfg_hud_weapon_icon(&icon);
        } else {
            crosshair(ix, mid, rad * 0.8f, hgt * 0.09f, jfg_rgba(OTHER, op * t));
        }
        if (r->killer[0]) {
            const float kw = text_w(ts, r->killer) + pad * 2;
            x = ix - rad - space - kw;
            rounded(x, y, kw, hgt, corner, jfg_rgba(BACK, op * 0.85f * t));
            text(x + pad, ty, ts, jfg_rgba(r->killer_color, op * t), 0, r->killer);
        }
    }
}
