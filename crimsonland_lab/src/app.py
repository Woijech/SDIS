from __future__ import annotations

from pathlib import Path
from typing import Any

import pygame

from src.core.config_loader import load_json
from src.core.resource_manager import ResourceManager
from src.scenes.base import BaseScene
from src.scenes.game import GameScene
from src.scenes.game_over import GameOverScene
from src.scenes.highscores import HighScoresScene
from src.scenes.menu import MainMenuScene


class App:
    """Main application object responsible for pygame lifecycle and scene switching."""

    def __init__(self, base_dir: Path) -> None:
        """Initialize pygame, shared resources, and the first scene.

        Args:
            base_dir: Project root directory that contains config and assets.

        Returns:
            None.
        """
        self.base_dir = base_dir
        self.settings = load_json(self.base_dir / "config" / "settings.json")

        pygame.init()
        self.screen = self._create_screen()
        pygame.display.set_caption(self.settings["title"])
        self.clock = pygame.time.Clock()
        self.running = True

        self.default_font = pygame.font.SysFont("trebuchetms", 24)
        self.title_font = pygame.font.SysFont("georgia", 48, bold=True)
        self.small_font = pygame.font.SysFont("consolas", 18)
        self.hud_font = pygame.font.SysFont("consolas", 20, bold=True)

        self.resources = ResourceManager(
            assets_dir=self.base_dir / "assets",
            music_volume=self.settings["music_volume"],
            sfx_volume=self.settings["sfx_volume"],
        )

        self.scene: BaseScene | None = None
        self.change_scene("menu")

    def _create_screen(self) -> pygame.Surface:
        """Create the main pygame display surface.

        Returns:
            Screen surface configured according to the current settings. The
            stored width and height are updated to reflect the actual display
            size selected by pygame.
        """
        is_fullscreen = self.settings.get("fullscreen", False)
        screen_size = (self.settings["screen_width"], self.settings["screen_height"])
        flags = pygame.FULLSCREEN if is_fullscreen else 0
        requested_size = (0, 0) if is_fullscreen else screen_size
        screen = pygame.display.set_mode(requested_size, flags)
        actual_width, actual_height = screen.get_size()
        self.settings["screen_width"] = actual_width
        self.settings["screen_height"] = actual_height
        return screen

    def change_scene(self, scene_name: str, **kwargs: Any) -> None:
        """Switch the active scene and call scene lifecycle hooks.

        Args:
            scene_name: Identifier of the scene that should become active.
            **kwargs: Extra values forwarded to the scene constructor when
                needed, for example the final score on the game-over screen.

        Returns:
            None.

        Raises:
            ValueError: If ``scene_name`` is not recognized.
        """
        if self.scene is not None and hasattr(self.scene, "on_exit"):
            self.scene.on_exit()

        if scene_name == "menu":
            self.scene = MainMenuScene(self)
        elif scene_name == "highscores":
            self.scene = HighScoresScene(self)
        elif scene_name == "game":
            self.scene = GameScene(self)
        elif scene_name == "game_over":
            self.scene = GameOverScene(self, **kwargs)
        else:
            raise ValueError(f"Unknown scene: {scene_name}")

        if hasattr(self.scene, "on_enter"):
            self.scene.on_enter()

    def quit(self) -> None:
        """Request application shutdown after the current frame.

        Returns:
            None.
        """
        self.running = False

    def run(self) -> None:
        """Run the main pygame event, update, and render loop.

        Returns:
            None. Control returns only after the application exits and pygame is
            shut down.
        """
        target_fps = self.settings.get("fps", 60)
        while self.running:
            dt = self.clock.tick(target_fps) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.scene.handle_event(event)
            self.scene.update(dt)
            self.scene.render(self.screen)
            pygame.display.flip()

        pygame.quit()
