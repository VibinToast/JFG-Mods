// Ammo Ring: the weapon panel redrawn as a ring around the weapon's icon, for Jet Force Gemini: Recompiled (mod API
// version 5). It pairs with the Health Ring.
//
// The game's panel is cancelled in jfg_on_weapon_hud and drawn here with the overlay, sharp at any resolution:
// - the ring: ammo as an arc (yellow, orange when low, a red track when empty), the charge bar as a thin inner arc
//   (green to red), the ammo count in the ring's opening, over a dark disc; the weapon's icon in the middle is the
//   game's own picture (jfg_hud_weapon_icon: texture packs replace it), so the disc under it is drawn into the game's
//   HUD (jfg_hud_disc) rather than with the overlay, which is drawn over the game;
// - on a weapon change, the weapons you own fan out along an arc beside the ring and roll along it, as the game's
//   selector strip slides, until the new one sits in the marked slot, named; 4 seconds as the game's selector;
// - when a Tribal is saved or lost, a badge under the ring: saved, lost, left (jfg_tribal_counts);
// - the pick-up messages (jfg_on_hud_message: ammo, keys, parts) as a feed of short lines under it, in the game's own
//   words (jfg_game_text), with the ammo gained; and any other ammo gained with no message (an enemy's dropped weapon,
//   a mod's ammo: modded weapons by their ids, mod API 6), named after the weapon (jfg_weapon_info).
// Lined up with the weapon panel's place (jfg_hud_in_corners), at the top left like the game's.

#include "jfg_api.h"
#include "jfg_util.h"

RECOMP_IMPORT("*", unsigned int recomp_get_config_u32(const char* key));
RECOMP_IMPORT("*", double recomp_get_config_double(const char* key));

#define WEAPONS 16
#define WATCHED 32           // weapon ids whose ammo the feed watches: the game's 16 and the first modded ones
#define MESSAGE_GRACE 30     // ticks a message line covers its weapon's ammo gain (no second line for it)
#define PANEL_SIDE 19.0f     // the weapon panel's outer edge from the HUD's left, in the game's 240-high units
#define PANEL_TOP 13.6f      // and its top from the screen's top
#define FAN_TICKS 240        // 1/60 s ticks the fan stays out after a weapon change (as the game's selector)
#define BADGE_TICKS 240      // ... the Tribal badge after a Tribal is saved or lost
#define LINE_TICKS 180       // ... a pick-up line
#define FADE_TICKS 12
#define MAX_LINES 4
#define FAN_SIDE 2.6f        // weapons shown in the fan: up to this many slots each side of the marked one
#define FAN_EASE 0.3f        // of the way the fan rolls to the new weapon each 1/60 s tick: settled in about 0.15 s
#define POP_TICKS 12         // the ring's icon grows into place after a change
#define ARC_STEP 2.0f         // degrees between an arc's points: smooth at any size
#define ARC_MAX 200

#define BACK 0x0B1622
#define TRACK 0x26384A
#define AMMO 0xFFD000
#define AMMO_LOW 0xFF8C1A
#define EMPTY 0xFF3B30
#define TEXT 0xF2F6FA
#define TEXT_DIM 0x8FA6B8
#define TRIBAL 0x6FA8FF

static struct {
    int enabled;
    float size;     // the ring's width, of the screen's height
    float opacity;  // 0..1
    int font;       // JFG_FONT_*
    int feed, tribals;
} cfg;

static void read_config(void) {
    cfg.enabled = recomp_get_config_u32("enabled") != 0;
    cfg.size = (float)recomp_get_config_double("size") / 100.0f;
    cfg.opacity = (float)recomp_get_config_double("opacity") / 100.0f;
    cfg.font = recomp_get_config_u32("font") ? JFG_FONT_JFG : JFG_FONT_LATO;
    cfg.feed = recomp_get_config_u32("feed") != 0;
    cfg.tribals = recomp_get_config_u32("tribals") != 0;
}

// --- state -----------------------------------------------------------------------------------------------------------
static int last_weapon = -1, fan_ticks, last_character = -1;
static int fan_from = -1;       // the weapon before a change, where the fan comes out and starts rolling from; -1 none
static float fan_pos;           // the fan's place: the slot (in owned order) at the marked spot, rolling to the weapon
static int pop_ticks;
static int saved = -1, killed = -1, left = -1, badge_ticks;
static int ammo_seen[WATCHED];   // each weapon's ammo last frame (the feed's ammo gained; -1 not owned)

typedef struct {
    char text[48];
    int weapon;         // the ammo it is about, -1 none
    int base;           // that weapon's ammo before the pick-up
    int gained;
    int ticks;          // how long it has been shown
} Line;
static Line lines[MAX_LINES];
static int line_count;

// Pick-up messages: ammo for weapon w is text 0x48 + w (extra ammo), 0x57 + w (a clip), 0x66 + w (full ammo),
// 0x75 + w (more capacity); keys are 0x170 + key.
static int ammo_weapon(int msg) {
    int w;
    return jfg_pickup_message(msg, &w) >= JFG_PICKUP_AMMO ? w : -1;
}

RECOMP_CALLBACK("*", jfg_on_hud_message) void ammo_ring_message(int msg, int character, int player) {
    if (player != 0) return;
    if (line_count == MAX_LINES) { // the oldest goes
        for (int i = 1; i < MAX_LINES; i++) lines[i - 1] = lines[i];
        line_count--;
    }
    Line* l = &lines[line_count];
    if (jfg_game_text(msg, l->text, sizeof(l->text)) <= 0) return;
    l->weapon = ammo_weapon(msg);
    l->base = l->weapon >= 0 ? ammo_seen[l->weapon] : 0;
    l->gained = 0;
    l->ticks = 0;
    line_count++;
}

// A line for ammo gained with no message: "<weapon> ammo" (its name from the weapon list, any id).
static void gained_line(int weapon, int base) {
    if (line_count == MAX_LINES) {
        for (int i = 1; i < MAX_LINES; i++) lines[i - 1] = lines[i];
        line_count--;
    }
    JfgWeaponInfo info;
    if (!jfg_weapon_info(weapon, &info) || info.display[0] == 0) return;
    Line* l = &lines[line_count];
    int k = 0;
    for (; k < (int)sizeof(l->text) - 1 && info.display[k] != 0; k++) l->text[k] = info.display[k];
    l->text[k] = 0;
    l->weapon = weapon;
    l->base = base;
    l->gained = 0;
    l->ticks = 0;
    line_count++;
}

// A new area: its own Tribal counts (no badge for the change), no old lines.
RECOMP_CALLBACK("*", jfg_on_level_change) void ammo_ring_level(int level, int character) {
    saved = -1;
    badge_ticks = 0;
    line_count = 0;
    fan_ticks = 0;
    last_character = -1;
    for (int w = 0; w < WATCHED; w++) ammo_seen[w] = -1;
}

// --- drawing helpers -------------------------------------------------------------------------------------------------

static float cx, cy, unit;

static void band(float a0, float a1, float r0, float r1, unsigned int fill) {
    jfg_draw_band(cx, cy, a0, a1, r0, r1, ARC_STEP, fill);
}

static void rect(float x, float y, float w, float h, unsigned int fill) { jfg_draw_rect(x, y, w, h, fill); }

// A box with rounded ends (a pill) or corners of radius r.
static void rounded(float x, float y, float w, float h, float r, unsigned int fill) {
    jfg_draw_rounded(x, y, w, h, r, 16, fill);
}

static void text(float x, float y, float size, unsigned int color, int align, const char* s) {
    jfg_draw_text(x, y, size, color, align, cfg.font, s);
}

static float text_w(float size, const char* s) { return jfg_text_width(size, cfg.font, s); }

static void number(char* out, int v) {
    char tmp[12];
    int n = 0;
    if (v < 0) v = 0;
    do { tmp[n++] = (char)('0' + v % 10); v /= 10; } while (v > 0 && n < 11);
    for (int i = 0; i < n; i++) out[i] = tmp[n - 1 - i];
    out[n] = 0;
}

static void append(char* out, const char* s) {
    while (*out) out++;
    while (*s) *out++ = *s++;
    *out = 0;
}

static float fade(int ticks, int total) {
    if (ticks < FADE_TICKS) return (float)ticks / FADE_TICKS;
    if (ticks > total - FADE_TICKS) return (float)(total - ticks) / FADE_TICKS;
    return 1.0f;
}

static void tribal_glyph(float x, float y, float s, unsigned int color) {
    JfgOverlayCircle head = { x, y - s * 0.55f, s * 0.32f, color, 0, 0 };
    jfg_overlay_circle(&head);
    float body[8] = { x - s * 0.55f, y + s * 0.65f, x - s * 0.25f, y - s * 0.1f, x + s * 0.25f, y - s * 0.1f,
                      x + s * 0.55f, y + s * 0.65f };
    JfgOverlayPolygon p = { body, 4, color, 0, 0 };
    jfg_overlay_polygon(&p);
}

// --- the panel -------------------------------------------------------------------------------------------------------
RECOMP_CALLBACK("*", jfg_on_weapon_hud) void ammo_ring_draw(JfgWeaponHud* h) {
    read_config();
    if (!cfg.enabled) return;
    h->cancel = 1;
    const int frames = h->frames > 0 ? h->frames : 1;
    const float op = cfg.opacity;

    // Changes since the last frame: a weapon change (not a hero switch), the Tribals, the ammo gained.
    if (h->character != last_character) {
        last_character = h->character;
        last_weapon = h->weapon;
        fan_ticks = 0;
        for (int w = 0; w < WATCHED; w++) ammo_seen[w] = jfg_hero_ammo(w);
    }
    if (h->weapon != last_weapon) {
        if (fan_ticks <= 0) fan_from = last_weapon; // the fan comes out on the old weapon, then rolls
        last_weapon = h->weapon;
        fan_ticks = FAN_TICKS;
        pop_ticks = POP_TICKS;
    }
    if (pop_ticks > 0) pop_ticks -= frames;
    int s = 0, k = 0, l = 0;
    if (jfg_tribal_counts(&s, &k, &l)) {
        if (saved >= 0 && (s != saved || k != killed)) badge_ticks = BADGE_TICKS;
        saved = s;
        killed = k;
        left = l;
    }
    for (int i = 0; i < line_count; i++) {
        Line* ln = &lines[i];
        if (ln->weapon >= 0) {
            const int g = jfg_hero_ammo(ln->weapon) - ln->base;
            if (g > ln->gained) ln->gained = g;
        }
        ln->ticks += frames;
    }
    while (line_count > 0 && lines[0].ticks >= LINE_TICKS) {
        for (int i = 1; i < line_count; i++) lines[i - 1] = lines[i];
        line_count--;
    }
    // Ammo gained without a message: a line of its own, named after the weapon.
    const int count = jfg_weapon_count() < WATCHED ? jfg_weapon_count() : WATCHED;
    for (int w = 0; w < count; w++) {
        const int now = jfg_hero_ammo(w);
        if (ammo_seen[w] >= 0 && now > ammo_seen[w] && w != 15) { // 15 lends itself to the modded weapon in hand
            int covered = 0;
            for (int i = 0; i < line_count && !covered; i++) covered = lines[i].weapon == w && lines[i].ticks < MESSAGE_GRACE;
            if (!covered) gained_line(w, ammo_seen[w]);
        }
        ammo_seen[w] = now;
    }
    if (fan_ticks > 0) fan_ticks -= frames;
    if (badge_ticks > 0) badge_ticks -= frames;

    float screen[2];
    jfg_overlay_size(screen);
    unit = screen[1] / 240.0f;
    const float d = screen[1] * cfg.size, r_out = d / 2;
    float area[2]; // the game HUD's edges (in the corners, the HUD ratio's area: Clamp 16:9 in a wider window)
    jfg_hud_area(area);
    const float hud_left = area[0];
    cx = hud_left + PANEL_SIDE + r_out;
    cy = PANEL_TOP + r_out;

    // The ring: a dark band, the ammo arc on it, the charge arc inside; open at the bottom for the count.
    const float thick = d * 0.085f, r_ammo1 = r_out - d * 0.03f, r_ammo0 = r_ammo1 - thick;
    const float r_charge1 = r_ammo0 - d * 0.035f, r_charge0 = r_charge1 - d * 0.03f;
    const float a0 = 135.0f, sweep = 270.0f;
    JfgHudDisc disc = { cx, cy, r_out, jfg_rgba(BACK, op * 0.85f) };
    jfg_hud_disc(&disc);
    const float fill = h->max_ammo > 0 ? (float)h->ammo / h->max_ammo : 0.0f;
    const unsigned int ammo_color = h->ammo <= 0 ? EMPTY : fill <= 0.25f ? AMMO_LOW : AMMO;
    band(a0, a0 + sweep, r_ammo0, r_ammo1, jfg_rgba(h->ammo <= 0 ? jfg_rgb_mix(TRACK, EMPTY, 0.45f) : TRACK, op));
    band(a0, a0 + sweep * (fill > 1.0f ? 1.0f : fill), r_ammo0, r_ammo1, jfg_rgba(ammo_color, op));
    if (h->charge >= 0.0f) {
        band(a0, a0 + sweep, r_charge0, r_charge1, jfg_rgba(TRACK, op * 0.8f));
        const float c = h->charge;
        const unsigned int cc = c < 0.5f ? jfg_rgb_mix(0x3BD45A, 0xFFD000, c * 2) : jfg_rgb_mix(0xFFD000, EMPTY, (c - 0.5f) * 2);
        band(a0, a0 + sweep * c, r_charge0, r_charge1, jfg_rgba(cc, op));
    }
    char buf[64];
    number(buf, h->ammo);
    text(cx, cy + r_out - d * 0.22f, d * 0.2f, jfg_rgba(h->ammo <= 0 ? EMPTY : TEXT, op), 1, buf);
    // The icon in the middle: the game's picture, as large as the ring's opening allows.
    const float clear = r_charge0 - d * 0.03f;
    const float pop = pop_ticks > 0 ? (float)pop_ticks / POP_TICKS : 0.0f; // 1 just changed .. 0
    JfgWeaponIcon icon = { h->weapon, cx, cy - d * 0.02f, clear * 2.0f * 0.8f / 32.0f * (1.0f - 0.3f * pop * pop),
                           (op > 0.6f ? 1.0f : op / 0.6f) * (1.0f - 0.6f * pop * pop) };
    jfg_hud_weapon_icon(&icon);

    float below = cy + r_out + d * 0.06f; // where the badge and the feed start

    // The fan: the weapons you own along an arc right of the ring, rolling until the one in hand is in the marked
    // slot, then named. Slots are in owned order and wrap round, as the game's strip.
    if (fan_ticks > 0) {
        const float t = fade(FAN_TICKS - fan_ticks, FAN_TICKS);
        // Modded weapons (ids 16 up, mod API 6) sit in slot 15, the one they borrow: the one in hand is drawn there.
        const int hand_slot = h->weapon >= WEAPONS - 1 ? WEAPONS - 1 : h->weapon;
        const int from_slot = fan_from >= WEAPONS - 1 ? WEAPONS - 1 : fan_from;
        int order[WEAPONS], n = 0, here = 0, from = -1;
        for (int w = 0; w < WEAPONS; w++) {
            if (!(h->owned & (1u << w)) && w != hand_slot) continue;
            if (w == hand_slot) here = n;
            if (w == from_slot) from = n;
            order[n++] = w == hand_slot ? h->weapon : w;
        }
        if (fan_from >= 0) {
            fan_pos = (float)(from >= 0 ? from : here);
            fan_from = -1;
        }
        // Roll the short way round.
        float to = (float)here - fan_pos;
        while (to > n / 2.0f) to -= n;
        while (to < -n / 2.0f) to += n;
        float ease = 1.0f;
        for (int f = 0; f < frames; f++) ease *= 1.0f - FAN_EASE;
        fan_pos += to * (1.0f - ease);
        if (to > -0.002f && to < 0.002f) fan_pos = (float)here;
        while (fan_pos >= n) fan_pos -= n;
        while (fan_pos < 0.0f) fan_pos += n;
        const float settled = 1.0f - (to < 0 ? -to : to) * 2.0f; // 1 once the new weapon is in the slot
        // Beside the ring, between its top and the badge under it; the marked slot in the middle.
        const float fr = r_out + d * (0.2f + 0.06f * t), dot = d * 0.13f, step = 20.0f, centre = -5.0f;
        const float sx = cx + fr * jfg_deg_cos(centre), sy = cy + fr * jfg_deg_sin(centre);
        for (int i = 0; i < n; i++) {
            float off = (float)i - fan_pos;
            while (off > n / 2.0f) off -= n;
            while (off < -n / 2.0f) off += n;
            const float far = off < 0 ? -off : off;
            if (far > FAN_SIDE || (n == 1 && i != here)) continue;
            const float a = centre + off * step, x = cx + fr * jfg_deg_cos(a), y = cy + fr * jfg_deg_sin(a);
            const float edge = far > FAN_SIDE - 0.6f ? (FAN_SIDE - far) / 0.6f : 1.0f; // fading in and out at the ends
            const float near = far < 1.0f ? 1.0f - far : 0.0f;                         // 1 in the marked slot
            JfgHudDisc fd = { x, y, dot, jfg_rgba(BACK, op * 0.85f * t * edge) };
            jfg_hud_disc(&fd);
            JfgOverlayCircle c = { x, y, dot, 0, jfg_rgba(TEXT_DIM, op * t * edge * 0.6f * (1.0f - near)), unit * 0.8f };
            jfg_overlay_circle(&c);
            JfgWeaponIcon fi = { order[i], x, y, dot * 2.0f * 0.75f / 32.0f * (0.85f + 0.15f * near),
                                 t * edge * (0.5f + 0.5f * near) };
            jfg_hud_weapon_icon(&fi);
        }
        // The marked slot, and the name once the weapon has rolled into it.
        JfgOverlayCircle slot = { sx, sy, dot + unit * 0.4f, 0, jfg_rgba(AMMO, op * t), unit * 1.5f };
        jfg_overlay_circle(&slot);
        JfgWeaponInfo info;
        if (settled > 0.0f && jfg_weapon_info(h->weapon, &info) && info.display[0] != 0) {
            int k = 0;
            for (; k < (int)sizeof(buf) - 1 && info.display[k] != 0; k++) buf[k] = info.display[k];
            buf[k] = 0;
            const float nt = t * settled;
            const float ts = d * 0.13f, tw = text_w(ts, buf), tx = sx + dot + d * 0.08f, ty = sy - ts * 0.55f;
            rounded(tx - d * 0.04f, ty - d * 0.03f, tw + d * 0.08f, ts + d * 0.06f, d * 0.05f, jfg_rgba(BACK, op * 0.8f * nt));
            text(tx, ty, ts, jfg_rgba(TEXT, op * nt), 0, buf);
        }
    } else {
        fan_from = -1;
    }

    // The Tribal badge.
    if (cfg.tribals && badge_ticks > 0 && saved >= 0) {
        const float t = fade(BADGE_TICKS - badge_ticks, BADGE_TICKS), ts = d * 0.13f, hgt = ts + d * 0.08f;
        char a[16], b[16];
        number(a, saved);
        buf[0] = 0;
        append(buf, a);
        append(buf, " saved");
        if (killed > 0) { number(b, killed); append(buf, "  \xC2\xB7  "); append(buf, b); append(buf, " lost"); }
        number(b, left);
        append(buf, "  \xC2\xB7  ");
        append(buf, b);
        append(buf, " left");
        const float tw = text_w(ts, buf), w = tw + hgt + d * 0.1f;
        const float x = cx - w / 2;
        rounded(x, below, w, hgt, hgt / 2, jfg_rgba(BACK, op * 0.85f * t));
        tribal_glyph(x + hgt * 0.62f, below + hgt / 2, hgt * 0.4f, jfg_rgba(TRIBAL, op * t));
        text(x + hgt * 1.05f, below + d * 0.04f, ts, jfg_rgba(TEXT, op * t), 0, buf);
        below += hgt + d * 0.04f;
    }

    // The feed: one line a pick-up, newest at the bottom, each fading out.
    if (cfg.feed) {
        const float ts = d * 0.125f, hgt = ts + d * 0.08f, x = hud_left + PANEL_SIDE;
        for (int i = 0; i < line_count; i++) {
            const Line* ln = &lines[i];
            const float t = fade(ln->ticks, LINE_TICKS);
            const float slide = (1.0f - (ln->ticks < FADE_TICKS ? (float)ln->ticks / FADE_TICKS : 1.0f)) * d * 0.2f;
            char gain[16] = "";
            if (ln->gained > 0) { gain[0] = '+'; number(gain + 1, ln->gained); }
            const float tw = text_w(ts, ln->text), gw = gain[0] ? text_w(ts, gain) + d * 0.08f : 0.0f;
            const float w = tw + gw + d * 0.16f;
            const unsigned int accent = ln->weapon >= 0 ? AMMO : 0x3FD0FF;
            rect(x - slide, below, w, hgt, jfg_rgba(BACK, op * 0.85f * t));
            rect(x - slide, below, d * 0.025f, hgt, jfg_rgba(accent, op * t));
            text(x - slide + d * 0.07f, below + d * 0.04f, ts, jfg_rgba(TEXT, op * t), 0, ln->text);
            if (gain[0]) text(x - slide + w - d * 0.05f, below + d * 0.04f, ts, jfg_rgba(AMMO, op * t), 2, gain);
            below += hgt + d * 0.025f;
        }
    }
}
