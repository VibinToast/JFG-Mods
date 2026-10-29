// Dodge: a quick dash in the direction you move, with a moment where nothing can hurt you, for Jet Force Gemini:
// Recompiled (mod API version 5).
//
// The dash is the game's own push (its knockback: jfg_hero_push), set each tick of the dodge so the hero covers the
// Distance in the Dodge Time; walls stop it as they stop walking. The push moves the hero a little further than its
// own units say (about 10 % standing, 20 % running: the game adds some of its own motion), so the mod measures how far
// the hero has gone along the dodge (from where it started) and each tick pushes it to where the dodge's clock says it
// should be: a dodge on the move takes as long as one standing still. It stops at the Distance, or where a wall
// stopped it, and then the game's own easing off is cut (push 0) so it does not slide on. The hero's own run speeds
// (data + 0x04, + 0x08) are held at 0 while it lasts. The direction is where the hero is
// moving (strafing while aiming included); standing still, it is a hop backwards. The hero is protected for its first
// moment (jfg_hero_protect: the game's own protection, which drops damage and makes enemies hold their fire), and
// is tinted red while protected (jfg_object_tint, as the game flashes the enemy it targets).
//
// Juno and Vela roll as they do with the side buttons (jfg_hero_roll), to the side the dodge goes (to the right when it
// goes straight ahead or back), the roll's animation (object + 0x28) set each tick so it ends with the dash: it follows
// whichever is further on, the dodge's time or its distance (the same, but for a wall), and the roll's last frame is
// shown for a tick before the hero stands. The game's
// roll also moves the hero sideways itself (its side speed, data + 0x10, along the body's facing, data + 0x11C: side
// direction (cos, -sin)); that is taken off the push, so the dodge covers just the Distance. The game ends a roll when
// its animation reaches its last frame exactly and goes on crouched (moves 0x0E, then 4, a crawl), so the mod ends the
// roll with the dash (the roll state, data + 0x584, and the sideways flag, + 0x56C, cleared) and sets a standing move
// (jfg_hero_move: a walk the game turns into a run, or standing still); no crouch while it lasts (state 2 set to 1).
//
// Firing carries on through a dodge (the game's own); Shoot While Dodging off holds the fire button (N64 Z) off for it
// (jfg_input_block). The hero's own jump voice plays with it (jfg_hero_speak: Juno's, Vela's or Lupus's). The button: on a modern
// controller the right stick's click (N64 L is bound to Back too, which opens the settings) or N64 L, as chosen; else
// N64 L. A press of Back never dodges, and after the settings menu the dodge buttons must be let go first (the press
// that opened it rolled the hero once it closed). The hero's facing (object + 0x00): forward is (-sin, -cos), right (cos, -sin).

#include "jfg_api.h"
#include "jfg_util.h"

RECOMP_IMPORT("*", unsigned int recomp_get_config_u32(const char* key));
RECOMP_IMPORT("*", double recomp_get_config_double(const char* key));

#define BUTTON_L 0x0020
#define BUTTON_Z 0x2000

static unsigned int last_pad = 0;  // the modern controller's buttons last tick
static int after_menu = 0;         // the world stood still (the settings menu): no dodge until the buttons are let go
static int active = 0;             // a dodge is under way
static int dash_left = 0;          // 1/60 s ticks left of its push
static int dash_total = 0;         // ... of all of it
static float dir_x, dir_z;         // the dodge's direction (length 1)
static float dash_speed;           // the push, units per 1/60 s
static float start_x, start_z;     // where it started
static float goal;                 // how far it goes
static float last_gone;            // how far it had gone last tick
static int stuck;                  // ticks it has not moved on (a wall)
static int finishing;              // the distance is reached: the roll's last frame shows this tick, then it ends
static int rolling = 0;            // the dodge rolls the hero
static int cooldown = 0;           // 1/60 s ticks until the next one
#define TINT 0xFF101050u           // the red tint while protected: colour, then strength (0x50 of 0xFF)
static int tint_left = 0;          // 1/60 s ticks left of the red tint
static void* tinted_hero = 0;      // the hero tinted now
static int blocking = 0;           // the fire button is held off

static unsigned char* hero_data(void* hero) { return *(unsigned char**)((unsigned char*)hero + 0x68); }

static void unblock(void) {
    if (blocking) jfg_input_block(BUTTON_Z, 0);
    blocking = 0;
}

static void untint(void) {
    if (tinted_hero != 0) jfg_object_tint(tinted_hero, 0);
    tint_left = 0;
    tinted_hero = 0;
}

// The dodge is over: the roll ends with the hero on its feet, the fire button back.
static void end_dodge(void* hero) {
    active = 0;
    dash_left = 0;
    unblock();
    if (hero != 0) jfg_hero_push(hero, 0.0f, 0.0f, 0); // no easing off after: the dodge stops at its distance
    if (!rolling || hero == 0) { rolling = 0; return; }
    rolling = 0;
    unsigned char* data = hero_data(hero);
    if (data == 0) return;
    data[0x584] = 0;  // the roll is over
    data[0x56C] = 0;  // no longer moving sideways
    if ((data[0x568] & 0xF) == JFG_HERO_CROUCHED) data[0x568] = (data[0x568] & 0xF0) | JFG_HERO_STANDING;
    // On its feet: walking on (the game makes it a run) if the stick is held, else standing.
    JfgInput in;
    jfg_input_get(&in);
    const int moving = in.stick_x * in.stick_x + in.stick_y * in.stick_y > 10 * 10;
    jfg_hero_move(hero, moving ? JFG_MOVE_WALK : JFG_MOVE_STAND);
}

RECOMP_CALLBACK("*", jfg_on_level_change) void dodge_level(int level, int character) {
    active = 0;
    dash_left = 0;
    rolling = 0;
    cooldown = 0;
    untint();
    unblock();
}

// One tick of a dodge under way.
static void dodge_on(void* hero, int state, int frames) {
    unsigned char* data = hero_data(hero);
    if (state == JFG_HERO_DEAD || state == JFG_HERO_SWIMMING || data == 0) { end_dodge(hero); return; }
    // How far along the dodge the hero has gone: done at the distance, at a wall, or well past its time.
    const float* pos = (const float*)((unsigned char*)hero + 0x0C);
    const float gone = (pos[0] - start_x) * dir_x + (pos[2] - start_z) * dir_z;
    const float left = goal - gone;
    if (frames > 0) {
        stuck = gone - last_gone < 0.2f ? stuck + 1 : 0;
        last_gone = gone;
    }
    if (finishing) { end_dodge(hero); return; }
    if (left <= 1.0f || stuck >= 3 || dash_left <= -dash_total) {
        if (!rolling) { end_dodge(hero); return; }
        finishing = 1; // the roll's last frame, no more push, then it ends
        *(float*)((unsigned char*)hero + 0x28) = 0.99f;
        jfg_hero_push(hero, 0.0f, 0.0f, 0);
        return;
    }
    // The push for this tick: what takes the hero to where the dodge's clock says it should be by the next tick, so it
    // covers the distance in the dodge's time whether the hero was standing or running (the game adds a little of its
    // own motion, more on the move; the next tick makes up for it). Never backwards, at most twice the steady speed.
    const int step = frames > 0 ? frames : 2;
    const int next = dash_total - dash_left + step;
    const float due = goal * (float)(next < dash_total ? next : dash_total) / (float)dash_total;
    float speed = (due - gone) / (float)step;
    if (speed < 0.0f) speed = 0.0f;
    if (speed > dash_speed * 2.0f) speed = dash_speed * 2.0f;
    float px = dir_x * speed, pz = dir_z * speed;
    // The hero's own run held back (forward speeds, data + 0x04 / + 0x08): only the dash moves it, so a dodge on the
    // move takes as long, and rolls at the same pace, as one standing still.
    *(float*)(data + 0x04) = 0.0f;
    *(float*)(data + 0x08) = 0.0f;
    if (rolling) {
        // The roll's animation in step with the dash, ending with it.
        float t = (float)(dash_total - dash_left) / (float)dash_total;
        const float d = goal > 0 ? gone / goal : 1.0f;
        if (d > t) t = d;
        *(float*)((unsigned char*)hero + 0x28) = t < 0.99f ? t : 0.99f;
        if ((data[0x568] & 0xF) == JFG_HERO_CROUCHED) data[0x568] = (data[0x568] & 0xF0) | JFG_HERO_STANDING;
        // The roll's own sideways move, taken off the push.
        const float side = *(float*)(data + 0x10);
        const unsigned int body = *(unsigned short*)(data + 0x11C);
        px -= side * jfg_turn_cos(body);
        pz += side * jfg_turn_sin(body);
    }
    jfg_hero_push(hero, px, pz, dash_left);
    dash_left -= frames;
}

// The red tint while protected.
static void tint_tick(int frames) {
    if (tint_left <= 0) return;
    tint_left -= frames;
    if (tint_left <= 0) untint();
}

RECOMP_CALLBACK("*", jfg_on_game_tick) void dodge_tick(int frames) {
    if (jfg_game_paused()) { after_menu = 1; return; }
    if (cooldown > 0) cooldown -= frames;
    void* hero = jfg_hero_get();
    if (recomp_get_config_u32("enabled") == 0 || hero == 0) {
        if (active) end_dodge(hero);
        untint();
        unblock();
        return;
    }
    const int state = jfg_hero_state(hero);
    tint_tick(frames);
    if (active) { dodge_on(hero, state, frames); return; }

    JfgInput in;
    jfg_input_get(&in);
    JfgControls controls;
    jfg_controls_get(&controls);
    // Back opens the settings menu, and it is N64 L too: a press of it is never a dodge (else the hero rolled as the
    // menu closed). Once the menu has been up, the dodge buttons must be let go before they dodge again.
    if (after_menu) {
        if ((in.held & BUTTON_L) || (controls.buttons & (JFG_PAD_R3 | JFG_PAD_BACK))) {
            last_pad = controls.buttons;
            return;
        }
        after_menu = 0;
    }
    int pressed;
    if (controls.modern && !controls.mouse && recomp_get_config_u32("dodge_button") == 0) {
        pressed = (controls.buttons & JFG_PAD_R3) != 0 && (last_pad & JFG_PAD_R3) == 0;
    } else {
        pressed = (in.pressed & BUTTON_L) != 0 && (controls.buttons & JFG_PAD_BACK) == 0 && (last_pad & JFG_PAD_BACK) == 0;
    }
    last_pad = controls.buttons;
    if (!pressed || cooldown > 0) return;
    const int aiming = state == JFG_HERO_AIMING || state == JFG_HERO_AIMING_MOVING;
    if (!(state == JFG_HERO_MOVING || state == JFG_HERO_STANDING || state == JFG_HERO_CROUCHED ||
          (aiming && recomp_get_config_u32("while_aiming") != 0))) return;

    // Where the hero is going (its velocity, units a frame at +0x1C / +0x24); standing still, backwards.
    const float* vel = (const float*)((unsigned char*)hero + 0x1C);
    float dx = vel[0], dz = vel[2];
    float len = jfg_sqrt(dx * dx + dz * dz);
    const unsigned int yaw = *(unsigned short*)hero; // facing (object + 0x00)
    const float fx = -jfg_turn_sin(yaw), fz = -jfg_turn_cos(yaw);   // forward
    if (len < 0.3f) { // standing still: back
        dx = -fx;
        dz = -fz;
        len = 1.0f;
    }
    // Distance in Dodge Time (hundredths of a second): the push per 1/60 s.
    dash_total = (int)(recomp_get_config_double("dodge_time") * 60.0 / 100.0);
    if (dash_total < 6) dash_total = 6;
    goal = (float)recomp_get_config_double("distance");
    dash_speed = goal / (float)dash_total;
    dir_x = dx / len;
    dir_z = dz / len;
    start_x = ((const float*)((unsigned char*)hero + 0x0C))[0];
    start_z = ((const float*)((unsigned char*)hero + 0x0C))[2];
    last_gone = 0.0f;
    stuck = 0;
    finishing = 0;
    dash_left = dash_total;
    active = 1;
    cooldown = (int)(recomp_get_config_double("cooldown") * 60.0 / 100.0); // hundredths of a second
    const int protect = (int)(recomp_get_config_double("protect") * 60.0 / 100.0);
    if (protect > 0) {
        jfg_hero_protect(hero, protect);
        if (recomp_get_config_u32("tint") != 0) {
            if (tinted_hero != hero) untint();
            tint_left = protect;
            tinted_hero = hero;
            jfg_object_tint(hero, TINT);
        }
    }
    if (recomp_get_config_u32("shoot") == 0) { jfg_input_block(BUTTON_Z, 1); blocking = 1; }
    // The roll, to the side the dodge goes: right is (-fz, fx).
    const int right = dx * -fz + dz * fx >= 0.0f;
    rolling = recomp_get_config_u32("roll") != 0 && jfg_hero_roll(hero, right);
    if (recomp_get_config_u32("jump_sound") != 0) jfg_hero_speak(hero, JFG_SPEAK_JUMP); // Juno's, Vela's or Lupus's
    dodge_on(hero, state, frames); // this tick is the first of the dodge
}
