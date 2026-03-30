# Project Architecture

## 1. App / Scene Lifecycle

`App` initializes pygame, creates the window, loads settings, and manages scene switching.
Scenes are changed through `change_scene`.

## 2. Scenes

- `MainMenuScene`
- `HighScoresScene`
- `GameScene`
- `GameOverScene`

## 3. Game Entities

- `Player`
- `Enemy`
- `Projectile`
- `Weapon`
- `WeaponPickup`
- `CircleEffect`

## 4. External Data

All settings and game content live in `config/*.json`:

- `settings.json`
- `players.json`
- `particles.json`
- `weapons.json`
- `enemies.json`
- `waves.json`
- `scores.json`

## 5. Testable Logic

Logic that can be tested separately from pygame is placed in `src/logic`:

- `WaveController`
- wave plan generation
- weapon spread math

High score persistence lives in `src/core/highscores.py`.
