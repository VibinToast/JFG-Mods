// Minimap: a map of the area you are in, always on screen while you play, for Jet Force Gemini: Recompiled (mod API
// version 5).
//
// The map is drawn from the level itself: when an area starts, its floors (the level's triangles that face up or
// down: jfg_level_triangles) are laid flat on a 1024 x 1024 grid fitted to the area (north up: -z), and turned into a
// 512 x 512 picture (4 grid cells a pixel, so its edges are smooth): a dark translucent fill with a light rim. The port
// draws it over the game at the window's own resolution (the overlay: jfg_overlay_image, jfg_overlay_draw_image), with
// the hero as an arrow pointing where it faces and dots, as anti-aliased shapes: the enemies (red) and tribals (blue)
// (jfg_enemies_near over the whole area), and the pickups not yet taken, chests and totem poles (jfg_objects_of_kind;
// colours and shapes: item_kinds below); every few ticks.

#include "jfg_api.h"
#include "jfg_util.h"

RECOMP_IMPORT("*", unsigned int recomp_get_config_u32(const char* key));
RECOMP_IMPORT("*", double recomp_get_config_double(const char* key));

#define GRID 1024                    // the floors' grid, cells a side
#define PIC 512                      // the picture, pixels a side
#define RIM 3                        // the rim's width, in picture pixels
#define CHUNK 256                    // triangles read at a time
#define MAX_DOTS 256
#define FADE_TICKS 12                // 1/60 s ticks a fade takes (out, then in)
#define SETTLE 30                    // ticks the area's triangle count must stay the same before its map is built

static unsigned char cover[GRID * GRID];          // 1 where a floor covers the cell
static unsigned char inside[PIC * PIC];           // 0..4 cells of each pixel covered
static unsigned int picture[PIC * PIC];           // 0xRRGGBBAA
static int stack[PIC * PIC];                      // the flood fill's pixels to visit
static unsigned char seen[PIC * PIC];
#define MIN_ISLAND (PIC * PIC / 3000)             // floor pieces smaller than this are left off (crate tops, steps)
#define MIN_HOLE (PIC * PIC / 1500)               // holes smaller than this are filled (pillars, props)
static JfgTriangle tris[CHUNK];

static int level_now = -1, built_for = -2;
static float min_x, min_z, span;                  // the floors being laid: from (min_x, min_z), span units a side
// The map on screen: its picture (overlay id 1 or 2, the other one takes the next area's), its place in the level and
// how visible it is (0..1, faded out before a new one is swapped in, and in after).
static int shown_image, ready_image;              // 0: none
static float show_x, show_z, show_span;
static float ready_x, ready_z, ready_span;
static float vis, vis_target;

// What each dot is: its colour and size (sizes, colours below), and its shape: chests and totems are rectangles.
enum { DOT_ENEMY, DOT_TRIBAL, DOT_ITEM, DOT_KEY_ITEM, DOT_AMMO, DOT_UPGRADE, DOT_HEALTH, DOT_TOKEN, DOT_CHEST, DOT_TOTEM };
typedef struct { float x, z; int type; unsigned int yaw; } Dot;
static Dot dots[MAX_DOTS];
static int dot_count, dot_wait;

static struct {
    int enabled;
    int corner;     // 0 top left, 1 top right, 2 bottom left, 3 bottom right
    float size;     // of the screen's height
    float opacity;  // 0..1
    int enemies, tribals, items, small_items;
} cfg;

static void read_config(void) {
    cfg.enabled = recomp_get_config_u32("enabled") != 0;
    cfg.corner = (int)recomp_get_config_u32("corner");
    cfg.size = (float)recomp_get_config_double("size") / 100.0f;
    cfg.opacity = (float)recomp_get_config_double("opacity") / 100.0f;
    cfg.enemies = recomp_get_config_u32("enemies") != 0;
    cfg.tribals = recomp_get_config_u32("tribals") != 0;
    cfg.items = recomp_get_config_u32("items") != 0;
    cfg.small_items = recomp_get_config_u32("health_tokens") != 0;
}

// --- the picture ------------------------------------------------------------------------------------------------------
// A floor or a ceiling: its normal mostly up or down (walls and steep slopes are left out).
static int flat(const JfgTriangle* t) {
    const float ax = (float)(t->v[1][0] - t->v[0][0]), ay = (float)(t->v[1][1] - t->v[0][1]), az = (float)(t->v[1][2] - t->v[0][2]);
    const float bx = (float)(t->v[2][0] - t->v[0][0]), by = (float)(t->v[2][1] - t->v[0][1]), bz = (float)(t->v[2][2] - t->v[0][2]);
    const float nx = ay * bz - az * by, ny = az * bx - ax * bz, nz = ax * by - ay * bx;
    const float len2 = nx * nx + ny * ny + nz * nz;
    return len2 > 0.0f && ny * ny > 0.4f * len2; // more than about 50 degrees from upright
}

static int count_triangles(void) { return jfg_level_triangles(0, 0, 0, 0); }

// The area's extent from its floors, so the map's scale stays the same for the whole area.
static int measure(void) {
    const int total = count_triangles();
    float x0 = 1e9f, z0 = 1e9f, x1 = -1e9f, z1 = -1e9f;
    for (int first = 0; first < total; first += CHUNK) {
        const int n = jfg_level_triangles(tris, first, CHUNK, 0) - first;
        for (int i = 0; i < n && i < CHUNK; i++) {
            if (!flat(&tris[i])) continue;
            for (int k = 0; k < 3; k++) {
                const float x = tris[i].v[k][0], z = tris[i].v[k][2];
                if (x < x0) x0 = x;
                if (x > x1) x1 = x;
                if (z < z0) z0 = z;
                if (z > z1) z1 = z;
            }
        }
    }
    if (x1 <= x0 || z1 <= z0) return 0;
    span = (x1 - x0 > z1 - z0 ? x1 - x0 : z1 - z0) * 1.04f; // a little margin, square
    min_x = (x0 + x1) * 0.5f - span * 0.5f;
    min_z = (z0 + z1) * 0.5f - span * 0.5f;
    return 1;
}

static float edge(float ax, float ay, float bx, float by, float px, float py) {
    return (bx - ax) * (py - ay) - (by - ay) * (px - ax);
}

// One triangle onto the grid: the cells whose centre it covers (either winding); one too small for any, its middle.
static void lay(const JfgTriangle* t) {
    const float k = (float)GRID / span;
    float x[3], y[3];
    for (int i = 0; i < 3; i++) {
        x[i] = ((float)t->v[i][0] - min_x) * k;
        y[i] = ((float)t->v[i][2] - min_z) * k;
    }
    float lx = x[0], hx = x[0], ly = y[0], hy = y[0];
    for (int i = 1; i < 3; i++) {
        if (x[i] < lx) lx = x[i];
        if (x[i] > hx) hx = x[i];
        if (y[i] < ly) ly = y[i];
        if (y[i] > hy) hy = y[i];
    }
    int c0 = (int)lx, c1 = (int)hx, r0 = (int)ly, r1 = (int)hy;
    if (c0 < 0) c0 = 0;
    if (r0 < 0) r0 = 0;
    if (c1 >= GRID) c1 = GRID - 1;
    if (r1 >= GRID) r1 = GRID - 1;
    int hit = 0;
    for (int r = r0; r <= r1; r++) {
        const float py = (float)r + 0.5f;
        for (int c = c0; c <= c1; c++) {
            const float px = (float)c + 0.5f;
            const float e0 = edge(x[0], y[0], x[1], y[1], px, py);
            const float e1 = edge(x[1], y[1], x[2], y[2], px, py);
            const float e2 = edge(x[2], y[2], x[0], y[0], px, py);
            if ((e0 >= 0 && e1 >= 0 && e2 >= 0) || (e0 <= 0 && e1 <= 0 && e2 <= 0)) {
                cover[r * GRID + c] = 1;
                hit = 1;
            }
        }
    }
    if (!hit) {
        const int c = (int)((x[0] + x[1] + x[2]) / 3.0f), r = (int)((y[0] + y[1] + y[2]) / 3.0f);
        if (c >= 0 && c < GRID && r >= 0 && r < GRID) cover[r * GRID + c] = 1;
    }
}

static int solid_at(int x, int y) { // a pixel at least half floor
    return x >= 0 && y >= 0 && x < PIC && y < PIC && inside[y * PIC + x] >= 2;
}

// How far a floor pixel is from the nearest pixel that is not floor, up to RIM + 1 (a square neighbourhood).
static int rim_distance(int x, int y) {
    for (int d = 1; d <= RIM; d++) {
        for (int k = -d; k <= d; k++) {
            if (!solid_at(x + k, y - d) || !solid_at(x + k, y + d) || !solid_at(x - d, y + k) || !solid_at(x + d, y + k)) return d;
        }
    }
    return RIM + 1;
}

// The connected pixels from (x0, y0) that are floor (floor = 1) or not: how many, marking them seen. If small (fewer
// than limit) and not touching the picture's edge, they are flipped: a small island cleared, a small hole filled.
static void tidy_region(int x0, int y0, int floor, int limit) {
    int top = 0, count = 0, edge = 0;
    stack[top++] = y0 * PIC + x0;
    seen[y0 * PIC + x0] = 1;
    while (top > 0) {
        const int i = stack[--top], x = i % PIC, y = i / PIC;
        count++;
        if (x == 0 || y == 0 || x == PIC - 1 || y == PIC - 1) edge = 1;
        const int nb[4] = { x > 0 ? i - 1 : -1, x < PIC - 1 ? i + 1 : -1, y > 0 ? i - PIC : -1, y < PIC - 1 ? i + PIC : -1 };
        for (int k = 0; k < 4; k++) {
            const int j = nb[k];
            if (j < 0 || seen[j] || (inside[j] >= 2) != floor) continue;
            seen[j] = 1;
            stack[top++] = j;
        }
    }
    if (count >= limit || (!floor && edge)) return;
    // Flip it: walk it again from the start (seen marks it; a second pass with a second mark).
    top = 0;
    stack[top++] = y0 * PIC + x0;
    seen[y0 * PIC + x0] = 2;
    while (top > 0) {
        const int i = stack[--top], x = i % PIC, y = i / PIC;
        const int nb[4] = { x > 0 ? i - 1 : -1, x < PIC - 1 ? i + 1 : -1, y > 0 ? i - PIC : -1, y < PIC - 1 ? i + PIC : -1 };
        for (int k = 0; k < 4; k++) {
            const int j = nb[k];
            if (j < 0 || seen[j] != 1 || (inside[j] >= 2) != floor) continue;
            seen[j] = 2;
            stack[top++] = j;
        }
        inside[i] = floor ? 0 : 4;
    }
}

static void tidy(void) {
    for (int i = 0; i < PIC * PIC; i++) seen[i] = 0;
    for (int i = 0; i < PIC * PIC; i++) {
        if (!seen[i] && inside[i] >= 2) tidy_region(i % PIC, i / PIC, 1, MIN_ISLAND);
    }
    for (int i = 0; i < PIC * PIC; i++) seen[i] = 0;
    for (int i = 0; i < PIC * PIC; i++) {
        if (!seen[i] && inside[i] < 2) tidy_region(i % PIC, i / PIC, 0, MIN_HOLE);
    }
    for (int i = 0; i < PIC * PIC; i++) { // a sliver (a quarter floor) stays only as the soft edge of floor next to it
        if (inside[i] != 1) continue;
        const int x = i % PIC, y = i / PIC;
        if (!(solid_at(x - 1, y) || solid_at(x + 1, y) || solid_at(x, y - 1) || solid_at(x, y + 1))) inside[i] = 0;
    }
}

#define FILL_RGB 0x1E6E2Eu   // dark green
#define RIM_RGB 0x8CFF8Cu    // light green

// Lays the area's floors and makes its picture; 0 if it has none.
static int build(void) {
    if (!measure()) return 0;
    for (int i = 0; i < GRID * GRID; i++) cover[i] = 0;
    const int total = count_triangles();
    for (int first = 0; first < total; first += CHUNK) {
        const int n = jfg_level_triangles(tris, first, CHUNK, 0) - first;
        for (int i = 0; i < n && i < CHUNK; i++) {
            if (flat(&tris[i])) lay(&tris[i]);
        }
    }
    for (int y = 0; y < PIC; y++) {
        for (int x = 0; x < PIC; x++) {
            const unsigned char* p = &cover[(y * 2) * GRID + x * 2];
            inside[y * PIC + x] = (unsigned char)(p[0] + p[1] + p[GRID] + p[GRID + 1]);
        }
    }
    tidy();
    // The fill, translucent; the rim, solid, blended into the fill over its inner pixel; edge pixels faded by how much
    // of them is floor.
    for (int y = 0; y < PIC; y++) {
        for (int x = 0; x < PIC; x++) {
            const int c = inside[y * PIC + x];
            unsigned int rgb = FILL_RGB, a = 0;
            if (c > 0) {
                const int d = c >= 2 ? rim_distance(x, y) : 1;
                if (d <= RIM - 1) { rgb = RIM_RGB; a = 0xFF; }
                else if (d == RIM) { rgb = jfg_rgb_mix(RIM_RGB, FILL_RGB, 0.5f); a = 0xE0; }
                else { a = 0xA8; }
                if (c < 4) a = a * (unsigned int)(c + 1) / 5;
            }
            picture[y * PIC + x] = (rgb << 8) | a;
        }
    }
    return 1;
}

// --- the dots -----------------------------------------------------------------------------------------------------------
// The pickups shown (Recomp-Docs LEVEL_OBJECTS.md lists every kind and where they are): keys, ship and Floyd parts
// (yellow, full size), the other collectables, weapons, power-ups and the parts to bring back (yellow), ammo (orange,
// small), upgrades (purple: ammo capacity, the health upgrade GeminiPowerup), chests (yellow rectangles, turned as
// they stand; not once opened or holding what the hero already has), totem poles not yet touched (brown rectangles), health (pink,
// small) and tokens (cyan, small).
static const int item_kinds[] = { JFG_KIND_WEAPON, JFG_KIND_COLLECTABLE, JFG_KIND_KEY, JFG_KIND_AMMO, JFG_KIND_MULTI,
                                  JFG_KIND_POWERUP, JFG_KIND_CHEST, JFG_KIND_QUEST, JFG_KIND_PART, JFG_KIND_TOTEM };

// Whether the object's definition (object + 0x40) is named name: its name is at definition + 4.
static int named(void* object, const char* name) {
    const char* def = *(const char**)((unsigned char*)object + 0x40);
    if (def == 0) return 0;
    const char* n = def + 4;
    for (int i = 0; i < 16; i++) {
        if (n[i] != name[i]) return 0;
        if (name[i] == 0) return 1;
    }
    return 1;
}

static int starts(void* object, const char* prefix) {
    const char* def = *(const char**)((unsigned char*)object + 0x40);
    if (def == 0) return 0;
    for (int i = 0; prefix[i]; i++) if (def[4 + i] != prefix[i]) return 0;
    return 1;
}

// The dot for an object of kind, or -1 for none.
static int dot_type(int kind, void* obj) {
    switch (kind) {
    case JFG_KIND_HEALTH: return named(obj, "GeminiPowerup") ? DOT_UPGRADE : DOT_HEALTH;
    case JFG_KIND_TOKEN: return DOT_TOKEN;
    case JFG_KIND_AMMO: return named(obj, "ammocapacity") ? DOT_UPGRADE : DOT_AMMO;
    case JFG_KIND_MULTI: return DOT_AMMO;
    case JFG_KIND_KEY: return DOT_KEY_ITEM;
    case JFG_KIND_COLLECTABLE: return starts(obj, "ship") || starts(obj, "Sidekick") ? DOT_KEY_ITEM : DOT_ITEM;
    case JFG_KIND_TOTEM: {
        // Touched (its data + 2; totemPoleInit / totemPoleControl, overlay 128): set when the hero touches it, and
        // when the area loads with its game flag already set.
        const unsigned char* data = *(const unsigned char**)((unsigned char*)obj + 0x68);
        if (data != 0 && data[2] != 0) return -1;
        return DOT_TOTEM;
    }
    case JFG_KIND_CHEST: {
        // Its state (its data, object + 0x68, + 4; chestInit, overlay 82): 4 opened, 5 holding what the hero has.
        const unsigned char* data = *(const unsigned char**)((unsigned char*)obj + 0x68);
        if (data != 0 && (data[4] == 4 || data[4] == 5)) return -1;
        return DOT_CHEST;
    }
    default: return DOT_ITEM;
    }
}

static void add_kind(int kind) {
    static JfgObjectInfo found[MAX_DOTS];
    int n = jfg_objects_of_kind(kind, found, MAX_DOTS);
    if (n > MAX_DOTS) n = MAX_DOTS;
    for (int i = 0; i < n && dot_count < MAX_DOTS; i++) {
        const int type = dot_type(kind, found[i].object);
        if (type < 0) continue;
        if ((type == DOT_HEALTH || type == DOT_TOKEN) ? !cfg.small_items : !cfg.items) continue;
        dots[dot_count].x = found[i].x;
        dots[dot_count].z = found[i].z;
        dots[dot_count].type = type;
        dots[dot_count].yaw = *(unsigned short*)found[i].object;
        dot_count++;
    }
}

static void find_dots(void) {
    static JfgEnemy found[MAX_DOTS];
    dot_count = 0;
    // Drawn in this order, so enemies and tribals are on top.
    add_kind(JFG_KIND_HEALTH);
    add_kind(JFG_KIND_TOKEN);
    for (unsigned int k = 0; k < sizeof(item_kinds) / sizeof(item_kinds[0]); k++) add_kind(item_kinds[k]);
    JfgNear q;
    q.x = show_x + show_span * 0.5f;
    q.y = 0.0f;
    q.z = show_z + show_span * 0.5f;
    q.radius = 1000000.0f;
    q.source = 0;
    int n = jfg_enemies_near(&q, found, MAX_DOTS);
    if (n > MAX_DOTS) n = MAX_DOTS;
    for (int i = 0; i < n && dot_count < MAX_DOTS; i++) {
        if (found[i].health <= 0 || jfg_enemy_dying(found[i].object)) continue;
        if (found[i].tribal ? !cfg.tribals : !cfg.enemies) continue;
        dots[dot_count].x = found[i].x;
        dots[dot_count].z = found[i].z;
        dots[dot_count].type = found[i].tribal ? DOT_TRIBAL : DOT_ENEMY;
        dot_count++;
    }
}

// A new area: the old map fades out, and the new one is built once the area's floors have settled (the level change
// comes before the new area's triangles are all in: their count stays the same for SETTLE ticks) and is shown, fading
// in, once the hero stands on it (else it is built again, at most 3 times). A hero who walks off the map within the
// same area (floors brought in without a level change) gets it built again the same way.
// The level change comes as the game starts leaving the old level, which stays loaded through the fade out with the
// hero still standing in it: nothing is built until the floors' count differs from the old level's (or OLD_WAIT ticks
// have passed, for an area that happens to have the same count), else the old level's map would be taken for the new.
#define OLD_WAIT (60 * 10)
static int last_count = -1, steady, check_wait, tries;
static int old_count = -1, old_wait;

static int off_map(void* hero, float x0, float z0, float size) {
    const float* p = (const float*)((unsigned char*)hero + 0x0C);
    return p[0] < x0 || p[2] < z0 || p[0] > x0 + size || p[2] > z0 + size;
}

RECOMP_CALLBACK("*", jfg_on_level_change) void minimap_level(int level, int character) {
    level_now = level;
    old_count = count_triangles();
    old_wait = OLD_WAIT;
    steady = 0;
    last_count = -1;
    tries = 0;
    ready_image = 0;
}

RECOMP_CALLBACK("*", jfg_on_game_tick) void minimap_tick(int frames) {
    read_config();
    void* hero = jfg_hero_get();
    if (!cfg.enabled || hero == 0) return;
    if ((check_wait -= frames) <= 0) {
        check_wait = 2;
        const int count = count_triangles();
        if (old_count >= 0 && (count != old_count || (old_wait -= 2) <= 0)) old_count = -1; // the old level has gone
        steady = count == last_count && old_count < 0 ? steady + 2 : 0;
        last_count = count;
        const int stray = built_for == level_now && shown_image && tries < 3 && off_map(hero, show_x, show_z, show_span);
        if (stray) built_for = -2;
        if (built_for != level_now) {
            vis_target = 0.0f; // the old area's map goes
            if (!ready_image && steady >= SETTLE && count > 0) {
                if (build() && (!off_map(hero, min_x, min_z, span) || tries >= 2)) {
                    ready_image = shown_image == 1 ? 2 : 1;
                    jfg_overlay_image(ready_image, PIC, PIC, picture);
                    ready_x = min_x;
                    ready_z = min_z;
                    ready_span = span;
                    built_for = level_now;
                    tries = 0;
                } else {
                    tries++;
                    steady = 0; // not this area's floors yet: wait for them to settle again
                }
            }
        }
    }
    // The fade, and the swap once the old map has gone.
    const float step = (float)frames / (float)FADE_TICKS;
    if (vis < vis_target) vis = vis + step < vis_target ? vis + step : vis_target;
    if (vis > vis_target) vis = vis - step > vis_target ? vis - step : vis_target;
    if (ready_image && vis <= 0.0f) {
        shown_image = ready_image;
        show_x = ready_x;
        show_z = ready_z;
        show_span = ready_span;
        ready_image = 0;
        vis_target = 1.0f;
        dot_count = 0;
        dot_wait = 0;
    }
    if (!shown_image || built_for != level_now) return;
    if ((dot_wait -= frames) <= 0) {
        dot_wait = 6;
        find_dots();
    }
}

// --- drawing: the overlay ---------------------------------------------------------------------------------------------

RECOMP_CALLBACK("*", jfg_on_draw_hud) void minimap_draw(JfgHudGfx* hud) {
    if (!cfg.enabled || !shown_image || vis <= 0.0f || jfg_game_paused()) return;
    void* hero = jfg_hero_get();
    if (hero == 0) return;
    float screen[2];
    jfg_overlay_size(screen);
    const float box = screen[1] * cfg.size, margin = screen[1] * 0.05f;
    const int corner = jfg_hud_corner(cfg.corner); // another mod's HUD piece there: the next free corner
    const float bx = (corner & 1) ? screen[0] - margin - box : margin;
    const float by = (corner & 2) ? screen[1] - margin - box : margin;
    const float op = cfg.opacity * vis;
    const int settled = built_for == level_now && !ready_image; // the hero and dots belong to the map on screen

    JfgOverlayImage img;
    img.x = bx;
    img.y = by;
    img.w = box;
    img.h = box;
    img.tint = jfg_rgba(0xFFFFFF, op);
    img.id = shown_image;
    jfg_overlay_draw_image(&img);

    if (!settled) return;
    const float k = box / show_span;
    const float r = box * 0.022f;
    JfgOverlayCircle c;
    c.radius = r;
    c.line = jfg_rgba(0x000000, op);
    c.thickness = r * 0.35f;
    // By DOT_*: enemy, tribal, item, key item, ammo, upgrade, health, token, chest, totem.
    static const unsigned int colours[] = { 0xFF3030, 0x3C78FF, 0xFFD000, 0xFFD000, 0xFF8C1A, 0xB45CFF, 0xFF70C8,
                                            0x40E8FF, 0xFFD000, 0xA8683A };
    static const float sizes[] = { 1.0f, 1.0f, 0.85f, 1.0f, 0.6f, 1.0f, 0.6f, 0.6f, 1.0f, 1.0f };
    for (int i = 0; i < dot_count; i++) {
        const int t = dots[i].type;
        c.x = bx + (dots[i].x - show_x) * k;
        c.y = by + (dots[i].z - show_z) * k;
        if (c.x < bx || c.y < by || c.x > bx + box || c.y > by + box) continue;
        if (t == DOT_CHEST || t == DOT_TOTEM) {
            // A rectangle turned as the object stands (a chest wide across its front, a totem pole a narrow block).
            const float half_w = r * (t == DOT_CHEST ? 1.25f : 0.55f), half_d = r * (t == DOT_CHEST ? 0.8f : 0.55f);
            const float ax = jfg_turn_cos(dots[i].yaw), az = -jfg_turn_sin(dots[i].yaw);   // its right
            const float fx = -jfg_turn_sin(dots[i].yaw), fz = -jfg_turn_cos(dots[i].yaw);  // its front
            float xy[8];
            const float sx[4] = { -1, 1, 1, -1 }, sz[4] = { -1, -1, 1, 1 };
            for (int v = 0; v < 4; v++) {
                xy[v * 2] = c.x + ax * half_w * sx[v] + fx * half_d * sz[v];
                xy[v * 2 + 1] = c.y + az * half_w * sx[v] + fz * half_d * sz[v];
            }
            JfgOverlayPolygon box_shape;
            box_shape.xy = xy;
            box_shape.count = 4;
            box_shape.fill = jfg_rgba(colours[t], op > 0.5f ? 1.0f : op * 2.0f);
            box_shape.line = jfg_rgba(0x000000, op);
            box_shape.thickness = r * 0.3f;
            jfg_overlay_polygon(&box_shape);
            continue;
        }
        c.radius = r * sizes[t];
        c.thickness = c.radius * 0.35f;
        c.fill = jfg_rgba(colours[t], op > 0.5f ? 1.0f : op * 2.0f);
        jfg_overlay_circle(&c);
    }

    const float* p = (const float*)((unsigned char*)hero + 0x0C);
    const float hx = bx + (p[0] - show_x) * k, hy = by + (p[2] - show_z) * k;
    const unsigned int yaw = *(unsigned short*)hero;
    const float fx = -jfg_turn_sin(yaw), fz = -jfg_turn_cos(yaw); // forward (and on the map: +z is down)
    const float len = box * 0.06f, wide = box * 0.04f;
    float xy[8];
    xy[0] = hx + fx * len;                       xy[1] = hy + fz * len;               // tip
    xy[2] = hx - fx * len * 0.6f - fz * wide;    xy[3] = hy - fz * len * 0.6f + fx * wide;
    xy[4] = hx - fx * len * 0.3f;                xy[5] = hy - fz * len * 0.3f;        // notch
    xy[6] = hx - fx * len * 0.6f + fz * wide;    xy[7] = hy - fz * len * 0.6f - fx * wide;
    // The arrowhead's notch makes it concave: drawn as two triangles, then outlined.
    JfgOverlayPolygon tri;
    float half[6];
    tri.xy = half;
    tri.count = 3;
    tri.line = 0;
    tri.thickness = 0.0f;
    tri.fill = jfg_rgba(0xFFD830, vis);
    half[0] = xy[0]; half[1] = xy[1]; half[2] = xy[2]; half[3] = xy[3]; half[4] = xy[4]; half[5] = xy[5];
    jfg_overlay_polygon(&tri);
    half[2] = xy[6]; half[3] = xy[7];
    jfg_overlay_polygon(&tri);
    JfgOverlayPolygon outline;
    outline.xy = xy;
    outline.count = 4;
    outline.fill = 0;
    outline.line = jfg_rgba(0x000000, vis);
    outline.thickness = box * 0.008f;
    jfg_overlay_polygon(&outline);
}
