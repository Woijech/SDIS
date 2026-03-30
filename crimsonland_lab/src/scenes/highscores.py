from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.core.highscores import load_scores
from src.scenes.base import BaseScene

if TYPE_CHECKING:
    from src.app import App


class HighScoresScene(BaseScene):
    """Scene that displays the saved top-10 table."""

    def __init__(self, app: App) -> None:
        """Initialize the high-score scene.

        Args:
            app: Running application instance.

        Returns:
            None.
        """
        super().__init__(app)
        self.scores: list[dict[str, str | int]] = []

    def on_enter(self) -> None:
        """Reload scores and start menu music.

        Returns:
            None.
        """
        self.app.resources.play_music("menu_music")
        self.scores = load_scores(self.app.base_dir / "config" / "scores.json")

    def handle_event(self, event: pygame.event.Event) -> None:
        """Return to the main menu on confirm/back actions.

        Args:
            event: Event received from the main loop.

        Returns:
            None.
        """
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_RETURN):
            self.app.resources.play_sound("ui_confirm")
            self.app.change_scene("menu")

    def render(self, surface: pygame.Surface) -> None:
        """Draw the high-score table.

        Args:
            surface: Framebuffer surface used for the current frame.

        Returns:
            None.
        """
        self.draw_backdrop(surface, accent=(93, 170, 238), secondary=(232, 156, 96))
        title = self.app.title_font.render("High Scores", True, (248, 240, 223))
        panel = pygame.Rect(0, 0, 820, 480)
        panel.center = (surface.get_width() // 2, surface.get_height() // 2 + 30)
        surface.blit(title, title.get_rect(midleft=(panel.x, 60)))

        headers = ("Place", "Name", "Score", "Date")
        x_positions = (
            panel.x + 30,
            panel.x + 140,
            panel.x + 460,
            panel.x + 640,
        )

        self.draw_panel(surface, panel, accent=(93, 170, 238), fill=(12, 17, 26, 224))

        for header, x in zip(headers, x_positions):
            text = self.app.default_font.render(header, True, (212, 224, 240))
            surface.blit(text, (x, panel.y + 25))

        start_y = panel.y + 70
        row_height = 36
        for index in range(10):
            row_rect = pygame.Rect(panel.x + 20, start_y + index * row_height - 6, 780, 30)
            if index % 2 == 0:
                pygame.draw.rect(surface, (30, 38, 50), row_rect, border_radius=8)
            entry = self.scores[index] if index < len(self.scores) else {"name": "---", "score": 0, "date": "---"}
            values = (str(index + 1), entry["name"], str(entry["score"]), entry["date"])
            for value, x in zip(values, x_positions):
                label = self.app.default_font.render(value, True, (240, 240, 240))
                surface.blit(label, (x, start_y + index * row_height))

        note = self.app.small_font.render("ESC / Enter - back", True, (150, 164, 182))
        surface.blit(note, note.get_rect(midleft=(panel.x, panel.bottom + 20)))
