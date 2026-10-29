// Health Ring: the health meter redrawn as a ring of segments around an emblem, sharp at any resolution, for Jet
// Force Gemini: Recompiled (mod API version 5).
//
// The game's meter (jfg_on_health_draw: cancelled, and drawn here in its place with the overlay) has segments: 6, one
// more per health upgrade, up to 12. Health fills them five times over (max = 5 * segments + 4): health / (segments +
// 1) full rounds, then health % (segments + 1) segments of the next. Each round has its colour (red, orange, yellow,
// lime, green: full health is all green), and the segments lie around the emblem (the game's: a blue cross with green
// tips around a green gem) from its bottom, up its left: 6 make a half ring, all 12 close it. Lost health turns white,
// stays a moment, then drains away; gained health fills in segment by segment (how fast: the Health Animation option);
// a new segment grows in; at low health a red ring pulses around it.
//
// Every shape is drawn once and none lies on another (the cross's arms stop at the gem, its tips meet the arms edge to
// edge), so at a lower opacity nothing shows through anything else: the meter fades as one.

#include "jfg_api.h"
#include "jfg_util.h"

RECOMP_IMPORT("*", unsigned int recomp_get_config_u32(const char* key));
RECOMP_IMPORT("*", double recomp_get_config_double(const char* key));

#define MAX_SEGMENTS 12
#define SLICES 16            // points along each of a segment's arcs
#define SEGMENT_DEGREES 30.0f
#define GAP_DEGREES 3.0f
#define GROW_TICKS 40        // a new segment (a health upgrade) grows in
#define PANEL_SIDE 19.0f     // the weapon panel's outer edge from the HUD's left, in the game's 240-high units
#define PANEL_TOP 13.6f      // and its top from the screen's top

// The Health Animation option (Instant, Fast, Normal, Slow): 1/60 s ticks lost health stays white before it drains,
// then units of health a tick it drains; units a tick gained health fills in.
static const int hold_ticks[4] = { 0, 8, 24, 40 };
static const float drain_speed[4] = { 1000.0f, 0.8f, 0.2f, 0.1f };
static const float fill_speed[4] = { 1000.0f, 1.0f, 0.3f, 0.15f };

// The rounds' colours, the first round's (the last health) first.
static const unsigned int round_colours[5] = { 0xFF3B30, 0xFF8C1A, 0xFFD000, 0xA8E03A, 0x34D25A };
#define EMPTY_FILL 0x0E2536
#define EMPTY_LINE 0x2F5A70
#define GHOST_FILL 0xFFFFFF
#define GHOST_LINE 0xFF9A9A
// The emblem, in the game's colours.
#define ARM_FILL 0x1C3FC4
#define ARM_LINE 0x5C8CFF
#define TIP_FILL 0x2FBF3A
#define GEM_FILL 0x3CCF46
#define GEM_LINE 0xC8D4CE

static struct {
    int enabled;
    int corner;     // 0 top left, 1 top right, 2 bottom left, 3 bottom right
    float size;     // the ring's width, of the screen's height
    float opacity;  // 0..1
    int pulse, next_slot;
    int speed;      // 0 instant, 1 fast, 2 normal, 3 slow
} cfg;

static void* last_hero;
static float shown = -1.0f;   // the health drawn: behind the real one while lost health drains or gained health fills
static int last_health, hold, last_segments, ticks;
static float grow = 1.0f;     // 0..1: the newest segment growing in

static void read_config(void) {
    cfg.enabled = recomp_get_config_u32("enabled") != 0;
    cfg.corner = (int)recomp_get_config_u32("corner");
    cfg.size = (float)recomp_get_config_double("size") / 100.0f;
    cfg.opacity = (float)recomp_get_config_double("opacity") / 100.0f;
    cfg.pulse = recomp_get_config_u32("pulse") != 0;
    cfg.next_slot = recomp_get_config_u32("next_slot") != 0;
    cfg.speed = (int)recomp_get_config_u32("speed");
    if (cfg.speed < 0 || cfg.speed > 3) cfg.speed = 1;
}

// Halfway to white.
static unsigned int lighter(unsigned int rgb) {
    return ((((rgb >> 16) & 0xFF) + 0xFF) / 2 << 16) | ((((rgb >> 8) & 0xFF) + 0xFF) / 2 << 8) | (((rgb & 0xFF) + 0xFF) / 2);
}

// The round whose colour segment i shows at health h (n segments), -1 for an empty one.
static int segment_round(int h, int i, int n) {
    const int round = h / (n + 1), lit = h % (n + 1);
    int r = i < lit ? round : round - 1;
    return r > 4 ? 4 : r;
}

static float cx, cy, r_out, r_in, unit, op;

static void polygon(const float* xy, int count, unsigned int fill, unsigned int line, float thickness) {
    JfgOverlayPolygon p;
    p.xy = xy;
    p.count = count;
    p.fill = fill;
    p.line = line;
    p.thickness = thickness;
    jfg_overlay_polygon(&p);
}

// Segment i (from the bottom, clockwise up the left), between radii inner and outer: filled (fill, 0 for none) and
// outlined (line, 0 for none).
static void segment(int i, float inner, float outer, unsigned int fill, unsigned int line) {
    const float a0 = 90.0f + i * SEGMENT_DEGREES + GAP_DEGREES / 2, a1 = a0 + SEGMENT_DEGREES - GAP_DEGREES;
    float xy[(SLICES + 1) * 4];
    for (int s = 0; s <= SLICES; s++) {
        const float a = a0 + (a1 - a0) * s / SLICES, c = jfg_deg_cos(a), n = jfg_deg_sin(a);
        xy[s * 2] = cx + outer * c;
        xy[s * 2 + 1] = cy + outer * n;
        xy[(2 * SLICES + 1 - s) * 2] = cx + inner * c;
        xy[(2 * SLICES + 1 - s) * 2 + 1] = cy + inner * n;
    }
    polygon(xy, (SLICES + 1) * 2, fill, line, unit * 0.9f);
}

// An arm of the emblem's cross pointing at deg: from the gem's rim (radius gem) out to length l, half width w; blue,
// with a green tip from tip out.
#define ARC 10
static void arm(float deg, float gem, float tip, float l, float w) {
    const float dx = jfg_deg_cos(deg), dy = jfg_deg_sin(deg), px = -dy, py = dx;
    // Where the arm's sides meet the gem's rim: asin(w / gem) as degrees (a short series), at t0 along the arm.
    const float x = w / gem, half = (x + x * x * x / 6 + 3 * x * x * x * x * x / 40) * (180.0f / 3.14159265f);
    float xy[(4 + ARC + 1) * 2];
    int k = 0;
#define PT(t, s) (xy[k++] = cx + dx * (t) + px * (s), xy[k++] = cy + dy * (t) + py * (s))
    PT(tip, -w);
    PT(tip, w);
    for (int j = 0; j <= ARC; j++) { // along the rim, from the w side to the -w side
        const float a = deg + half - 2 * half * j / ARC;
        xy[k++] = cx + gem * jfg_deg_cos(a);
        xy[k++] = cy + gem * jfg_deg_sin(a);
    }
    polygon(xy, k / 2, jfg_rgba(ARM_FILL, op), 0, 0);
    k = 0;
    PT(tip, -w);
    PT(l, -w);
    PT(l, w);
    PT(tip, w);
    polygon(xy, 4, jfg_rgba(TIP_FILL, op), 0, 0);
    // One outline round the whole arm.
    k = 0;
    PT(l, -w);
    PT(l, w);
    for (int j = 0; j <= ARC; j++) {
        const float a = deg + half - 2 * half * j / ARC;
        xy[k++] = cx + gem * jfg_deg_cos(a);
        xy[k++] = cy + gem * jfg_deg_sin(a);
    }
#undef PT
    polygon(xy, k / 2, 0, jfg_rgba(ARM_LINE, op), unit * 0.8f);
}

static void draw(int health, int n, int max) {
    float screen[2];
    jfg_overlay_size(screen);
    unit = screen[1] / 240.0f;
    const float d = screen[1] * cfg.size;
    r_out = d / 2;
    r_in = r_out * 0.77f;
    // In line with the weapon panel: as far in from the HUD's side as its outer edge, and from the top or bottom as
    // its top. The HUD is at the window's edges, or in the middle 4:3 area (HUD in Screen Corners off).
    float area[2]; // the game HUD's edges (in the corners, the HUD ratio's area: Clamp 16:9 in a wider window)
    jfg_hud_area(area);
    const float left = area[0] + PANEL_SIDE * unit, right = area[1] - PANEL_SIDE * unit;
    const int corner = jfg_hud_corner(cfg.corner); // another mod's HUD piece there: the next free corner
    cx = (corner & 1) ? right - r_out : left + r_out;
    cy = (corner & 2) ? screen[1] - PANEL_TOP * unit - r_out : PANEL_TOP * unit + r_out;
    op = cfg.opacity;

    const int s = (int)(shown + 0.5f);
    for (int i = 0; i < n; i++) {
        const int now = segment_round(health, i, n);
        int r = now;
        int ghost = 0;
        if (s > health) ghost = segment_round(s, i, n) != now; // lost: white until it drains
        else if (s < health) r = segment_round(s, i, n);         // gained: fills in
        float inner = r_in, outer = r_out;
        float a = op;
        if (i == n - 1 && grow < 1.0f) {
            outer = r_in + (r_out - r_in) * grow;
            a = op * grow;
        }
        if (ghost) segment(i, inner, outer, jfg_rgba(GHOST_FILL, a * 0.9f), jfg_rgba(GHOST_LINE, a));
        else if (r < 0) segment(i, inner, outer, jfg_rgba(EMPTY_FILL, a * 0.8f), jfg_rgba(EMPTY_LINE, a));
        else segment(i, inner, outer, jfg_rgba(round_colours[r], a), jfg_rgba(lighter(round_colours[r]), a));
    }
    if (cfg.next_slot && n < MAX_SEGMENTS) segment(n, r_in, r_out, 0, jfg_rgba(EMPTY_LINE, op * 0.5f));

    // The emblem: four arms from the gem's rim, then the gem.
    const float l = r_out * 0.56f, gem = l * 0.46f;
    for (int k = 0; k < 4; k++) arm(45.0f + 90.0f * k, gem, l * 0.68f, l, l * 0.27f);
    JfgOverlayCircle c;
    c.x = cx;
    c.y = cy;
    c.radius = gem;
    c.fill = jfg_rgba(GEM_FILL, op);
    c.line = jfg_rgba(GEM_LINE, op);
    c.thickness = unit * 1.2f;
    jfg_overlay_circle(&c);

    // Low health: a red ring pulses around it.
    if (cfg.pulse && health * 4 <= max) {
        const float p = 0.5f + 0.5f * jfg_turn_sin((unsigned int)ticks * 0x500u);
        c.radius = r_out + unit * 3.0f;
        c.fill = 0;
        c.line = jfg_rgba(0xFF3B30, op * (0.25f + 0.65f * p));
        c.thickness = unit * 1.6f;
        jfg_overlay_circle(&c);
    }
}

RECOMP_CALLBACK("*", jfg_on_health_draw) void health_ring_draw(JfgHealth* h) {
    read_config();
    if (!cfg.enabled || h->players != 1) return;
    h->cancel = 1;
    const int n = h->segments < 1 ? 1 : h->segments > MAX_SEGMENTS ? MAX_SEGMENTS : h->segments;
    const int health = h->health < 0 ? 0 : h->health > h->max ? h->max : h->health;
    const int frames = h->frames > 0 ? h->frames : 1;
    ticks += frames;

    if (h->hero != last_hero || shown < 0.0f) {
        last_hero = h->hero;
        shown = (float)health;
        last_health = health;
        last_segments = n;
        grow = 1.0f;
    }
    if (n > last_segments) grow = 0.0f; // a health upgrade
    last_segments = n;
    if (grow < 1.0f) grow = grow + (float)frames / GROW_TICKS < 1.0f ? grow + (float)frames / GROW_TICKS : 1.0f;

    if (health < last_health) hold = hold_ticks[cfg.speed]; // a new hit: the white stays a moment again
    last_health = health;
    const float drain = drain_speed[cfg.speed] * frames, fill = fill_speed[cfg.speed] * frames;
    if (shown > (float)health) {
        if (hold > 0) hold -= frames;
        else shown = shown - drain > (float)health ? shown - drain : (float)health;
    } else if (shown < (float)health) {
        shown = shown + fill < (float)health ? shown + fill : (float)health;
    }
    draw(health, n, h->max);
}
