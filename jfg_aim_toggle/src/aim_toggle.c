// Toggle Aim: manual aiming (the aim button, N64 R) toggles instead of being held, for Jet Force Gemini: Recompiled
// (mod API version 5).
//
// The port turns R into a toggle on the input side (jfg_input_toggle), after Swap Triggers and before the dual-stick
// controls read it, so every control scheme gets it. The mod lets go of the aim when there is nothing to aim for: the
// hero is dead, the level changes, or (an option) the hero jumps or swims.

#include "jfg_api.h"

RECOMP_IMPORT("*", unsigned int recomp_get_config_u32(const char* key));

#define BUTTON_R 0x0010

static int on = -1;

RECOMP_CALLBACK("*", jfg_on_game_tick) void aim_toggle_tick(int frames) {
    const int want = recomp_get_config_u32("enabled") != 0;
    if (want != on) {
        jfg_input_toggle(BUTTON_R, want);
        on = want;
    }
    if (!on || (jfg_input_toggled() & BUTTON_R) == 0) return;
    void* hero = jfg_hero_get();
    const int state = hero != 0 ? jfg_hero_state(hero) : -1;
    if (state < 0 || state == JFG_HERO_DEAD) { jfg_input_toggle_release(BUTTON_R); return; }
    if (recomp_get_config_u32("release") != 0 && (state == JFG_HERO_IN_AIR || state == JFG_HERO_SWIMMING))
        jfg_input_toggle_release(BUTTON_R);
}

RECOMP_CALLBACK("*", jfg_on_level_change) void aim_toggle_level(int level, int character) {
    if (on) jfg_input_toggle_release(BUTTON_R);
}
