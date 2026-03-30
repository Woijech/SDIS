# Crimsonland Lite

Small arcade survival game built with **Python + pygame**, inspired by Crimsonland.

## Features

- event-driven pygame application structure;
- main menu with `Start Game / High Scores / Exit`;
- **20 waves** of enemies defined in `config/waves.json`;
- **3 weapons**: pistol, shotgun, rifle;
- **5 enemy types** with different stats and behaviors:
  - walker,
  - runner,
  - tank,
  - shooter,
  - kamikaze;
- PNG sprite support for the player and every enemy type;
- weapon upgrades dropped during combat;
- miniboss encounters on waves 5, 10, 15, and 20;
- persistent high-score table stored in `config/scores.json`;
- sound effects and music from `assets/sounds`;
- hit, death, pickup, and wave announcement effects;
- external JSON configuration files.

## Project Structure

```text
crimsonland_lab/
├── main.py
├── README.md
├── requirements.txt
├── config/
├── assets/
├── docs/
├── src/
│   ├── core/
│   ├── entities/
│   ├── logic/
│   ├── scenes/
│   └── ui/
└── tests/
```

## Run

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the game:

```bash
python main.py
```

## Controls

- `WASD` - move
- `LMB` - fire
- `1 / 2 / 3` - switch weapon
- `ESC` - return to menu

## Configuration

### `config/settings.json`

General window, player, audio, and weapon drop settings.

Optional fields:

- `fullscreen` - set to `true` to launch directly in fullscreen mode
- `player_size_scale` - scale factor applied to `player_radius`
- `enemy_size_scale` - scale factor applied to enemy `radius` values from `config/enemies.json`
- `player_sprite` - fallback path to the player PNG inside `assets/images`

### `config/weapons.json`

Weapon parameters:

- damage
- cooldown
- projectile speed
- pellets per shot
- spread

### `config/enemies.json`

Enemy parameters:

- health
- speed
- radius
- damage
- behavior
- PNG sprite
- score reward

### `config/waves.json`

The file contains **20 waves**. Each wave defines:

- wave number
- delay before the next wave
- enemy groups
- spawn count and interval

## Architecture

The project is split by responsibility:

- `src/core` - config loading, resources, profiles, and highscores
- `src/logic` - pure gameplay logic and helper math
- `src/entities` - game entities
- `src/scenes` - menu, highscores, gameplay, and game-over screens
- `src/ui` - reusable UI components

## Character Sprites

The game can load PNG images for the player and enemies from `assets/images`.

Expected structure:

```text
assets/images/
├── player.png
└── enemies/
    ├── walker.png
    ├── runner.png
    ├── tank.png
    ├── shooter.png
    └── kamikaze.png
```

How it works:

- the player uses data from `config/players.json`, and the active model is selected through `config/settings.json` -> `player_model`;
- each enemy reads its sprite path from `config/enemies.json` -> `sprite`;
- if a PNG file is missing, the game automatically falls back to the original circular rendering;
- every image is scaled to match the entity size and then cropped to a circle.

## Hit Particles

When a bullet hits an enemy, the game can spawn a floating text hit effect.

- shared defaults live in `config/particles.json` -> `enemy_hit_text`;
- each enemy type can override the text in `config/enemies.json` -> `hit_text`;
- minibosses are configured as dedicated enemies inside `config/enemies.json`.

Example:

```json
{
  "enemy_hit_text": {
    "color": [92, 186, 255],
    "chance": 0.35,
    "lifetime": 0.55,
    "gravity": 420,
    "drift_x_min": -65,
    "drift_x_max": 65,
    "launch_y_min": -105,
    "launch_y_max": -50,
    "offset_y": -8
  }
}
```

Example for a specific enemy:

```json
{
  "walker": {
    "hit_text": {
      "text": ["SC", "CRIT", "HIT"]
    }
  },
  "boss_juggernaut": {
    "title": "Juggernaut Prime",
    "health": 420,
    "speed": 88,
    "radius": 24,
    "contact_damage": 28,
    "score": 150,
    "behavior": "chase",
    "sprite": "bosses/juggernaut.png"
  }
}
```

Configurable fields:

- `text` - single string or list of strings randomly selected on hit
- `color` - text color
- `chance` - spawn chance
- `lifetime` - effect duration
- `gravity` - downward acceleration
- `drift_x_min` / `drift_x_max` - horizontal velocity range
- `launch_y_min` / `launch_y_max` - initial vertical velocity range
- `offset_y` - spawn offset relative to the enemy center

Dedicated boss entries look like this:

```json
{
  "boss_stormcaller": {
    "title": "Stormcaller Prime",
    "health": 260,
    "speed": 105,
    "radius": 18,
    "contact_damage": 16,
    "score": 210,
    "behavior": "keep_distance",
    "preferred_distance": 280,
    "shoot_cooldown": 0.9,
    "ranged_damage": 13,
    "ranged_speed": 330,
    "sprite": "bosses/stormcaller.png"
  }
}
```

Current boss enemy ids:

- `boss_juggernaut`
- `boss_stormcaller`
- `boss_reaper`
- `boss_overlord`

You can edit them like any standard enemy by changing `title`, `health`, `speed`, `radius`, `contact_damage`, `score`, `behavior`, `sprite`, and ranged attack settings.

Example `config/players.json`:

```json
{
  "default": {
    "speed": 260,
    "radius": 16,
    "health": 100,
    "sprite": "player.png",
    "color": [126, 232, 180]
  },
  "marine": {
    "sprite": "players/marine.png",
    "color": [110, 210, 255]
  }
}
```

To add a new player model:

- place the PNG in `assets/images`, for example `assets/images/players/marine.png`;
- add a new profile to `config/players.json`;
- point `config/settings.json` -> `player_model` to that profile, for example `"marine"`.

The legacy `player_sprite` field in `settings.json` is still kept as a fallback, so existing setups continue to work.

## Tests

Unit tests cover logic that does not depend on pygame:

```bash
python -m unittest discover -s tests -v
```

Coverage includes:

- config loading
- wave logic
- high-score insertion
- weapon spread math
- progression helpers
