// More Enemies: two or three times the enemies in every squad, for Jet Force Gemini: Recompiled (mod API version 6).
//
// The port does the work (jfg_squad_multiplier): each squad's member count is multiplied as its level is set up, the
// extra members save no kills (so saves, Keep Area Progress included, read the same at any setting, and no level runs
// out of kill flags), and Tribals, bosses and big enemies keep their count. Flying squads have their own setting. The mod hands it the setting before each
// level loads; a change takes effect at the next level.

#include "jfg_api.h"

RECOMP_IMPORT("*", unsigned int recomp_get_config_u32(const char* key));
RECOMP_IMPORT("*", double recomp_get_config_double(const char* key));

static void apply(void) {
    const int on = recomp_get_config_u32("enabled") != 0;
    const int percent = on ? (int)recomp_get_config_double("multiplier") : 100;
    const int flyers = on ? (int)recomp_get_config_double("flyers") : 100; // drones, flying insects: their own setting
    jfg_squad_multiplier(percent, recomp_get_config_u32("sentries") != 0 ? 1 : 0, flyers);
}

RECOMP_CALLBACK("*", jfg_on_level_change) void more_level(int level, int character) {
    apply();
}

RECOMP_CALLBACK("*", jfg_on_game_tick) void more_tick(int frames) {
    apply();
}
