// Concussion Cannon's ammo: the game has none of it, so it comes from four places, each an option, run by the port
// (jfg_weapon_ammo_sources, the same for every mod's weapon):
// - Drops: an enemy the heroes or Floyd kill may drop a charge cell (the pack's charge orb, hovering where the enemy
//   died; the shared drop pool: one drop a kill across mods, twice as likely from a big enemy); walking into it gives
//   two charges.
// - Shotgun refill: picking up plasma shotgun ammo, or the shotgun itself, gives three charges too.
// - Pickups: a share of the level's shotgun pickups give this weapon instead (their model stays the shotgun's).
// - Recharge: one comes back every so many seconds while you have fewer than its most.
// None of them goes past the weapon's capacity.

#include "jfg_api.h"

RECOMP_IMPORT("*", unsigned int recomp_get_config_u32(const char* key));
RECOMP_IMPORT("*", double recomp_get_config_double(const char* key));

extern int weapon_id; // cannon.c

#define CELL_TYPE "jfg_concussion_cannon:objtype_charge"
#define STOCK 3               // the plasma shotgun

RECOMP_CALLBACK("*", jfg_on_game_tick) void cannon_ammo_tick(int frames) {
    if (weapon_id < 0) return;
    const int on = recomp_get_config_u32("enabled") != 0;
    JfgAmmoSources s = {
        CELL_TYPE,
        on && recomp_get_config_u32("drops") != 0 ? (int)recomp_get_config_double("drop_chance") : 0,
        2, 1.6f, 18.0f, 0,
        STOCK, on && recomp_get_config_u32("shotgun_refill") != 0 ? 3 : 0,
        STOCK, on ? (int)recomp_get_config_double("pickup_share") : 0,
        on && recomp_get_config_u32("recharge") != 0 ? (int)(recomp_get_config_double("recharge_secs") * 60.0) : 0,
    };
    jfg_weapon_ammo_sources(weapon_id, &s);
}
