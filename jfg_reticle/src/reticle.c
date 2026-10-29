// Reticle: a reticle of your own for Jet Force Gemini: Recompiled (mod API version 5).
//
// The game's reticle jumps onto an enemy the aim passes over (the aim lock); Snap to Enemies Off turns that off
// (jfg_aim_lock). Any shape other than the game's cancels the game's reticle (jfg_on_reticle_draw) and draws this one
// in its place, into the HUD's display list as the game would have, as solid rectangles in the chosen colour and size
// (1-cycle rectangles coloured by the combiner's primitive colour: the fill mode's colour depends on the frame buffer's
// format, and came out black), with a dark outline so it shows on any background. A locked target (only
// with Snap to Enemies on, or a homing weapon) draws the reticle in the lock colour.

#include "jfg_api.h"
#include "jfg_util.h"

RECOMP_IMPORT("*", unsigned int recomp_get_config_u32(const char* key));
RECOMP_IMPORT("*", double recomp_get_config_double(const char* key));

enum { SHAPE_GAME, SHAPE_DOT, SHAPE_CROSS, SHAPE_CROSS_DOT, SHAPE_CIRCLE, SHAPE_CIRCLE_DOT, SHAPE_BRACKETS };

// White, Red, Green, Cyan, Yellow, Magenta, Orange (0xRRGGBB).
static const unsigned int colors[] = { 0xFFFFFF, 0xFF3030, 0x40FF60, 0x40E0FF, 0xFFE040, 0xFF40FF, 0xFF9020 };
#define COLORS (int)(sizeof(colors) / sizeof(colors[0]))

static struct {
    int enabled;
    int shape;
    unsigned int color, lock_color;
    float size;    // 1 = 100%
    int outline;
} cfg;

static unsigned int pick_color(const char* key) {
    unsigned int i = recomp_get_config_u32(key);
    return colors[i < (unsigned int)COLORS ? i : 0];
}

static void read_config(void) {
    cfg.enabled = recomp_get_config_u32("enabled") != 0;
    jfg_aim_lock(!cfg.enabled || recomp_get_config_u32("snap") != 0);
    cfg.shape = (int)recomp_get_config_u32("shape");
    cfg.color = pick_color("color");
    cfg.lock_color = pick_color("lock_color");
    cfg.size = (float)recomp_get_config_double("size") / 100.0f;
    cfg.outline = recomp_get_config_u32("outline") != 0;
}

RECOMP_CALLBACK("*", jfg_on_game_tick) void reticle_tick(int frames) {
    read_config();
}

// --- drawing: RDP fill rectangles -----------------------------------------------------------------------------------
// The renderer draws 2D rectangles on the game's own pixels (448 x 336 in its hi-res mode), whatever their quarter-pixel
// coordinates and RT64's upscale flag: so the shapes are drawn as clean pixel art on that grid, centred on one pixel and
// mirrored both ways, so they are exactly symmetric (a ring by the midpoint method, row spans that join up, no gaps).
// The commands go straight into the HUD's list (a call into a list in the mod's memory ended the HUD's drawing).
static unsigned int** gfx;
static int screen_w, screen_h;

static void cmd(unsigned int w0, unsigned int w1) {
    (*gfx)[0] = w0;
    (*gfx)[1] = w1;
    *gfx += 2;
}

static void fill_color(unsigned int rgb) {
    cmd(0xE7000000, 0);                       // pipe sync
    cmd(0xFA000000, (rgb << 8) | 0xFF);       // primitive colour, opaque
}

// The pixels from (x0, y0) to (x1, y1), both included, clipped to the screen.
static void rect(int x0, int y0, int x1, int y1) {
    if (x0 < 0) x0 = 0;
    if (y0 < 0) y0 = 0;
    if (x1 >= screen_w) x1 = screen_w - 1;
    if (y1 >= screen_h) y1 = screen_h - 1;
    if (x1 < x0 || y1 < y0) return;
    // In 1-cycle mode the lower right edge is not drawn: one more each way.
    cmd(0xF6000000 | ((unsigned int)(x1 + 1) << 14) | ((unsigned int)(y1 + 1) << 2), ((unsigned int)x0 << 14) | ((unsigned int)y0 << 2));
}

// How far a circle of radius r reaches across the row k pixels from its centre row: the last pixel whose centre is
// inside it (x * x + k * k <= r * r), -1 past it.
static int reach(float r, int k) {
    const float d = r * r - (float)(k * k);
    if (d < 0) return -1;
    int x = (int)jfg_sqrt(d);
    while ((float)((x + 1) * (x + 1)) <= d) x++; // the square root's rounding
    while (x > 0 && (float)(x * x) > d) x--;
    return x;
}

// A ring of pixels around (cx, cy): outer radius ro, inner ri (ri < 0: a filled disc). Each row is drawn in both
// halves, and the row as far above as below: symmetric. A row reaches in at least as far as the next row out reaches
// out, so the ring has no gaps where it turns steeply.
static void ring(int cx, int cy, float ro, float ri) {
    const int rows = (int)ro;
    for (int k = 0; k <= rows; k++) {
        const int out_x = reach(ro, k);
        if (out_x < 0) continue;
        int in_x = ri >= 0 ? reach(ri, k) + 1 : 0; // the first column not inside the hole (0: none)
        const int next = reach(ro, k + 1);
        if (ri >= 0 && next >= 0 && next < in_x) in_x = next;
        if (in_x <= 0) {
            rect(cx - out_x, cy - k, cx + out_x, cy - k);
            if (k != 0) rect(cx - out_x, cy + k, cx + out_x, cy + k);
        } else {
            rect(cx - out_x, cy - k, cx - in_x, cy - k);
            rect(cx + in_x, cy - k, cx + out_x, cy - k);
            if (k != 0) {
                rect(cx - out_x, cy + k, cx - in_x, cy + k);
                rect(cx + in_x, cy + k, cx + out_x, cy + k);
            }
        }
    }
}

static int round_px(float v) { return (int)(v + 0.5f); }

// The shape around the pixel (cx, cy), every part grown by g pixels (the outline pass). unit: the reticle's size in
// pixels per step (1 at 100 % on a 240-line screen).
static void shape(int cx, int cy, float unit, int g) {
    const int t = round_px(unit * 0.6f) > 0 ? round_px(unit * 0.6f) : 1;      // line thickness
    const int h = (t - 1) / 2, h2 = t - 1 - h;                               // lines centred on the pixel
    const float dot = unit * 1.6f > 1.5f ? unit * 1.6f : 1.5f;               // dot radius (2.24 at 100 %: a round 5 x 5)
    const int arm = round_px(unit * 5.0f), gap = round_px(unit * 2.0f);
    const int s = cfg.shape;
    if (s == SHAPE_DOT || s == SHAPE_CROSS_DOT || s == SHAPE_CIRCLE_DOT) ring(cx, cy, dot + (float)g, -1.0f);
    if (s == SHAPE_CROSS || s == SHAPE_CROSS_DOT) {
        rect(cx - gap - arm - g, cy - h - g, cx - gap + g, cy + h2 + g);   // left
        rect(cx + gap - g, cy - h - g, cx + gap + arm + g, cy + h2 + g);   // right
        rect(cx - h - g, cy - gap - arm - g, cx + h2 + g, cy - gap + g);   // up
        rect(cx - h - g, cy + gap - g, cx + h2 + g, cy + gap + arm + g);   // down
    }
    if (s == SHAPE_CIRCLE || s == SHAPE_CIRCLE_DOT) {
        const float radius = (float)round_px(unit * 5.0f);
        const float ro = radius + (float)t * 0.5f + (float)g + 0.25f; // a hair past the half pixel: no lone end pixels
        ring(cx, cy, ro, ro - (float)t - 2.0f * (float)g);
    }
    if (s == SHAPE_BRACKETS) {
        const int r = round_px(unit * 5.0f), l = round_px(unit * 2.5f);
        for (int sx = -1; sx <= 1; sx += 2) {
            for (int sy = -1; sy <= 1; sy += 2) {
                const int x = cx + sx * r, y = cy + sy * r;
                // the corner's two arms, pointing back towards the centre
                if (sx < 0) rect(x - g, y - h - g, x + l + g, y + h2 + g); else rect(x - l - g, y - h - g, x + g, y + h2 + g);
                if (sy < 0) rect(x - h - g, y - g, x + h2 + g, y + l + g); else rect(x - h - g, y - l - g, x + h2 + g, y + g);
            }
        }
    }
}

RECOMP_CALLBACK("*", jfg_on_reticle_draw) void reticle_draw(JfgReticle* r) {
    if (!cfg.enabled || cfg.shape == SHAPE_GAME || r->player != 0 || r->gfx == 0) return;
    r->cancel = 1;
    gfx = (unsigned int**)r->gfx;
    screen_w = r->width > 0 ? r->width : 320;
    screen_h = r->height > 0 ? r->height : 240;
    const float unit = cfg.size * (float)screen_h / 240.0f;
    // The game's microcode is F3D (Rare's F3DDKR): its own opcodes for the other modes.
    cmd(0xE7000000, 0);                          // pipe sync
    cmd(0xBA001402, 0x00000000);                 // cycle type: 1 cycle (G_SETOTHERMODE_H)
    cmd(0xFCFFFFFF, 0xFFFDF6FB);                 // combine: the primitive colour (G_CC_PRIMITIVE, both cycles)
    cmd(0xB900031D, 0x0F0A4000);                 // render mode: opaque surface (G_SETOTHERMODE_L: G_RM_OPA_SURF, 2)
    if (cfg.outline) {
        fill_color(0x000000);
        shape(r->x, r->y, unit, 1);
    }
    fill_color(r->locked ? cfg.lock_color : cfg.color);
    shape(r->x, r->y, unit, 0);
    cmd(0xE7000000, 0);
}
