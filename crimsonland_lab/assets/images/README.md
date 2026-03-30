Place PNG sprites for the player and enemies here.

Expected structure:

```text
assets/images/
├── players/
│   └── player.png
├── bosses/
│   ├── juggernaut.png
│   ├── stormcaller.png
│   ├── reaper.png
│   └── overlord.png
└── enemies/
    ├── walker.png
    ├── runner.png
    ├── tank.png
    ├── shooter.png
    └── kamikaze.png
```

You can use different file names if you also update:

- `config/players.json` -> `sprite`
- `config/enemies.json` -> `sprite`

`players/player.png` can stay as a temporary placeholder until you replace it with your own PNG.
You can keep dedicated files for bosses:

- `bosses/juggernaut.png`
- `bosses/stormcaller.png`
- `bosses/reaper.png`
- `bosses/overlord.png`

If an image is missing, the game automatically falls back to the default circle.
